"""Independent geometry and relation-overlap checks for the bounded probe."""

from collections import Counter
from copy import deepcopy
from fractions import Fraction
import unittest

from moo.relation_geometry_probe import (
    DELTA, FIRST_TURN, SECOND_TURN, exact_graph_audit,
    parametric_direction_check, relation_audit,
)
from moo.unit_direction_branch_probe import count_subset_geometry, triangular_generators, unit_shell


class RelationGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.denominator, _, cls.original = triangular_generators(3)
        cls.closed = [cls.original[j] for j in (0, 3, 4, 5, 6, 7, 8)] + [DELTA]
        cls.chosen = cls.closed + [FIRST_TURN, SECOND_TURN]
        cls.result = count_subset_geometry(cls.chosen, cls.denominator, unit_shell(3, 3), retain_graph=True)

    def test_complete_edge_comparison_and_finite_improvement(self):
        for generators, result, expected in (
            (self.original, count_subset_geometry(self.original, self.denominator, unit_shell(3, 3),
                                                  retain_graph=True), (1024, 5128)),
            (self.chosen, self.result, (1020, 5188)),
        ):
            audit = exact_graph_audit(generators, result)
            self.assertEqual((audit["distinct_points"], audit["distinct_unit_pairs"]), expected)
            self.assertTrue(audit["complete_edge_sets_match"])
        self.assertEqual(exact_graph_audit(self.chosen, self.result)["unordered_pairs_tested"], 519690)

    def test_relations_overlap_and_coordinate_edges_merge(self):
        audit = relation_audit(self.chosen, self.result)
        self.assertEqual([f["distinct_edges"] for f in audit["relation_families"]], [32, 32, 8, 2])
        self.assertEqual([(o["family_indices"], o["shared_edges"])
                          for o in audit["pairwise_family_overlaps"]], [([1, 2], 2)])
        self.assertEqual(audit["union_distinct_extra_edges"], 72)
        self.assertEqual(len(audit["merged_points"]), 4)
        self.assertTrue(all(len(p["subset_masks"]) == 2 for p in audit["merged_points"]))
        self.assertEqual(audit["coordinate_edge_occurrence_loss"], 4)
        actual = Counter((row[2], row[3]) for row in self.result["point_graph"]["unit_edges"] if not row[4])
        self.assertEqual(actual, {(263640, 76895): 32, (133055, 240240): 38, (105625, 253500): 2})

    def test_independent_audit_rejects_missing_edge(self):
        corrupted = deepcopy(self.result)
        corrupted["point_graph"]["unit_edges"].pop()
        with self.assertRaises(AssertionError):
            exact_graph_audit(self.chosen, corrupted)

    def test_rational_direction_continuation_and_limit_distance(self):
        report = parametric_direction_check()
        for row in report["checked_iterates"]:
            n = row["n"]
            x, y = Fraction(row["real"]), Fraction(row["imaginary"])
            self.assertEqual(x * x + (y - 1) ** 2, Fraction(2, 2 * n * n + 2 * n + 1))
        self.assertEqual(report["checked_iterates"][1], {"n": 1, "real": "3/5", "imaginary": "4/5"})
        self.assertEqual(report["checked_iterates"][2], {"n": 2, "real": "5/13", "imaginary": "12/13"})
        self.assertFalse(report["longer_relation_residuals"][0]["zero_relation_holds"])
        self.assertTrue(report["longer_relation_residuals"][1]["zero_relation_holds"])
        self.assertFalse(report["longer_relation_residuals"][2]["zero_relation_holds"])


if __name__ == "__main__":
    unittest.main()
