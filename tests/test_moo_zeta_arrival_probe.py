from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from moo.zeta_arrival_probe import (
    _deterministic_block_permutation,
    _load_source_schedules,
    _radial_diagnostics,
    _schedule_summary,
    zeta_arrival_probe,
)
from moo.strict_stage_moo import build_strict_stage_graph


def _create_fixture(path: Path) -> None:
    build_strict_stage_graph(
        db_path=path,
        max_stage=4,
        max_abs_p=100,
        max_abs_q=100,
        max_abs_value=100.0,
        max_edges=None,
        time_limit_seconds=None,
        commit_every=4,
        retain_confirmed_edges=True,
        verbose=False,
    )


class ZetaArrivalScheduleTests(unittest.TestCase):
    def test_schedule_keeps_presence_readiness_and_reciprocal_evidence_separate(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arrival.sqlite"
            _create_fixture(db_path)
            import sqlite3

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            schedules = _load_source_schedules(conn, hasse_terms=4)
            conn.close()

        self.assertEqual(
            [row.source_node_present_stage for row in schedules],
            [1, 1, 2, 2],
        )
        self.assertEqual(
            [row.source_operand_ready_stage for row in schedules],
            [1, 2, 3, 4],
        )
        self.assertEqual(
            [row.direct_reciprocal_edge_present_stage for row in schedules],
            [1, 2, 3, 4],
        )
        self.assertEqual(schedules[0].reciprocal_witness_stages, (1, 2, 3, 4))
        self.assertEqual(schedules[1].reciprocal_witness_stages, (2, 4))
        summary = _schedule_summary(schedules, stage_horizon=4)
        self.assertTrue(summary["operand_ready_and_direct_reciprocal_stage_identical"])
        self.assertTrue(summary["operational_schedule_is_natural_source_order"])
        self.assertTrue(summary["all_reciprocal_witness_ladders_match_divisibility"])
        self.assertEqual(
            summary["operand_ready_and_direct_reciprocal_comparison"]["status"],
            "full_schedule_identical",
        )

    def test_checkpoint_suppresses_future_operational_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arrival.sqlite"
            _create_fixture(db_path)
            report = zeta_arrival_probe(
                db_path=db_path,
                sigma=0.5,
                t=14.134725141734693,
                hasse_terms=4,
                stage_horizon=2,
                control_delta=0.01,
                height_control_ts=[10.0, 18.0],
                envelope_guard=1e-12,
                permutation_samples=4,
                target_kind="user_supplied_reference_zero",
                target_label="fixture coordinate",
            )

        masks = report["mask_results"]
        present = masks["source_node_present"]["target_trajectory"][-1]
        operational = masks["operational_source_and_reciprocal_edge"][
            "target_trajectory"
        ][-1]
        self.assertEqual(present["active_source_count"], 4)
        self.assertEqual(operational["active_source_count"], 2)
        self.assertFalse(
            report["summary"][
                "speculative_presence_effect_is_admissible_runtime_computation"
            ]
        )
        self.assertEqual(
            report["summary"]["classification"],
            "incomplete_operational_schedule_arrival_exploration",
        )
        comparison = report["source_schedule"]["summary"][
            "operand_ready_and_direct_reciprocal_comparison"
        ]
        self.assertEqual(comparison["observed_equal_source_count"], 2)
        self.assertEqual(comparison["jointly_right_censored_source_count"], 2)
        self.assertFalse(
            report["source_schedule"]["summary"][
                "operand_ready_and_direct_reciprocal_stage_identical"
            ]
        )
        self.assertTrue(
            report["source_schedule"]["summary"][
                "operational_schedule_is_observed_natural_prefix_through_horizon"
            ]
        )

    def test_partial_strict_stage_prefix_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arrival.sqlite"
            build_strict_stage_graph(
                db_path=db_path,
                max_stage=4,
                max_abs_p=100,
                max_abs_q=100,
                max_abs_value=100.0,
                max_edges=3,
                time_limit_seconds=None,
                commit_every=4,
                retain_confirmed_edges=True,
                verbose=False,
            )
            with self.assertRaisesRegex(
                ValueError,
                "strict-stage prefix validation failed",
            ):
                zeta_arrival_probe(
                    db_path=db_path,
                    sigma=0.5,
                    t=14.134725141734693,
                    hasse_terms=4,
                    stage_horizon=1,
                    height_control_ts=[10.0, 18.0],
                    permutation_samples=2,
                    target_kind="numerical_candidate",
                )


class ZetaArrivalNumericalTests(unittest.TestCase):
    def test_handcrafted_radial_path_classifies_inward_steps(self) -> None:
        metrics = _radial_diagnostics([1.0, 2.0, 1.5, 1.0, 0.5])
        self.assertEqual(metrics["peak_index"], 1)
        self.assertEqual(metrics["resolved_post_peak_step_count"], 3)
        self.assertEqual(metrics["resolved_inward_step_count"], 3)
        self.assertEqual(metrics["longest_resolved_inward_streak"], 3)
        self.assertAlmostEqual(metrics["post_peak_radial_efficiency"], 1.0)

    def test_block_permutation_is_deterministic_and_local(self) -> None:
        first = _deterministic_block_permutation(
            8,
            sample_index=17,
            block_size=2,
        )
        second = _deterministic_block_permutation(
            8,
            sample_index=17,
            block_size=2,
        )
        self.assertEqual(first, second)
        self.assertEqual(sorted(first), list(range(8)))
        for start in range(0, 8, 2):
            self.assertEqual(set(first[start : start + 2]), {start, start + 1})

    def test_complete_report_reconstructs_terminal_endpoint_and_add_one_rank(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arrival.sqlite"
            _create_fixture(db_path)
            report = zeta_arrival_probe(
                db_path=db_path,
                sigma=0.5,
                t=14.134725141734693,
                hasse_terms=4,
                stage_horizon=4,
                control_delta=0.01,
                height_control_ts=[10.0, 18.0],
                envelope_guard=1e-12,
                permutation_samples=8,
                target_kind="user_supplied_reference_zero",
                target_label="fixture coordinate",
            )

        self.assertEqual(
            report["summary"]["operational_terminal_reconstruction_difference"],
            0.0,
        )
        self.assertTrue(
            report["summary"][
                "operational_terminal_reconstruction_passes_binary64_guard"
            ]
        )
        reciprocal_ready = [
            row["reciprocal_result_is_operand_ready_at_operational_arrival"]
            for row in report["source_schedule"]["rows"]
        ]
        self.assertEqual(reciprocal_ready, [True, False, False, False])
        complete_nulls = [
            row["block_size_2"]
            for row in report["endpoint_preserving_permutation_nulls"]
            if row["block_size_2"]["status"] == "complete"
        ]
        self.assertTrue(complete_nulls)
        for null in complete_nulls:
            rank = null["metrics"]["longest_resolved_inward_streak"][
                "add_one_monte_carlo_tail_fraction"
            ]
            self.assertGreater(rank, 0.0)
            self.assertTrue(null["terminal_endpoint_invariance"]["passes"])
            self.assertLessEqual(
                null["terminal_endpoint_invariance"][
                    "maximum_normalized_difference"
                ],
                null["terminal_endpoint_invariance"][
                    "normalized_binary64_guard"
                ],
            )

        primary = next(
            row["block_size_2"]
            for row in report["endpoint_preserving_permutation_nulls"]
            if "operational_source_and_reciprocal_edge"
            in row["mask_kinds_with_identical_schedule"]
        )
        self.assertEqual(
            primary["metrics"]["longest_resolved_inward_streak"][
                "natural_value"
            ],
            report["summary"]["operational_target_metrics"][
                "longest_resolved_inward_streak"
            ],
        )
        self.assertEqual(
            primary["metrics"]["resolved_inward_fraction"]["natural_value"],
            report["summary"]["operational_target_metrics"][
                "resolved_inward_fraction"
            ],
        )
        self.assertEqual(
            primary["metrics"]["post_peak_radial_efficiency"]["natural_value"],
            report["summary"]["operational_target_metrics"][
                "post_peak_radial_efficiency"
            ],
        )
        criteria = report["summary"]["configured_v1_collapse_criteria"]
        self.assertFalse(
            criteria["primary_block_null_rank_resolution_sufficient"]
        )
        self.assertEqual(
            criteria[
                "primary_block_null_minimum_attainable_add_one_tail_fraction"
            ],
            1.0 / 9.0,
        )

    def test_control_target_never_receives_reference_collapse_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arrival.sqlite"
            _create_fixture(db_path)
            report = zeta_arrival_probe(
                db_path=db_path,
                sigma=0.5,
                t=10.0,
                hasse_terms=4,
                stage_horizon=4,
                height_control_ts=[11.0, 18.0],
                permutation_samples=2,
                target_kind="control",
            )

        self.assertEqual(
            report["summary"]["classification"],
            "underresolved_control_trajectory",
        )

    def test_close_height_controls_keep_distinct_report_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "arrival.sqlite"
            _create_fixture(db_path)
            report = zeta_arrival_probe(
                db_path=db_path,
                sigma=0.5,
                t=14.134725141734693,
                hasse_terms=4,
                stage_horizon=4,
                height_control_ts=[10.0000001, 10.0000002],
                permutation_samples=2,
                target_kind="numerical_candidate",
            )

        self.assertEqual(
            len(report["coordinate_evaluations"]["height_controls"]),
            2,
        )

    def test_candidate_domain_and_hard_limits_are_enforced(self) -> None:
        with self.assertRaisesRegex(ValueError, "require 0 < sigma < 1"):
            zeta_arrival_probe(
                db_path=Path("unused.sqlite"),
                sigma=2.0,
                t=14.0,
                hasse_terms=4,
                height_control_ts=[10.0],
                permutation_samples=1,
                target_kind="numerical_candidate",
                full_scan=True,
            )
        with self.assertRaisesRegex(ValueError, "hard workload limit"):
            zeta_arrival_probe(
                db_path=Path("unused.sqlite"),
                sigma=0.5,
                t=14.0,
                hasse_terms=4,
                height_control_ts=[10.0],
                permutation_samples=4097,
                target_kind="numerical_candidate",
                full_scan=True,
            )


if __name__ == "__main__":
    unittest.main()
