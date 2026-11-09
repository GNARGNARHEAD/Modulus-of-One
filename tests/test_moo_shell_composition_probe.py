"""Check that shell-composition claims fail when their graph evidence fails."""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from moo.research_utils import connect_readonly, require_strict_alignment
from moo.shell_composition_probe import (
    CASES, Case, WitnessReader, audit_case, compose, exact_calibration, homogeneous,
    normalized,
)
from moo.strict_stage_moo import build_strict_stage_graph


class AlgebraTests(unittest.TestCase):
    def test_parameter_covers_independent_shell_and_endpoint(self) -> None:
        result = exact_calibration()
        self.assertTrue(result["parameter_roundtrips_pass"])
        self.assertEqual(result["composition_comparisons"], 9216)
        self.assertEqual(normalized(homogeneous(0, 1)), (-1, 0))
        with self.assertRaises(ValueError):
            homogeneous(0, 0)

    def test_sorting_is_not_compatible_with_composition(self) -> None:
        a, swapped = (3, 4, 5), (4, 3, 5)
        self.assertEqual(sorted(a[:2]), sorted(swapped[:2]))
        self.assertEqual(compose(a, a), (-7, 24, 25))
        self.assertEqual(compose(a, swapped), (0, 25, 25))
        self.assertNotEqual(normalized(compose(a, a)), normalized(compose(a, swapped)))
        self.assertEqual(normalized(compose((4, 3, 5), (4, 3, 5))),
                         normalized(compose((8, 6, 10), (8, 6, 10))))


class GraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def corpus(self, cap: float = 100000.0) -> Path:
        path = Path(self.directory.name) / f"u32_{cap}.sqlite"
        build_strict_stage_graph(
            db_path=path, max_stage=32, max_abs_p=100000, max_abs_q=100000,
            max_abs_value=cap, max_edges=None, time_limit_seconds=None,
            commit_every=10, retain_confirmed_edges=True, verbose=False,
        )
        return path

    def test_composition_is_not_direct_output_proof(self) -> None:
        with closing(connect_readonly(self.corpus())) as conn:
            reader = WitnessReader(conn)
            row = audit_case(reader, CASES[0])
            self.assertTrue(row["motifs"]["source_composition"]["complete"])
            self.assertEqual(row["motifs"]["source_composition"]["completion_stage"], 16)
            self.assertFalse(row["motifs"]["target_shell"]["complete"])
            self.assertFalse(row["motifs"]["full_closure"]["complete"])
            self.assertEqual(row["motifs"]["target_shell"]["predicted_stage_with_wide_retention"], 576)
            self.assertTrue(reader.edge(24, "*", 24)["present"])
            self.assertFalse(reader.edge(49, "+", 576)["present"])

    def test_signed_and_zero_outputs_do_not_license_reuse(self) -> None:
        with closing(connect_readonly(self.corpus())) as conn:
            reader = WitnessReader(conn)
            for case in CASES[2:4]:
                row = audit_case(reader, case)
                self.assertTrue(row["motifs"]["source_composition"]["complete"])
                self.assertFalse(row["motifs"]["target_shell"]["complete"])
                self.assertFalse(row["motifs"]["target_normalization"]["complete"])
            self.assertTrue(reader.edge(9, "-", 16)["present"])
            self.assertTrue(reader.edge(12, "-", 12)["present"])
            for a in (-7, 0):
                edge = reader.edge(a, "*", a)
                self.assertFalse(edge["present"])
                self.assertEqual(edge["reason"], "operand_not_positive_spine")
                self.assertIsNone(edge["predicted_stage_with_wide_retention"])
            for case in CASES[4:6]:
                self.assertFalse(audit_case(reader, case)["motifs"]["composition"]["complete"])

    def test_nonhit_is_rejected_even_when_every_request_is_retained(self) -> None:
        with closing(connect_readonly(self.corpus())) as conn:
            row = audit_case(WitnessReader(conn), Case("small_nonhit", (2, 1, 3), (2, 1, 3)))
            for name in ("left_shell", "right_shell", "target_shell", "full_closure"):
                motif = row["motifs"][name]
                self.assertTrue(motif["all_requested_edges_present"])
                self.assertFalse(motif["algebraic_agreement"])
                self.assertFalse(motif["complete"])
            self.assertTrue(row["motifs"]["composition"]["complete"])

    def test_checkpoint_does_not_use_future_edges_or_confirmation(self) -> None:
        with closing(connect_readonly(self.corpus())) as conn:
            early = WitnessReader(conn, 15)
            late = WitnessReader(conn, 16)
            self.assertFalse(audit_case(early, CASES[0])["motifs"]["source_composition"]["complete"])
            self.assertTrue(audit_case(late, CASES[0])["motifs"]["source_composition"]["complete"])
            self.assertTrue(early.edge(5, "*", 5)["present"])
            self.assertEqual(early.nodes["25"]["status_at_checkpoint"], "speculative")
            self.assertEqual(early.nodes["25"]["confirmed_stage"], 25)
            self.assertFalse(early.edge(25, "/", 25)["present"])
            self.assertIsNone(early.edge(7, "/", 25)["result_node_id"])
            self.assertTrue(late.edge(9, "-", 16)["present"])
            self.assertFalse(early.edge(9, "-", 16)["present"])

    def test_node_presence_and_alternate_routes_do_not_replace_deleted_event(self) -> None:
        path = self.corpus()
        with closing(connect_readonly(path)) as conn:
            edge = WitnessReader(conn).edge(12, "+", 12)["occurrences"][0]
        with closing(sqlite3.connect(path)) as conn:
            conn.execute("DELETE FROM edges WHERE edge_id=?", (edge["edge_id"],))
            conn.commit()
        with closing(connect_readonly(path)) as conn:
            reader = WitnessReader(conn)
            row = audit_case(reader, CASES[0])
            self.assertFalse(row["motifs"]["source_composition"]["complete"])
            missing = reader.edge(12, "+", 12)
            self.assertTrue(missing["value_visible"])
            self.assertEqual(missing["reason"], "no_retained_edge")
            self.assertTrue(reader.edge(3, "*", 8)["present"])

    def test_all_occurrences_are_kept_but_shared_roles_are_not_independent(self) -> None:
        path = self.corpus()
        with closing(sqlite3.connect(path)) as conn:
            conn.execute(
                "INSERT INTO edges(stage,op,left_node_id,right_node_id,result_node_id) "
                "SELECT 17,op,left_node_id,right_node_id,result_node_id FROM edges "
                "WHERE op='+' AND left_node_id=(SELECT node_id FROM nodes WHERE p=12 AND q=1) "
                "AND right_node_id=left_node_id")
            conn.commit()
        with closing(connect_readonly(path)) as conn:
            reader = WitnessReader(conn)
            row = audit_case(reader, CASES[0])
            self.assertEqual(len(reader.edge(12, "+", 12)["occurrences"]), 2)
            joint = row["motifs"]["source_composition"]
            self.assertEqual(joint["completion_stage"], 16)
            self.assertLess(joint["distinct_requests"], len(joint["requests"]))

    def test_retention_and_late_confirmation_are_separate_failures(self) -> None:
        with closing(connect_readonly(self.corpus(4.0))) as conn:
            reader = WitnessReader(conn)
            edge = reader.edge(4, "*", 4)
            self.assertTrue(edge["value_visible"])
            self.assertFalse(edge["present"])
            self.assertFalse(audit_case(reader, CASES[0])["motifs"]["source_composition"]["complete"])
        path = self.corpus()
        with closing(sqlite3.connect(path)) as conn:
            conn.execute("UPDATE nodes SET confirmed_stage=20 WHERE p=4 AND q=1")
            conn.commit()
        with closing(connect_readonly(path)) as conn:
            with self.assertRaises(SystemExit):
                require_strict_alignment(conn)
            edge = WitnessReader(conn).edge(4, "*", 4)
            self.assertFalse(edge["present"])
            self.assertEqual(edge["reason"], "invalid_saved_event")
            self.assertEqual(len(edge["rejected_occurrences"]), 1)


if __name__ == "__main__":
    unittest.main()
