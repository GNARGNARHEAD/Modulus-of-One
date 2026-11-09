"""Inspect three selected pair-power families through the existing profiles.

This is a fixed worked comparison, not a branch-discovery engine. Each new index
uses the same source, bounds, and rules; only the ordered seed changes. Existing
composition probes inspect every split i+j=n through n=4, including alternatives
to sequential multiplication by the seed. Independent SQLite audits check the
saved index evidence. No corpus or existing output is overwritten.
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

from moo.node_profiles import build_index, find_members, load_association, load_certificate
from moo.profile_certificates import compare_certificates
from moo.research_utils import connect_readonly, file_sha256
from moo.shell_composition_probe import Case, WitnessReader, audit_case
from research.geometry.audit_node_profile_snapshot import audit as audit_snapshot

SEEDS = ((4, 3, 5), (3, 4, 5), (8, 6, 10))


def support_summary(certificate: dict) -> dict:
    support = certificate["support"]
    return {
        "ref": certificate["ref"], "criterion": certificate["criterion"],
        **{key: support[key] for key in ("status", "first_supported_stage",
                                       "local_first_supported_stage", "blockers")},
        "dependencies": support["dependencies"],
        "requests": support["requests"],
    }


def inspect(source: Path, index_dir: Path) -> dict:
    if index_dir.exists():
        raise ValueError(f"Choose a new index directory: {index_dir}")
    before = file_sha256(source)
    families, audits = [], []
    with closing(connect_readonly(source)) as conn:
        reader = WitnessReader(conn)
        if reader.stage != 576:
            raise ValueError("This fixed inspection uses the saved U576 calibration")
        for seed in SEEDS:
            key = ",".join(map(str, seed))
            index = index_dir / f"seed_{key.replace(',', '_')}.sqlite"
            built = build_index(source, index, spiral_seed=seed, spiral_steps=4)
            independently_checked = audit_snapshot(source, index)
            if independently_checked["errors"]:
                raise ValueError(f"Independent snapshot audit failed: {index}")
            audits.append(independently_checked)
            steps = []
            for n in range(1, 5):
                association = load_association(index, f"spiral:{key}:{n}")
                triple = tuple(int(association["parameters"][v]) for v in ("x", "y", "r"))
                shell_ref = "shell:" + ",".join(map(str, triple)) + "#literal"
                steps.append({
                    "iteration": n, "triple": list(triple),
                    "normalized_observation": [str(Fraction(v, triple[2])) for v in triple[:2]],
                    "lineage": support_summary(association["certificates"][0]),
                    "direct_shell": support_summary(load_certificate(index, shell_ref)),
                })
            splits = []
            for n in range(2, 5):
                for left_n in range(1, n):
                    right_n = n - left_n
                    case = Case(f"{key}:power_{left_n}_times_power_{right_n}",
                                tuple(steps[left_n - 1]["triple"]),
                                tuple(steps[right_n - 1]["triple"]))
                    result = audit_case(reader, case)
                    if list(result["target"]) != steps[n - 1]["triple"]:
                        raise ValueError("Composition does not reach the claimed power state")
                    splits.append({"target_iteration": n, "split": [left_n, right_n], **result})
            queries = [find_members(index, ["square:result", "spiral:radius"], by_stage=t)
                       for t in (15, 16, 64, 96, 576)]
            queries.append(find_members(index, ["square:result", "spiral:radius"]))
            shared_radius = compare_certificates(
                index, f"square:{seed[2]}#literal", f"spiral:{key}:2#scalar_lineage")
            families.append({"seed": list(seed), "index": str(index.resolve()),
                             "manifest": built["manifest"], "steps": steps,
                             "composition_splits": splits, "square_radius_queries": queries,
                             "second_radius_shared_evidence": shared_radius})

        primary = Path(families[0]["index"])
        scalar_joins = []
        for stage in (16, 400, 576):
            query = find_members(primary, ["shell:radius", "spiral:radius"], by_stage=stage)
            matches = query["matches"].get("25", [])
            shells, spirals = [], []
            for match in matches:
                association = load_association(primary, match["association_id"])
                row = {"id": association["id"], "triple": [association["parameters"][v]
                                                             for v in ("x", "y", "r")]}
                (shells if association["family"] == "shell" else spirals).append(row)
            scalar_joins.append({
                "stage": stage, "query": query, "inspected_value": "25",
                "same_configuration_pairs": [[shell["id"], spiral["id"]]
                    for shell in shells for spiral in spirals if shell["triple"] == spiral["triple"]],
            })
        chains = []
        for roots in (("2", "4", "16"), ("1/2", "1/4", "1/16")):
            chain = []
            for root in roots:
                association = load_association(primary, f"square:{root}")
                chain.append({"parameters": association["parameters"],
                              "support": association["support"],
                              "supported_constructions": [
                                  {"ref": c["ref"], "criterion": c["criterion"]}
                                  for c in association["certificates"]
                                  if c["support"]["status"] == "witnessed"]})
            chains.append(chain)
        requests = reader.requests
    if file_sha256(source) != before:
        raise RuntimeError("Source changed during inspection")
    return {
        "report_version": "node_profile_inspection.v1",
        "scope": "Three fixed seeds, four mathematical power states each; one unchanged U576 source. Unsupported states remain external candidates.",
        "source": {"path": str(source.resolve()), "sha256": before, "unchanged": True},
        "script_sha256": file_sha256(Path(__file__)), "families": families,
        "independent_snapshot_audits": audits, "composition_requests": requests,
        "scalar_join_comparisons": scalar_joins, "square_chain_examples": chains,
        "square_bridges": {
            "selected": find_members(primary, ["square:result", "square:root"]),
            "witnessed": find_members(primary, ["square:result", "square:root"], witnessed_only=True),
        },
        "interpretation": {
            "lineage": "Seed direct shell plus successive scalar transitions. Joint availability, not a chronological execution trace.",
            "splits": "All ordered i+j=n through n=4. source_composition also requires both DIRECT source shells; its stage may exceed the linked-lineage stage.",
            "prediction": "predicted_stage_with_wide_retention is arithmetic operand readiness, not a witness beyond the source checkpoint.",
            "selection": "Missing selected lineage support does not exclude another construction of the same state. A scalar join does not identify a shared configuration.",
            "discovery": "This worked comparison explains known identities and operand rules; it establishes no new geometric or timing law.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--index-dir", type=Path, required=True)
    parser.add_argument("--write", type=Path, required=True)
    args = parser.parse_args()
    if args.write.exists():
        parser.error("Refusing to overwrite report: " + str(args.write))
    result = inspect(args.db, args.index_dir)
    args.write.parent.mkdir(parents=True, exist_ok=True)
    with args.write.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    for family in result["families"]:
        print(f"Seed {family['seed']}")
        for step in family["steps"]:
            lineage = step["lineage"]
            print(step["iteration"], step["triple"], lineage["status"],
                  lineage["first_supported_stage"], lineage["blockers"])
    print("Report:", args.write)


if __name__ == "__main__":
    main()
