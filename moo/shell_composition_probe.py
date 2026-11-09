"""Audit ordered shell compositions in immutable positive-spine graph corpora."""
from __future__ import annotations

import argparse
import json
import math
import shlex
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

ROOT = PROJECT_ROOT
DESIGN = ROOT / "research/geometry/SHELL_COMPOSITION_20260920.pre.md"
Triple = tuple[int, int, int]
Request = tuple[int, str, int]


@dataclass(frozen=True)
class Case:
    name: str
    left: Triple
    right: Triple


CASES = (
    Case("positive_double", (4, 3, 5), (4, 3, 5)),
    Case("positive_mixed", (4, 3, 5), (12, 5, 13)),
    Case("signed_output", (3, 4, 5), (3, 4, 5)),
    Case("axis_output", (3, 4, 5), (4, 3, 5)),
    Case("inverse_input", (3, 4, 5), (3, -4, 5)),
    Case("identity_input", (1, 0, 1), (4, 3, 5)),
    Case("scaled_double", (8, 6, 10), (8, 6, 10)),
    Case("non_shell_control", (4, 3, 6), (4, 3, 5)),
)

# Exact existing inputs, bound to out/experiments/CORPUS_INVENTORY.md.
CORPORA = (
    ("primary", "out/experiments/pascal_edge_probe_u300.sqlite",
     "3d23228ea2a1926918d49bbdc89d9f7bf85ecfe4729ec96c7bd6e9f97e54b097"),
    ("later_stage_validation", "out/experiments/gauss/strict_stage_u850_holdout_v1.sqlite",
     "cf3d1dd7a67dbd6772647dac7c746e09267e6e4c3d888f53b05c6e4073565162"),
    ("retention_control", "out/experiments/circle_as_one_u80.sqlite",
     "796e043087eee8908c840d21f1c14235310c0093e816927bbab8374fbd0d4780"),
)


def compose(left: Triple, right: Triple) -> Triple:
    a, b, r = left
    c, d, s = right
    if r <= 0 or s <= 0:
        raise ValueError("Radii must be positive")
    return a*c-b*d, a*d+b*c, r*s


def homogeneous(m: int, n: int) -> Triple:
    if m == n == 0:
        raise ValueError("The homogeneous pair cannot be zero")
    return m*m-n*n, 2*m*n, m*m+n*n


def normalized(t: Triple) -> tuple[Fraction, Fraction]:
    a, b, r = t
    if r <= 0:
        raise ValueError("Radius must be positive")
    return Fraction(a, r), Fraction(b, r)


def discrepancy(t: Triple) -> int:
    a, b, r = t
    return a*a+b*b-r*r


def arithmetic(a: int, op: str, b: int) -> Fraction:
    if op == "+":
        return Fraction(a+b)
    if op == "-":
        return Fraction(a-b)
    if op == "*":
        return Fraction(a*b)
    if op == "/":
        return Fraction(a, b)
    raise ValueError(op)


class WitnessReader:
    """Literal ordered events; no sign, zero, or commutativity shortcuts."""

    def __init__(self, conn: sqlite3.Connection, checkpoint: int | None = None) -> None:
        self.conn = conn
        last = int(conn.execute("SELECT MAX(stage) FROM stages").fetchone()[0])
        self.stage = last if checkpoint is None else checkpoint
        if not 1 <= self.stage <= last:
            raise ValueError("Checkpoint must be within the saved corpus")
        self.nodes: dict[str, dict[str, Any] | None] = {}
        self.requests: dict[str, dict[str, Any]] = {}

    def node(self, value: Fraction) -> dict[str, Any] | None:
        key = str(value)
        if key not in self.nodes:
            row = self.conn.execute(
                "SELECT * FROM nodes WHERE p=? AND q=? AND first_stage<=?",
                (value.numerator, value.denominator, self.stage),
            ).fetchone()
            payload = dict(row) if row is not None else None
            if payload is not None:
                confirmed = payload["confirmed_stage"]
                payload["status_at_checkpoint"] = (
                    "confirmed" if confirmed is not None and confirmed <= self.stage
                    else "speculative")
                # first_edge_id is corpus metadata, not an extra witness at this checkpoint.
            self.nodes[key] = payload
        return self.nodes[key]

    def edge(self, a: int, op: str, b: int) -> dict[str, Any]:
        value = arithmetic(a, op, b)
        key = f"{a} {op} {b} -> {value}"
        if key in self.requests:
            return self.requests[key]
        left, right, result = [self.node(v) for v in (Fraction(a), Fraction(b), value)]
        eligible_operands = a > 0 and b > 0
        payload: dict[str, Any] = {
            "equation": key, "a": a, "op": op, "b": b, "value": str(value),
            "left_node_id": left["node_id"] if left else None,
            "right_node_id": right["node_id"] if right else None,
            "result_node_id": result["node_id"] if result else None,
            "value_visible": result is not None,
            "operand_policy_permits": eligible_operands,
            "predicted_stage_with_wide_retention": max(a, b) if eligible_operands else None,
            "present": False, "occurrences": [], "rejected_occurrences": [],
            "first_stage": None,
        }
        if not eligible_operands:
            payload["reason"] = "operand_not_positive_spine"
        elif max(a, b) > self.stage:
            payload["reason"] = "operand_beyond_checkpoint"
        elif left is None or right is None or result is None:
            payload["reason"] = "required_node_absent_at_checkpoint"
        else:
            rows = self.conn.execute(
                "SELECT * FROM edges INDEXED BY idx_edges_result "
                "WHERE result_node_id=? AND op=? AND left_node_id=? "
                "AND right_node_id=? AND stage<=? ORDER BY stage,edge_id",
                (result["node_id"], op, left["node_id"], right["node_id"], self.stage),
            ).fetchall()
            for row in rows:
                valid = all(
                    n["q"] == 1 and 1 <= n["p"] <= row["stage"]
                    and n["confirmed_stage"] is not None
                    and n["confirmed_stage"] <= row["stage"]
                    and n["first_stage"] <= row["stage"]
                    for n in (left, right)
                ) and result["first_stage"] <= row["stage"]
                payload["occurrences" if valid else "rejected_occurrences"].append(dict(row))
            if payload["occurrences"]:
                payload["present"] = True
                payload["first_stage"] = payload["occurrences"][0]["stage"]
            else:
                payload["reason"] = "invalid_saved_event" if rows else "no_retained_edge"
        self.requests[key] = payload
        return payload


def shell_requests(t: Triple) -> dict[str, Request]:
    a, b, r = t
    return {"square_a": (a, "*", a), "square_b": (b, "*", b),
            "square_r": (r, "*", r), "square_sum": (a*a, "+", b*b)}


def motif(reader: WitnessReader, requests: dict[str, Request], agrees: bool) -> dict[str, Any]:
    edges = {name: reader.edge(*request) for name, request in requests.items()}
    missing = [name for name, edge in edges.items() if not edge["present"]]
    predicted = [edge["predicted_stage_with_wide_retention"] for edge in edges.values()]
    candidate = max(predicted) if all(p is not None for p in predicted) else None
    complete = agrees and not missing
    return {
        "requests": {name: edge["equation"] for name, edge in edges.items()},
        "algebraic_agreement": agrees, "complete": complete,
        "all_requested_edges_present": not missing, "missing_roles": missing,
        "present_roles": len(edges)-len(missing),
        "distinct_requests": len({edge["equation"] for edge in edges.values()}),
        "completion_stage": max(edge["first_stage"] for edge in edges.values()) if complete else None,
        "predicted_stage_with_wide_retention": candidate,
        "predicted_complete_with_wide_retention": (
            agrees and candidate is not None and candidate <= reader.stage),
    }


def audit_case(reader: WitnessReader, case: Case) -> dict[str, Any]:
    left, right = case.left, case.right
    target = compose(left, right)
    a, b, r = left
    c, d, s = right
    parts = {
        "left_shell": shell_requests(left), "right_shell": shell_requests(right),
        "composition": {"ac": (a, "*", c), "bd": (b, "*", d),
                        "ad": (a, "*", d), "bc": (b, "*", c),
                        "difference": (a*c, "-", b*d), "sum": (a*d, "+", b*c),
                        "radius_product": (r, "*", s)},
        "target_shell": shell_requests(target),
        "target_normalization": {"x": (target[0], "/", target[2]),
                                 "y": (target[1], "/", target[2])},
    }
    agreement = {"left_shell": discrepancy(left) == 0,
                 "right_shell": discrepancy(right) == 0,
                 "composition": True, "target_shell": discrepancy(target) == 0,
                 "target_normalization": True}
    groups = {name: motif(reader, requests, agreement[name]) for name, requests in parts.items()}
    joined: dict[str, Request] = {}
    for name in ("left_shell", "right_shell", "composition"):
        joined.update({f"{name}.{role}": request for role, request in parts[name].items()})
    source_agreement = agreement["left_shell"] and agreement["right_shell"]
    groups["source_composition"] = motif(reader, joined, source_agreement)
    joined.update({f"target_shell.{role}": request for role, request in parts["target_shell"].items()})
    groups["full_closure"] = motif(reader, joined, source_agreement and agreement["target_shell"])
    return {
        "case_id": case.name, "left": left, "right": right, "target": target,
        "normalized_observations": {name: [str(v) for v in normalized(t)]
                                    for name, t in (("left", left), ("right", right), ("target", target))},
        "discrepancies": {"left": discrepancy(left), "right": discrepancy(right),
                          "target": discrepancy(target)},
        "motifs": groups,
        "interpretation": "Normalized values and the norm identity are external; request records carry graph status.",
    }


def exact_calibration() -> dict[str, Any]:
    # Independent enumeration by squared integer coordinates, not the parameter generator.
    points = {(Fraction(a, r), Fraction(b, r)) for r in range(1, 26)
              for a in range(-r, r+1) for b in range(-r, r+1) if a*a+b*b == r*r}
    for x, y in points:
        if x == -1:
            reconstructed = normalized(homogeneous(0, 1))
        else:
            t = y / (1+x)
            reconstructed = normalized(homogeneous(t.denominator, t.numerator))
        if reconstructed != (x, y):
            raise AssertionError("Parameter inverse failed independent shell enumeration")
    pairs = [(m, n) for m in range(-6, 7) for n in range(-6, 7) if math.gcd(m, n) == 1]
    for m, n in pairs:
        for p, q in pairs:
            if compose(homogeneous(m, n), homogeneous(p, q)) != homogeneous(m*p-n*q, m*q+n*p):
                raise AssertionError("Homogeneous composition disagrees")
    return {"independent_radius_cap": 25, "independent_shell_points": len(points),
            "parameter_roundtrips_pass": True, "homogeneous_pair_bound": 6,
            "composition_comparisons": len(pairs)**2, "composition_pass": True,
            "finite_endpoint": {"pair": [0, 1], "position": ["-1", "0"]},
            "scope": "Finite implementation checks; general proofs are in SHELL_COMPOSITION_BRANCH_NOTE.md."}


def scan_corpus(role: str, relative_path: str, expected_hash: str,
                checkpoint: int | None = None) -> dict[str, Any]:
    path = ROOT / relative_path
    if not path.is_file():
        raise SystemExit(f"Corpus unavailable; no substitute generated: {path}")
    before = file_sha256(path)
    if before != expected_hash:
        raise SystemExit(f"Frozen input hash mismatch: {path}")
    with closing(connect_readonly(path)) as conn:
        alignment = require_strict_alignment(conn)
        reader = WitnessReader(conn, checkpoint)
        config = json.loads(conn.execute("SELECT value FROM meta WHERE key='config_json'").fetchone()[0])
        rows = [audit_case(reader, case) for case in CASES]
        summary = {}
        for name in rows[0]["motifs"]:
            motifs = [row["motifs"][name] for row in rows]
            summary[name] = {
                "complete": sum(m["complete"] for m in motifs),
                "partial": sum(not m["complete"] and m["present_roles"] > 0 for m in motifs),
                "absent": sum(m["present_roles"] == 0 for m in motifs),
                "wide_retention_prediction_mismatches": sum(
                    m["complete"] != m["predicted_complete_with_wide_retention"]
                    or (m["complete"] and m["completion_stage"] != m["predicted_stage_with_wide_retention"])
                    for m in motifs),
            }
        summary["missing_request_reasons"] = dict(Counter(
            e["reason"] for e in reader.requests.values() if not e["present"]))
        command = shlex.join(["python3", "-B", "-m", "moo.graph_query", "--db", relative_path])
        payload = {
            "role": role, "path": relative_path, "bytes": path.stat().st_size,
            "sha256": before, "checkpoint": reader.stage, "config": config,
            "alignment": alignment, "summary": summary, "cases": rows,
            "nodes": reader.nodes, "requests": reader.requests,
            "neighborhood_queries": [f"{command} --node {v} --neighborhood --pretty"
                                     for v in ("7", "24", "25", "-7", "0", "7/25")],
        }
    after = file_sha256(path)
    if before != after:
        raise AssertionError(f"Input changed during read-only audit: {path}")
    payload.update(sha256_after=after, unchanged=True)
    return payload


def build_report(fixture_manifest: Path | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    specs = [(role, path, sha, None) for role, path, sha in CORPORA]
    manifest_data = None
    if fixture_manifest is not None:
        manifest_data = json.loads(fixture_manifest.read_text(encoding="utf-8"))
        if manifest_data["experiment_id"] != "shell_composition_20260920_current_v1":
            raise SystemExit("Unexpected current-fixture experiment ID")
        for name, expected in manifest_data["generator_source_hashes"].items():
            location = {"strict_stage_moo.py": "moo/strict_stage_moo.py",
                        "moo_graph_corpus.py": "moo/graph_corpus.py"}.get(name, name)
            if file_sha256(ROOT / location) != expected:
                raise SystemExit(f"Current-fixture generator source changed: {name}")
        specs = [(entry["role"], entry["path"], entry["sha256"], entry["checkpoint"])
                 for entry in manifest_data["observations"]]
    calibration = exact_calibration()
    corpora = []
    for role, path, expected_hash, checkpoint in specs:
        print(f"Auditing {role}: {path}", flush=True)
        corpus = scan_corpus(role, path, expected_hash, checkpoint)
        print(json.dumps({"role": role, "summary": corpus["summary"]}), flush=True)
        corpora.append(corpus)
    return {
        "tool_name": "moo_shell_composition_probe", "schema_version": "1",
        "experiment_id": ("shell_composition_20260920_current_v1" if fixture_manifest
                          else "shell_composition_20260920_v1"),
        "input_scope": "new_current_generator_calibration" if fixture_manifest else "historical_frozen_inputs",
        "fixture_manifest": manifest_data,
        "fixture_manifest_sha256": file_sha256(fixture_manifest) if fixture_manifest else None,
        "amendment_sha256": (
            file_sha256(ROOT / "research/geometry/SHELL_COMPOSITION_20260920.amendment.md")
            if fixture_manifest else None),
        "evidence_layers": ["external_probe", "strict"], "claim_status": "observation",
        "design_sha256": file_sha256(DESIGN),
        "source_hashes": {name: file_sha256(ROOT / name) for name in
                          ('moo/shell_composition_probe.py', 'moo/research_utils.py')},
        "exact_calibration": calibration, "corpora": corpora,
        "interpretation_limits": [
            "Fixed illustrative cases, not blind discovery or independent samples.",
            "Classical arithmetic closure is distinct from retained direct output-shell evidence.",
            "No signed, zero, or speculative operands are added to the runtime.",
            "Normalization preserves value comparisons, not construction identity.",
            "Wide-retention predictions need not hold in the narrow retention control.",
            "No completed circle, privileged geometry, residual timing law, or pi construction is claimed.",
        ],
        "elapsed_seconds": time.perf_counter()-started,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", type=Path, required=True)
    parser.add_argument("--current-fixtures-manifest", type=Path,
                        help="Explicitly audit new calibration fields instead of historical inputs")
    args = parser.parse_args()
    if args.write.exists():
        parser.error("Refusing to overwrite an existing report")
    report = build_report(args.current_fixtures_manifest)
    args.write.parent.mkdir(parents=True, exist_ok=True)
    with args.write.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"Saved {args.write}; elapsed {report['elapsed_seconds']:.2f}s")


if __name__ == "__main__":
    main()
