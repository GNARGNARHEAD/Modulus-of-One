from __future__ import annotations

import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from typing import Union

from moo.circle_as_one_probe import (
    additive_return_order,
    circle_as_one_probe,
    cyclotomic_closure_payload,
    euler_totient,
    phase_cycle,
    phase_fraction,
)
from moo.graph_corpus import GraphCorpus, GraphCorpusConfig, normalize_key


Value = Union[int, Fraction]


def _create_fixture(path: Path) -> None:
    config = GraphCorpusConfig(
        generator="strict_stage_moo_graph",
        max_stage=5,
        max_abs_p=100,
        max_abs_q=100,
        max_abs_value=10.0,
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

        def core(value: int) -> int:
            found, _ = corpus.ensure_core_integer(value)
            return found

        one_id = core(1)
        corpus.insert_edge(
            stage=1,
            op="seed",
            left_node_id=None,
            right_node_id=None,
            result_node_id=one_id,
        )

        for left in range(1, 5):
            result = left + 1
            left_id = core(left)
            result_id = core(result)
            corpus.insert_edge(
                stage=result,
                op="+",
                left_node_id=left_id,
                right_node_id=one_id,
                result_node_id=result_id,
            )
            if left != 1:
                corpus.insert_edge(
                    stage=result,
                    op="+",
                    left_node_id=one_id,
                    right_node_id=left_id,
                    result_node_id=result_id,
                )

        denominator_id = core(2)
        for numerator in [1, 3, 5]:
            numerator_id = core(numerator)
            result = Fraction(numerator, 2)
            result_id = node_id(result, first_stage=max(numerator, 2))
            corpus.insert_edge(
                stage=max(numerator, 2),
                op="/",
                left_node_id=numerator_id,
                right_node_id=denominator_id,
                result_node_id=result_id,
            )

        corpus.record_stage(
            stage=5,
            candidate_events=0,
            retained_events=0,
            new_nodes=0,
            new_edges=0,
            elapsed_seconds=0.0,
        )


class CircleAsOneMathTests(unittest.TestCase):
    def test_phase_fraction_discards_exact_integer_lift(self) -> None:
        self.assertEqual(phase_fraction(Fraction(7, 3)), Fraction(1, 3))
        self.assertEqual(phase_fraction(Fraction(-1, 3)), Fraction(2, 3))
        self.assertEqual(phase_fraction(8), Fraction(0, 1))

    def test_reduced_denominator_is_return_order(self) -> None:
        self.assertEqual(additive_return_order(Fraction(2, 5)), 5)
        self.assertEqual(additive_return_order(Fraction(7, 3)), 3)
        self.assertEqual(additive_return_order(4), 1)
        self.assertEqual(
            [euler_totient(value) for value in range(1, 7)],
            [1, 1, 2, 2, 4, 2],
        )

    def test_phase_cycle_returns_only_after_full_order(self) -> None:
        self.assertEqual(
            phase_cycle(Fraction(2, 5)),
            [
                Fraction(0),
                Fraction(2, 5),
                Fraction(4, 5),
                Fraction(1, 5),
                Fraction(3, 5),
            ],
        )
        closure = cyclotomic_closure_payload(
            Fraction(2, 5),
            cycle_point_limit=10,
        )
        self.assertEqual(closure["return_order"], 5)
        self.assertEqual(closure["full_minimal_orbit_sum"], "0")
        self.assertTrue(closure["returns_to_identity"])


class CircleAsOneCorpusTests(unittest.TestCase):
    def test_probe_separates_quotient_fibre_from_graph_witnesses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = circle_as_one_probe(
                db_path=db_path,
                max_denominator=4,
                max_phase_classes=8,
                sample_lifts=8,
                translation_pair_limit=8,
                edge_limit=4,
                cycle_point_limit=8,
            )

        self.assertEqual(report["corpus"]["alignment"]["status"], "pass")
        self.assertEqual(report["summary"]["identity_lifts"], 5)

        classes = {
            row["phase"]["frac"]: row for row in report["phase_classes"]
        }
        identity = classes["0"]
        half = classes["1/2"]

        self.assertEqual(identity["quotient_fibre"]["observed_lift_count"], 5)
        self.assertGreaterEqual(identity["unit_translation"]["witnessed_pairs"], 4)

        self.assertEqual(half["phase"]["additive_return_order"], 2)
        self.assertEqual(half["quotient_fibre"]["observed_lift_count"], 3)
        self.assertEqual(half["unit_translation"]["witnessed_pairs"], 0)
        self.assertEqual(
            half["unit_translation"]["blockers"],
            {"operand_not_positive_spine": 2},
        )
        self.assertEqual(
            half["finite_return_cycle"]["full_minimal_orbit_sum"],
            "0",
        )


if __name__ == "__main__":
    unittest.main()
