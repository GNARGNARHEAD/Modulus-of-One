from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from fractions import Fraction
from pathlib import Path
from typing import Dict, Sequence, Set, Tuple
from unittest.mock import patch

from moo.phase_transport_probe import (
    DEFAULT_SEED,
    FROZEN_PRIMARY_CORPUS_CONFIG,
    MAX_PATH_LENGTH,
    _null_summary,
    main,
    phase_transport_probe,
)


BASE_STAGE = 1_000_000_000
FUTURE_STAGE = 2_000_000_000
DEFAULT_PATH_LENGTH = 8
CHECKPOINT_STAGE = BASE_STAGE + DEFAULT_PATH_LENGTH - 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class CorpusBuilder:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL
            );
            CREATE TABLE nodes (
              node_id INTEGER PRIMARY KEY AUTOINCREMENT,
              p INTEGER NOT NULL,
              q INTEGER NOT NULL,
              label TEXT NOT NULL,
              kind TEXT NOT NULL,
              first_stage INTEGER NOT NULL,
              confirmed_stage INTEGER,
              first_edge_id INTEGER,
              UNIQUE(p, q)
            );
            CREATE TABLE edges (
              edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
              stage INTEGER NOT NULL,
              op TEXT NOT NULL,
              left_node_id INTEGER,
              right_node_id INTEGER,
              result_node_id INTEGER NOT NULL,
              FOREIGN KEY(left_node_id) REFERENCES nodes(node_id),
              FOREIGN KEY(right_node_id) REFERENCES nodes(node_id),
              FOREIGN KEY(result_node_id) REFERENCES nodes(node_id)
            );
            CREATE TABLE stages (
              stage INTEGER PRIMARY KEY,
              candidate_events INTEGER NOT NULL,
              retained_events INTEGER NOT NULL,
              new_nodes INTEGER NOT NULL,
              new_edges INTEGER NOT NULL,
              total_nodes INTEGER NOT NULL,
              total_edges INTEGER NOT NULL,
              elapsed_seconds REAL NOT NULL
            );
            """
        )
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES ('schema_version', 'test-v1')"
        )
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES ('config_json', ?)",
            (json.dumps({"fixture": "phase-transport"}),),
        )
        self.node_ids: Dict[Tuple[int, int], int] = {}
        self.used_input_values: Set[int] = set()
        self.component_serial = 0

    def close(self) -> None:
        self._record_stage(BASE_STAGE)
        self.conn.commit()
        self.conn.close()

    def _record_stage(self, stage: int) -> None:
        nodes = int(self.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0])
        edges = int(self.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0])
        self.conn.execute(
            """
            INSERT OR REPLACE INTO stages(
              stage, candidate_events, retained_events, new_nodes, new_edges,
              total_nodes, total_edges, elapsed_seconds
            ) VALUES (?, 0, 0, 0, 0, ?, ?, 0.0)
            """,
            (stage, nodes, edges),
        )

    def node(
        self,
        p: int,
        q: int,
        *,
        first_stage: int,
        confirmed_stage: int | None,
        kind: str,
    ) -> int:
        value = Fraction(p, q)
        key = (int(value.numerator), int(value.denominator))
        if key in self.node_ids:
            return self.node_ids[key]
        cursor = self.conn.execute(
            """
            INSERT INTO nodes(p, q, label, kind, first_stage, confirmed_stage)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                key[0],
                key[1],
                f"{key[0]}/{key[1]}",
                kind,
                first_stage,
                confirmed_stage,
            ),
        )
        node_id = int(cursor.lastrowid)
        self.node_ids[key] = node_id
        return node_id

    def integer(self, value: int) -> int:
        return self.node(
            value,
            1,
            first_stage=value,
            confirmed_stage=value,
            kind="ref",
        )

    def add_transport_components(
        self,
        *,
        qs: Sequence[int],
        components_per_q: int,
        path_length: int,
        pattern: str,
        stage: int = BASE_STAGE,
    ) -> None:
        for q in qs:
            for local_component in range(components_per_q):
                serial = self.component_serial
                self.component_serial += 1
                if pattern == "alternating":
                    offset = local_component % 2
                    residues = [
                        1 if (index + offset) % 2 == 0 else q - 1
                        for index in range(path_length)
                    ]
                elif pattern == "blocked":
                    residues = [1] * (path_length // 2) + [q - 1] * (
                        path_length - path_length // 2
                    )
                    if local_component % 2:
                        residues = [q - residue for residue in residues]
                elif pattern == "constant":
                    residues = [1] * path_length
                else:
                    raise ValueError(pattern)
                reduced_numerators = [
                    (serial * 100 + 10 + index) * q + residue
                    for index, residue in enumerate(residues)
                ]
                scale = 1009 + serial * 101
                while True:
                    denominator = scale * q
                    numerators = [scale * value for value in reduced_numerators]
                    candidate_inputs = {denominator, *numerators}
                    if (
                        len(candidate_inputs) == path_length + 1
                        and not candidate_inputs.intersection(self.used_input_values)
                        and max(candidate_inputs) <= stage
                    ):
                        break
                    scale += 1
                self.used_input_values.update(candidate_inputs)
                right_id = self.integer(denominator)
                for index, (numerator, reduced_numerator) in enumerate(
                    zip(numerators, reduced_numerators)
                ):
                    edge_stage = stage + index
                    left_id = self.integer(numerator)
                    result_id = self.node(
                        reduced_numerator,
                        q,
                        first_stage=edge_stage,
                        confirmed_stage=None,
                        kind="spec",
                    )
                    cursor = self.conn.execute(
                        """
                        INSERT INTO edges(stage, op, left_node_id, right_node_id, result_node_id)
                        VALUES (?, '/', ?, ?, ?)
                        """,
                        (edge_stage, left_id, right_id, result_id),
                    )
                    self.conn.execute(
                        """
                        UPDATE nodes SET first_edge_id = COALESCE(first_edge_id, ?)
                        WHERE node_id = ?
                        """,
                        (int(cursor.lastrowid), result_id),
                    )
        self._record_stage(stage + path_length - 1)

    def add_future_duplicate_edges(self, count: int) -> None:
        rows = list(
            self.conn.execute(
                """
                SELECT left_node_id, right_node_id, result_node_id
                FROM edges
                WHERE stage >= ? AND stage <= ?
                ORDER BY edge_id
                LIMIT ?
                """,
                (BASE_STAGE, CHECKPOINT_STAGE, count),
            )
        )
        for row in rows:
            self.conn.execute(
                """
                INSERT INTO edges(stage, op, left_node_id, right_node_id, result_node_id)
                VALUES (?, '/', ?, ?, ?)
                """,
                (
                    FUTURE_STAGE,
                    int(row["left_node_id"]),
                    int(row["right_node_id"]),
                    int(row["result_node_id"]),
                ),
            )
        self._record_stage(FUTURE_STAGE)


def _build_corpus(
    path: Path,
    *,
    pattern: str,
    components_per_q: int,
    qs: Sequence[int] = (3, 4, 5, 7),
    path_length: int = 8,
) -> None:
    builder = CorpusBuilder(path)
    try:
        builder.add_transport_components(
            qs=qs,
            components_per_q=components_per_q,
            path_length=path_length,
            pattern=pattern,
        )
    finally:
        builder.close()


def _reverse_edge_insertion_order(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        rows = list(
            conn.execute(
                """
                SELECT stage, op, left_node_id, right_node_id, result_node_id
                FROM edges
                ORDER BY edge_id
                """
            )
        )
        conn.execute("DELETE FROM edges")
        for row in reversed(rows):
            conn.execute(
                """
                INSERT INTO edges(stage, op, left_node_id, right_node_id, result_node_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                tuple(row),
            )


def _run(path: Path, **overrides: object) -> Dict[str, object]:
    kwargs: Dict[str, object] = {
        "db_path": path,
        "max_denominator": 7,
        "path_length": 8,
        "max_occurrences_per_q": 512,
        "max_out_degree": 32,
        "max_paths_per_q": 64,
        "null_samples": 128,
        "stage_bin_width": 1,
        "seed": DEFAULT_SEED,
        "checkpoint_stage": CHECKPOINT_STAGE,
    }
    kwargs.update(overrides)
    return phase_transport_probe(**kwargs)  # type: ignore[arg-type]


class PhaseTransportProbeTests(unittest.TestCase):
    def test_null_comparisons_remain_exact_past_binary64_resolution(self) -> None:
        observed = Fraction(2**53 + 1, 2**54)
        summary = _null_summary(observed, [Fraction(1, 2)])
        self.assertTrue(summary["observed_exceeds_mean"])
        self.assertTrue(summary["observed_above_percentile_99"])
        self.assertEqual(summary["mean"]["frac"], "1/2")
        self.assertEqual(
            summary["comparison_arithmetic"],
            "exact Fraction; decimals are serialization aids only",
        )

    def test_positive_controlled_ordering_signal_retains(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "positive.sqlite"
            _build_corpus(db, pattern="alternating", components_per_q=24)
            report = _run(db)

        self.assertEqual(
            report["decision"]["status"],
            "diagnostic_pattern_meets_retention_rule",
        )
        self.assertEqual(
            report["decision"]["primary_rule_outcome"],
            "retain_provenance_conditioned_candidate",
        )
        self.assertFalse(report["decision"]["frozen_experiment_eligible"])
        self.assertTrue(report["aperture"]["sufficient"])
        self.assertGreaterEqual(report["aperture"]["holdout_path_count"], 32)
        self.assertEqual(len(report["aperture"]["holdout_q_values"]), 4)
        self.assertTrue(
            report["controls"]["stratified_label_shuffle"][
                "exact_stage_stratification"
            ]
        )
        self.assertTrue(
            all(report["decision"]["retention_checks"].values())
        )
        for path in report["paths"]:
            residues = path["external_counterfactual_transport"]["residues"]
            self.assertTrue(
                all(
                    residues[index] != residues[index + 1]
                    for index in range(len(residues) - 1)
                )
            )
            self.assertEqual(len(path["transition_witnesses"]), 7)
            self.assertTrue(
                all(
                    witness["shared_confirmed_input_node_ids"]
                    for witness in path["transition_witnesses"]
                )
            )
            self.assertFalse(
                path["external_counterfactual_transport"]["runtime_operational"]
            )
            stages = [
                occurrence["stage"]
                for occurrence in path["source_occurrence_evidence"]
            ]
            self.assertTrue(
                all(left < right for left, right in zip(stages, stages[1:]))
            )
            for occurrence in path["source_occurrence_evidence"]:
                branch = occurrence["division_branch_prediction"]
                self.assertGreater(
                    branch["full_preimage_count"],
                    branch["recorded_q"],
                )
                self.assertNotEqual(
                    branch["selected_full_preimage_branch_index"],
                    branch["recorded_residue"],
                )
                self.assertTrue(branch["full_preimage_relation_validated"])
                self.assertIn(
                    "not the full preimage count/branch index",
                    branch["coordinate_boundary"],
                )

    def test_sufficient_null_ordering_kills_current_hypothesis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "null.sqlite"
            _build_corpus(db, pattern="blocked", components_per_q=24)
            report = _run(db)

        self.assertTrue(report["aperture"]["sufficient"])
        self.assertEqual(
            report["decision"]["status"],
            "diagnostic_pattern_fails_retention_rule",
        )
        self.assertEqual(
            report["decision"]["primary_rule_outcome"],
            "kill_current_hypothesis",
        )
        self.assertFalse(all(report["decision"]["retention_checks"].values()))

    def test_insufficient_aperture_preempts_null_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "small.sqlite"
            _build_corpus(db, pattern="alternating", components_per_q=2, qs=(3, 5))
            report = _run(db, max_denominator=5, null_samples=16)

        self.assertEqual(
            report["decision"]["status"], "diagnostic_insufficient_aperture"
        )
        self.assertFalse(report["aperture"]["sufficient"])
        self.assertFalse(
            report["aperture"]["checks"]["holdout_paths_at_least_32"]
        )
        self.assertFalse(
            report["aperture"]["checks"]["holdout_denominators_at_least_4"]
        )

    def test_immutable_labels_fail_mutable_aperture_guard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "immutable.sqlite"
            _build_corpus(db, pattern="constant", components_per_q=24)
            report = _run(db, null_samples=16)

        self.assertEqual(
            report["decision"]["status"], "diagnostic_insufficient_aperture"
        )
        self.assertEqual(report["aperture"]["mutable_holdout_position_count"], 0)
        self.assertFalse(
            report["aperture"]["checks"]["mutable_positions_at_least_16"]
        )

    def test_checkpoint_excludes_future_edge_occurrences_and_exposure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "checkpoint.sqlite"
            builder = CorpusBuilder(db)
            builder.add_transport_components(
                qs=(3, 4, 5, 7),
                components_per_q=4,
                path_length=8,
                pattern="alternating",
            )
            builder.conn.commit()
            before = _run(db, null_samples=8)
            builder.add_future_duplicate_edges(16)
            builder.conn.commit()
            after = _run(db, null_samples=8)
            builder.close()

        self.assertEqual(
            before["graph_selection"]["selection_checksum_sha256"],
            after["graph_selection"]["selection_checksum_sha256"],
        )
        self.assertEqual(
            before["summary"]["eligible_division_occurrences_before_caps"],
            after["summary"]["eligible_division_occurrences_before_caps"],
        )
        before_exposure = [
            occurrence["incoming_witness_exposure_at_checkpoint"]
            for path in before["paths"]
            for occurrence in path["source_occurrence_evidence"]
        ]
        after_exposure = [
            occurrence["incoming_witness_exposure_at_checkpoint"]
            for path in after["paths"]
            for occurrence in path["source_occurrence_evidence"]
        ]
        self.assertEqual(before_exposure, after_exposure)

    def test_same_stage_sqlite_reinsertion_order_does_not_change_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "reinsertion.sqlite"
            _build_corpus(db, pattern="alternating", components_per_q=12)
            before = _run(db, null_samples=32)
            _reverse_edge_insertion_order(db)
            after = _run(db, null_samples=32)

        self.assertEqual(
            before["graph_selection"]["selection_checksum_sha256"],
            after["graph_selection"]["selection_checksum_sha256"],
        )
        self.assertEqual(
            before["observed_holdout_statistic"]["aggregate"],
            after["observed_holdout_statistic"]["aggregate"],
        )
        self.assertEqual(
            before["controls"]["exact_step_permutation"]["aggregate_histogram"],
            after["controls"]["exact_step_permutation"]["aggregate_histogram"],
        )
        self.assertEqual(
            before["controls"]["stratified_label_shuffle"][
                "aggregate_histogram"
            ],
            after["controls"]["stratified_label_shuffle"][
                "aggregate_histogram"
            ],
        )
        self.assertEqual(
            before["decision"]["retention_checks"],
            after["decision"]["retention_checks"],
        )
        self.assertEqual(
            before["decision"]["primary_rule_outcome"],
            after["decision"]["primary_rule_outcome"],
        )

    def test_rejects_arithmetic_mismatch_and_speculative_operand(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            arithmetic_db = Path(directory) / "arithmetic.sqlite"
            builder = CorpusBuilder(arithmetic_db)
            left = builder.integer(5)
            right = builder.integer(3)
            wrong_result = builder.node(
                4,
                3,
                first_stage=BASE_STAGE,
                confirmed_stage=None,
                kind="spec",
            )
            builder.conn.execute(
                "INSERT INTO edges(stage, op, left_node_id, right_node_id, result_node_id) VALUES (?, '/', ?, ?, ?)",
                (BASE_STAGE, left, right, wrong_result),
            )
            builder.close()
            with self.assertRaisesRegex(ValueError, "division edge audit failed"):
                _run(
                    arithmetic_db,
                    null_samples=1,
                    checkpoint_stage=BASE_STAGE,
                )

            misaligned_db = Path(directory) / "misaligned.sqlite"
            builder = CorpusBuilder(misaligned_db)
            rational = builder.node(
                1,
                3,
                first_stage=BASE_STAGE,
                confirmed_stage=None,
                kind="spec",
            )
            right = builder.integer(2)
            result = builder.node(
                1,
                6,
                first_stage=BASE_STAGE,
                confirmed_stage=None,
                kind="spec",
            )
            builder.conn.execute(
                "INSERT INTO edges(stage, op, left_node_id, right_node_id, result_node_id) VALUES (?, '/', ?, ?, ?)",
                (BASE_STAGE, rational, right, result),
            )
            builder.close()
            with self.assertRaisesRegex(ValueError, "strict operand alignment"):
                _run(
                    misaligned_db,
                    null_samples=1,
                    checkpoint_stage=BASE_STAGE,
                )

            future_node_db = Path(directory) / "future-node.sqlite"
            builder = CorpusBuilder(future_node_db)
            left = builder.integer(5)
            right = builder.integer(3)
            future_result = builder.node(
                5,
                3,
                first_stage=FUTURE_STAGE,
                confirmed_stage=None,
                kind="spec",
            )
            builder.conn.execute(
                "INSERT INTO edges(stage, op, left_node_id, right_node_id, result_node_id) VALUES (?, '/', ?, ?, ?)",
                (BASE_STAGE, left, right, future_result),
            )
            builder.close()
            with self.assertRaisesRegex(ValueError, "result_arrival=1"):
                _run(
                    future_node_db,
                    null_samples=1,
                    checkpoint_stage=BASE_STAGE,
                )

    def test_declared_strict_generator_rejects_delayed_frontier_edge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "delayed-frontier.sqlite"
            builder = CorpusBuilder(db)
            left = builder.integer(5)
            right = builder.integer(3)
            result = builder.node(
                5,
                3,
                first_stage=BASE_STAGE,
                confirmed_stage=None,
                kind="spec",
            )
            builder.conn.execute(
                "UPDATE meta SET value = ? WHERE key = 'config_json'",
                (json.dumps(FROZEN_PRIMARY_CORPUS_CONFIG),),
            )
            builder.conn.execute(
                """
                INSERT INTO edges(stage, op, left_node_id, right_node_id, result_node_id)
                VALUES (?, '/', ?, ?, ?)
                """,
                (BASE_STAGE, left, right, result),
            )
            builder.close()

            with self.assertRaisesRegex(ValueError, "frontier_stage=1"):
                _run(
                    db,
                    null_samples=1,
                    checkpoint_stage=BASE_STAGE,
                )

    def test_frozen_filename_config_and_schema_cannot_spoof_primary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = (
                Path(directory)
                / "out"
                / "experiments"
                / "circle_as_one_u40_wide.sqlite"
            )
            db.parent.mkdir(parents=True)
            builder = CorpusBuilder(db)
            one = builder.integer(1)
            builder.conn.execute(
                "UPDATE meta SET value = '1' WHERE key = 'schema_version'"
            )
            builder.conn.execute(
                "UPDATE meta SET value = ? WHERE key = 'config_json'",
                (json.dumps(FROZEN_PRIMARY_CORPUS_CONFIG),),
            )
            builder.conn.execute(
                """
                INSERT INTO edges(stage, op, left_node_id, right_node_id, result_node_id)
                VALUES (1, 'seed', NULL, NULL, ?)
                """,
                (one,),
            )
            builder._record_stage(40)
            builder.conn.commit()
            builder.conn.close()

            report = phase_transport_probe(db_path=db, checkpoint_stage=40)

        checks = report["frozen_experiment_identity"]["checks"]
        self.assertTrue(checks["database_path_matches"])
        self.assertTrue(checks["corpus_schema_matches"])
        self.assertTrue(checks["corpus_config_matches"])
        self.assertTrue(checks["checkpoint_matches"])
        self.assertFalse(checks["database_sha256_matches"])
        self.assertFalse(report["frozen_experiment_identity"]["eligible"])
        self.assertEqual(
            report["decision"]["status"],
            "diagnostic_insufficient_aperture",
        )

    def test_caps_are_reported_and_source_database_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "caps.sqlite"
            _build_corpus(db, pattern="alternating", components_per_q=3, qs=(3,))
            before = _sha256(db)
            occurrence_capped = _run(
                db,
                max_denominator=3,
                max_occurrences_per_q=8,
                null_samples=4,
            )
            degree_capped = _run(
                db,
                max_denominator=3,
                max_occurrences_per_q=24,
                max_out_degree=2,
                null_samples=4,
            )
            path_capped = _run(
                db,
                max_denominator=3,
                max_occurrences_per_q=24,
                max_out_degree=32,
                max_paths_per_q=1,
                null_samples=4,
            )
            with patch("moo.phase_transport_probe.MAX_TOTAL_DFS_STATES", 1):
                with self.assertRaisesRegex(ValueError, "aggregate DFS state"):
                    _run(
                        db,
                        max_denominator=3,
                        max_occurrences_per_q=24,
                        null_samples=1,
                    )
            after = _sha256(db)

        self.assertEqual(before, after)
        self.assertFalse(occurrence_capped["graph_corpus"]["mutated"])
        self.assertIn("mode=ro", occurrence_capped["graph_corpus"]["connection"])
        self.assertGreater(
            occurrence_capped["graph_selection"]["occurrence_cap"][
                "total_excluded"
            ],
            0,
        )
        self.assertGreater(
            degree_capped["graph_selection"]["provenance_dag"][
                "arcs_excluded_by_degree_cap"
            ],
            0,
        )
        self.assertTrue(
            path_capped["graph_selection"]["paths"]["by_q"][0][
                "path_cap_reached"
            ]
        )
        self.assertGreater(
            path_capped["graph_selection"]["paths"][
                "seed_entries_unconsidered_due_to_path_cap"
            ],
            0,
        )
        self.assertLessEqual(path_capped["summary"]["accepted_paths"], 1)
        with self.assertRaisesRegex(ValueError, "path_length"):
            phase_transport_probe(
                db_path=db,
                path_length=MAX_PATH_LENGTH + 1,
                null_samples=1,
            )

    def test_exposure_materialization_cap_is_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "exposure-cap.sqlite"
            _build_corpus(db, pattern="alternating", components_per_q=2, qs=(3,))
            with patch(
                "moo.phase_transport_probe.MAX_MATERIALIZED_EXPOSURE_RESULTS",
                1,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "exposure materialization",
                ):
                    _run(db, max_denominator=3, null_samples=1)

    def test_direct_api_rejects_non_integer_numeric_parameters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "types.sqlite"
            _build_corpus(db, pattern="alternating", components_per_q=1, qs=(3,))
            with self.assertRaisesRegex(TypeError, "max_denominator"):
                phase_transport_probe(
                    db_path=db,
                    max_denominator=7.0,  # type: ignore[arg-type]
                )
            with self.assertRaisesRegex(TypeError, "path_length"):
                phase_transport_probe(
                    db_path=db,
                    path_length=True,  # type: ignore[arg-type]
                )
            with self.assertRaisesRegex(TypeError, "experiment_id"):
                phase_transport_probe(
                    db_path=db,
                    experiment_id="",
                )

    def test_cli_writes_metadata_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "cli.sqlite"
            output = Path(directory) / "report.json"
            _build_corpus(db, pattern="alternating", components_per_q=1, qs=(3,))
            argv = [
                "--db",
                str(db),
                "--max-q",
                "3",
                "--null-samples",
                "2",
                "--checkpoint-stage",
                str(BASE_STAGE),
                "--write",
                str(output),
            ]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv), 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_metadata"]["schema_version"], "moo_phase_transport_probe.v1")
            self.assertIsNotNone(payload["report_metadata"]["db_sha256"])
            with redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(SystemExit, "Refusing to overwrite"):
                    main(argv)


if __name__ == "__main__":
    unittest.main()
