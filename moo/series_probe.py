from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from moo.graph_corpus import format_key, normalize_key
from moo.graph_evidence import GraphEvidence
from moo.research_utils import (
    connect_readonly,
    emit_json,
    positive_int,
    report_metadata,
    require_strict_alignment,
)


Key = Tuple[int, int]
MAX_GEOMETRIC_TERMS = 64
MAX_ZETA_N = 100
MAX_EULER_PRIME = 200
MAX_EULER_LOCAL_TERMS = 64
MAX_RATIO_COMPONENT_BITS = 256


@dataclass(frozen=True)
class GeometricStep:
    index: int
    term: Fraction
    partial_sum: Fraction
    closed_form: Fraction
    previous_term: Optional[Fraction]
    previous_sum: Optional[Fraction]


@dataclass(frozen=True)
class ZetaStep:
    n: int
    square: int
    term: Fraction
    partial_sum: Fraction
    previous_sum: Optional[Fraction]


@dataclass(frozen=True)
class EulerProductStep:
    prime: int
    square: int
    ratio: Fraction
    factor: Fraction
    partial_product: Fraction
    previous_product: Fraction
    local_partial_sum: Fraction
    local_residual: Fraction


def _fraction_arg(raw: str) -> Fraction:
    try:
        return Fraction(str(raw))
    except (ValueError, ZeroDivisionError) as exc:
        raise argparse.ArgumentTypeError(f"must be an exact rational: {exc}") from exc


def _at_least_two_int(raw: str) -> int:
    value = positive_int(raw)
    if value < 2:
        raise argparse.ArgumentTypeError("must be >= 2")
    return value


def _key(value: Fraction | int) -> Key:
    fraction = value if isinstance(value, Fraction) else Fraction(int(value), 1)
    return normalize_key(int(fraction.numerator), int(fraction.denominator))


def _label(value: Fraction | int) -> str:
    return format_key(_key(value))


def fraction_payload(value: Fraction | int) -> Dict[str, object]:
    fraction = value if isinstance(value, Fraction) else Fraction(int(value), 1)
    key = _key(fraction)
    try:
        value_float: Optional[float] = float(fraction)
    except OverflowError:
        value_float = None
    return {
        "frac": format_key(key),
        "p": int(key[0]),
        "q": int(key[1]),
        "value_float": value_float,
    }


def geometric_series_steps(ratio: Fraction, term_count: int) -> List[GeometricStep]:
    count = int(term_count)
    if count < 1:
        raise ValueError("term_count must be >= 1")

    steps: List[GeometricStep] = []
    term = Fraction(1, 1)
    partial_sum = Fraction(0, 1)
    previous_term: Optional[Fraction] = None
    previous_sum: Optional[Fraction] = None
    for index in range(count):
        partial_sum += term
        if ratio == 1:
            closed_form = Fraction(index + 1, 1)
        else:
            closed_form = (1 - ratio ** (index + 1)) / (1 - ratio)
        if partial_sum != closed_form:
            raise AssertionError("geometric recurrence and closed form disagree")
        steps.append(
            GeometricStep(
                index=index,
                term=term,
                partial_sum=partial_sum,
                closed_form=closed_form,
                previous_term=previous_term,
                previous_sum=previous_sum,
            )
        )
        previous_term = term
        previous_sum = partial_sum
        term *= ratio
    return steps


def zeta2_steps(max_n: int) -> List[ZetaStep]:
    limit = int(max_n)
    if limit < 1:
        raise ValueError("max_n must be >= 1")

    steps: List[ZetaStep] = []
    partial_sum = Fraction(0, 1)
    previous_sum: Optional[Fraction] = None
    for n in range(1, limit + 1):
        square = n * n
        term = Fraction(1, square)
        partial_sum += term
        steps.append(
            ZetaStep(
                n=n,
                square=square,
                term=term,
                partial_sum=partial_sum,
                previous_sum=previous_sum,
            )
        )
        previous_sum = partial_sum
    return steps


def primes_up_to(limit: int) -> List[int]:
    maximum = int(limit)
    primes: List[int] = []
    for candidate in range(2, maximum + 1):
        is_prime = True
        for prime in primes:
            if prime * prime > candidate:
                break
            if candidate % prime == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
    return primes


def euler_product_steps(
    max_prime: int,
    *,
    local_term_count: int,
) -> List[EulerProductStep]:
    count = int(local_term_count)
    if count < 1:
        raise ValueError("local_term_count must be >= 1")

    steps: List[EulerProductStep] = []
    partial_product = Fraction(1, 1)
    for prime in primes_up_to(int(max_prime)):
        square = prime * prime
        ratio = Fraction(1, square)
        factor = Fraction(square, square - 1)
        local_steps = geometric_series_steps(ratio, count)
        local_partial_sum = local_steps[-1].partial_sum
        local_residual = factor - local_partial_sum
        expected_residual = ratio**count / (1 - ratio)
        if local_residual != expected_residual:
            raise AssertionError("Euler-factor geometric residual identity failed")
        previous_product = partial_product
        partial_product *= factor
        steps.append(
            EulerProductStep(
                prime=prime,
                square=square,
                ratio=ratio,
                factor=factor,
                partial_product=partial_product,
                previous_product=previous_product,
                local_partial_sum=local_partial_sum,
                local_residual=local_residual,
            )
        )
    return steps


def _not_applicable(relation: str, reason: str) -> Dict[str, object]:
    return {
        "relation": relation,
        "present": False,
        "edge_count": 0,
        "status": "not_applicable",
        "blocker": reason,
    }


class SeriesGraphInspector:
    def __init__(self, conn: sqlite3.Connection, *, edge_limit: int) -> None:
        if int(edge_limit) < 2:
            raise ValueError("edge_limit must be >= 2 so commuted edge pairs can be audited")
        self.conn = conn
        self.edge_limit = int(edge_limit)
        self.evidence = GraphEvidence(conn)
        self._node_cache: Dict[Key, Dict[str, object]] = {}
        self.corpus_config = self._load_corpus_config()

    def _load_corpus_config(self) -> Dict[str, object]:
        try:
            row = self.conn.execute(
                "SELECT value FROM meta WHERE key = 'config_json'"
            ).fetchone()
        except sqlite3.OperationalError:
            return {}
        if row is None:
            return {}
        try:
            parsed = json.loads(str(row["value"]))
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _corpus_censoring(self, key: Key) -> Dict[str, object]:
        p, q = key
        reasons: List[str] = []
        max_abs_p = self.corpus_config.get("max_abs_p")
        max_abs_q = self.corpus_config.get("max_abs_q")
        max_abs_value = self.corpus_config.get("max_abs_value")
        max_stage = self.corpus_config.get("max_stage")
        if max_abs_p is not None and abs(p) > int(max_abs_p):
            reasons.append("numerator_bound_exceeded")
        if max_abs_q is not None and abs(q) > int(max_abs_q):
            reasons.append("denominator_bound_exceeded")
        if max_abs_value is not None and abs(Fraction(p, q)) > float(max_abs_value):
            reasons.append("absolute_value_bound_exceeded")
        direct_quotient_stage: Optional[int] = None
        if p >= 1 and q >= 1:
            direct_quotient_stage = max(p, q)
            if max_stage is not None and direct_quotient_stage > int(max_stage):
                reasons.append("direct_quotient_stage_beyond_corpus")
        return {
            "censored_by_config": bool(reasons),
            "reasons": reasons,
            "direct_quotient_candidate_stage": direct_quotient_stage,
            "corpus_max_stage": int(max_stage) if max_stage is not None else None,
        }

    def node(self, value: Fraction | int) -> Dict[str, object]:
        key = _key(value)
        cached = self._node_cache.get(key)
        if cached is not None:
            return cached

        payload = self.evidence.node_payload(key)
        if not bool(payload["present"]):
            payload = dict(payload)
            payload["corpus_censoring"] = self._corpus_censoring(key)
            self._node_cache[key] = payload
            return payload

        node_id = int(payload["node_id"])
        operation_counts = {"+": 0, "-": 0, "*": 0, "/": 0, "seed": 0}
        for row in self.conn.execute(
            "SELECT op, COUNT(*) AS n FROM edges "
            "WHERE result_node_id = ? GROUP BY op ORDER BY op",
            (node_id,),
        ).fetchall():
            operation_counts[str(row["op"])] = int(row["n"])

        incoming_rows = self.conn.execute(
            """
            SELECT
              e.edge_id,
              e.stage,
              e.op,
              l.label AS left_label,
              r.label AS right_label
            FROM edges e
            LEFT JOIN nodes l ON l.node_id = e.left_node_id
            LEFT JOIN nodes r ON r.node_id = e.right_node_id
            WHERE e.result_node_id = ?
            ORDER BY e.stage, e.edge_id
            LIMIT ?
            """,
            (node_id, self.edge_limit),
        ).fetchall()
        incoming_examples = [
            {
                "edge_id": int(row["edge_id"]),
                "stage": int(row["stage"]),
                "op": str(row["op"]),
                "left": row["left_label"],
                "right": row["right_label"],
            }
            for row in incoming_rows
        ]

        input_count_row = self.conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM (
              SELECT left_node_id AS input_node_id
              FROM edges
              WHERE result_node_id = ? AND left_node_id IS NOT NULL
              UNION
              SELECT right_node_id AS input_node_id
              FROM edges
              WHERE result_node_id = ? AND right_node_id IS NOT NULL
            )
            """,
            (node_id, node_id),
        ).fetchone()
        outgoing_row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM edges "
            "WHERE left_node_id = ? OR right_node_id = ?",
            (node_id, node_id),
        ).fetchone()
        derivation_events = sum(operation_counts.values())
        operation_diversity = sum(1 for count in operation_counts.values() if count > 0)
        outgoing_edges = int(outgoing_row["n"])
        only_division = derivation_events > 0 and operation_counts["/"] == derivation_events
        if outgoing_edges == 0 and only_division:
            graph_reading = "quotient_landing_only"
        elif outgoing_edges == 0:
            graph_reading = "recorded_endpoint_not_operand"
        else:
            graph_reading = "participates_as_recorded_operand"

        payload = dict(payload)
        payload["graph_evidence"] = {
            "derivation_events": derivation_events,
            "incoming_operation_counts": operation_counts,
            "incoming_operation_diversity": operation_diversity,
            "incoming_edge_examples": incoming_examples,
            "distinct_input_nodes": int(input_count_row["n"]),
            "outgoing_edge_count": outgoing_edges,
            "graph_reading": graph_reading,
        }
        self._node_cache[key] = payload
        return payload

    def direct_quotient_edge(
        self,
        value: Fraction | int,
        *,
        claim_id: str,
    ) -> Dict[str, object]:
        fraction = value if isinstance(value, Fraction) else Fraction(int(value), 1)
        return self.evidence.edge_witness(
            left=int(fraction.numerator),
            op="/",
            right=int(fraction.denominator),
            result=fraction,
            allow_commuted=False,
            claim_id=claim_id,
            relation=(
                f"{int(fraction.numerator)} / {int(fraction.denominator)} "
                f"-> {_label(fraction)}"
            ),
            edge_limit=self.edge_limit,
        )


def _edge_summary(rows: Iterable[Dict[str, object]]) -> Dict[str, object]:
    witnesses = list(rows)
    top_level_blockers = Counter(
        str(row["blocker"])
        for row in witnesses
        if not bool(row.get("present")) and row.get("blocker") is not None
    )
    stage_aperture_blockers: Counter[str] = Counter()
    relation_signatures = set()
    edge_ids = set()
    missing_node_occurrences = 0
    for row in witnesses:
        aperture = row.get("stage_aperture")
        if isinstance(aperture, dict) and aperture.get("blocker") is not None:
            stage_aperture_blockers[str(aperture["blocker"])] += 1
        missing = row.get("missing_nodes")
        if isinstance(missing, list) and missing:
            missing_node_occurrences += 1
        left = row.get("left")
        right = row.get("right")
        result = row.get("result")
        if isinstance(left, dict) and isinstance(right, dict) and isinstance(result, dict):
            relation_signatures.add(
                (
                    str(row.get("op")),
                    tuple(left.get("key", [])),
                    tuple(right.get("key", [])),
                    tuple(result.get("key", [])),
                    bool(row.get("allow_commuted")),
                )
            )
        refs = row.get("edge_refs")
        if isinstance(refs, list):
            for ref in refs:
                if isinstance(ref, dict) and ref.get("edge_id") is not None:
                    edge_ids.add(int(ref["edge_id"]))
    return {
        "step_occurrences": len(witnesses),
        "present_step_occurrences": sum(
            1 for row in witnesses if bool(row.get("present"))
        ),
        "absent_step_occurrences": sum(
            1 for row in witnesses if not bool(row.get("present"))
        ),
        "distinct_relation_signatures": len(relation_signatures),
        "distinct_present_edge_ids": len(edge_ids),
        "top_level_blockers": dict(sorted(top_level_blockers.items())),
        "stage_aperture_blockers": dict(sorted(stage_aperture_blockers.items())),
        "missing_node_step_occurrences": missing_node_occurrences,
    }


def _node_summary(nodes: Iterable[Dict[str, object]]) -> Dict[str, int]:
    payloads = list(nodes)
    present_rows = [node for node in payloads if bool(node.get("present"))]
    expected_keys = {
        tuple(node.get("key", []))
        for node in payloads
        if isinstance(node.get("key"), (list, tuple))
    }
    present_keys = {
        tuple(node.get("key", []))
        for node in present_rows
        if isinstance(node.get("key"), (list, tuple))
    }
    return {
        "row_occurrences": len(payloads),
        "present_row_occurrences": len(present_rows),
        "absent_row_occurrences": len(payloads) - len(present_rows),
        "distinct_expected_nodes": len(expected_keys),
        "distinct_present_nodes": len(present_keys),
        "distinct_absent_nodes": len(expected_keys - present_keys),
    }


def _geometric_report(
    inspector: SeriesGraphInspector,
    *,
    ratio: Fraction,
    term_count: int,
) -> Dict[str, object]:
    steps = geometric_series_steps(ratio, term_count)
    convergent = abs(ratio) < 1
    limit = Fraction(1, 1) / (1 - ratio) if convergent else None
    rows: List[Dict[str, object]] = []
    term_nodes: List[Dict[str, object]] = []
    term_edges: List[Dict[str, object]] = []
    sum_edges: List[Dict[str, object]] = []
    term_direct_edges: List[Dict[str, object]] = []
    endpoint_direct_edges: List[Dict[str, object]] = []
    endpoint_nodes: List[Dict[str, object]] = []

    for step in steps:
        term_node = inspector.node(step.term)
        endpoint_node = inspector.node(step.partial_sum)
        term_nodes.append(term_node)
        endpoint_nodes.append(endpoint_node)
        if step.previous_term is None:
            term_edge = _not_applicable("seed term 1", "initial_term")
        else:
            term_edge = inspector.evidence.edge_witness(
                left=step.previous_term,
                op="*",
                right=ratio,
                result=step.term,
                allow_commuted=True,
                claim_id="geometric_term_step",
                relation=(
                    f"{_label(step.previous_term)} * {_label(ratio)} "
                    f"-> {_label(step.term)}"
                ),
                edge_limit=inspector.edge_limit,
            )
            term_edges.append(term_edge)
        if step.previous_sum is None:
            sum_edge = _not_applicable("seed partial sum 1", "initial_partial_sum")
        else:
            sum_edge = inspector.evidence.edge_witness(
                left=step.previous_sum,
                op="+",
                right=step.term,
                result=step.partial_sum,
                allow_commuted=True,
                claim_id="geometric_partial_sum_step",
                relation=(
                    f"{_label(step.previous_sum)} + {_label(step.term)} "
                    f"-> {_label(step.partial_sum)}"
                ),
                edge_limit=inspector.edge_limit,
            )
            sum_edges.append(sum_edge)
        term_direct_edge = inspector.direct_quotient_edge(
            step.term,
            claim_id="geometric_term_direct_quotient",
        )
        endpoint_direct_edge = inspector.direct_quotient_edge(
            step.partial_sum,
            claim_id="geometric_endpoint_direct_quotient",
        )
        term_direct_edges.append(term_direct_edge)
        endpoint_direct_edges.append(endpoint_direct_edge)

        row: Dict[str, object] = {
            "index": step.index,
            "term": fraction_payload(step.term),
            "partial_sum": fraction_payload(step.partial_sum),
            "closed_form": fraction_payload(step.closed_form),
            "closed_form_matches_recurrence": step.closed_form == step.partial_sum,
            "graph": {
                "term_node": term_node,
                "partial_sum_node": endpoint_node,
                "term_step_edge": term_edge,
                "partial_sum_step_edge": sum_edge,
                "direct_term_quotient_edge": term_direct_edge,
                "direct_endpoint_quotient_edge": endpoint_direct_edge,
            },
        }
        if limit is not None:
            residual = limit - step.partial_sum
            row["signed_residual_to_projected_limit"] = fraction_payload(residual)
            row["absolute_gap_to_projected_limit"] = fraction_payload(abs(residual))
        rows.append(row)

    return {
        "family": "finite_geometric_series",
        "definition": "G_K(r) = sum_{k=0}^{K-1} r^k",
        "indexing": "term_count K includes exponents 0 through K-1",
        "ratio": fraction_payload(ratio),
        "ratio_node": inspector.node(ratio),
        "term_count": int(term_count),
        "convergent_ratio": convergent,
        "projected_limit": {
            "status": "external_exact_limit" if limit is not None else "not_convergent",
            "value": fraction_payload(limit) if limit is not None else None,
            "node": inspector.node(limit) if limit is not None else None,
            "runtime_semantics": "projection_only_not_a_completed_infinite_runtime_sum",
        },
        "summary": {
            "term_nodes": _node_summary(term_nodes),
            "partial_sum_nodes": _node_summary(endpoint_nodes),
            "direct_term_quotient_edges": _edge_summary(term_direct_edges),
            "direct_endpoint_quotient_edges": _edge_summary(endpoint_direct_edges),
            "term_step_edges": _edge_summary(term_edges),
            "partial_sum_step_edges": _edge_summary(sum_edges),
        },
        "rows": rows,
    }


def _zeta2_report(
    inspector: SeriesGraphInspector,
    *,
    max_n: int,
) -> Dict[str, object]:
    steps = zeta2_steps(max_n)
    rows: List[Dict[str, object]] = []
    square_edges: List[Dict[str, object]] = []
    term_nodes: List[Dict[str, object]] = []
    term_edges: List[Dict[str, object]] = []
    sum_edges: List[Dict[str, object]] = []
    endpoint_direct_edges: List[Dict[str, object]] = []
    endpoint_nodes: List[Dict[str, object]] = []

    for step in steps:
        square_node = inspector.node(step.square)
        term_node = inspector.node(step.term)
        endpoint_node = inspector.node(step.partial_sum)
        term_nodes.append(term_node)
        endpoint_nodes.append(endpoint_node)
        square_edge = inspector.evidence.edge_witness(
            left=step.n,
            op="*",
            right=step.n,
            result=step.square,
            allow_commuted=True,
            claim_id="zeta2_denominator_square",
            relation=f"{step.n} * {step.n} -> {step.square}",
            edge_limit=inspector.edge_limit,
        )
        square_edges.append(square_edge)
        term_edge = inspector.evidence.edge_witness(
            left=1,
            op="/",
            right=step.square,
            result=step.term,
            allow_commuted=False,
            claim_id="zeta2_reciprocal_square_term",
            relation=f"1 / {step.square} -> {_label(step.term)}",
            edge_limit=inspector.edge_limit,
        )
        term_edges.append(term_edge)
        if step.previous_sum is None:
            sum_edge = _not_applicable("seed zeta partial sum 1", "initial_partial_sum")
        else:
            sum_edge = inspector.evidence.edge_witness(
                left=step.previous_sum,
                op="+",
                right=step.term,
                result=step.partial_sum,
                allow_commuted=True,
                claim_id="zeta2_partial_sum_step",
                relation=(
                    f"{_label(step.previous_sum)} + {_label(step.term)} "
                    f"-> {_label(step.partial_sum)}"
                ),
                edge_limit=inspector.edge_limit,
            )
            sum_edges.append(sum_edge)
        endpoint_direct_edge = inspector.direct_quotient_edge(
            step.partial_sum,
            claim_id="zeta2_endpoint_direct_quotient",
        )
        endpoint_direct_edges.append(endpoint_direct_edge)
        rows.append(
            {
                "n": step.n,
                "n_squared": step.square,
                "term": fraction_payload(step.term),
                "partial_sum": fraction_payload(step.partial_sum),
                "graph": {
                    "n_squared_node": square_node,
                    "term_node": term_node,
                    "partial_sum_node": endpoint_node,
                    "square_edge": square_edge,
                    "reciprocal_square_edge": term_edge,
                    "partial_sum_step_edge": sum_edge,
                    "direct_endpoint_quotient_edge": endpoint_direct_edge,
                },
            }
        )

    return {
        "family": "finite_zeta2_partial_sums",
        "definition": "S_N = sum_{n=1}^{N} 1/n^2",
        "max_n": int(max_n),
        "projected_limit": {
            "label": "zeta(2) = pi^2/6",
            "status": "external_non_rational_projection_not_a_runtime_node",
        },
        "summary": {
            "term_nodes": _node_summary(term_nodes),
            "partial_sum_nodes": _node_summary(endpoint_nodes),
            "denominator_square_edges": _edge_summary(square_edges),
            "reciprocal_square_term_edges": _edge_summary(term_edges),
            "direct_endpoint_quotient_edges": _edge_summary(endpoint_direct_edges),
            "partial_sum_step_edges": _edge_summary(sum_edges),
        },
        "rows": rows,
    }


def _euler_product_report(
    inspector: SeriesGraphInspector,
    *,
    max_prime: int,
    local_term_count: int,
) -> Dict[str, object]:
    steps = euler_product_steps(
        max_prime,
        local_term_count=local_term_count,
    )
    rows: List[Dict[str, object]] = []
    factor_nodes: List[Dict[str, object]] = []
    square_edges: List[Dict[str, object]] = []
    ratio_edges: List[Dict[str, object]] = []
    factor_edges: List[Dict[str, object]] = []
    product_edges: List[Dict[str, object]] = []
    product_direct_edges: List[Dict[str, object]] = []
    local_direct_edges: List[Dict[str, object]] = []
    product_nodes: List[Dict[str, object]] = []
    local_nodes: List[Dict[str, object]] = []

    for step in steps:
        factor_node = inspector.node(step.factor)
        product_node = inspector.node(step.partial_product)
        local_node = inspector.node(step.local_partial_sum)
        factor_nodes.append(factor_node)
        product_nodes.append(product_node)
        local_nodes.append(local_node)
        square_edge = inspector.evidence.edge_witness(
            left=step.prime,
            op="*",
            right=step.prime,
            result=step.square,
            allow_commuted=True,
            claim_id="euler_prime_square",
            relation=f"{step.prime} * {step.prime} -> {step.square}",
            edge_limit=inspector.edge_limit,
        )
        square_edges.append(square_edge)
        ratio_edge = inspector.evidence.edge_witness(
            left=1,
            op="/",
            right=step.square,
            result=step.ratio,
            allow_commuted=False,
            claim_id="euler_factor_geometric_ratio",
            relation=f"1 / {step.square} -> {_label(step.ratio)}",
            edge_limit=inspector.edge_limit,
        )
        ratio_edges.append(ratio_edge)
        factor_edge = inspector.evidence.edge_witness(
            left=step.square,
            op="/",
            right=step.square - 1,
            result=step.factor,
            allow_commuted=False,
            claim_id="euler_factor_direct_quotient",
            relation=(
                f"{step.square} / {step.square - 1} -> {_label(step.factor)}"
            ),
            edge_limit=inspector.edge_limit,
        )
        factor_edges.append(factor_edge)
        product_edge = inspector.evidence.edge_witness(
            left=step.previous_product,
            op="*",
            right=step.factor,
            result=step.partial_product,
            allow_commuted=True,
            claim_id="euler_partial_product_step",
            relation=(
                f"{_label(step.previous_product)} * {_label(step.factor)} "
                f"-> {_label(step.partial_product)}"
            ),
            edge_limit=inspector.edge_limit,
        )
        product_edges.append(product_edge)
        product_direct_edge = inspector.direct_quotient_edge(
            step.partial_product,
            claim_id="euler_closed_factor_product_endpoint_direct_quotient",
        )
        local_direct_edge = inspector.direct_quotient_edge(
            step.local_partial_sum,
            claim_id="euler_local_geometric_endpoint_direct_quotient",
        )
        product_direct_edges.append(product_direct_edge)
        local_direct_edges.append(local_direct_edge)
        rows.append(
            {
                "prime": step.prime,
                "prime_squared": step.square,
                "factor": fraction_payload(step.factor),
                "closed_factor_partial_product": fraction_payload(step.partial_product),
                "local_geometric_expansion": {
                    "identity": "(1-p^-2)^-1 = sum_{k>=0} p^(-2k)",
                    "calculation_layer": "external_exact_rational",
                    "recurrence_edges_inspected": False,
                    "ratio": fraction_payload(step.ratio),
                    "finite_term_count": int(local_term_count),
                    "indexing": "exponents 0 through K-1",
                    "finite_partial_sum": fraction_payload(step.local_partial_sum),
                    "exact_residual_to_factor": fraction_payload(step.local_residual),
                    "factor_matches_partial_plus_residual": (
                        step.factor == step.local_partial_sum + step.local_residual
                    ),
                },
                "graph": {
                    "factor_node": factor_node,
                    "closed_factor_partial_product_node": product_node,
                    "local_geometric_partial_node": local_node,
                    "prime_square_edge": square_edge,
                    "geometric_ratio_edge": ratio_edge,
                    "direct_factor_quotient_edge": factor_edge,
                    "closed_factor_partial_product_step_edge": product_edge,
                    "direct_closed_factor_product_endpoint_quotient_edge": (
                        product_direct_edge
                    ),
                    "direct_local_endpoint_quotient_edge": local_direct_edge,
                },
            }
        )

    return {
        "family": "finite_euler_product_for_zeta2",
        "closed_factor_product_definition": (
            "P_P = product_{prime p <= P} (1-p^-2)^-1"
        ),
        "max_prime": int(max_prime),
        "primes": [step.prime for step in steps],
        "local_geometric_diagnostic_term_count": int(local_term_count),
        "projected_limit": {
            "label": "zeta(2) = pi^2/6",
            "status": "external_non_rational_projection_not_a_runtime_node",
        },
        "summary": {
            "factor_nodes": _node_summary(factor_nodes),
            "closed_factor_partial_product_nodes": _node_summary(product_nodes),
            "local_geometric_partial_nodes": _node_summary(local_nodes),
            "prime_square_edges": _edge_summary(square_edges),
            "geometric_ratio_edges": _edge_summary(ratio_edges),
            "direct_factor_quotient_edges": _edge_summary(factor_edges),
            "direct_closed_factor_product_endpoint_quotient_edges": _edge_summary(
                product_direct_edges
            ),
            "direct_local_endpoint_quotient_edges": _edge_summary(local_direct_edges),
            "closed_factor_partial_product_step_edges": _edge_summary(product_edges),
        },
        "rows": rows,
    }


def _cross_family_report(
    inspector: SeriesGraphInspector,
    *,
    geometric: Dict[str, object],
    zeta2: Dict[str, object],
    euler_product: Dict[str, object],
) -> Dict[str, object]:
    endpoints: List[Tuple[Fraction, str, str]] = []
    for row in geometric["rows"]:  # type: ignore[index]
        value = Fraction(str(row["partial_sum"]["frac"]))  # type: ignore[index]
        endpoints.append((value, "geometric", f"partial_sum_k={row['index']}"))
    for row in zeta2["rows"]:  # type: ignore[index]
        value = Fraction(str(row["partial_sum"]["frac"]))  # type: ignore[index]
        endpoints.append((value, "zeta2_sum", f"partial_sum_n={row['n']}"))
    for row in euler_product["rows"]:  # type: ignore[index]
        value = Fraction(  # type: ignore[index]
            str(row["closed_factor_partial_product"]["frac"])
        )
        endpoints.append((value, "euler_product", f"partial_product_p={row['prime']}"))

    grouped: Dict[Fraction, List[Tuple[str, str]]] = {}
    for value, family, role in endpoints:
        grouped.setdefault(value, []).append((family, role))

    collisions: List[Dict[str, object]] = []
    for value in sorted(grouped):
        roles = grouped[value]
        if len({family for family, _ in roles}) < 2:
            continue
        collisions.append(
            {
                "value": fraction_payload(value),
                "roles": [
                    {"family": family, "role": role}
                    for family, role in sorted(roles)
                ],
                "node": inspector.node(value),
                "interpretation": (
                    "shared rational endpoint only; construction alignment requires "
                    "the family-specific recurrence edges"
                ),
            }
        )

    zeta_rows: List[Dict[str, object]] = zeta2["rows"]  # type: ignore[assignment]
    euler_rows: List[Dict[str, object]] = euler_product["rows"]  # type: ignore[assignment]
    final_comparison: Optional[Dict[str, object]] = None
    if zeta_rows and euler_rows:
        zeta_final = Fraction(str(zeta_rows[-1]["partial_sum"]["frac"]))  # type: ignore[index]
        euler_final = Fraction(  # type: ignore[index]
            str(euler_rows[-1]["closed_factor_partial_product"]["frac"])
        )
        final_comparison = {
            "zeta_max_n": int(zeta2["max_n"]),
            "euler_max_prime": int(euler_product["max_prime"]),
            "zeta_partial_sum": fraction_payload(zeta_final),
            "euler_closed_factor_partial_product": fraction_payload(euler_final),
            "euler_minus_zeta": fraction_payload(euler_final - zeta_final),
            "absolute_gap": fraction_payload(abs(euler_final - zeta_final)),
            "interpretation": (
                "exact finite truncation comparison only; different cutoffs do not "
                "constitute a convergence result"
            ),
        }

    return {
        "identity_lens": (
            "zeta(2) = product_p (1-p^-2)^-1, with each factor an infinite "
            "geometric series in p^-2"
        ),
        "shared_endpoint_collisions": collisions,
        "final_finite_endpoint_comparison": final_comparison,
    }


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row is not None else None


def _corpus_payload(
    conn: sqlite3.Connection,
    *,
    alignment: Dict[str, object],
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
        "schema_version": _meta_value(conn, "schema_version"),
        "config": config,
        "latest_stage": dict(latest) if latest is not None else None,
        "nodes": int(conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()["n"]),
        "edges": int(conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()["n"]),
        "alignment": alignment,
    }


def _claim_boundary() -> Dict[str, object]:
    return {
        "evidence_layer": "external_probe_over_strict_graph",
        "claim_status": "observation",
        "allowed_claim_language": [
            "The report computes exact finite rational series and product endpoints.",
            "The report records whether each endpoint and intended construction edge exists in the selected strict corpus.",
            "A direct quotient landing is graph evidence for that rational value, not evidence for the series recurrence.",
            "Missing recurrence edges may expose the strict positive-spine operand boundary.",
        ],
        "disallowed_claim_language": [
            "Do not claim that endpoint presence means MoO constructed a geometric or zeta series.",
            "Do not claim that finite agreement constructs zeta(2), pi, or a completed infinite object.",
            "Do not treat scaled integer-division witnesses as independent series routes.",
            "Do not use this probe to authorize speculative rational operands.",
        ],
        "interpretation_limits": [
            "Every reported sum and product is finite and exactly rational.",
            "The zeta(2) and infinite geometric limits are external projection labels.",
            "Family meaning requires recorded recurrence/product edges, not value collision alone.",
            "Controls and held-out corpus comparisons are still required before promotion beyond observation.",
        ],
    }


def _validate_probe_limits(
    *,
    geometric_ratio: Fraction,
    geometric_terms: int,
    zeta_max_n: int,
    euler_max_prime: int,
    euler_local_geometric_terms: int,
    edge_limit: int,
    full_scan: bool,
) -> None:
    if int(geometric_terms) < 1:
        raise ValueError("geometric_terms must be >= 1")
    if int(zeta_max_n) < 1:
        raise ValueError("zeta_max_n must be >= 1")
    if int(euler_max_prime) < 2:
        raise ValueError("euler_max_prime must be >= 2")
    if int(euler_local_geometric_terms) < 1:
        raise ValueError("euler_local_geometric_terms must be >= 1")
    if int(edge_limit) < 2:
        raise ValueError("edge_limit must be >= 2")
    if full_scan:
        return

    over_limit: List[str] = []
    if int(geometric_terms) > MAX_GEOMETRIC_TERMS:
        over_limit.append(f"geometric_terms>{MAX_GEOMETRIC_TERMS}")
    if int(zeta_max_n) > MAX_ZETA_N:
        over_limit.append(f"zeta_max_n>{MAX_ZETA_N}")
    if int(euler_max_prime) > MAX_EULER_PRIME:
        over_limit.append(f"euler_max_prime>{MAX_EULER_PRIME}")
    if int(euler_local_geometric_terms) > MAX_EULER_LOCAL_TERMS:
        over_limit.append(
            f"euler_local_geometric_terms>{MAX_EULER_LOCAL_TERMS}"
        )
    if max(
        geometric_ratio.numerator.bit_length(),
        geometric_ratio.denominator.bit_length(),
    ) > MAX_RATIO_COMPONENT_BITS:
        over_limit.append(
            f"geometric_ratio_component_bits>{MAX_RATIO_COMPONENT_BITS}"
        )
    if over_limit:
        raise ValueError(
            "probe safety limit exceeded ("
            + ", ".join(over_limit)
            + "); pass --full-scan to acknowledge the larger exact calculation"
        )


def series_probe(
    *,
    db_path: Path,
    geometric_ratio: Fraction,
    geometric_terms: int,
    zeta_max_n: int,
    euler_max_prime: int,
    euler_local_geometric_terms: int,
    edge_limit: int,
    full_scan: bool = False,
) -> Dict[str, object]:
    _validate_probe_limits(
        geometric_ratio=geometric_ratio,
        geometric_terms=geometric_terms,
        zeta_max_n=zeta_max_n,
        euler_max_prime=euler_max_prime,
        euler_local_geometric_terms=euler_local_geometric_terms,
        edge_limit=edge_limit,
        full_scan=full_scan,
    )
    with closing(connect_readonly(Path(db_path))) as conn:
        alignment = require_strict_alignment(conn)
        inspector = SeriesGraphInspector(conn, edge_limit=edge_limit)
        geometric = _geometric_report(
            inspector,
            ratio=geometric_ratio,
            term_count=geometric_terms,
        )
        zeta2 = _zeta2_report(inspector, max_n=zeta_max_n)
        euler_product = _euler_product_report(
            inspector,
            max_prime=euler_max_prime,
            local_term_count=euler_local_geometric_terms,
        )
        cross_family = _cross_family_report(
            inspector,
            geometric=geometric,
            zeta2=zeta2,
            euler_product=euler_product,
        )
        corpus = _corpus_payload(conn, alignment=alignment)

    return {
        "report_type": "exact_finite_series_graph_probe",
        "config": {
            "geometric_ratio": fraction_payload(geometric_ratio),
            "geometric_terms": int(geometric_terms),
            "zeta_max_n": int(zeta_max_n),
            "euler_max_prime": int(euler_max_prime),
            "euler_local_geometric_terms": int(euler_local_geometric_terms),
            "edge_limit": int(edge_limit),
            "full_scan": bool(full_scan),
        },
        "claim_boundary": _claim_boundary(),
        "corpus": corpus,
        "geometric": geometric,
        "zeta2": zeta2,
        "euler_product": euler_product,
        "cross_family": cross_family,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect exact finite geometric, zeta(2), and Euler-product families "
            "against a strict MoO graph corpus."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--geometric-ratio", type=_fraction_arg, default=Fraction(1, 2))
    parser.add_argument("--geometric-terms", type=positive_int, default=5)
    parser.add_argument("--zeta-max-n", type=positive_int, default=5)
    parser.add_argument("--euler-max-prime", type=_at_least_two_int, default=7)
    parser.add_argument(
        "--euler-local-geometric-terms",
        "--euler-factor-terms",
        dest="euler_local_geometric_terms",
        type=positive_int,
        default=4,
        help=(
            "Diagnostic finite depth for each factor's local geometric expansion; "
            "the closed-factor Euler product itself is not truncated by this value."
        ),
    )
    parser.add_argument("--edge-limit", type=_at_least_two_int, default=3)
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help="Acknowledge exact-calculation sizes above the default safety caps.",
    )
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--write",
        type=Path,
        help="Also write the JSON report. Existing files are never overwritten.",
    )
    parser.add_argument("--experiment-id")
    parser.add_argument(
        "--with-checksums",
        action="store_true",
        help="Include SHA-256 hashes for the corpus DB and probe tool.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        payload = series_probe(
            db_path=Path(args.db),
            geometric_ratio=args.geometric_ratio,
            geometric_terms=int(args.geometric_terms),
            zeta_max_n=int(args.zeta_max_n),
            euler_max_prime=int(args.euler_max_prime),
            euler_local_geometric_terms=int(args.euler_local_geometric_terms),
            edge_limit=int(args.edge_limit),
            full_scan=bool(args.full_scan),
        )
    except ValueError as exc:
        parser.error(str(exc))
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_series_probe.v2",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
