"""Independent arithmetic, counting, and scope checks for variable denominators."""

from fractions import Fraction as F
from itertools import combinations
from math import gcd, isqrt, prod
import unittest

from moo.variable_denominator_probe import (
    CASE_SPECS, SEEDS, box_pairs, box_row, first_average_above,
    make_case, prime_witness, scalar_witness_graph,
)
from tests.test_moo_split_prime_branch_probe import polynomial_product, polynomial_conjugate
from moo.verify_split_prime_branch_report import (
    ONE, ZERO, add, build_level, conjugate, element, from_basis,
    multiply, multiply_all, scale,
)


class VariableDenominatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {(m, factors): make_case(m, factors) for m, factors in CASE_SPECS}

    def test_new_prime_factors_with_independent_radical_arithmetic(self):
        for m in (4, 8, 24):
            independent = build_level(m)
            for (order, prime), coefficients in SEEDS.items():
                if order != m:
                    continue
                conjugates = {}
                for t in range(m):
                    if gcd(t, m) == 1:
                        value = ZERO
                        for j, c in enumerate(coefficients):
                            value = add(value, scale(independent.powers[j * t % m], c))
                        conjugates[t] = value
                self.assertEqual(multiply_all(conjugates.values()), scale(ONE, prime))
                witness = prime_witness(m, prime)
                for row in witness["prime_factors"]:
                    self.assertEqual(from_basis(row["basis_coefficients"], independent.basis),
                                     conjugates[row["automorphism"]])
                if m == 24 and prime in (73, 97):
                    expected = {73: element({0: 6, 1: F(5, 2), 2: 2, 3: F(1, 2)}),
                                97: element({0: 5, 1: 2, 2: 2, 3: 1})}[prime]
                    self.assertEqual(multiply(conjugates[1], conjugate(conjugates[1])), expected)
        self.assertEqual(35 ** 2 - 2 * 24 ** 2, 73)
        self.assertEqual(15 ** 2 - 2 * 8 ** 2, 97)

    def test_all_direction_norms_with_polynomial_long_division(self):
        for (m, factors), case in self.cases.items():
            degree = {4: 2, 8: 4, 24: 8}[m]
            self.assertEqual(len(case.directions), m * prod((2 * k + 1) ** (degree // 2) for _, k in factors))
            expected_norm = (case.denominator ** 2,) + (0,) * (degree - 1)
            for vector in case.directions:
                self.assertEqual(polynomial_product(vector, polynomial_conjugate(vector, m), m), expected_norm)

    def test_factor_graph_edges_and_complete_symbolic_product(self):
        for (m, _), case in self.cases.items():
            graph = case.construction
            block_sizes = []
            expected_edges = len(case.directions)
            for block in graph["prime_choice_blocks"]:
                nodes = {j: tuple(v) for j, _, v in block["nodes"]}
                block_sizes.append(len(nodes))
                axes = len(block["ratio_numerators_over_prime"])
                self.assertEqual(len(nodes), (2 * block["depth"] + 1) ** axes)
                for source, axis, target in block["edges"]:
                    actual = polynomial_product(nodes[source], block["ratio_numerators_over_prime"][axis], m)
                    self.assertEqual(actual, tuple(block["prime"] * c for c in nodes[target]))
                expected_edges += len(case.directions) * len(block["edges"]) // len(nodes)
            self.assertEqual(graph["product_node_count"], m * prod(block_sizes))
            self.assertEqual(graph["product_edge_count"], expected_edges)
            phases = graph["phase_cycle"]["nodes"]
            for source, target in graph["phase_cycle"]["edges"]:
                self.assertEqual(polynomial_product(phases[source], phases[1], m), tuple(phases[target]))

    def test_gaussian_arbitrary_denominator_control(self):
        for denominator in range(1, 501):
            directions = set()
            for x in range(-denominator, denominator + 1):
                square = denominator ** 2 - x ** 2
                y = isqrt(square)
                if y * y == square:
                    directions.update(((x, y), (x, -y)))
            remaining, p, exact, upper = denominator, 2, 4, 4
            while p * p <= remaining:
                exponent = 0
                while remaining % p == 0:
                    exponent += 1
                    remaining //= p
                if exponent:
                    upper *= 2 * exponent + 1
                    if p % 4 == 1:
                        exact *= 2 * exponent + 1
                p += 1
            if remaining > 1:
                upper *= 3
                if remaining % 4 == 1:
                    exact *= 3
            self.assertEqual(len(directions), exact)
            self.assertLessEqual(len(directions), upper)
            if denominator in (65, 241):
                factors = ((5, 1), (13, 1)) if denominator == 65 else ((241, 1),)
                self.assertEqual(directions, self.cases[4, factors].directions)

    def test_profile_counts_and_exact_cap_thresholds(self):
        for case in self.cases.values():
            for side in (64, 512, 8192):
                ordered = sum(prod(max(side - abs(c), 0) for c in vector) for vector in case.directions)
                self.assertEqual(2 * box_pairs(case, side), ordered)
        case = self.cases[24, ((73, 1), (97, 1))]
        for cap, threshold in ((1944, 6454), (15000, 9806)):
            self.assertEqual(first_average_above(case, cap)["first_coefficient_side"], threshold)
            for side in (threshold - 1, threshold):
                ordered = sum(prod(max(side - abs(c), 0) for c in vector) for vector in case.directions)
                self.assertEqual(ordered > cap * side ** 8, side == threshold)
        self.assertEqual({box_row(case, 512)["point_count_decimal"] for case in self.cases.values()}, {str(512 ** 8)})

    def test_small_geometry_and_large_denominator_scope_control(self):
        case = make_case(4, ((5, 1),))
        points = [(x, y) for x in range(7) for y in range(7)]
        exact_edges = sum((a - c) ** 2 + (b - d) ** 2 == 25 for (a, b), (c, d) in combinations(points, 2))
        self.assertEqual(box_pairs(case, 7), exact_edges)
        for n in (10, 20, 30):
            t = 2 ** n
            denominator = t * t + 1
            q = (F(t * t - 1, denominator), F(2 * t, denominator))
            self.assertEqual(q[0] ** 2 + q[1] ** 2, 1)
            self.assertEqual(q[0].denominator, denominator)
            self.assertGreater(denominator, n ** 3)
            points = [(j * q[0], j * q[1]) for j in range(n)]
            edges = sum((a - c) ** 2 + (b - d) ** 2 == 1 for (a, b), (c, d) in combinations(points, 2))
            self.assertEqual(edges, n - 1)

    def test_scalar_status_and_bounded_inputs(self):
        report = scalar_witness_graph()
        self.assertFalse(report["allow_speculative_operands"])
        graph = report["graph"]
        nodes = {row["node_uid"]: row for row in graph["nodes"]}
        self.assertTrue(all(nodes[uid]["status"] == "G" for edge in graph["edges"] for uid in edge["input_uids"]))
        statuses = {row["value"]: row["status"] for row in report["products"]}
        self.assertEqual(statuses, {65: "G", 697: "S", 5329: "S", 7081: "S", 58081: "S"})
        for factors in ((), ((73, 1), (73, 1)), ((73, 3),), ((73, 2), (97, 1))):
            with self.assertRaises(ValueError):
                make_case(24, factors)
        with self.assertRaises(ValueError):
            first_average_above(self.cases[24, ((73, 1),)], 1944)


if __name__ == "__main__":
    unittest.main()
