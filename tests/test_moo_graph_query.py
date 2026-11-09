from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from moo.graph_query import inspect_node, later_confirmed_nodes
from moo.research_utils import connect_readonly
from moo.strict_stage_moo import build_strict_stage_graph


class ConfirmationQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)

    def build(self, stage: int, *, max_edges=None) -> Path:
        path = Path(self.scratch.name) / f"u{stage}.sqlite"
        build_strict_stage_graph(
            db_path=path, max_stage=stage, max_abs_p=100, max_abs_q=100,
            max_abs_value=100, max_edges=max_edges, time_limit_seconds=None,
            commit_every=stage, retain_confirmed_edges=True, verbose=False,
        )
        return path

    def test_u3_excludes_future_confirmations_without_erasing_their_schedule(self) -> None:
        with closing(connect_readonly(self.build(3))) as conn:
            confirmed = later_confirmed_nodes(conn, limit=20)
            self.assertEqual([r["p"] for r in confirmed], [2, 3])
            future = inspect_node(conn, (9, 1), limit=8)
            self.assertEqual(future["node"]["confirmed_stage"], 9)

    def test_reached_confirmations_preserve_observed_lag(self) -> None:
        with closing(connect_readonly(self.build(6))) as conn:
            confirmed = later_confirmed_nodes(conn, limit=20)
            self.assertEqual([r["p"] for r in confirmed], [2, 3, 4, 5, 6])
            six = next(r for r in confirmed if r["p"] == 6)
            self.assertEqual(six["first_stage"], 3)
            self.assertEqual(six["confirmed_stage"], 6)
            self.assertEqual(six["speculative_for_stages"], 3)

    def test_partial_frontier_uses_last_complete_stage_not_requested_maximum(self) -> None:
        with closing(connect_readonly(self.build(20, max_edges=19))) as conn:
            self.assertEqual(conn.execute("SELECT MAX(stage) FROM stages").fetchone()[0], 3)
            self.assertEqual([r["p"] for r in later_confirmed_nodes(conn, limit=20)], [2])

    def test_missing_stage_evidence_does_not_assert_confirmation(self) -> None:
        path = self.build(3)
        with closing(sqlite3.connect(path)) as conn:
            conn.execute("DROP TABLE stages")
            conn.commit()
        with closing(connect_readonly(path)) as conn:
            self.assertEqual(later_confirmed_nodes(conn, limit=20), [])


if __name__ == "__main__":
    unittest.main()
