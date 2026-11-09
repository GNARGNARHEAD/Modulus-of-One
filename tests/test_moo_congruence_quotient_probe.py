from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from moo.congruence_quotient_probe import (
    congruence_quotient_report,
    gauss_totient,
    least_residue,
    parse_positive_csv,
)
from moo.strict_stage_moo import build_strict_stage_graph


def _build_fixture(path: Path, max_stage: int = 3) -> None:
    build_strict_stage_graph(
        db_path=path,
        max_stage=max_stage,
        max_abs_p=10_000,
        max_abs_q=10_000,
        max_abs_value=10_000.0,
        max_edges=None,
        time_limit_seconds=None,
        commit_every=1,
        retain_confirmed_edges=True,
        verbose=False,
    )


class CongruenceQuotientProbeTests(unittest.TestCase):
    def test_modulus_one_boundary_helpers(self) -> None:
        self.assertEqual(least_residue(-19, 1), 0)
        self.assertEqual(least_residue(-1, 5), 4)
        self.assertEqual(gauss_totient(1), 1)
        self.assertEqual(gauss_totient(6), 2)
        self.assertEqual(parse_positive_csv("3,1,3,2", field_name="x"), [1, 2, 3])

    def test_u3_report_preserves_edges_inside_one_class(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "u3.sqlite"
            _build_fixture(db_path)
            report = congruence_quotient_report(
                db_path=db_path,
                moduli=[1, 2, 3],
                checkpoints=[1, 2, 3],
                sample_limit=3,
                include_checksums=False,
                argv=[],
            )

        focus = report["focus_checkpoint"]
        all_integer = focus["domains"]["all_integer_shadow"]
        confirmed = focus["domains"]["confirmed_positive_spine"]
        mod_one = next(
            row for row in all_integer["projections"] if row["modulus"] == 1
        )

        self.assertEqual(all_integer["source"]["edge_occurrence_count"], 33)
        self.assertEqual(
            all_integer["source"]["edge_occurrences_by_operation"],
            {"seed": 1, "+": 9, "-": 9, "*": 9, "/": 5},
        )
        self.assertEqual(focus["excluded_rational_result_edges"]["count"], 4)
        self.assertEqual(mod_one["occupied_residue_count"], 1)
        self.assertEqual(mod_one["edge_occurrences_retained_after_projection"], 33)
        self.assertEqual(mod_one["distinct_nonseed_operation_decorated_signatures"], 4)
        self.assertEqual(mod_one["distinct_unlabeled_nonseed_topologies"], 1)
        self.assertEqual(mod_one["algebra_validation"]["failure_count"], 0)

        self.assertEqual(confirmed["source"]["node_count"], 3)
        self.assertEqual(confirmed["source"]["edge_occurrence_count"], 17)
        self.assertEqual(confirmed["completeness"]["status"], "pass")
        self.assertEqual(all_integer["completeness"]["status"], "pass")

    def test_first_fan_collapses_values_but_retains_status_and_operations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "u3.sqlite"
            _build_fixture(db_path)
            report = congruence_quotient_report(
                db_path=db_path,
                moduli=[1, 2],
                checkpoints=[3],
                sample_limit=4,
                include_checksums=False,
                argv=[],
            )

        fan = report["first_operator_fan"]
        self.assertEqual(fan["source_result_values"], ["2", "0", "1", "1"])
        self.assertEqual(fan["projected_result_residues_mod_1"], [0, 0, 0, 0])
        self.assertEqual(
            [row["op"] for row in fan["edge_occurrences"]], ["+", "-", "*", "/"]
        )
        self.assertEqual(
            fan["edge_occurrences"][0]["result_status_at_event"],
            "speculative_positive_at_event",
        )
        self.assertEqual(
            fan["edge_occurrences"][1]["result_status_at_checkpoint"],
            "relational_nonpositive",
        )

    def test_art_39_and_domain_boundary_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "u2.sqlite"
            _build_fixture(db_path, max_stage=2)
            report = congruence_quotient_report(
                db_path=db_path,
                moduli=[1, 2],
                checkpoints=[2],
                sample_limit=2,
                include_checksums=False,
                argv=[],
            )

        phi_one = report["arithmetic_boundary_checks"]["totient_endpoint"]["records"][0]
        self.assertEqual(phi_one["strictly_below_count"], 0)
        self.assertEqual(phi_one["not_greater_than_count"], 1)
        self.assertTrue(phi_one["divisor_sum_identity_holds"])
        phase = report["domain_separation"]["fractional_phase_mod_1"]
        self.assertEqual(phase["classes"], "infinitely_many")
        self.assertFalse(phase["general_multiplication_compatible"])


if __name__ == "__main__":
    unittest.main()
