from __future__ import annotations

import math
import unittest
from fractions import Fraction

from moo.phase import (
    additive_return_order,
    circular_distance,
    circular_length,
    classify_phase_operation,
    integer_division_branch,
    phase_add,
    phase_fraction,
    phase_scale,
    phase_scale_kernel,
    phase_scale_preimages,
    phase_subtract,
    sampled_path_payload,
    triangle_slack,
)


def _payload_fraction(payload: dict[str, object]) -> Fraction:
    return Fraction(int(payload["p"]), int(payload["q"]))


class PhaseAdditiveDescentTests(unittest.TestCase):
    def test_addition_and_subtraction_ignore_integer_representative_shifts(self) -> None:
        values = [
            Fraction(-2, 3),
            Fraction(-1, 4),
            Fraction(0),
            Fraction(1, 5),
            Fraction(1, 2),
            Fraction(5, 4),
        ]
        for left in values:
            for right in values:
                expected_add = phase_fraction(left + right)
                expected_subtract = phase_fraction(left - right)
                self.assertEqual(phase_add(left, right), expected_add)
                self.assertEqual(phase_subtract(left, right), expected_subtract)
                for left_lift in (-2, -1, 0, 1, 3):
                    for right_lift in (-3, 0, 2):
                        self.assertEqual(
                            phase_add(left + left_lift, right + right_lift),
                            expected_add,
                        )
                        self.assertEqual(
                            phase_subtract(left + left_lift, right + right_lift),
                            expected_subtract,
                        )

    def test_multiplication_and_division_counterexamples_do_not_descend(self) -> None:
        half = Fraction(1, 2)
        self.assertEqual(phase_fraction(0), phase_fraction(1))
        self.assertNotEqual(
            phase_fraction(Fraction(0) * half),
            phase_fraction(Fraction(1) * half),
        )
        self.assertNotEqual(
            phase_fraction(Fraction(0) / 2),
            phase_fraction(Fraction(1) / 2),
        )
        self.assertEqual(phase_fraction(half), phase_fraction(Fraction(3, 2)))
        self.assertNotEqual(
            phase_fraction(half / half),
            phase_fraction(half / Fraction(3, 2)),
        )

    def test_static_operation_classification_keeps_scalar_action_external(self) -> None:
        for op in ("+", "-"):
            payload = classify_phase_operation(op)
            self.assertTrue(payload["well_defined_on_quotient_classes"])
            self.assertEqual(payload["descent_kind"], "binary_additive_operation")
        for op in ("*", "/"):
            payload = classify_phase_operation(op)
            self.assertFalse(payload["well_defined_on_quotient_classes"])
            self.assertEqual(payload["descent_kind"], "no_binary_quotient_descent")

        self.assertEqual(phase_fraction(1), phase_fraction(2))
        self.assertNotEqual(
            phase_scale(1, Fraction(1, 3)),
            phase_scale(2, Fraction(1, 3)),
        )
        with self.assertRaises(ValueError):
            classify_phase_operation("^")
        with self.assertRaises(TypeError):
            classify_phase_operation(1)  # type: ignore[arg-type]


class IntegerPhaseActionTests(unittest.TestCase):
    def test_integer_action_laws_and_return_order_formula(self) -> None:
        values = [
            Fraction(-5, 6),
            Fraction(-1, 3),
            Fraction(0),
            Fraction(1, 5),
            Fraction(1, 2),
            Fraction(7, 4),
        ]
        for value in values:
            self.assertEqual(phase_scale(0, value), 0)
            self.assertEqual(phase_scale(1, value), phase_fraction(value))
            self.assertEqual(phase_scale(-1, value), phase_fraction(-value))
            order = additive_return_order(value)
            for scalar in range(-5, 6):
                expected_order = order // math.gcd(order, abs(scalar))
                self.assertEqual(
                    additive_return_order(phase_scale(scalar, value)),
                    expected_order,
                )
                self.assertLessEqual(
                    circular_distance(
                        phase_scale(scalar, value),
                        phase_scale(scalar, 0),
                    ),
                    abs(scalar) * circular_distance(value, 0),
                )
                for outer in range(-3, 4):
                    self.assertEqual(
                        phase_scale(outer, phase_scale(scalar, value)),
                        phase_scale(outer * scalar, value),
                    )
                    self.assertEqual(
                        phase_scale(outer + scalar, value),
                        phase_add(
                            phase_scale(outer, value),
                            phase_scale(scalar, value),
                        ),
                    )

        for left in values:
            for right in values:
                for scalar in range(-3, 4):
                    self.assertEqual(
                        phase_scale(scalar, phase_add(left, right)),
                        phase_add(
                            phase_scale(scalar, left),
                            phase_scale(scalar, right),
                        ),
                    )

        self.assertGreater(circular_distance(0, Fraction(1, 5)), 0)
        self.assertEqual(
            circular_distance(
                phase_scale(5, 0),
                phase_scale(5, Fraction(1, 5)),
            ),
            0,
        )

    def test_scalars_must_be_actual_integers(self) -> None:
        for scalar in (True, 2.0, Fraction(2, 1), "2"):
            with self.assertRaises(TypeError):
                phase_scale(scalar, Fraction(1, 3))  # type: ignore[arg-type]
            with self.assertRaises(TypeError):
                phase_scale_kernel(scalar)  # type: ignore[arg-type]
            with self.assertRaises(TypeError):
                phase_scale_preimages(scalar, Fraction(1, 3))  # type: ignore[arg-type]

    def test_finite_kernels_are_exact_and_capped(self) -> None:
        for scalar in range(-6, 7):
            payload = phase_scale_kernel(scalar, materialization_limit=8)
            if scalar == 0:
                self.assertEqual(payload["kind"], "all_phases")
                self.assertIsNone(payload["cardinality"])
                self.assertIsNone(payload["kernel_points"])
                continue
            cardinality = abs(scalar)
            self.assertEqual(payload["kind"], "finite")
            self.assertEqual(payload["cardinality"], cardinality)
            points = payload["kernel_points"]
            self.assertIsNotNone(points)
            phases = [_payload_fraction(point) for point in points]  # type: ignore[arg-type]
            self.assertEqual(len(phases), cardinality)
            self.assertEqual(len(set(phases)), cardinality)
            self.assertEqual(
                phases,
                [Fraction(index, cardinality) for index in range(cardinality)],
            )
            for phase in phases:
                self.assertEqual(phase_scale(scalar, phase), 0)

        capped = phase_scale_kernel(9, materialization_limit=4)
        self.assertEqual(capped["cardinality"], 9)
        self.assertFalse(capped["materialized"])
        self.assertIsNone(capped["kernel_points"])

    def test_materialization_caps_are_exact_integers(self) -> None:
        for limit in (-1,):
            with self.assertRaises(ValueError):
                phase_scale_kernel(2, materialization_limit=limit)
        for limit in (True, 2.0, Fraction(2, 1)):
            with self.assertRaises(TypeError):
                phase_scale_preimages(2, 0, materialization_limit=limit)  # type: ignore[arg-type]


class TorsionPreimageTests(unittest.TestCase):
    def test_zero_and_unit_scalars_have_correct_preimage_kinds(self) -> None:
        all_phases = phase_scale_preimages(0, 0)
        self.assertEqual(all_phases["kind"], "all_phases")
        self.assertIsNone(all_phases["cardinality"])

        empty = phase_scale_preimages(0, Fraction(1, 3))
        self.assertEqual(empty["kind"], "empty")
        self.assertEqual(empty["cardinality"], 0)
        self.assertEqual(empty["preimages"], [])

        plus_one = phase_scale_preimages(1, Fraction(1, 3))
        minus_one = phase_scale_preimages(-1, Fraction(1, 3))
        self.assertEqual(plus_one["cardinality"], 1)
        self.assertEqual(minus_one["cardinality"], 1)
        self.assertEqual(
            _payload_fraction(plus_one["preimages"][0]["phase"]),  # type: ignore[index]
            Fraction(1, 3),
        )
        self.assertEqual(
            _payload_fraction(minus_one["preimages"][0]["phase"]),  # type: ignore[index]
            Fraction(2, 3),
        )

    def test_preimage_fibres_are_complete_unique_cosets(self) -> None:
        targets = [0, Fraction(1, 3), Fraction(1, 2), Fraction(5, 7)]
        for scalar in (-5, -3, -2, 1, 2, 3, 5):
            for target in targets:
                target_phase = phase_fraction(target)
                payload = phase_scale_preimages(
                    scalar,
                    target,
                    materialization_limit=8,
                )
                self.assertEqual(payload["cardinality"], abs(scalar))
                rows = payload["preimages"]
                self.assertIsNotNone(rows)
                roots = [
                    _payload_fraction(row["phase"]) for row in rows  # type: ignore[union-attr]
                ]
                self.assertEqual(len(roots), abs(scalar))
                self.assertEqual(len(set(roots)), abs(scalar))
                for root in roots:
                    self.assertEqual(phase_scale(scalar, root), target_phase)
                    root_order = additive_return_order(root)
                    target_order = additive_return_order(target_phase)
                    self.assertEqual(
                        root_order // math.gcd(root_order, abs(scalar)),
                        target_order,
                    )
                anchor = roots[0]
                translated = {
                    phase_subtract(root, anchor) for root in roots
                }
                expected_kernel = {
                    Fraction(index, abs(scalar)) for index in range(abs(scalar))
                }
                self.assertEqual(translated, expected_kernel)

    def test_named_preimage_examples_and_cap(self) -> None:
        examples = [
            (2, Fraction(1, 3), [Fraction(1, 6), Fraction(2, 3)]),
            (
                3,
                Fraction(1, 2),
                [Fraction(1, 6), Fraction(1, 2), Fraction(5, 6)],
            ),
            (4, 0, [Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)]),
        ]
        for scalar, target, expected in examples:
            payload = phase_scale_preimages(scalar, target)
            roots = [
                _payload_fraction(row["phase"])  # type: ignore[index]
                for row in payload["preimages"]
            ]
            self.assertEqual(roots, expected)

        capped = phase_scale_preimages(7, Fraction(1, 3), materialization_limit=3)
        self.assertEqual(capped["cardinality"], 7)
        self.assertFalse(capped["materialized"])
        self.assertIsNone(capped["preimages"])


class IntegerDivisionBranchTests(unittest.TestCase):
    def test_equal_source_phases_select_branches_by_retained_lift(self) -> None:
        cases = [
            (Fraction(1, 3), Fraction(1, 6), 0),
            (Fraction(4, 3), Fraction(2, 3), 1),
            (Fraction(7, 3), Fraction(7, 6), 0),
        ]
        for source, result, branch in cases:
            payload = integer_division_branch(source, 2, result)
            self.assertTrue(payload["source_relation_valid"])
            self.assertTrue(payload["phase_relation_holds"])
            self.assertEqual(payload["selected_branch_index"], branch)
            self.assertEqual(payload["preimage_count"], 2)
            self.assertTrue(payload["selection_uses_retained_source_lift"])
            self.assertEqual(
                _payload_fraction(payload["result_phase"]),
                phase_fraction(result),
            )

        self.assertEqual(phase_fraction(Fraction(1, 3)), phase_fraction(Fraction(4, 3)))
        self.assertNotEqual(phase_fraction(Fraction(1, 6)), phase_fraction(Fraction(2, 3)))

    def test_negative_and_unit_divisors(self) -> None:
        negative = integer_division_branch(
            Fraction(4, 3),
            -2,
            Fraction(-2, 3),
        )
        self.assertEqual(negative["selected_branch_index"], 1)
        self.assertEqual(negative["preimage_count"], 2)
        self.assertTrue(negative["selection_uses_retained_source_lift"])

        for divisor in (-1, 1):
            source = Fraction(4, 3)
            payload = integer_division_branch(source, divisor, source / divisor)
            self.assertEqual(payload["preimage_count"], 1)
            self.assertEqual(payload["selected_branch_index"], 0)
            self.assertTrue(payload["single_valued_from_phase"])
            self.assertFalse(payload["selection_uses_retained_source_lift"])

    def test_source_arithmetic_is_validated_before_phase_classification(self) -> None:
        with self.assertRaises(ValueError):
            integer_division_branch(Fraction(4, 3), 2, Fraction(1, 6))
        with self.assertRaises(ZeroDivisionError):
            integer_division_branch(1, 0, 0)
        with self.assertRaises(TypeError):
            integer_division_branch(1, Fraction(2, 1), Fraction(1, 2))  # type: ignore[arg-type]

    def test_branch_payload_respects_materialization_cap(self) -> None:
        payload = integer_division_branch(
            Fraction(8, 3),
            7,
            Fraction(8, 21),
            materialization_limit=3,
        )
        self.assertEqual(payload["preimage_count"], 7)
        self.assertFalse(payload["preimage_family"]["materialized"])
        self.assertIsNone(payload["preimage_family"]["preimages"])


class PhaseMetricMathTests(unittest.TestCase):
    """Exact Q/Z metric contracts shared with the maintained metric probe."""

    def test_exact_circular_lengths_and_distances(self) -> None:
        self.assertEqual(circular_length(Fraction(3, 4)), Fraction(1, 4))
        self.assertEqual(circular_length(Fraction(-1, 4)), Fraction(1, 4))
        self.assertEqual(circular_length(Fraction(1, 2)), Fraction(1, 2))
        self.assertEqual(
            circular_distance(Fraction(1, 10), Fraction(9, 10)),
            Fraction(1, 5),
        )
        self.assertEqual(
            circular_distance(Fraction(1, 3), Fraction(4, 3)),
            Fraction(0),
        )
        self.assertEqual(
            circular_distance(Fraction(1, 3), Fraction(2, 3)),
            Fraction(1, 3),
        )

    def test_triangle_slack_detects_tight_and_wrapped_routes(self) -> None:
        self.assertEqual(triangle_slack(0, Fraction(1, 8), Fraction(1, 4)), 0)
        self.assertEqual(
            triangle_slack(0, Fraction(1, 3), Fraction(2, 3)),
            Fraction(1, 3),
        )
        self.assertEqual(triangle_slack(0, Fraction(1, 2), 1), 1)

    def test_small_exact_grid_satisfies_pseudometric_axioms(self) -> None:
        values = sorted(
            {
                Fraction(numerator, denominator)
                for denominator in range(1, 6)
                for numerator in range(-denominator, 2 * denominator + 1)
            }
        )
        for left in values:
            self.assertEqual(circular_distance(left, left), 0)
            for right in values:
                self.assertEqual(
                    circular_distance(left, right),
                    circular_distance(right, left),
                )
                self.assertLessEqual(circular_distance(left, right), abs(left - right))
                for via in values:
                    self.assertLessEqual(
                        circular_distance(left, right),
                        circular_distance(left, via) + circular_distance(via, right),
                    )

    def test_sampled_paths_keep_lift_information_after_phase_collapse(self) -> None:
        full_turn = sampled_path_payload([Fraction(index, 4) for index in range(5)])
        self.assertEqual(full_turn["sampled_phase_path_length"]["frac"], "1")
        self.assertEqual(full_turn["phase_endpoint_distance"]["frac"], "0")
        self.assertEqual(full_turn["phase_detour"]["frac"], "1")
        self.assertEqual(full_turn["sampled_net_integer_lift"], 1)

        endpoints_only = sampled_path_payload([0, 1])
        self.assertEqual(endpoints_only["sampled_phase_path_length"]["frac"], "0")
        self.assertEqual(endpoints_only["sampled_step_contraction"]["frac"], "1")

        positive_lift = sampled_path_payload(
            [index * Fraction(2, 3) for index in range(4)]
        )
        negative_lift = sampled_path_payload(
            [index * Fraction(-1, 3) for index in range(4)]
        )
        self.assertEqual(
            positive_lift["projected_phase_points"],
            negative_lift["projected_phase_points"],
        )
        self.assertEqual(positive_lift["sampled_net_integer_lift"], 2)
        self.assertEqual(negative_lift["sampled_net_integer_lift"], -1)

    def test_metric_api_rejects_inexact_inputs_and_empty_paths(self) -> None:
        with self.assertRaises(TypeError):
            circular_length(0.75)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            circular_distance("1/3", 0)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            sampled_path_payload([])

        singleton = sampled_path_payload([Fraction(1, 2)])
        self.assertEqual(singleton["sampled_phase_path_length"]["frac"], "0")
        self.assertEqual(singleton["phase_endpoint_distance"]["frac"], "0")


if __name__ == "__main__":
    unittest.main()
