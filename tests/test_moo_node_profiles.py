from __future__ import annotations

from contextlib import closing, redirect_stderr, redirect_stdout
from fractions import Fraction
import io
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from moo.node_profiles import (
    build_index,
    compare_profiles,
    find_members,
    load_association,
    load_certificate,
    node_profile,
    verify_source,
)
from moo.graph_query import main as graph_query_main
from moo.research_utils import file_sha256
from moo.strict_stage_moo import build_strict_stage_graph


def _build_corpus(path: Path, *, stage: int = 160, narrow: bool = False) -> None:
    build_strict_stage_graph(
        db_path=path,
        max_stage=stage,
        max_abs_p=10**9,
        max_abs_q=stage,
        max_abs_value=4.0 if narrow else None,
        max_edges=None,
        time_limit_seconds=None,
        commit_every=stage,
        retain_confirmed_edges=True,
        verbose=False,
    )


def _delete_edge(path: Path, left: int, op: str, right: int, result: int | Fraction) -> None:
    result = Fraction(result)
    with closing(sqlite3.connect(path)) as conn:
        cursor = conn.execute(
            """
            DELETE FROM edges
            WHERE op=?
              AND left_node_id=(SELECT node_id FROM nodes WHERE p=? AND q=1)
              AND right_node_id=(SELECT node_id FROM nodes WHERE p=? AND q=1)
              AND result_node_id=(SELECT node_id FROM nodes WHERE p=? AND q=?)
            """,
            (op, left, right, result.numerator, result.denominator),
        )
        if cursor.rowcount != 1:
            raise AssertionError(f"Expected one directed edge to delete; got {cursor.rowcount}")
        conn.commit()


def _support(association, certificate_id="literal"):
    return next(c["support"] for c in association["certificates"] if c["id"] == certificate_id)


class NodeProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="moo-node-profile-tests-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)
        cls.source = cls.directory / "source-u160.sqlite"
        _build_corpus(cls.source)
        cls.source_hash = file_sha256(cls.source)
        cls.full_index = cls.directory / "profiles-u160.sqlite"
        cls.full_summary = build_index(cls.source, cls.full_index)
        cls.early_index = cls.directory / "profiles-u16.sqlite"
        cls.early_summary = build_index(cls.source, cls.early_index, stage=16)

    def test_square_relationship_retains_root_and_result_roles(self) -> None:
        root = node_profile(self.full_index, "6/2", family="square")
        result = node_profile(self.full_index, "9", family="square", details=True)
        self.assertEqual(root["value"], "3")
        root_associations = {item["id"]: item for item in root["associations"]}
        result_associations = {item["id"]: item for item in result["associations"]}
        self.assertEqual(root_associations["square:3"]["roles"], ["root"])
        self.assertEqual(result_associations["square:3"]["roles"], ["square"])
        self.assertEqual(result_associations["square:9"]["roles"], ["root"])
        self.assertNotIn("requests", root_associations["square:3"]["support"])
        support = result_associations["square:3"]["support"]
        self.assertEqual(support["status"], "witnessed")
        self.assertEqual(support["first_supported_stage"], 3)

        # Independently resolve the retained occurrence, rather than trusting its label.
        edge_id = _support(result_associations["square:3"])["requests"][0]["edge_refs"][0]["edge_id"]
        with closing(sqlite3.connect(self.source)) as conn:
            row = conn.execute(
                """SELECT l.p,l.q,e.op,r.p,r.q,o.p,o.q,e.stage
                   FROM edges e JOIN nodes l ON l.node_id=e.left_node_id
                   JOIN nodes r ON r.node_id=e.right_node_id
                   JOIN nodes o ON o.node_id=e.result_node_id WHERE e.edge_id=?""",
                (edge_id,),
            ).fetchone()
        self.assertEqual(row, (3, 1, "*", 3, 1, 9, 1, 3))

    def test_rational_and_zero_square_membership_do_not_license_operands(self) -> None:
        root = node_profile(self.full_index, "3/5", family="square")
        output = node_profile(self.full_index, "9/25", family="square")
        self.assertTrue(root["node"]["present"])
        self.assertTrue(output["node"]["present"])
        self.assertIn("square:3/5", {item["id"] for item in output["associations"]})
        fractional = load_association(self.full_index, "square:3/5")
        self.assertEqual(fractional["parameters"], {"root": "3/5", "square": "9/25"})
        self.assertEqual(fractional["support"]["mathematical_membership"], "exact")
        self.assertEqual(fractional["support"]["status"], "witnessed")
        self.assertEqual(fractional["support"]["first_supported_stage"], 25)
        self.assertEqual(_support(fractional)["status"], "unwitnessed")
        self.assertIn("operand_not_positive_spine", _support(fractional)["blockers"])
        self.assertEqual(_support(fractional, "integer_ratio")["first_supported_stage"], 25)

        zero = node_profile(self.full_index, "0", family="square")
        self.assertEqual(zero["association_count"], 1)
        self.assertEqual(set(zero["associations"][0]["roles"]), {"root", "square"})
        self.assertEqual(zero["associations"][0]["support"]["status"], "unwitnessed")

    def test_checkpoint_filters_physically_later_edges_and_nodes(self) -> None:
        late = load_association(self.full_index, "shell:5,12,13")
        early = load_association(self.early_index, "shell:5,12,13")
        self.assertEqual(late["support"]["status"], "witnessed")
        self.assertEqual(late["support"]["first_supported_stage"], 144)
        self.assertEqual(early["support"]["status"], "partial")
        self.assertIsNone(early["support"]["first_supported_stage"])
        addition = next(r for r in _support(early)["requests"] if r["role"] == "shell_sum")
        self.assertGreater(addition["source_edge_count"], 0)
        self.assertFalse(addition["witnessed"])
        self.assertEqual(addition["edge_refs"], [])

        late_node = node_profile(self.early_index, "289")["node"]
        self.assertTrue(late_node["in_saved_corpus"])
        self.assertFalse(late_node["present"])
        self.assertEqual(late_node["status_at_checkpoint"], "not_observed")
        self.assertEqual(late_node["status"], "not_observed")
        self.assertIsNone(late_node["first_stage"])
        self.assertIsNone(late_node["first_edge_id"])
        self.assertIsNone(late_node["confirmed_stage"])
        self.assertEqual(late_node["confirmation_threshold"], 289)
        self.assertEqual(late_node["saved_source_node"]["first_stage"], 17)
        existing_future_integer = node_profile(self.early_index, "25")["node"]
        self.assertTrue(existing_future_integer["present"])
        self.assertEqual(existing_future_integer["status_at_checkpoint"], "speculative")
        self.assertIsNone(existing_future_integer["confirmed_stage"])
        self.assertEqual(existing_future_integer["confirmation_threshold"], 25)

    def test_expanded_square_certificate_requires_root_binding(self) -> None:
        copied = self.directory / "missing-root-binding.sqlite"
        index = self.directory / "missing-root-binding-profiles.sqlite"
        shutil.copy2(self.source, copied)
        _delete_edge(copied, 7, "+", 2, 9)
        build_index(copied, index, square_height=9, max_radius=0, spiral_steps=0)
        self.assertTrue(node_profile(index, "9")["node"]["present"])
        self.assertTrue(node_profile(index, "81")["node"]["present"])
        for route in ("generic_expanded_left", "generic_expanded_paired"):
            support = load_certificate(index, f"square:9#route:{route}")["support"]
            self.assertEqual(support["status"], "partial")
            self.assertIsNone(support["first_supported_stage"])
            self.assertFalse(next(r for r in support["requests"] if r["role"] == "binding:root_sum")["witnessed"])
        self.assertEqual(load_certificate(index, "square:9#literal")["support"]["status"], "witnessed")

    def test_spiral_lineage_does_not_require_later_direct_target_shell(self) -> None:
        step = load_association(self.early_index, "spiral:4,3,5:2")
        shell = load_association(self.early_index, "shell:7,24,25")
        self.assertEqual(step["parameters"]["iteration"], 2)
        self.assertEqual(step["support"]["status"], "witnessed")
        self.assertEqual(step["support"]["first_supported_stage"], 16)
        self.assertNotEqual(shell["support"]["status"], "witnessed")
        self.assertIsNone(shell["support"]["first_supported_stage"])
        shell_sum = next(r for r in _support(shell)["requests"] if r["role"] == "shell_sum")
        self.assertEqual(shell_sum["candidate_stage"], 576)

    def test_negative_output_is_visible_but_cannot_feed_next_spiral_step(self) -> None:
        third = load_association(self.full_index, "spiral:4,3,5:3")
        self.assertEqual(third["parameters"]["x"], "-44")
        self.assertEqual(third["parameters"]["y"], "117")
        self.assertEqual(third["support"]["status"], "witnessed")
        self.assertEqual(third["support"]["first_supported_stage"], 96)
        self.assertTrue(node_profile(self.full_index, "-44")["node"]["present"])

        third_shell = load_association(self.full_index, "shell:-44,117,125")
        fourth = load_association(self.full_index, "spiral:4,3,5:4")
        self.assertNotEqual(third_shell["support"]["status"], "witnessed")
        self.assertIn("operand_not_positive_spine", _support(third_shell)["blockers"])
        self.assertNotEqual(fourth["support"]["status"], "witnessed")
        self.assertFalse(_support(fourth, "scalar_lineage")["local_requests_complete"])
        signed_request = next(r for r in _support(fourth, "scalar_lineage")["requests"] if r["role"] == "ac")
        self.assertEqual(signed_request["left"], "-44")
        self.assertEqual(signed_request["blocker"], "operand_not_positive_spine")

    def test_deleting_prior_transition_breaks_lineage_despite_complete_local_step(self) -> None:
        copied = self.directory / "missing-prior-transition.sqlite"
        index = self.directory / "missing-prior-transition-profiles.sqlite"
        shutil.copy2(self.source, copied)
        _delete_edge(copied, 16, "-", 9, 7)
        build_index(copied, index, square_height=0, max_radius=0, spiral_steps=3)
        third = load_certificate(index, "spiral:4,3,5:3#scalar_lineage")["support"]
        self.assertTrue(third["local_requests_complete"])
        self.assertEqual(third["local_first_supported_stage"], 96)
        self.assertNotEqual(third["status"], "witnessed")
        self.assertIsNone(third["first_supported_stage"])
        self.assertIn("dependency_not_witnessed:spiral:4,3,5:2#scalar_lineage", third["blockers"])
        self.assertEqual(node_profile(index, "-44", family="spiral", witnessed_only=True)["association_count"], 0)

    def test_deleting_square_edge_preserves_value_and_mathematical_association(self) -> None:
        copied = self.directory / "missing-square-edge.sqlite"
        index = self.directory / "missing-square-edge-profiles.sqlite"
        shutil.copy2(self.source, copied)
        _delete_edge(copied, 3, "*", 3, 9)
        build_index(copied, index, square_height=3, max_radius=0, spiral_steps=0)
        profile = node_profile(index, "9")
        self.assertTrue(profile["node"]["present"])
        support = load_association(index, "square:3")["support"]
        self.assertEqual(support["mathematical_membership"], "exact")
        self.assertEqual(support["status"], "unwitnessed")
        self.assertEqual(node_profile(index, "9", witnessed_only=True)["association_count"], 0)
        literal = load_certificate(index, "square:3#literal")["support"]
        self.assertNotEqual(literal["requests"][0]["blocker"], "result_outside_retention_aperture")

    def test_scaled_shells_remain_distinct_and_normalized_shell_is_not_literal_witness(self) -> None:
        original = load_association(self.full_index, "shell:3,4,5")
        scaled = load_association(self.full_index, "shell:6,8,10")
        self.assertEqual(original["support"]["first_supported_stage"], 16)
        self.assertEqual(scaled["support"]["first_supported_stage"], 64)
        for item in (original, scaled):
            parameters = item["parameters"]
            self.assertEqual(Fraction(parameters["x"]) / Fraction(parameters["r"]), Fraction(3, 5))
            self.assertEqual(Fraction(parameters["y"]) / Fraction(parameters["r"]), Fraction(4, 5))
        unit = load_association(self.full_index, "shell:3/5,4/5,1")
        self.assertEqual(unit["support"]["mathematical_membership"], "exact")
        self.assertEqual(unit["support"]["status"], "witnessed")
        self.assertEqual(unit["support"]["first_supported_stage"], 25)
        self.assertNotEqual(_support(unit)["status"], "witnessed")
        self.assertIn("operand_not_positive_spine", _support(unit)["blockers"])
        self.assertEqual(_support(unit, "normalize:3,4,5")["first_supported_stage"], 25)
        self.assertEqual(_support(unit, "normalize:6,8,10")["first_supported_stage"], 100)

    def test_comparison_and_intersection_distinguish_shared_families_from_shared_instances(self) -> None:
        comparison = compare_profiles(self.full_index, ["3", "9", "6/2"])
        self.assertEqual(comparison["values"], ["3", "9"])
        self.assertIn("square", comparison["common_families"])
        self.assertIn("square:3", comparison["common_associations"])
        self.assertNotIn("square:9", comparison["common_associations"])
        mathematical = find_members(self.full_index, ["shell", "spiral"])
        witnessed = find_members(self.full_index, ["shell", "spiral"], witnessed_only=True)
        self.assertIn("-44", mathematical["values"])
        self.assertNotIn("-44", witnessed["values"])
        self.assertIn("25", witnessed["values"])
        self.assertTrue(set(witnessed["values"]).issubset(mathematical["values"]))
        self.assertEqual(mathematical["values"], sorted(mathematical["values"], key=Fraction))

    def test_missing_normalization_witness_preserves_other_route_without_mixing_certificates(self) -> None:
        copied = self.directory / "missing-normalization.sqlite"
        shutil.copy2(self.source, copied)
        _delete_edge(copied, 9, "/", 25, Fraction(9, 25))
        early = self.directory / "normalization-u25.sqlite"
        later = self.directory / "normalization-u100.sqlite"
        for stage, index in ((25, early), (100, later)):
            build_index(copied, index, square_height=5, max_radius=10, spiral_steps=0, stage=stage)
        identifier = "shell:3/5,4/5,1"
        initial = load_association(early, identifier)
        self.assertEqual(initial["support"]["status"], "partial")
        self.assertIsNone(initial["support"]["first_supported_stage"])
        recovered = load_association(later, identifier)
        self.assertEqual(recovered["support"]["status"], "witnessed")
        self.assertEqual(recovered["support"]["first_supported_stage"], 100)
        self.assertEqual(_support(recovered, "normalize:3,4,5")["status"], "partial")
        self.assertEqual(_support(recovered, "normalize:6,8,10")["status"], "witnessed")
        square = load_association(later, "square:3/5")
        self.assertEqual(square["support"]["status"], "partial")
        self.assertTrue(node_profile(later, "9/25")["node"]["present"])
        encoded = next(r for r in _support(recovered, "normalize:6,8,10")["requests"]
                       if r["role"] == "x_square_encoding")
        edge_id = encoded["edge_refs"][0]["edge_id"]
        with closing(sqlite3.connect(copied)) as conn:
            row = conn.execute("""SELECT l.p,l.q,e.op,r.p,r.q,o.p,o.q,e.stage
                FROM edges e JOIN nodes l ON l.node_id=e.left_node_id
                JOIN nodes r ON r.node_id=e.right_node_id
                JOIN nodes o ON o.node_id=e.result_node_id WHERE e.edge_id=?""", (edge_id,)).fetchone()
        self.assertEqual(row, (36, 1, "/", 100, 1, 9, 25, 100))

    def test_v1_snapshot_stays_literal_only_and_readable(self) -> None:
        legacy = self.directory / "legacy-v1.sqlite"
        literal = load_certificate(self.full_index, "square:3/5#literal")["support"]
        literal["mathematical_membership"] = "exact"
        manifest = json.loads(json.dumps(self.full_summary["manifest"]))
        manifest["schema_version"] = "moo_node_profiles.v1"
        with closing(sqlite3.connect(legacy)) as conn:
            conn.executescript("""
                CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
                CREATE TABLE nodes(value TEXT PRIMARY KEY,snapshot TEXT);
                CREATE TABLE associations(id TEXT PRIMARY KEY,family TEXT,label TEXT,
                    parameters TEXT,support TEXT,status TEXT,first_supported_stage INTEGER);
                CREATE TABLE participants(association_id TEXT,role TEXT,value TEXT);
            """)
            conn.execute("INSERT INTO metadata VALUES('manifest',?)", (json.dumps(manifest),))
            conn.execute("INSERT INTO nodes VALUES('9/25',?)",
                         (json.dumps(node_profile(self.full_index, "9/25")["node"]),))
            conn.execute("INSERT INTO associations VALUES(?,?,?,?,?,?,?)", (
                "square:3/5", "square", "Self-product of 3/5",
                json.dumps({"root": "3/5", "square": "9/25"}), json.dumps(literal), "unwitnessed", None))
            conn.executemany("INSERT INTO participants VALUES('square:3/5',?,?)",
                             [("root", "3/5"), ("square", "9/25")])
            conn.commit()
        before = file_sha256(legacy)
        profile = node_profile(legacy, "9/25", details=True)
        self.assertEqual(profile["associations"][0]["support"]["status"], "unwitnessed")
        self.assertEqual(len(profile["associations"][0]["certificates"]), 1)
        self.assertTrue(load_certificate(legacy, "square:3/5#literal")["legacy_snapshot"])
        with self.assertRaisesRegex(ValueError, "Certificate not indexed"):
            load_certificate(legacy, "square:3/5#integer_ratio")
        self.assertEqual(file_sha256(legacy), before)

    def test_unindexed_value_is_unknown_even_when_it_exists_in_source(self) -> None:
        with closing(sqlite3.connect(self.source)) as conn:
            self.assertIsNotNone(conn.execute("SELECT node_id FROM nodes WHERE p=37 AND q=1").fetchone())
        profile = node_profile(self.full_index, "37")
        self.assertEqual(profile["associations"], [])
        self.assertIsNone(profile["node"]["present"])
        self.assertEqual(profile["node"]["reason"], "not_in_indexed_participants")
        self.assertIn("not mathematical nonmembership", profile["interpretation"]["absence"])

    def test_retention_exclusion_is_not_claimed_as_mathematical_failure(self) -> None:
        narrow = self.directory / "narrow-u16.sqlite"
        index = self.directory / "narrow-profiles.sqlite"
        _build_corpus(narrow, stage=16, narrow=True)
        build_index(narrow, index, square_height=3, max_radius=0, spiral_steps=0)
        self.assertTrue(node_profile(index, "9")["node"]["present"])
        support = load_association(index, "square:3")["support"]
        self.assertEqual(support["mathematical_membership"], "exact")
        self.assertEqual(support["status"], "unwitnessed")
        self.assertIn("result_outside_retention_aperture", load_certificate(index, "square:3#literal")["support"]["blockers"])

    def test_incomplete_frontier_clamps_evidence_even_with_later_stored_rows(self) -> None:
        copied = self.directory / "incomplete-frontier.sqlite"
        index = self.directory / "incomplete-frontier-profiles.sqlite"
        shutil.copy2(self.source, copied)
        with closing(sqlite3.connect(copied)) as conn:
            conn.execute("UPDATE stages SET candidate_events=0 WHERE stage=16")
            conn.commit()
        summary = build_index(copied, index, square_height=16, max_radius=0, spiral_steps=0)
        self.assertEqual(summary["manifest"]["source"]["recorded_stage"], 160)
        self.assertEqual(summary["manifest"]["source"]["checkpoint"], 15)
        support = load_association(index, "square:16")["support"]
        self.assertEqual(support["status"], "unwitnessed")
        literal = load_certificate(index, "square:16#literal")["support"]
        self.assertIn("candidate_stage_in_incomplete_frontier", literal["blockers"])
        self.assertGreater(literal["requests"][0]["source_edge_count"], 0)
        self.assertFalse(node_profile(index, "256")["node"]["present"])

    def test_build_and_queries_leave_source_unchanged_and_refuse_overwrite(self) -> None:
        self.assertEqual(file_sha256(self.source), self.source_hash)
        self.assertEqual(self.full_summary["manifest"]["source"]["sha256"], self.source_hash)
        original_index_hash = file_sha256(self.full_index)
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            build_index(self.source, self.full_index)
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            build_index(self.source, self.source)
        self.assertEqual(file_sha256(self.full_index), original_index_hash)
        self.assertEqual(file_sha256(self.source), self.source_hash)
        verify_source(self.full_index, self.source)

    def test_index_remains_a_snapshot_and_explicit_source_verification_detects_change(self) -> None:
        copied = self.directory / "changed-after-index.sqlite"
        index = self.directory / "changed-after-index-profiles.sqlite"
        shutil.copy2(self.source, copied)
        build_index(copied, index, square_height=3, max_radius=0, spiral_steps=0)
        _delete_edge(copied, 3, "*", 3, 9)
        with self.assertRaisesRegex(ValueError, "different source snapshot"):
            verify_source(index, copied)
        self.assertEqual(load_association(index, "square:3")["support"]["status"], "witnessed")

    def test_existing_graph_query_attaches_profiles_and_comparisons(self) -> None:
        base = ["--db", str(self.source), "--associations", str(self.full_index)]
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = graph_query_main([*base, "--node", "9"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["node"]["frac"], "9")
        self.assertEqual(payload["associations"]["value"], "9")
        self.assertIn("square:3", {a["id"] for a in payload["associations"]["associations"]})

        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = graph_query_main([*base, "--compare", "3", "9"])
        self.assertEqual(exit_code, 0)
        comparison = json.loads(output.getvalue())["associations"]
        self.assertEqual(comparison["values"], ["3", "9"])
        self.assertIn("square:3", comparison["common_associations"])

    def test_existing_graph_query_rejects_index_from_another_source_snapshot(self) -> None:
        copied = self.directory / "different-query-source.sqlite"
        shutil.copy2(self.source, copied)
        _delete_edge(copied, 3, "*", 3, 9)
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            with self.assertRaises(SystemExit) as caught:
                graph_query_main([
                    "--db", str(copied), "--associations", str(self.full_index), "--node", "9",
                ])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("different source snapshot", errors.getvalue())

    def test_uncheckpointed_wal_is_rejected_without_mutating_source(self) -> None:
        copied = self.directory / "wal-source.sqlite"
        saved_index = self.directory / "checkpointed-wal-profiles.sqlite"
        rejected_index = self.directory / "uncheckpointed-wal-profiles.sqlite"
        shutil.copy2(self.source, copied)
        wal = Path(str(copied) + "-wal")
        # Keep the writer open so closing a reader cannot checkpoint the last connection.
        with closing(sqlite3.connect(copied)) as writer:
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("PRAGMA wal_autocheckpoint=0")
            build_index(copied, saved_index, square_height=3, max_radius=0, spiral_steps=0)
            main_hash = file_sha256(copied)
            cursor = writer.execute(
                """DELETE FROM edges WHERE op='*'
                   AND left_node_id=(SELECT node_id FROM nodes WHERE p=3 AND q=1)
                   AND right_node_id=(SELECT node_id FROM nodes WHERE p=3 AND q=1)"""
            )
            self.assertEqual(cursor.rowcount, 1)
            writer.commit()
            self.assertGreater(wal.stat().st_size, 0)
            self.assertEqual(file_sha256(copied), main_hash)
            wal_hash = file_sha256(wal)

            with self.assertRaisesRegex(ValueError, "uncheckpointed WAL"):
                verify_source(saved_index, copied)
            with self.assertRaisesRegex(ValueError, "uncheckpointed WAL"):
                build_index(copied, rejected_index, square_height=3, max_radius=0, spiral_steps=0)

            self.assertFalse(rejected_index.exists())
            self.assertEqual(file_sha256(copied), main_hash)
            self.assertEqual(file_sha256(wal), wal_hash)
            self.assertEqual(load_association(saved_index, "square:3")["support"]["status"], "witnessed")


if __name__ == "__main__":
    unittest.main()
