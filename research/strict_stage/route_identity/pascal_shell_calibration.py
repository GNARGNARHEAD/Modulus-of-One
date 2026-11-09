"""Reproduce the fixed 2026-09-22 calibration without modifying its inputs."""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import closing
from fractions import Fraction
from itertools import combinations
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from moo.graph_evidence import GraphEvidence
from moo.research_utils import connect_readonly, file_sha256, require_strict_alignment
from moo.route_identity_probe import (
    RouteCertificate,
    RouteStep,
    compare_route_certificates,
    evaluate_route_certificate,
)


def step(name, left, op, right, result):
    return RouteStep(name, (left, 1), op, (right, 1), (result, 1))


def certificates():
    routes = []
    for family, x, y in (("shell", 16, 9), ("generic", 7, 2)):
        base = ()
        premises = ()
        if family == "shell":
            base = (step("a2", 4, "*", 4, 16), step("b2", 3, "*", 3, 9))
            premises = (
                step("radius_square", 5, "*", 5, 25),
                step("source_agreement", 16, "+", 9, 25),
            )
        xx, xy, yy = x*x, x*y, y*y
        target = (x+y)**2
        monomials = (
            step("xx", x, "*", x, xx),
            step("xy", x, "*", y, xy),
            step("yy", y, "*", y, yy),
        )
        schemas = {
            "factored": (
                step("sum", x, "+", y, x+y),
                step("square", x+y, "*", x+y, target),
            ),
            "expanded_left": monomials + (
                step("sum1", xx, "+", xy, xx+xy),
                step("sum2", xx+xy, "+", xy, xx+2*xy),
                step("sum3", xx+2*xy, "+", yy, target),
            ),
            "expanded_paired": monomials + (
                step("extremes", xx, "+", yy, xx+yy),
                step("middle", xy, "+", xy, 2*xy),
                step("sum", xx+yy, "+", 2*xy, target),
            ),
        }
        if family == "shell":
            schemas["composed_norm"] = (
                step("cross", 4, "*", 3, 12),
                step("real", 16, "-", 9, 7),
                step("imag", 12, "+", 12, 24),
                step("real_square", 7, "*", 7, 49),
                step("imag_square", 24, "*", 24, 576),
                step("norm", 49, "+", 576, 625),
            )
        for name, schema in schemas.items():
            extra = (step("cross_reversed", 3, "*", 4, 12),) if name == "composed_norm" else ()
            routes.append(RouteCertificate(
                route_id=f"{family}_{name}",
                external_family=family,
                description=f"Fixed {name} certificate at X={x}, Y={y}.",
                target=(target, 1),
                steps=base+schema,
                premise_steps=premises+extra,
                dependency_tags=(f"{family}_binomial_norm_identity",),
                interpretation_limit="Declared dependent certificate; repeated uses share witnesses.",
            ))
    return routes


def multiply(z, w):
    a, b = z
    c, d = w
    return a*c-b*d, a*d+b*c


def algebra_check():
    cases = 0
    for t in (Fraction(0), Fraction(1, 2), Fraction(3, 4), Fraction(-2, 3)):
        a, b = (1-t*t)/(1+t*t), 2*t/(1+t*t)
        actual = (Fraction(1), Fraction(0))
        for n in range(9):
            real = sum((-1)**j * comb(n, 2*j) * a**(n-2*j) * b**(2*j)
                       for j in range(n//2+1))
            imag = sum((-1)**j * comb(n, 2*j+1) * a**(n-2*j-1) * b**(2*j+1)
                       for j in range((n-1)//2+1))
            assert (real, imag) == actual
            assert real*real+imag*imag == 1
            weights = [comb(n, k)*a**(2*(n-k))*b**(2*k) for k in range(n+1)]
            assert all(weight >= 0 for weight in weights) and sum(weights) == 1
            actual = multiply(actual, (a, b))
            cases += 1
    p = Fraction(9, 25)
    assert 4*p*(1-p) == Fraction(576, 625)
    assert 2*p*(1-p) == Fraction(288, 625)
    return {"exact_parameter_exponent_cases": cases, "all_passed": True,
            "squared_composed_second_coordinate": "576/625",
            "binomial_middle_weight": "288/625"}


def raw_readback(conn, evaluated, extras):
    checked = set()
    requests = []
    for route, payload in evaluated:
        for request, measured in zip((*route.steps, *route.premise_steps), payload["edges"]):
            requests.append((request.left, request.op, request.right, request.result,
                             measured["specified_direction"]["edge_refs"]))
    for payload in extras.values():
        requests.append((tuple(payload["left"]["key"]), payload["op"],
                         tuple(payload["right"]["key"]), tuple(payload["result"]["key"]),
                         payload["edge_refs"]))
    for left, op, right, result, refs in requests:
        for ref in refs:
            row = conn.execute("SELECT * FROM edges WHERE edge_id=?", (ref["edge_id"],)).fetchone()
            assert row is not None and row["op"] == op and row["stage"] == ref["stage"]
            for role, expected in (("left", left), ("right", right), ("result", result)):
                node = conn.execute("SELECT * FROM nodes WHERE node_id=?",
                                    (row[f"{role}_node_id"],)).fetchone()
                assert (node["p"], node["q"]) == expected
                assert node["first_stage"] <= row["stage"]
                if role != "result":
                    assert node["q"] == 1 and 1 <= node["p"] <= row["stage"]
                    assert node["confirmed_stage"] == node["p"]
            a, b = Fraction(*left), Fraction(*right)
            value = {"+": lambda: a+b, "-": lambda: a-b,
                     "*": lambda: a*b, "/": lambda: a/b}[op]()
            assert value == Fraction(*result)
            checked.add(ref["edge_id"])
    return {"distinct_directed_edge_records_checked": len(checked), "all_passed": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", type=Path, required=True)
    args = parser.parse_args()
    if args.write.exists():
        raise SystemExit(f"Refusing to overwrite {args.write}")
    design = Path(__file__).with_name("PASCAL_SHELL_20260922.pre.md")
    manifest_path = ROOT / "research/geometry/results/2026-09-20-shell-composition-current-manifest-v1.json"
    manifest = json.loads(manifest_path.read_text())
    routes = certificates()
    predictions = dict(zip((route.route_id for route in routes), (25, 544, 337, 576, 9, 77, 53)))
    report = {
        "experiment_id": "pascal_shell_certificate_20260922_v1",
        "scope": "Fixed calibration; no new holdout, salience, or runtime claim.",
        "source_hashes": {str(path.relative_to(ROOT)): file_sha256(path) for path in (
            Path(__file__), design, manifest_path, ROOT/'moo/route_identity_probe.py',
            ROOT/'moo/graph_evidence.py', ROOT/'moo/graph_corpus.py', ROOT/'moo/research_utils.py')},
        "external_algebra_checks": algebra_check(),
        "wide_stage_predictions": predictions,
        "route_comparisons": [compare_route_certificates(a, b) for a, b in combinations(routes, 2)
                              if a.external_family == b.external_family],
        "inputs": [],
    }
    for source in manifest["inputs"]:
        path = ROOT / source["path"]
        before = file_sha256(path)
        if before != source["sha256"]:
            raise SystemExit(f"Input hash mismatch: {path}")
        with closing(connect_readonly(path)) as conn:
            alignment = require_strict_alignment(conn)
            evidence = GraphEvidence(conn)
            checkpoint = evidence.complete_corpus_stage
            evaluated = [(route, evaluate_route_certificate(
                evidence, route, as_of_stage=checkpoint, edge_ref_limit=8)) for route in routes]
            extras = {
                "return_to_one": evidence.edge_witness(left=625, op="/", right=625, result=1),
                "literal_rational_square": evidence.edge_witness(
                    left=Fraction(4, 5), op="*", right=Fraction(4, 5), result=Fraction(16, 25)),
            }
            readback = raw_readback(conn, evaluated, extras)
        after = file_sha256(path)
        assert before == after
        wide = source["name"] == "wide_u576"
        matches = {route.route_id: (
            payload["graph_support"]["earliest_complete_stage"] == predictions[route.route_id]
            if wide else not payload["graph_support"]["visible_as_of_stage"])
            for route, payload in evaluated}
        report["inputs"].append({
            "path": source["path"], "sha256_before": before, "sha256_after": after,
            "checkpoint": checkpoint, "alignment": alignment,
            "prediction_matches": matches, "routes": [payload for _, payload in evaluated],
            "boundary_requests": extras, "raw_sql_readback": readback,
        })
    args.write.parent.mkdir(parents=True, exist_ok=True)
    with args.write.open("x") as output:
        json.dump(report, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps({"report": str(args.write), "algebra": report["external_algebra_checks"],
                      "prediction_matches": [entry["prediction_matches"] for entry in report["inputs"]]}, indent=2))


if __name__ == "__main__":
    main()
