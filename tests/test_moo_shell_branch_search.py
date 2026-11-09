"""Independent enumeration and real-corpus witness checks (stdlib unittest)."""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from fractions import Fraction
from pathlib import Path

from moo.research_utils import connect_readonly, require_strict_alignment
from moo.shell_branch_search import (
    Triple, WitnessReader, audit_triple, berggren_selector, blind_pairs,
    euclid_selector, from_parameter, square_factor_pairs,
)
from moo.strict_stage_moo import build_strict_stage_graph


class SelectorTests(unittest.TestCase):
    def test_independent_enumerators_and_parameter_roundtrip(self) -> None:
        brute, _ = blind_pairs(150)
        self.assertEqual(brute, square_factor_pairs(150))
        self.assertEqual(brute, euclid_selector(150)[0])
        primitives = {t for t in brute if t.primitive}
        self.assertEqual(primitives, set(berggren_selector(150)))
        for t in primitives:
            self.assertEqual(t, from_parameter(t.parameter))
        self.assertLess(sum(set(w) <= {"A"} for w in berggren_selector(150).values()),
                        len(primitives))

    def test_gap_prediction_and_invalid_parameter(self) -> None:
        t = Fraction(1+2, 2+3)
        self.assertTrue(Fraction(1, 2) < t < Fraction(2, 3))
        self.assertEqual(from_parameter(t), Triple(8, 15, 17))
        self.assertEqual(from_parameter(Fraction(4, 7)), Triple(33, 56, 65))
        self.assertEqual(from_parameter(Fraction(5, 8)), Triple(39, 80, 89))
        for invalid in (Fraction(0), Fraction(1), Fraction(-1)):
            with self.assertRaises(ValueError):
                from_parameter(invalid)


class CorpusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def corpus(self, stage: int, value_cap: float = 10000.0) -> Path:
        path = Path(self.directory.name) / f"u{stage}_{value_cap}.sqlite"
        build_strict_stage_graph(
            db_path=path, max_stage=stage, max_abs_p=10000, max_abs_q=10000,
            max_abs_value=value_cap, max_edges=None, time_limit_seconds=None,
            commit_every=10, retain_confirmed_edges=True, verbose=False,
        )
        return path

    def read(self, path: Path, t: Triple = Triple(3, 4, 5)) -> dict:
        with closing(connect_readonly(path)) as conn:
            return audit_triple(WitnessReader(conn), t)

    def test_earlier_factor_witness_and_speculative_outputs(self) -> None:
        row = self.read(self.corpus(8))
        self.assertFalse(row["direct"]["complete"])
        self.assertTrue(row["factor"]["complete"])
        self.assertTrue(row["quotient"]["complete"])
        self.assertEqual(row["factor"]["completion_stage"], 8)
        self.assertIsNotNone(row["edges"]["square_r"]["result_node"])
        self.assertEqual(row["edges"]["square_r"]["result_node"]["confirmed_stage"], 25)
        self.assertEqual(row["edges"]["square_r"]["result_node"]["status_at_observed_stage"],
                         "speculative")
        self.assertTrue(row["edges"]["factor_product"]["operands_confirmed"])

    def test_direct_witness_requires_square_operand_promotion(self) -> None:
        row = self.read(self.corpus(16))
        self.assertTrue(row["direct"]["complete"])
        self.assertEqual(row["direct"]["completion_stage"], 16)
        self.assertEqual(row["factor"]["completion_stage"], 8)
        self.assertEqual(row["edges"]["square_sum"]["right_node"]["confirmed_stage"], 16)

    def test_nearby_nonhit_with_present_edges_is_rejected(self) -> None:
        row = self.read(self.corpus(32), Triple(3, 4, 6))
        self.assertTrue(all(e["present"] for e in row["edges"].values()))
        for name in ("direct", "factor", "quotient"):
            self.assertFalse(row[name]["complete"])
        self.assertEqual(row["shell_discrepancy"], -11)
        self.assertEqual(row["factor_discrepancy"], 11)

    def test_narrow_retention_does_not_turn_node_presence_into_witnesses(self) -> None:
        row = self.read(self.corpus(32, 4.0))
        for name in ("square_x", "square_y", "square_r"):
            self.assertIsNotNone(row["edges"][name]["result_node"])
            self.assertFalse(row["edges"][name]["present"])
        self.assertFalse(row["factor"]["complete"])

    def test_missing_edge_is_distinct_from_arithmetic_truth(self) -> None:
        path = self.corpus(16)
        original = self.read(path)["edges"]["factor_product"]["edge"]["edge_id"]
        with closing(sqlite3.connect(path)) as conn:
            conn.execute("DELETE FROM edges WHERE edge_id=?", (original,))
            conn.commit()
        row = self.read(path)
        self.assertFalse(row["factor"]["complete"])
        self.assertTrue(row["quotient"]["complete"])
        self.assertTrue(row["direct"]["complete"])

    def test_late_confirmation_fails_strict_alignment(self) -> None:
        path = self.corpus(8)
        with closing(sqlite3.connect(path)) as conn:
            conn.execute("UPDATE nodes SET confirmed_stage=100 WHERE p=8 AND q=1")
            conn.commit()
        with closing(connect_readonly(path)) as conn:
            with self.assertRaises(SystemExit):
                require_strict_alignment(conn)
            row = audit_triple(WitnessReader(conn), Triple(3, 4, 5))
            self.assertFalse(row["factor"]["complete"])
            self.assertEqual(row["edges"]["factor_product"]["reason"],
                             "unconfirmed_operand_in_saved_edge")


if __name__ == "__main__":
    unittest.main()
