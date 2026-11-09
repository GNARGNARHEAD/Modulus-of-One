from __future__ import annotations

import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Union

from moo.circle_probe import unit_shell_point
from moo.graph_corpus import GraphCorpus, GraphCorpusConfig, normalize_key
from moo.zeta_centered_inversion_probe import (
    centered_inversion_s,
    centered_inversion_u,
    centered_u,
    phase_inversion,
    ratio_w,
    zeta_centered_inversion_probe,
)


Value = Union[int, Fraction]


def _create_fixture(path: Path) -> None:
    config = GraphCorpusConfig(
        generator="strict_stage_moo_graph",
        max_stage=8,
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

        for value in range(1, 9):
            core(value)
        corpus.insert_edge(
            stage=1,
            op="seed",
            left_node_id=None,
            right_node_id=None,
            result_node_id=core(1),
        )
        for denominator in range(1, 9):
            reciprocal = Fraction(1, denominator)
            corpus.insert_edge(
                stage=denominator,
                op="/",
                left_node_id=core(1),
                right_node_id=core(denominator),
                result_node_id=node_id(reciprocal, first_stage=denominator),
            )
            x, y = unit_shell_point(Fraction(denominator, 1))
            reciprocal_x, reciprocal_y = unit_shell_point(reciprocal)
            for component in (x, y, reciprocal_x, reciprocal_y, -1):
                node_id(component, first_stage=denominator)

        # Quarter-turn calibration support.
        for value in (Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), 0):
            node_id(value, first_stage=4)

        corpus.record_stage(
            stage=8,
            candidate_events=0,
            retained_events=0,
            new_nodes=0,
            new_edges=0,
            elapsed_seconds=0.0,
        )


class CenteredInversionMathTests(unittest.TestCase):
    def test_centered_and_ratio_actions(self) -> None:
        source = 0.5 + 14.134725141734693j
        image = centered_inversion_s(source)
        self.assertLess(abs(centered_inversion_s(image) - source), 1e-12)
        self.assertLess(
            abs(centered_u(image) - centered_inversion_u(centered_u(source))),
            1e-12,
        )
        self.assertLess(abs(ratio_w(image) + 1.0 / ratio_w(source)), 1e-12)
        u = centered_u(source)
        self.assertLess(abs(ratio_w(source) - (u - 1.0) / (u + 1.0)), 1e-12)
        self.assertAlmostEqual(source.imag * image.imag, 0.25, places=14)

    def test_fixed_points_and_phase_action(self) -> None:
        for point in (0.5 + 0.5j, 0.5 - 0.5j):
            self.assertLess(abs(centered_inversion_s(point) - point), 1e-15)
        self.assertEqual(phase_inversion(Fraction(0)), Fraction(1, 2))
        self.assertEqual(phase_inversion(Fraction(1, 4)), Fraction(1, 4))
        self.assertEqual(phase_inversion(Fraction(1, 2)), Fraction(0))
        self.assertEqual(phase_inversion(Fraction(3, 4)), Fraction(3, 4))

    def test_rational_shell_reciprocity_is_exact(self) -> None:
        for integer in range(1, 13):
            x, y = unit_shell_point(Fraction(integer, 1))
            reciprocal_x, reciprocal_y = unit_shell_point(Fraction(1, integer))
            self.assertEqual(reciprocal_x, -x)
            self.assertEqual(reciprocal_y, y)

    def test_singular_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            centered_inversion_s(0.5)
        with self.assertRaises(ValueError):
            centered_inversion_u(0.0)
        with self.assertRaises(ValueError):
            ratio_w(0.0)


class CenteredInversionCorpusTests(unittest.TestCase):
    def test_report_separates_exact_geometry_graph_and_zeta_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = zeta_centered_inversion_probe(
                db_path=db_path,
                t=14.134725141734693,
                hasse_terms=64,
                ladder_terms=[48, 56, 60, 64],
                near_zero_tolerance=1e-10,
                stability_tolerance=1e-12,
                shell_max_integer=4,
                edge_limit=4,
            )

        self.assertEqual(report["corpus"]["alignment"]["status"], "pass")
        self.assertEqual(
            report["exact_centered_geometry"]["classification"],
            "exact_centered_geometry_verified",
        )
        domains = report["unit_shell_domain_separation"]
        self.assertFalse(domains["set_relation"]["sets_equal"])
        self.assertFalse(domains["q_mod_z_phase_model"]["group_homomorphism"])
        self.assertIn(
            "normalized external w/U(1) plane",
            domains["q_mod_z_phase_model"]["coordinate_status"],
        )
        self.assertEqual(
            domains["set_relation"]["exact_intersection"],
            ["1", "i", "-1", "-i"],
        )
        self.assertFalse(
            domains["rational_coordinate_shell"]["example"]["root_of_unity"]
        )
        self.assertIn(
            "chosen real determinant-one representative",
            report["exact_centered_geometry"]["matrix_lift"][
                "representative_status"
            ],
        )

        graph = report["graph_shell_audit"]
        self.assertTrue(graph["summary"]["all_external_shell_identities_exact"])
        self.assertEqual(
            graph["summary"]["direct_unit_fraction_edges"][
                "complete_directed_occurrences"
            ],
            4,
        )
        self.assertEqual(
            graph["summary"]["reverse_parameter_edges"][
                "present_relation_occurrences"
            ],
            1,
        )
        self.assertEqual(
            graph["summary"]["reverse_parameter_edges"]["top_level_blockers"],
            {"operand_not_positive_spine": 3},
        )
        self.assertEqual(
            graph["summary"][
                "direct_witness_and_both_shell_points_present_count"
            ],
            4,
        )
        self.assertFalse(
            graph["summary"]["co_presence_is_transformation_witness"]
        )
        self.assertEqual(
            graph["interaction_classification"],
            "external_projection_only_insufficient_repeated_graph_witnesses",
        )

        zeta = report["zeta_evaluations"]
        self.assertEqual(
            zeta["pointwise_classification"],
            "supplied_near_zero_not_preserved_by_centered_inversion",
        )
        self.assertFalse(zeta["zeta_inversion_symmetry_supported_at_supplied_point"])
        self.assertTrue(
            zeta["functional_reflection_on_critical_line_control"]["passes"]
        )
        self.assertTrue(zeta["centered_inversion_image_cutoff_stable"])
        self.assertLess(
            zeta["points"]["source"]["diagnostic"]["absolute_residual"],
            1e-10,
        )
        self.assertTrue(
            zeta["points"]["source"]["numeric_preflight"][
                "configured_meets_empirical_recommendation"
            ]
        )
        self.assertIsNone(zeta["points"]["source"]["zeta"]["phase_turns"])
        self.assertGreater(
            zeta["points"]["centered_inversion_image"]["diagnostic"][
                "absolute_residual"
            ],
            1.0,
        )
        self.assertEqual(
            report["analytic_obstruction"]["classification"],
            "global_fixed_radius_zero_set_symmetry_analytically_obstructed",
        )
        self.assertIn(
            "new representation",
            report["analytic_obstruction"]["transformed_function_caveat"][
                "interpretation"
            ],
        )
        self.assertEqual(
            report["summary"]["formal_branch_status"],
            "candidate_centered_reciprocal_shell_lens_not_promoted",
        )


if __name__ == "__main__":
    unittest.main()
