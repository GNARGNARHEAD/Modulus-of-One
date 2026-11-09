from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from fractions import Fraction
from pathlib import Path
from typing import Union
from unittest import mock

from moo import phase_metric_probe as phase_probe_module
from moo.graph_corpus import GraphCorpus, GraphCorpusConfig, normalize_key
from moo.phase import (
    circular_distance,
    circular_length,
    sampled_path_payload,
    triangle_slack,
)
from moo.phase_metric_probe import (
    _external_return_walk,
    _metric_calibration,
    phase_metric_probe,
)


Value = Union[int, Fraction]


def _create_fixture(path: Path, *, malformed_addition: bool = False) -> None:
    config = GraphCorpusConfig(
        generator="strict_stage_moo_graph",
        max_stage=6,
        max_abs_p=100,
        max_abs_q=100,
        max_abs_value=20.0,
        retain_confirmed_edges=True,
    )
    with GraphCorpus(path) as corpus:
        corpus.init_schema()
        corpus.ensure_config(config)

        def node(value: Value, *, first_stage: int) -> int:
            fraction = value if isinstance(value, Fraction) else Fraction(value, 1)
            key = normalize_key(fraction.numerator, fraction.denominator)
            found, _ = corpus.ensure_node(key, first_stage=first_stage)
            return found

        def core(value: int) -> int:
            found, _ = corpus.ensure_core_integer(value)
            return found

        cores = {value: core(value) for value in range(1, 7)}
        corpus.insert_edge(
            stage=1,
            op="seed",
            left_node_id=None,
            right_node_id=None,
            result_node_id=cores[1],
        )

        two = node(2, first_stage=1)
        zero = node(0, first_stage=1)
        negative_one = node(-1, first_stage=2)
        corpus.insert_edge(
            stage=1,
            op="+",
            left_node_id=cores[1],
            right_node_id=cores[1],
            result_node_id=two,
        )
        corpus.insert_edge(
            stage=1,
            op="-",
            left_node_id=cores[1],
            right_node_id=cores[1],
            result_node_id=zero,
        )
        corpus.insert_edge(
            stage=2,
            op="+",
            left_node_id=cores[2],
            right_node_id=cores[1],
            result_node_id=cores[3],
        )
        corpus.insert_edge(
            stage=2,
            op="+",
            left_node_id=cores[1],
            right_node_id=cores[2],
            result_node_id=cores[3],
        )
        corpus.insert_edge(
            stage=2,
            op="+",
            left_node_id=cores[2],
            right_node_id=cores[2],
            result_node_id=node(4, first_stage=2),
        )
        corpus.insert_edge(
            stage=2,
            op="-",
            left_node_id=cores[2],
            right_node_id=cores[1],
            result_node_id=cores[1],
        )
        corpus.insert_edge(
            stage=2,
            op="-",
            left_node_id=cores[1],
            right_node_id=cores[2],
            result_node_id=negative_one,
        )
        if malformed_addition:
            corpus.insert_edge(
                stage=1,
                op="+",
                left_node_id=cores[1],
                right_node_id=cores[1],
                result_node_id=zero,
            )

        for numerator, denominator in [
            (1, 2),
            (3, 2),
            (5, 2),
            (1, 3),
            (4, 3),
            (2, 3),
            (5, 3),
            (1, 4),
            (5, 4),
        ]:
            stage = max(numerator, denominator)
            result = Fraction(numerator, denominator)
            result_id = node(result, first_stage=stage)
            corpus.insert_edge(
                stage=stage,
                op="/",
                left_node_id=cores[numerator],
                right_node_id=cores[denominator],
                result_node_id=result_id,
            )

        corpus.insert_edge(
            stage=4,
            op="/",
            left_node_id=cores[2],
            right_node_id=cores[4],
            result_node_id=node(Fraction(1, 2), first_stage=2),
        )

        corpus.record_stage(
            stage=6,
            candidate_events=0,
            retained_events=0,
            new_nodes=0,
            new_edges=0,
            elapsed_seconds=0.0,
        )


class PhaseMetricMathTests(unittest.TestCase):
    def test_exact_circular_lengths_and_distances(self) -> None:
        self.assertEqual(circular_length(Fraction(3, 4)), Fraction(1, 4))
        self.assertEqual(circular_length(Fraction(-1, 4)), Fraction(1, 4))
        self.assertEqual(circular_length(Fraction(1, 2)), Fraction(1, 2))
        self.assertEqual(
            circular_distance(Fraction(1, 10), Fraction(9, 10)),
            Fraction(1, 5),
        )
        self.assertEqual(
            circular_distance(Fraction(1, 3), Fraction(4, 3)),
            Fraction(0),
        )
        self.assertEqual(
            circular_distance(Fraction(1, 3), Fraction(2, 3)),
            Fraction(1, 3),
        )

    def test_triangle_slack_detects_tight_and_wrapped_routes(self) -> None:
        self.assertEqual(
            triangle_slack(0, Fraction(1, 8), Fraction(1, 4)),
            0,
        )
        self.assertEqual(
            triangle_slack(0, Fraction(1, 3), Fraction(2, 3)),
            Fraction(1, 3),
        )
        self.assertEqual(
            triangle_slack(0, Fraction(1, 2), 1),
            1,
        )

    def test_small_exact_grid_satisfies_pseudometric_axioms(self) -> None:
        values = sorted(
            {
                Fraction(numerator, denominator)
                for denominator in range(1, 6)
                for numerator in range(-denominator, 2 * denominator + 1)
            }
        )
        for left in values:
            self.assertEqual(circular_distance(left, left), 0)
            for right in values:
                self.assertEqual(
                    circular_distance(left, right),
                    circular_distance(right, left),
                )
                self.assertLessEqual(circular_distance(left, right), abs(left - right))
                for via in values:
                    self.assertLessEqual(
                        circular_distance(left, right),
                        circular_distance(left, via) + circular_distance(via, right),
                    )

    def test_sampled_paths_expose_return_and_endpoint_aliasing(self) -> None:
        full_turn = sampled_path_payload(
            [Fraction(index, 4) for index in range(5)]
        )
        self.assertEqual(full_turn["sampled_phase_path_length"]["frac"], "1")
        self.assertEqual(full_turn["phase_endpoint_distance"]["frac"], "0")
        self.assertEqual(full_turn["phase_detour"]["frac"], "1")
        self.assertEqual(full_turn["sampled_net_integer_lift"], 1)

        endpoints_only = sampled_path_payload([0, 1])
        self.assertEqual(endpoints_only["sampled_phase_path_length"]["frac"], "0")
        self.assertEqual(endpoints_only["sampled_step_contraction"]["frac"], "1")

        positive_lift = sampled_path_payload(
            [index * Fraction(2, 3) for index in range(4)]
        )
        negative_lift = sampled_path_payload(
            [index * Fraction(-1, 3) for index in range(4)]
        )
        self.assertEqual(
            positive_lift["projected_phase_points"],
            negative_lift["projected_phase_points"],
        )
        self.assertEqual(positive_lift["sampled_net_integer_lift"], 2)
        self.assertEqual(negative_lift["sampled_net_integer_lift"], -1)
        self.assertEqual(
            positive_lift["sampled_phase_path_length"]["frac"],
            "1",
        )

    def test_phase_api_rejects_inexact_inputs_and_handles_small_paths(self) -> None:
        with self.assertRaises(TypeError):
            circular_length(0.75)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            circular_distance("1/3", 0)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            sampled_path_payload([])

        singleton = sampled_path_payload([Fraction(1, 2)])
        self.assertEqual(singleton["sampled_phase_path_length"]["frac"], "0")
        self.assertEqual(singleton["phase_endpoint_distance"]["frac"], "0")
        repeated = sampled_path_payload([Fraction(1, 2), Fraction(1, 2)])
        self.assertEqual(repeated["sampled_phase_path_length"]["frac"], "0")

    def test_external_return_walk_marks_convention_and_antipode(self) -> None:
        antipode = _external_return_walk(Fraction(1, 2))
        self.assertTrue(antipode["shortest_arc_orientation_ambiguous"])
        self.assertEqual(antipode["canonical_representative_net_lift"], 1)
        self.assertIn("convention-dependent", antipode["canonical_representative_convention"])

        large_order = _external_return_walk(Fraction(1, 29))
        self.assertTrue(
            large_order["sampled_canonical_lift_orbit"]["points_omitted"]
        )
        self.assertEqual(large_order["canonical_representative_net_lift"], 1)

    def test_empty_metric_calibration_is_not_a_substantive_pass(self) -> None:
        calibration = _metric_calibration([])
        self.assertEqual(calibration["status"], "insufficient_scope")
        self.assertEqual(calibration["route_check_count"], 0)


class PhaseMetricCorpusTests(unittest.TestCase):
    def test_neighborhood_materialization_cap_is_enforced_during_insertion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "fixture.sqlite"
            _create_fixture(db_path)
            with closing(sqlite3.connect(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                target_id = int(
                    conn.execute(
                        "SELECT node_id FROM nodes WHERE p = 2 AND q = 1"
                    ).fetchone()["node_id"]
                )
                direct_input_cache = {}
                neighborhood_cache = {}
                with mock.patch.object(
                    phase_probe_module,
                    "MAX_MATERIALIZED_NEIGHBORHOOD_ENTRIES",
                    0,
                ):
                    with self.assertRaisesRegex(ValueError, "hard cap"):
                        phase_probe_module._bulk_populate_graph_caches(
                            conn,
                            node_ids=[target_id],
                            checkpoint_stage=6,
                            direct_input_cache=direct_input_cache,
                            neighborhood_cache=neighborhood_cache,
                        )
                self.assertEqual(neighborhood_cache[target_id], set())

    def test_direct_api_limits_are_hard_and_positive(self) -> None:
        with self.assertRaises(ValueError):
            phase_metric_probe(db_path=Path("unused.sqlite"), slack_sample_limit=0)
        with self.assertRaises(ValueError):
            phase_metric_probe(
                db_path=Path("unused.sqlite"),
                max_phase_classes=129,
                full_scan=True,
            )

    def test_probe_returns_zero_distance_pairs_to_graph_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = phase_metric_probe(
                db_path=db_path,
                max_denominator=4,
                max_phase_classes=8,
                pairs_per_phase=4,
                neighborhood_sample_limit=4,
                edge_ref_limit=4,
                slack_sample_limit=4,
            )

        json.dumps(report)
        self.assertEqual(report["graph_corpus"]["alignment"]["status"], "pass")
        self.assertEqual(report["metric_calibration"]["status"], "pass")
        self.assertGreater(report["summary"]["exact_scored_zero_distance_pairs"], 0)

        fibres = {row["phase"]["frac"]: row for row in report["phase_fibres"]}
        half = fibres["1/2"]
        self.assertEqual(half["observed_lift_count"], 3)
        self.assertTrue(half["zero_distance_graph_pairs"])
        for pair in half["zero_distance_graph_pairs"]:
            self.assertTrue(pair["phase_metric"]["zero_distance"])

        third = fibres["1/3"]
        pair = third["zero_distance_graph_pairs"][0]
        self.assertTrue(pair["matched_different_phase_control"]["present"])
        control = pair["matched_different_phase_control"]["pair"]
        self.assertFalse(control["phase_metric"]["zero_distance"])

    def test_additive_audit_shows_source_slack_erased_by_phase_projection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = phase_metric_probe(
                db_path=db_path,
                max_denominator=4,
                max_phase_classes=4,
                pairs_per_phase=2,
                neighborhood_sample_limit=2,
                edge_ref_limit=2,
                slack_sample_limit=4,
            )

        audit = report["additive_triangle_audit"]
        self.assertEqual(
            audit["nonidentity_additive_edge_aperture"][
                "nontrivial_phase_additive_step_status"
            ],
            "blocked_by_strict_positive_spine_operand_rule",
        )
        self.assertEqual(audit["validation"]["status"], "pass")
        plus = audit["by_operation"]["+"]
        minus = audit["by_operation"]["-"]
        self.assertEqual(plus["operation_relation_failure_count"], 0)
        self.assertEqual(minus["operation_relation_failure_count"], 0)
        self.assertEqual(plus["phase_strict_edge_count"], 0)
        self.assertEqual(minus["phase_strict_edge_count"], 0)
        self.assertGreater(minus["source_strict_edge_count"], 0)
        self.assertGreater(minus["source_strict_phase_tight_erasure_count"], 0)
        self.assertTrue(minus["largest_source_slack_erasure_samples"])

    def test_checkpoint_filters_future_nodes_and_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            latest = phase_metric_probe(
                db_path=db_path,
                max_denominator=4,
                max_phase_classes=4,
                pairs_per_phase=2,
                neighborhood_sample_limit=2,
                edge_ref_limit=2,
                slack_sample_limit=2,
            )
            checkpoint = phase_metric_probe(
                db_path=db_path,
                max_denominator=4,
                max_phase_classes=4,
                pairs_per_phase=2,
                neighborhood_sample_limit=2,
                edge_ref_limit=2,
                slack_sample_limit=2,
                checkpoint_stage=3,
            )

        self.assertEqual(checkpoint["graph_corpus"]["checkpoint_stage"], 3)
        self.assertLess(checkpoint["summary"]["scanned_nodes"], latest["summary"]["scanned_nodes"])
        self.assertLess(
            checkpoint["graph_corpus"]["edges_at_checkpoint"],
            latest["graph_corpus"]["edges_at_checkpoint"],
        )

        def node_observation(report: dict, frac: str) -> dict:
            for fibre in report["phase_fibres"]:
                for pair in fibre["zero_distance_graph_pairs"]:
                    for side in ("left", "right"):
                        node_payload = pair["nodes"][side]
                        if node_payload["value"]["frac"] == frac:
                            return {
                                "node": node_payload,
                                "edges": pair["edges"][
                                    f"{side}_incoming_edge_refs"
                                ],
                                "query": pair["neighborhood_query"],
                            }
            raise AssertionError(f"missing observed node {frac}")

        latest_half = node_observation(latest, "1/2")
        checkpoint_half = node_observation(checkpoint, "1/2")
        self.assertEqual(
            latest_half["node"]["incoming_edge_count_at_checkpoint"],
            2,
        )
        self.assertEqual(
            checkpoint_half["node"]["incoming_edge_count_at_checkpoint"],
            1,
        )
        self.assertTrue(any(edge["stage"] == 4 for edge in latest_half["edges"]))
        self.assertFalse(any(edge["stage"] > 3 for edge in checkpoint_half["edges"]))
        self.assertFalse(checkpoint_half["query"]["checkpoint_exact"])
        self.assertEqual(checkpoint_half["query"]["commands"], [])

        checkpoint_four = node_observation(checkpoint, "4")
        self.assertEqual(
            checkpoint_four["node"]["status_at_checkpoint"],
            "speculative_positive_at_checkpoint",
        )
        self.assertEqual(checkpoint_four["node"]["confirmed_stage"], 4)
        identity_fibre = next(
            fibre for fibre in checkpoint["phase_fibres"] if fibre["phase"]["frac"] == "0"
        )
        four_pairs = [
            pair
            for pair in identity_fibre["zero_distance_graph_pairs"]
            if "4" in {
                pair["nodes"]["left"]["value"]["frac"],
                pair["nodes"]["right"]["value"]["frac"],
            }
        ]
        self.assertTrue(four_pairs)
        self.assertTrue(
            any(
                pair["graph_divergence"]["status_and_arrival"][
                    "confirmation_presence_mismatch_at_checkpoint"
                ]
                for pair in four_pairs
            )
        )

        half_fibre = next(
            fibre for fibre in latest["phase_fibres"] if fibre["phase"]["frac"] == "1/2"
        )
        self.assertTrue(
            any(
                pair["edges"]["unit_translation"].get("blocker")
                == "operand_not_confirmed_positive_spine"
                for pair in half_fibre["zero_distance_graph_pairs"]
                if pair["edges"]["unit_translation"].get("applicable")
            )
        )
        self.assertTrue(
            all(
                pair["matched_different_phase_control"]["match_status"]
                == "structurally_not_applicable"
                for pair in half_fibre["zero_distance_graph_pairs"]
            )
        )

    def test_malformed_additive_edge_fails_validation_and_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "malformed.sqlite"
            _create_fixture(db_path, malformed_addition=True)
            report = phase_metric_probe(
                db_path=db_path,
                max_denominator=4,
                max_phase_classes=4,
                pairs_per_phase=2,
                neighborhood_sample_limit=2,
                edge_ref_limit=2,
                slack_sample_limit=2,
            )

        audit = report["additive_triangle_audit"]
        self.assertEqual(audit["validation"]["status"], "fail")
        self.assertEqual(
            audit["validation"]["failure_counts"]["operation_relation"],
            1,
        )
        plus = audit["by_operation"]["+"]
        self.assertEqual(plus["edge_count"], plus["validated_edge_count"] + 1)
        self.assertTrue(plus["validation_failure_samples"])


if __name__ == "__main__":
    unittest.main()
