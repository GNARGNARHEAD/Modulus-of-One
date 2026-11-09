"""Independent arithmetic and counting checks for the split-prime example."""

from fractions import Fraction
from itertools import combinations, product
import unittest

from moo.split_prime_branch_probe import (
    CyclotomicRing, PRIME, ORDERS, box_row, count_coefficient_box, cyclotomic_growth_ceiling,
    direction_graph, embed, equal_point_comparison, generator_span,
    make_level, refinement_witnesses, scalar_witness_graph,
    small_point_graph, splitting_witnesses,
)


def reduce_polynomial(coefficients, order):
    polynomial = {4: [1, 0, 1], 8: [1, 0, 0, 0, 1],
                  24: [1, 0, 0, 0, -1, 0, 0, 0, 1]}[order]
    degree = len(polynomial) - 1
    work = list(coefficients) + [0] * max(0, degree - len(coefficients))
    for k in range(len(work) - 1, degree - 1, -1):
        leading = work[k]
        for j, coefficient in enumerate(polynomial):
            work[k - degree + j] -= leading * coefficient
    return tuple(work[:degree])


def polynomial_product(left, right, order):
    work = [0] * (len(left) + len(right) - 1)
    for j, x in enumerate(left):
        for k, y in enumerate(right):
            work[j + k] += x * y
    return reduce_polynomial(work, order)


def polynomial_conjugate(value, order):
    work = [0] * order
    for j, x in enumerate(value):
        work[-j % order] += x
    return reduce_polynomial(work, order)


class SplitPrimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.levels = [make_level(order) for order in ORDERS]

    def test_ring_multiplication_against_polynomial_long_division(self):
        for level in self.levels:
            ring = level.ring
            for left, right in product(ring.powers, repeat=2):
                self.assertEqual(ring.multiply(left, right), polynomial_product(left, right, ring.order))
            for value in (level.seed, *level.generators):
                self.assertEqual(ring.sigma(value, -1), polynomial_conjugate(value, ring.order))

    def test_prime_splitting_has_distinct_modular_and_norm_witnesses(self):
        self.assertTrue(all(PRIME % d for d in range(2, 16)))
        for level in self.levels:
            ring = level.ring
            data = splitting_witnesses(level)
            roots = [root for _, root in data["roots_mod_prime"]]
            self.assertEqual(len(roots), len(set(roots)))
            self.assertEqual(len(roots), ring.degree)
            base = data["primitive_root_for_zeta"]
            self.assertEqual(pow(base, ring.order, PRIME), 1)
            self.assertFalse(any(pow(base, k, PRIME) == 1 for k in range(1, ring.order)))
            self.assertEqual({row["field_norm"] for row in data["prime_generators"]}, {PRIME})
            self.assertTrue(all(len(row["zero_mod_prime"]) == 1 for row in data["prime_generators"]))
            self.assertEqual({row["zero_mod_prime"][0] for row in data["prime_generators"]}, set(roots))
            total = ring.one
            for row in data["prime_generators"]:
                total = polynomial_product(total, row["basis_coefficients"], ring.order)
            self.assertEqual(total, ring.scalar(PRIME))

    def test_every_unit_direction_with_independent_polynomial_arithmetic(self):
        for level, expected in zip(self.levels, (12, 72, 1944)):
            ring = level.ring
            self.assertEqual(len(level.directions), expected)
            self.assertEqual(expected, ring.order * 3 ** len(level.pairs))
            for value in level.directions:
                self.assertEqual(polynomial_product(value, polynomial_conjugate(value, ring.order), ring.order),
                                 ring.scalar(PRIME ** 2))

    def test_branch_choices_recover_from_prime_factor_poles(self):
        for level in self.levels:
            ring = level.ring
            roots = [root for _, root in splitting_witnesses(level)["roots_mod_prime"]]
            pair_roots = []
            for a, b in level.pairs:
                pair_roots.append((next(root for root in roots if ring.evaluate_mod_prime(a, root) == 0),
                                   next(root for root in roots if ring.evaluate_mod_prime(b, root) == 0)))
            for value, (exponents, _) in level.directions.items():
                for exponent, (positive, negative) in zip(exponents, pair_roots):
                    # Multiplication by 241 shifts every prime valuation up by 1.
                    self.assertEqual(ring.evaluate_mod_prime(value, positive) != 0, exponent == -1)
                    self.assertEqual(ring.evaluate_mod_prime(value, negative) != 0, exponent == 1)

    def test_refinement_and_direction_graph_edges_are_actual_products(self):
        self.assertTrue(all(row["verified"] for row in refinement_witnesses(self.levels)))
        for parent, child, other_automorphism in ((self.levels[0], self.levels[1], 5),
                                                 (self.levels[1], self.levels[2], 17)):
            actual = polynomial_product(child.seed, child.ring.sigma(child.seed, other_automorphism), child.ring.order)
            self.assertEqual(actual, embed(parent.seed, parent.ring.order, child.ring))
        for level in self.levels:
            ring = level.ring
            graph = direction_graph(level)
            nodes = {j: tuple(value) for j, _, _, value in graph["nodes"]}
            generators = {"q_" + str(t): value for t, value in zip(level.representatives, level.generators)}
            for source, multiplier, target in graph["edges"]:
                if multiplier == "zeta":
                    actual = polynomial_product(nodes[source], ring.powers[1], ring.order)
                    self.assertEqual(actual, nodes[target])
                else:
                    actual = polynomial_product(nodes[source], generators[multiplier], ring.order)
                    self.assertEqual(actual, tuple(PRIME * c for c in nodes[target]))

    def test_complete_span_intersection_and_independent_point_pair_counts(self):
        for level in self.levels:
            ring = level.ring
            span = generator_span(level)
            axes = {tuple(sign if j == k else 0 for j in range(len(level.pairs)))
                    for k in range(len(level.pairs)) for sign in (-1, 1)}
            self.assertEqual(set(span["unit_steps_in_integer_span"]), axes)
            graph = small_point_graph(level)
            points = {j: tuple(value) for j, _, value in graph["points"]}
            self.assertEqual(len(set(points.values())), len(points))
            expected = set()
            for a, b in combinations(points, 2):
                difference = tuple(x - y for x, y in zip(points[a], points[b]))
                squared_norm = polynomial_product(difference, polynomial_conjugate(difference, ring.order), ring.order)
                if squared_norm == ring.scalar(PRIME ** 2):
                    expected.add((a, b))
            actual = {tuple(sorted((a, b))) for a, _, b in graph["addition_edges"]}
            self.assertEqual(actual, expected)
            self.assertEqual(len(actual), count_coefficient_box(list(axes), 3, len(level.pairs)))

    def test_box_overlap_formula_against_exhaustive_integer_geometry(self):
        # Independent radius-5 integer-circle control, with finite boundaries.
        steps = [(x, y) for x in range(-5, 6) for y in range(-5, 6) if x*x + y*y == 25]
        for side in (1, 4, 6, 9):
            points = list(product(range(side), repeat=2))
            expected = sum((a-c)**2 + (b-d)**2 == 25 for (a, b), (c, d) in combinations(points, 2))
            self.assertEqual(count_coefficient_box(steps, side, 2), expected)

    def test_equal_point_crossover_and_permanent_direction_cap(self):
        comparison = equal_point_comparison(self.levels, 259)
        self.assertEqual(comparison["first_strict_win_over_all_smaller_fields"], {"8": 18, "24": 259})
        self.assertEqual(comparison["permanent_dominance_from_direction_cap"], {"8": 18, "24": 259})
        for t in (17, 18, 258, 259):
            rows = [box_row(level, t) for level in self.levels]
            self.assertEqual({row["point_count_decimal"] for row in rows}, {str(t ** 8)})
        row = box_row(self.levels[-1], 259)
        average = Fraction(int(row["average_unit_neighbors"]["numerator"]),
                           int(row["average_unit_neighbors"]["denominator"]))
        self.assertGreater(average, 72)
        self.assertLess(average, 1944)

    def test_scalar_witness_eligibility_and_input_limits(self):
        ceiling = cyclotomic_growth_ceiling()
        self.assertEqual(ceiling["maximum_degree"], 64)
        self.assertEqual(ceiling["degrees"][240], 64)
        self.assertTrue(all(240 % m == 0 for m in ceiling["compatible_conductors"]))
        data = scalar_witness_graph()
        self.assertTrue(data["outputs_identical"])
        self.assertFalse(data["allow_speculative_operands"])
        graph = data["graph"]
        nodes = {row["node_uid"]: row for row in graph["nodes"]}
        self.assertLessEqual(len(nodes), 270)
        self.assertLessEqual(len(graph["edges"]), 280)
        self.assertTrue(all(nodes[uid]["status"] == "G" for edge in graph["edges"] for uid in edge["input_uids"]))
        for order in (3, 12, True):
            with self.assertRaises(ValueError):
                CyclotomicRing(order)
        with self.assertRaises(ValueError):
            equal_point_comparison(self.levels, 513)
        with self.assertRaises(ValueError):
            count_coefficient_box([(1, 0)], 0, 2)
        with self.assertRaises(ValueError):
            count_coefficient_box([(1, 0)], 4, 3)


if __name__ == "__main__":
    unittest.main()
