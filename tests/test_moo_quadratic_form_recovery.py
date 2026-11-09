from __future__ import annotations

import inspect
import random
import tempfile
import unittest
from collections import Counter, defaultdict
from contextlib import closing
from fractions import Fraction
from pathlib import Path

from moo.graph_corpus import GraphCorpus, GraphCorpusConfig
from moo.quadratic_form_recovery import (
    GraphBlockPermutationResult,
    NODE_CUTOFF_OFFSET,
    collision_ceiling_report,
    conditional_mutual_information,
    deterministic_label_permutation_test,
    exact_collision_ceiling,
    extract_graph_features,
    extract_node_features,
    extract_scalar_features,
    feature_matrix,
    fit_nearest_centroid,
    graph_feature_names,
    macro_balanced_accuracy,
    mutual_information,
    paired_graph_block_permutation_test,
    positive_divisors,
    predict_nearest_centroid,
    primes_through,
    scalar_feature_names,
)
from moo.research_utils import connect_readonly


def _create_feature_fixture(path: Path, *, latest_stage: int = 60) -> None:
    config = GraphCorpusConfig(
        generator="strict_stage_moo_graph",
        max_stage=int(latest_stage),
        max_abs_p=1_000,
        max_abs_q=1_000,
        max_abs_value=1_000.0,
        retain_confirmed_edges=True,
    )
    with GraphCorpus(path) as corpus:
        corpus.init_schema()
        corpus.ensure_config(config)
        nodes = {
            value: corpus.ensure_core_integer(value)[0]
            for value in range(1, 7)
        }
        # Give node 2 one stage of confirmation lag while retaining its core
        # confirmation at stage 2.
        corpus.ensure_node((2, 1), first_stage=1)

        def edge(
            stage: int,
            op: str,
            left: int | None,
            right: int | None,
            result: int,
        ) -> None:
            corpus.insert_edge(
                stage=stage,
                op=op,
                left_node_id=nodes[left] if left is not None else None,
                right_node_id=nodes[right] if right is not None else None,
                result_node_id=nodes[result],
            )

        edge(1, "seed", None, None, 1)
        edge(1, "+", 1, 1, 2)
        edge(4, "-", 4, 2, 2)
        edge(5, "custom", 3, 1, 2)
        edge(2, "+", 2, 1, 3)
        edge(2, "+", 1, 2, 3)
        edge(2, "*", 2, 2, 4)
        # Node 2 uses cutoff 52. These two edges must not enter its features.
        edge(53, "+", 5, 1, 2)
        edge(53, "+", 2, 3, 5)
        corpus.record_stage(
            stage=int(latest_stage),
            candidate_events=0,
            retained_events=0,
            new_nodes=0,
            new_edges=0,
            elapsed_seconds=0.0,
        )


def _naive_graph_block_permutation_oracle(
    training_scalar_rows: tuple[tuple[float, ...], ...],
    training_graph_rows: tuple[tuple[float, ...], ...],
    training_labels: tuple[str, ...],
    training_strata: tuple[str, ...],
    test_scalar_rows: tuple[tuple[float, ...], ...],
    test_graph_rows: tuple[tuple[float, ...], ...],
    test_labels: tuple[str, ...],
    test_strata: tuple[str, ...],
    *,
    permutation_count: int,
    seed: int,
) -> GraphBlockPermutationResult:
    """Small regression oracle retaining the original refit-every-run algorithm."""

    def shuffled(
        rows: tuple[tuple[float, ...], ...],
        strata: tuple[str, ...],
        generator: random.Random,
    ) -> tuple[tuple[float, ...], ...]:
        by_stratum: dict[str, list[int]] = defaultdict(list)
        for index, stratum in enumerate(strata):
            by_stratum[stratum].append(index)
        result = list(rows)
        for indices in by_stratum.values():
            sources = [rows[index] for index in indices]
            generator.shuffle(sources)
            for target, source in zip(indices, sources):
                result[target] = source
        return tuple(result)

    labels = tuple(sorted(set(training_labels) | set(test_labels)))
    scalar_model = fit_nearest_centroid(
        training_scalar_rows,
        training_labels,
        class_labels=labels,
    )
    scalar_score = macro_balanced_accuracy(
        test_labels,
        predict_nearest_centroid(scalar_model, test_scalar_rows),
        labels=labels,
    )
    training_combined = tuple(
        scalar + graph
        for scalar, graph in zip(training_scalar_rows, training_graph_rows)
    )
    test_combined = tuple(
        scalar + graph
        for scalar, graph in zip(test_scalar_rows, test_graph_rows)
    )
    combined_model = fit_nearest_centroid(
        training_combined,
        training_labels,
        class_labels=labels,
    )
    combined_score = macro_balanced_accuracy(
        test_labels,
        predict_nearest_centroid(combined_model, test_combined),
        labels=labels,
    )
    observed_lift = combined_score - scalar_score

    generator = random.Random(seed)
    null_lifts = []
    for _ in range(permutation_count):
        shuffled_training_graph = shuffled(
            training_graph_rows,
            training_strata,
            generator,
        )
        shuffled_test_graph = shuffled(
            test_graph_rows,
            test_strata,
            generator,
        )
        shuffled_training_combined = tuple(
            scalar + graph
            for scalar, graph in zip(training_scalar_rows, shuffled_training_graph)
        )
        shuffled_test_combined = tuple(
            scalar + graph
            for scalar, graph in zip(test_scalar_rows, shuffled_test_graph)
        )
        model = fit_nearest_centroid(
            shuffled_training_combined,
            training_labels,
            class_labels=labels,
        )
        score = macro_balanced_accuracy(
            test_labels,
            predict_nearest_centroid(model, shuffled_test_combined),
            labels=labels,
        )
        null_lifts.append(score - scalar_score)

    exceedances = sum(lift >= observed_lift for lift in null_lifts)
    training_counts = Counter(training_strata)
    test_counts = Counter(test_strata)
    training_movable = sum(
        count for count in training_counts.values() if count > 1
    )
    test_movable = sum(count for count in test_counts.values() if count > 1)
    total = len(training_labels) + len(test_labels)
    return GraphBlockPermutationResult(
        scalar_score=scalar_score,
        combined_score=combined_score,
        observed_graph_lift=observed_lift,
        null_graph_lifts=tuple(null_lifts),
        exceedance_count=exceedances,
        permutation_count=permutation_count,
        seed=seed,
        p_value=(1 + exceedances) / (1 + permutation_count),
        training_movable_row_fraction=training_movable / len(training_labels),
        test_movable_row_fraction=test_movable / len(test_labels),
        movable_row_fraction=(training_movable + test_movable) / total,
    )


class ScalarFeatureTests(unittest.TestCase):
    def test_positive_divisors_and_prime_sieve_are_exact(self) -> None:
        self.assertEqual(positive_divisors(1), (1,))
        self.assertEqual(positive_divisors(20), (1, 2, 4, 5, 10, 20))
        self.assertEqual(primes_through(1), ())
        self.assertEqual(primes_through(20), (2, 3, 5, 7, 11, 13, 17, 19))

    def test_scalar_block_contains_factorization_gcd_and_residue_one_hots(self) -> None:
        features = extract_scalar_features(
            12,
            moduli=(1, 4, 3, 4),
            prime_exponent_max_value=20,
        )
        self.assertEqual(tuple(features), scalar_feature_names(
            (1, 4, 3, 4),
            prime_exponent_max_value=20,
        ))
        self.assertEqual(features["divisor_count"], 6.0)
        self.assertEqual(features["omega"], 2.0)
        self.assertEqual(features["big_omega"], 3.0)
        self.assertEqual(features["squarefree"], 0.0)
        self.assertEqual(features["prime_exponent_2"], 2.0)
        self.assertEqual(features["prime_exponent_3"], 1.0)
        self.assertEqual(features["prime_exponent_5"], 0.0)
        self.assertEqual(features["gcd_with_3"], 3.0)
        self.assertEqual(features["gcd_with_4"], 4.0)
        self.assertEqual(features["gcd_with_1"], 1.0)
        self.assertEqual(features["residue_mod_1_is_0"], 1.0)
        self.assertEqual(
            sum(
                features[f"residue_mod_4_is_{residue}"]
                for residue in range(4)
            ),
            1.0,
        )
        self.assertEqual(features["residue_mod_4_is_0"], 1.0)

    def test_prime_exponent_bound_must_cover_the_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "exceeds prime_exponent_max_value"):
            extract_scalar_features(
                21,
                moduli=(3,),
                prime_exponent_max_value=20,
            )


class GraphFeatureTests(unittest.TestCase):
    def test_extractor_is_label_free_complete_and_uses_per_node_cutoff(self) -> None:
        parameters = tuple(inspect.signature(extract_graph_features).parameters)
        self.assertEqual(parameters, ("conn", "value"))
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "features.sqlite"
            _create_feature_fixture(db_path)
            with closing(connect_readonly(db_path)) as conn:
                features = extract_graph_features(conn, 2)
                one_features = extract_graph_features(conn, 1)
                row = extract_node_features(
                    conn,
                    2,
                    moduli=positive_divisors(20),
                    prime_exponent_max_value=6,
                )

        self.assertEqual(tuple(features), graph_feature_names())
        self.assertEqual(features["confirmation_lag"], 1.0)
        self.assertEqual(features["incoming_edge_count"], 3.0)
        self.assertEqual(features["incoming_op_add_count"], 1.0)
        self.assertEqual(features["incoming_op_subtract_count"], 1.0)
        self.assertEqual(features["incoming_op_other_count"], 1.0)
        self.assertEqual(features["incoming_distinct_operand_count"], 4.0)
        self.assertEqual(features["outgoing_edge_count"], 4.0)
        self.assertEqual(features["outgoing_op_add_count"], 2.0)
        self.assertEqual(features["outgoing_op_subtract_count"], 1.0)
        self.assertEqual(features["outgoing_op_multiply_count"], 1.0)
        self.assertEqual(features["outgoing_distinct_result_count"], 3.0)
        self.assertNotIn("incoming_op_seed_count", graph_feature_names())
        self.assertEqual(one_features["incoming_edge_count"], 1.0)
        self.assertEqual(one_features["incoming_op_other_count"], 1.0)
        self.assertEqual(row.cutoff_stage, 2 + NODE_CUTOFF_OFFSET)
        self.assertEqual(row.moduli, (1, 2, 4, 5, 10, 20))
        self.assertFalse(row.payload()["form_or_class_inputs_used"])
        names, matrix = feature_matrix((row,), feature_set="combined")
        self.assertEqual(len(names), len(matrix[0]))

    def test_extractor_refuses_a_censored_neighborhood(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "short.sqlite"
            _create_feature_fixture(db_path, latest_stage=51)
            with closing(connect_readonly(db_path)) as conn:
                with self.assertRaisesRegex(ValueError, "required cutoff 52"):
                    extract_graph_features(conn, 2)


class RecoveryStatisticTests(unittest.TestCase):
    def test_training_zscore_nearest_centroid_and_empty_class_guard(self) -> None:
        training = ((0.0, 5.0), (1.0, 5.0), (9.0, 5.0), (10.0, 5.0))
        labels = ("A", "A", "B", "B")
        model = fit_nearest_centroid(
            training,
            labels,
            feature_names=("signal", "constant"),
            class_labels=("A", "B"),
        )
        self.assertEqual(model.training_scales[1], 1.0)
        self.assertEqual(model.centroids["A"][1], 0.0)
        self.assertEqual(model.centroids["B"][1], 0.0)
        self.assertEqual(
            predict_nearest_centroid(model, ((-1.0, 5.0), (11.0, 5.0))),
            ("A", "B"),
        )
        tied = fit_nearest_centroid(
            ((-1.0,), (1.0,), (0.0,)),
            ("Z", "Z", "A"),
        )
        self.assertEqual(
            predict_nearest_centroid(tied, ((0.0,),)),
            ("Z",),
        )
        with self.assertRaisesRegex(ValueError, "empty training centroid"):
            fit_nearest_centroid(
                training,
                labels,
                class_labels=("A", "B", "C"),
            )

    def test_macro_balanced_accuracy_is_macro_recall(self) -> None:
        score = macro_balanced_accuracy(
            ("A", "A", "A", "B"),
            ("A", "A", "B", "B"),
        )
        self.assertAlmostEqual(score, 5.0 / 6.0)

    def test_label_permutation_test_is_deterministic(self) -> None:
        training = ((0.0,), (1.0,), (2.0,), (8.0,), (9.0,), (10.0,))
        training_labels = ("A", "A", "A", "B", "B", "B")
        test = ((0.5,), (1.5,), (8.5,), (9.5,))
        test_labels = ("A", "A", "B", "B")
        first = deterministic_label_permutation_test(
            training,
            training_labels,
            test,
            test_labels,
            permutation_count=24,
            seed=17,
        )
        second = deterministic_label_permutation_test(
            training,
            training_labels,
            test,
            test_labels,
            permutation_count=24,
            seed=17,
        )
        self.assertEqual(first, second)
        self.assertEqual(first.observed_score, 1.0)
        self.assertGreater(first.p_value, 0.0)
        self.assertLessEqual(first.p_value, 1.0)

    def test_paired_graph_block_permutation_reports_lift_and_mobility(self) -> None:
        train_scalar = ((0.0,),) * 4
        train_graph = ((-2.0,), (-1.0,), (1.0,), (2.0,))
        train_labels = ("A", "A", "B", "B")
        test_scalar = ((0.0,),) * 4
        test_graph = ((-1.5,), (-0.5,), (0.5,), (1.5,))
        test_labels = ("A", "A", "B", "B")
        strata = ("matched",) * 4
        first = paired_graph_block_permutation_test(
            train_scalar,
            train_graph,
            train_labels,
            strata,
            test_scalar,
            test_graph,
            test_labels,
            strata,
            permutation_count=24,
            seed=9,
        )
        second = paired_graph_block_permutation_test(
            train_scalar,
            train_graph,
            train_labels,
            strata,
            test_scalar,
            test_graph,
            test_labels,
            strata,
            permutation_count=24,
            seed=9,
        )
        self.assertEqual(first, second)
        self.assertEqual(first.scalar_score, 0.5)
        self.assertEqual(first.combined_score, 1.0)
        self.assertEqual(first.observed_graph_lift, 0.5)
        self.assertEqual(first.training_movable_row_fraction, 1.0)
        self.assertEqual(first.test_movable_row_fraction, 1.0)
        self.assertEqual(first.movable_row_fraction, 1.0)
        self.assertGreater(first.p_value, 0.0)

    def test_optimized_graph_permutation_matches_naive_oracle_exactly(self) -> None:
        train_scalar = (
            (0.2, 3.0),
            (1.1, 1.0),
            (2.4, 2.0),
            (4.2, 0.0),
            (5.3, 4.0),
            (6.8, 2.0),
        )
        train_graph = (
            (0.1, 6.0),
            (0.7, 3.0),
            (1.8, 5.0),
            (4.1, 2.0),
            (5.4, 0.0),
            (6.2, 1.0),
        )
        train_labels = ("A", "A", "A", "B", "B", "B")
        train_strata = ("x", "y", "x", "x", "y", "x")
        test_scalar = ((0.8, 2.0), (2.0, 1.0), (4.8, 3.0), (6.0, 1.0))
        test_graph = ((0.4, 4.0), (1.5, 2.0), (4.7, 1.0), (5.9, 3.0))
        test_labels = ("A", "A", "B", "B")
        test_strata = ("x", "y", "x", "y")
        arguments = (
            train_scalar,
            train_graph,
            train_labels,
            train_strata,
            test_scalar,
            test_graph,
            test_labels,
            test_strata,
        )
        optimized = paired_graph_block_permutation_test(
            *arguments,
            permutation_count=37,
            seed=91,
        )
        naive = _naive_graph_block_permutation_oracle(
            *arguments,
            permutation_count=37,
            seed=91,
        )
        self.assertEqual(optimized, naive)

    def test_mutual_information_and_conditional_information(self) -> None:
        x = (0, 0, 1, 1)
        y = (0, 0, 1, 1)
        z = (0, 0, 1, 1)
        self.assertAlmostEqual(mutual_information(x, y), 1.0)
        self.assertAlmostEqual(conditional_mutual_information(x, y, z), 0.0)
        self.assertAlmostEqual(
            mutual_information((0, 0, 1, 1), (0, 1, 0, 1)),
            0.0,
        )

    def test_collision_ceiling_is_exact_for_accuracy_and_balanced_accuracy(self) -> None:
        rows = ((0,), (0,), (1,), (1,))
        labels = ("A", "B", "A", "A")
        self.assertEqual(
            exact_collision_ceiling(rows, labels, metric="accuracy"),
            Fraction(3, 4),
        )
        self.assertEqual(
            exact_collision_ceiling(rows, labels),
            Fraction(5, 6),
        )
        report = collision_ceiling_report(rows, labels)
        self.assertEqual(report["accuracy_ceiling_exact"], "3/4")
        self.assertEqual(report["macro_balanced_accuracy_ceiling_exact"], "5/6")
        self.assertEqual(report["conflicting_feature_signature_count"], 1)


if __name__ == "__main__":
    unittest.main()
