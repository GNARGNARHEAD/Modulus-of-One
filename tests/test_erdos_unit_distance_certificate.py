"""Independent arithmetic, optimization, and bound checks for the external probe."""

from decimal import Decimal
from fractions import Fraction
from itertools import combinations
import unittest

from moo.erdos_unit_distance_certificate import (
    IntervalArithmetic, SAWIN_K, SAWIN_S, SAWIN_T, best_multiplicity_exact,
    bound_original_formula, choose_weighted, evaluate_certificate, gs_budget,
    prime_data, profitable_prime_cutoff, validate_certificate,
)


class CertificateTests(unittest.TestCase):
    def test_published_example_and_precision_refinement(self):
        low = evaluate_certificate(SAWIN_T, dict(zip(SAWIN_S, SAWIN_K)), Fraction(72), 30)
        high = evaluate_certificate(SAWIN_T, dict(zip(SAWIN_S, SAWIN_K)), Fraction(72), 65)
        self.assertEqual((high["budget"], high["budget_used"], high["split_count"]), (22, 22, 0))
        self.assertTrue(high["exponent"]["lower"].startswith("1.014114428678498238894"))
        self.assertLessEqual(Decimal(low["exponent"]["lower"]), Decimal(high["exponent"]["lower"]))
        self.assertGreaterEqual(Decimal(low["exponent"]["upper"]), Decimal(high["exponent"]["upper"]))

    def test_split_prime_cost_and_two_admissibility_are_distinct(self):
        # 7 splits in Q(sqrt(15)), yet 3 is an inertness witness for Q(sqrt(3)).
        self.assertEqual(prime_data(7, (3, 5)), (1, 3, 2))
        self.assertEqual(prime_data(2, (3, 5)), (2, 5, 1))
        self.assertIsNone(prime_data(2, (3, 7))[1])

    def test_bad_certificate_cannot_reach_numerical_evaluation(self):
        data = dict(zip(SAWIN_S, SAWIN_K))
        for t_values, ks, radius in [
            (SAWIN_T + (3,), data, Fraction(72)),
            (SAWIN_T, {**data, 41: 1}, Fraction(72)),  # One unit over budget.
            (SAWIN_T, {**data, 2: 0}, Fraction(72)),
            (SAWIN_T, {**data, 2: True}, Fraction(72)),
            (SAWIN_T, data, Fraction(1)),
        ]:
            with self.subTest(t=t_values, radius=radius):
                with self.assertRaises(ValueError):
                    validate_certificate(t_values, ks, radius)

    def test_decimal_log_enclosures_against_exact_rational_series(self):
        # For 1 <= x <= 2, ln x = 2*atanh((x-1)/(x+1)).
        # This independent series provides rational bounds without Decimal.ln.
        ar = IntervalArithmetic(35)
        for x in (Fraction(2), Fraction(7, 5), Fraction(11, 7)):
            z = (x - 1) / (x + 1)
            terms = 65
            lower = 2 * sum((z ** (2 * j + 1) / (2 * j + 1)
                             for j in range(terms)), Fraction())
            upper = lower + 2 * z ** (2 * terms + 1) / ((2 * terms + 1) * (1 - z * z))
            enclosure = ar.ln(ar.number(x))
            self.assertLessEqual(Fraction(enclosure.lo), lower)
            self.assertGreaterEqual(Fraction(enclosure.hi), upper)
        with self.assertRaises(TypeError):
            ar.number(0.1)

    def test_weight_one_two_optimizer_against_exhaustive_subsets(self):
        items = [(8.0, 2, 2, 1), (5.0, 1, 3, 1), (4.0, 1, 5, 1),
                 (9.0, 2, 7, 1), (2.0, 1, 11, 1), (-1.0, 1, 13, 1)]
        for budget in range(8):
            exhaustive = max(
                [0.0] + [sum(row[0] for row in subset)
                         for count in range(1, len(items) + 1)
                         for subset in combinations(items, count)
                         if sum(row[1] for row in subset) <= budget]
            )
            score, selected = choose_weighted(items, budget)
            self.assertEqual(score, exhaustive)
            self.assertLessEqual(sum(row[1] for row in selected), budget)

    def test_cutoff_and_integer_multiplicity_have_exact_witnesses(self):
        # delta=1/25 gives p < 2^(25/2), so p^2 < 2^25.
        delta = Fraction(1, 25)
        cutoff = profitable_prime_cutoff(delta)
        self.assertEqual(cutoff, 5792)
        self.assertLess(cutoff ** 2, 2 ** 25)
        self.assertGreaterEqual((cutoff + 1) ** 2, 2 ** 25)
        for p in (2, 3, 11, 5791, 5801):
            # Exponentiating 25 times the objective makes comparison rational.
            exact_scores = [Fraction((k + 1) ** 25, p ** (2 * k)) for k in range(31)]
            got = best_multiplicity_exact(p, delta)
            self.assertEqual(exact_scores[got], max(exact_scores))
        with self.assertRaises(ValueError):
            profitable_prime_cutoff(Fraction(1, 100))

    def test_uniform_bound_closes_infinite_tail_and_does_not_always_exclude(self):
        coarse = bound_original_formula(Fraction(351, 10_000), 30)
        fine = bound_original_formula(Fraction(351, 10_000), 60)
        self.assertTrue(coarse["excluded"])
        self.assertTrue(fine["excluded"])
        self.assertEqual(fine["worst_case"]["t"], 45)
        self.assertEqual(fine["positive_profit_prime_count"], 2197)
        count, stop = fine["positive_profit_prime_count"], fine["tail_starts_at_t"]
        self.assertGreaterEqual(gs_budget(stop), count)
        self.assertLess(gs_budget(stop - 1), count)
        self.assertEqual([row["t"] for row in fine["rows"]], list(range(7, stop + 1)))
        self.assertLess(Decimal(fine["worst_case"]["residual"]["upper"]), Decimal("-0.12"))
        self.assertGreaterEqual(
            Decimal(coarse["worst_case"]["residual"]["upper"]),
            Decimal(fine["worst_case"]["residual"]["upper"]),
        )
        # The upper relaxation still permits delta=.035; exclusion is not automatic.
        lower_threshold = bound_original_formula(Fraction(7, 200), 35)
        self.assertFalse(lower_threshold["excluded"])

    def test_tighter_reported_threshold_and_relaxation_direction(self):
        target = Fraction(3503, 100000)
        bound = bound_original_formula(target, 40)
        self.assertTrue(bound["excluded"])
        self.assertEqual((bound["prime_cutoff_inclusive"], bound["tail_starts_at_t"]), (19803, 98))
        self.assertLess(Decimal(bound["worst_case"]["residual"]["upper"]), Decimal("-0.0049"))
        example = evaluate_certificate(SAWIN_T, dict(zip(SAWIN_S, SAWIN_K)), Fraction(72), 40)
        ar = IntervalArithmetic(40)
        actual_upper = ar.sub(
            ar.number(example["numerator"]["upper"]),
            ar.scale(ar.number(example["denominator"]["lower"]), target),
        ).hi
        relaxed_lower = Decimal(next(row["residual"]["lower"] for row in bound["rows"] if row["t"] == 13))
        self.assertLess(actual_upper, relaxed_lower)


if __name__ == "__main__":
    unittest.main()
