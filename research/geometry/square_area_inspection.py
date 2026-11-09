"""Small, reproducible construction-route calibration; not a new branch law.

Run from the repository root:
  python3 -B research/geometry/square_area_inspection.py --output-dir PATH

Creates a NEW U160 positive-spine corpus and saves all selected witnesses.
Euclidean coordinates, tangent lines, containment and area are external
interpretations. Rational squares remain included; their integer encodings
are distinguished from literal fractional self-product edges.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from fractions import Fraction as F
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from moo.research_utils import connect_readonly, file_sha256, require_strict_alignment
from moo.shell_branch_search import WitnessReader
from moo.strict_stage_moo import build_strict_stage_graph


CASES = (("base", 3, 4, 5), ("rescaled", 6, 8, 10),
         ("exchanged", 4, 3, 5), ("nearby_failure", 3, 4, 6))
CONFIG = dict(max_stage=160, max_abs_p=25600, max_abs_q=25600,
              max_abs_value=25600, max_edges=None, time_limit_seconds=None,
              commit_every=40, retain_confirmed_edges=True, verbose=False)


def shoelace(vertices):
    return abs(sum((x*v-y*u for (x, y), (u, v) in
                    zip(vertices, vertices[1:]+vertices[:1])), F(0)))/2


def audit(reader, name, p, q, r):
    groups = {}

    def group(label, requests):
        records = {role: reader.edge(a, op, b)
                   for role, (a, op, b) in requests.items()}
        assert all(row["present"] and row["operands_confirmed"]
                   for row in records.values())
        for row in records.values():
            assert row["edge"]["stage"] == max(row["a"], row["b"])
        groups[label] = dict(
            records=records,
            completion_stage=max(row["edge"]["stage"] for row in records.values()),
        )

    group("square_relation", {
        "p_square": (p, "*", p), "q_square": (q, "*", q),
        "r_square": (r, "*", r), "sum": (p*p, "+", q*q),
        "x": (p, "/", r), "y": (q, "/", r),
        "x_square_encoding": (p*p, "/", r*r),
        "y_square_encoding": (q*q, "/", r*r),
        "sum_encoding": (p*p+q*q, "/", r*r),
    })
    agrees = p*p+q*q == r*r
    relation = groups["square_relation"]["records"]
    shared_node = (relation["sum"]["edge"]["result_node_id"] ==
                   relation["r_square"]["edge"]["result_node_id"])
    assert shared_node == agrees
    result = dict(name=name, source=[p,q,r], coordinates=[str(F(p,r)), str(F(q,r))],
                  rational_squares=[str(F(p*p,r*r)), str(F(q*q,r*r))],
                  normalized_sum=str(F(p*p+q*q,r*r)), shared_square_node=shared_node,
                  groups=groups, area_interpretation="not_applicable")
    if not agrees:
        return result

    # All runtime operands are positive integers; fractions are final outputs.
    # For normalized vertices (1,0), (p/r,q/r), (0,1), reflected around the
    # origin, the inner polygon area is 2(p+q)/r.
    group("inner_area_encoding", {
        "two": (1, "+", 1), "sum": (p, "+", q),
        "numerator": (2, "*", p+q), "area": (2*(p+q), "/", r),
    })
    # Consecutive tangents meet at (1,(r-p)/q) and ((r-q)/p,1).
    # Using p^2+q^2=r^2, their outer polygon area is 4r(p+q-r)/(pq).
    group("outer_area_encoding", {
        "two": (1, "+", 1), "four": (2, "*", 2),
        "sum": (p, "+", q), "excess": (p+q, "-", r),
        "four_r": (4, "*", r), "numerator": (4*r, "*", p+q-r),
        "denominator": (p, "*", q),
        "area": (4*r*(p+q-r), "/", p*q),
    })
    inner = F(2*(p+q), r)
    outer = F(4*r*(p+q-r), p*q)
    inner_vertices = [(F(0), F(0)), (F(1), F(0)),
                      (F(p,r), F(q,r)), (F(0), F(1))]
    outer_vertices = [(F(0), F(0)), (F(1), F(0)),
                      (F(1), F(r-p,q)), (F(r-q,p), F(1)), (F(0), F(1))]
    assert 4*shoelace(inner_vertices) == inner
    assert 4*shoelace(outer_vertices) == outer
    assert F(p,r)+F(q,r)*F(r-p,q) == 1
    assert F(p,r)*F(r-q,p)+F(q,r) == 1
    assert inner < outer
    result.update(area_interpretation="external_unit_disk_bounds",
                  lower=str(inner), upper=str(outer), width=str(outer-inner),
                  quarter_inner_vertices=[[str(x),str(y)] for x,y in inner_vertices],
                  quarter_outer_vertices=[[str(x),str(y)] for x,y in outer_vertices],
                  complete_inspection_stage=max(g["completion_stage"] for g in groups.values()))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    db = out / "current_u160.sqlite"
    design = dict(
        evidence_layer="external_probe", claim_status="observation",
        scope="Fixed worked-example calibration; no new invariant or general branch claim.",
        cases=CASES, config=CONFIG,
        selection="Known small shell, common rescaling, exchanged legs, nearby nonshell.",
        prediction="Equivalent representations have identical normalized areas but route-dependent stages.",
        controls="Require a shared square node; reject (3,4,6) before interpreting bounds.",
        holdout="None: these fixed examples calibrate the inspection, not a predictive claim.",
        primary_metric="Completeness and earliest stage of each specified witness bundle.",
        failure_rule="Any missing or inadmissible witness, wrong shared-node test, or disagreement with shoelace fails this encoding.",
        limits=["No intrinsic MoO geometry, area measure, or completed irrational is defined.",
                "Cleared-denominator witnesses are not fractional self-product edges.",
                "Readiness is route-specific; no minimal construction-cost claim.",
                "No pi, trigonometry, or irrational constant is a numerical input."],
        source_hashes={str(path.relative_to(ROOT)): file_sha256(path) for path in
                       (Path(__file__), ROOT/'moo/strict_stage_moo.py', ROOT/'moo/graph_corpus.py',
                        ROOT/'moo/research_utils.py', ROOT/'moo/shell_branch_search.py')},
    )
    (out/"design.json").write_text(json.dumps(design, indent=2)+"\n")
    build = build_strict_stage_graph(db_path=db, **CONFIG)
    before = file_sha256(db)
    with closing(connect_readonly(db)) as con:
        alignment = require_strict_alignment(con)
        reader = WitnessReader(con)
        cases = [audit(reader, *case) for case in CASES]
        seed = dict(con.execute("SELECT * FROM edges WHERE op='seed'").fetchone())
        # Preserve the counted spine to ground every requested integer operand.
        spine = [reader.edge(n, "+", 1) for n in range(1, CONFIG["max_stage"])]
        assert all(row["present"] for row in spine)
        integer_one = reader.node(F(1))
    after = file_sha256(db)
    assert before == after
    assert all(c["lower"] == "14/5" and c["upper"] == "10/3" for c in cases[:3])
    assert cases[3]["normalized_sum"] == "25/36" and not cases[3]["shared_square_node"]
    assert cases[0]["complete_inspection_stage"] == 40
    assert cases[1]["complete_inspection_stage"] == 160
    report = dict(design=design, graph_corpus=str(db), graph_sha256=after,
                  build=build, alignment=alignment, cases=cases,
                  grounding=dict(seed=seed, one=integer_one, positive_spine=spine),
                  checks="Exact independent shoelace, tangent equations, shared nodes, operand readiness, representation comparison and input immutability passed.")
    (out/"report.json").write_text(json.dumps(report, indent=2)+"\n")
    for case in cases:
        print(case["name"], case["rational_squares"], case["normalized_sum"],
              case.get("lower"), case.get("upper"), case.get("complete_inspection_stage"))
    print("Report:", out/"report.json")


if __name__ == "__main__":
    main()
