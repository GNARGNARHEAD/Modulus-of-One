from fractions import Fraction as F
from math import gcd
import unittest

from research.dynamics.branch_rhythm_probe import (
    Evidence,calibrations,near_certificate,rational_comparison,recurrence,scan_near,
)


class RhythmTests(unittest.TestCase):
    def test_exact_scan_matches_independent_pair_enumeration(self):
        expected=[(n,m) for m in range(1,65) for n in range(1,93) if abs(n*n-2*m*m)==1]
        self.assertEqual(scan_near(64),expected)
        self.assertEqual(recurrence(64),expected)

    def test_inverse_recovers_previous_primitive_state(self):
        pairs=recurrence(512)
        for previous,(n,m) in zip(pairs,pairs[1:]):
            self.assertEqual((2*m-n,n-m),previous)
            self.assertLess(n-m,m)
            self.assertEqual(gcd(n,m),1)

    def test_fractional_and_rescaled_near_comparisons(self):
        for scale in (1,2,5):
            for denominator in (1,3,7):
                r=near_certificate(Evidence(),7,5,scale,denominator)
                self.assertEqual(F(r['relative_defect']),F(-1,25))
                self.assertEqual(F(r['directed_defect']),F(-scale*scale,denominator*denominator))

    def test_neighbor_can_return_to_relation_after_normalization(self):
        r=near_certificate(Evidence(),18,12,1,1)
        self.assertFalse(r['raw_unit_defect'])
        self.assertEqual(r['primitive'],[3,2])
        self.assertEqual(r['primitive_defect'],1)

    def test_scaled_fractional_square_witnesses_preserve_comparison(self):
        for scale in (1,2,3):
            same=rational_comparison(Evidence(),F(3,4),F(1,2),F(9,4),scale)
            different=rational_comparison(Evidence(),F(3,4),F(1,2),F(2),scale)
            self.assertTrue(same['exact_match'])
            self.assertFalse(different['exact_match'])
            self.assertEqual(F(same['square_value']),F(9,16))

    def test_clock_predicates_are_distinct(self):
        e=Evidence()
        result=calibrations(e)
        self.assertEqual(result['same_source_square_self_add'],[2])
        self.assertEqual(len(result['linear_output_coincidences']),42)
        self.assertEqual(len(result['square_output_coincidences']),8)
        for row in result['records']:
            self.assertEqual(e.edges[row['square']]['predicted_stage'],e.edges[row['self_add']]['predicted_stage'])


if __name__=='__main__':
    unittest.main()
