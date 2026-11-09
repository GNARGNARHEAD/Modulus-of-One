from __future__ import annotations

import json
import random
import shutil
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from moo.quadratic_form_nested_math import D20_FAMILY, D23_FAMILY, D56_FAMILY
from moo.quadratic_form_nested_probe import (
    DEFAULT_INJECTIVE_MODULUS,
    EXPERIMENT_ID,
    FROZEN_ANALYSIS_CLI_ARGS,
    FROZEN_ANALYSIS_SOURCE_PATHS,
    current_source_path,
    SCHEMA_VERSION,
    _analysis_manifest_audit,
    _class_counts,
    _family_moduli,
    _family_representations,
    _holm_adjust,
    _effective_mobility,
    _distribution_summary,
    _matched_strata,
    _matrix_for_samples,
    _operation_bucket_indices,
    _operation_histogram_null,
    _prefix_feature_parity,
    _quotient_information_report,
    _scalar_baseline_moduli,
    _slice_rows,
    _support_rows,
    _shuffle_operation_buckets,
    _task_exclusion_report,
    _task_samples,
    nested_quadratic_form_probe,
)
from moo.quadratic_form_recovery import (
    NodeFeatureRow,
    extract_scalar_features,
    fit_nearest_centroid,
    graph_feature_names,
    macro_balanced_accuracy,
    predict_nearest_centroid,
)
from moo.research_utils import connect_readonly, file_sha256
from moo.strict_stage_moo import build_strict_stage_graph


def _naive_operation_histogram_null(
    training_samples,
    test_samples,
    training_features,
    test_features,
    *,
    permutation_count,
    seed,
):
    """Reference implementation retained in tests for exact equivalence."""
    scalar_names, train_scalar, train_labels = _matrix_for_samples(
        training_samples, training_features, "scalar"
    )
    graph_names, train_graph, _ = _matrix_for_samples(
        training_samples, training_features, "graph"
    )
    test_scalar_names, test_scalar, test_labels = _matrix_for_samples(
        test_samples, test_features, "scalar"
    )
    test_graph_names, test_graph, _ = _matrix_for_samples(
        test_samples, test_features, "graph"
    )
    if scalar_names != test_scalar_names or graph_names != test_graph_names:
        raise AssertionError("operation-null feature schemas differ by split")
    labels = tuple(sorted(set(train_labels) | set(test_labels)))
    scalar_model = fit_nearest_centroid(
        train_scalar,
        train_labels,
        feature_names=scalar_names,
        class_labels=labels,
    )
    scalar_score = macro_balanced_accuracy(
        test_labels,
        predict_nearest_centroid(scalar_model, test_scalar),
        labels=labels,
    )
    combined_names = scalar_names + graph_names
    observed_train = tuple(
        scalar + graph for scalar, graph in zip(train_scalar, train_graph)
    )
    observed_test = tuple(
        scalar + graph for scalar, graph in zip(test_scalar, test_graph)
    )
    observed_model = fit_nearest_centroid(
        observed_train,
        train_labels,
        feature_names=combined_names,
        class_labels=labels,
    )
    observed_score = macro_balanced_accuracy(
        test_labels,
        predict_nearest_centroid(observed_model, observed_test),
        labels=labels,
    )
    observed_lift = observed_score - scalar_score
    generator = random.Random(int(seed))
    null_lifts = []
    for _ in range(int(permutation_count)):
        shuffled_train_graph = _shuffle_operation_buckets(train_graph, generator)
        shuffled_test_graph = _shuffle_operation_buckets(test_graph, generator)
        shuffled_train = tuple(
            scalar + graph
            for scalar, graph in zip(train_scalar, shuffled_train_graph)
        )
        shuffled_test = tuple(
            scalar + graph
            for scalar, graph in zip(test_scalar, shuffled_test_graph)
        )
        model = fit_nearest_centroid(
            shuffled_train,
            train_labels,
            feature_names=combined_names,
            class_labels=labels,
        )
        score = macro_balanced_accuracy(
            test_labels,
            predict_nearest_centroid(model, shuffled_test),
            labels=labels,
        )
        null_lifts.append(score - scalar_score)
    exceedances = sum(lift >= observed_lift for lift in null_lifts)
    return {
        "scheme": (
            "split-wise incoming/outgoing operation-bucket multiset shuffle; "
            "per-row directional totals and split-wide bucket totals preserved"
        ),
        "inferential_status": "destructive_descriptive_ablation_only",
        "graph_realizability_preserved": False,
        "incoming_outgoing_edge_coupling_preserved": False,
        "other_bucket_includes_seed_occurrences": True,
        "buckets": ["+", "-", "*", "/", "other"],
        "permutation_count": int(permutation_count),
        "seed": int(seed),
        "scalar_score": scalar_score,
        "combined_score": observed_score,
        "observed_graph_lift": observed_lift,
        "null_lift_summary": _distribution_summary(null_lifts),
        "exceedance_count": exceedances,
        "p_value": (1 + exceedances) / (1 + int(permutation_count)),
    }


class NestedQuadraticFormOrchestrationHelperTests(unittest.TestCase):
    @staticmethod
    def _feature_row(
        value: int,
        *,
        incoming: int,
        outgoing: int,
        marker: int,
    ) -> NodeFeatureRow:
        names = graph_feature_names()
        graph = {name: 0.0 for name in names}
        graph["incoming_edge_count"] = float(incoming)
        graph["outgoing_edge_count"] = float(outgoing)
        graph["incoming_distinct_operand_count"] = float(marker)
        return NodeFeatureRow(
            value=value,
            cutoff_stage=value + 50,
            moduli=(1,),
            prime_exponent_max_value=None,
            scalar_names=("scalar",),
            scalar_values=(float(value),),
            graph_names=names,
            graph_values=tuple(graph[name] for name in names),
        )

    def test_injective_quotient_modulus_is_not_a_scalar_model_feature(self) -> None:
        for family in (D20_FAMILY, D23_FAMILY, D56_FAMILY):
            scalar_moduli = _scalar_baseline_moduli(family)
            quotient_moduli = _family_moduli(family)
            self.assertNotIn(DEFAULT_INJECTIVE_MODULUS, scalar_moduli)
            self.assertIn(DEFAULT_INJECTIVE_MODULUS, quotient_moduli)
            self.assertEqual(
                scalar_moduli,
                tuple(
                    divisor
                    for divisor in quotient_moduli
                    if divisor != DEFAULT_INJECTIVE_MODULUS
                ),
            )
            scalar = extract_scalar_features(
                12,
                moduli=scalar_moduli,
                gcd_modulus=abs(family.discriminant),
            )
            gcd_names = [name for name in scalar if name.startswith("gcd_with_")]
            self.assertEqual(
                gcd_names,
                [f"gcd_with_{abs(family.discriminant)}"],
            )

    def test_modulus_one_information_is_exactly_zero(self) -> None:
        representations = _family_representations(D56_FAMILY, 90)
        rows = _support_rows(
            D56_FAMILY,
            representations,
            min_n=1,
            max_n=90,
        )
        report = _quotient_information_report(
            D56_FAMILY,
            _slice_rows(rows, minimum=1, maximum=30),
            _slice_rows(rows, minimum=31, maximum=90),
        )
        by_modulus = {
            int(record["modulus"]): record for record in report["records"]
        }
        modulus_one = by_modulus[1]
        self.assertTrue(report["modulus_one_exact_zero_information"])
        self.assertEqual(
            modulus_one["genus_residue_mutual_information_bits"],
            0.0,
        )
        self.assertEqual(
            modulus_one["class_residue_information_given_genus_bits"],
            0.0,
        )
        self.assertIn(DEFAULT_INJECTIVE_MODULUS, by_modulus)

    def test_task_labels_are_unoriented_and_exclusions_are_explicit(self) -> None:
        d23_representations = _family_representations(D23_FAMILY, 100)
        d23_rows = _support_rows(
            D23_FAMILY,
            d23_representations,
            min_n=1,
            max_n=100,
        )
        d23_samples = _task_samples(
            d23_rows,
            task_id="d23_class_mod_inversion",
        )
        self.assertTrue(d23_samples)
        self.assertLessEqual(
            set(_class_counts(d23_samples)),
            {"A", "M|P"},
        )
        self.assertNotIn("P", _class_counts(d23_samples))
        self.assertNotIn("M", _class_counts(d23_samples))

        d56_representations = _family_representations(D56_FAMILY, 100)
        d56_rows = _support_rows(
            D56_FAMILY,
            d56_representations,
            min_n=1,
            max_n=100,
        )
        d56_genus = _task_samples(d56_rows, task_id="d56_genus")
        d56_class = _task_samples(
            d56_rows,
            task_id="d56_within_genus_class",
        )
        self.assertTrue(d56_genus)
        self.assertTrue(d56_class)
        self.assertLessEqual(
            set(_class_counts(d56_genus)),
            {"genus_0", "genus_1"},
        )
        self.assertLessEqual(set(_class_counts(d56_class)), {"A", "C"})

        crafted_rows = [
            {
                "value": 1,
                "coprime_to_discriminant": True,
                "primitive_class_support_count": 1,
                "single_genus_target": "genus_0",
                "single_inversion_orbit_target": "A",
                "genus_indices": [0],
                "inversion_orbit_support": ["A"],
            },
            {
                "value": 2,
                "coprime_to_discriminant": False,
                "primitive_class_support_count": 1,
                "single_genus_target": "genus_0",
                "single_inversion_orbit_target": "A",
                "genus_indices": [0],
                "inversion_orbit_support": ["A"],
            },
            {
                "value": 3,
                "coprime_to_discriminant": True,
                "primitive_class_support_count": 0,
                "single_genus_target": None,
                "single_inversion_orbit_target": None,
                "genus_indices": [],
                "inversion_orbit_support": [],
            },
            {
                "value": 5,
                "coprime_to_discriminant": True,
                "primitive_class_support_count": 2,
                "single_genus_target": "genus_0",
                "single_inversion_orbit_target": None,
                "genus_indices": [0],
                "inversion_orbit_support": ["A", "C"],
            },
            {
                "value": 11,
                "coprime_to_discriminant": True,
                "primitive_class_support_count": 2,
                "single_genus_target": None,
                "single_inversion_orbit_target": None,
                "genus_indices": [0, 1],
                "inversion_orbit_support": ["A", "M|P"],
            },
        ]
        crafted_genus = _task_samples(crafted_rows, task_id="d56_genus")
        crafted_class = _task_samples(
            crafted_rows,
            task_id="d56_within_genus_class",
        )
        self.assertEqual([sample["value"] for sample in crafted_genus], [1, 5])
        self.assertEqual([sample["value"] for sample in crafted_class], [1])
        exclusions = _task_exclusion_report(crafted_rows, crafted_genus)
        self.assertEqual(exclusions["range_value_count"], 5)
        self.assertEqual(exclusions["coprime_primitive_base_count"], 3)
        self.assertEqual(exclusions["included_single_target_count"], 2)
        self.assertEqual(exclusions["excluded_from_single_target_count"], 1)
        self.assertEqual(exclusions["multiple_class_support_count"], 2)
        self.assertEqual(exclusions["multiple_genus_support_count"], 1)
        self.assertEqual(
            exclusions["multiple_inversion_orbit_support_count"],
            2,
        )

    def test_holm_adjustment_is_monotone_and_tie_deterministic(self) -> None:
        adjusted = _holm_adjust({"z_task": 0.02, "a_task": 0.01, "b_task": 0.02})
        self.assertEqual(adjusted["a_task"]["rank"], 1)
        self.assertEqual(adjusted["b_task"]["rank"], 2)
        self.assertEqual(adjusted["z_task"]["rank"], 3)
        self.assertAlmostEqual(
            adjusted["a_task"]["holm_adjusted_p_value"],
            0.03,
        )
        self.assertAlmostEqual(
            adjusted["b_task"]["holm_adjusted_p_value"],
            0.04,
        )
        self.assertAlmostEqual(
            adjusted["z_task"]["holm_adjusted_p_value"],
            0.04,
        )
        ordered = [
            adjusted[task]["holm_adjusted_p_value"]
            for task in ("a_task", "b_task", "z_task")
        ]
        self.assertEqual(ordered, sorted(ordered))
        self.assertEqual(_holm_adjust({}), {})
        with self.assertRaises(ValueError):
            _holm_adjust({"bad": -0.01})
        with self.assertRaises(ValueError):
            _holm_adjust({"bad": float("nan")})

    def test_matching_strata_are_form_free_and_mobility_is_effective(self) -> None:
        samples = [
            {"value": 8, "target": "A", "primitive_class_support_count": 1},
            {"value": 9, "target": "A", "primitive_class_support_count": 9},
            {"value": 10, "target": "B", "primitive_class_support_count": 2},
        ]
        features = {
            8: self._feature_row(8, incoming=2, outgoing=1, marker=1),
            9: self._feature_row(9, incoming=2, outgoing=1, marker=1),
            10: self._feature_row(10, incoming=2, outgoing=1, marker=2),
        }
        self.assertEqual(_matched_strata(samples, features), ((3, 2),) * 3)
        mobility = _effective_mobility(samples, features)
        self.assertEqual(mobility["potential_cross_label_row_fraction"], 1.0)
        self.assertEqual(
            mobility["potential_cross_label_graph_changing_row_fraction"],
            1.0,
        )
        self.assertAlmostEqual(
            mobility["expected_cross_label_transfer_fraction"],
            4.0 / 9.0,
        )
        self.assertAlmostEqual(
            mobility["expected_cross_label_graph_changing_transfer_fraction"],
            4.0 / 9.0,
        )

        duplicate_features = dict(features)
        duplicate_features[10] = self._feature_row(
            10,
            incoming=2,
            outgoing=1,
            marker=1,
        )
        duplicate = _effective_mobility(samples, duplicate_features)
        self.assertEqual(
            duplicate["expected_cross_label_graph_changing_transfer_fraction"],
            0.0,
        )

    def test_operation_shuffle_preserves_frozen_margins(self) -> None:
        width = len(graph_feature_names())
        indices = _operation_bucket_indices()
        rows = [[0.0] * width for _ in range(3)]
        for offset, index in enumerate(indices["incoming"]):
            rows[0][index] = float(offset)
            rows[1][index] = float(4 - offset)
        for offset, index in enumerate(indices["outgoing"]):
            rows[1][index] = float(offset + 1)
            rows[2][index] = float(5 - offset)
        before_directional_totals = {
            direction: [sum(row[index] for index in bucket_indices) for row in rows]
            for direction, bucket_indices in indices.items()
        }
        before_bucket_totals = {
            direction: [sum(row[index] for row in rows) for index in bucket_indices]
            for direction, bucket_indices in indices.items()
        }
        shuffled = _shuffle_operation_buckets(rows, random.Random(7))
        for direction, bucket_indices in indices.items():
            self.assertEqual(
                [sum(row[index] for index in bucket_indices) for row in shuffled],
                before_directional_totals[direction],
            )
            self.assertEqual(
                [sum(row[index] for row in shuffled) for index in bucket_indices],
                before_bucket_totals[direction],
            )
        untouched = set(range(width)) - {
            index for bucket_indices in indices.values() for index in bucket_indices
        }
        self.assertTrue(
            all(shuffled[row][index] == rows[row][index]
                for row in range(len(rows)) for index in untouched)
        )

    def test_analysis_manifest_audit_closes_local_source_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "analysis_manifest.json"
            manifest = {
                "experiment_id": EXPERIMENT_ID,
                "python_version": "3.12.13",
                "analysis_cli_args": FROZEN_ANALYSIS_CLI_ARGS,
                "source_sha256": {
                    path.as_posix(): file_sha256(current_source_path(path))
                    for path in FROZEN_ANALYSIS_SOURCE_PATHS
                },
            }
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True),
                encoding="utf-8",
            )
            # Exercise the frozen experiment's contract independently of the
            # interpreter running this test suite. The production guard stays
            # strict: this does not authorize a different reproduction runtime.
            with patch("moo.quadratic_form_nested_probe.sys.version_info", (3, 12, 13)):
                audit = _analysis_manifest_audit(manifest_path)
            self.assertTrue(audit["passes"])
            self.assertTrue(all(audit["checks"].values()))
            self.assertIn("moo_graph_invariants.py", manifest["source_sha256"])
            self.assertIn("rational_baselines.py", manifest["source_sha256"])

            manifest["python_version"] = "3.13.0"
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True),
                encoding="utf-8",
            )
            with patch("moo.quadratic_form_nested_probe.sys.version_info", (3, 12, 13)):
                wrong_manifest = _analysis_manifest_audit(manifest_path)
            self.assertFalse(wrong_manifest["passes"])
            self.assertFalse(wrong_manifest["checks"]["analysis_python_is_3_12_13"])
            self.assertTrue(wrong_manifest["checks"]["current_analysis_runtime_is_3_12_13"])

            manifest["python_version"] = "3.12.13"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with patch("moo.quadratic_form_nested_probe.sys.version_info", (3, 14, 4)):
                wrong_runtime = _analysis_manifest_audit(manifest_path)
            self.assertFalse(wrong_runtime["passes"])
            self.assertTrue(wrong_runtime["checks"]["analysis_python_is_3_12_13"])
            self.assertFalse(wrong_runtime["checks"]["current_analysis_runtime_is_3_12_13"])
            self.assertTrue(wrong_runtime["checks"]["source_hashes_match"])

    @staticmethod
    def _operation_null_fixture():
        scalar_names = (
            "phase",
            "phase_parity",
            "phase_squared",
            "phase_mod_three",
            "constant",
        )
        graph_names = graph_feature_names()

        def feature_row(value, label_index, phase):
            phase_toggle = phase % 2
            incoming_patterns = (
                (5 + phase_toggle, 1, 0, 0, 1),
                (0, 1, 5 + phase_toggle, 0, 1),
                (1, 0, 0, 5 + phase_toggle, 1),
            )
            outgoing_patterns = (
                (4 + phase_toggle, 0, 1, 0, 0),
                (0, 1, 4 + phase_toggle, 0, 0),
                (0, 0, 1, 4 + phase_toggle, 0),
            )
            incoming = incoming_patterns[label_index]
            outgoing = outgoing_patterns[label_index]
            graph = {name: 0.0 for name in graph_names}
            graph["confirmation_lag"] = float(phase % 3)
            graph["incoming_edge_count"] = float(sum(incoming))
            graph["outgoing_edge_count"] = float(sum(outgoing))
            graph["incoming_distinct_operand_count"] = float(phase + 1)
            graph["outgoing_distinct_result_count"] = float((phase % 3) + 1)
            for direction, counts in (
                ("incoming", incoming),
                ("outgoing", outgoing),
            ):
                for operation, count in zip(
                    ("add", "subtract", "multiply", "divide", "other"),
                    counts,
                ):
                    graph[f"{direction}_op_{operation}_count"] = float(count)
            return NodeFeatureRow(
                value=value,
                cutoff_stage=value + 50,
                moduli=(),
                prime_exponent_max_value=None,
                scalar_names=scalar_names,
                scalar_values=(
                    float(phase),
                    float(phase_toggle),
                    float(phase * phase),
                    float(phase % 3),
                    1.0,
                ),
                graph_names=graph_names,
                graph_values=tuple(graph[name] for name in graph_names),
            )

        labels = ("A", "B", "C")
        training_samples = []
        test_samples = []
        training_features = {}
        test_features = {}
        for phase in range(4):
            for label_index, label in enumerate(labels):
                value = 1 + (phase * len(labels)) + label_index
                training_samples.append({"value": value, "target": label})
                training_features[value] = feature_row(
                    value, label_index, phase
                )
        for phase in range(3):
            for label_index, label in enumerate(labels):
                value = 101 + (phase * len(labels)) + label_index
                test_samples.append({"value": value, "target": label})
                test_features[value] = feature_row(value, label_index, phase)
        return (
            training_samples,
            test_samples,
            training_features,
            test_features,
        )

    def test_operation_null_is_bit_exact_with_naive_combined_refits(self) -> None:
        fixture = self._operation_null_fixture()
        arguments = {
            "permutation_count": 43,
            "seed": 1729,
        }
        expected = _naive_operation_histogram_null(*fixture, **arguments)
        actual = _operation_histogram_null(*fixture, **arguments)
        self.assertEqual(actual, expected)
        self.assertEqual(actual["null_lift_summary"]["count"], 43)
        self.assertLess(
            actual["null_lift_summary"]["minimum"],
            actual["null_lift_summary"]["maximum"],
        )

    def test_operation_null_refits_only_graph_block_per_shuffle(self) -> None:
        fixture = self._operation_null_fixture()
        permutation_count = 7
        with patch(
            "moo.quadratic_form_nested_probe.fit_nearest_centroid",
            wraps=fit_nearest_centroid,
        ) as fit_spy:
            _operation_histogram_null(
                *fixture,
                permutation_count=permutation_count,
                seed=2718,
            )
        scalar_width = len(next(iter(fixture[2].values())).scalar_names)
        graph_width = len(graph_feature_names())
        fitted_widths = [
            len(call.args[0][0]) for call in fit_spy.call_args_list
        ]
        self.assertEqual(
            fitted_widths,
            [scalar_width, scalar_width + graph_width]
            + [graph_width] * permutation_count,
        )


class NestedQuadraticFormSyntheticCorpusTests(unittest.TestCase):
    development_max_n = 30
    intermediate_holdout_max_n = 50
    holdout_max_n = 90
    permutation_count = 3
    operation_null_count = 3

    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        root = Path(cls._temporary_directory.name)
        cls.development_path = root / "nested_development.sqlite"
        cls.holdout_path = root / "nested_holdout.sqlite"
        build_strict_stage_graph(
            db_path=cls.development_path,
            max_stage=cls.holdout_max_n + 50,
            max_abs_p=500,
            max_abs_q=200,
            max_abs_value=500.0,
            max_edges=None,
            time_limit_seconds=None,
            commit_every=25,
            retain_confirmed_edges=True,
            verbose=False,
        )
        shutil.copyfile(cls.development_path, cls.holdout_path)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def test_exact_prefix_feature_parity_on_identical_strict_prefixes(self) -> None:
        with closing(connect_readonly(self.development_path)) as development, closing(
            connect_readonly(self.holdout_path)
        ) as holdout:
            parity = _prefix_feature_parity(
                development,
                holdout,
                max_n=self.development_max_n,
            )
        self.assertTrue(parity["exact_prefix_feature_parity"])
        self.assertEqual(parity["mismatch_count"], 0)
        self.assertEqual(parity["values_compared"], self.development_max_n)
        self.assertEqual(parity["cutoff_rule"], "inclusive value+50")

    def _run_probe(self) -> dict[str, object]:
        return nested_quadratic_form_probe(
            development_db_path=self.development_path,
            holdout_db_path=self.holdout_path,
            development_max_n=self.development_max_n,
            intermediate_holdout_max_n=self.intermediate_holdout_max_n,
            holdout_max_n=self.holdout_max_n,
            edge_limit=4,
            composition_event_limit=5,
            permutation_count=self.permutation_count,
            operation_null_count=self.operation_null_count,
            enforce_preregistered_inputs=False,
        )

    def test_small_end_to_end_report_is_deterministic_and_read_only(self) -> None:
        before = {
            "development": file_sha256(self.development_path),
            "holdout": file_sha256(self.holdout_path),
        }
        first = self._run_probe()
        middle = {
            "development": file_sha256(self.development_path),
            "holdout": file_sha256(self.holdout_path),
        }
        second = self._run_probe()
        after = {
            "development": file_sha256(self.development_path),
            "holdout": file_sha256(self.holdout_path),
        }
        self.assertEqual(before, middle)
        self.assertEqual(before, after)
        self.assertEqual(
            json.dumps(first, sort_keys=True, separators=(",", ":")),
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

        self.assertEqual(first["schema_version"], SCHEMA_VERSION)
        self.assertEqual(
            first["report_type"],
            "gauss_nested_class_genus_ablation",
        )
        self.assertEqual(set(first["families"]), {"-56", "-23", "-20"})
        self.assertFalse(first["config"]["enforce_preregistered_inputs"])
        self.assertEqual(first["config"]["permutation_count"], 3)
        self.assertEqual(first["config"]["operation_null_count"], 3)
        self.assertTrue(
            first["corpora"]["prefix_feature_parity"][
                "exact_prefix_feature_parity"
            ]
        )
        self.assertTrue(
            first["corpora"]["database_hash_invariance"][
                "development_unchanged"
            ]
        )
        self.assertTrue(
            first["corpora"]["database_hash_invariance"][
                "holdout_unchanged"
            ]
        )
        self.assertTrue(first["summary"]["all_exact_family_calibrations_pass"])
        self.assertTrue(first["summary"]["prefix_feature_parity_passes"])
        self.assertTrue(first["summary"]["feature_provenance_passes"])
        self.assertTrue(first["summary"]["database_hashes_unchanged"])
        self.assertTrue(
            first["summary"]["modulus_one_is_exact_maximal_erasure"]
        )
        self.assertFalse(
            first["recovery"]["quotient_modulus_809_used_as_model_feature"]
        )

        for discriminant, integrity in first["feature_integrity"].items():
            with self.subTest(discriminant=discriminant):
                self.assertNotIn(
                    DEFAULT_INJECTIVE_MODULUS,
                    integrity["scalar_moduli"],
                )
                self.assertIn(
                    DEFAULT_INJECTIVE_MODULUS,
                    integrity["quotient_moduli"],
                )
                self.assertEqual(integrity["node_count"], self.holdout_max_n)

        modulus_one = first["modulus_one_projection"]
        self.assertEqual(modulus_one["carrier_cardinality"], 1)
        self.assertEqual(modulus_one["sole_residue"], 0)
        self.assertTrue(modulus_one["all_endpoint_information_checks_exactly_zero"])
        for family in modulus_one["families"].values():
            self.assertEqual(family["bare_occupied_residues"], [0])
            self.assertEqual(
                family["genus_residue_mutual_information_bits"],
                0.0,
            )
            self.assertEqual(
                family["class_residue_information_given_genus_bits"],
                0.0,
            )

        for family in first["families"].values():
            self.assertTrue(all(family["exact_calibration_checks"].values()))
            ledger = family["bounded_composition_ledger"]
            self.assertEqual(ledger["event_limit"], 5)
            self.assertEqual(ledger["reported_event_count"], 5)
            self.assertTrue(ledger["events_truncated"])
            self.assertTrue(ledger["all_events_verified_exactly"])
        for shadow in first["graph_audit"][
            "composition_scalar_shadows"
        ].values():
            self.assertTrue(shadow["all_scalar_shadows_usable"])

        final_checkpoint = "values_31_to_90"
        d56_genus = first["recovery"]["tasks"]["d56_genus"][
            "checkpoints"
        ][final_checkpoint]
        self.assertEqual(d56_genus["status"], "scored")
        self.assertEqual(
            d56_genus["matched_graph_block_permutation"]["permutation_count"],
            self.permutation_count,
        )
        self.assertEqual(
            d56_genus["operation_histogram_null"]["permutation_count"],
            self.operation_null_count,
        )


if __name__ == "__main__":
    unittest.main()
