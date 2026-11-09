from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from moo.graph_corpus import (
    strict_stage_expected_candidate_events,
    strict_stage_retains_result,
)
from moo.graph_evidence import GraphEvidence
from moo.strict_stage_moo import build_strict_stage_graph


def _create_fixture(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE stages("
            "stage INTEGER PRIMARY KEY, candidate_events INTEGER, retained_events INTEGER, "
            "new_nodes INTEGER, new_edges INTEGER, total_nodes INTEGER, total_edges INTEGER, "
            "elapsed_seconds REAL)"
        )
        conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute(
            "CREATE TABLE nodes("
            "node_id INTEGER PRIMARY KEY, p INTEGER, q INTEGER, label TEXT, "
            "kind TEXT, first_stage INTEGER, confirmed_stage INTEGER)"
        )
        conn.execute(
            "CREATE TABLE edges("
            "edge_id INTEGER PRIMARY KEY, stage INTEGER, op TEXT, "
            "left_node_id INTEGER, right_node_id INTEGER, result_node_id INTEGER)"
        )
        conn.executemany(
            "INSERT INTO stages VALUES(?, ?, 0, 0, 0, 0, 0, 0.0)",
            [
                (stage, strict_stage_expected_candidate_events(stage))
                for stage in range(1, 11)
            ],
        )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES('config_json', ?)",
            (
                json.dumps(
                    {
                        "generator": "strict_stage_moo_graph",
                        "max_stage": 10,
                        "max_abs_p": 100,
                        "max_abs_q": 100,
                        "max_abs_value": 100.0,
                        "retain_confirmed_edges": True,
                    },
                    sort_keys=True,
                ),
            ),
        )
        nodes = [
            (1, 1, 1, "1", "certainty", 1, 1),
            (2, 2, 1, "2", "positive_integer", 2, 2),
            (3, 3, 1, "3", "positive_integer", 3, 3),
            (4, 5, 1, "5", "positive_integer", 5, 5),
            (5, 3, 2, "3/2", "rational", 3, None),
            (6, 5, 2, "5/2", "rational", 5, None),
            (7, 20, 1, "20", "positive_integer", 20, 20),
            (8, 25, 1, "25", "positive_integer", 25, 25),
            (9, 45, 1, "45", "positive_integer", 45, 45),
        ]
        conn.executemany(
            "INSERT INTO nodes(node_id, p, q, label, kind, first_stage, confirmed_stage) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            nodes,
        )
        edges = [
            (1, 3, "+", 2, 3, 4),
            (2, 3, "+", 3, 2, 4),
        ]
        conn.executemany(
            "INSERT INTO edges(edge_id, stage, op, left_node_id, right_node_id, result_node_id) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            edges,
        )
        conn.commit()
    finally:
        conn.close()


class GraphEvidenceTests(unittest.TestCase):
    def test_edge_witness_reports_directed_complete_addition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                witness = GraphEvidence(conn).edge_witness(
                    left=2,
                    op="+",
                    right=3,
                    result=5,
                    allow_commuted=True,
                )
            finally:
                conn.close()

        self.assertTrue(witness["present"])
        self.assertEqual(witness["edge_count"], 2)
        self.assertEqual(witness["expected_directed_edges"], 2)
        self.assertEqual(witness["status"], "complete_directed")
        self.assertEqual(witness["candidate_stage"], 3)
        self.assertTrue(witness["eligible_by_stage"])
        self.assertEqual(witness["edge_refs"][0], {"edge_id": 1, "stage": 3})

    def test_edge_truth_cache_is_independent_of_display_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                evidence = GraphEvidence(conn)
                limited = evidence.edge_witness(
                    left=2,
                    op="+",
                    right=3,
                    result=5,
                    allow_commuted=True,
                    claim_id="limited-call",
                    edge_limit=1,
                )
                expanded = evidence.edge_witness(
                    left=2,
                    op="+",
                    right=3,
                    result=5,
                    allow_commuted=True,
                    edge_limit=8,
                )
            finally:
                conn.close()

        self.assertEqual(limited["edge_count"], 2)
        self.assertEqual(len(limited["edge_refs"]), 1)
        self.assertTrue(limited["edge_refs_truncated"])
        self.assertEqual(expanded["edge_count"], 2)
        self.assertEqual(len(expanded["edge_refs"]), 2)
        self.assertFalse(expanded["edge_refs_truncated"])
        self.assertIsNone(expanded["claim_id"])

    def test_partial_frontier_is_not_reported_as_stage_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "partial.sqlite"
            build_strict_stage_graph(
                db_path=db_path,
                max_stage=10,
                max_abs_p=100,
                max_abs_q=100,
                max_abs_value=None,
                max_edges=7,
                time_limit_seconds=None,
                commit_every=10,
                retain_confirmed_edges=True,
                verbose=False,
            )
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                witness = GraphEvidence(conn, corpus_stage=2).edge_witness(
                    left=2,
                    op="*",
                    right=1,
                    result=2,
                )
            finally:
                conn.close()

        self.assertEqual(witness["recorded_corpus_stage"], 2)
        self.assertEqual(witness["complete_corpus_stage"], 1)
        self.assertEqual(witness["corpus_stage"], 1)
        self.assertFalse(witness["eligible_by_stage"])
        self.assertEqual(witness["blocker"], "candidate_stage_in_incomplete_frontier")

    def test_result_retention_aperture_explains_intentional_absence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "bounded.sqlite"
            build_strict_stage_graph(
                db_path=db_path,
                max_stage=4,
                max_abs_p=200,
                max_abs_q=200,
                max_abs_value=4.0,
                max_edges=None,
                time_limit_seconds=None,
                commit_every=10,
                retain_confirmed_edges=True,
                verbose=False,
            )
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                witness = GraphEvidence(conn).edge_witness(
                    left=4,
                    op="+",
                    right=1,
                    result=5,
                )
            finally:
                conn.close()

        self.assertTrue(witness["eligible_by_stage"])
        self.assertFalse(witness["eligible_by_retention"])
        self.assertFalse(witness["eligible"])
        self.assertIn("result", witness["missing_nodes"])
        self.assertEqual(witness["blocker"], "result_outside_retention_aperture")

    def test_missing_retention_config_never_claims_absence_is_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("DELETE FROM meta WHERE key = 'config_json'")
                conn.commit()
                witness = GraphEvidence(conn).edge_witness(
                    left=2,
                    op="*",
                    right=2,
                    result=4,
                )
            finally:
                conn.close()

        self.assertTrue(witness["eligible_by_stage"])
        self.assertIsNone(witness["eligible_by_retention"])
        self.assertFalse(witness["eligible"])
        self.assertEqual(witness["stage_aperture"]["retention_config_status"], "missing")
        self.assertEqual(witness["blocker"], "retention_config_unavailable")

    def test_shared_retention_rule_covers_each_bound_and_confirmed_exemption(self) -> None:
        self.assertFalse(
            strict_stage_retains_result(
                (6, 1),
                stage=4,
                max_abs_p=5,
                max_abs_q=20,
                max_abs_value=None,
                retain_confirmed_edges=False,
            )
        )
        self.assertFalse(
            strict_stage_retains_result(
                (1, 6),
                stage=4,
                max_abs_p=20,
                max_abs_q=5,
                max_abs_value=None,
                retain_confirmed_edges=False,
            )
        )
        self.assertFalse(
            strict_stage_retains_result(
                (11, 2),
                stage=4,
                max_abs_p=20,
                max_abs_q=20,
                max_abs_value=5.0,
                retain_confirmed_edges=False,
            )
        )
        self.assertTrue(
            strict_stage_retains_result(
                (5, 1),
                stage=4,
                max_abs_p=5,
                max_abs_q=5,
                max_abs_value=5.0,
                retain_confirmed_edges=False,
            )
        )
        self.assertTrue(
            strict_stage_retains_result(
                (4, 1),
                stage=4,
                max_abs_p=0,
                max_abs_q=1,
                max_abs_value=0.0,
                retain_confirmed_edges=True,
            )
        )

    def test_edge_witness_marks_rational_operands_ineligible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                witness = GraphEvidence(conn).edge_witness(
                    left=Fraction(3, 2),
                    op="+",
                    right=1,
                    result=Fraction(5, 2),
                )
            finally:
                conn.close()

        self.assertFalse(witness["present"])
        self.assertFalse(witness["eligible_by_stage"])
        self.assertEqual(witness["blocker"], "operand_not_positive_spine")
        self.assertEqual(witness["missing_nodes"], [])

    def test_edge_witness_marks_stage_aperture_miss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                witness = GraphEvidence(conn).edge_witness(
                    left=20,
                    op="+",
                    right=25,
                    result=45,
                    allow_commuted=True,
                )
            finally:
                conn.close()

        self.assertFalse(witness["present"])
        self.assertEqual(witness["candidate_stage"], 25)
        self.assertFalse(witness["eligible_by_stage"])
        self.assertEqual(witness["blocker"], "candidate_stage_beyond_corpus")


if __name__ == "__main__":
    unittest.main()
