"""Independent geometry checks for the fixed-seed branch gate."""

from fractions import Fraction
from itertools import combinations
from math import isqrt
import unittest

from moo.unit_direction_branch_probe import (
    count_subset_geometry, collision_witness, moo_seed_calibration,
    single_seed_stage, triangular_generators, two_seed_stage, unit_shell,
)


def rational_product(left, right):
    # Independent rational implementation, not the imported integer-pair helper.
    a, b = left
    c, d = right
    return a * c - b * d, a * d + b * c


def rational_power(pair, exponent):
    result = (Fraction(1), Fraction(0))
    for _ in range(exponent):
        result = rational_product(result, pair)
    return result


class UnitDirectionGateTests(unittest.TestCase):
    def test_complete_shell_against_integer_square_search(self):
        for k5, k13 in ((0, 0), (1, 0), (0, 1), (2, 0), (1, 1)):
            denominator = 5 ** k5 * 13 ** k13
            expected = set()
            for x in range(-denominator, denominator + 1):
                y2 = denominator ** 2 - x * x
                y = isqrt(y2)
                if y * y == y2:
                    expected.update(((x, y), (x, -y)))
            self.assertEqual(unit_shell(k5, k13), expected)
            self.assertEqual(len(expected), 4 * (2 * k5 + 1) * (2 * k13 + 1))

    def test_full_stage_against_all_point_pairs(self):
        row = two_seed_stage(3, retain_graph=True)
        points = {j: (x, y) for j, x, y, _ in row["point_graph"]["points"]}
        denominator = row["denominator"]
        expected_edges = set()
        for source, target in combinations(points, 2):
            x, y = points[source]
            a, b = points[target]
            if (x - a) ** 2 + (y - b) ** 2 == denominator ** 2:
                expected_edges.add((source, target))
        recorded = {tuple(sorted(edge[:2])) for edge in row["point_graph"]["unit_edges"]}
        self.assertEqual(recorded, expected_edges)
        self.assertEqual((len(points), len(recorded), row["extra_unit_pairs"]), (1024, 5128, 8))

    def test_direction_and_addition_witnesses_reconstruct_coordinates(self):
        row = two_seed_stage(3, retain_graph=True)
        denominator = row["denominator"]
        directions = {j: (x, y) for j, _, _, x, y in row["direction_nodes"]}
        seeds = {"u": (Fraction(3, 5), Fraction(4, 5)),
                 "v": (Fraction(5, 13), Fraction(12, 13))}
        for source, seed, target in row["direction_construction_edges"]:
            actual = rational_product(tuple(Fraction(c, denominator) for c in directions[source]), seeds[seed])
            self.assertEqual(actual, tuple(Fraction(c, denominator) for c in directions[target]))
        points = {j: (x, y) for j, x, y, _ in row["point_graph"]["points"]}
        mask_to_point = {mask: j for j, _, _, masks in row["point_graph"]["points"] for mask in masks}
        for source, direction, target, input_mask, output_mask in row["point_graph"]["addition_occurrences"]:
            self.assertEqual((mask_to_point[input_mask], mask_to_point[output_mask]), (source, target))
            self.assertEqual(output_mask, input_mask | (1 << direction))
            self.assertEqual(points[target], tuple(a + b for a, b in zip(points[source], directions[direction])))

    def test_duplicate_paths_do_not_inflate_points_or_unit_pairs(self):
        row = count_subset_geometry([(1, 0), (1, 0)], 1, unit_shell(0, 0), retain_graph=True)
        self.assertEqual((row["raw_subset_paths"], row["distinct_points"], row["distinct_unit_pairs"]), (4, 3, 2))
        self.assertEqual(row["coordinate_flip_occurrences"], 4)
        self.assertEqual(row["distinct_coordinate_flip_edges"], 2)
        self.assertEqual(row["max_paths_at_one_point"], 2)
        self.assertEqual(len(row["point_graph"]["addition_occurrences"]), 3)
        opposite = count_subset_geometry([(1, 0), (-1, 0)], 1, unit_shell(0, 0))
        self.assertEqual((opposite["distinct_points"], opposite["distinct_unit_pairs"]), (3, 2))

    def test_single_seed_control_matches_all_ten_predicted_counts(self):
        for length in range(1, 11):
            with self.subTest(length=length):
                row = single_seed_stage(length)
                self.assertTrue(row["matches_exact_formula"])
                self.assertEqual(row["extra_unit_pairs"], 0)
                self.assertEqual(row["duplicate_subset_paths"], 0)

    def test_new_direction_and_later_collision_with_independent_rationals(self):
        u = (Fraction(3, 5), Fraction(4, 5))
        v = (Fraction(5, 13), Fraction(12, 13))

        def term(a, b):
            return rational_product(rational_power(u, a), rational_power(v, b))

        direction = term(3, 2)
        self.assertEqual(direction, (Fraction(8643, 21125), Fraction(-19276, 21125)))
        self.assertEqual(sum(c * c for c in direction), 1)
        signed_powers = [(-1, 0, 0), (-1, 2, 0), (1, 1, 1), (-1, 0, 2),
                         (-1, 3, 0), (1, 2, 1), (-1, 1, 2)]
        difference = tuple(sum(sign * term(a, b)[axis] for sign, a, b in signed_powers) for axis in (0, 1))
        self.assertEqual(difference, direction)
        witness = collision_witness()
        self.assertTrue(witness["verified_equal"])
        self.assertFalse(witness["full_stage_enumerated"])
        totals = []
        for side in ("left_subset_exponents", "right_subset_exponents"):
            terms = witness[side]
            self.assertEqual(len(terms), len(set(terms)))
            self.assertTrue(all(a + b <= 5 for a, b in terms))
            totals.append(tuple(sum(term(a, b)[axis] for a, b in terms) for axis in (0, 1)))
        self.assertEqual(totals[0], totals[1])
        for coords in (witness["left_scaled_coordinates"], witness["right_scaled_coordinates"]):
            self.assertEqual(tuple(Fraction(c, witness["denominator"]) for c in coords), totals[0])

    def test_scalar_graph_retains_shell_witnesses_and_speculative_ratios(self):
        calibration = moo_seed_calibration()
        graph = calibration["graph"]
        self.assertFalse(calibration["allow_speculative_operands"])
        self.assertLessEqual(len(graph["nodes"]), 180)
        self.assertLessEqual(len(graph["edges"]), 185)
        nodes = {row["node_uid"]: row for row in graph["nodes"]}
        edges = {row["edge_uid"]: row for row in graph["edges"]}
        for shell in calibration["shell_witnesses"]:
            self.assertTrue(shell["matches_radius_square"])
            self.assertEqual(edges[shell["sum_edge_uid"]]["op"], "+")
            self.assertEqual(nodes[shell["common_squared_radius_uid"]]["status"], "G")
            self.assertTrue(all(edges[uid]["op"] == "*" for uid in shell["square_edge_uids"]))
        ratios = {row["node_uid"] for row in calibration["ratio_outputs"]}
        self.assertEqual({uid for uid, row in nodes.items() if row["status"] == "S"}, ratios)
        self.assertFalse(any(ratios.intersection(edge["input_uids"]) for edge in graph["edges"]))

    def test_resource_limits_and_invalid_geometry_are_rejected(self):
        for value in (-1, 4, True):
            with self.assertRaises(ValueError):
                triangular_generators(value)
        with self.assertRaises(ValueError):
            single_seed_stage(11)
        for generators, denominator, shell in (
            ([(1, 0)] * 11, 1, unit_shell(0, 0)),
            ([(0, 0)], 1, unit_shell(0, 0)),
            ([(1.0, 0)], 1, unit_shell(0, 0)),
            ([(1, 0)], 1, {(1, 0)}),
        ):
            with self.assertRaises(ValueError):
                count_subset_geometry(generators, denominator, shell)


if __name__ == "__main__":
    unittest.main()
