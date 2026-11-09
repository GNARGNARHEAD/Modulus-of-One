"""Exact external area bounds and a read-only audit of their MoO precursors.

No target constant or trigonometric evaluation enters the computation.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import time
from contextlib import closing
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from moo.paths import PROJECT_ROOT
from typing import Any

from moo.research_utils import connect_readonly, file_sha256, require_strict_alignment
from moo.shell_branch_search import WitnessReader


ROUND_DENOMINATOR = 10**24


def decimal_text(value: Fraction) -> str:
    with localcontext() as ctx:
        ctx.prec = 32
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def interval_record(lo: Fraction, hi: Fraction) -> dict[str, Any]:
    return {"lower": str(lo), "upper": str(hi),
            "lower_decimal": decimal_text(lo), "upper_decimal": decimal_text(hi),
            "width": str(hi-lo), "width_decimal": decimal_text(hi-lo)}


def polygon_bounds(n: int, denominator: int = ROUND_DENOMINATOR) -> tuple[Fraction, Fraction]:
    if n < 1 or denominator < 1:
        raise ValueError("Positive subdivision and rounding denominators required")
    lower_units = upper_units = 0
    for k in range(n):
        d = n*n + k*(k+1)
        lower_units += (4*n*d*denominator) // (d*d+n*n)
        upper_units += (4*n*denominator+d-1) // d
    return Fraction(lower_units, denominator), Fraction(upper_units, denominator)


def grid_bounds(n: int) -> tuple[Fraction, Fraction]:
    if n < 1:
        raise ValueError("Positive grid size required")
    lower = sum(math.isqrt(n*n-i*i) for i in range(1, n+1))
    upper = sum(min(n, math.isqrt(n*n-i*i)+1) for i in range(n))
    return Fraction(4*lower, n*n), Fraction(4*upper, n*n)


def floor_sqrt(value: Fraction) -> int:
    if value < 0:
        raise ValueError("Negative square-root input")
    return math.isqrt(value.numerator // value.denominator)


def ceil_sqrt(value: Fraction) -> int:
    root = floor_sqrt(value)
    return root if root*root == value else root+1


def side_bounds(lo: Fraction, hi: Fraction, denominator: int = 10**12) -> tuple[Fraction, Fraction]:
    return (Fraction(floor_sqrt(lo*denominator*denominator), denominator),
            Fraction(ceil_sqrt(hi*denominator*denominator), denominator))


def compatible_ratios(lo: Fraction, hi: Fraction, max_denominator: int) -> list[Fraction]:
    """Exhaustive within 1 <= side <= 2; no floating-point decision."""
    found = []
    for q in range(1, max_denominator+1):
        start = max(q, ceil_sqrt(lo*q*q))
        stop = min(2*q, floor_sqrt(hi*q*q))
        for p in range(start, stop+1):
            if math.gcd(p, q) == 1:
                found.append(Fraction(p, q))
    return sorted(found)


def classify_square(side: Fraction, lo: Fraction, hi: Fraction) -> str:
    square = side*side
    if square < lo:
        return "too_small"
    if square > hi:
        return "too_large"
    if lo == hi == square:
        return "exact"
    return "unresolved"


def bracket_path(lo: Fraction, hi: Fraction, denominator_cap: int = 10000) -> dict[str, Any]:
    if not 1 <= lo <= hi <= 4:
        raise ValueError("This bracket implementation requires area within [1,4]")
    left, right = Fraction(1), Fraction(2)
    steps: list[dict[str, Any]] = []
    for endpoint in (left, right):
        if lo == hi == endpoint*endpoint:
            return {"steps": [], "stop": "exact", "exact_ratio": str(endpoint),
                    "left": str(endpoint), "right": str(endpoint)}
    while left.denominator + right.denominator <= denominator_cap:
        candidate = Fraction(left.numerator+right.numerator,
                             left.denominator+right.denominator)
        status = classify_square(candidate, lo, hi)
        row = {"side": str(candidate), "square": str(candidate*candidate), "status": status}
        steps.append(row)
        if status in ("unresolved", "exact"):
            terminal = {"steps": steps, "stop": status, "pending_ratio": str(candidate),
                        "left": str(left), "right": str(right)}
            if status == "exact":
                terminal["exact_ratio"] = str(candidate)
            return terminal
        if status == "too_small":
            left = candidate
        else:
            right = candidate
        row.update(left=str(left), right=str(right))
    return {"steps": steps, "stop": "denominator_cap", "left": str(left), "right": str(right)}


def edge_ref(reader: WitnessReader, a: int, op: str, b: int) -> str:
    reader.edge(a, op, b)
    return f"{a}|{op}|{b}"


def source_vertex(reader: WitnessReader, n: int, k: int) -> dict[str, Any]:
    if not 0 < k < n:
        raise ValueError("Interior rational vertices only")
    x, y, r = n*n-k*k, 2*n*k, n*n+k*k
    named = {
        "n_square": (n, "*", n), "k_square": (k, "*", k),
        "x_numerator": (n*n, "-", k*k), "nk": (n, "*", k),
        "y_numerator": (n*k, "+", n*k), "radius": (n*n, "+", k*k),
        "coordinate_x": (x, "/", r), "coordinate_y": (y, "/", r),
    }
    refs = {name: edge_ref(reader, *spec) for name, spec in named.items()}
    records = [reader.edges[spec] for spec in named.values()]
    complete = all(e["present"] for e in records)
    return {"n": n, "k": k, "parameter": str(Fraction(k,n)),
            "integer_components": [x,y,r], "edge_refs": refs, "complete": complete,
            "predicted_stage": r,
            "completion_stage": max(e["edge"]["stage"] for e in records) if complete else None,
            "prediction_match": complete == (r <= reader.stage)
                and (not complete or max(e["edge"]["stage"] for e in records) == r)}


def ratio_source(reader: WitnessReader, h: Fraction) -> dict[str, Any]:
    p, q = h.numerator, h.denominator
    named = {"length_ratio": (p,"/",q), "p_square": (p,"*",p),
             "q_square": (q,"*",q), "square_area_ratio": (p*p,"/",q*q)}
    return {"ratio": str(h), "edge_refs": {name:edge_ref(reader,*spec) for name,spec in named.items()},
            "length_landing_present": reader.edges[named["length_ratio"]]["present"],
            "square_area_landing_present": reader.edges[named["square_area_ratio"]]["present"],
            "ratio_operand_permitted": q == 1 and p <= reader.stage}


def intended_fraction_edge(reader: WitnessReader, a: Fraction, op: str, b: Fraction) -> dict[str, Any]:
    """Inspect a proposed rational-operand edge; never insert or execute it in MoO."""
    if op == "+":
        result = a+b
    elif op == "*":
        result = a*b
    else:
        raise ValueError(op)
    left, right, out = reader.node(a), reader.node(b), reader.node(result)
    operand_allowed = all(v.denominator == 1 and 1 <= v <= reader.stage for v in (a,b))
    saved = None
    if left and right and out:
        row = reader.conn.execute(
            "SELECT edge_id,stage FROM edges INDEXED BY idx_edges_result "
            "WHERE result_node_id=? AND left_node_id=? AND op=? AND right_node_id=? "
            "ORDER BY stage,edge_id LIMIT 1",
            (out["node_id"],left["node_id"],op,right["node_id"]),
        ).fetchone()
        saved = dict(row) if row is not None else None
    landing = edge_ref(reader,result.numerator,"/",result.denominator)
    return {"expression": f"{a} {op} {b} -> {result}", "operand_rule_allows": operand_allowed,
            "intended_edge_present": saved is not None, "intended_edge": saved,
            "reason": None if operand_allowed else "fractional_or_unconfirmed_operands",
            "result_node_present": out is not None, "direct_integer_quotient_ref": landing}


def export_graph(reader: WitnessReader) -> dict[str, Any]:
    nodes = {str(row["node_id"]):row for row in reader.nodes.values() if row is not None}
    edges = {}
    for (a,op,b), raw in reader.edges.items():
        row = {k:v for k,v in raw.items() if k not in ("left_node","right_node","result_node")}
        for role in ("left","right","result"):
            node = raw[f"{role}_node"]
            row[f"{role}_node_id"] = node["node_id"] if node else None
        edges[f"{a}|{op}|{b}"] = row
    return {"nodes": nodes, "edge_records": edges}


def audit_corpus(path: Path, side_ratios: list[Fraction]) -> dict[str, Any]:
    before = file_sha256(path)
    with closing(connect_readonly(path)) as conn:
        alignment = require_strict_alignment(conn)
        reader = WitnessReader(conn)
        vertices = [source_vertex(reader,n,k) for n in (2,4,8,16,32) for k in range(1,n)]
        sides = [ratio_source(reader,h) for h in side_ratios]
        intended = [
            intended_fraction_edge(reader,Fraction(8,5),"+",Fraction(6,5)),
            intended_fraction_edge(reader,Fraction(2),"+",Fraction(4,3)),
            intended_fraction_edge(reader,Fraction(4),"*",Fraction(1,2)),
            intended_fraction_edge(reader,Fraction(4),"*",Fraction(1,3)),
        ]
        result = {
            "path": str(path.resolve()), "stage": reader.stage, "alignment": alignment,
            "vertices": vertices, "side_ratios": sides, "intended_area_operations": intended,
            "summary": {"vertex_cases": len(vertices), "complete_vertex_cases": sum(r["complete"] for r in vertices),
                "vertex_size_prediction_mismatches": sum(not r["prediction_match"] for r in vertices),
                "side_ratios": len(sides), "length_landings": sum(r["length_landing_present"] for r in sides),
                "square_area_landings": sum(r["square_area_landing_present"] for r in sides),
                "intended_fraction_area_edges": sum(r["intended_edge_present"] for r in intended)},
            **export_graph(reader),
        }
    after = file_sha256(path)
    if before != after:
        raise AssertionError("Read-only input changed")
    result.update(sha256=before, sha256_after=after, unchanged=True, bytes=path.stat().st_size)
    return result


def build_report(max_n: int, candidate_cap: int, with_graph: bool) -> dict[str, Any]:
    started = time.perf_counter()
    levels: list[dict[str, Any]] = []
    lower, upper = Fraction(1), Fraction(4)
    previous_candidates: set[Fraction] | None = None
    previous_steps: list[tuple[str,str]] = []
    n = 1
    all_path_ratios: set[Fraction] = {Fraction(1),Fraction(2)}
    while n <= max_n:
        raw_lo, raw_hi = polygon_bounds(n)
        if raw_hi-raw_lo > Fraction(4,n*n)+Fraction(2*n,ROUND_DENOMINATOR):
            raise AssertionError("Outward rounding gap exceeded proved bound")
        lower, upper = max(lower,raw_lo), min(upper,raw_hi)
        candidates = compatible_ratios(lower,upper,candidate_cap)
        if previous_candidates is not None and not set(candidates) <= previous_candidates:
            raise AssertionError("Candidate rejection was not monotone")
        path = bracket_path(lower,upper)
        resolved = [(s["side"],s["status"]) for s in path["steps"] if s["status"] != "unresolved"]
        if resolved[:len(previous_steps)] != previous_steps:
            raise AssertionError("A previously certified comparison changed")
        all_path_ratios.update(Fraction(s["side"]) for s in path["steps"])
        side_lo, side_hi = side_bounds(lower,upper)
        levels.append({"n_per_quadrant": n, "polygon_sides": 4*n,
            "raw_area": interval_record(raw_lo,raw_hi), "nested_area": interval_record(lower,upper),
            "side_interval": interval_record(side_lo,side_hi),
            "compatible_count": len(candidates),
            "compatible_sample": [str(h) for h in candidates[:20]],
            "compatible_ratios": [str(h) for h in candidates],
            "excluded_since_previous": len(previous_candidates-set(candidates)) if previous_candidates is not None else None,
            "path": path})
        previous_candidates, previous_steps = set(candidates), resolved
        print(f"N={n}: compatible={len(candidates)}, side=[{decimal_text(side_lo)}, {decimal_text(side_hi)}]",flush=True)
        n *= 2
    independent = []
    for m in (32,128,512,2048,8192):
        lo,hi = grid_bounds(m)
        contains = lo <= lower <= upper <= hi
        if not contains:
            raise AssertionError("Independent grid and polygon bounds disagree")
        independent.append({"grid_n":m,"area":interval_record(lo,hi),"contains_finest_polygon_interval":contains})
    controls = {"diamond_area_2": bracket_path(Fraction(2),Fraction(2)),
                "square_area_4": bracket_path(Fraction(4),Fraction(4))}
    root = PROJECT_ROOT
    corpora = []
    if with_graph:
        for name in ("pascal_edge_probe_u300.sqlite","pascal_cubic_scale_u1000.sqlite"):
            print(f"Auditing graph {name} ...",flush=True)
            corpus = audit_corpus(root/"out/experiments"/name,sorted(all_path_ratios))
            print(json.dumps(corpus["summary"]),flush=True)
            corpora.append(corpus)
    return {
        "tool_name":"moo_circle_square_area_probe", "schema_version":"1",
        "evidence_layers":["external_exact_Euclidean_area_bounds","strict_precursor_audit"],
        "claim_status":"external_certified_bounds_with_runtime_boundary",
        "target_constant_supplied":False, "candidate_max_denominator":candidate_cap,
        "rounding_denominator":str(ROUND_DENOMINATOR), "levels":levels,
        "independent_grid_checks":independent, "controls":controls, "corpora":corpora,
        "limits":[
            "Geometry and area are declared external lenses, not derived runtime semantics.",
            "Finite bracket compatibility is not an exact equal-area hit.",
            "The area calculation and refinement remain external rational computation.",
            "Fractional nodes are not used as MoO operands.",
            "The limit and irrationality theorem are mathematical statements, not finite graph nodes.",
            "Resolved mediant decisions follow the area bounds; no new simple recurrence is established.",
        ],
        "source_hashes":{name:file_sha256(root/name) for name in
            ('moo/circle_square_area_probe.py','moo/shell_branch_search.py','moo/research_utils.py')},
        "design_sha256":file_sha256(root/"research/geometry/CIRCLE_SQUARE_AREA_BRIDGE_20260911.pre.md"),
        "elapsed_seconds":time.perf_counter()-started,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-n",type=int,default=65536)
    parser.add_argument("--max-denominator",type=int,default=1000)
    parser.add_argument("--without-graph",action="store_true")
    parser.add_argument("--write",type=Path,required=True)
    args = parser.parse_args()
    if args.max_n < 8192 or args.max_n & (args.max_n-1):
        parser.error("--max-n must be a power of two >= 8192 for the fixed grid controls")
    if args.max_denominator < 1:
        parser.error("--max-denominator must be positive")
    if args.write.exists():
        parser.error("Refusing to overwrite an existing report")
    report = build_report(args.max_n,args.max_denominator,not args.without_graph)
    args.write.parent.mkdir(parents=True,exist_ok=True)
    with args.write.open("x",encoding="utf-8") as handle:
        json.dump(report,handle,indent=2,sort_keys=True)
        handle.write("\n")
    print(f"Saved {args.write}; elapsed {report['elapsed_seconds']:.2f}s")


if __name__ == "__main__":
    main()
