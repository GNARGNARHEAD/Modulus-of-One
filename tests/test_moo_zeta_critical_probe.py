from __future__ import annotations

import cmath
import math
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Union

from moo.graph_corpus import (
    GraphCorpus,
    GraphCorpusConfig,
    normalize_key,
    strict_stage_expected_candidate_events,
)
from moo.zeta_critical_probe import (
    _nearest_phase_fraction,
    _target_evaluation,
    hasse_source_weights,
    hasse_zeta,
    recommended_hasse_terms,
    zeta_critical_probe,
)


Value = Union[int, Fraction]


def _create_fixture(path: Path) -> None:
    config = GraphCorpusConfig(
        generator="strict_stage_moo_graph",
        max_stage=16,
        max_abs_p=1_000,
        max_abs_q=1_000,
        max_abs_value=1_000.0,
        retain_confirmed_edges=True,
    )
    with GraphCorpus(path) as corpus:
        corpus.init_schema()
        corpus.ensure_config(config)

        def node_id(value: Value, *, first_stage: int) -> int:
            fraction = value if isinstance(value, Fraction) else Fraction(value, 1)
            key = normalize_key(fraction.numerator, fraction.denominator)
            found, _ = corpus.ensure_node(key, first_stage=first_stage)
            return found

        def core(value: int) -> int:
            found, _ = corpus.ensure_core_integer(value)
            return found

        def add_edge(
            left: int,
            op: str,
            right: int,
            result: Value,
            *,
            stage: int,
        ) -> None:
            corpus.insert_edge(
                stage=int(stage),
                op=str(op),
                left_node_id=core(left),
                right_node_id=core(right),
                result_node_id=node_id(result, first_stage=int(stage)),
            )

        for value in range(1, 17):
            core(value)
        # A positive integer may land before its own core-confirmation stage.
        node_id(20, first_stage=10)
        corpus.insert_edge(
            stage=1,
            op="seed",
            left_node_id=None,
            right_node_id=None,
            result_node_id=core(1),
        )

        # Direct rational landings used by the source and quarter-turn audits.
        for denominator in range(1, 17):
            add_edge(
                1,
                "/",
                denominator,
                Fraction(1, denominator),
                stage=denominator,
            )
        add_edge(3, "/", 4, Fraction(3, 4), stage=4)
        add_edge(1, "-", 1, 0, stage=1)

        # Exact directed Pascal scaffold through row 4.
        for left, right, result in [
            (1, 1, 2),
            (1, 2, 3),
            (1, 3, 4),
            (3, 3, 6),
        ]:
            stage = max(left, right)
            add_edge(left, "+", right, result, stage=stage)
            if left != right:
                add_edge(right, "+", left, result, stage=stage)

        for stage in range(1, 17):
            corpus.record_stage(
                stage=stage,
                candidate_events=strict_stage_expected_candidate_events(stage),
                retained_events=0,
                new_nodes=0,
                new_edges=0,
                elapsed_seconds=0.0,
            )


class CriticalZetaMathTests(unittest.TestCase):
    def test_regrouped_hasse_weights_are_exact(self) -> None:
        self.assertEqual(
            hasse_source_weights(3),
            (Fraction(7, 8), Fraction(-1, 2), Fraction(1, 8)),
        )

    def test_regrouped_eta_matches_direct_triangle_ordering(self) -> None:
        point = 0.5 + 3.25j
        for terms in range(1, 9):
            direct_cells = []
            for k in range(terms):
                inner = sum(
                    (
                        ((-1) ** j)
                        * math.comb(k, j)
                        * cmath.exp(-point * math.log(j + 1))
                        for j in range(k + 1)
                    ),
                    0j,
                )
                direct_cells.append(inner / (2 ** (k + 1)))
            direct_eta = sum(direct_cells, 0j)
            regrouped = hasse_zeta(point, terms)
            self.assertLess(abs(regrouped.eta - direct_eta), 2e-15)

    def test_hasse_calibrates_zeta2_and_first_zero(self) -> None:
        zeta2 = hasse_zeta(2.0 + 0.0j, 48)
        self.assertIsNotNone(zeta2.zeta)
        assert zeta2.zeta is not None
        self.assertLess(abs(zeta2.zeta - math.pi**2 / 6.0), 1e-12)

        first_zero = hasse_zeta(0.5 + 14.134725141734693j, 64)
        off_zero = hasse_zeta(0.5 + 14.144725141734693j, 64)
        self.assertIsNotNone(first_zero.zeta)
        self.assertIsNotNone(off_zero.zeta)
        assert first_zero.zeta is not None
        assert off_zero.zeta is not None
        self.assertLess(abs(first_zero.zeta), 1e-10)
        self.assertGreater(abs(off_zero.zeta), 1e-3)

    def test_trivial_zero_pole_guard_and_conjugation_controls(self) -> None:
        trivial = hasse_zeta(-2.0 + 0.0j, 48)
        self.assertIsNotNone(trivial.zeta)
        assert trivial.zeta is not None
        self.assertLess(abs(trivial.zeta), 1e-11)

        pole = hasse_zeta(1.0 + 0.0j, 48)
        self.assertIsNone(pole.zeta)
        self.assertEqual(pole.status, "zeta_pole_neighborhood_guard")

        removable = hasse_zeta(
            1.0 + (2.0 * math.pi / math.log(2.0)) * 1j,
            48,
        )
        self.assertIsNone(removable.zeta)
        self.assertEqual(
            removable.status,
            "eta_bridge_removable_singularity_guard",
        )

        point = 0.5 + 14.2j
        direct = hasse_zeta(point, 64)
        conjugate = hasse_zeta(point.conjugate(), 64)
        self.assertIsNotNone(direct.zeta)
        self.assertIsNotNone(conjugate.zeta)
        assert direct.zeta is not None
        assert conjugate.zeta is not None
        self.assertLess(abs(conjugate.zeta - direct.zeta.conjugate()), 1e-12)

    def test_empirical_preflight_rounds_up_to_eight(self) -> None:
        self.assertEqual(recommended_hasse_terms(0.0), 64)
        self.assertEqual(recommended_hasse_terms(14.134725141734693), 64)
        self.assertEqual(recommended_hasse_terms(50.0), 120)

    def test_phase_fraction_wraps_near_one_to_zero(self) -> None:
        nearest, error = _nearest_phase_fraction(0.999999999999, 80)
        self.assertEqual(nearest, Fraction(0, 1))
        self.assertLess(error, 1e-10)

    def test_small_residual_below_term_preflight_is_underresolved(self) -> None:
        target = hasse_zeta(0.5 + 49.7738324776723j, 96)
        report = _target_evaluation(
            target,
            target_kind="numerical_candidate",
            target_label=None,
            near_zero_tolerance=1e-10,
            stability_tolerance=1e-12,
            ladder_terms=[64, 80, 88, 92, 96],
        )
        self.assertFalse(
            report["numeric_preflight"][
                "configured_meets_empirical_recommendation"
            ]
        )
        self.assertEqual(
            report["zero_diagnostic"]["classification"],
            "underresolved_small_residual_below_empirical_term_recommendation",
        )


class CriticalZetaCorpusTests(unittest.TestCase):
    def test_report_separates_quarter_turn_sources_and_external_complex_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = zeta_critical_probe(
                db_path=db_path,
                sigma=0.5,
                t=14.134725141734693,
                hasse_terms=8,
                ladder_terms=[4, 8],
                control_delta=0.01,
                near_zero_tolerance=1.0,
                target_kind="user_supplied_reference_zero",
                target_label="test calibration",
                pascal_max_row=4,
                phase_max_denominator=32,
                phase_sample_terms=4,
                edge_limit=4,
            )

        self.assertEqual(report["corpus"]["alignment"]["status"], "pass")
        quarter = report["complex_calibration"]["quarter_turn"]
        self.assertTrue(quarter["graph_node"]["present"])
        self.assertEqual(quarter["graph_node"]["status"], "speculative")
        self.assertEqual(quarter["graph_node"]["outgoing_edge_count"], 0)
        self.assertTrue(quarter["direct_quotient_witness"]["present"])

        i_squared = report["complex_calibration"]["i_squared_calibration"]
        self.assertFalse(i_squared["graph_phase_addition"]["present"])
        self.assertEqual(
            i_squared["graph_phase_addition"]["blocker"],
            "operand_not_positive_spine",
        )
        contrast = report["complex_calibration"]["rational_multiplication_contrast"]
        self.assertFalse(contrast["graph"]["present"])
        self.assertEqual(contrast["graph"]["blocker"], "operand_not_positive_spine")

        sources = report["graph_source_audit"]
        self.assertEqual(sources["summary"]["index_nodes"]["present_distinct_nodes"], 8)
        self.assertEqual(
            sources["summary"]["reciprocal_precursor_edges"]
            ["complete_directed_occurrences"],
            8,
        )
        self.assertFalse(sources["complex_term_is_runtime_node"])
        self.assertFalse(
            sources["rows"][1]["phase_projection"]["selection_is_graph_native"]
        )
        self.assertEqual(
            sources["summary"]["sampled_phase_approximation_nodes"][
                "evidence_status"
            ],
            "visualization_only_not_construction_evidence",
        )

        pascal = report["pascal_coefficient_audit"]
        self.assertEqual(pascal["summary"]["relation_occurrences"], 6)
        self.assertEqual(pascal["summary"]["complete_directed_occurrences"], 6)
        self.assertEqual(pascal["required_max_pascal_row"], 7)
        self.assertEqual(pascal["audited_max_pascal_row"], 4)
        self.assertEqual(
            pascal["coverage_status"],
            "named_interior_recurrence_sample_only",
        )
        self.assertIn("lower_sigma", report["controls"]["nearby_cross_controls"])
        self.assertFalse(report["controls"]["calibration_suite"]["passes"])
        self.assertEqual(
            report["target_evaluation"]["reference_coordinate"]["status"],
            "caller_supplied_not_independently_verified_by_probe",
        )
        self.assertFalse(
            report["target_evaluation"]["zero_diagnostic"]["is_certified_zero"]
        )
        self.assertFalse(report["method"]["ordinary_euler_product_used_in_strip"])

    def test_missing_late_sources_remain_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = zeta_critical_probe(
                db_path=db_path,
                sigma=2.0,
                t=0.0,
                hasse_terms=20,
                ladder_terms=[12, 16, 20],
                control_delta=0.01,
                near_zero_tolerance=1e-10,
                target_kind="control",
                target_label="zeta2",
                pascal_max_row=4,
                phase_max_denominator=32,
                phase_sample_terms=4,
                edge_limit=4,
            )

        summary = report["graph_source_audit"]["summary"]
        self.assertEqual(summary["index_nodes"]["missing_distinct_nodes"], 3)
        self.assertEqual(
            summary["index_nodes"]["present_not_operand_ready_distinct_nodes"],
            1,
        )
        self.assertEqual(
            summary["reciprocal_precursor_edges"]["missing_node_relation_occurrences"],
            4,
        )

    def test_edge_limit_and_soft_caps_are_enforced(self) -> None:
        with self.assertRaisesRegex(ValueError, "edge_limit must be >= 2"):
            zeta_critical_probe(
                db_path=Path("unused.sqlite"),
                sigma=0.5,
                t=14.0,
                hasse_terms=8,
                ladder_terms=[4, 8],
                control_delta=0.01,
                near_zero_tolerance=1e-8,
                target_kind="numerical_candidate",
                target_label=None,
                pascal_max_row=4,
                phase_max_denominator=32,
                phase_sample_terms=4,
                edge_limit=1,
            )

        with self.assertRaisesRegex(ValueError, "pass --full-scan"):
            zeta_critical_probe(
                db_path=Path("unused.sqlite"),
                sigma=0.5,
                t=14.0,
                hasse_terms=65,
                ladder_terms=[64, 65],
                control_delta=0.01,
                near_zero_tolerance=1e-8,
                target_kind="numerical_candidate",
                target_label=None,
                pascal_max_row=4,
                phase_max_denominator=32,
                phase_sample_terms=4,
                edge_limit=4,
            )

        with self.assertRaisesRegex(ValueError, "require 0 < sigma < 1"):
            zeta_critical_probe(
                db_path=Path("unused.sqlite"),
                sigma=2.0,
                t=14.0,
                hasse_terms=8,
                ladder_terms=[4, 8],
                control_delta=0.01,
                near_zero_tolerance=1e-8,
                target_kind="numerical_candidate",
                target_label=None,
                pascal_max_row=4,
                phase_max_denominator=32,
                phase_sample_terms=4,
                edge_limit=4,
                full_scan=True,
            )

        with self.assertRaisesRegex(ValueError, "requires target_label"):
            zeta_critical_probe(
                db_path=Path("unused.sqlite"),
                sigma=0.5,
                t=14.0,
                hasse_terms=8,
                ladder_terms=[4, 8],
                control_delta=0.01,
                near_zero_tolerance=1e-8,
                target_kind="user_supplied_reference_zero",
                target_label=None,
                pascal_max_row=4,
                phase_max_denominator=32,
                phase_sample_terms=4,
                edge_limit=4,
            )

        with self.assertRaisesRegex(ValueError, "SQLite signed-integer"):
            zeta_critical_probe(
                db_path=Path("unused.sqlite"),
                sigma=0.5,
                t=14.0,
                hasse_terms=8,
                ladder_terms=[4, 8],
                control_delta=0.01,
                near_zero_tolerance=1e-8,
                target_kind="numerical_candidate",
                target_label=None,
                pascal_max_row=67,
                phase_max_denominator=32,
                phase_sample_terms=4,
                edge_limit=4,
                full_scan=True,
            )


if __name__ == "__main__":
    unittest.main()
