from __future__ import annotations

import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Union

from moo.graph_corpus import GraphCorpus, GraphCorpusConfig, normalize_key
from moo.series_probe import (
    euler_product_steps,
    geometric_series_steps,
    primes_up_to,
    series_probe,
    zeta2_steps,
)


Value = Union[int, Fraction]


def _create_fixture(path: Path) -> None:
    config = GraphCorpusConfig(
        generator="strict_stage_moo_graph",
        max_stage=49,
        max_abs_p=1_000,
        max_abs_q=1_000,
        max_abs_value=1_000.0,
        retain_confirmed_edges=True,
    )
    with GraphCorpus(path) as corpus:
        corpus.init_schema()
        corpus.ensure_config(config)

        def node_id(value: Value, *, first_stage: int) -> int:
            fraction = value if isinstance(value, Fraction) else Fraction(value, 1)
            key = normalize_key(fraction.numerator, fraction.denominator)
            found, _ = corpus.ensure_node(key, first_stage=first_stage)
            return found

        def add_edge(
            left: int,
            op: str,
            right: int,
            result: Value,
            *,
            stage: int,
        ) -> None:
            left_id, _ = corpus.ensure_core_integer(left)
            right_id, _ = corpus.ensure_core_integer(right)
            result_id = node_id(result, first_stage=stage)
            corpus.insert_edge(
                stage=stage,
                op=op,
                left_node_id=left_id,
                right_node_id=right_id,
                result_node_id=result_id,
            )

        one_id, _ = corpus.ensure_core_integer(1)
        corpus.insert_edge(
            stage=1,
            op="seed",
            left_node_id=None,
            right_node_id=None,
            result_node_id=one_id,
        )

        # Genuine positive-integer geometric recurrence for ratio 2.
        add_edge(1, "*", 2, 2, stage=2)
        add_edge(2, "*", 1, 2, stage=2)
        add_edge(1, "+", 2, 3, stage=2)
        add_edge(2, "+", 1, 3, stage=2)
        add_edge(2, "*", 2, 4, stage=2)
        add_edge(3, "+", 4, 7, stage=4)
        add_edge(4, "+", 3, 7, stage=4)

        # Square witnesses used by the reciprocal-square and Euler rows.
        add_edge(1, "*", 1, 1, stage=1)
        add_edge(2, "*", 2, 4, stage=2)
        add_edge(3, "*", 3, 9, stage=3)

        # Canonical quotient landings only; no rational operand is reused.
        for numerator, denominator, value, stage in [
            (1, 1, Fraction(1, 1), 1),
            (1, 2, Fraction(1, 2), 2),
            (1, 4, Fraction(1, 4), 4),
            (1, 9, Fraction(1, 9), 9),
            (3, 2, Fraction(3, 2), 3),
            (7, 4, Fraction(7, 4), 7),
            (5, 4, Fraction(5, 4), 5),
            (49, 36, Fraction(49, 36), 49),
            (4, 3, Fraction(4, 3), 4),
            (9, 8, Fraction(9, 8), 9),
        ]:
            add_edge(numerator, "/", denominator, value, stage=stage)

        corpus.record_stage(
            stage=49,
            candidate_events=0,
            retained_events=0,
            new_nodes=0,
            new_edges=0,
            elapsed_seconds=0.0,
        )


class SeriesProbeMathTests(unittest.TestCase):
    def test_geometric_recurrence_matches_closed_form(self) -> None:
        steps = geometric_series_steps(Fraction(1, 2), 4)
        self.assertEqual(
            [step.term for step in steps],
            [Fraction(1), Fraction(1, 2), Fraction(1, 4), Fraction(1, 8)],
        )
        self.assertEqual(
            [step.partial_sum for step in steps],
            [Fraction(1), Fraction(3, 2), Fraction(7, 4), Fraction(15, 8)],
        )
        self.assertTrue(all(step.partial_sum == step.closed_form for step in steps))

        for ratio in [Fraction(0), Fraction(1), Fraction(-1, 2), Fraction(2)]:
            rows = geometric_series_steps(ratio, 5)
            self.assertTrue(all(row.partial_sum == row.closed_form for row in rows))

    def test_zeta2_partial_sums_are_exact(self) -> None:
        steps = zeta2_steps(5)
        self.assertEqual(steps[1].partial_sum, Fraction(5, 4))
        self.assertEqual(steps[2].partial_sum, Fraction(49, 36))
        self.assertEqual(steps[3].partial_sum, Fraction(205, 144))
        self.assertEqual(steps[4].partial_sum, Fraction(5269, 3600))

    def test_euler_products_and_local_geometric_residuals_are_exact(self) -> None:
        self.assertEqual(primes_up_to(13), [2, 3, 5, 7, 11, 13])
        steps = euler_product_steps(7, local_term_count=4)
        self.assertEqual(
            [step.factor for step in steps],
            [Fraction(4, 3), Fraction(9, 8), Fraction(25, 24), Fraction(49, 48)],
        )
        self.assertEqual(
            [step.partial_product for step in steps],
            [Fraction(4, 3), Fraction(3, 2), Fraction(25, 16), Fraction(1225, 768)],
        )
        for step in steps:
            self.assertEqual(
                step.factor,
                step.local_partial_sum + step.local_residual,
            )


class SeriesProbeCorpusTests(unittest.TestCase):
    def test_rational_endpoints_do_not_imply_series_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = series_probe(
                db_path=db_path,
                geometric_ratio=Fraction(1, 2),
                geometric_terms=3,
                zeta_max_n=3,
                euler_max_prime=3,
                euler_local_geometric_terms=2,
                edge_limit=3,
            )

        self.assertEqual(report["corpus"]["alignment"]["status"], "pass")

        geometric_row = report["geometric"]["rows"][2]
        self.assertEqual(geometric_row["partial_sum"]["frac"], "7/4")
        self.assertTrue(geometric_row["graph"]["partial_sum_node"]["present"])
        self.assertTrue(
            geometric_row["graph"]["direct_endpoint_quotient_edge"]["present"]
        )
        self.assertFalse(geometric_row["graph"]["partial_sum_step_edge"]["present"])
        self.assertEqual(
            geometric_row["graph"]["partial_sum_step_edge"]["blocker"],
            "operand_not_positive_spine",
        )
        self.assertEqual(
            geometric_row["graph"]["partial_sum_node"]["graph_evidence"]["graph_reading"],
            "quotient_landing_only",
        )

        zeta_row = report["zeta2"]["rows"][2]
        self.assertEqual(zeta_row["partial_sum"]["frac"], "49/36")
        self.assertTrue(zeta_row["graph"]["reciprocal_square_edge"]["present"])
        self.assertTrue(zeta_row["graph"]["partial_sum_node"]["present"])
        self.assertFalse(zeta_row["graph"]["partial_sum_step_edge"]["present"])
        self.assertEqual(
            zeta_row["graph"]["partial_sum_step_edge"]["blocker"],
            "operand_not_positive_spine",
        )
        self.assertEqual(
            report["zeta2"]["summary"]["partial_sum_step_edges"]
            ["stage_aperture_blockers"],
            {"operand_not_positive_spine": 2},
        )

        euler_row = report["euler_product"]["rows"][1]
        self.assertEqual(euler_row["closed_factor_partial_product"]["frac"], "3/2")
        self.assertTrue(euler_row["graph"]["direct_factor_quotient_edge"]["present"])
        self.assertTrue(
            euler_row["graph"]["closed_factor_partial_product_node"]["present"]
        )
        self.assertFalse(
            euler_row["graph"]["closed_factor_partial_product_step_edge"]["present"]
        )
        self.assertEqual(
            euler_row["graph"]["closed_factor_partial_product_step_edge"]["blocker"],
            "operand_not_positive_spine",
        )
        self.assertEqual(
            report["euler_product"]["summary"]
            ["closed_factor_partial_product_step_edges"]["stage_aperture_blockers"],
            {"operand_not_positive_spine": 2},
        )
        self.assertFalse(
            euler_row["local_geometric_expansion"]["recurrence_edges_inspected"]
        )

        collisions = report["cross_family"]["shared_endpoint_collisions"]
        collision_values = {row["value"]["frac"] for row in collisions}
        self.assertIn("1", collision_values)
        self.assertIn("3/2", collision_values)

    def test_integer_ratio_calibration_finds_real_recurrence_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = series_probe(
                db_path=db_path,
                geometric_ratio=Fraction(2, 1),
                geometric_terms=3,
                zeta_max_n=2,
                euler_max_prime=3,
                euler_local_geometric_terms=2,
                edge_limit=3,
            )

        summary = report["geometric"]["summary"]
        self.assertEqual(summary["term_step_edges"]["present_step_occurrences"], 2)
        self.assertEqual(
            summary["partial_sum_step_edges"]["present_step_occurrences"],
            2,
        )
        self.assertTrue(
            report["geometric"]["rows"][2]["graph"]["partial_sum_step_edge"]["present"]
        )

    def test_edge_limit_must_cover_commuted_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            with self.assertRaisesRegex(ValueError, "edge_limit must be >= 2"):
                series_probe(
                    db_path=db_path,
                    geometric_ratio=Fraction(2, 1),
                    geometric_terms=3,
                    zeta_max_n=2,
                    euler_max_prime=3,
                    euler_local_geometric_terms=2,
                    edge_limit=1,
                )

    def test_summaries_separate_rows_from_distinct_nodes_and_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = series_probe(
                db_path=db_path,
                geometric_ratio=Fraction(1, 1),
                geometric_terms=4,
                zeta_max_n=2,
                euler_max_prime=3,
                euler_local_geometric_terms=2,
                edge_limit=3,
            )

        term_nodes = report["geometric"]["summary"]["term_nodes"]
        self.assertEqual(term_nodes["row_occurrences"], 4)
        self.assertEqual(term_nodes["distinct_expected_nodes"], 1)
        term_edges = report["geometric"]["summary"]["term_step_edges"]
        self.assertEqual(term_edges["present_step_occurrences"], 3)
        self.assertEqual(term_edges["distinct_present_edge_ids"], 1)

    def test_absent_endpoint_reports_corpus_censoring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = series_probe(
                db_path=db_path,
                geometric_ratio=Fraction(1, 2),
                geometric_terms=3,
                zeta_max_n=5,
                euler_max_prime=3,
                euler_local_geometric_terms=2,
                edge_limit=3,
            )

        missing = report["zeta2"]["rows"][4]["graph"]["partial_sum_node"]
        self.assertFalse(missing["present"])
        self.assertTrue(missing["corpus_censoring"]["censored_by_config"])
        self.assertIn(
            "denominator_bound_exceeded",
            missing["corpus_censoring"]["reasons"],
        )
        self.assertIn(
            "direct_quotient_stage_beyond_corpus",
            missing["corpus_censoring"]["reasons"],
        )

    def test_default_safety_caps_require_explicit_full_scan(self) -> None:
        with self.assertRaisesRegex(ValueError, "pass --full-scan"):
            series_probe(
                db_path=Path("unused.sqlite"),
                geometric_ratio=Fraction(1, 2),
                geometric_terms=65,
                zeta_max_n=2,
                euler_max_prime=3,
                euler_local_geometric_terms=2,
                edge_limit=3,
            )


if __name__ == "__main__":
    unittest.main()
