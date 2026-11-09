"""Read-only shell branch audit; external selectors remain separate from witnesses."""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import time
from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from moo.paths import PROJECT_ROOT
from typing import Any

from moo.research_utils import connect_readonly, file_sha256, require_strict_alignment


@dataclass(frozen=True, order=True)
class Triple:
    x: int
    y: int
    r: int

    @property
    def primitive(self) -> bool:
        return math.gcd(self.x, math.gcd(self.y, self.r)) == 1

    @property
    def parameter(self) -> Fraction:
        return Fraction(self.y, self.r + self.x)

    def values(self) -> list[int]:
        return [self.x, self.y, self.r]


def from_parameter(t: Fraction) -> Triple:
    """External rational parametrization, oriented by sorting positive legs."""
    if not 0 < t < 1:
        raise ValueError("Parameter must lie strictly between zero and one")
    p, q = t.numerator, t.denominator
    a, b, c = q*q - p*p, 2*p*q, q*q + p*p
    d = math.gcd(a, math.gcd(b, c))
    return Triple(min(a, b)//d, max(a, b)//d, c//d)


def blind_pairs(cap: int) -> tuple[set[Triple], int]:
    hits: set[Triple] = set()
    trials = 0
    for x in range(1, cap):
        for y in range(x, cap):
            trials += 1
            r = math.isqrt(x*x + y*y)
            if r <= cap and r*r == x*x + y*y:
                hits.add(Triple(x, y, r))
    return hits, trials


def square_factor_pairs(cap: int) -> set[Triple]:
    """Independent exact factor selector; trial division is not a speed claim."""
    hits: set[Triple] = set()
    for y in range(1, cap):
        for u in range(1, y):
            v, rem = divmod(y*y, u)
            if rem or (u + v) % 2:
                continue
            x, r = (v-u)//2, (v+u)//2
            if 0 < x <= y and r <= cap:
                hits.add(Triple(x, y, r))
    return hits


def euclid_selector(cap: int) -> tuple[set[Triple], int]:
    hits: set[Triple] = set()
    trials = 0
    for m in range(2, math.isqrt(cap-1)+1):
        for n in range(1, m):
            trials += 1
            r = m*m + n*n
            if r > cap or (m-n) % 2 == 0 or math.gcd(m, n) != 1:
                continue
            x, y = sorted((m*m - n*n, 2*m*n))
            for k in range(1, cap//r+1):
                hits.add(Triple(k*x, k*y, k*r))
    return hits, trials


def berggren_selector(cap: int) -> dict[Triple, str]:
    """External classical tree, with odd leg first internally. No graph claims."""
    result: dict[Triple, str] = {}
    stack = [(3, 4, 5, "")]
    while stack:
        a, b, c, word = stack.pop()
        if c > cap:
            continue
        triple = Triple(min(a, b), max(a, b), c)
        if triple in result:
            raise AssertionError("Repeated primitive triple in tree")
        result[triple] = word
        children = (
            (a-2*b+2*c, 2*a-b+2*c, 2*a-2*b+3*c, word+"A"),
            (a+2*b+2*c, 2*a+b+2*c, 2*a+2*b+3*c, word+"B"),
            (-a+2*b+2*c, -2*a+b+2*c, -2*a+2*b+3*c, word+"C"),
        )
        stack.extend(children)
    return result


def is_prime(n: int) -> bool:
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n)+1))


class WitnessReader:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.stage = int(conn.execute("SELECT MAX(stage) FROM stages").fetchone()[0])
        self.nodes: dict[Fraction, dict[str, Any] | None] = {}
        self.edges: dict[tuple[int, str, int], dict[str, Any]] = {}

    def node(self, value: Fraction) -> dict[str, Any] | None:
        value = Fraction(value)
        if value not in self.nodes:
            row = self.conn.execute(
                "SELECT * FROM nodes WHERE p=? AND q=?",
                (value.numerator, value.denominator),
            ).fetchone()
            payload = dict(row) if row is not None else None
            if payload is not None:
                confirmation = payload["confirmed_stage"]
                payload["status_at_observed_stage"] = (
                    "confirmed" if confirmation is not None and confirmation <= self.stage
                    else "speculative")
            self.nodes[value] = payload
        return self.nodes[value]

    def edge(self, a: int, op: str, b: int) -> dict[str, Any]:
        key = (a, op, b)
        if key in self.edges:
            return self.edges[key]
        if op == "+":
            value = Fraction(a+b)
        elif op == "-":
            value = Fraction(a-b)
        elif op == "*":
            value = Fraction(a*b)
        elif op == "/":
            value = Fraction(a, b)
        else:
            raise ValueError(op)
        left, right, result = self.node(Fraction(a)), self.node(Fraction(b)), self.node(value)
        payload: dict[str, Any] = {
            "equation": f"{a} {op} {b} -> {value}", "a": a, "b": b,
            "op": op, "value": str(value), "present": False,
            "candidate_stage": max(a, b),
            "left_node": left, "right_node": right, "result_node": result,
        }
        if max(a, b) > self.stage:
            payload["reason"] = "operand_beyond_observed_stage"
        elif left is None or right is None or result is None:
            payload["reason"] = "required_node_absent"
        else:
            rows = self.conn.execute(
                "SELECT * FROM edges INDEXED BY idx_edges_result "
                "WHERE result_node_id=? AND op=? AND left_node_id=? "
                "AND right_node_id=? ORDER BY stage,edge_id",
                (result["node_id"], op, left["node_id"], right["node_id"]),
            ).fetchall()
            eligible = [row for row in rows if all(
                n["q"] == 1 and n["p"] >= 1 and n["confirmed_stage"] is not None
                and n["confirmed_stage"] <= row["stage"] <= self.stage
                for n in (left, right)
            )]
            if eligible:
                payload.update(present=True, edge=dict(eligible[0]),
                               occurrence_count=len(eligible), operands_confirmed=True)
            else:
                payload["reason"] = ("unconfirmed_operand_in_saved_edge" if rows
                                     else "no_retained_edge")
        self.edges[key] = payload
        return payload


def motif(edges: dict[str, dict[str, Any]], names: list[str], agrees: bool) -> dict[str, Any]:
    missing = [name for name in names if not edges[name]["present"]]
    complete = not missing and agrees
    return {
        "witness_names": names, "algebraic_agreement": agrees,
        "complete": complete, "missing_witnesses": missing,
        "completion_stage": max(edges[n]["edge"]["stage"] for n in names) if complete else None,
        "present_witnesses": len(names)-len(missing),
    }


def audit_triple(reader: WitnessReader, t: Triple) -> dict[str, Any]:
    x, y, r = t.x, t.y, t.r
    u, v = r-x, r+x
    edges = {
        "square_x": reader.edge(x, "*", x),
        "square_y": reader.edge(y, "*", y),
        "square_r": reader.edge(r, "*", r),
        "square_sum": reader.edge(x*x, "+", y*y),
        "difference": reader.edge(r, "-", x),
        "sum": reader.edge(r, "+", x),
        "factor_product": reader.edge(u, "*", v),
        "ratio_left": reader.edge(u, "/", y),
        "ratio_right": reader.edge(y, "/", v),
        "normalized_x": reader.edge(x, "/", r),
        "normalized_y": reader.edge(y, "/", r),
    }
    squares = ["square_x", "square_y", "square_r"]
    factor_base = squares + ["difference", "sum"]
    hit = x*x + y*y == r*r
    return {
        "triple": t.values(), "primitive": t.primitive,
        "algebraic_hit": hit, "parameter": str(t.parameter),
        "shell_discrepancy": x*x+y*y-r*r,
        "factor_discrepancy": u*v-y*y,
        "quotient_discrepancy": str(Fraction(u, y)-Fraction(y, v)),
        "direct": motif(edges, squares+["square_sum"], hit),
        "factor": motif(edges, factor_base+["factor_product"], u*v == y*y),
        "quotient": motif(edges, factor_base+["ratio_left", "ratio_right"],
                          Fraction(u, y) == Fraction(y, v)),
        "predicted_stages": {"direct": y*y, "factor": v, "quotient": v},
        "edges": edges,
        "neighborhood_query": f"python moo_graph_query.py --node {r*r} --neighborhood --pretty",
    }


def summarize(rows: list[dict[str, Any]], stage: int, previous_stage: int) -> dict[str, Any]:
    result: dict[str, Any] = {"rows": len(rows)}
    for name in ("direct", "factor", "quotient"):
        complete = [r for r in rows if r[name]["complete"]]
        result[name] = {
            "complete": len(complete),
            "primitive_complete": sum(r["primitive"] for r in complete),
            "new_since_previous_stage": sum(r[name]["completion_stage"] > previous_stage for r in complete),
            "new_primitive_since_previous_stage": sum(
                r["primitive"] and r[name]["completion_stage"] > previous_stage for r in complete),
            "partial": sum(not r[name]["complete"] and r[name]["present_witnesses"] > 0 for r in rows),
            "absent": sum(r[name]["present_witnesses"] == 0 for r in rows),
            "size_prediction_mismatches": sum(
                r[name]["complete"] != (r["predicted_stages"][name] <= stage)
                or (r[name]["complete"] and r[name]["completion_stage"] != r["predicted_stages"][name])
                for r in rows),
        }
    result["factor_before_direct_available"] = sum(r["factor"]["complete"] and not r["direct"]["complete"] for r in rows)
    result["primitive_composite_radius_factor_hits"] = [r["triple"] for r in rows
        if r["primitive"] and r["factor"]["complete"] and not is_prime(r["triple"][2])]
    result["direct_node_presence_without_motif"] = sum(
        all(r["edges"][n]["result_node"] is not None for n in ("square_x", "square_y", "square_r"))
        and not r["direct"]["complete"] for r in rows)
    return result


def scan_corpus(path: Path, triples: set[Triple], cap: int, previous_stage: int) -> dict[str, Any]:
    before = file_sha256(path)
    with closing(connect_readonly(path)) as conn:
        alignment = require_strict_alignment(conn)
        reader = WitnessReader(conn)
        config = json.loads(conn.execute("SELECT value FROM meta WHERE key='config_json'").fetchone()[0])
        rows = [audit_triple(reader, t) for t in sorted(triples, key=lambda z:(z.r,z.x,z.y))]
        controls = [audit_triple(reader, Triple(t.x, t.y, t.r+1)) for t in sorted(triples)
                    if t.r+1 <= cap]
        summary = summarize(rows, reader.stage, previous_stage)
        summary["nearby_nonhit_controls"] = len(controls)
        summary["nonhit_false_positives"] = sum(any(r[n]["complete"] for n in
            ("direct", "factor", "quotient")) for r in controls)
        summary["missing_edge_reasons"] = dict(Counter(e.get("reason") for r in rows
            for e in r["edges"].values() if not e["present"]))
        # Inspect square/product collisions directly in the saved graph, without
        # first supplying a shell-triple list to the SQL query.
        collisions: set[Triple] = set()
        collision_witnesses = []
        for y in range(1, min(cap-1, reader.stage)+1):
            square = reader.edge(y, "*", y)
            if not square["present"]:
                continue
            for row in conn.execute(
                "SELECT e.edge_id,e.stage,l.p AS u,l.q AS uq,l.confirmed_stage AS uc,"
                "r.p AS v,r.q AS vq,r.confirmed_stage AS vc FROM edges e "
                "INDEXED BY idx_edges_result JOIN nodes l ON l.node_id=e.left_node_id "
                "JOIN nodes r ON r.node_id=e.right_node_id "
                "WHERE e.result_node_id=? AND e.op='*' AND l.p<r.p",
                (square["result_node"]["node_id"],),
            ):
                u, v = row["u"], row["v"]
                if (row["uq"] != 1 or row["vq"] != 1 or u < 1
                    or row["uc"] is None or row["vc"] is None
                    or max(row["uc"], row["vc"]) > row["stage"]
                    or row["stage"] > reader.stage or (u+v) % 2):
                    continue
                candidate = Triple((v-u)//2, y, (v+u)//2)
                if 0 < candidate.x <= y and candidate.r <= cap:
                    collisions.add(candidate)
                    collision_witnesses.append({"triple": candidate.values(),
                        "product_edge_id": row["edge_id"], "product_stage": row["stage"],
                        "square_edge_id": square["edge"]["edge_id"]})
        complete_factor = {Triple(*r["triple"]) for r in rows if r["factor"]["complete"]}
        summary["graph_first_collision_candidates"] = len(collisions)
        summary["graph_first_collision_only_without_complete_motif"] = [t.values() for t in sorted(collisions-complete_factor)]
        summary["complete_factor_missed_by_collision_scan"] = [t.values() for t in sorted(complete_factor-collisions)]
        stage = reader.stage
    after = file_sha256(path)
    if before != after:
        raise AssertionError(f"Input corpus changed during audit: {path}")
    return {
        "path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": before,
        "sha256_after": after, "unchanged": True, "stage": stage,
        "config": config, "alignment": alignment, "summary": summary,
        "rows": rows, "controls": controls, "graph_first_collisions": collision_witnesses,
    }


def build_report(cap: int, corpus_specs: list[tuple[Path, int]]) -> dict[str, Any]:
    start = time.perf_counter()
    triples, pair_trials = blind_pairs(cap)
    factors = square_factor_pairs(cap)
    euclid, parameter_trials = euclid_selector(cap)
    tree = berggren_selector(cap)
    primitives = {t for t in triples if t.primitive}
    if not (triples == factors == euclid and primitives == set(tree)):
        raise AssertionError("Independent candidate selectors disagree")
    if any(from_parameter(t.parameter) != t for t in primitives):
        raise AssertionError("Normalized rational parameter did not recover a shape")
    reports = []
    for path, previous in corpus_specs:
        print(f"Auditing {path.name} ...", flush=True)
        report = scan_corpus(path, triples, cap, previous)
        print(json.dumps({"corpus": path.name, "summary": report["summary"]}), flush=True)
        reports.append(report)
    return {
        "tool_name": "moo_shell_branch_search", "schema_version": "1",
        "evidence_layers": ["external_exact_selectors", "strict_retained_witnesses"],
        "claim_status": "bounded_observation", "radius_cap": cap,
        "interpretation_limits": [
            "Rational shells are a provisional proxy; no equal-area squaring or pi construction.",
            "Parametrization and factor identity are classical; graph timing is compared to operand size.",
            "Later-stage validation is nested, not independent sampling.",
            "No new graph edges or speculative-operand operations are introduced.",
            "A factor certificate is not a retained square/addition closure.",
            "Primitive shapes and scale copies are counted separately.",
            "Candidate-loop counts are algorithm-specific, not a universal complexity bound.",
        ],
        "candidate_search": {
            "blind_pair_trials": pair_trials, "euclid_parameter_trials": parameter_trials,
            "integer_hits": len(triples), "primitive_shapes": len(primitives),
            "all_selectors_agree": True, "parameter_roundtrip_all_primitive": True,
            "one_A_ray_shapes": sum(set(word) <= {"A"} for word in tree.values()),
            "tree_addresses": [{"triple": t.values(), "address": word or "root"}
                for t, word in sorted(tree.items(), key=lambda kv:(kv[0].r,kv[0].x))],
        },
        "gap_predictions": [{"t": str(t), "triple": from_parameter(t).values()}
                            for t in (Fraction(1,2),Fraction(3,5),Fraction(2,3),Fraction(4,7),Fraction(5,8))],
        "corpora": reports,
        "source_hashes": {name: file_sha256(PROJECT_ROOT / name) for name in
                          ('moo/shell_branch_search.py', 'moo/research_utils.py')},
        "design_sha256": file_sha256(PROJECT_ROOT / "research/geometry/SHELL_SQUARE_BRANCH_SEARCH_20260911.pre.md"),
        "elapsed_seconds": time.perf_counter()-start,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-radius", type=int, default=500)
    parser.add_argument("--write", type=Path, required=True)
    args = parser.parse_args()
    if args.max_radius < 5:
        parser.error("--max-radius must be >= 5")
    if args.write.exists():
        parser.error("Refusing to overwrite an existing report")
    base = PROJECT_ROOT / "out/experiments"
    specs = [(base / "pascal_edge_probe_u300.sqlite", 0),
             (base / "gauss/strict_stage_u850_holdout_v1.sqlite", 300),
             (base / "pascal_cubic_scale_u1000.sqlite", 850),
             (base / "circle_as_one_u80.sqlite", 0)]
    result = build_report(args.max_radius, specs)
    args.write.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also protects against a concurrent writer.
    with args.write.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"Saved {args.write}; elapsed {result['elapsed_seconds']:.2f}s")


if __name__ == "__main__":
    main()
