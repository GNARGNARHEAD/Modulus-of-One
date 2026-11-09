from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from moo.node_profiles import build_index, index_manifest, load_association, load_certificate
from moo.profile_certificates import compare_certificates
from moo.strict_stage_moo import build_strict_stage_graph


def _key(request: dict) -> tuple[str, str, str, str]:
    return tuple(request[field] for field in ("left", "op", "right", "result"))


class ProfileCertificateComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="moo-certificate-comparison-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)
        cls.source = cls.directory / "source-u100.sqlite"
        build_strict_stage_graph(
            db_path=cls.source, max_stage=100, max_abs_p=10**9, max_abs_q=100,
            max_abs_value=None, max_edges=None, time_limit_seconds=None,
            commit_every=100, retain_confirmed_edges=True, verbose=False,
        )
        cls.index = cls.directory / "profiles-u100.sqlite"
        cls.early = cls.directory / "profiles-u16.sqlite"
        build_index(cls.source, cls.index)
        build_index(cls.source, cls.early, stage=16)

    def test_rational_square_and_shell_share_four_exact_observed_requests(self) -> None:
        result = compare_certificates(
            self.index, "square:3/5#integer_ratio", "shell:3/5,4/5,1#normalize:3,4,5",
        )
        self.assertEqual(result["counts"]["shared_directed_requests"], 4)
        self.assertEqual(result["counts"]["shared_materialized_retained_edge_occurrences"], 4)
        self.assertEqual({_key(row) for row in result["shared_directed_requests"]}, {
            ("3", "*", "3", "9"), ("5", "*", "5", "25"),
            ("3", "/", "5", "3/5"), ("9", "/", "25", "9/25"),
        })
        self.assertEqual(result["left"]["certificate"]["support"]["first_supported_stage"], 25)
        self.assertEqual(result["right"]["certificate"]["support"]["first_supported_stage"], 25)
        self.assertIsNone(result["declared_ac_expression_equal"])
        for edge in result["shared_retained_edge_refs"]:
            self.assertEqual(edge["source_sha256"], result["source"]["sha256"])
            self.assertTrue(edge["left_role_links"])
            self.assertTrue(edge["right_role_links"])

    def test_partial_aperture_keeps_request_overlap_separate_from_observed_occurrences(self) -> None:
        result = compare_certificates(
            self.early, "square:3/5#integer_ratio", "shell:3/5,4/5,1#normalize:3,4,5",
        )
        self.assertEqual(result["source"]["checkpoint"], 16)
        self.assertEqual(result["counts"]["shared_directed_requests"], 4)
        self.assertEqual(result["counts"]["shared_materialized_retained_edge_occurrences"], 3)
        self.assertEqual(result["left"]["certificate"]["support"]["status"], "partial")
        self.assertEqual(result["right"]["certificate"]["support"]["status"], "partial")
        quotient = next(row for row in result["shared_directed_requests"] if _key(row) == ("9", "/", "25", "9/25"))
        self.assertFalse(quotient["left_witnessed"])
        self.assertFalse(quotient["right_witnessed"])
        self.assertEqual(quotient["shared_retained_edge_refs"], [])
        self.assertTrue(all(edge["stage"] <= 16 for edge in result["shared_retained_edge_refs"]))

    def test_rescaled_certificates_keep_same_association_and_distinct_requests(self) -> None:
        result = compare_certificates(
            self.index, "shell:3/5,4/5,1#normalize:3,4,5", "shell:3/5,4/5,1#normalize:6,8,10",
        )
        left, right = result["left"]["certificate"], result["right"]["certificate"]
        self.assertEqual(left["association_id"], right["association_id"])
        self.assertNotEqual(left["parameters"]["raw_source"], right["parameters"]["raw_source"])
        self.assertEqual(left["support"]["first_supported_stage"], 25)
        self.assertEqual(right["support"]["first_supported_stage"], 100)
        self.assertEqual(result["counts"]["shared_directed_requests"], 0)
        self.assertEqual(result["counts"]["shared_materialized_retained_edge_occurrences"], 0)
        self.assertIn("No independence claim", result["interpretation"]["independence"])

    def test_directed_addition_is_not_silently_quotiented_by_commutativity(self) -> None:
        result = compare_certificates(
            self.index, "shell:3/5,4/5,1#normalize:3,4,5", "shell:4/5,3/5,1#normalize:4,3,5",
        )
        self.assertEqual(result["counts"]["shared_directed_requests"], 8)
        self.assertEqual({_key(row) for row in result["left_only_directed_requests"]}, {("9", "+", "16", "25")})
        self.assertEqual({_key(row) for row in result["right_only_directed_requests"]}, {("16", "+", "9", "25")})
        self.assertFalse(result["same_directed_request_set"])
        self.assertFalse(result["same_retained_edge_set"])

    def test_repeated_premise_and_construction_roles_do_not_duplicate_occurrences(self) -> None:
        reference = "square:25#route:shell_factored"
        result = compare_certificates(self.index, reference, reference)
        left = result["left"]
        self.assertGreater(left["counts"]["request_roles"], left["counts"]["unique_directed_requests"])
        agreement = next(row for row in left["directed_requests"] if _key(row) == ("16", "+", "9", "25"))
        self.assertEqual({role["request_role"] for role in agreement["role_links"]},
                         {"step:sum", "premise:source_agreement"})
        self.assertEqual(len(agreement["retained_edge_refs"]), 1)
        self.assertTrue(result["same_directed_request_set"])
        self.assertTrue(result["same_retained_edge_set"])

    def test_spiral_comparison_expands_signed_lineage_without_claiming_local_completion(self) -> None:
        result = compare_certificates(
            self.index, "spiral:4,3,5:3#scalar_lineage", "spiral:4,3,5:4#scalar_lineage",
        )
        left, right = result["left"], result["right"]
        self.assertEqual(left["certificate"]["support"]["status"], "witnessed")
        self.assertEqual(left["certificate"]["support"]["first_supported_stage"], 96)
        self.assertEqual(right["certificate"]["support"]["status"], "partial")
        self.assertIsNone(right["certificate"]["support"]["first_supported_stage"])
        closure = [certificate["ref"] for certificate in right["dependency_closure"]]
        self.assertEqual(len(closure), len(set(closure)))
        self.assertIn("shell:4,3,5#literal", closure)
        self.assertIn("spiral:4,3,5:1#scalar_lineage", closure)
        self.assertIn("spiral:4,3,5:2#scalar_lineage", closure)
        self.assertIn("spiral:4,3,5:3#scalar_lineage", closure)
        self.assertEqual(result["counts"]["shared_directed_requests"], left["counts"]["unique_directed_requests"])
        self.assertTrue(result["same_retained_edge_set"])
        self.assertFalse(result["same_directed_request_set"])
        signed = next(row for row in right["directed_requests"] if _key(row) == ("-44", "*", "4", "-176"))
        self.assertFalse(signed["witnessed"])
        self.assertEqual(signed["retained_edge_refs"], [])

    def test_declared_ac_metadata_does_not_merge_distinct_request_bundles(self) -> None:
        result = compare_certificates(
            self.index, "square:25#route:shell_expanded_paired", "square:25#route:shell_expanded_left",
        )
        self.assertTrue(result["declared_ac_expression_equal"])
        self.assertFalse(result["same_directed_request_set"])
        self.assertIn("shell_binomial_norm_identity", result["shared_declared_dependency_tags"])
        for side in ("left", "right"):
            self.assertEqual(result[side]["certificate"]["support"]["status"], "partial")
            premises = {role["request_role"]: _key(row)
                        for row in result[side]["directed_requests"] for role in row["role_links"]
                        if role["request_role"].startswith("premise:")}
            self.assertEqual(premises, {
                "premise:radius_square": ("5", "*", "5", "25"),
                "premise:source_agreement": ("16", "+", "9", "25"),
            })

    def test_truncated_occurrences_do_not_support_an_exhaustive_edge_set_claim(self) -> None:
        source = self.directory / "duplicate-occurrences.sqlite"
        index = self.directory / "duplicate-occurrences-profiles.sqlite"
        shutil.copy2(self.source, source)
        with closing(sqlite3.connect(source)) as conn:
            row = conn.execute(
                """SELECT stage,op,left_node_id,right_node_id,result_node_id FROM edges
                   WHERE op='*' AND left_node_id=(SELECT node_id FROM nodes WHERE p=3 AND q=1)
                   AND right_node_id=(SELECT node_id FROM nodes WHERE p=3 AND q=1)"""
            ).fetchone()
            # Synthetic repeated occurrence records; the original witness and its
            # confirmation status are untouched, and all copies have eligible inputs.
            conn.executemany("INSERT INTO edges(stage,op,left_node_id,right_node_id,result_node_id) VALUES(?,?,?,?,?)", [row] * 9)
            conn.commit()
        build_index(source, index, square_height=3, max_radius=0, spiral_steps=0)
        result = compare_certificates(index, "square:3#literal", "square:3#literal")
        self.assertEqual(result["counts"]["shared_materialized_retained_edge_occurrences"], 8)
        self.assertTrue(result["same_materialized_retained_edge_set"])
        self.assertIsNone(result["same_retained_edge_set"])
        coverage = result["occurrence_reference_coverage"]
        self.assertFalse(coverage["shared_occurrence_references_exhaustive"])
        request = result["left"]["directed_requests"][0]
        self.assertFalse(request["occurrence_references_exhaustive"])
        self.assertEqual(request["role_links"][0]["source_edge_count"], 10)
        self.assertTrue(request["role_links"][0]["source_edge_refs_truncated"])

    def test_dependency_cycles_are_rejected_instead_of_silently_short_circuiting(self) -> None:
        copied = self.directory / "cyclic-index.sqlite"
        shutil.copy2(self.index, copied)
        reference = "square:3#literal"
        with closing(sqlite3.connect(copied)) as conn:
            row = conn.execute("SELECT data FROM certificates WHERE ref=?", (reference,)).fetchone()
            certificate = json.loads(row[0])
            certificate["support"]["dependencies"] = [{"ref": reference, "status": "witnessed", "first_supported_stage": 3}]
            conn.execute("UPDATE certificates SET data=? WHERE ref=?", (json.dumps(certificate), reference))
            conn.commit()
        with self.assertRaisesRegex(ValueError, "dependency cycle"):
            compare_certificates(copied, reference, reference)

    def test_legacy_v1_dependency_references_are_expanded_without_migration(self) -> None:
        legacy = self.directory / "legacy-v1.sqlite"
        manifest = index_manifest(self.index)
        manifest["schema_version"] = "moo_node_profiles.v1"
        identifiers = ("shell:4,3,5", "spiral:4,3,5:1", "spiral:4,3,5:2")
        with closing(sqlite3.connect(legacy)) as conn:
            conn.executescript("""
                CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE associations(id TEXT PRIMARY KEY,family TEXT,label TEXT,
                  parameters TEXT,support TEXT,status TEXT,first_supported_stage INTEGER);
                CREATE TABLE participants(association_id TEXT,role TEXT,value TEXT);
            """)
            conn.execute("INSERT INTO metadata VALUES('manifest',?)", (json.dumps(manifest),))
            for identifier in identifiers:
                association = load_association(self.index, identifier)
                certificate_id = "scalar_lineage" if identifier.startswith("spiral:") else "literal"
                support = load_certificate(self.index, f"{identifier}#{certificate_id}")["support"]
                support["dependencies"] = [
                    {"id": dependency["ref"].split("#")[0], "status": dependency["status"],
                     "first_supported_stage": dependency["first_supported_stage"]}
                    for dependency in support["dependencies"]
                ]
                conn.execute("INSERT INTO associations VALUES(?,?,?,?,?,?,?)", (
                    identifier, association["family"], association["label"], json.dumps(association["parameters"]),
                    json.dumps(support), support["status"], support["first_supported_stage"],
                ))
                conn.executemany("INSERT INTO participants VALUES(?,?,?)", [
                    (identifier, participant["role"], participant["value"])
                    for participant in association["participants"]
                ])
            conn.commit()
        result = compare_certificates(legacy, "shell:4,3,5#literal", "spiral:4,3,5:2#scalar_lineage")
        self.assertTrue(result["left"]["certificate"]["legacy_snapshot"])
        self.assertTrue(result["right"]["certificate"]["legacy_snapshot"])
        self.assertEqual(result["counts"]["shared_directed_requests"], 4)
        self.assertEqual(len(result["right"]["dependency_closure"]), 3)
        with closing(sqlite3.connect(legacy)) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='certificates'").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
