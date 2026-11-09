"""Geometric and integer-graph checks independent of the optimized area sum."""
from __future__ import annotations

import tempfile
import unittest
from contextlib import closing
from fractions import Fraction as F
from pathlib import Path

from moo.circle_square_area_probe import (
    bracket_path, ceil_sqrt, classify_square, compatible_ratios, floor_sqrt,
    grid_bounds, intended_fraction_edge, polygon_bounds, side_bounds, source_vertex,
)
from moo.research_utils import connect_readonly
from moo.shell_branch_search import WitnessReader
from moo.strict_stage_moo import build_strict_stage_graph


def cross(p: tuple[F,F], q: tuple[F,F]) -> F:
    return p[0]*q[1]-p[1]*q[0]


def shoelace(vertices: list[tuple[F,F]]) -> F:
    return sum((cross(vertices[i],vertices[(i+1)%len(vertices)])
                for i in range(len(vertices))),F(0))/2


def geometric_polygon_areas(n: int) -> tuple[F,F]:
    quarter = []
    for k in range(n):
        t=F(k,n)
        quarter.append(((1-t*t)/(1+t*t),2*t/(1+t*t)))
    vertices=[]
    for turns in range(4):
        for p in quarter:
            for _ in range(turns):
                p=(-p[1],p[0])
            vertices.append(p)
    tangents=[]
    for i,p in enumerate(vertices):
        q=vertices[(i+1)%len(vertices)]
        det=cross(p,q)
        t=((q[1]-p[1])/det,(p[0]-q[0])/det)
        assert p[0]*t[0]+p[1]*t[1] == q[0]*t[0]+q[1]*t[1] == 1
        tangents.append(t)
    return shoelace(vertices),shoelace(tangents)


class AreaTests(unittest.TestCase):
    def test_explicit_polygons_verify_optimized_formula_and_rounding(self) -> None:
        self.assertEqual(geometric_polygon_areas(1),(F(2),F(4)))
        self.assertEqual(geometric_polygon_areas(2),(F(14,5),F(10,3)))
        for n in (1,2,3,4,8,16):
            exact_lower,exact_upper=geometric_polygon_areas(n)
            lower,upper=polygon_bounds(n,10**12)
            self.assertLessEqual(lower,exact_lower)
            self.assertGreaterEqual(upper,exact_upper)
            self.assertLessEqual(exact_upper-exact_lower,F(4,n*n))
            self.assertLessEqual(upper-lower,F(4,n*n)+F(2*n,10**12))

    def test_grid_counts_match_explicit_corner_enumeration(self) -> None:
        for n in (1,2,3,8,16):
            lower=sum((i+1)**2+(j+1)**2<=n*n for i in range(n) for j in range(n))
            upper=sum(i*i+j*j<=n*n for i in range(n) for j in range(n))
            self.assertEqual(grid_bounds(n),(F(4*lower,n*n),F(4*upper,n*n)))

    def test_refinement_and_independent_geometry(self) -> None:
        previous=(F(0),F(5))
        for n in (1,2,4,8,16,32,64,128):
            lower,upper=polygon_bounds(n)
            self.assertGreaterEqual(lower,previous[0])
            self.assertLessEqual(upper,previous[1])
            previous=lower,upper
        gl,gu=grid_bounds(128)
        self.assertTrue(gl<=lower<=upper<=gu)

    def test_exact_square_root_rounding(self) -> None:
        for value in (F(0),F(1),F(2),F(4),F(17,4),F(399,100)):
            low,high=floor_sqrt(value),ceil_sqrt(value)
            self.assertLessEqual(low*low,value)
            self.assertGreaterEqual(high*high,value)
            self.assertLess(value,(low+1)**2)
        lower,upper=side_bounds(F(14,5),F(10,3),10000)
        self.assertLessEqual(lower*lower,F(14,5))
        self.assertGreaterEqual(upper*upper,F(10,3))

    def test_candidate_filter_matches_blind_rational_enumeration(self) -> None:
        for n in (1,4,16,64):
            lower,upper=polygon_bounds(n)
            expected={F(p,q) for q in range(1,41) for p in range(q,2*q+1)
                      if lower<=F(p*p,q*q)<=upper}
            self.assertEqual(set(compatible_ratios(lower,upper,40)),expected)

    def test_compatibility_is_not_exact_equality(self) -> None:
        self.assertEqual(classify_square(F(7,4),F(3),F(16,5)),"unresolved")
        self.assertEqual(classify_square(F(3,2),F(9,4),F(9,4)),"exact")
        self.assertEqual(bracket_path(F(4),F(4))["exact_ratio"],"2")
        self.assertEqual(bracket_path(F(9,4),F(9,4))["exact_ratio"],"3/2")

    def test_resolved_path_is_certified_and_preserved(self) -> None:
        old=[]
        for n in (1,2,4,8,16,32,64,128,256):
            lower,upper=polygon_bounds(n)
            path=bracket_path(lower,upper)
            resolved=[]
            for step in path["steps"]:
                square=F(step["side"])**2
                if step["status"]=="too_small":
                    self.assertLess(square,lower)
                elif step["status"]=="too_large":
                    self.assertGreater(square,upper)
                else:
                    self.assertTrue(lower<=square<=upper)
                    continue
                resolved.append((step["side"],step["status"]))
            self.assertEqual(resolved[:len(old)],old)
            old=resolved
            a,b=F(path["left"]),F(path["right"])
            self.assertEqual(b.numerator*a.denominator-a.numerator*b.denominator,1)


class GraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"wide_u20.sqlite"
        build_strict_stage_graph(db_path=self.path,max_stage=20,max_abs_p=1000000,
            max_abs_q=1000000,max_abs_value=1000000,max_edges=None,time_limit_seconds=None,
            commit_every=20,retain_confirmed_edges=True,verbose=False)

    def test_vertex_recurrence_obeys_confirmed_operand_stages(self) -> None:
        with closing(connect_readonly(self.path)) as con:
            reader=WitnessReader(con)
            small=source_vertex(reader,2,1)
            self.assertTrue(small["complete"])
            self.assertEqual(small["completion_stage"],5)
            late=source_vertex(reader,4,3)
            self.assertFalse(late["complete"])
            self.assertEqual(late["predicted_stage"],25)
            self.assertTrue(late["prediction_match"])

    def test_area_value_landing_does_not_supply_fractional_recurrence(self) -> None:
        with closing(connect_readonly(self.path)) as con:
            reader=WitnessReader(con)
            row=intended_fraction_edge(reader,F(8,5),"+",F(6,5))
            self.assertTrue(row["result_node_present"])
            self.assertFalse(row["operand_rule_allows"])
            self.assertFalse(row["intended_edge_present"])
            self.assertTrue(reader.edges[(14,"/",5)]["present"])


if __name__=="__main__":
    unittest.main()
