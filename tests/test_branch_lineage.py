from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from moo.branch_lineage import branch_lineage_report
from moo.research_utils import connect_readonly
from moo.strict_stage_moo import build_strict_stage_graph


def _create_corpus(path: Path, *, stage: int, bound: int = 1000, max_edges=None) -> None:
    build_strict_stage_graph(
        db_path=path, max_stage=stage, max_abs_p=bound, max_abs_q=bound,
        max_abs_value=bound, max_edges=max_edges, time_limit_seconds=None,
        commit_every=stage, retain_confirmed_edges=True, verbose=False,
    )


def _create_fixture(path: Path) -> None:
    # Real complete frontiers: 4*4 is filtered at U4, while recurrence reaches
    # the same value at U16. Sparse hand-written telemetry cannot certify U16.
    _create_corpus(path, stage=16, bound=10)


class BranchLineageTests(unittest.TestCase):
    def test_absent_or_unconfirmed_prime_has_only_an_arithmetic_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "u4.sqlite"
            _create_corpus(path, stage=4)
            with closing(connect_readonly(path)) as conn:
                entries = {e["value"]: e for e in branch_lineage_report(
                    conn, branch="prime", limit=11)["entries"]}
        self.assertFalse(entries[11]["value_node"]["present"])
        self.assertTrue(entries[5]["value_node"]["present"])
        for value in (5, 11):
            entry = entries[value]
            self.assertNotIn("prime_branch_member", entry["moo_reading"])
            self.assertEqual(entry["arithmetic_classification"], "prime")
            self.assertEqual(entry["classification_basis"]["arithmetic_label"], "arithmetic_shortcut")
            self.assertFalse(entry["irreducibility_evidence"]["eligible"])

    def test_confirmed_prime_requires_a_complete_retention_eligible_product_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "u5.sqlite"
            _create_corpus(path, stage=5)
            with closing(connect_readonly(path)) as conn:
                five = branch_lineage_report(conn, branch="prime", limit=5)["entries"][-1]
        self.assertIn("prime_branch_member", five["moo_reading"])
        self.assertTrue(five["irreducibility_evidence"]["eligible"])
        self.assertEqual(five["classification_basis"]["prime_branch_membership"],
                         "inferred_from_field_absence")

    def test_filtered_product_absence_does_not_certify_irreducibility(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bounded.sqlite"
            _create_corpus(path, stage=5, bound=2)
            with closing(connect_readonly(path)) as conn:
                entries = {e["value"]: e for e in branch_lineage_report(
                    conn, branch="prime", limit=5)["entries"]}
        for value in (4, 5):
            entry = entries[value]
            self.assertTrue(entry["counting_spine_witnessed"])
            self.assertFalse(entry["product_branch_witness"]["present"])
            self.assertFalse(entry["irreducibility_evidence"]["eligible"])
            self.assertNotIn("prime_branch_member", entry["moo_reading"])
        self.assertEqual(entries[4]["arithmetic_classification"], "composite")
        self.assertEqual(entries[5]["arithmetic_classification"], "prime")
        self.assertEqual(entries[4]["classification_basis"]["product_branch"],
                         "inferred_from_generator_rule")

    def test_unknown_retention_rule_does_not_certify_prime_membership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unknown.sqlite"
            _create_corpus(path, stage=5)
            with closing(sqlite3.connect(path)) as conn:
                conn.execute("DELETE FROM meta WHERE key = 'config_json'")
                conn.commit()
            with closing(connect_readonly(path)) as conn:
                five = branch_lineage_report(conn, branch="prime", limit=5)["entries"][-1]
        self.assertNotIn("prime_branch_member", five["moo_reading"])
        self.assertIsNone(five["irreducibility_evidence"]["result_retention_eligible"])

    def test_arithmetic_factorization_does_not_make_future_operands_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "u4.sqlite"
            _create_corpus(path, stage=4)
            with closing(connect_readonly(path)) as conn:
                entry = branch_lineage_report(conn, branch="prime", limit=22)["entries"][-1]
        self.assertFalse(entry["product_branch_permitted"])
        self.assertIn("product_landing_not_yet_permitted_by_recurrence", entry["moo_reading"])
        self.assertNotIn("product_landing_permitted_but_not_witnessed_in_field", entry["moo_reading"])

    def test_product_witness_search_includes_alternate_factor_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "u4.sqlite"
            _create_corpus(path, stage=4)
            with closing(connect_readonly(path)) as conn:
                twelve = branch_lineage_report(conn, branch="prime", limit=12)["entries"][-1]
        self.assertIn("witnessed_through_product_branch", twelve["moo_reading"])
        self.assertNotIn("product_landing_permitted_but_not_witnessed_in_field", twelve["moo_reading"])
        witness = twelve["product_branch_witness"]
        self.assertEqual({(e["left"], e["right"]) for e in witness["edge_refs"]}, {(3, 4), (4, 3)})
        self.assertEqual(witness["edge_count"], 2)
        self.assertEqual(witness["stage"], 4)

    def test_all_retained_product_routes_remain_inspectable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "u18.sqlite"
            _create_corpus(path, stage=18)
            with closing(connect_readonly(path)) as conn:
                thirty_six = branch_lineage_report(conn, branch="prime", limit=36)["entries"][-1]
        witness = thirty_six["product_branch_witness"]
        self.assertEqual({(e["left"], e["right"]) for e in witness["edge_refs"]},
                         {(2, 18), (18, 2), (3, 12), (12, 3), (4, 9), (9, 4), (6, 6)})
        self.assertEqual(witness["edge_count"], 7)
        self.assertEqual(witness["stage"], 6)

    def test_arithmetic_factorization_does_not_invent_a_filtered_witness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bounded.sqlite"
            _create_corpus(path, stage=12, bound=2)
            with closing(connect_readonly(path)) as conn:
                twelve = branch_lineage_report(conn, branch="prime", limit=12)["entries"][-1]
        self.assertFalse(twelve["product_branch_witness"]["present"])
        self.assertTrue(twelve["counting_spine_witnessed"])
        self.assertNotIn("witnessed_through_product_branch", twelve["moo_reading"])

    def test_prime_spine_witness_requires_reached_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "u4.sqlite"
            _create_corpus(path, stage=4)
            with closing(connect_readonly(path)) as conn:
                entries = {e["value"]: e for e in branch_lineage_report(
                    conn, branch="prime", limit=12)["entries"]}
        for value in (2, 3, 4):
            self.assertTrue(entries[value]["counting_spine_witnessed"])
        for value in (5, 12):
            self.assertFalse(entries[value]["counting_spine_witnessed"])
            self.assertNotIn("witnessed_through_counting_spine", entries[value]["moo_reading"])

    def test_later_recurrence_supplies_the_spine_witness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "u12.sqlite"
            _create_corpus(path, stage=12)
            with closing(connect_readonly(path)) as conn:
                twelve = branch_lineage_report(conn, branch="prime", limit=12)["entries"][-1]
        self.assertTrue(twelve["counting_spine_witnessed"])
        self.assertEqual(twelve["value_node"]["node"]["first_stage"], 4)

    def test_partial_frontier_does_not_supply_future_spine_or_operand_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "partial.sqlite"
            _create_corpus(path, stage=20, max_edges=19)
            with closing(connect_readonly(path)) as conn:
                prime = branch_lineage_report(conn, branch="prime", limit=4)["entries"]
                square = branch_lineage_report(conn, branch="square", limit=3)["entries"]
        self.assertTrue(prime[0]["counting_spine_witnessed"])
        self.assertFalse(prime[1]["counting_spine_witnessed"])
        self.assertFalse(prime[2]["counting_spine_witnessed"])
        self.assertFalse(square[1]["counting_spine_witnessed"])
        self.assertFalse(square[2]["relation_permitted"])
        self.assertIn("candidate_stage_beyond_U", square[2]["field_blockers"])

    def test_partial_stage_edges_are_not_in_the_complete_branch_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "partial-with-square.sqlite"
            _create_corpus(path, stage=20, max_edges=29)
            with closing(connect_readonly(path)) as conn:
                self.assertEqual(conn.execute(
                    "SELECT COUNT(*) FROM edges WHERE op='*' AND stage=3"
                ).fetchone()[0], 3)
                square = branch_lineage_report(conn, branch="square", limit=3)["entries"][-1]
        self.assertFalse(square["relation_permitted"])
        self.assertFalse(square["branch_witness"]["present"])
        self.assertNotIn("witnessed_through_branch", square["moo_reading"])

    def test_even_branch_records_repeated_relation_witness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                report = branch_lineage_report(conn, branch="even", limit=3)

        entry = report["entries"][2]
        self.assertEqual(entry["source"], 3)
        self.assertEqual(entry["result"], 6)
        self.assertIn("witnessed_through_branch", entry["moo_reading"])
        self.assertIn("witnessed_through_counting_spine", entry["moo_reading"])
        self.assertTrue(entry["branch_witness"]["present"])

    def test_square_branch_separates_branch_membership_from_retained_edge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                report = branch_lineage_report(conn, branch="square", limit=4)

        entry = report["entries"][3]
        self.assertEqual(entry["source"], 4)
        self.assertEqual(entry["result"], 16)
        self.assertTrue(entry["relation_permitted"])
        self.assertFalse(entry["branch_witness"]["present"])
        self.assertTrue(entry["counting_spine_witnessed"])
        self.assertIn("permitted_but_not_witnessed_in_field", entry["moo_reading"])
        self.assertIn("witnessed_through_counting_spine", entry["moo_reading"])
        self.assertIn("outside_max_abs_p", entry["field_blockers"])
        self.assertIn("outside_max_abs_value", entry["field_blockers"])

    def test_prime_branch_is_not_just_factor_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                report = branch_lineage_report(conn, branch="prime", limit=6)

        five = report["entries"][3]
        six = report["entries"][4]
        self.assertEqual(five["value"], 5)
        self.assertEqual(five["branch"], "prime")
        self.assertIn("prime_branch_member", five["moo_reading"])
        self.assertIn("irreducibility_condition", five["moo_reading"])
        self.assertIsNone(five["nontrivial_product_landing"])
        self.assertEqual(six["value"], 6)
        self.assertEqual(six["branch"], "prime")
        self.assertIn("product_branch_landing", six["moo_reading"])
        self.assertIn("witnessed_through_product_branch", six["moo_reading"])
        self.assertEqual(six["nontrivial_product_landing"], {"left": 2, "right": 3})


if __name__ == "__main__":
    unittest.main()
