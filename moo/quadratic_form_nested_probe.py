from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import random
import shlex
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from moo.paths import PROJECT_ROOT
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from moo.quadratic_form_nested_math import (
    D20_FAMILY,
    D23_FAMILY,
    D56_FAMILY,
    QuadraticFamilySpec,
    bounded_composition_ledger,
    class_table_report,
    derive_genus_cosets,
    genus_character_audit_d56,
    inverse_reflection_report,
    local_residue_distribution,
    proper_pm_i_orbit_table,
    quotient_ladder_report,
    symbolic_identity_report,
)
from moo.quadratic_form_probe import (
    ScalarGraphInspector,
    enumerate_representations,
    reduced_primitive_forms,
)
from moo.quadratic_form_recovery import (
    NodeFeatureRow,
    collision_ceiling_report,
    conditional_mutual_information,
    extract_graph_features,
    extract_node_features,
    fit_nearest_centroid,
    graph_feature_names,
    macro_balanced_accuracy,
    mutual_information,
    paired_graph_block_permutation_test,
    positive_divisors,
    predict_nearest_centroid,
)
from moo.research_utils import (
    connect_readonly,
    file_sha256,
    require_strict_alignment,
)


EXPERIMENT_ID = "gauss_nested_class_genus_ablation_u850_v1"
SCHEMA_VERSION = "moo_quadratic_form_nested_probe.v1"
DEFAULT_DEVELOPMENT_MAX_N = 200
DEFAULT_HOLDOUT_MAX_N = 800
DEFAULT_INTERMEDIATE_HOLDOUT_MAX_N = 400
DEFAULT_INJECTIVE_MODULUS = 809
DEFAULT_COMPOSITION_EVENT_LIMIT = 1_000
DEFAULT_PERMUTATION_COUNT = 10_000
DEFAULT_OPERATION_NULL_COUNT = 1_000
DEFAULT_EDGE_LIMIT = 8
MIN_CLASS_COUNT = 4
PRIME_EXPONENT_MAX_VALUE = 800
FAMILIES = (D20_FAMILY, D23_FAMILY, D56_FAMILY)
FROZEN_DEVELOPMENT_SHA256 = (
    "3D23228EA2A1926918D49BBDC89D9F7BF85ECFE4729EC96C7BD6E9F97E54B097"
)
FROZEN_GENERATOR_SHA256 = {
    "strict_stage_moo.py": (
        "E91574E0DF7C573EC6E36D56DFBE5C779DA632108D631EC22B4D2196ACFC099B"
    ),
    "moo_graph_corpus.py": (
        "5F863DC297B3B2136FA76835D13067AE41206A150885DD37BA2BB49DA5532C1F"
    ),
}
FROZEN_HOLDOUT_CONFIG = {
    "generator": "strict_stage_moo_graph",
    "max_abs_p": 1_000_000_000,
    "max_abs_q": 850,
    "max_abs_value": 1_000_000_000,
    "max_stage": 850,
    "retain_confirmed_edges": True,
}
DEFAULT_HOLDOUT_SUMMARY_PATH = Path(
    "research/experiments/gauss/strict_stage_u850_holdout_v1.summary.json"
)
DEFAULT_GENERATION_MANIFEST_PATH = Path(
    "research/experiments/gauss/strict_stage_u850_holdout_v1.provenance.json"
)
DEFAULT_ANALYSIS_MANIFEST_PATH = Path(
    "research/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.analysis_manifest.json"
)
DEFAULT_REPORT_PATH = Path(
    "out/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.json"
)
FROZEN_GENERATION_ARGV = [
    "strict_stage_moo.py",
    "--db",
    "out/experiments/gauss/strict_stage_u850_holdout_v1.sqlite",
    "--max-stage",
    "850",
    "--max-abs-p",
    "1000000000",
    "--max-abs-q",
    "850",
    "--max-abs-value",
    "1000000000",
    "--commit-every",
    "25",
    "--summary",
    "out/experiments/gauss/strict_stage_u850_holdout_v1.summary.json",
    "--quiet",
]
FROZEN_ANALYSIS_CLI_ARGS = [
    "--write",
    str(DEFAULT_REPORT_PATH).replace("\\", "/"),
    "--pretty",
    "--quiet",
    "--with-checksums",
]
FROZEN_ANALYSIS_SOURCE_PATHS = (
    Path("out/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.pre.md"),
    Path("moo_quadratic_form_nested_probe.py"),
    Path("moo_quadratic_form_recovery.py"),
    Path("moo_quadratic_form_nested_math.py"),
    Path("moo_quadratic_form_probe.py"),
    Path("moo_research_utils.py"),
    Path("moo_graph_invariants.py"),
    Path("rational_baselines.py"),
)

# Historical manifest keys remain unchanged. These are locations of the
# current files to compare against those original hashes, not replacements
# certified as the frozen analysis sources.
_CURRENT_SOURCE_LOCATIONS = {'strict_stage_moo.py': 'moo/strict_stage_moo.py',
 'moo_graph_corpus.py': 'moo/graph_corpus.py',
 'moo_quadratic_form_nested_probe.py': 'moo/quadratic_form_nested_probe.py',
 'moo_quadratic_form_recovery.py': 'moo/quadratic_form_recovery.py',
 'moo_quadratic_form_nested_math.py': 'moo/quadratic_form_nested_math.py',
 'moo_quadratic_form_probe.py': 'moo/quadratic_form_probe.py',
 'moo_research_utils.py': 'moo/research_utils.py',
 'moo_graph_invariants.py': 'moo/graph_invariants.py',
 'rational_baselines.py': 'moo/rational_baselines.py',
 'out/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.pre.md': 'research/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.pre.md'}


def current_source_path(historical_path: Path | str) -> Path:
    name = Path(historical_path).as_posix()
    return PROJECT_ROOT / _CURRENT_SOURCE_LOCATIONS.get(name, name)


BANNED_GRAPH_TOKENS = (
    "form",
    "class",
    "genus",
    "witness",
    "orbit",
    "coefficient",
    "coordinate",
)

RepresentationTable = Dict[int, Tuple[Tuple[int, int], ...]]
FeatureMap = Dict[int, NodeFeatureRow]


def _experiment_seed(suffix: str) -> int:
    digest = hashlib.sha256(f"{EXPERIMENT_ID}:{suffix}".encode("ascii")).digest()
    return int.from_bytes(digest[:8], "big")


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return str(row[0]) if row is not None else None


def _corpus_payload(
    path: Path,
    conn: sqlite3.Connection,
    *,
    alignment: Mapping[str, object],
) -> Dict[str, object]:
    config_raw = _meta_value(conn, "config_json")
    try:
        config: object = json.loads(config_raw) if config_raw is not None else None
    except json.JSONDecodeError:
        config = config_raw
    latest = conn.execute(
        "SELECT * FROM stages ORDER BY stage DESC LIMIT 1"
    ).fetchone()
    return {
        "path": str(Path(path)),
        "sha256": file_sha256(Path(path)),
        "schema_version": _meta_value(conn, "schema_version"),
        "config": config,
        "latest_stage": dict(latest) if latest is not None else None,
        "node_count": int(
            conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        ),
        "edge_count": int(
            conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        ),
        "alignment": dict(alignment),
    }


def _primitive_pair(pair: Tuple[int, int]) -> bool:
    return math.gcd(abs(int(pair[0])), abs(int(pair[1]))) == 1


def _family_representations(
    spec: QuadraticFamilySpec,
    max_n: int,
) -> Dict[str, RepresentationTable]:
    return {
        form.form_id: enumerate_representations(form, int(max_n))
        for form in spec.forms
    }


def _inversion_orbits(spec: QuadraticFamilySpec) -> Dict[str, str]:
    by_exponent = spec.form_id_by_exponent
    exponent_by_id = spec.exponent_by_form_id
    labels = {form.form_id: form.class_label for form in spec.forms}
    result: Dict[str, str] = {}
    for form in spec.forms:
        exponent = exponent_by_id[form.form_id]
        inverse_id = by_exponent[(-exponent) % spec.cyclic_order]
        members = sorted({labels[form.form_id], labels[inverse_id]})
        result[form.form_id] = "|".join(members)
    return result


def _support_rows(
    spec: QuadraticFamilySpec,
    representations: Mapping[str, RepresentationTable],
    *,
    min_n: int,
    max_n: int,
) -> List[Dict[str, object]]:
    genus = derive_genus_cosets(spec)
    class_to_genus = genus["class_to_genus_index"]
    inversion_orbit = _inversion_orbits(spec)
    rows: List[Dict[str, object]] = []
    for value in range(int(min_n), int(max_n) + 1):
        primitive_ids = tuple(
            form.form_id
            for form in spec.forms
            if any(
                _primitive_pair(pair)
                for pair in representations[form.form_id][value]
            )
        )
        genera = tuple(
            sorted({int(class_to_genus[form_id]) for form_id in primitive_ids})
        )
        inversion_support = tuple(
            sorted({inversion_orbit[form_id] for form_id in primitive_ids})
        )
        rows.append(
            {
                "value": value,
                "coprime_to_discriminant": (
                    math.gcd(value, abs(spec.discriminant)) == 1
                ),
                "primitive_class_ids": list(primitive_ids),
                "primitive_class_support_count": len(primitive_ids),
                "genus_indices": list(genera),
                "single_genus_target": (
                    f"genus_{genera[0]}" if len(genera) == 1 else None
                ),
                "inversion_orbit_support": list(inversion_support),
                "single_inversion_orbit_target": (
                    inversion_support[0] if len(inversion_support) == 1 else None
                ),
            }
        )
    return rows


def _representation_report(
    spec: QuadraticFamilySpec,
    representations: Mapping[str, RepresentationTable],
    *,
    max_n: int,
) -> Dict[str, object]:
    form_reports = []
    for form in spec.forms:
        table = representations[form.form_id]
        orbits = proper_pm_i_orbit_table(form, table)
        represented_values = [
            value for value in range(1, max_n + 1) if table[value]
        ]
        primitive_values = [
            value
            for value in represented_values
            if any(_primitive_pair(pair) for pair in table[value])
        ]
        coefficients = [len(orbits[value]) for value in range(1, max_n + 1)]
        primitive_coefficients = [
            sum(_primitive_pair(pair) for pair in orbits[value])
            for value in range(1, max_n + 1)
        ]
        form_reports.append(
            {
                "form": form.payload(),
                "raw_witness_count": sum(len(table[n]) for n in table),
                "proper_orbit_count": sum(len(orbits[n]) for n in orbits),
                "represented_value_count": len(represented_values),
                "primitive_represented_value_count": len(primitive_values),
                "represented_values": represented_values,
                "proper_orbit_coefficient_prefix": coefficients,
                "primitive_proper_orbit_coefficient_prefix": (
                    primitive_coefficients
                ),
                "proper_automorphism_group": ["+I", "-I"],
                "proper_automorphism_group_order": 2,
            }
        )
    return {
        "bound": int(max_n),
        "enumeration_method": (
            "complete exact completed-square bounds from 4aQ=(2ax+by)^2+|D|y^2"
        ),
        "standard_reduced_primitive_forms": [
            list(coefficients)
            for coefficients in reduced_primitive_forms(spec.discriminant)
        ],
        "configured_forms_match_enumeration": (
            set(reduced_primitive_forms(spec.discriminant))
            == {(form.a, form.b, form.c) for form in spec.forms}
        ),
        "forms": form_reports,
    }


def _family_moduli(spec: QuadraticFamilySpec) -> Tuple[int, ...]:
    return tuple(
        sorted(
            set(positive_divisors(abs(spec.discriminant)))
            | {DEFAULT_INJECTIVE_MODULUS}
        )
    )


def _scalar_baseline_moduli(spec: QuadraticFamilySpec) -> Tuple[int, ...]:
    return positive_divisors(abs(spec.discriminant))


def _extract_feature_map(
    conn: sqlite3.Connection,
    values: Iterable[int],
    *,
    moduli: Sequence[int],
    gcd_modulus: int,
) -> FeatureMap:
    return {
        int(value): extract_node_features(
            conn,
            int(value),
            moduli=moduli,
            prime_exponent_max_value=PRIME_EXPONENT_MAX_VALUE,
            gcd_modulus=gcd_modulus,
        )
        for value in sorted(set(int(item) for item in values))
    }


def _prefix_feature_parity(
    development_conn: sqlite3.Connection,
    holdout_conn: sqlite3.Connection,
    *,
    max_n: int,
) -> Dict[str, object]:
    mismatches = []
    for value in range(1, int(max_n) + 1):
        development = extract_graph_features(development_conn, value)
        holdout = extract_graph_features(holdout_conn, value)
        if development != holdout:
            mismatches.append(
                {
                    "value": value,
                    "development": development,
                    "holdout": holdout,
                }
            )
    return {
        "values_compared": int(max_n),
        "cutoff_rule": "inclusive value+50",
        "mismatch_count": len(mismatches),
        "mismatches": mismatches[:10],
        "mismatches_truncated": len(mismatches) > 10,
        "exact_prefix_feature_parity": not mismatches,
    }


def _task_samples(
    rows: Sequence[Mapping[str, object]],
    *,
    task_id: str,
) -> List[Dict[str, object]]:
    samples: List[Dict[str, object]] = []
    for row in rows:
        if not bool(row["coprime_to_discriminant"]):
            continue
        value = int(row["value"])
        support_count = int(row["primitive_class_support_count"])
        if support_count < 1:
            continue
        target: Optional[str]
        if task_id == "d56_genus":
            target = (
                str(row["single_genus_target"])
                if row["single_genus_target"] is not None
                else None
            )
        elif task_id == "d56_within_genus_class":
            candidate = row["single_inversion_orbit_target"]
            target = str(candidate) if candidate in {"A", "C"} else None
        elif task_id == "d23_class_mod_inversion":
            candidate = row["single_inversion_orbit_target"]
            target = str(candidate) if candidate in {"A", "M|P"} else None
        elif task_id == "d20_class_genus_calibration":
            candidate = row["single_inversion_orbit_target"]
            target = str(candidate) if candidate is not None else None
        else:
            raise ValueError(f"unknown recovery task: {task_id}")
        if target is None:
            continue
        samples.append(
            {
                "value": value,
                "target": target,
                "primitive_class_support_count": support_count,
            }
        )
    return samples


def _class_counts(samples: Sequence[Mapping[str, object]]) -> Dict[str, int]:
    return dict(
        sorted(Counter(str(sample["target"]) for sample in samples).items())
    )


def _matrix_for_samples(
    samples: Sequence[Mapping[str, object]],
    features: Mapping[int, NodeFeatureRow],
    feature_set: str,
) -> Tuple[Tuple[str, ...], Tuple[Tuple[float, ...], ...], Tuple[str, ...]]:
    if not samples:
        raise ValueError("a scored task must contain at least one sample")
    first = features[int(samples[0]["value"])]
    names = first.names(feature_set)
    rows = []
    labels = []
    for sample in samples:
        row = features[int(sample["value"])]
        if row.names(feature_set) != names:
            raise AssertionError("feature schema drift inside one recovery task")
        rows.append(row.vector(feature_set))
        labels.append(str(sample["target"]))
    return names, tuple(rows), tuple(labels)


def _score_model(
    training_samples: Sequence[Mapping[str, object]],
    test_samples: Sequence[Mapping[str, object]],
    training_features: Mapping[int, NodeFeatureRow],
    test_features: Mapping[int, NodeFeatureRow],
    *,
    feature_set: str,
) -> Dict[str, object]:
    names, train_rows, train_labels = _matrix_for_samples(
        training_samples, training_features, feature_set
    )
    test_names, test_rows, test_labels = _matrix_for_samples(
        test_samples, test_features, feature_set
    )
    if names != test_names:
        raise AssertionError("development and holdout feature schemas differ")
    labels = tuple(sorted(set(train_labels) | set(test_labels)))
    model = fit_nearest_centroid(
        train_rows,
        train_labels,
        feature_names=names,
        class_labels=labels,
    )
    predictions = predict_nearest_centroid(model, test_rows)
    score = macro_balanced_accuracy(test_labels, predictions, labels=labels)
    return {
        "feature_set": feature_set,
        "feature_count": len(names),
        "feature_names": list(names),
        "balanced_accuracy": score,
        "training_class_counts": _class_counts(training_samples),
        "test_class_counts": _class_counts(test_samples),
        "prediction_count": len(predictions),
        "predictions": [
            {
                "value": int(sample["value"]),
                "truth": truth,
                "prediction": prediction,
            }
            for sample, truth, prediction in zip(
                test_samples, test_labels, predictions
            )
        ],
        "model": model.payload(),
    }


def _matched_strata(
    samples: Sequence[Mapping[str, object]],
    features: Mapping[int, NodeFeatureRow],
) -> Tuple[Tuple[int, int], ...]:
    strata = []
    for sample in samples:
        value = int(sample["value"])
        graph = dict(
            zip(
                features[value].graph_names,
                features[value].graph_values,
            )
        )
        degree = int(
            graph["incoming_edge_count"] + graph["outgoing_edge_count"]
        )
        strata.append(
            (
                value.bit_length() - 1,
                int(math.log2(1 + degree)),
            )
        )
    return tuple(strata)


def _distribution_summary(values: Sequence[float]) -> Dict[str, object]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return {"count": 0}

    def quantile(fraction: float) -> float:
        index = round(fraction * (len(ordered) - 1))
        return ordered[index]

    return {
        "count": len(ordered),
        "minimum": ordered[0],
        "q05": quantile(0.05),
        "median": quantile(0.5),
        "q95": quantile(0.95),
        "maximum": ordered[-1],
        "mean": math.fsum(ordered) / len(ordered),
    }


def _operation_bucket_indices() -> Dict[str, Tuple[int, ...]]:
    names = graph_feature_names()
    return {
        direction: tuple(
            names.index(f"{direction}_op_{operation}_count")
            for operation in ("add", "subtract", "multiply", "divide", "other")
        )
        for direction in ("incoming", "outgoing")
    }


def _shuffle_operation_buckets(
    rows: Sequence[Sequence[float]],
    generator: random.Random,
) -> Tuple[Tuple[float, ...], ...]:
    shuffled = [list(float(value) for value in row) for row in rows]
    indices_by_direction = _operation_bucket_indices()
    for indices in indices_by_direction.values():
        labels: List[int] = []
        row_totals = []
        for row in rows:
            counts = [int(round(float(row[index]))) for index in indices]
            if any(count < 0 for count in counts):
                raise AssertionError("operation counts must be nonnegative")
            row_totals.append(sum(counts))
            for bucket, count in enumerate(counts):
                labels.extend([bucket] * count)
        generator.shuffle(labels)
        cursor = 0
        for output, total in zip(shuffled, row_totals):
            chunk = labels[cursor : cursor + total]
            cursor += total
            counts = Counter(chunk)
            for bucket, index in enumerate(indices):
                output[index] = float(counts.get(bucket, 0))
        if cursor != len(labels):
            raise AssertionError("operation-label repartition lost labels")
    return tuple(tuple(row) for row in shuffled)


def _operation_histogram_null(
    training_samples: Sequence[Mapping[str, object]],
    test_samples: Sequence[Mapping[str, object]],
    training_features: Mapping[int, NodeFeatureRow],
    test_features: Mapping[int, NodeFeatureRow],
    *,
    permutation_count: int,
    seed: int,
) -> Dict[str, object]:
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

    # The scalar block is identical in every destructive-null fit.  Its
    # training means, scales, and class centroids are therefore exactly the
    # scalar prefix of every naively refitted combined model.  Cache the
    # per-coordinate squared-distance terms (rather than their sum) so the
    # later math.fsum still sees scalar terms followed by graph terms in the
    # same order as predict_nearest_centroid on a combined row.
    scalar_distance_terms = []
    for row in test_scalar:
        standardized = tuple(
            (row[column] - scalar_model.training_means[column])
            / scalar_model.training_scales[column]
            for column in range(len(row))
        )
        scalar_distance_terms.append(
            {
                label: tuple(
                    (
                        standardized[column]
                        - scalar_model.centroids[label][column]
                    )
                    ** 2
                    for column in range(len(row))
                )
                for label in scalar_model.labels
            }
        )

    generator = random.Random(int(seed))
    null_lifts = []
    for _ in range(int(permutation_count)):
        shuffled_train_graph = _shuffle_operation_buckets(train_graph, generator)
        shuffled_test_graph = _shuffle_operation_buckets(test_graph, generator)
        graph_model = fit_nearest_centroid(
            shuffled_train_graph,
            train_labels,
            feature_names=graph_names,
            class_labels=labels,
        )
        predictions = []
        for row_index, row in enumerate(shuffled_test_graph):
            standardized = tuple(
                (row[column] - graph_model.training_means[column])
                / graph_model.training_scales[column]
                for column in range(len(row))
            )
            distances = {}
            for label in graph_model.labels:
                graph_terms = tuple(
                    (
                        standardized[column]
                        - graph_model.centroids[label][column]
                    )
                    ** 2
                    for column in range(len(row))
                )
                distances[label] = math.fsum(
                    scalar_distance_terms[row_index][label] + graph_terms
                )
            predictions.append(
                min(
                    graph_model.labels,
                    key=lambda label: (
                        distances[label],
                        -int(graph_model.training_class_counts[label]),
                        label,
                    ),
                )
            )
        score = macro_balanced_accuracy(
            test_labels,
            predictions,
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


def _minimum_count_status(
    training_samples: Sequence[Mapping[str, object]],
    test_samples: Sequence[Mapping[str, object]],
) -> Dict[str, object]:
    training = _class_counts(training_samples)
    test = _class_counts(test_samples)
    labels = sorted(set(training) | set(test))
    sufficient = bool(labels) and all(
        training.get(label, 0) >= MIN_CLASS_COUNT
        and test.get(label, 0) >= MIN_CLASS_COUNT
        for label in labels
    )
    return {
        "minimum_per_class": MIN_CLASS_COUNT,
        "training_class_counts": training,
        "test_class_counts": test,
        "sufficient": sufficient,
    }


def _score_recovery_task(
    task_id: str,
    training_samples: Sequence[Mapping[str, object]],
    test_samples: Sequence[Mapping[str, object]],
    training_features: Mapping[int, NodeFeatureRow],
    test_features: Mapping[int, NodeFeatureRow],
    *,
    primary: bool,
    permutation_count: int,
    operation_null_count: int,
    seed: int,
) -> Dict[str, object]:
    sufficiency = _minimum_count_status(training_samples, test_samples)
    report: Dict[str, object] = {
        "task_id": task_id,
        "primary": bool(primary),
        "sample_sufficiency": sufficiency,
    }
    if not sufficiency["sufficient"]:
        report["status"] = "insufficient_data"
        return report

    scalar = _score_model(
        training_samples,
        test_samples,
        training_features,
        test_features,
        feature_set="scalar",
    )
    graph = _score_model(
        training_samples,
        test_samples,
        training_features,
        test_features,
        feature_set="graph",
    )
    combined = _score_model(
        training_samples,
        test_samples,
        training_features,
        test_features,
        feature_set="combined",
    )
    lift = float(combined["balanced_accuracy"]) - float(
        scalar["balanced_accuracy"]
    )
    report.update(
        {
            "status": "scored",
            "scalar_model": scalar,
            "topology_only_model": graph,
            "scalar_plus_graph_model": combined,
            "observed_graph_lift": lift,
        }
    )
    if not primary:
        report["inference_status"] = "secondary_descriptive_not_promotable"
        return report

    scalar_names, train_scalar, train_labels = _matrix_for_samples(
        training_samples, training_features, "scalar"
    )
    graph_names, train_graph, _ = _matrix_for_samples(
        training_samples, training_features, "graph"
    )
    _, test_scalar, test_labels = _matrix_for_samples(
        test_samples, test_features, "scalar"
    )
    _, test_graph, _ = _matrix_for_samples(
        test_samples, test_features, "graph"
    )
    block = paired_graph_block_permutation_test(
        train_scalar,
        train_graph,
        train_labels,
        _matched_strata(training_samples, training_features),
        test_scalar,
        test_graph,
        test_labels,
        _matched_strata(test_samples, test_features),
        permutation_count=int(permutation_count),
        seed=int(seed),
        scalar_feature_names=scalar_names,
        graph_feature_names=graph_names,
    )
    block_payload = block.payload()
    block_payload.pop("null_graph_lifts", None)
    diagnostic_raw_p_value = float(block_payload.pop("p_value"))
    block_payload["diagnostic_raw_p_value"] = diagnostic_raw_p_value
    block_payload["null_lift_summary"] = _distribution_summary(
        block.null_graph_lifts
    )
    movable = bool(
        block.training_movable_row_fraction >= 0.5
        and block.test_movable_row_fraction >= 0.5
    )
    block_payload["movable_threshold"] = 0.5
    block_payload["movable_threshold_passes"] = movable
    if movable:
        block_payload["p_value"] = diagnostic_raw_p_value
        block_payload["p_value_status"] = "valid_for_frozen_holm_family"
    else:
        block_payload["p_value"] = None
        block_payload["p_value_status"] = "insufficient_movable_rows"
        block_payload["inference_status"] = "insufficient_movable_rows"
    operation_null = _operation_histogram_null(
        training_samples,
        test_samples,
        training_features,
        test_features,
        permutation_count=int(operation_null_count),
        seed=int(seed) ^ 0x5A5A5A5A,
    )
    report["matched_graph_block_permutation"] = block_payload
    report["operation_histogram_null"] = operation_null
    report["inference_status"] = (
        "eligible_for_holm"
        if movable
        else "insufficient_movable_rows"
    )
    return report


def _majority_by_residue(
    training_samples: Sequence[Mapping[str, object]],
    test_samples: Sequence[Mapping[str, object]],
    *,
    modulus: int,
) -> Dict[str, object]:
    m = int(modulus)
    labels = tuple(
        sorted(
            {str(sample["target"]) for sample in training_samples}
            | {str(sample["target"]) for sample in test_samples}
        )
    )
    training_counts = Counter(str(sample["target"]) for sample in training_samples)
    if not labels or any(training_counts[label] == 0 for label in labels):
        return {"status": "insufficient_training_labels", "modulus": m}
    overall_majority = min(
        labels,
        key=lambda label: (-training_counts[label], label),
    )
    bucket_counts: Dict[int, Counter[str]] = {}
    for sample in training_samples:
        residue = int(sample["value"]) % m
        bucket_counts.setdefault(residue, Counter())[str(sample["target"])] += 1
    bucket_prediction = {
        residue: min(
            labels,
            key=lambda label: (-counts[label], label),
        )
        for residue, counts in bucket_counts.items()
    }
    seen_test = sum(
        int(sample["value"]) % m in bucket_prediction
        for sample in test_samples
    )
    if seen_test == 0:
        return {
            "status": "descriptive_unseen_endpoint",
            "modulus": m,
            "training_bucket_count": len(bucket_prediction),
            "seen_test_residue_count": 0,
            "test_sample_count": len(test_samples),
        }
    truth = tuple(str(sample["target"]) for sample in test_samples)
    predictions = tuple(
        bucket_prediction.get(int(sample["value"]) % m, overall_majority)
        for sample in test_samples
    )
    return {
        "status": "scored",
        "modulus": m,
        "training_bucket_count": len(bucket_prediction),
        "seen_test_residue_count": seen_test,
        "test_sample_count": len(test_samples),
        "unseen_fallback": overall_majority,
        "balanced_accuracy": macro_balanced_accuracy(
            truth, predictions, labels=labels
        ),
    }


def _sample_bucket_report(
    samples: Sequence[Mapping[str, object]],
    *,
    modulus: int,
) -> Dict[str, object]:
    m = int(modulus)
    counts = Counter(int(sample["value"]) % m for sample in samples)
    return {
        "sample_count": len(samples),
        "occupied_residues": sorted(counts),
        "occupied_residue_count": len(counts),
        "bucket_sizes": {
            str(residue): int(counts.get(residue, 0))
            for residue in range(m)
        },
    }


def _quotient_information_report(
    spec: QuadraticFamilySpec,
    development_rows: Sequence[Mapping[str, object]],
    holdout_rows: Sequence[Mapping[str, object]],
) -> Dict[str, object]:
    genus_train = _task_samples(
        development_rows,
        task_id=(
            "d56_genus"
            if spec.discriminant == -56
            else "d20_class_genus_calibration"
        ),
    ) if spec.discriminant in {-20, -56} else []
    genus_test = _task_samples(
        holdout_rows,
        task_id=(
            "d56_genus"
            if spec.discriminant == -56
            else "d20_class_genus_calibration"
        ),
    ) if spec.discriminant in {-20, -56} else []
    class_task = {
        -20: "d20_class_genus_calibration",
        -23: "d23_class_mod_inversion",
        -56: "d56_within_genus_class",
    }[spec.discriminant]
    class_train = _task_samples(development_rows, task_id=class_task)
    class_test = _task_samples(holdout_rows, task_id=class_task)
    genus_by_value = {
        int(row["value"]): str(row["single_genus_target"])
        for row in list(development_rows) + list(holdout_rows)
        if row["single_genus_target"] is not None
    }
    records = []
    for modulus in _family_moduli(spec):
        all_genus = list(genus_train) + list(genus_test)
        all_class = list(class_train) + list(class_test)
        genus_mi = (
            mutual_information(
                [sample["target"] for sample in all_genus],
                [int(sample["value"]) % modulus for sample in all_genus],
            )
            if all_genus
            else 0.0
        )
        conditional_rows = [
            sample
            for sample in all_class
            if int(sample["value"]) in genus_by_value
        ]
        conditional_class_mi = (
            conditional_mutual_information(
                [sample["target"] for sample in conditional_rows],
                [int(sample["value"]) % modulus for sample in conditional_rows],
                [genus_by_value[int(sample["value"])] for sample in conditional_rows],
            )
            if conditional_rows
            else 0.0
        )
        record: Dict[str, object] = {
            "modulus": modulus,
            "genus_sample_buckets": _sample_bucket_report(
                all_genus,
                modulus=modulus,
            ),
            "class_sample_buckets": _sample_bucket_report(
                all_class,
                modulus=modulus,
            ),
            "genus_residue_mutual_information_bits": genus_mi,
            "class_residue_information_given_genus_bits": conditional_class_mi,
            "class_majority_by_residue": _majority_by_residue(
                class_train,
                class_test,
                modulus=modulus,
            ),
        }
        if genus_train and genus_test:
            record["genus_majority_by_residue"] = _majority_by_residue(
                genus_train,
                genus_test,
                modulus=modulus,
            )
        records.append(record)
    modulus_one = next(record for record in records if record["modulus"] == 1)
    if float(modulus_one["genus_residue_mutual_information_bits"]) != 0.0:
        raise AssertionError("modulus one retained genus mutual information")
    if float(modulus_one["class_residue_information_given_genus_bits"]) != 0.0:
        raise AssertionError("modulus one retained class mutual information")
    return {
        "family_id": spec.family_id,
        "information_unit": (
            "qualified integer nodes with primitive class-support targets"
        ),
        "genus_information_status": (
            "undefined_single_genus"
            if spec.discriminant == -23
            else "defined"
        ),
        "records": records,
        "modulus_one_exact_zero_information": True,
        "injective_endpoint_is_descriptive": True,
    }


def _local_residue_controls(spec: QuadraticFamilySpec) -> Dict[str, object]:
    distributions = {
        modulus: {
            form.form_id: local_residue_distribution(form, modulus)
            for form in spec.forms
        }
        for modulus in spec.local_moduli
    }
    labels = {form.class_label: form.form_id for form in spec.forms}
    controls: Dict[str, object] = {
        "inverse_form_distributions_equal_at_every_local_modulus": True,
        "failures": [],
    }
    inverse_pairs = []
    by_exponent = spec.form_id_by_exponent
    for form_id, exponent in spec.class_exponents:
        inverse_id = by_exponent[(-exponent) % spec.cyclic_order]
        if form_id < inverse_id:
            inverse_pairs.append((form_id, inverse_id))
    for modulus, by_form in distributions.items():
        for left_id, right_id in inverse_pairs:
            if by_form[left_id] != by_form[right_id]:
                controls["inverse_form_distributions_equal_at_every_local_modulus"] = False
                controls["failures"].append(
                    {
                        "modulus": modulus,
                        "left_form_id": left_id,
                        "right_form_id": right_id,
                    }
                )
    if spec.discriminant == -23:
        by_form = distributions[23]
        controls["all_d23_forms_equal_mod_23"] = (
            len({tuple(sorted(counts.items())) for counts in by_form.values()}) == 1
        )
    if spec.discriminant == -56:
        for modulus in (7, 8, 56):
            by_form = distributions[modulus]
            controls[f"d56_same_genus_distributions_equal_mod_{modulus}"] = bool(
                by_form[labels["A"]] == by_form[labels["C"]]
                and by_form[labels["P"]] == by_form[labels["M"]]
            )
        coprime_supports = {}
        for genus_label, form_ids in {
            "principal_genus": (labels["A"], labels["C"]),
            "other_genus": (labels["P"], labels["M"]),
        }.items():
            coprime_supports[genus_label] = sorted(
                residue
                for residue in range(56)
                if math.gcd(residue, 56) == 1
                and any(distributions[56][form_id][residue] for form_id in form_ids)
            )
        controls["d56_coprime_genus_supports_mod_56"] = coprime_supports
        controls["d56_coprime_genus_supports_disjoint"] = not (
            set(coprime_supports["principal_genus"])
            & set(coprime_supports["other_genus"])
        )
    return controls


def _inverse_collision_report(
    spec: QuadraticFamilySpec,
    representations: Mapping[str, RepresentationTable],
    features: Mapping[int, NodeFeatureRow],
) -> Dict[str, object]:
    by_exponent = spec.form_id_by_exponent
    forms = spec.forms_by_id
    records = []
    visited = set()
    for form_id, exponent in spec.class_exponents:
        inverse_id = by_exponent[(-exponent) % spec.cyclic_order]
        pair_key = tuple(sorted((form_id, inverse_id)))
        if form_id == inverse_id or pair_key in visited:
            continue
        visited.add(pair_key)
        common_values = [
            value
            for value in sorted(features)
            if representations[form_id][value]
            and representations[inverse_id][value]
        ]
        signatures = []
        labels = []
        for value in common_values:
            signature = (
                features[value].scalar_values + features[value].graph_values
            )
            signatures.extend((signature, signature))
            labels.extend((forms[form_id].class_label, forms[inverse_id].class_label))
        collision = (
            collision_ceiling_report(signatures, labels)
            if signatures
            else None
        )
        if collision is not None and collision[
            "macro_balanced_accuracy_ceiling_exact"
        ] != "1/2":
            raise AssertionError("an inverse-pair collision ceiling is not 1/2")
        records.append(
            {
                "left_form_id": form_id,
                "right_form_id": inverse_id,
                "common_scalar_value_count": len(common_values),
                "common_scalar_values": common_values,
                "node_feature_source": (
                    "the identical integer node is duplicated only for the exact "
                    "non-identifiability audit"
                ),
                "observable_block": "frozen scalar plus graph features",
                "exact_collision_ceiling": collision,
                "oriented_node_only_recovery_allowed": False,
            }
        )
    return {
        "family_id": spec.family_id,
        "inverse_pair_count": len(records),
        "pairs": records,
        "falsifier": (
            "any scalar-node claim above the exact collision ceiling is leakage"
        ),
    }


def _parse_multiplication_relation(relation_id: str) -> Tuple[int, int, int]:
    parts = str(relation_id).split(":")
    if len(parts) != 4 or parts[0] != "multiply":
        raise ValueError(f"invalid multiplication relation ID: {relation_id}")
    return int(parts[1]), int(parts[2]), int(parts[3])


def _composition_graph_shadow_audit(
    inspector: ScalarGraphInspector,
    composition_ledger: Mapping[str, object],
) -> Dict[str, object]:
    failures = []
    directed_edge_ids = set()
    minimum_stages = []
    relation_ids = [str(item) for item in composition_ledger["scalar_relation_ids"]]
    for relation_id in relation_ids:
        left, right, result = _parse_multiplication_relation(relation_id)
        evidence = inspector.relation(left, "*", right, result)
        usable = bool(evidence["present"]) and bool(
            evidence["operand_confirmation_at_edge_passes"]
        )
        if not usable:
            failures.append(
                {
                    "relation_id": relation_id,
                    "present": evidence["present"],
                    "operand_confirmation_at_edge_passes": evidence[
                        "operand_confirmation_at_edge_passes"
                    ],
                }
            )
        directed_edge_ids.update(int(edge_id) for edge_id in evidence["directed_edge_ids"])
        if evidence["minimum_evidence_stage"] is not None:
            minimum_stages.append(int(evidence["minimum_evidence_stage"]))
    return {
        "family_id": composition_ledger["family_id"],
        "graph_stage_cutoff": inspector.stage_cutoff,
        "distinct_scalar_multiplication_relation_count": len(relation_ids),
        "usable_relation_count": len(relation_ids) - len(failures),
        "unusable_relation_count": len(failures),
        "first_unusable_relations": failures[:10],
        "distinct_directed_edge_id_count": len(directed_edge_ids),
        "maximum_first_evidence_stage": max(minimum_stages) if minimum_stages else None,
        "all_scalar_shadows_usable": not failures,
        "interpretation": (
            "strict positive-spine scalar multiplication coverage is a saturation "
            "calibration and not graph-native Gauss composition"
        ),
        "graph_native_composition_prediction_performed": False,
    }


def _support_accounting(
    rows: Sequence[Mapping[str, object]],
) -> Dict[str, object]:
    primitive_rows = [
        row for row in rows if int(row["primitive_class_support_count"]) > 0
    ]
    qualified = [
        row for row in primitive_rows if bool(row["coprime_to_discriminant"])
    ]
    return {
        "value_count": len(rows),
        "primitive_represented_value_count": len(primitive_rows),
        "coprime_primitive_value_count": len(qualified),
        "unrepresented_or_imprimitive_only_count": len(rows) - len(primitive_rows),
        "multiple_proper_class_support_count": sum(
            int(row["primitive_class_support_count"]) > 1 for row in qualified
        ),
        "multiple_genus_support_count": sum(
            len(row["genus_indices"]) > 1 for row in qualified
        ),
        "multiple_inversion_orbit_support_count": sum(
            len(row["inversion_orbit_support"]) > 1 for row in qualified
        ),
        "single_genus_target_count": sum(
            row["single_genus_target"] is not None for row in qualified
        ),
        "single_inversion_orbit_target_count": sum(
            row["single_inversion_orbit_target"] is not None
            for row in qualified
        ),
    }


def _character_phase_table(spec: QuadraticFamilySpec) -> Dict[str, object]:
    records = []
    for form in spec.forms:
        exponent = int(spec.exponent_by_form_id[form.form_id])
        angle = 2.0 * math.pi * exponent / spec.cyclic_order
        records.append(
            {
                "form_id": form.form_id,
                "class_label": form.class_label,
                "class_exponent": exponent,
                "formal_phase": f"zeta_{spec.cyclic_order}^{exponent}",
                "complex_phase_approximation": [math.cos(angle), math.sin(angle)],
                "modulus_one_residue": 0,
            }
        )
    return {
        "status": "external_auxiliary_class_labels_only",
        "cyclic_order": spec.cyclic_order,
        "records": records,
        "interpreted_as_additional_residues_in_z_mod_1z": False,
    }


def _family_exact_report(
    spec: QuadraticFamilySpec,
    representations: Mapping[str, RepresentationTable],
    support_rows: Sequence[Mapping[str, object]],
    *,
    development_max_n: int,
    holdout_max_n: int,
    composition_event_limit: int,
) -> Dict[str, object]:
    development_rows = [
        row for row in support_rows if int(row["value"]) <= development_max_n
    ]
    holdout_rows = [
        row for row in support_rows if int(row["value"]) > development_max_n
    ]
    table = class_table_report(spec)
    genus = derive_genus_cosets(spec)
    inverse = inverse_reflection_report(spec, max_n=holdout_max_n)
    symbolic = symbolic_identity_report(spec)
    composition = bounded_composition_ledger(
        spec,
        max_n=holdout_max_n,
        event_limit=composition_event_limit,
    )
    representation = _representation_report(
        spec,
        representations,
        max_n=holdout_max_n,
    )
    quotient = quotient_ladder_report(
        spec,
        max_n=holdout_max_n,
        moduli=_family_moduli(spec),
    )
    local_controls = _local_residue_controls(spec)
    information = _quotient_information_report(
        spec,
        development_rows,
        holdout_rows,
    )
    exact_checks = {
        "configured_forms_match_reduced_enumeration": representation[
            "configured_forms_match_enumeration"
        ],
        "independent_class_table_matches": table[
            "matches_expected_cyclic_table"
        ],
        "inverse_reflection_controls_exact": inverse[
            "all_inverse_reflection_controls_exact"
        ],
        "symbolic_bilinear_identities_exact": symbolic[
            "all_symbolic_identities_hold"
        ],
        "bounded_composition_events_exact": composition[
            "all_events_verified_exactly"
        ],
        "modulus_one_is_singleton": quotient["modulus_one_is_singleton"],
        "inverse_local_distributions_equal": local_controls[
            "inverse_form_distributions_equal_at_every_local_modulus"
        ],
        "modulus_one_information_is_zero": information[
            "modulus_one_exact_zero_information"
        ],
    }
    if not all(bool(value) for value in exact_checks.values()):
        failed = [key for key, value in exact_checks.items() if not value]
        raise AssertionError(
            f"exact family calibration failed for {spec.family_id}: {failed}"
        )
    report: Dict[str, object] = {
        "family_id": spec.family_id,
        "discriminant": spec.discriminant,
        "forms": [form.payload() for form in spec.forms],
        "class_group_model": f"C{spec.cyclic_order}",
        "class_table": table,
        "derived_genus_cosets": genus,
        "inverse_reflection": inverse,
        "symbolic_composition_identities": symbolic,
        "bounded_composition_ledger": composition,
        "representations": representation,
        "support_accounting": {
            "development_checkpoint_N100": {
                "requested_bound": 100,
                "effective_bound": min(100, development_max_n),
                "complete": development_max_n >= 100,
                "accounting": _support_accounting(
                    [
                        row
                        for row in development_rows
                        if int(row["value"]) <= 100
                    ]
                ),
            },
            "development_checkpoint_N200": {
                "requested_bound": 200,
                "effective_bound": min(200, development_max_n),
                "complete": development_max_n >= 200,
                "accounting": _support_accounting(
                    [
                        row
                        for row in development_rows
                        if int(row["value"]) <= 200
                    ]
                ),
            },
            "development": _support_accounting(development_rows),
            "holdout": _support_accounting(holdout_rows),
            "all_values": _support_accounting(support_rows),
        },
        "support_rows": list(support_rows),
        "local_residue_controls": local_controls,
        "external_quotient_ladder": quotient,
        "predictive_quotient_information": information,
        "character_phases": _character_phase_table(spec),
        "exact_calibration_checks": exact_checks,
    }
    if spec.discriminant == -56:
        report["genus_character_audit"] = genus_character_audit_d56(
            max_n=holdout_max_n
        )
        if not report["genus_character_audit"][
            "all_coprime_values_match_derived_genus"
        ]:
            raise AssertionError("D=-56 genus character calibration failed")
    return report


def _database_label_absence(conn: sqlite3.Connection) -> Dict[str, object]:
    tables = [
        str(row[0])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
    ]
    columns = []
    for table in tables:
        for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall():
            columns.append(f"{table}.{row[1]}")
    hits = [
        column
        for column in columns
        if any(token in column.lower() for token in BANNED_GRAPH_TOKENS)
    ]
    return {
        "tables": tables,
        "column_count": len(columns),
        "banned_tokens": list(BANNED_GRAPH_TOKENS),
        "banned_column_name_hits": hits,
        "passes": not hits,
        "scope": (
            "schema names and the fixed extractor interface; external form "
            "tables are never joined to the graph corpus"
        ),
    }


def _feature_provenance_audit(
    features_by_family: Mapping[int, Mapping[int, NodeFeatureRow]],
    database_audit: Mapping[str, object],
) -> Dict[str, object]:
    signature = inspect.signature(extract_graph_features)
    argument_names = list(signature.parameters)
    first_family = next(iter(features_by_family.values()))
    first_row = first_family[min(first_family)]
    graph_names = list(first_row.graph_names)
    banned_name_hits = [
        name
        for name in graph_names
        if any(token in name.lower() for token in BANNED_GRAPH_TOKENS)
    ]
    cross_family_mismatches = []
    family_items = list(features_by_family.items())
    reference_discriminant, reference = family_items[0]
    for discriminant, feature_map in family_items[1:]:
        for value in sorted(set(reference) & set(feature_map)):
            if reference[value].graph_values != feature_map[value].graph_values:
                cross_family_mismatches.append(
                    {
                        "value": value,
                        "reference_discriminant": reference_discriminant,
                        "other_discriminant": discriminant,
                    }
                )
    extractor_passes = argument_names == ["conn", "value"]
    provenance_checks = {
        "extractor_interface_is_integer_only": extractor_passes,
        "graph_feature_names_are_label_free": not banned_name_hits,
        "graph_vectors_are_cross_family_invariant": not cross_family_mismatches,
        "database_schema_is_label_free": bool(database_audit["passes"]),
    }
    passes = bool(
        all(provenance_checks.values())
    )
    return {
        "graph_extractor_arguments": argument_names,
        "graph_extractor_accepts_only_connection_and_integer_value": (
            extractor_passes
        ),
        "graph_feature_names": graph_names,
        "banned_graph_feature_name_hits": banned_name_hits,
        "cross_family_graph_vector_mismatch_count": len(
            cross_family_mismatches
        ),
        "first_cross_family_mismatches": cross_family_mismatches[:10],
        "database_schema_label_absence": dict(database_audit),
        "provenance_checks": provenance_checks,
        "form_conditioned_edge_selection_detected": not passes,
        "form_conditioned_edge_selection_performed": (
            False if passes else None
        ),
        "passes": passes,
    }


def _target_coefficient_sentinel(
    spec: QuadraticFamilySpec,
    samples: Sequence[Mapping[str, object]],
    *,
    task_id: str,
) -> Dict[str, object]:
    forms_by_label = {form.class_label: form for form in spec.forms}
    genus = derive_genus_cosets(spec)
    forms_by_id = spec.forms_by_id
    signature_by_target: Dict[str, Tuple[int, int, int]] = {}
    for target in sorted({str(sample["target"]) for sample in samples}):
        if task_id == "d56_genus":
            genus_index = int(target.removeprefix("genus_"))
            form = forms_by_id[genus["cosets"][genus_index][0]]
        elif task_id == "d23_class_mod_inversion":
            form = forms_by_label["A" if target == "A" else "P"]
        else:
            form = forms_by_label[target]
        signature_by_target[target] = (form.a, form.b, form.c)
    signature_to_targets: Dict[Tuple[int, int, int], List[str]] = {}
    for target, signature_value in signature_by_target.items():
        signature_to_targets.setdefault(signature_value, []).append(target)
    unique = all(len(targets) == 1 for targets in signature_to_targets.values())
    return {
        "level": "A1_deliberate_leakage_sentinel",
        "task_id": task_id,
        "sample_count": len(samples),
        "feature": "externally target-selected reduced-form coefficients (a,b,c)",
        "signature_by_target": {
            target: list(value)
            for target, value in signature_by_target.items()
        },
        "target_signatures_are_unique": unique,
        "balanced_accuracy": 1.0 if samples and unique else None,
        "uses_banned_external_information": True,
        "included_in_any_a2_or_a3_model": False,
        "interpretation": (
            "a positive plumbing sentinel only; it demonstrates how retaining "
            "coefficients can carry the externally supplied answer"
        ),
    }


def _slice_rows(
    rows: Sequence[Mapping[str, object]],
    *,
    minimum: int,
    maximum: int,
) -> List[Mapping[str, object]]:
    return [
        row
        for row in rows
        if int(minimum) <= int(row["value"]) <= int(maximum)
    ]


def _task_exclusion_report(
    rows: Sequence[Mapping[str, object]],
    samples: Sequence[Mapping[str, object]],
) -> Dict[str, object]:
    eligible_base = [
        row
        for row in rows
        if bool(row["coprime_to_discriminant"])
        and int(row["primitive_class_support_count"]) > 0
    ]
    return {
        "range_value_count": len(rows),
        "coprime_primitive_base_count": len(eligible_base),
        "included_single_target_count": len(samples),
        "excluded_from_single_target_count": len(eligible_base) - len(samples),
        "multiple_class_support_count": sum(
            int(row["primitive_class_support_count"]) > 1
            for row in eligible_base
        ),
        "multiple_genus_support_count": sum(
            len(row["genus_indices"]) > 1 for row in eligible_base
        ),
        "multiple_inversion_orbit_support_count": sum(
            len(row["inversion_orbit_support"]) > 1
            for row in eligible_base
        ),
    }


def _holm_adjust(
    p_values: Mapping[str, float],
    *,
    alpha: float = 0.01,
) -> Dict[str, Dict[str, object]]:
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("Holm alpha must lie strictly between zero and one")
    for task_id, p_value in p_values.items():
        if not math.isfinite(float(p_value)) or not 0.0 <= float(p_value) <= 1.0:
            raise ValueError(f"invalid p-value for {task_id}: {p_value}")
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    count = len(ordered)
    running = 0.0
    stopped = False
    adjusted: Dict[str, Dict[str, object]] = {}
    for rank, (task_id, p_value) in enumerate(ordered, start=1):
        raw_adjusted = min(1.0, (count - rank + 1) * float(p_value))
        running = max(running, raw_adjusted)
        critical_value = float(alpha) / (count - rank + 1)
        rejected = not stopped and float(p_value) <= critical_value
        if not rejected:
            stopped = True
        adjusted[task_id] = {
            "raw_p_value": float(p_value),
            "rank": rank,
            "family_size": count,
            "holm_adjusted_p_value": min(1.0, running),
            "alpha": float(alpha),
            "rank_critical_value": critical_value,
            "rejected": rejected,
            "step_down_stopped_at_or_before_this_rank": stopped,
        }
    return adjusted


def _operation_null_interpretation(report: Mapping[str, object]) -> str:
    del report
    return (
        "destructive descriptive ablation with no preregistered decision "
        "threshold; it cannot support a graph-native composition claim"
    )


def _effective_mobility(
    samples: Sequence[Mapping[str, object]],
    features: Mapping[int, NodeFeatureRow],
) -> Dict[str, object]:
    strata = _matched_strata(samples, features)
    labels_by_stratum: Dict[Tuple[int, int], set[str]] = {}
    rows_by_stratum: Dict[
        Tuple[int, int],
        List[Tuple[str, Tuple[float, ...]]],
    ] = {}
    counts = Counter(strata)
    for sample, stratum in zip(samples, strata):
        label = str(sample["target"])
        graph = features[int(sample["value"])].graph_values
        labels_by_stratum.setdefault(stratum, set()).add(label)
        rows_by_stratum.setdefault(stratum, []).append((label, graph))
    nonsingleton_rows = sum(count for count in counts.values() if count > 1)
    potential_cross_label_rows = sum(
        counts[stratum]
        for stratum, labels in labels_by_stratum.items()
        if len(labels) > 1
    )
    potential_graph_changing_rows = sum(
        any(
            right_label != left_label and right_graph != left_graph
            for right_label, right_graph in rows
        )
        for rows in rows_by_stratum.values()
        for left_label, left_graph in rows
    )
    expected_cross_label_transfer = 0.0
    expected_graph_changing_transfer = 0.0
    for rows in rows_by_stratum.values():
        size = len(rows)
        label_counts = Counter(label for label, _ in rows)
        expected_cross_label_transfer += size - math.fsum(
            count * count / size for count in label_counts.values()
        )
        expected_graph_changing_transfer += sum(
            left_label != right_label and left_graph != right_graph
            for left_label, left_graph in rows
            for right_label, right_graph in rows
        ) / size
    row_count = len(samples)
    return {
        "row_count": row_count,
        "stratum_count": len(counts),
        "nonsingleton_stratum_count": sum(
            count > 1 for count in counts.values()
        ),
        "cross_label_stratum_count": sum(
            len(labels) > 1 for labels in labels_by_stratum.values()
        ),
        "nonsingleton_row_fraction": (
            nonsingleton_rows / row_count if row_count else 0.0
        ),
        "potential_cross_label_row_fraction": (
            potential_cross_label_rows / row_count if row_count else 0.0
        ),
        "potential_cross_label_graph_changing_row_fraction": (
            potential_graph_changing_rows / row_count if row_count else 0.0
        ),
        "expected_cross_label_transfer_fraction": (
            expected_cross_label_transfer / row_count if row_count else 0.0
        ),
        "expected_cross_label_graph_changing_transfer_fraction": (
            expected_graph_changing_transfer / row_count if row_count else 0.0
        ),
    }


def _decorate_primary_checkpoint(
    report: Dict[str, object],
    training_samples: Sequence[Mapping[str, object]],
    test_samples: Sequence[Mapping[str, object]],
    training_features: Mapping[int, NodeFeatureRow],
    test_features: Mapping[int, NodeFeatureRow],
) -> None:
    report["effective_mobility"] = {
        "development": _effective_mobility(
            training_samples,
            training_features,
        ),
        "holdout": _effective_mobility(test_samples, test_features),
        "matching_key": [
            "floor(log2(n))",
            "floor(log2(1+incoming+outgoing))",
        ],
    }
    if report.get("status") != "scored":
        return
    operation_null = report["operation_histogram_null"]
    operation_null["interpretation"] = _operation_null_interpretation(
        operation_null
    )
    operation_null["decision_threshold"] = None
    operation_null["vetoes_graph_increment_promotion"] = False
    operation_null["permits_composition_signal_claim"] = False
    mobility = report["effective_mobility"]
    effective_estimable = bool(
        mobility["development"][
            "expected_cross_label_graph_changing_transfer_fraction"
        ]
        > 0.0
        and mobility["holdout"][
            "expected_cross_label_graph_changing_transfer_fraction"
        ]
        > 0.0
    )
    mobility["association_null_is_estimable"] = effective_estimable
    if not effective_estimable:
        report["inference_status"] = "association_null_not_estimable"
        permutation = report["matched_graph_block_permutation"]
        if permutation.get("p_value") is not None:
            permutation["diagnostic_raw_p_value"] = permutation["p_value"]
        permutation["p_value"] = None
        permutation["p_value_status"] = "association_null_not_estimable"


def _form_target_for_task(
    spec: QuadraticFamilySpec,
    form_id: str,
    *,
    task_id: str,
) -> Optional[str]:
    form = spec.forms_by_id[form_id]
    if task_id == "d56_genus":
        genus = derive_genus_cosets(spec)
        return f"genus_{genus['class_to_genus_index'][form_id]}"
    if task_id == "d56_within_genus_class":
        return form.class_label if form.class_label in {"A", "C"} else None
    if task_id == "d23_class_mod_inversion":
        return "A" if form.class_label == "A" else "M|P"
    if task_id == "d20_class_genus_calibration":
        return form.class_label
    raise ValueError(f"unknown recovery task: {task_id}")


def _task_identifiability_audit(
    spec: QuadraticFamilySpec,
    *,
    task_id: str,
    inverse_collision_report: Mapping[str, object],
) -> Dict[str, object]:
    by_exponent = spec.form_id_by_exponent
    records = []
    invariant = True
    for form_id, exponent in spec.class_exponents:
        inverse_id = by_exponent[(-exponent) % spec.cyclic_order]
        target = _form_target_for_task(spec, form_id, task_id=task_id)
        inverse_target = _form_target_for_task(
            spec,
            inverse_id,
            task_id=task_id,
        )
        pair_invariant = target is None or target == inverse_target
        invariant = invariant and pair_invariant
        records.append(
            {
                "form_id": form_id,
                "inverse_form_id": inverse_id,
                "task_target": target,
                "inverse_task_target": inverse_target,
                "target_is_inversion_invariant": pair_invariant,
            }
        )
    ceiling_records = []
    ceilings_exact = True
    for pair in inverse_collision_report["pairs"]:
        ceiling = pair["exact_collision_ceiling"]
        exact_half = bool(
            ceiling is not None
            and ceiling["macro_balanced_accuracy_ceiling_exact"] == "1/2"
        )
        ceilings_exact = ceilings_exact and exact_half
        ceiling_records.append(
            {
                "left_form_id": pair["left_form_id"],
                "right_form_id": pair["right_form_id"],
                "exact_half_ceiling": exact_half,
            }
        )
    return {
        "task_id": task_id,
        "form_targets": records,
        "target_is_invariant_under_every_inverse_pair": invariant,
        "oriented_inverse_class_prediction_performed": False,
        "nontrivial_inverse_collision_ceilings_exact": ceilings_exact,
        "inverse_collision_ceiling_records": ceiling_records,
        "exact_identifiability_ceiling_conflict": not invariant,
        "passes": invariant and ceilings_exact,
    }


def _recovery_suite(
    rows_by_discriminant: Mapping[int, Sequence[Mapping[str, object]]],
    features_by_discriminant: Mapping[int, Mapping[int, NodeFeatureRow]],
    inverse_collisions: Mapping[int, Mapping[str, object]],
    *,
    development_max_n: int,
    intermediate_holdout_max_n: int,
    holdout_max_n: int,
    permutation_count: int,
    operation_null_count: int,
    feature_audit_passes: bool,
) -> Dict[str, object]:
    task_specs = (
        ("d56_genus", D56_FAMILY, True),
        ("d56_within_genus_class", D56_FAMILY, True),
        ("d23_class_mod_inversion", D23_FAMILY, False),
        ("d20_class_genus_calibration", D20_FAMILY, False),
    )
    tasks: Dict[str, object] = {}
    for task_id, spec, primary in task_specs:
        identifiability = _task_identifiability_audit(
            spec,
            task_id=task_id,
            inverse_collision_report=inverse_collisions[spec.discriminant],
        )
        all_rows = rows_by_discriminant[spec.discriminant]
        development_rows = _slice_rows(
            all_rows,
            minimum=1,
            maximum=development_max_n,
        )
        intermediate_rows = _slice_rows(
            all_rows,
            minimum=development_max_n + 1,
            maximum=intermediate_holdout_max_n,
        )
        final_rows = _slice_rows(
            all_rows,
            minimum=development_max_n + 1,
            maximum=holdout_max_n,
        )
        training_samples = _task_samples(development_rows, task_id=task_id)
        intermediate_samples = _task_samples(
            intermediate_rows,
            task_id=task_id,
        )
        final_samples = _task_samples(final_rows, task_id=task_id)
        features = features_by_discriminant[spec.discriminant]
        developmental_checkpoints = {}
        for requested_bound in (100, 200):
            checkpoint_rows = _slice_rows(
                development_rows,
                minimum=1,
                maximum=min(requested_bound, development_max_n),
            )
            checkpoint_samples = _task_samples(
                checkpoint_rows,
                task_id=task_id,
            )
            developmental_checkpoints[f"N{requested_bound}"] = {
                "requested_bound": requested_bound,
                "effective_bound": min(requested_bound, development_max_n),
                "complete": development_max_n >= requested_bound,
                "prediction_status": "descriptive_no_heldout_score",
                "class_counts": _class_counts(checkpoint_samples),
                "target_exclusions": _task_exclusion_report(
                    checkpoint_rows,
                    checkpoint_samples,
                ),
            }
        checkpoints = {}
        for checkpoint_id, test_rows, test_samples in (
            (
                f"values_{development_max_n + 1}_to_"
                f"{intermediate_holdout_max_n}",
                intermediate_rows,
                intermediate_samples,
            ),
            (
                f"values_{development_max_n + 1}_to_{holdout_max_n}",
                final_rows,
                final_samples,
            ),
        ):
            checkpoint_seed = _experiment_seed(f"{task_id}:{checkpoint_id}")
            checkpoint = _score_recovery_task(
                task_id,
                training_samples,
                test_samples,
                features,
                features,
                primary=primary,
                permutation_count=permutation_count,
                operation_null_count=operation_null_count,
                seed=checkpoint_seed,
            )
            checkpoint["range"] = {
                "training": [1, development_max_n],
                "test": [
                    development_max_n + 1,
                    max(int(row["value"]) for row in test_rows),
                ],
            }
            checkpoint["target_exclusions"] = {
                "development": _task_exclusion_report(
                    development_rows,
                    training_samples,
                ),
                "test": _task_exclusion_report(test_rows, test_samples),
            }
            if primary:
                _decorate_primary_checkpoint(
                    checkpoint,
                    training_samples,
                    test_samples,
                    features,
                    features,
                )
            checkpoints[checkpoint_id] = checkpoint
        tasks[task_id] = {
            "task_id": task_id,
            "discriminant": spec.discriminant,
            "primary": primary,
            "identifiability_audit": identifiability,
            "target_definition": {
                "d56_genus": "derived genus {A,C} versus {P,M}",
                "d56_within_genus_class": "A versus C modulo inversion",
                "d23_class_mod_inversion": "A versus {P,M}",
                "d20_class_genus_calibration": (
                    "principal versus nonprincipal; class equals genus"
                ),
            }[task_id],
            "developmental_checkpoints": developmental_checkpoints,
            "checkpoints": checkpoints,
            "a1_leakage_sentinel": _target_coefficient_sentinel(
                spec,
                final_samples,
                task_id=task_id,
            ),
        }

    final_checkpoint_id = (
        f"values_{development_max_n + 1}_to_{holdout_max_n}"
    )
    intermediate_checkpoint_id = (
        f"values_{development_max_n + 1}_to_"
        f"{intermediate_holdout_max_n}"
    )
    primary_ids = ("d56_genus", "d56_within_genus_class")
    holm_inputs = {}
    primary_eligibility = {}
    for task_id in primary_ids:
        final = tasks[task_id]["checkpoints"][final_checkpoint_id]
        eligible = final.get("inference_status") == "eligible_for_holm"
        primary_eligibility[task_id] = {
            "eligible": eligible,
            "ineligible_primary_assigned_p_one": not eligible,
        }
        if eligible:
            holm_inputs[task_id] = float(
                final["matched_graph_block_permutation"]["p_value"]
            )
        else:
            holm_inputs[task_id] = 1.0
    holm = _holm_adjust(holm_inputs, alpha=0.01)
    promotions = {}
    for task_id in primary_ids:
        intermediate = tasks[task_id]["checkpoints"][
            intermediate_checkpoint_id
        ]
        final = tasks[task_id]["checkpoints"][final_checkpoint_id]
        holm_record = holm.get(task_id)
        checks = {
            "final_lift_at_least_0_05": bool(
                final.get("status") == "scored"
                and float(final["observed_graph_lift"]) >= 0.05
            ),
            "holm_adjusted_p_at_most_0_01": bool(
                holm_record is not None
                and float(holm_record["holm_adjusted_p_value"]) <= 0.01
            ),
            "positive_intermediate_lift": bool(
                intermediate.get("status") == "scored"
                and float(intermediate["observed_graph_lift"]) > 0.0
            ),
            "positive_final_lift": bool(
                final.get("status") == "scored"
                and float(final["observed_graph_lift"]) > 0.0
            ),
            "no_banned_feature_or_form_conditioning": bool(
                feature_audit_passes
            ),
            "nominal_movable_fraction_passes": bool(
                final.get("status") == "scored"
                and final.get("matched_graph_block_permutation", {}).get(
                    "movable_threshold_passes",
                    False,
                )
            ),
            "association_null_is_estimable": bool(
                final.get("effective_mobility", {}).get(
                    "association_null_is_estimable",
                    False,
                )
            ),
            "no_exact_identifiability_ceiling_conflict": bool(
                tasks[task_id]["identifiability_audit"]["passes"]
            ),
        }
        promoted = all(checks.values())
        promotions[task_id] = {
            "checks": checks,
            "promoted": promoted,
            "holm": holm_record,
            "operation_histogram_control": (
                final.get("operation_histogram_null", {}).get(
                    "interpretation"
                )
            ),
            "composition_signal_claim_allowed": False,
        }
    return {
        "classifier": (
            "training z-score followed by nearest class centroid in Euclidean "
            "distance; ties use training majority then lexical label"
        ),
        "metric": "macro_balanced_accuracy",
        "matched_graph_block_null": {
            "matching_key": [
                "floor(log2(n))",
                "floor(log2(1+incoming+outgoing))",
            ],
            "external_form_or_class_support_used_in_matching": False,
            "interpretation": (
                "coarse exposure-matched sensitivity null; deterministic graph "
                "features of n do not provide literal row exchangeability"
            ),
        },
        "scalar_baseline_note": (
            "complete prime exponent vector through 800, factor counts, one "
            "gcd with |D|, and one-hot residues only for positive divisors of D"
        ),
        "quotient_modulus_809_used_as_model_feature": False,
        "tasks": tasks,
        "holm_correction": {
            "implemented_composition_recovery_tests": 0,
            "frozen_primary_family_size": len(primary_ids),
            "eligible_primary_test_count": sum(
                record["eligible"] for record in primary_eligibility.values()
            ),
            "ineligible_primary_rule": (
                "assign p=1 and retain the frozen two-test family"
            ),
            "eligibility": primary_eligibility,
            "records": holm,
        },
        "promotion": promotions,
        "any_graph_conditioned_effect_promoted": any(
            record["promoted"] for record in promotions.values()
        ),
        "graph_native_composition_prediction_performed": False,
    }


def _analysis_manifest_audit(
    analysis_manifest_path: Path,
) -> Dict[str, object]:
    manifest: Optional[Mapping[str, object]] = None
    if analysis_manifest_path.is_file():
        loaded = json.loads(analysis_manifest_path.read_text(encoding="utf-8"))
        if isinstance(loaded, Mapping):
            manifest = loaded
    observed_hashes = {
        path.as_posix(): file_sha256(current_source_path(path))
        for path in FROZEN_ANALYSIS_SOURCE_PATHS
    }
    manifest_hashes = (
        manifest.get("source_sha256") if manifest is not None else None
    )
    checks = {
        "manifest_exists_and_is_object": manifest is not None,
        "experiment_id_matches": bool(
            manifest is not None
            and manifest.get("experiment_id") == EXPERIMENT_ID
        ),
        "analysis_python_is_3_12_13": bool(
            manifest is not None
            and manifest.get("python_version") == "3.12.13"
        ),
        "current_analysis_runtime_is_3_12_13": (
            sys.version_info[:3] == (3, 12, 13)
        ),
        "analysis_cli_args_match": bool(
            manifest is not None
            and manifest.get("analysis_cli_args")
            == FROZEN_ANALYSIS_CLI_ARGS
        ),
        "source_hashes_match": bool(
            isinstance(manifest_hashes, Mapping)
            and all(
                manifest_hashes.get(path) == digest
                for path, digest in observed_hashes.items()
            )
        ),
    }
    return {
        "path": str(analysis_manifest_path),
        "sha256": (
            file_sha256(analysis_manifest_path)
            if analysis_manifest_path.is_file()
            else None
        ),
        "manifest": manifest,
        "observed_source_sha256": observed_hashes,
        "checks": checks,
        "passes": all(checks.values()),
    }


def _preregistered_input_audit(
    development_path: Path,
    holdout_path: Path,
    holdout_summary_path: Path,
    generation_manifest_path: Path,
    analysis_manifest_path: Path,
    development_corpus: Mapping[str, object],
    holdout_corpus: Mapping[str, object],
) -> Dict[str, object]:
    generator_hashes = {
        name: file_sha256(current_source_path(name)).upper()
        for name in FROZEN_GENERATOR_SHA256
    }
    analysis_manifest = _analysis_manifest_audit(analysis_manifest_path)
    holdout_config = holdout_corpus.get("config")
    config_checks = {
        key: bool(
            isinstance(holdout_config, Mapping)
            and holdout_config.get(key) == expected
        )
        for key, expected in FROZEN_HOLDOUT_CONFIG.items()
    }
    latest = holdout_corpus.get("latest_stage")
    latest_stage = (
        int(latest["stage"])
        if isinstance(latest, Mapping) and latest.get("stage") is not None
        else None
    )
    summary_payload: Optional[Mapping[str, object]] = None
    manifest_payload: Optional[Mapping[str, object]] = None
    if holdout_summary_path.is_file():
        loaded_summary = json.loads(
            holdout_summary_path.read_text(encoding="utf-8")
        )
        if isinstance(loaded_summary, Mapping):
            summary_payload = loaded_summary
    if generation_manifest_path.is_file():
        loaded_manifest = json.loads(
            generation_manifest_path.read_text(encoding="utf-8")
        )
        if isinstance(loaded_manifest, Mapping):
            manifest_payload = loaded_manifest
    current_db_hash = str(holdout_corpus["sha256"])
    current_summary_hash = (
        file_sha256(holdout_summary_path)
        if holdout_summary_path.is_file()
        else None
    )
    manifest_generator_hashes = (
        manifest_payload.get("generator_sha256")
        if manifest_payload is not None
        else None
    )
    manifest_checks = {
        "manifest_exists_and_is_object": manifest_payload is not None,
        "experiment_id_matches": bool(
            manifest_payload is not None
            and manifest_payload.get("experiment_id") == EXPERIMENT_ID
        ),
        "generation_python_is_3_12_13": bool(
            manifest_payload is not None
            and manifest_payload.get("python_version") == "3.12.13"
        ),
        "generation_argv_matches": bool(
            manifest_payload is not None
            and manifest_payload.get("argv") == FROZEN_GENERATION_ARGV
        ),
        "manifest_db_hash_matches": bool(
            manifest_payload is not None
            and manifest_payload.get("db_sha256") == current_db_hash
        ),
        "manifest_summary_hash_matches": bool(
            manifest_payload is not None
            and manifest_payload.get("summary_sha256") == current_summary_hash
        ),
        "manifest_generator_hashes_match": bool(
            isinstance(manifest_generator_hashes, Mapping)
            and all(
                str(manifest_generator_hashes.get(name, "")).upper()
                == expected
                for name, expected in FROZEN_GENERATOR_SHA256.items()
            )
        ),
    }
    summary_checks = {
        "summary_exists_and_is_object": summary_payload is not None,
        "requested_max_stage_is_850": bool(
            summary_payload is not None
            and summary_payload.get("requested_max_stage") == 850
        ),
        "final_stage_is_850": bool(
            summary_payload is not None
            and summary_payload.get("final_stage") == 850
        ),
        "summary_config_matches": bool(
            summary_payload is not None
            and summary_payload.get("config") == FROZEN_HOLDOUT_CONFIG
        ),
    }
    checks = {
        "development_hash_matches": (
            str(development_corpus["sha256"]).upper()
            == FROZEN_DEVELOPMENT_SHA256
        ),
        "development_filename_matches": development_path.as_posix().endswith(
            "out/experiments/pascal_edge_probe_u300.sqlite"
        ),
        "holdout_filename_matches": holdout_path.as_posix().endswith(
            "out/experiments/gauss/strict_stage_u850_holdout_v1.sqlite"
        ),
        "holdout_latest_stage_is_850": latest_stage == 850,
        "holdout_config_matches": all(config_checks.values()),
        "generator_hashes_match": all(
            generator_hashes[name] == expected
            for name, expected in FROZEN_GENERATOR_SHA256.items()
        ),
        "summary_provenance_matches": all(summary_checks.values()),
        "generation_manifest_matches": all(manifest_checks.values()),
        "analysis_manifest_matches": analysis_manifest["passes"],
    }
    return {
        "frozen_generation_python_version": "3.12.13",
        "analysis_python_version": ".".join(
            str(item) for item in sys.version_info[:3]
        ),
        "frozen_development_sha256": FROZEN_DEVELOPMENT_SHA256,
        "frozen_generator_sha256": dict(FROZEN_GENERATOR_SHA256),
        "observed_generator_sha256": generator_hashes,
        "frozen_generation_argv": list(FROZEN_GENERATION_ARGV),
        "frozen_holdout_config": dict(FROZEN_HOLDOUT_CONFIG),
        "holdout_config_field_checks": config_checks,
        "holdout_summary_path": str(holdout_summary_path),
        "holdout_summary_sha256": current_summary_hash,
        "summary_checks": summary_checks,
        "generation_manifest_path": str(generation_manifest_path),
        "generation_manifest_sha256": (
            file_sha256(generation_manifest_path)
            if generation_manifest_path.is_file()
            else None
        ),
        "generation_manifest": manifest_payload,
        "generation_manifest_checks": manifest_checks,
        "analysis_manifest": analysis_manifest,
        "checks": checks,
        "passes": all(checks.values()),
    }


def _graph_audit(
    holdout_conn: sqlite3.Connection,
    holdout_corpus: Mapping[str, object],
    family_reports: Mapping[int, Mapping[str, object]],
    features_by_discriminant: Mapping[int, Mapping[int, NodeFeatureRow]],
    *,
    holdout_max_n: int,
    edge_limit: int,
) -> Dict[str, object]:
    latest = holdout_corpus["latest_stage"]
    latest_stage = (
        int(latest["stage"])
        if isinstance(latest, Mapping) and latest.get("stage") is not None
        else None
    )
    inspector = ScalarGraphInspector(
        holdout_conn,
        latest_stage=latest_stage,
        edge_limit=edge_limit,
        stage_cutoff=holdout_max_n + 50,
    )
    database_audit = _database_label_absence(holdout_conn)
    feature_audit = _feature_provenance_audit(
        features_by_discriminant,
        database_audit,
    )
    composition_shadows = {
        str(discriminant): _composition_graph_shadow_audit(
            inspector,
            family_reports[discriminant]["bounded_composition_ledger"],
        )
        for discriminant in sorted(family_reports)
    }
    if not all(
        report["all_scalar_shadows_usable"]
        for report in composition_shadows.values()
    ):
        raise AssertionError("a bounded scalar composition shadow is unusable")
    return {
        "feature_provenance": feature_audit,
        "per_node_exposure_rule": "inclusive stage cutoff n+50",
        "global_composition_shadow_stage_cutoff": inspector.stage_cutoff,
        "composition_scalar_shadows": composition_shadows,
        "scalar_multiplication_edges_used_for_sample_selection": False,
        "graph_native_composition_prediction_performed": False,
        "interpretation": (
            "construction edges are primary graph evidence for node features; "
            "multiplication coverage is only a saturation audit for externally "
            "verified composition"
        ),
    }


def _modulus_one_projection(
    family_reports: Mapping[int, Mapping[str, object]],
    inverse_collisions: Mapping[int, Mapping[str, object]],
) -> Dict[str, object]:
    families = {}
    for discriminant, report in sorted(family_reports.items()):
        predictive_records = report["predictive_quotient_information"][
            "records"
        ]
        predictive = next(
            record for record in predictive_records if record["modulus"] == 1
        )
        external_records = report["external_quotient_ladder"][
            "modulus_records"
        ]
        external = next(
            record for record in external_records if record["modulus"] == 1
        )
        families[str(discriminant)] = {
            "bare_occupied_residues": external["bare_occupied_residues"],
            "bare_occupied_residue_count": external[
                "bare_occupied_residue_count"
            ],
            "genus_residue_mutual_information_bits": predictive[
                "genus_residue_mutual_information_bits"
            ],
            "class_residue_information_given_genus_bits": predictive[
                "class_residue_information_given_genus_bits"
            ],
            "all_form_class_and_genus_labels_project_to_residue": 0,
            "character_phases_project_to_residue": 0,
            "inverse_collision_audit": inverse_collisions[discriminant],
        }
    exact = all(
        item["bare_occupied_residues"] == [0]
        and item["genus_residue_mutual_information_bits"] == 0.0
        and item["class_residue_information_given_genus_bits"] == 0.0
        for item in families.values()
    )
    if not exact:
        raise AssertionError("the modulus-one projection retained information")
    return {
        "carrier": "Z/1Z",
        "carrier_cardinality": 1,
        "sole_residue": 0,
        "deduplicated_bare_quotient_node_count": 1,
        "deduplicated_unlabelled_edge_relation_count": 1,
        "families": families,
        "all_endpoint_information_checks_exactly_zero": exact,
        "retains_form_orientation": False,
        "retains_proper_class": False,
        "retains_genus": False,
        "retains_character_phase": False,
        "retains_composition_provenance": False,
        "interpretation": (
            "modulus one is the maximal-erasure endpoint: every integer, class "
            "phase, and scalar relation lands on the same bare residue"
        ),
    }


def _source_map() -> Dict[str, object]:
    return {
        "gauss_primary_scan": {
            "title": "Disquisitiones Arithmeticae, Section V",
            "latin_scan": "https://www.e-rara.ch/zut/content/structure/1254642",
            "french_translation": (
                "https://fr.wikisource.org/wiki/"
                "Recherches_arithm%C3%A9tiques/Section_cinqui%C3%A8me"
            ),
        },
        "modern_composition_reference": {
            "title": "Binary quadratic forms course notes",
            "url": (
                "https://www.math.ucsd.edu/~apollack/"
                "9_305S_course_notes_binary_quadratic_forms.pdf"
            ),
        },
        "convention": "modern discriminant b^2-4ac",
        "role": (
            "historical and mathematical framing only; every finite table and "
            "identity in this report is independently recomputed"
        ),
    }


def _claim_boundary() -> Dict[str, object]:
    return {
        "can_establish": [
            "exact finite representation fibres through the stated bound",
            "inverse-pair scalar identity under (x,y)->(x,-y)",
            "independently validated reduced-form class tables",
            "held-out scalar and graph-conditioned correlations",
            "exact erasure at the singleton modulus-one endpoint",
        ],
        "cannot_establish": [
            "that the MoO runtime natively contains quadratic forms or class groups",
            "that any scalar multiplication edge is a form-composition witness",
            "that Z/1Z contains hidden class, genus, or phase structure",
            "a theorem about class groups, theta series, zeta functions, or zeros",
            "information beyond integer identity in an unrestricted classifier",
        ],
        "positive_lift_semantics": (
            "incremental predictive value in the frozen standardized nearest-"
            "centroid geometry; the prime vector already identifies n exactly"
        ),
        "composition_recovery_status": "not_implemented_in_this_version",
    }


def _validate_probe_config(
    *,
    development_max_n: int,
    intermediate_holdout_max_n: int,
    holdout_max_n: int,
    edge_limit: int,
    composition_event_limit: int,
    permutation_count: int,
    operation_null_count: int,
    enforce_preregistered_inputs: bool,
) -> None:
    if int(development_max_n) < 1:
        raise ValueError("development_max_n must be >= 1")
    if int(intermediate_holdout_max_n) <= int(development_max_n):
        raise ValueError(
            "intermediate_holdout_max_n must exceed development_max_n"
        )
    if int(holdout_max_n) < int(intermediate_holdout_max_n):
        raise ValueError(
            "holdout_max_n must be at least intermediate_holdout_max_n"
        )
    if int(holdout_max_n) > PRIME_EXPONENT_MAX_VALUE:
        raise ValueError(
            f"holdout_max_n>{PRIME_EXPONENT_MAX_VALUE} exceeds the frozen "
            "prime-factor feature vector"
        )
    if int(edge_limit) < 1:
        raise ValueError("edge_limit must be >= 1")
    if int(composition_event_limit) < 0:
        raise ValueError("composition_event_limit must be >= 0")
    if int(permutation_count) < 1:
        raise ValueError("permutation_count must be >= 1")
    if int(operation_null_count) < 1:
        raise ValueError("operation_null_count must be >= 1")
    if enforce_preregistered_inputs and (
        int(development_max_n) != DEFAULT_DEVELOPMENT_MAX_N
        or int(intermediate_holdout_max_n)
        != DEFAULT_INTERMEDIATE_HOLDOUT_MAX_N
        or int(holdout_max_n) != DEFAULT_HOLDOUT_MAX_N
        or int(permutation_count) != DEFAULT_PERMUTATION_COUNT
        or int(operation_null_count) != DEFAULT_OPERATION_NULL_COUNT
    ):
        raise ValueError(
            "preregistered enforcement requires the frozen 1..200 training, "
            "201..400/800 checkpoints, 10,000 matched permutations, and 1,000 "
            "operation-null shuffles"
        )


def _feature_digest(features: Mapping[int, NodeFeatureRow]) -> str:
    digest = hashlib.sha256()
    for value in sorted(features):
        row = features[value]
        payload = {
            "value": value,
            "cutoff_stage": row.cutoff_stage,
            "gcd_modulus": row.gcd_modulus,
            "scalar_names": row.scalar_names,
            "scalar_values": row.scalar_values,
            "graph_names": row.graph_names,
            "graph_values": row.graph_values,
        }
        digest.update(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        )
        digest.update(b"\n")
    return digest.hexdigest()


def nested_quadratic_form_probe(
    *,
    development_db_path: Path,
    holdout_db_path: Path,
    holdout_summary_path: Path = DEFAULT_HOLDOUT_SUMMARY_PATH,
    generation_manifest_path: Path = DEFAULT_GENERATION_MANIFEST_PATH,
    analysis_manifest_path: Path = DEFAULT_ANALYSIS_MANIFEST_PATH,
    development_max_n: int = DEFAULT_DEVELOPMENT_MAX_N,
    intermediate_holdout_max_n: int = DEFAULT_INTERMEDIATE_HOLDOUT_MAX_N,
    holdout_max_n: int = DEFAULT_HOLDOUT_MAX_N,
    edge_limit: int = DEFAULT_EDGE_LIMIT,
    composition_event_limit: int = DEFAULT_COMPOSITION_EVENT_LIMIT,
    permutation_count: int = DEFAULT_PERMUTATION_COUNT,
    operation_null_count: int = DEFAULT_OPERATION_NULL_COUNT,
    enforce_preregistered_inputs: bool = True,
) -> Dict[str, object]:
    _validate_probe_config(
        development_max_n=development_max_n,
        intermediate_holdout_max_n=intermediate_holdout_max_n,
        holdout_max_n=holdout_max_n,
        edge_limit=edge_limit,
        composition_event_limit=composition_event_limit,
        permutation_count=permutation_count,
        operation_null_count=operation_null_count,
        enforce_preregistered_inputs=enforce_preregistered_inputs,
    )
    development_path = Path(development_db_path)
    holdout_path = Path(holdout_db_path)
    summary_path = Path(holdout_summary_path)
    manifest_path = Path(generation_manifest_path)
    analysis_manifest = Path(analysis_manifest_path)
    with closing(connect_readonly(development_path)) as development_conn, closing(
        connect_readonly(holdout_path)
    ) as holdout_conn:
        development_alignment = require_strict_alignment(development_conn)
        holdout_alignment = require_strict_alignment(holdout_conn)
        development_corpus = _corpus_payload(
            development_path,
            development_conn,
            alignment=development_alignment,
        )
        holdout_corpus = _corpus_payload(
            holdout_path,
            holdout_conn,
            alignment=holdout_alignment,
        )
        preregistered_inputs = _preregistered_input_audit(
            development_path,
            holdout_path,
            summary_path,
            manifest_path,
            analysis_manifest,
            development_corpus,
            holdout_corpus,
        )
        if enforce_preregistered_inputs and not preregistered_inputs["passes"]:
            failed = [
                key
                for key, value in preregistered_inputs["checks"].items()
                if not value
            ]
            raise SystemExit(
                "Preregistered input audit failed: " + ", ".join(failed)
            )

        prefix_parity = _prefix_feature_parity(
            development_conn,
            holdout_conn,
            max_n=development_max_n,
        )
        if not prefix_parity["exact_prefix_feature_parity"]:
            raise SystemExit(
                "Corpus-comparability stop: development and holdout prefix "
                "features differ"
            )

        representations_by_discriminant = {
            spec.discriminant: _family_representations(spec, holdout_max_n)
            for spec in FAMILIES
        }
        support_rows_by_discriminant = {
            spec.discriminant: _support_rows(
                spec,
                representations_by_discriminant[spec.discriminant],
                min_n=1,
                max_n=holdout_max_n,
            )
            for spec in FAMILIES
        }
        family_reports = {
            spec.discriminant: _family_exact_report(
                spec,
                representations_by_discriminant[spec.discriminant],
                support_rows_by_discriminant[spec.discriminant],
                development_max_n=development_max_n,
                holdout_max_n=holdout_max_n,
                composition_event_limit=composition_event_limit,
            )
            for spec in FAMILIES
        }

        features_by_discriminant: Dict[int, FeatureMap] = {}
        for spec in FAMILIES:
            scalar_moduli = _scalar_baseline_moduli(spec)
            development_features = _extract_feature_map(
                development_conn,
                range(1, development_max_n + 1),
                moduli=scalar_moduli,
                gcd_modulus=abs(spec.discriminant),
            )
            holdout_features = _extract_feature_map(
                holdout_conn,
                range(development_max_n + 1, holdout_max_n + 1),
                moduli=scalar_moduli,
                gcd_modulus=abs(spec.discriminant),
            )
            overlap = set(development_features) & set(holdout_features)
            if overlap:
                raise AssertionError("development and holdout feature keys overlap")
            features_by_discriminant[spec.discriminant] = {
                **development_features,
                **holdout_features,
            }

        graph_audit = _graph_audit(
            holdout_conn,
            holdout_corpus,
            family_reports,
            features_by_discriminant,
            holdout_max_n=holdout_max_n,
            edge_limit=edge_limit,
        )
        inverse_collisions = {
            spec.discriminant: _inverse_collision_report(
                spec,
                representations_by_discriminant[spec.discriminant],
                features_by_discriminant[spec.discriminant],
            )
            for spec in FAMILIES
        }
        recovery = _recovery_suite(
            support_rows_by_discriminant,
            features_by_discriminant,
            inverse_collisions,
            development_max_n=development_max_n,
            intermediate_holdout_max_n=intermediate_holdout_max_n,
            holdout_max_n=holdout_max_n,
            permutation_count=permutation_count,
            operation_null_count=operation_null_count,
            feature_audit_passes=bool(
                graph_audit["feature_provenance"]["passes"]
            ),
        )
        modulus_one = _modulus_one_projection(
            family_reports,
            inverse_collisions,
        )
        feature_integrity = {
            str(spec.discriminant): {
                "scalar_moduli": list(_scalar_baseline_moduli(spec)),
                "gcd_modulus": abs(spec.discriminant),
                "quotient_moduli": list(_family_moduli(spec)),
                "node_count": len(
                    features_by_discriminant[spec.discriminant]
                ),
                "feature_sha256": _feature_digest(
                    features_by_discriminant[spec.discriminant]
                ),
            }
            for spec in FAMILIES
        }

    final_development_hash = file_sha256(development_path)
    final_holdout_hash = file_sha256(holdout_path)
    database_hash_invariance = {
        "development_before": development_corpus["sha256"],
        "development_after": final_development_hash,
        "development_unchanged": (
            development_corpus["sha256"] == final_development_hash
        ),
        "holdout_before": holdout_corpus["sha256"],
        "holdout_after": final_holdout_hash,
        "holdout_unchanged": holdout_corpus["sha256"] == final_holdout_hash,
    }
    if not all(
        database_hash_invariance[key]
        for key in ("development_unchanged", "holdout_unchanged")
    ):
        raise AssertionError("a supposedly read-only corpus hash changed")

    final_checkpoint_id = (
        f"values_{development_max_n + 1}_to_{holdout_max_n}"
    )
    primary_summary = {}
    for task_id in ("d56_genus", "d56_within_genus_class"):
        final = recovery["tasks"][task_id]["checkpoints"][final_checkpoint_id]
        primary_summary[task_id] = {
            "status": final["status"],
            "scalar_balanced_accuracy": (
                final.get("scalar_model", {}).get("balanced_accuracy")
            ),
            "scalar_plus_graph_balanced_accuracy": (
                final.get("scalar_plus_graph_model", {}).get(
                    "balanced_accuracy"
                )
            ),
            "graph_lift": final.get("observed_graph_lift"),
            "promotion": recovery["promotion"][task_id],
        }
    return {
        "report_type": "gauss_nested_class_genus_ablation",
        "experiment_id": EXPERIMENT_ID,
        "schema_version": SCHEMA_VERSION,
        "config": {
            "development_values": [1, development_max_n],
            "intermediate_holdout_values": [
                development_max_n + 1,
                intermediate_holdout_max_n,
            ],
            "final_holdout_values": [
                development_max_n + 1,
                holdout_max_n,
            ],
            "feature_cutoff": "n+50 inclusive",
            "prime_exponent_max_value": PRIME_EXPONENT_MAX_VALUE,
            "permutation_count": permutation_count,
            "operation_null_count": operation_null_count,
            "composition_event_limit": composition_event_limit,
            "edge_limit": edge_limit,
            "enforce_preregistered_inputs": enforce_preregistered_inputs,
            "holdout_summary_path": str(summary_path),
            "generation_manifest_path": str(manifest_path),
            "analysis_manifest_path": str(analysis_manifest),
        },
        "source_map": _source_map(),
        "claim_boundary": _claim_boundary(),
        "preregistered_input_audit": preregistered_inputs,
        "corpora": {
            "development": development_corpus,
            "holdout": holdout_corpus,
            "database_hash_invariance": database_hash_invariance,
            "prefix_feature_parity": prefix_parity,
        },
        "feature_integrity": feature_integrity,
        "families": {
            str(discriminant): report
            for discriminant, report in sorted(family_reports.items())
        },
        "graph_audit": graph_audit,
        "inverse_collision_controls": {
            str(discriminant): report
            for discriminant, report in sorted(inverse_collisions.items())
        },
        "recovery": recovery,
        "modulus_one_projection": modulus_one,
        "summary": {
            "all_exact_family_calibrations_pass": all(
                all(
                    bool(value)
                    for value in report["exact_calibration_checks"].values()
                )
                for report in family_reports.values()
            ),
            "prefix_feature_parity_passes": prefix_parity[
                "exact_prefix_feature_parity"
            ],
            "feature_provenance_passes": graph_audit[
                "feature_provenance"
            ]["passes"],
            "database_hashes_unchanged": all(
                database_hash_invariance[key]
                for key in (
                    "development_unchanged",
                    "holdout_unchanged",
                )
            ),
            "primary_final_results": primary_summary,
            "any_graph_conditioned_effect_promoted": recovery[
                "any_graph_conditioned_effect_promoted"
            ],
            "graph_native_composition_prediction_performed": False,
            "modulus_one_is_exact_maximal_erasure": modulus_one[
                "all_endpoint_information_checks_exactly_zero"
            ],
        },
    }


def _positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return value


def _nonnegative_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return value


def _report_metadata(
    *,
    argv: Optional[Sequence[str]],
    development_db_path: Path,
    holdout_db_path: Path,
    include_checksums: bool,
) -> Dict[str, object]:
    tool_path = Path(__file__)
    arguments = list(argv) if argv is not None else sys.argv[1:]
    generated_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    preregistration_path = Path(
        'research/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.pre.md'
    )
    return {
        "generated_at_utc": generated_at,
        "python_version": ".".join(str(item) for item in sys.version_info[:3]),
        "command": shlex.join([sys.executable, str(tool_path), *arguments]),
        "tool_path": str(tool_path),
        "development_db_path": str(development_db_path),
        "holdout_db_path": str(holdout_db_path),
        "checksums_included": include_checksums,
        "tool_sha256": file_sha256(tool_path) if include_checksums else None,
        "preregistration_path": str(preregistration_path),
        "preregistration_sha256": (
            file_sha256(preregistration_path)
            if include_checksums and preregistration_path.exists()
            else None
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the preregistered D=-20,-23,-56 nested class/genus control "
            "against development and held-out strict-stage MoO corpora."
        )
    )
    parser.add_argument(
        "--development-db",
        type=Path,
        default=Path("out/experiments/pascal_edge_probe_u300.sqlite"),
    )
    parser.add_argument(
        "--holdout-db",
        type=Path,
        default=Path(
            "out/experiments/gauss/strict_stage_u850_holdout_v1.sqlite"
        ),
    )
    parser.add_argument(
        "--holdout-summary",
        type=Path,
        default=DEFAULT_HOLDOUT_SUMMARY_PATH,
    )
    parser.add_argument(
        "--generation-manifest",
        type=Path,
        default=DEFAULT_GENERATION_MANIFEST_PATH,
    )
    parser.add_argument(
        "--analysis-manifest",
        type=Path,
        default=DEFAULT_ANALYSIS_MANIFEST_PATH,
    )
    parser.add_argument(
        "--development-max-n",
        type=_positive_int,
        default=DEFAULT_DEVELOPMENT_MAX_N,
    )
    parser.add_argument(
        "--intermediate-holdout-max-n",
        type=_positive_int,
        default=DEFAULT_INTERMEDIATE_HOLDOUT_MAX_N,
    )
    parser.add_argument(
        "--holdout-max-n",
        type=_positive_int,
        default=DEFAULT_HOLDOUT_MAX_N,
    )
    parser.add_argument(
        "--composition-event-limit",
        type=_nonnegative_int,
        default=DEFAULT_COMPOSITION_EVENT_LIMIT,
    )
    parser.add_argument(
        "--permutations",
        type=_positive_int,
        default=DEFAULT_PERMUTATION_COUNT,
    )
    parser.add_argument(
        "--operation-null-permutations",
        type=_positive_int,
        default=DEFAULT_OPERATION_NULL_COUNT,
    )
    parser.add_argument(
        "--edge-limit",
        type=_positive_int,
        default=DEFAULT_EDGE_LIMIT,
    )
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--write",
        type=Path,
        help="Also write the JSON report; existing files are never overwritten.",
    )
    parser.add_argument(
        "--with-checksums",
        "--checksums",
        dest="with_checksums",
        action="store_true",
    )
    parser.add_argument(
        "--allow-nonpreregistered-fixture",
        action="store_true",
        help="Disable frozen input/range enforcement for synthetic tests only.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    actual_arguments = list(argv) if argv is not None else sys.argv[1:]
    args = parser.parse_args(actual_arguments)
    if not args.allow_nonpreregistered_fixture and (
        actual_arguments != FROZEN_ANALYSIS_CLI_ARGS
    ):
        raise SystemExit(
            "Preregistered analysis invocation mismatch. Expected arguments: "
            + shlex.join(FROZEN_ANALYSIS_CLI_ARGS)
        )
    payload = nested_quadratic_form_probe(
        development_db_path=Path(args.development_db),
        holdout_db_path=Path(args.holdout_db),
        holdout_summary_path=Path(args.holdout_summary),
        generation_manifest_path=Path(args.generation_manifest),
        analysis_manifest_path=Path(args.analysis_manifest),
        development_max_n=int(args.development_max_n),
        intermediate_holdout_max_n=int(args.intermediate_holdout_max_n),
        holdout_max_n=int(args.holdout_max_n),
        edge_limit=int(args.edge_limit),
        composition_event_limit=int(args.composition_event_limit),
        permutation_count=int(args.permutations),
        operation_null_count=int(args.operation_null_permutations),
        enforce_preregistered_inputs=not bool(
            args.allow_nonpreregistered_fixture
        ),
    )
    include_checksums = bool(args.with_checksums or args.write)
    payload["report_metadata"] = _report_metadata(
        argv=argv,
        development_db_path=Path(args.development_db),
        holdout_db_path=Path(args.holdout_db),
        include_checksums=include_checksums,
    )
    serialized = json.dumps(
        payload,
        indent=2 if args.pretty else None,
        sort_keys=True,
    ) + "\n"
    if args.write is not None:
        output_path = Path(args.write)
        if output_path.exists():
            raise SystemExit(f"Refusing to overwrite existing report: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized, encoding="utf-8")
    if not args.quiet:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
