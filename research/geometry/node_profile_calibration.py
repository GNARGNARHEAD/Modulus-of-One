"""Re-audit the fixed node-profile examples against an unchanged U576 source.

Build a fresh current index with moo_node_profiles.py first. This script checks its
source/rule hashes, named certificate stages, and every materialized edge used
by the selected profiles, then writes a NEW report. It does not rebuild a corpus.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from fractions import Fraction
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from moo.node_profiles import (
    VERSION, compare_profiles, find_members, index_manifest, load_certificate,
    node_profile, verify_source,
)
from moo.profile_certificates import compare_certificates
from moo.research_utils import connect_readonly, file_sha256


VALUES = ("3", "9", "25", "625", "3/5", "9/25", "16/25", "-44")
EXPECTED_STAGES = {
    "square:3/5#integer_ratio": 25,
    "shell:3/5,4/5,1#normalize:3,4,5": 25,
    "shell:3/5,4/5,1#normalize:6,8,10": 100,
    "square:25#literal": 25,
    "square:25#route:shell_factored": 25,
    "square:25#route:shell_expanded_paired": 337,
    "square:25#route:shell_expanded_left": 544,
    "square:25#route:shell_composed_norm": 576,
    "square:9#route:generic_factored": 9,
    "square:9#route:generic_expanded_paired": 53,
    "square:9#route:generic_expanded_left": 77,
    "spiral:4,3,5:2#scalar_lineage": 16,
    "spiral:4,3,5:3#scalar_lineage": 96,
}
COMPARISONS = (
    ("square:3/5#integer_ratio", "shell:3/5,4/5,1#normalize:3,4,5"),
    ("shell:3/5,4/5,1#normalize:3,4,5", "shell:3/5,4/5,1#normalize:6,8,10"),
    ("square:25#route:shell_expanded_paired", "square:25#route:shell_expanded_left"),
)


def audit(db_path: Path, index_path: Path) -> dict:
    manifest = index_manifest(index_path)
    if manifest["schema_version"] != VERSION or manifest["source"]["checkpoint"] != 576:
        raise ValueError("This fixed calibration requires a current index at U576")
    verify_source(index_path, db_path)
    for group in ("source_hashes", "research_source_hashes"):
        for name, expected in manifest[group].items():
            if file_sha256(ROOT / name) != expected:
                raise ValueError(f"Index rule/source changed; build a fresh index: {name}")
    before = file_sha256(db_path)
    profiles = [node_profile(index_path, value, details=True) for value in VALUES]
    certificates = {}

    def include(certificate):
        if certificate["ref"] in certificates:
            return
        certificates[certificate["ref"]] = certificate
        for dependency in certificate["support"]["dependencies"]:
            include(load_certificate(index_path, dependency["ref"]))

    for profile in profiles:
        for association in profile["associations"]:
            for certificate in association["certificates"]:
                include(certificate)

    observed_stages = {}
    for reference, expected in EXPECTED_STAGES.items():
        certificate = load_certificate(index_path, reference)
        assert certificate["support"]["status"] == "witnessed", reference
        observed = certificate["support"]["first_supported_stage"]
        assert observed == expected, (reference, observed, expected)
        observed_stages[reference] = observed
    assert load_certificate(index_path, "square:3/5#literal")["support"]["status"] == "unwitnessed"
    assert load_certificate(index_path, "spiral:4,3,5:4#scalar_lineage")["support"]["status"] != "witnessed"

    edge_ids, request_keys, readback_edges = set(), set(), {}
    reference_count = 0
    with closing(connect_readonly(db_path)) as conn:
        for certificate in certificates.values():
            for request in certificate["support"]["requests"]:
                a, b, result = map(Fraction, (request["left"], request["right"], request["result"]))
                op = request["op"]
                actual = {"+": lambda: a+b, "-": lambda: a-b,
                          "*": lambda: a*b, "/": lambda: a/b}[op]()
                assert actual == result
                request_keys.add((str(a), op, str(b), str(result)))
                refs = request["edge_refs"]
                assert bool(refs) == request["witnessed"]
                for ref in refs:
                    row = conn.execute("""SELECT e.stage,e.op,
                        l.node_id,l.p,l.q,l.confirmed_stage,
                        r.node_id,r.p,r.q,r.confirmed_stage,
                        o.node_id,o.p,o.q FROM edges e
                        JOIN nodes l ON l.node_id=e.left_node_id
                        JOIN nodes r ON r.node_id=e.right_node_id
                        JOIN nodes o ON o.node_id=e.result_node_id
                        WHERE e.edge_id=?""", (ref["edge_id"],)).fetchone()
                    assert row is not None
                    assert row[0] == ref["stage"] <= 576 and row[1] == op
                    assert Fraction(row[3], row[4]) == a
                    assert Fraction(row[7], row[8]) == b
                    assert Fraction(row[11], row[12]) == result
                    assert row[4] == row[8] == 1 and min(row[3], row[7]) >= 1
                    assert row[5] <= row[0] and row[9] <= row[0]
                    readback_edges[ref["edge_id"]] = {
                        "edge_id": ref["edge_id"], "stage": row[0], "op": op,
                        "left_node_id": row[2], "right_node_id": row[6], "result_node_id": row[10],
                        "left": str(a), "right": str(b), "result": str(result),
                    }
                    edge_ids.add(ref["edge_id"])
                    reference_count += 1
    verify_source(index_path, db_path)
    assert file_sha256(db_path) == before
    comparisons = [compare_certificates(index_path, *pair) for pair in COMPARISONS]
    assert comparisons[0]["counts"]["shared_directed_requests"] == 4
    assert comparisons[2]["declared_ac_expression_equal"] is True
    profile_comparisons = []
    for values in (("3", "9"), ("25", "625")):
        comparison = compare_profiles(index_path, values, witnessed_only=True)
        comparison.pop("profiles")
        profile_comparisons.append(comparison)
    return {
        "report_version": "moo_node_profiles.report.v3",
        "scope": "Fixed integration calibration; no new branch law or independent holdout.",
        "manifest": manifest, "index_path": str(index_path.resolve()),
        "calibration_source_sha256": file_sha256(Path(__file__)),
        "profiles": profiles, "profile_comparisons": profile_comparisons,
        "certificate_comparisons": comparisons,
        "readback_edges": [readback_edges[key] for key in sorted(readback_edges)],
        "witnessed_intersection": find_members(index_path, ["square", "shell", "spiral"], witnessed_only=True),
        "validation": {
            "observed_named_stages": observed_stages,
            "selected_certificates_and_dependencies": len(certificates),
            "distinct_arithmetic_requests_checked": len(request_keys),
            "materialized_edge_references_checked": reference_count,
            "distinct_materialized_edge_occurrences_checked": len(edge_ids),
            "method": "Direct SQL readback of every materialized reference in the selected profiles and certificate dependencies, plus exact arithmetic for witnessed and unwitnessed requests.",
            "source_unchanged": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--write", type=Path, required=True)
    args = parser.parse_args()
    if args.write.exists():
        parser.error(f"Refusing to overwrite {args.write}")
    report = audit(args.db, args.index)
    args.write.parent.mkdir(parents=True, exist_ok=True)
    with args.write.open("x") as output:
        json.dump(report, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps({"report": str(args.write), "validation": report["validation"]}, indent=2))


if __name__ == "__main__":
    main()
