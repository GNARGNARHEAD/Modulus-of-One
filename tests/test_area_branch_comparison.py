"""Independent arithmetic/geometry checks for the finite inspection compiler."""
from fractions import Fraction as F
import unittest

from research.geometry.area_branch_comparison import (
    Registry, Trace, classification, comparison_certificate, explicit_polygon_areas,
    grid, polygons, rounded_units,
)


class InspectionTests(unittest.TestCase):
    def test_rational_compiler_against_fraction_arithmetic(self):
        reg=Registry()
        t=Trace(reg)
        for x in (F(0),F(1,4),F(2,3),F(4,5),F(7,3)):
            for y in (F(1,6),F(2,3),F(9,10),F(3)):
                self.assertEqual(t.radd(x,y),x+y)
        for edge in reg.edges:
            self.assertGreater(int(edge["a"]),0)
            self.assertGreater(int(edge["b"]),0)

    def test_certificate_rejects_fractional_and_zero_operands(self):
        t=Trace(Registry())
        with self.assertRaises(AssertionError): t.op(F(1,2),"*",F(1,2))
        with self.assertRaises(AssertionError): t.op(0,"+",1)

    def test_rounding_proofs_for_exact_and_inexact_divisions(self):
        for a,b,D in ((2,1,1),(8,5,8),(6,5,8),(1,100,1),(355,113,64)):
            t=Trace(Registry())
            low=rounded_units(t,a,b,D,False)
            high=rounded_units(t,a,b,D,True)
            value=F(a*D,b)
            self.assertLessEqual(low,value)
            self.assertLess(value,low+1)
            self.assertGreaterEqual(high,value)
            self.assertGreater(value,high-1)

    def test_polygon_formula_against_explicit_vertices_and_tangents(self):
        for n in (1,2,3,5,8):
            expected=explicit_polygon_areas(n)
            for scale in (1,2,3):
                lo,hi,_,_=polygons(Registry(),n,scale)
                self.assertEqual((lo,hi),expected)
                rl,ru,_,_=polygons(Registry(),n,scale,True)
                self.assertLessEqual(rl,lo)
                self.assertGreaterEqual(ru,hi)
                self.assertLessEqual(ru-rl,F(6,n*n))

    def test_grid_against_independent_cell_enumeration(self):
        for n in (1,2,3,5,8):
            for shape in ("disk","diamond","square"):
                def inside(i,j):
                    if shape=="disk": return i*i+j*j<=n*n
                    if shape=="diamond": return i+j<=n
                    return i<=n and j<=n
                low=sum(inside(i+1,j+1) for i in range(n) for j in range(n))
                high=sum(inside(i,j) for i in range(n) for j in range(n))
                for scale in (1,2):
                    lo,hi,_,_=grid(Registry(),n,scale,shape)
                    self.assertEqual((lo,hi),(F(4*low,n*n),F(4*high,n*n)))

    def test_finite_overlap_does_not_claim_equality(self):
        self.assertEqual(classification(F(49,16),F(3),F(16,5)),"unresolved")
        self.assertEqual(classification(F(4),F(4),F(4)),"exact")
        for root in (F(1,2),F(7,4),F(16,9),F(2)):
            result=comparison_certificate(Registry(),root,F(14,5),F(10,3))
            for test,bound in zip(result["tests"],(F(14,5),F(10,3))):
                expected="less" if root*root<bound else "greater" if root*root>bound else "equal"
                self.assertEqual(test["relation"],expected)


if __name__=="__main__":
    unittest.main()
