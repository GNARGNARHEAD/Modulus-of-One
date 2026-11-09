from __future__ import annotations

import math
import random
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from itertools import chain
from typing import Dict, Hashable, Iterable, List, Mapping, Optional, Sequence, Tuple


NODE_CUTOFF_OFFSET = 50
GRAPH_OPERATIONS = ("+", "-", "*", "/")
OPERATION_NAMES = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "divide",
}


def positive_divisors(value: int) -> Tuple[int, ...]:
    """Return all positive divisors in increasing order."""
    n = int(value)
    if n < 1:
        raise ValueError("value must be >= 1")
    lower: List[int] = []
    upper: List[int] = []
    candidate = 1
    while candidate * candidate <= n:
        if n % candidate == 0:
            lower.append(candidate)
            partner = n // candidate
            if partner != candidate:
                upper.append(partner)
        candidate += 1
    return tuple(lower + list(reversed(upper)))


DEFAULT_MODULI = tuple(
    sorted(
        {
            divisor
            for discriminant in (20, 23, 56)
            for divisor in positive_divisors(discriminant)
            if divisor > 1
        }
    )
)


def _normalized_moduli(moduli: Iterable[int]) -> Tuple[int, ...]:
    normalized = set()
    for raw in moduli:
        modulus = int(raw)
        if modulus < 1:
            raise ValueError("moduli must be positive integers")
        normalized.add(modulus)
    return tuple(sorted(normalized))


def _prime_exponents(value: int) -> Tuple[int, ...]:
    n = int(value)
    if n < 1:
        raise ValueError("value must be >= 1")
    exponents: List[int] = []
    divisor = 2
    remaining = n
    while divisor * divisor <= remaining:
        if remaining % divisor:
            divisor = 3 if divisor == 2 else divisor + 2
            continue
        exponent = 0
        while remaining % divisor == 0:
            remaining //= divisor
            exponent += 1
        exponents.append(exponent)
        divisor = 3 if divisor == 2 else divisor + 2
    if remaining > 1:
        exponents.append(1)
    return tuple(exponents)


def primes_through(max_value: int) -> Tuple[int, ...]:
    """Return the primes at most max_value using a deterministic sieve."""
    limit = int(max_value)
    if limit < 1:
        raise ValueError("prime exponent max_value must be >= 1")
    if limit < 2:
        return ()
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    candidate = 2
    while candidate * candidate <= limit:
        if sieve[candidate]:
            start = candidate * candidate
            count = ((limit - start) // candidate) + 1
            sieve[start : limit + 1 : candidate] = b"\x00" * count
        candidate += 1
    return tuple(index for index in range(2, limit + 1) if sieve[index])


def _prime_exponent(value: int, prime: int) -> int:
    remaining = int(value)
    exponent = 0
    while remaining % int(prime) == 0:
        remaining //= int(prime)
        exponent += 1
    return exponent


def scalar_feature_names(
    moduli: Iterable[int] = DEFAULT_MODULI,
    *,
    prime_exponent_max_value: Optional[int] = None,
    gcd_modulus: Optional[int] = None,
) -> Tuple[str, ...]:
    normalized = _normalized_moduli(moduli)
    names = [
        "log1p_value",
        "divisor_count",
        "omega",
        "big_omega",
        "squarefree",
    ]
    if prime_exponent_max_value is not None:
        names.extend(
            f"prime_exponent_{prime}"
            for prime in primes_through(int(prime_exponent_max_value))
        )
    if gcd_modulus is not None:
        if int(gcd_modulus) < 1:
            raise ValueError("gcd_modulus must be >= 1")
        names.append(f"gcd_with_{int(gcd_modulus)}")
    for modulus in normalized:
        if gcd_modulus is None:
            names.append(f"gcd_with_{modulus}")
        names.extend(
            f"residue_mod_{modulus}_is_{residue}"
            for residue in range(modulus)
        )
    return tuple(names)


def extract_scalar_features(
    value: int,
    *,
    moduli: Iterable[int] = DEFAULT_MODULI,
    prime_exponent_max_value: Optional[int] = None,
    gcd_modulus: Optional[int] = None,
) -> Dict[str, float]:
    """Return the frozen value-only baseline features for one positive integer."""
    n = int(value)
    if n < 1:
        raise ValueError("value must be >= 1")
    normalized = _normalized_moduli(moduli)
    exponents = _prime_exponents(n)
    divisor_count = 1
    for exponent in exponents:
        divisor_count *= exponent + 1
    features: Dict[str, float] = {
        "log1p_value": math.log1p(n),
        "divisor_count": float(divisor_count),
        "omega": float(len(exponents)),
        "big_omega": float(sum(exponents)),
        "squarefree": float(all(exponent == 1 for exponent in exponents)),
    }
    if prime_exponent_max_value is not None:
        prime_limit = int(prime_exponent_max_value)
        if n > prime_limit:
            raise ValueError(
                "value exceeds prime_exponent_max_value; the requested vector "
                "would not encode its full factorization"
            )
        for prime in primes_through(prime_limit):
            features[f"prime_exponent_{prime}"] = float(
                _prime_exponent(n, prime)
            )
    if gcd_modulus is not None:
        normalized_gcd_modulus = int(gcd_modulus)
        if normalized_gcd_modulus < 1:
            raise ValueError("gcd_modulus must be >= 1")
        features[f"gcd_with_{normalized_gcd_modulus}"] = float(
            math.gcd(n, normalized_gcd_modulus)
        )
    for modulus in normalized:
        if gcd_modulus is None:
            features[f"gcd_with_{modulus}"] = float(math.gcd(n, modulus))
        observed = n % modulus
        for residue in range(modulus):
            features[f"residue_mod_{modulus}_is_{residue}"] = float(
                residue == observed
            )
    expected_names = scalar_feature_names(
        normalized,
        prime_exponent_max_value=prime_exponent_max_value,
        gcd_modulus=gcd_modulus,
    )
    if tuple(features) != expected_names:
        raise AssertionError("scalar feature ordering drifted from its frozen schema")
    return features


def graph_feature_names() -> Tuple[str, ...]:
    names = [
        "confirmation_lag",
        "incoming_edge_count",
        "outgoing_edge_count",
    ]
    for direction in ("incoming", "outgoing"):
        names.extend(
            f"{direction}_op_{OPERATION_NAMES[operation]}_count"
            for operation in GRAPH_OPERATIONS
        )
        names.append(f"{direction}_op_other_count")
    names.extend(
        (
            "incoming_distinct_operand_count",
            "outgoing_distinct_result_count",
        )
    )
    return tuple(names)


def _operation_histogram(
    conn: sqlite3.Connection,
    *,
    where_sql: str,
    params: Sequence[object],
) -> Dict[str, int]:
    rows = conn.execute(
        f"SELECT op, COUNT(*) FROM edges WHERE {where_sql} GROUP BY op",
        tuple(params),
    ).fetchall()
    return {str(row[0]): int(row[1]) for row in rows}


def extract_graph_features(
    conn: sqlite3.Connection,
    value: int,
) -> Dict[str, float]:
    """Extract a complete, form-independent node neighborhood through n + 50.

    The function deliberately accepts no form, genus, class, witness, or label
    argument. It performs SELECT queries only and refuses to return a censored
    neighborhood when the corpus has not reached the required per-node cutoff.
    """
    n = int(value)
    if n < 1:
        raise ValueError("value must be >= 1")
    cutoff = n + NODE_CUTOFF_OFFSET
    latest_row = conn.execute("SELECT MAX(stage) FROM stages").fetchone()
    latest_stage = (
        int(latest_row[0])
        if latest_row is not None and latest_row[0] is not None
        else None
    )
    if latest_stage is None or latest_stage < cutoff:
        raise ValueError(
            f"corpus latest stage {latest_stage} is below required cutoff {cutoff} "
            f"for node {n}"
        )

    node_row = conn.execute(
        "SELECT node_id, first_stage, confirmed_stage "
        "FROM nodes WHERE p = ? AND q = 1",
        (n,),
    ).fetchone()
    if node_row is None:
        raise ValueError(f"positive integer node {n} is absent from the corpus")
    node_id = int(node_row[0])
    first_stage = int(node_row[1])
    confirmed_stage = int(node_row[2]) if node_row[2] is not None else None
    if first_stage > cutoff:
        raise ValueError(f"node {n} is not present by required cutoff {cutoff}")
    if confirmed_stage is None or confirmed_stage > cutoff:
        raise ValueError(f"node {n} is not confirmed by required cutoff {cutoff}")
    confirmation_lag = confirmed_stage - first_stage
    if confirmation_lag < 0:
        raise ValueError(f"node {n} has a negative confirmation lag")

    incoming_where = "result_node_id = ? AND stage <= ?"
    incoming_params = (node_id, cutoff)
    outgoing_where = "(left_node_id = ? OR right_node_id = ?) AND stage <= ?"
    outgoing_params = (node_id, node_id, cutoff)
    incoming_histogram = _operation_histogram(
        conn,
        where_sql=incoming_where,
        params=incoming_params,
    )
    outgoing_histogram = _operation_histogram(
        conn,
        where_sql=outgoing_where,
        params=outgoing_params,
    )
    incoming_count = sum(incoming_histogram.values())
    outgoing_count = sum(outgoing_histogram.values())

    incoming_distinct_operands = int(
        conn.execute(
            "SELECT COUNT(*) FROM ("
            "SELECT left_node_id AS operand_node_id FROM edges "
            "WHERE result_node_id = ? AND stage <= ? AND left_node_id IS NOT NULL "
            "UNION "
            "SELECT right_node_id AS operand_node_id FROM edges "
            "WHERE result_node_id = ? AND stage <= ? AND right_node_id IS NOT NULL"
            ")",
            (node_id, cutoff, node_id, cutoff),
        ).fetchone()[0]
    )
    outgoing_distinct_results = int(
        conn.execute(
            "SELECT COUNT(DISTINCT result_node_id) FROM edges "
            "WHERE (left_node_id = ? OR right_node_id = ?) AND stage <= ?",
            outgoing_params,
        ).fetchone()[0]
    )

    features: Dict[str, float] = {
        "confirmation_lag": float(confirmation_lag),
        "incoming_edge_count": float(incoming_count),
        "outgoing_edge_count": float(outgoing_count),
    }
    known_operations = set(GRAPH_OPERATIONS)
    for direction, histogram in (
        ("incoming", incoming_histogram),
        ("outgoing", outgoing_histogram),
    ):
        for operation in GRAPH_OPERATIONS:
            features[
                f"{direction}_op_{OPERATION_NAMES[operation]}_count"
            ] = float(histogram.get(operation, 0))
        features[f"{direction}_op_other_count"] = float(
            sum(
                count
                for operation, count in histogram.items()
                if operation not in known_operations
            )
        )
    features["incoming_distinct_operand_count"] = float(
        incoming_distinct_operands
    )
    features["outgoing_distinct_result_count"] = float(
        outgoing_distinct_results
    )
    if tuple(features) != graph_feature_names():
        raise AssertionError("graph feature ordering drifted from its frozen schema")
    return features


@dataclass(frozen=True)
class NodeFeatureRow:
    value: int
    cutoff_stage: int
    moduli: Tuple[int, ...]
    prime_exponent_max_value: Optional[int]
    scalar_names: Tuple[str, ...]
    scalar_values: Tuple[float, ...]
    graph_names: Tuple[str, ...]
    graph_values: Tuple[float, ...]
    gcd_modulus: Optional[int] = None

    def names(self, feature_set: str) -> Tuple[str, ...]:
        if feature_set == "scalar":
            return self.scalar_names
        if feature_set == "graph":
            return self.graph_names
        if feature_set == "combined":
            return self.scalar_names + self.graph_names
        raise ValueError("feature_set must be 'scalar', 'graph', or 'combined'")

    def vector(self, feature_set: str) -> Tuple[float, ...]:
        if feature_set == "scalar":
            return self.scalar_values
        if feature_set == "graph":
            return self.graph_values
        if feature_set == "combined":
            return self.scalar_values + self.graph_values
        raise ValueError("feature_set must be 'scalar', 'graph', or 'combined'")

    def payload(self) -> Dict[str, object]:
        return {
            "value": self.value,
            "cutoff_stage": self.cutoff_stage,
            "cutoff_rule": "value+50",
            "moduli": list(self.moduli),
            "prime_exponent_max_value": self.prime_exponent_max_value,
            "gcd_modulus": self.gcd_modulus,
            "scalar_features": dict(zip(self.scalar_names, self.scalar_values)),
            "graph_features": dict(zip(self.graph_names, self.graph_values)),
            "form_or_class_inputs_used": False,
        }


def extract_node_features(
    conn: sqlite3.Connection,
    value: int,
    *,
    moduli: Iterable[int] = DEFAULT_MODULI,
    prime_exponent_max_value: Optional[int] = None,
    gcd_modulus: Optional[int] = None,
) -> NodeFeatureRow:
    """Combine independently extracted scalar and graph-only feature blocks."""
    n = int(value)
    normalized = _normalized_moduli(moduli)
    scalar = extract_scalar_features(
        n,
        moduli=normalized,
        prime_exponent_max_value=prime_exponent_max_value,
        gcd_modulus=gcd_modulus,
    )
    graph = extract_graph_features(conn, n)
    return NodeFeatureRow(
        value=n,
        cutoff_stage=n + NODE_CUTOFF_OFFSET,
        moduli=normalized,
        prime_exponent_max_value=(
            int(prime_exponent_max_value)
            if prime_exponent_max_value is not None
            else None
        ),
        scalar_names=tuple(scalar),
        scalar_values=tuple(float(value) for value in scalar.values()),
        graph_names=tuple(graph),
        graph_values=tuple(float(value) for value in graph.values()),
        gcd_modulus=(int(gcd_modulus) if gcd_modulus is not None else None),
    )


def feature_matrix(
    rows: Sequence[NodeFeatureRow],
    *,
    feature_set: str,
) -> Tuple[Tuple[str, ...], Tuple[Tuple[float, ...], ...]]:
    if not rows:
        raise ValueError("at least one feature row is required")
    names = rows[0].names(feature_set)
    matrix: List[Tuple[float, ...]] = []
    for row in rows:
        if row.names(feature_set) != names:
            raise ValueError("feature rows do not share one frozen feature schema")
        matrix.append(row.vector(feature_set))
    return names, tuple(matrix)


def _validated_matrix(
    rows: Sequence[Sequence[float]],
    *,
    expected_width: Optional[int] = None,
) -> Tuple[Tuple[float, ...], ...]:
    if not rows:
        raise ValueError("feature matrix must not be empty")
    matrix = tuple(tuple(float(value) for value in row) for row in rows)
    width = len(matrix[0])
    if width < 1:
        raise ValueError("feature rows must contain at least one value")
    if expected_width is not None and width != int(expected_width):
        raise ValueError("feature row width does not match the trained model")
    for row in matrix:
        if len(row) != width:
            raise ValueError("feature matrix rows must have equal width")
        if not all(math.isfinite(value) for value in row):
            raise ValueError("feature values must be finite")
    return matrix


@dataclass(frozen=True)
class NearestCentroidModel:
    feature_names: Tuple[str, ...]
    labels: Tuple[str, ...]
    training_means: Tuple[float, ...]
    training_scales: Tuple[float, ...]
    centroids: Mapping[str, Tuple[float, ...]]
    training_class_counts: Mapping[str, int]

    def payload(self) -> Dict[str, object]:
        return {
            "classifier": "training_zscore_nearest_centroid",
            "feature_names": list(self.feature_names),
            "labels": list(self.labels),
            "training_means": list(self.training_means),
            "training_scales": list(self.training_scales),
            "centroids": {
                label: list(self.centroids[label]) for label in self.labels
            },
            "training_class_counts": dict(self.training_class_counts),
            "zero_variance_scale_policy": (
                "centered values are exactly zero; store divisor scale 1"
            ),
            "distance": "squared_euclidean_after_training_zscore",
            "tie_break": (
                "larger_training_class_count_then_lexicographically_smallest_label"
            ),
        }


def fit_nearest_centroid(
    rows: Sequence[Sequence[float]],
    labels: Sequence[str],
    *,
    feature_names: Optional[Sequence[str]] = None,
    class_labels: Optional[Sequence[str]] = None,
) -> NearestCentroidModel:
    matrix = _validated_matrix(rows)
    if len(matrix) != len(labels):
        raise ValueError("feature rows and labels must have equal length")
    normalized_labels = tuple(str(label) for label in labels)
    if class_labels is None:
        ordered_labels = tuple(sorted(set(normalized_labels)))
    else:
        ordered_labels = tuple(str(label) for label in class_labels)
        if len(set(ordered_labels)) != len(ordered_labels):
            raise ValueError("class_labels must be unique")
        unknown = sorted(set(normalized_labels) - set(ordered_labels))
        if unknown:
            raise ValueError(f"training labels are absent from class_labels: {unknown}")
    if not ordered_labels:
        raise ValueError("at least one class label is required")
    width = len(matrix[0])
    if feature_names is None:
        names = tuple(f"feature_{index}" for index in range(width))
    else:
        names = tuple(str(name) for name in feature_names)
        if len(names) != width:
            raise ValueError("feature_names length must match feature row width")
        if len(set(names)) != len(names):
            raise ValueError("feature_names must be unique")

    sample_count = len(matrix)
    means = tuple(
        math.fsum(row[column] for row in matrix) / sample_count
        for column in range(width)
    )
    population_scales = []
    for column in range(width):
        variance = math.fsum(
            (row[column] - means[column]) ** 2 for row in matrix
        ) / sample_count
        scale = math.sqrt(variance)
        population_scales.append(scale if scale > 0.0 else 1.0)
    scales = tuple(population_scales)
    standardized = tuple(
        tuple(
            (row[column] - means[column]) / scales[column]
            for column in range(width)
        )
        for row in matrix
    )

    member_indices: Dict[str, List[int]] = defaultdict(list)
    for index, label in enumerate(normalized_labels):
        member_indices[label].append(index)
    centroids: Dict[str, Tuple[float, ...]] = {}
    for label in ordered_labels:
        indices = member_indices[label]
        if not indices:
            raise ValueError(f"class {label!r} has an empty training centroid")
        centroids[label] = tuple(
            math.fsum(standardized[index][column] for index in indices)
            / len(indices)
            for column in range(width)
        )
    return NearestCentroidModel(
        feature_names=names,
        labels=ordered_labels,
        training_means=means,
        training_scales=scales,
        centroids=centroids,
        training_class_counts={
            label: len(member_indices[label]) for label in ordered_labels
        },
    )


def predict_nearest_centroid(
    model: NearestCentroidModel,
    rows: Sequence[Sequence[float]],
) -> Tuple[str, ...]:
    if not rows:
        return ()
    matrix = _validated_matrix(rows, expected_width=len(model.feature_names))
    predictions: List[str] = []
    for row in matrix:
        standardized = tuple(
            (row[column] - model.training_means[column])
            / model.training_scales[column]
            for column in range(len(row))
        )
        distances = {
            label: math.fsum(
                (standardized[column] - model.centroids[label][column]) ** 2
                for column in range(len(row))
            )
            for label in model.labels
        }
        predictions.append(
            min(
                model.labels,
                key=lambda label: (
                    distances[label],
                    -int(model.training_class_counts[label]),
                    label,
                ),
            )
        )
    return tuple(predictions)


def macro_balanced_accuracy(
    true_labels: Sequence[str],
    predicted_labels: Sequence[str],
    *,
    labels: Optional[Sequence[str]] = None,
) -> float:
    """Return multiclass balanced accuracy, i.e. macro-average recall."""
    if len(true_labels) != len(predicted_labels):
        raise ValueError("true and predicted labels must have equal length")
    if not true_labels:
        raise ValueError("at least one labelled sample is required")
    truth = tuple(str(label) for label in true_labels)
    predicted = tuple(str(label) for label in predicted_labels)
    ordered = (
        tuple(sorted(set(truth)))
        if labels is None
        else tuple(str(label) for label in labels)
    )
    if not ordered or len(set(ordered)) != len(ordered):
        raise ValueError("labels must be a nonempty unique sequence")
    recalls = []
    for label in ordered:
        total = sum(observed == label for observed in truth)
        if total == 0:
            raise ValueError(f"label {label!r} has no true samples")
        correct = sum(
            observed == label and guessed == label
            for observed, guessed in zip(truth, predicted)
        )
        recalls.append(correct / total)
    return math.fsum(recalls) / len(recalls)


@dataclass(frozen=True)
class PermutationTestResult:
    observed_score: float
    null_scores: Tuple[float, ...]
    exceedance_count: int
    permutation_count: int
    seed: int
    p_value: float

    def payload(self) -> Dict[str, object]:
        return {
            "metric": "macro_balanced_accuracy",
            "observed_score": self.observed_score,
            "null_scores": list(self.null_scores),
            "exceedance_count": self.exceedance_count,
            "permutation_count": self.permutation_count,
            "seed": self.seed,
            "p_value": self.p_value,
            "p_value_formula": "(1 + null_scores_ge_observed)/(1 + permutations)",
            "permutation_scheme": (
                "deterministic independent label permutations within the fixed "
                "training and test partitions"
            ),
        }


def deterministic_label_permutation_test(
    training_rows: Sequence[Sequence[float]],
    training_labels: Sequence[str],
    test_rows: Sequence[Sequence[float]],
    test_labels: Sequence[str],
    *,
    permutation_count: int,
    seed: int = 0,
    feature_names: Optional[Sequence[str]] = None,
) -> PermutationTestResult:
    if int(permutation_count) < 1:
        raise ValueError("permutation_count must be >= 1")
    training_matrix = _validated_matrix(training_rows)
    test_matrix = _validated_matrix(
        test_rows,
        expected_width=len(training_matrix[0]),
    )
    if len(training_matrix) != len(training_labels):
        raise ValueError("training rows and labels must have equal length")
    if len(test_matrix) != len(test_labels):
        raise ValueError("test rows and labels must have equal length")
    train_truth = tuple(str(label) for label in training_labels)
    test_truth = tuple(str(label) for label in test_labels)
    labels = tuple(sorted(set(train_truth) | set(test_truth)))
    if not set(test_truth).issubset(set(train_truth)):
        raise ValueError("every test label must occur in the training labels")

    observed_model = fit_nearest_centroid(
        training_matrix,
        train_truth,
        feature_names=feature_names,
    )
    observed_predictions = predict_nearest_centroid(observed_model, test_matrix)
    observed_score = macro_balanced_accuracy(
        test_truth,
        observed_predictions,
        labels=labels,
    )

    generator = random.Random(int(seed))
    null_scores: List[float] = []
    for _ in range(int(permutation_count)):
        shuffled_train = list(train_truth)
        shuffled_test = list(test_truth)
        generator.shuffle(shuffled_train)
        generator.shuffle(shuffled_test)
        model = fit_nearest_centroid(
            training_matrix,
            shuffled_train,
            feature_names=feature_names,
        )
        predictions = predict_nearest_centroid(model, test_matrix)
        null_scores.append(
            macro_balanced_accuracy(
                shuffled_test,
                predictions,
                labels=labels,
            )
        )
    exceedances = sum(score >= observed_score for score in null_scores)
    return PermutationTestResult(
        observed_score=observed_score,
        null_scores=tuple(null_scores),
        exceedance_count=exceedances,
        permutation_count=int(permutation_count),
        seed=int(seed),
        p_value=(1 + exceedances) / (1 + int(permutation_count)),
    )


def deterministic_label_permutation_p_value(
    training_rows: Sequence[Sequence[float]],
    training_labels: Sequence[str],
    test_rows: Sequence[Sequence[float]],
    test_labels: Sequence[str],
    *,
    permutation_count: int,
    seed: int = 0,
    feature_names: Optional[Sequence[str]] = None,
) -> float:
    return deterministic_label_permutation_test(
        training_rows,
        training_labels,
        test_rows,
        test_labels,
        permutation_count=permutation_count,
        seed=seed,
        feature_names=feature_names,
    ).p_value


@dataclass(frozen=True)
class GraphBlockPermutationResult:
    scalar_score: float
    combined_score: float
    observed_graph_lift: float
    null_graph_lifts: Tuple[float, ...]
    exceedance_count: int
    permutation_count: int
    seed: int
    p_value: float
    training_movable_row_fraction: float
    test_movable_row_fraction: float
    movable_row_fraction: float

    def payload(self) -> Dict[str, object]:
        return {
            "metric": "macro_balanced_accuracy",
            "scalar_score": self.scalar_score,
            "combined_score": self.combined_score,
            "observed_graph_lift": self.observed_graph_lift,
            "null_graph_lifts": list(self.null_graph_lifts),
            "exceedance_count": self.exceedance_count,
            "permutation_count": self.permutation_count,
            "seed": self.seed,
            "p_value": self.p_value,
            "p_value_formula": "(1 + null_lifts_ge_observed)/(1 + permutations)",
            "training_movable_row_fraction": self.training_movable_row_fraction,
            "test_movable_row_fraction": self.test_movable_row_fraction,
            "movable_row_fraction": self.movable_row_fraction,
            "null_scheme": (
                "shuffle the complete graph feature block within caller-supplied "
                "strata, separately in the fixed training and test partitions; "
                "keep scalar rows and labels fixed"
            ),
        }


def _movable_row_count(strata: Sequence[Hashable]) -> int:
    counts = Counter(strata)
    return sum(count for count in counts.values() if count > 1)


def _shuffle_rows_within_strata(
    rows: Tuple[Tuple[float, ...], ...],
    strata: Sequence[Hashable],
    generator: random.Random,
) -> Tuple[Tuple[float, ...], ...]:
    if len(rows) != len(strata):
        raise ValueError("feature rows and strata must have equal length")
    indices_by_stratum: Dict[Hashable, List[int]] = defaultdict(list)
    for index, stratum in enumerate(strata):
        indices_by_stratum[stratum].append(index)
    shuffled = list(rows)
    for indices in indices_by_stratum.values():
        source_rows = [rows[index] for index in indices]
        generator.shuffle(source_rows)
        for target_index, source_row in zip(indices, source_rows):
            shuffled[target_index] = source_row
    return tuple(shuffled)


def _standardize_with_model(
    model: NearestCentroidModel,
    rows: Tuple[Tuple[float, ...], ...],
) -> Tuple[Tuple[float, ...], ...]:
    return tuple(
        tuple(
            (row[column] - model.training_means[column])
            / model.training_scales[column]
            for column in range(len(row))
        )
        for row in rows
    )


def _centroids_from_standardized_rows(
    rows: Tuple[Tuple[float, ...], ...],
    *,
    labels: Tuple[str, ...],
    member_indices: Mapping[str, Sequence[int]],
) -> Dict[str, Tuple[float, ...]]:
    width = len(rows[0])
    return {
        label: tuple(
            math.fsum(rows[index][column] for index in member_indices[label])
            / len(member_indices[label])
            for column in range(width)
        )
        for label in labels
    }


def _cached_scalar_squared_terms(
    scalar_model: NearestCentroidModel,
    standardized_test_scalar: Tuple[Tuple[float, ...], ...],
) -> Tuple[Dict[str, Tuple[float, ...]], ...]:
    return tuple(
        {
            label: tuple(
                (row[column] - scalar_model.centroids[label][column]) ** 2
                for column in range(len(row))
            )
            for label in scalar_model.labels
        }
        for row in standardized_test_scalar
    )


def _predict_from_cached_scalar_and_graph(
    *,
    labels: Tuple[str, ...],
    training_class_counts: Mapping[str, int],
    scalar_squared_terms: Tuple[Dict[str, Tuple[float, ...]], ...],
    standardized_test_graph: Tuple[Tuple[float, ...], ...],
    graph_centroids: Mapping[str, Tuple[float, ...]],
) -> Tuple[str, ...]:
    predictions: List[str] = []
    for scalar_terms, graph_row in zip(
        scalar_squared_terms,
        standardized_test_graph,
    ):
        distances = {
            label: math.fsum(
                chain(
                    scalar_terms[label],
                    (
                        (graph_row[column] - graph_centroids[label][column]) ** 2
                        for column in range(len(graph_row))
                    ),
                )
            )
            for label in labels
        }
        predictions.append(
            min(
                labels,
                key=lambda label: (
                    distances[label],
                    -int(training_class_counts[label]),
                    label,
                ),
            )
        )
    return tuple(predictions)


def paired_graph_block_permutation_test(
    training_scalar_rows: Sequence[Sequence[float]],
    training_graph_rows: Sequence[Sequence[float]],
    training_labels: Sequence[str],
    training_strata: Sequence[Hashable],
    test_scalar_rows: Sequence[Sequence[float]],
    test_graph_rows: Sequence[Sequence[float]],
    test_labels: Sequence[str],
    test_strata: Sequence[Hashable],
    *,
    permutation_count: int,
    seed: int = 0,
    scalar_feature_names: Optional[Sequence[str]] = None,
    graph_feature_names: Optional[Sequence[str]] = None,
) -> GraphBlockPermutationResult:
    """Test scalar+graph lift against a matched graph-block shuffle null."""
    if int(permutation_count) < 1:
        raise ValueError("permutation_count must be >= 1")
    train_scalar = _validated_matrix(training_scalar_rows)
    train_graph = _validated_matrix(training_graph_rows)
    test_scalar = _validated_matrix(
        test_scalar_rows,
        expected_width=len(train_scalar[0]),
    )
    test_graph = _validated_matrix(
        test_graph_rows,
        expected_width=len(train_graph[0]),
    )
    train_count = len(train_scalar)
    test_count = len(test_scalar)
    if len(train_graph) != train_count or len(training_labels) != train_count:
        raise ValueError("training scalar, graph, and label rows must align")
    if len(training_strata) != train_count:
        raise ValueError("training rows and strata must have equal length")
    if len(test_graph) != test_count or len(test_labels) != test_count:
        raise ValueError("test scalar, graph, and label rows must align")
    if len(test_strata) != test_count:
        raise ValueError("test rows and strata must have equal length")
    train_truth = tuple(str(label) for label in training_labels)
    test_truth = tuple(str(label) for label in test_labels)
    labels = tuple(sorted(set(train_truth) | set(test_truth)))
    if not set(test_truth).issubset(set(train_truth)):
        raise ValueError("every test label must occur in the training labels")

    if scalar_feature_names is None:
        scalar_names = tuple(
            f"scalar_feature_{index}" for index in range(len(train_scalar[0]))
        )
    else:
        scalar_names = tuple(str(name) for name in scalar_feature_names)
        if len(scalar_names) != len(train_scalar[0]):
            raise ValueError("scalar_feature_names width mismatch")
    if graph_feature_names is None:
        graph_names = tuple(
            f"graph_feature_{index}" for index in range(len(train_graph[0]))
        )
    else:
        graph_names = tuple(str(name) for name in graph_feature_names)
        if len(graph_names) != len(train_graph[0]):
            raise ValueError("graph_feature_names width mismatch")
    combined_names = scalar_names + graph_names
    if len(set(combined_names)) != len(combined_names):
        raise ValueError("scalar and graph feature names must be jointly unique")

    scalar_model = fit_nearest_centroid(
        train_scalar,
        train_truth,
        feature_names=scalar_names,
        class_labels=labels,
    )
    scalar_predictions = predict_nearest_centroid(scalar_model, test_scalar)
    scalar_score = macro_balanced_accuracy(
        test_truth,
        scalar_predictions,
        labels=labels,
    )

    train_combined = tuple(
        scalar + graph for scalar, graph in zip(train_scalar, train_graph)
    )
    test_combined = tuple(
        scalar + graph for scalar, graph in zip(test_scalar, test_graph)
    )
    combined_model = fit_nearest_centroid(
        train_combined,
        train_truth,
        feature_names=combined_names,
        class_labels=labels,
    )
    combined_predictions = predict_nearest_centroid(combined_model, test_combined)
    combined_score = macro_balanced_accuracy(
        test_truth,
        combined_predictions,
        labels=labels,
    )
    observed_lift = combined_score - scalar_score

    # A graph-block shuffle preserves the training multiset of every graph
    # coordinate. Its training means and population scales therefore do not
    # change. Scalar rows and labels are fixed as well, so their class
    # centroids and contribution to every test/class distance can be cached.
    graph_model = fit_nearest_centroid(
        train_graph,
        train_truth,
        feature_names=graph_names,
        class_labels=labels,
    )
    standardized_train_graph = _standardize_with_model(graph_model, train_graph)
    standardized_test_graph = _standardize_with_model(graph_model, test_graph)
    standardized_test_scalar = _standardize_with_model(scalar_model, test_scalar)
    scalar_squared_terms = _cached_scalar_squared_terms(
        scalar_model,
        standardized_test_scalar,
    )
    member_indices: Dict[str, List[int]] = defaultdict(list)
    for index, label in enumerate(train_truth):
        member_indices[label].append(index)

    generator = random.Random(int(seed))
    null_lifts: List[float] = []
    for _ in range(int(permutation_count)):
        shuffled_train_graph = _shuffle_rows_within_strata(
            standardized_train_graph,
            training_strata,
            generator,
        )
        shuffled_test_graph = _shuffle_rows_within_strata(
            standardized_test_graph,
            test_strata,
            generator,
        )
        graph_centroids = _centroids_from_standardized_rows(
            shuffled_train_graph,
            labels=labels,
            member_indices=member_indices,
        )
        predictions = _predict_from_cached_scalar_and_graph(
            labels=labels,
            training_class_counts=scalar_model.training_class_counts,
            scalar_squared_terms=scalar_squared_terms,
            standardized_test_graph=shuffled_test_graph,
            graph_centroids=graph_centroids,
        )
        score = macro_balanced_accuracy(
            test_truth,
            predictions,
            labels=labels,
        )
        null_lifts.append(score - scalar_score)
    exceedances = sum(lift >= observed_lift for lift in null_lifts)
    train_movable = _movable_row_count(training_strata)
    test_movable = _movable_row_count(test_strata)
    total_rows = train_count + test_count
    return GraphBlockPermutationResult(
        scalar_score=scalar_score,
        combined_score=combined_score,
        observed_graph_lift=observed_lift,
        null_graph_lifts=tuple(null_lifts),
        exceedance_count=exceedances,
        permutation_count=int(permutation_count),
        seed=int(seed),
        p_value=(1 + exceedances) / (1 + int(permutation_count)),
        training_movable_row_fraction=train_movable / train_count,
        test_movable_row_fraction=test_movable / test_count,
        movable_row_fraction=(train_movable + test_movable) / total_rows,
    )


def _validate_discrete_sequences(
    *sequences: Sequence[Hashable],
) -> Tuple[Tuple[Hashable, ...], ...]:
    if not sequences:
        raise ValueError("at least one sequence is required")
    normalized = tuple(tuple(sequence) for sequence in sequences)
    length = len(normalized[0])
    if length < 1:
        raise ValueError("discrete sequences must not be empty")
    if any(len(sequence) != length for sequence in normalized):
        raise ValueError("discrete sequences must have equal length")
    return normalized


def _log_ratio(ratio: float, base: float) -> float:
    if not math.isfinite(float(base)) or float(base) <= 0.0 or float(base) == 1.0:
        raise ValueError("logarithm base must be finite, positive, and not 1")
    return math.log(ratio) / math.log(float(base))


def mutual_information(
    left: Sequence[Hashable],
    right: Sequence[Hashable],
    *,
    base: float = 2.0,
) -> float:
    """Return the empirical plug-in mutual information of two discrete variables."""
    x, y = _validate_discrete_sequences(left, right)
    total = len(x)
    x_counts = Counter(x)
    y_counts = Counter(y)
    joint_counts = Counter(zip(x, y))
    information = math.fsum(
        (count / total)
        * _log_ratio(
            (count * total) / (x_counts[x_value] * y_counts[y_value]),
            base,
        )
        for (x_value, y_value), count in joint_counts.items()
    )
    return 0.0 if abs(information) < 1e-15 else information


def conditional_mutual_information(
    left: Sequence[Hashable],
    right: Sequence[Hashable],
    condition: Sequence[Hashable],
    *,
    base: float = 2.0,
) -> float:
    """Return empirical I(left; right | condition) for discrete variables."""
    x, y, z = _validate_discrete_sequences(left, right, condition)
    total = len(x)
    xyz_counts = Counter(zip(x, y, z))
    xz_counts = Counter(zip(x, z))
    yz_counts = Counter(zip(y, z))
    z_counts = Counter(z)
    information = math.fsum(
        (count / total)
        * _log_ratio(
            (count * z_counts[z_value])
            / (xz_counts[(x_value, z_value)] * yz_counts[(y_value, z_value)]),
            base,
        )
        for (x_value, y_value, z_value), count in xyz_counts.items()
    )
    return 0.0 if abs(information) < 1e-15 else information


def exact_collision_ceiling(
    rows: Sequence[Sequence[Hashable]],
    labels: Sequence[str],
    *,
    metric: str = "macro_balanced_accuracy",
) -> Fraction:
    """Return the exact best deterministic score allowed by feature collisions."""
    if len(rows) != len(labels):
        raise ValueError("feature rows and labels must have equal length")
    if not rows:
        raise ValueError("at least one labelled feature row is required")
    signatures = [tuple(row) for row in rows]
    normalized_labels = tuple(str(label) for label in labels)
    ordered_labels = tuple(sorted(set(normalized_labels)))
    cells: Dict[Tuple[Hashable, ...], Counter[str]] = defaultdict(Counter)
    for signature, label in zip(signatures, normalized_labels):
        cells[signature][label] += 1

    if metric == "accuracy":
        correct = sum(max(counts.values()) for counts in cells.values())
        return Fraction(correct, len(signatures))
    if metric != "macro_balanced_accuracy":
        raise ValueError("metric must be 'accuracy' or 'macro_balanced_accuracy'")

    class_totals = Counter(normalized_labels)
    best_recall_mass = Fraction(0, 1)
    for counts in cells.values():
        best_recall_mass += max(
            Fraction(counts.get(label, 0), class_totals[label])
            for label in ordered_labels
        )
    return best_recall_mass / len(ordered_labels)


def collision_ceiling_report(
    rows: Sequence[Sequence[Hashable]],
    labels: Sequence[str],
) -> Dict[str, object]:
    signatures = [tuple(row) for row in rows]
    normalized_labels = tuple(str(label) for label in labels)
    if len(signatures) != len(normalized_labels):
        raise ValueError("feature rows and labels must have equal length")
    if not signatures:
        raise ValueError("at least one labelled feature row is required")
    cells: Dict[Tuple[Hashable, ...], Counter[str]] = defaultdict(Counter)
    for signature, label in zip(signatures, normalized_labels):
        cells[signature][label] += 1
    conflicting = [counts for counts in cells.values() if len(counts) > 1]
    accuracy = exact_collision_ceiling(signatures, normalized_labels, metric="accuracy")
    balanced = exact_collision_ceiling(
        signatures,
        normalized_labels,
        metric="macro_balanced_accuracy",
    )
    return {
        "sample_count": len(signatures),
        "distinct_feature_signature_count": len(cells),
        "conflicting_feature_signature_count": len(conflicting),
        "samples_in_conflicting_signatures": sum(sum(row.values()) for row in conflicting),
        "accuracy_ceiling": float(accuracy),
        "accuracy_ceiling_exact": f"{accuracy.numerator}/{accuracy.denominator}",
        "macro_balanced_accuracy_ceiling": float(balanced),
        "macro_balanced_accuracy_ceiling_exact": (
            f"{balanced.numerator}/{balanced.denominator}"
        ),
        "interpretation": (
            "best in-sample deterministic score obtainable by assigning one label "
            "to each exact feature signature"
        ),
    }
