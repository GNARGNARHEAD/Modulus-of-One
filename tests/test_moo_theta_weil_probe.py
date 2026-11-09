from __future__ import annotations

import math
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Union

from moo.graph_corpus import GraphCorpus, GraphCorpusConfig, normalize_key
from moo.theta_weil_probe import (
    DEFAULT_WEIL_SCALE,
    D4_PRINCIPAL,
    _involution_pairing_fixture,
    _matrix_report,
    _theta_layer,
    jacobi_eigendecomposition,
    off_line_zero_quartet,
    theta_tail_envelope,
    theta_weil_probe,
    weil_basis_transform,
    weil_zero_side_matrix,
)


Value = Union[int, Fraction]


def _create_fixture(path: Path, *, core_max: int = 12) -> None:
    config = GraphCorpusConfig(
        generator="strict_stage_moo_graph",
        max_stage=max(12, core_max),
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
                stage=stage,
                op=op,
                left_node_id=core(left),
                right_node_id=core(right),
                result_node_id=node_id(result, first_stage=stage),
            )

        for value in range(1, core_max + 1):
            core(value)
        corpus.insert_edge(
            stage=1,
            op="seed",
            left_node_id=None,
            right_node_id=None,
            result_node_id=core(1),
        )
        add_edge(1, "-", 1, 0, stage=1)
        add_edge(2, "*", 3, 6, stage=3)
        add_edge(3, "*", 2, 6, stage=3)
        corpus.record_stage(
            stage=max(12, core_max),
            candidate_events=0,
            retained_events=0,
            new_nodes=0,
            new_edges=0,
            elapsed_seconds=0.0,
        )


def _assert_no_float(test: unittest.TestCase, value: object) -> None:
    if isinstance(value, float):
        test.fail(f"formal exact payload unexpectedly contains float {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_float(test, nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_no_float(test, nested)


class ThetaPrefixTests(unittest.TestCase):
    def test_formal_constants_channels_and_cross_terms_are_exact(self) -> None:
        layer = _theta_layer(
            max_n=6,
            theta_t=(0.5, 1.0, 2.0),
            graph_rows=[{"value": n, "present": True} for n in range(1, 7)],
        )
        formal = layer["exact_formal_theta_prefixes"]
        self.assertFalse(formal["coefficient_is_graph_derived"])
        self.assertEqual(
            [
                row["constant_term"]["unit_normalized"]["frac"]
                for row in formal["form_class_basis"]
            ],
            ["1/4", "1/2", "1/2"],
        )
        self.assertEqual(
            [row["constant_term"]["frac"] for row in formal["d20_character_basis"]],
            ["1", "0"],
        )
        _assert_no_float(self, formal)

        channels = {row["channel_id"]: row for row in formal["d20_character_basis"]}
        plus = {row["n"]: row["coefficient"] for row in channels["trivial"]["positive_index_rows"]}
        minus = {row["n"]: row["coefficient"] for row in channels["sign"]["positive_index_rows"]}
        self.assertEqual([plus[n] for n in (2, 3, 6)], [1, 2, 2])
        self.assertEqual([minus[n] for n in (2, 3, 6)], [-1, -2, 2])

        controls = layer["c2_cross_term_controls"]
        self.assertTrue(controls["all_fixtures_require_cross_terms"])
        fixtures = {row["n"]: row for row in controls["cancellation_fixtures"]}
        self.assertEqual(fixtures[2]["diagonal_only_contribution"]["frac"], "1/2")
        self.assertEqual(fixtures[2]["full_value"]["frac"], "0")
        self.assertEqual(fixtures[6]["diagonal_only_contribution"]["frac"], "2")
        self.assertEqual(fixtures[6]["full_value"]["frac"], "0")

    def test_analytic_tail_envelope_dominates_a_large_finite_subset(self) -> None:
        max_n = 10
        t = 0.5
        report = theta_tail_envelope(D4_PRINCIPAL, max_n=max_n, t=t)
        sampled_tail = math.fsum(
            math.exp(-math.pi * t * (x * x + y * y))
            for x in range(-50, 51)
            for y in range(-50, 51)
            if x * x + y * y > max_n
        )
        self.assertLessEqual(
            sampled_tail,
            report["analytic_bound_formula_value_binary64"],
        )
        self.assertTrue(report["formula_is_analytic_bound"])
        self.assertFalse(report["numeric_value_is_certified_upper_bound"])
        self.assertFalse(report["numeric_interval_is_rigorous"])

        underflow = theta_tail_envelope(D4_PRINCIPAL, max_n=10_000, t=4.0)
        self.assertTrue(underflow["binary64_evaluation_underflowed_to_zero"])
        self.assertEqual(underflow["analytic_bound_formula_value_binary64"], 0.0)
        self.assertTrue(math.isfinite(underflow["analytic_bound_log_binary64"]))
        self.assertFalse(underflow["numeric_value_is_certified_upper_bound"])

    def test_d4_transform_is_only_a_tail_calibration(self) -> None:
        layer = _theta_layer(
            max_n=20,
            theta_t=(0.25, 0.5, 1.0, 2.0, 4.0),
            graph_rows=[{"value": n, "present": True} for n in range(1, 21)],
        )
        rows = layer["d4_poisson_transform_calibration"]
        self.assertTrue(
            all(row["residual_within_tail_plus_roundoff_guard"] for row in rows)
        )
        self.assertTrue(all(not row["identity_proved_by_probe"] for row in rows))
        self.assertTrue(all(not row["rigorous_interval_check"] for row in rows))

        tighter = _theta_layer(
            max_n=200,
            theta_t=(0.25, 0.5, 1.0, 2.0, 4.0),
            graph_rows=[{"value": n, "present": True} for n in range(1, 201)],
        )["d4_poisson_transform_calibration"]
        self.assertEqual(
            sum(row["residual_within_analytic_tail_only"] for row in tighter),
            3,
        )
        self.assertTrue(
            all(row["residual_within_tail_plus_roundoff_guard"] for row in tighter)
        )
        self.assertTrue(all(not row["roundoff_guard_is_certified"] for row in tighter))


class WeilMatrixTests(unittest.TestCase):
    def test_basis_enforces_both_endpoint_moment_constraints(self) -> None:
        for degree in range(8):
            self.assertEqual(
                weil_basis_transform(degree, 0j, scale=DEFAULT_WEIL_SCALE),
                0j,
            )
            self.assertEqual(
                weil_basis_transform(degree, 1 + 0j, scale=DEFAULT_WEIL_SCALE),
                0j,
            )

    def test_jacobi_solver_finds_exact_control_inertia(self) -> None:
        eigenvalues, eigenvectors, solver = jacobi_eigendecomposition(
            [[0.0, 2.0], [2.0, 0.0]]
        )
        self.assertTrue(solver["converged"])
        self.assertAlmostEqual(eigenvalues[0], -2.0, places=12)
        self.assertAlmostEqual(eigenvalues[1], 2.0, places=12)
        self.assertAlmostEqual(
            sum(value * value for value in eigenvectors[0]),
            1.0,
            places=12,
        )

    def test_matrix_uses_the_dual_point_not_the_same_point(self) -> None:
        points = off_line_zero_quartet(sigma=0.7, t=3.0)
        matrix, construction = weil_zero_side_matrix(
            points,
            basis_dim=3,
            scale=DEFAULT_WEIL_SCALE,
        )
        expected_01 = sum(
            weil_basis_transform(0, rho, scale=DEFAULT_WEIL_SCALE).conjugate()
            * weil_basis_transform(
                1,
                1.0 - rho.conjugate(),
                scale=DEFAULT_WEIL_SCALE,
            )
            for rho in points
        )
        self.assertAlmostEqual(matrix[0][1], expected_01.real, places=12)
        self.assertIn("1-conj(rho)", construction["matrix_formula"])

    def test_off_line_control_defeats_both_placebos(self) -> None:
        report = _matrix_report(
            off_line_zero_quartet(sigma=0.7, t=3.0),
            label="test",
            basis_dim=6,
            scale=DEFAULT_WEIL_SCALE,
            psd_relative_tolerance=1e-10,
            point_status="synthetic",
        )
        self.assertFalse(report["eigendecomposition"]["passes_finite_psd_test"])
        self.assertLess(report["eigendecomposition"]["minimum_eigenvalue"], -1.0)
        self.assertTrue(
            report["diagonal_only_placebo"]["would_pass_nonnegative_diagonal_test"]
        )
        self.assertTrue(
            report["same_point_gram_placebo"]["passes_finite_psd_test"]
        )
        self.assertFalse(report["is_evidence_for_rh"])

        fixture = _involution_pairing_fixture()
        self.assertTrue(fixture["control_passes"])
        self.assertEqual(fixture["true_eigenvalues"], [-2.0, 2.0])
        self.assertEqual(fixture["same_point_eigenvalues"], [2.0, 2.0])

    def test_incomplete_zero_orbit_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "closed under conjugation"):
            weil_zero_side_matrix(
                [complex(0.7, 3.0), complex(0.3, 3.0)],
                basis_dim=2,
                scale=DEFAULT_WEIL_SCALE,
            )


class ThetaWeilCorpusTests(unittest.TestCase):
    def test_integrated_report_keeps_graph_and_analytic_layers_separate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = theta_weil_probe(
                db_path=db_path,
                max_n=10,
                theta_t=(0.5, 1.0, 2.0),
            )

        self.assertEqual(report["corpus"]["alignment"]["status"], "pass")
        self.assertFalse(report["graph_source_audit"]["theta_or_weil_edge_type_exists"])
        self.assertTrue(report["summary"]["exact_theta_coefficient_prefix"])
        self.assertTrue(report["summary"]["synthetic_off_line_control_has_negative_direction"])
        self.assertTrue(report["summary"]["off_line_same_point_gram_placebo_would_pass"])
        self.assertFalse(report["summary"]["explicit_formula_arithmetic_side_evaluated"])
        self.assertFalse(report["summary"]["test_space_density_proved"])
        self.assertFalse(report["summary"]["riemann_hypothesis_proved"])
        obligations = {row["obligation"] for row in report["missing_proof_obligations"]}
        self.assertIn("arithmetic_explicit_formula_matrix", obligations)
        self.assertIn("test_space_density", obligations)
        self.assertIn("rigorous_numerics", obligations)

    def test_limits_fail_before_database_access(self) -> None:
        with self.assertRaisesRegex(ValueError, "basis_dim must be >= 2"):
            theta_weil_probe(
                db_path=Path("unused.sqlite"),
                max_n=10,
                weil_basis_dim=1,
            )
        with self.assertRaisesRegex(ValueError, "must not equal 0.5"):
            theta_weil_probe(
                db_path=Path("unused.sqlite"),
                max_n=10,
                off_line_sigma=0.5,
            )


if __name__ == "__main__":
    unittest.main()
