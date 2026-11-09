from __future__ import annotations

import argparse
import cmath
import json
import math
import sqlite3
from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

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
TARGET_KINDS = {
    "user_supplied_reference_zero",
    "numerical_candidate",
    "control",
}
MAX_HASSE_TERMS = 64
HARD_MAX_HASSE_TERMS = 256
MAX_PASCAL_ROW = 16
HARD_MAX_PASCAL_ROW = 66
MAX_PHASE_DENOMINATOR = 512
HARD_MAX_PHASE_DENOMINATOR = 2_147_483_647
MAX_PHASE_SAMPLE_TERMS = 64
MAX_ABS_SIGMA = 8.0
MAX_ABS_T = 100.0
ETA_BRIDGE_GUARD = 1e-10
NEAR_POLE_RADIUS = 1e-8
DEFAULT_STABILITY_TOLERANCE = 1e-12
BINARY64_EPSILON = 2.0**-52
ZETA2_CONTROL_TOLERANCE = 1e-12
TRIVIAL_ZERO_CONTROL_TOLERANCE = 1e-10


@dataclass(frozen=True)
class HasseApproximation:
    s: complex
    terms: int
    eta: complex
    bridge_denominator: complex
    zeta: Optional[complex]
    status: str
    source_weights: Tuple[Fraction, ...]
    source_powers: Tuple[complex, ...]
    source_contributions: Tuple[complex, ...]
    absolute_contribution_mass: float
    cancellation_ratio: Optional[float]


def _key(value: Fraction | int) -> Key:
    fraction = value if isinstance(value, Fraction) else Fraction(int(value), 1)
    return normalize_key(int(fraction.numerator), int(fraction.denominator))


def fraction_payload(value: Fraction | int) -> Dict[str, object]:
    fraction = value if isinstance(value, Fraction) else Fraction(int(value), 1)
    key = _key(fraction)
    return {
        "frac": format_key(key),
        "p": int(key[0]),
        "q": int(key[1]),
    }


def complex_payload(value: Optional[complex]) -> Dict[str, object]:
    if value is None:
        return {
            "available": False,
            "real": None,
            "imag": None,
            "magnitude": None,
            "phase_turns": None,
        }
    real = float(value.real)
    imag = float(value.imag)
    magnitude = float(abs(value))
    if not all(math.isfinite(item) for item in (real, imag, magnitude)):
        return {
            "available": False,
            "real": None,
            "imag": None,
            "magnitude": None,
            "phase_turns": None,
            "reason": "non_finite_binary64_value",
        }
    phase_turns = None
    if magnitude > 0.0:
        phase_turns = float((math.atan2(imag, real) / (2.0 * math.pi)) % 1.0)
    return {
        "available": True,
        "real": real,
        "imag": imag,
        "magnitude": magnitude,
        "phase_turns": phase_turns,
    }


def complex_input_payload(value: complex) -> Dict[str, object]:
    sigma = float(value.real)
    t = float(value.imag)
    return {
        "sigma": sigma,
        "t": t,
        "sigma_binary64_hex": sigma.hex(),
        "t_binary64_hex": t.hex(),
    }


def _sum_complex(values: Sequence[complex]) -> complex:
    return complex(
        math.fsum(value.real for value in values),
        math.fsum(value.imag for value in values),
    )


@lru_cache(maxsize=None)
def hasse_source_weights(terms: int) -> Tuple[Fraction, ...]:
    """Return exact finite Hasse weights regrouped by the integer source j+1."""

    count = int(terms)
    if count < 1:
        raise ValueError("terms must be >= 1")
    weights: List[Fraction] = []
    for j in range(count):
        unsigned = sum(
            (
                Fraction(math.comb(k, j), 2 ** (k + 1))
                for k in range(j, count)
            ),
            Fraction(0, 1),
        )
        weights.append(unsigned if j % 2 == 0 else -unsigned)
    return tuple(weights)


def hasse_zeta(
    s: complex,
    terms: int,
    *,
    bridge_guard: float = ETA_BRIDGE_GUARD,
) -> HasseApproximation:
    """Evaluate a binary64 finite Hasse/eta approximation to zeta(s)."""

    point = complex(s)
    if not all(math.isfinite(item) for item in (point.real, point.imag)):
        raise ValueError("s must have finite real and imaginary components")
    if int(terms) < 1:
        raise ValueError("terms must be >= 1")
    if not math.isfinite(float(bridge_guard)) or float(bridge_guard) <= 0.0:
        raise ValueError("bridge_guard must be a finite positive number")

    weights = hasse_source_weights(int(terms))
    powers = tuple(
        cmath.exp(-point * math.log(source))
        for source in range(1, int(terms) + 1)
    )
    contributions = tuple(
        float(weight) * power for weight, power in zip(weights, powers)
    )
    eta = _sum_complex(contributions)
    bridge = 1.0 - cmath.exp((1.0 - point) * math.log(2.0))
    absolute_mass = float(math.fsum(abs(value) for value in contributions))
    cancellation_ratio = (
        float(abs(eta) / absolute_mass) if absolute_mass > 0.0 else None
    )

    finite = all(
        math.isfinite(item)
        for item in (
            eta.real,
            eta.imag,
            bridge.real,
            bridge.imag,
            absolute_mass,
        )
    )
    if not finite:
        status = "non_finite_binary64_evaluation"
        zeta = None
    elif abs(point - 1.0) < NEAR_POLE_RADIUS:
        status = "zeta_pole_neighborhood_guard"
        zeta = None
    elif abs(bridge) <= float(bridge_guard):
        status = "eta_bridge_removable_singularity_guard"
        zeta = None
    else:
        zeta = eta / bridge
        if not all(math.isfinite(item) for item in (zeta.real, zeta.imag)):
            status = "non_finite_binary64_evaluation"
            zeta = None
        else:
            status = "finite_external_approximation"

    return HasseApproximation(
        s=point,
        terms=int(terms),
        eta=eta,
        bridge_denominator=bridge,
        zeta=zeta,
        status=status,
        source_weights=weights,
        source_powers=powers,
        source_contributions=contributions,
        absolute_contribution_mass=absolute_mass,
        cancellation_ratio=cancellation_ratio,
    )


def approximation_payload(
    approximation: HasseApproximation,
) -> Dict[str, object]:
    bridge_magnitude = float(abs(approximation.bridge_denominator))
    roundoff_proxy = (
        float(
            BINARY64_EPSILON
            * approximation.absolute_contribution_mass
            / bridge_magnitude
        )
        if bridge_magnitude > 0.0
        else None
    )
    return {
        "s": complex_input_payload(approximation.s),
        "hasse_terms": int(approximation.terms),
        "source_term_count": len(approximation.source_weights),
        "triangle_cell_count": int(
            approximation.terms * (approximation.terms + 1) // 2
        ),
        "status": approximation.status,
        "eta_numerator": complex_payload(approximation.eta),
        "eta_bridge_denominator": complex_payload(
            approximation.bridge_denominator
        ),
        "zeta": complex_payload(approximation.zeta),
        "absolute_contribution_mass": float(
            approximation.absolute_contribution_mass
        ),
        "eta_to_absolute_mass_ratio": approximation.cancellation_ratio,
        "binary64_roundoff_proxy": roundoff_proxy,
        "roundoff_proxy_status": (
            "conditioning_indicator_only_not_a_rigorous_error_bound"
        ),
        "eta_bridge_amplification": (
            float(1.0 / bridge_magnitude) if bridge_magnitude > 0.0 else None
        ),
        "cancellation_reading": (
            "small ratios indicate strong finite weighted cancellation; this is not an error bound"
        ),
    }


def _default_ladder(terms: int) -> List[int]:
    count = int(terms)
    candidates = [
        max(1, count // 2),
        max(1, count - 16),
        max(1, count - 8),
        max(1, count - 4),
        count,
    ]
    return sorted(set(candidates))


def recommended_hasse_terms(t: float) -> int:
    """Return an empirical binary64 preflight cutoff, rounded up to eight."""

    raw = max(64, int(math.ceil(1.6 * abs(float(t)) + 40.0)))
    return int(((raw + 7) // 8) * 8)


def _ladder_report(s: complex, checkpoints: Sequence[int]) -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    previous: Optional[complex] = None
    for terms in checkpoints:
        approximation = hasse_zeta(s, int(terms))
        row = approximation_payload(approximation)
        change = (
            float(abs(approximation.zeta - previous))
            if approximation.zeta is not None and previous is not None
            else None
        )
        row["change_from_previous_zeta"] = change
        rows.append(row)
        if approximation.zeta is not None:
            previous = approximation.zeta
    terminal_change = rows[-1]["change_from_previous_zeta"] if rows else None
    return {
        "checkpoints": [int(value) for value in checkpoints],
        "rows": rows,
        "terminal_change": terminal_change,
        "stability_status": "empirical_cutoff_comparison_not_error_bound",
    }


class CriticalGraphInspector:
    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        corpus_stage: Optional[int],
        edge_limit: int,
    ) -> None:
        self.conn = conn
        self.evidence = GraphEvidence(conn, corpus_stage=corpus_stage)
        self.edge_limit = int(edge_limit)
        self._node_cache: Dict[Key, Dict[str, object]] = {}

    def node(self, value: Fraction | int) -> Dict[str, object]:
        key = _key(value)
        cached = self._node_cache.get(key)
        if cached is not None:
            return dict(cached)
        payload = self.evidence.node_payload(key)
        if not bool(payload["present"]):
            payload["graph_reading"] = "not_present_in_selected_corpus"
            self._node_cache[key] = dict(payload)
            return payload

        node_id = int(payload["node_id"])
        incoming = self.conn.execute(
            """
            SELECT
              COUNT(*) AS total,
              COALESCE(SUM(CASE WHEN op = '+' THEN 1 ELSE 0 END), 0) AS plus_count,
              COALESCE(SUM(CASE WHEN op = '-' THEN 1 ELSE 0 END), 0) AS minus_count,
              COALESCE(SUM(CASE WHEN op = '*' THEN 1 ELSE 0 END), 0) AS multiply_count,
              COALESCE(SUM(CASE WHEN op = '/' THEN 1 ELSE 0 END), 0) AS divide_count,
              COALESCE(SUM(CASE WHEN op = 'seed' THEN 1 ELSE 0 END), 0) AS seed_count
            FROM edges
            WHERE result_node_id = ?
            """,
            (node_id,),
        ).fetchone()
        outgoing = self.conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM edges
            WHERE left_node_id = ? OR right_node_id = ?
            """,
            (node_id, node_id),
        ).fetchone()
        payload["incoming_edge_count"] = int(incoming["total"])
        payload["incoming_operation_counts"] = {
            "+": int(incoming["plus_count"]),
            "-": int(incoming["minus_count"]),
            "*": int(incoming["multiply_count"]),
            "/": int(incoming["divide_count"]),
            "seed": int(incoming["seed_count"]),
        }
        payload["outgoing_edge_count"] = int(outgoing["total"])
        status = str(payload["status"])
        confirmed_stage = payload.get("confirmed_stage")
        corpus_stage = self.evidence.corpus_stage
        operand_ready = bool(
            status == "certainty"
            or (
                confirmed_stage is not None
                and corpus_stage is not None
                and int(confirmed_stage) <= int(corpus_stage)
            )
        )
        payload["operand_ready_at_corpus_stage"] = operand_ready
        payload["operand_readiness_corpus_stage"] = corpus_stage
        if operand_ready:
            payload["graph_reading"] = "positive_spine_operand_available"
        elif status == "speculative_until_confirmed":
            payload["graph_reading"] = (
                "positive_integer_present_awaiting_core_confirmation"
            )
        elif int(outgoing["total"]) == 0:
            payload["graph_reading"] = "speculative_landing_not_operand"
        else:
            payload["graph_reading"] = "speculative_node_with_outgoing_edges"
        self._node_cache[key] = dict(payload)
        return payload

    def edge(
        self,
        *,
        left: Fraction | int,
        op: str,
        right: Fraction | int,
        result: Fraction | int,
        allow_commuted: bool,
        claim_id: str,
        relation: str,
    ) -> Dict[str, object]:
        return self.evidence.edge_witness(
            left=left,
            op=op,
            right=right,
            result=result,
            allow_commuted=allow_commuted,
            claim_id=claim_id,
            relation=relation,
            edge_limit=self.edge_limit,
        )


def _compact_edge(payload: Dict[str, object]) -> Dict[str, object]:
    return {
        "claim_id": payload.get("claim_id"),
        "relation": payload.get("relation"),
        "present": bool(payload["present"]),
        "status": str(payload["status"]),
        "edge_count": int(payload["edge_count"]),
        "expected_directed_edges": int(payload["expected_directed_edges"]),
        "first_edge_stage": payload["first_edge_stage"],
        "edge_refs": list(payload["edge_refs"]),
        "blocker": payload["blocker"],
        "missing_nodes": list(payload["missing_nodes"]),
        "candidate_stage": payload["candidate_stage"],
        "corpus_stage": payload["corpus_stage"],
        "eligible_by_stage": bool(payload["eligible_by_stage"]),
        "stage_aperture": dict(payload["stage_aperture"]),
    }


def _node_summary(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    distinct: Dict[Tuple[int, int], Dict[str, object]] = {}
    for row in rows:
        distinct[(int(row["p"]), int(row["q"]))] = row
    status_counts = Counter(
        str(row.get("status", "missing")) if bool(row["present"]) else "missing"
        for row in rows
    )
    present_distinct = sum(bool(row["present"]) for row in distinct.values())
    operand_ready_distinct = sum(
        bool(row.get("operand_ready_at_corpus_stage", False))
        for row in distinct.values()
    )
    return {
        "row_occurrences": len(rows),
        "distinct_expected_nodes": len(distinct),
        "present_row_occurrences": sum(bool(row["present"]) for row in rows),
        "present_distinct_nodes": int(present_distinct),
        "missing_distinct_nodes": len(distinct) - int(present_distinct),
        "operand_ready_row_occurrences": sum(
            bool(row.get("operand_ready_at_corpus_stage", False)) for row in rows
        ),
        "operand_ready_distinct_nodes": int(operand_ready_distinct),
        "present_not_operand_ready_distinct_nodes": int(present_distinct)
        - int(operand_ready_distinct),
        "status_counts_by_row": dict(sorted(status_counts.items())),
    }


def _edge_summary(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    blockers = Counter(
        str(row["blocker"])
        for row in rows
        if not bool(row["present"]) and row["blocker"] is not None
    )
    edge_ids = {
        int(ref["edge_id"])
        for row in rows
        for ref in row["edge_refs"]  # type: ignore[index]
    }
    stage_aperture_blockers = Counter(
        str(row["stage_aperture"]["blocker"])  # type: ignore[index]
        for row in rows
        if isinstance(row.get("stage_aperture"), dict)
        and row["stage_aperture"].get("blocker") is not None  # type: ignore[union-attr]
    )
    missing_node_occurrences = sum(bool(row["missing_nodes"]) for row in rows)
    relation_signatures = {
        (str(row.get("claim_id")), str(row.get("relation"))) for row in rows
    }
    return {
        "relation_occurrences": len(rows),
        "present_relation_occurrences": sum(bool(row["present"]) for row in rows),
        "complete_directed_occurrences": sum(
            str(row["status"]) == "complete_directed" for row in rows
        ),
        "absent_relation_occurrences": sum(not bool(row["present"]) for row in rows),
        "distinct_relation_signatures": len(relation_signatures),
        "distinct_present_edge_ids": len(edge_ids),
        "top_level_blockers": dict(sorted(blockers.items())),
        "stage_aperture_blockers": dict(sorted(stage_aperture_blockers.items())),
        "missing_node_relation_occurrences": int(missing_node_occurrences),
    }


def _phase_fraction(value: Fraction) -> Fraction:
    return Fraction(int(value.numerator) % int(value.denominator), value.denominator)


def _complex_calibration(inspector: CriticalGraphInspector) -> Dict[str, object]:
    quarter = Fraction(1, 4)
    orbit = [
        (Fraction(0, 1), "1"),
        (Fraction(1, 4), "i"),
        (Fraction(1, 2), "-1"),
        (Fraction(3, 4), "-i"),
    ]
    phase_nodes = [inspector.node(phase) for phase, _ in orbit]
    addition_rows: List[Dict[str, object]] = []
    for phase, label in orbit:
        raw_result = phase + quarter
        quotient_result = _phase_fraction(raw_result)
        witness = inspector.edge(
            left=phase,
            op="+",
            right=quarter,
            result=raw_result,
            allow_commuted=True,
            claim_id="quarter_turn_phase_step",
            relation=(
                f"{format_key(_key(phase))} + 1/4 -> "
                f"{format_key(_key(raw_result))}"
            ),
        )
        addition_rows.append(
            {
                "from_phase": fraction_payload(phase),
                "from_u1_label": label,
                "added_phase": fraction_payload(quarter),
                "raw_rational_sum": fraction_payload(raw_result),
                "quotient_phase": fraction_payload(quotient_result),
                "graph": _compact_edge(witness),
            }
        )

    quotient_witness = inspector.edge(
        left=1,
        op="/",
        right=4,
        result=quarter,
        allow_commuted=False,
        claim_id="quarter_turn_direct_quotient",
        relation="1 / 4 -> 1/4",
    )
    rational_multiply = inspector.edge(
        left=quarter,
        op="*",
        right=quarter,
        result=Fraction(1, 16),
        allow_commuted=True,
        claim_id="rational_multiplication_contrast",
        relation="1/4 * 1/4 -> 1/16",
    )
    exact_complex_orbit = [1 + 0j, 0 + 1j, -1 + 0j, 0 - 1j]
    complex_sum = _sum_complex(exact_complex_orbit)
    return {
        "representation_status": "external_phase_and_pair_views_not_runtime_complex_number",
        "unit_modulus_meaning": "absolute value 1 in U(1), not the one-class integer quotient Z/1Z",
        "quarter_turn": {
            "phase": fraction_payload(quarter),
            "external_map": "exp(2*pi*i*1/4)",
            "external_identity": "i",
            "graph_node": inspector.node(quarter),
            "direct_quotient_witness": _compact_edge(quotient_witness),
        },
        "c4_orbit": {
            "phase_points": [
                {
                    "phase": fraction_payload(phase),
                    "external_u1_label": label,
                    "graph_node": node,
                }
                for (phase, label), node in zip(orbit, phase_nodes)
            ],
            "external_exact_sum": "1 + i - 1 - i = 0",
            "binary64_sum_check": complex_payload(complex_sum),
            "phase_addition_edges": addition_rows,
            "phase_addition_edge_summary": _edge_summary(
                [row["graph"] for row in addition_rows]  # type: ignore[list-item]
            ),
        },
        "i_squared_calibration": {
            "external_phase_relation": "1/4 + 1/4 = 1/2 mod 1",
            "external_complex_relation": "i * i = -1",
            "graph_phase_addition": addition_rows[1]["graph"],
            "runtime_status": "not_a_graph_witnessed_complex_multiplication",
        },
        "rational_multiplication_contrast": {
            "meaning": (
                "Core rational multiplication of 1/4 by 1/4 targets 1/16; it must not be aliased to i*i."
            ),
            "graph": _compact_edge(rational_multiply),
        },
        "gaussian_pair_view": {
            "external_pair": {"real": 0, "imag": 1},
            "external_norm_squared": 1,
            "real_component_node": inspector.node(0),
            "imaginary_component_node": inspector.node(1),
            "pair_is_runtime_node": False,
            "phase_to_pair_projection_edge": {
                "present": False,
                "reason": "the rational graph has no domain-tagged complex pair or projection-edge type",
            },
        },
    }


def _nearest_phase_fraction(turns: float, max_denominator: int) -> Tuple[Fraction, float]:
    unwrapped = Fraction(float(turns)).limit_denominator(int(max_denominator))
    nearest = _phase_fraction(unwrapped)
    error = abs(((float(turns) - float(nearest) + 0.5) % 1.0) - 0.5)
    return nearest, float(error)


def _source_audit(
    inspector: CriticalGraphInspector,
    approximation: HasseApproximation,
    *,
    phase_max_denominator: int,
    phase_sample_terms: int,
) -> Dict[str, object]:
    source_rows: List[Dict[str, object]] = []
    index_nodes: List[Dict[str, object]] = []
    reciprocal_nodes: List[Dict[str, object]] = []
    reciprocal_edges: List[Dict[str, object]] = []
    phase_nodes: List[Dict[str, object]] = []

    for offset, (weight, power, contribution) in enumerate(
        zip(
            approximation.source_weights,
            approximation.source_powers,
            approximation.source_contributions,
        )
    ):
        source = offset + 1
        index_node = inspector.node(source)
        reciprocal = Fraction(1, source)
        reciprocal_node = inspector.node(reciprocal)
        reciprocal_edge = _compact_edge(
            inspector.edge(
                left=1,
                op="/",
                right=source,
                result=reciprocal,
                allow_commuted=False,
                claim_id="hasse_source_reciprocal_precursor",
                relation=f"1 / {source} -> {format_key(_key(reciprocal))}",
            )
        )
        row: Dict[str, object] = {
            "source_integer": source,
            "hasse_triangle_occurrences": int(approximation.terms - source + 1),
            "exact_regrouped_weight": fraction_payload(weight),
            "external_complex_power": {
                "formula": f"{source}^(-s)",
                "value": complex_payload(power),
                "calculation_layer": "external_binary64_complex",
                "runtime_node": False,
            },
            "external_weighted_contribution": complex_payload(contribution),
            "graph": {
                "index_node": index_node,
                "reciprocal_precursor_node": reciprocal_node,
                "reciprocal_precursor_edge": reciprocal_edge,
                "complex_power_edge_present": False,
                "complex_power_edge_absence_reason": (
                    "the runtime has no logarithm, complex exponentiation, or complex-value node domain"
                ),
            },
        }
        if source <= int(phase_sample_terms):
            payload = complex_payload(contribution)
            turns = payload["phase_turns"]
            if turns is not None:
                nearest, error = _nearest_phase_fraction(
                    float(turns), int(phase_max_denominator)
                )
                phase_node = inspector.node(nearest)
                phase_nodes.append(phase_node)
                row["phase_projection"] = {
                    "external_binary64_turns": float(turns),
                    "nearest_rational_phase": fraction_payload(nearest),
                    "max_denominator": int(phase_max_denominator),
                    "circular_error_turns": float(error),
                    "graph_node": phase_node,
                    "selection_is_graph_native": False,
                }
        source_rows.append(row)
        index_nodes.append(index_node)
        reciprocal_nodes.append(reciprocal_node)
        reciprocal_edges.append(reciprocal_edge)

    phase_summary = _node_summary(phase_nodes)
    phase_summary.update(
        {
            "evidence_status": "visualization_only_not_construction_evidence",
            "reading": (
                "post_hoc nearest rational phases; node presence does not witness "
                "the external complex phase or its construction"
            ),
        }
    )
    return {
        "source_relation": (
            "exact finite Hasse weight A_(K,n) times external complex power n^(-s)"
        ),
        "finite_regrouping": (
            "A_(K,n) = (-1)^(n-1) * sum_{k=n-1}^{K-1} C(k,n-1)/2^(k+1)"
        ),
        "complex_term_is_runtime_node": False,
        "reciprocal_is_only_a_rational_precursor": True,
        "summary": {
            "index_nodes": _node_summary(index_nodes),
            "reciprocal_precursor_nodes": _node_summary(reciprocal_nodes),
            "reciprocal_precursor_edges": _edge_summary(reciprocal_edges),
            "sampled_phase_approximation_nodes": phase_summary,
        },
        "rows": source_rows,
        "unrepresented_runtime_operations": [
            "domain-tagged complex numbers",
            "logarithm",
            "real or complex exponentiation",
            "complex accumulation",
            "analytic continuation",
        ],
    }


def _pascal_audit(
    inspector: CriticalGraphInspector,
    *,
    requested_max_row: int,
    required_max_row: int,
) -> Dict[str, object]:
    audited_max_row = min(int(requested_max_row), int(required_max_row))
    rows: List[Dict[str, object]] = []
    edges: List[Dict[str, object]] = []
    for n in range(2, audited_max_row + 1):
        for k in range(1, n):
            left = math.comb(n - 1, k - 1)
            right = math.comb(n - 1, k)
            result = math.comb(n, k)
            edge = _compact_edge(
                inspector.edge(
                    left=left,
                    op="+",
                    right=right,
                    result=result,
                    allow_commuted=True,
                    claim_id="hasse_pascal_coefficient_recurrence",
                    relation=f"{left} + {right} -> {result}",
                )
            )
            rows.append(
                {
                    "pascal_row": n,
                    "position": k,
                    "left_coefficient": left,
                    "right_coefficient": right,
                    "result_coefficient": result,
                    "identity_holds": left + right == result,
                    "graph": edge,
                }
            )
            edges.append(edge)
    return {
        "role": (
            "sample interior Pascal recurrences that underlie externally computed "
            "exact Hasse coefficients"
        ),
        "calculation_layer": "exact_integer_identity_audited_against_strict_graph",
        "boundary_coefficients": {
            "identity": "C(n,0) = C(n,n) = 1",
            "graph_node_for_one": inspector.node(1),
            "required_rows_including_row_zero": int(required_max_row) + 1,
            "status": "coefficient_identity_external_node_one_graph_audited",
        },
        "required_max_pascal_row": int(required_max_row),
        "requested_max_pascal_row": int(requested_max_row),
        "audited_max_pascal_row": int(audited_max_row),
        "coverage_status": (
            "complete_required_interior_recurrence_coverage"
            if audited_max_row >= int(required_max_row)
            else "named_interior_recurrence_sample_only"
        ),
        "summary": _edge_summary(edges),
        "rows": rows,
    }


def _controls(
    target: HasseApproximation,
    *,
    control_delta: float,
) -> Dict[str, object]:
    terms = int(target.terms)
    zeta2 = hasse_zeta(2.0 + 0.0j, terms)
    zeta2_reference = float(math.pi * math.pi / 6.0)
    zeta2_error = (
        float(abs(zeta2.zeta - zeta2_reference))
        if zeta2.zeta is not None
        else None
    )
    trivial = hasse_zeta(-2.0 + 0.0j, terms)
    pole = hasse_zeta(1.0 + 0.0j, terms)
    removable_bridge_point = complex(1.0, 2.0 * math.pi / math.log(2.0))
    removable_bridge = hasse_zeta(removable_bridge_point, terms)
    conjugate = hasse_zeta(target.s.conjugate(), terms)
    conjugate_error = (
        float(abs(conjugate.zeta - target.zeta.conjugate()))
        if conjugate.zeta is not None and target.zeta is not None
        else None
    )
    lower = hasse_zeta(
        complex(target.s.real, target.s.imag - float(control_delta)), terms
    )
    upper = hasse_zeta(
        complex(target.s.real, target.s.imag + float(control_delta)), terms
    )
    left = hasse_zeta(
        complex(target.s.real - float(control_delta), target.s.imag), terms
    )
    right = hasse_zeta(
        complex(target.s.real + float(control_delta), target.s.imag), terms
    )
    zeta2_pass = bool(
        zeta2_error is not None and zeta2_error <= ZETA2_CONTROL_TOLERANCE
    )
    trivial_residual = (
        float(abs(trivial.zeta)) if trivial.zeta is not None else None
    )
    trivial_pass = bool(
        trivial_residual is not None
        and trivial_residual <= TRIVIAL_ZERO_CONTROL_TOLERANCE
    )
    pole_pass = pole.status == "zeta_pole_neighborhood_guard"
    removable_bridge_pass = (
        removable_bridge.status == "eta_bridge_removable_singularity_guard"
    )
    calibration_suite_pass = bool(
        zeta2_pass and trivial_pass and pole_pass and removable_bridge_pass
    )
    return {
        "zeta2_convergent_region_calibration": {
            "evaluation": approximation_payload(zeta2),
            "external_reference": {
                "label": "pi^2/6",
                "binary64_value": zeta2_reference,
            },
            "absolute_error": zeta2_error,
            "pass_tolerance": ZETA2_CONTROL_TOLERANCE,
            "passes": zeta2_pass,
            "cross_lens_note": (
                "moo_series_probe.py separately audits exact finite rational zeta(2) partial sums"
            ),
        },
        "trivial_zero_calibration": {
            "evaluation": approximation_payload(trivial),
            "expected_external_value": "zeta(-2) = 0 by analytic continuation",
            "absolute_residual": trivial_residual,
            "pass_tolerance": TRIVIAL_ZERO_CONTROL_TOLERANCE,
            "passes": trivial_pass,
            "certified_by_this_probe": False,
        },
        "pole_guard": {
            "evaluation": approximation_payload(pole),
            "expected_external_behavior": "zeta has a pole at s=1",
            "guard_triggered": pole_pass,
        },
        "eta_bridge_removable_singularity_guard": {
            "evaluation": approximation_payload(removable_bridge),
            "input_formula": "s = 1 + 2*pi*i/log(2)",
            "expected_external_behavior": (
                "the eta quotient has a removable 0/0 representation here; "
                "this is not a zeta pole"
            ),
            "guard_triggered": removable_bridge_pass,
        },
        "conjugate_symmetry": {
            "evaluation_at_conjugate_s": approximation_payload(conjugate),
            "expected_relation": "zeta(conjugate(s)) = conjugate(zeta(s))",
            "absolute_error": conjugate_error,
            "binary64_check_only": True,
            "independent_accuracy_validation": False,
            "reading": (
                "same-algorithm real-coefficient consistency check only"
            ),
        },
        "nearby_cross_controls": {
            "delta": float(control_delta),
            "lower_t": approximation_payload(lower),
            "upper_t": approximation_payload(upper),
            "lower_sigma": approximation_payload(left),
            "upper_sigma": approximation_payload(right),
            "geometry": "vertical_and_horizontal_cross_around_target",
        },
        "calibration_suite": {
            "passes": calibration_suite_pass,
            "status": "pass" if calibration_suite_pass else "fail",
            "required_checks": [
                "zeta2_convergent_region_calibration",
                "trivial_zero_calibration",
                "pole_guard",
                "eta_bridge_removable_singularity_guard",
            ],
            "conjugate_symmetry_is_independent_requirement": False,
        },
    }


def _target_evaluation(
    target: HasseApproximation,
    *,
    target_kind: str,
    target_label: Optional[str],
    near_zero_tolerance: float,
    stability_tolerance: float,
    ladder_terms: Sequence[int],
) -> Dict[str, object]:
    payload = approximation_payload(target)
    residual = float(abs(target.zeta)) if target.zeta is not None else None
    below = residual is not None and residual <= float(near_zero_tolerance)
    ladder = _ladder_report(target.s, ladder_terms)
    change_values = [
        float(row["change_from_previous_zeta"])
        for row in ladder["rows"]  # type: ignore[union-attr]
        if row["change_from_previous_zeta"] is not None
    ]
    terminal_changes = change_values[-2:]
    stability_scale = 1.0 + (float(abs(target.zeta)) if target.zeta else 0.0)
    stability_threshold = float(stability_tolerance) * stability_scale
    cutoff_stable = (
        len(terminal_changes) == 2
        and all(value <= stability_threshold for value in terminal_changes)
    )
    recommended_terms = recommended_hasse_terms(target.s.imag)
    preflight_ok = int(target.terms) >= recommended_terms
    roundoff_proxy = payload["binary64_roundoff_proxy"]
    roundoff_below_residual_tolerance = bool(
        roundoff_proxy is not None
        and float(roundoff_proxy) <= float(near_zero_tolerance)
    )
    if target.status == "zeta_pole_neighborhood_guard":
        classification = "zeta_pole_neighborhood_guard"
    elif target.zeta is None:
        classification = "not_evaluable_with_eta_bridge_at_this_input"
    elif below and not preflight_ok:
        classification = "underresolved_small_residual_below_empirical_term_recommendation"
    elif below and not roundoff_below_residual_tolerance:
        classification = "small_residual_not_resolved_below_roundoff_proxy"
    elif below and not cutoff_stable:
        classification = "residual_below_tolerance_but_two_step_cutoff_stability_failed"
    elif below and target_kind == "user_supplied_reference_zero":
        classification = (
            "user_supplied_reference_residual_and_stability_below_tolerances"
        )
    elif below:
        classification = "near_zero_at_configured_finite_precision"
    else:
        classification = "residual_above_configured_tolerance"
    zeta_payload = payload["zeta"]
    if isinstance(zeta_payload, dict):
        zeta_payload["phase_reliability"] = (
            "undefined_below_configured_zero_tolerance"
            if below
            else "ordinary_binary64_phase"
        )
        if below:
            zeta_payload["phase_turns"] = None
    payload.update(
        {
            "target_kind": str(target_kind),
            "target_label": target_label,
            "numeric_preflight": {
                "empirical_recommended_hasse_terms": recommended_terms,
                "configured_hasse_terms": int(target.terms),
                "configured_meets_empirical_recommendation": preflight_ok,
                "status": "heuristic_from_binary64_calibration_not_an_error_bound",
            },
            "reference_coordinate": {
                "status": (
                    "caller_supplied_not_independently_verified_by_probe"
                    if target_kind == "user_supplied_reference_zero"
                    else "not_designated_as_reference"
                ),
                "label": target_label,
            },
            "zero_diagnostic": {
                "absolute_residual": residual,
                "configured_tolerance": float(near_zero_tolerance),
                "below_tolerance": bool(below),
                "classification": classification,
                "stability_relative_tolerance": float(stability_tolerance),
                "stability_absolute_threshold": stability_threshold,
                "two_terminal_cutoff_changes": terminal_changes,
                "two_terminal_changes_below_stability_threshold": bool(
                    cutoff_stable
                ),
                "roundoff_proxy_below_residual_tolerance": (
                    roundoff_below_residual_tolerance
                ),
                "is_certified_zero": False,
                "certification_status": "not_attempted_no_interval_error_bound",
            },
            "cutoff_stability": ladder,
        }
    )
    return payload


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
        "evidence_layer": "external_complex_analysis_over_strict_graph",
        "claim_status": "numerical_calibration_or_candidate_only",
        "allowed_claim_language": [
            "The probe evaluates a finite external binary64 approximation to zeta(s) at the named complex input.",
            "Hasse weights are computed exactly externally; integer sources, rational reciprocal precursors, and a named sample of interior Pascal recurrences are audited against the selected strict graph.",
            "The reported residual may be compared across named finite cutoffs, conjugates, and a local horizontal-and-vertical control cross.",
            "The quarter-turn phase gives an exact external representation of i while remaining distinct from a runtime complex operand.",
        ],
        "disallowed_claim_language": [
            "Do not claim that strict MoO contains i, complex numbers, logarithms, exponentials, analytic continuation, or zeta(s) as runtime objects.",
            "Do not identify a small external complex residual with a graph-witnessed construction of node 0.",
            "Do not claim that a numerical near-zero proves an exact zero, certifies all zeros in a height interval, or proves the Riemann hypothesis.",
            "Do not use the ordinary Dirichlet series or Euler product as convergent critical-strip constructions.",
            "Do not alias rational multiplication of 1/4 with complex multiplication of i.",
            "Do not treat a post-hoc nearest rational phase node as evidence that the external complex phase was graph-constructed.",
            "Do not treat a user-supplied reference-zero label as independent verification of that coordinate.",
        ],
        "interpretation_limits": [
            "The Q/Z quarter-turn and Gaussian pair are external representation views, not complex runtime nodes.",
            "Graph evidence attaches to rational and integer source constructions, not to the external complex power or accumulated value.",
            "Every zero diagnostic is finite-term and finite-precision and has no rigorous truncation or rounding interval.",
            "Certification would require rigorous error bounds plus a zero-counting method such as argument-principle or Hardy-Z/Turing-style machinery.",
            "A critical-line scan alone cannot exclude hypothetical zeros away from the critical line.",
            "The binary64 roundoff proxy is a conditioning indicator, not a rigorous error interval.",
        ],
    }


def _method_payload() -> Dict[str, object]:
    return {
        "name": "finite_hasse_euler_transformed_dirichlet_eta",
        "formula": (
            "zeta(s) ~= [sum_{k=0}^{K-1} 2^(-k-1) "
            "sum_{j=0}^{k} (-1)^j C(k,j) (j+1)^(-s)] / (1-2^(1-s))"
        ),
        "finite_regrouping": (
            "the triangular sum is regrouped by source integer with exact Fraction weights before binary64 complex evaluation"
        ),
        "calculation_layer": "external_finite_precision_complex",
        "numeric_model": "python_binary64_complex_with_math_fsum",
        "ordinary_zeta_dirichlet_series_used_in_strip": False,
        "ordinary_euler_product_used_in_strip": False,
        "functional_equation_evaluated": False,
        "functional_equation_status": (
            "deferred; complex gamma and rigorous error semantics are not implemented"
        ),
        "eta_bridge_guard": ETA_BRIDGE_GUARD,
        "near_pole_radius": NEAR_POLE_RADIUS,
        "eta_bridge_guard_limitation": (
            "the eta quotient denominator also vanishes at s=1+2*pi*i*k/log(2); "
            "for nonzero integer k these are removable quotient singularities, not zeta poles"
        ),
        "term_indexing": "hasse_terms K means outer rows k=0..K-1",
        "error_model": {
            "rigorous_interval_bound": False,
            "truncation_bound": False,
            "rounding_bound": False,
            "cutoff_ladder": "empirical_only",
        },
        "binary64_preflight_heuristic": (
            "round_up_to_8(max(64, ceil(1.6*abs(t)+40))); empirical only"
        ),
        "stability_rule": (
            "the last two cutoff changes must each be <= configured relative "
            "stability tolerance times (1+abs(zeta))"
        ),
    }


def _input_domain(sigma: float) -> Dict[str, object]:
    value = float(sigma)
    inside = 0.0 < value < 1.0
    on_line = value == 0.5
    if on_line:
        classification = "critical_line_inside_critical_strip"
    elif inside:
        classification = "critical_strip_off_critical_line"
    elif value in {0.0, 1.0}:
        classification = "critical_strip_boundary"
    elif value < 0.0:
        classification = "left_of_critical_strip_control_domain"
    else:
        classification = "right_of_critical_strip_control_domain"
    return {
        "inside_open_critical_strip": inside,
        "on_critical_line_binary64_exact": on_line,
        "domain_classification": classification,
        "eligible_for_nontrivial_zero_target_mode": inside,
    }


def _validate_probe_limits(
    *,
    sigma: float,
    t: float,
    hasse_terms: int,
    ladder_terms: Sequence[int],
    control_delta: float,
    near_zero_tolerance: float,
    stability_tolerance: float,
    pascal_max_row: int,
    phase_max_denominator: int,
    phase_sample_terms: int,
    edge_limit: int,
    full_scan: bool,
) -> None:
    numeric = [sigma, t, control_delta, near_zero_tolerance, stability_tolerance]
    if not all(math.isfinite(float(value)) for value in numeric):
        raise ValueError("all numeric inputs must be finite")
    if int(hasse_terms) < 1:
        raise ValueError("hasse_terms must be >= 1")
    if int(hasse_terms) > HARD_MAX_HASSE_TERMS:
        raise ValueError(
            f"hasse_terms>{HARD_MAX_HASSE_TERMS} exceeds the hard binary64 safety limit"
        )
    if not ladder_terms or any(int(value) < 1 for value in ladder_terms):
        raise ValueError("ladder_terms must contain positive integers")
    if max(int(value) for value in ladder_terms) > int(hasse_terms):
        raise ValueError("ladder_terms must not exceed hasse_terms")
    if float(control_delta) <= 0.0:
        raise ValueError("control_delta must be > 0")
    if float(near_zero_tolerance) <= 0.0:
        raise ValueError("near_zero_tolerance must be > 0")
    if float(stability_tolerance) <= 0.0:
        raise ValueError("stability_tolerance must be > 0")
    if int(pascal_max_row) < 2:
        raise ValueError("pascal_max_row must be >= 2")
    if int(phase_max_denominator) < 1:
        raise ValueError("phase_max_denominator must be >= 1")
    if int(phase_sample_terms) < 1:
        raise ValueError("phase_sample_terms must be >= 1")
    if int(phase_sample_terms) > int(hasse_terms):
        raise ValueError("phase_sample_terms must not exceed hasse_terms")
    if int(edge_limit) < 2:
        raise ValueError(
            "edge_limit must be >= 2 so commuted Pascal edge pairs are not truncated"
        )
    if int(pascal_max_row) > HARD_MAX_PASCAL_ROW:
        raise ValueError(
            f"pascal_max_row>{HARD_MAX_PASCAL_ROW} exceeds the SQLite signed-integer safety limit"
        )
    if int(phase_max_denominator) > HARD_MAX_PHASE_DENOMINATOR:
        raise ValueError(
            "phase_max_denominator exceeds the SQLite signed-integer safety limit"
        )
    if int(phase_sample_terms) > HARD_MAX_HASSE_TERMS:
        raise ValueError(
            f"phase_sample_terms>{HARD_MAX_HASSE_TERMS} exceeds the hard source-term limit"
        )
    if abs(float(sigma)) > MAX_ABS_SIGMA:
        raise ValueError(f"abs(sigma)>{MAX_ABS_SIGMA:g} exceeds the calibrated domain")
    if abs(float(t)) > MAX_ABS_T:
        raise ValueError(f"abs(t)>{MAX_ABS_T:g} exceeds the calibrated domain")
    if full_scan:
        return
    exceeded: List[str] = []
    if int(hasse_terms) > MAX_HASSE_TERMS:
        exceeded.append(f"hasse_terms>{MAX_HASSE_TERMS}")
    if int(pascal_max_row) > MAX_PASCAL_ROW:
        exceeded.append(f"pascal_max_row>{MAX_PASCAL_ROW}")
    if int(phase_max_denominator) > MAX_PHASE_DENOMINATOR:
        exceeded.append(f"phase_max_denominator>{MAX_PHASE_DENOMINATOR}")
    if int(phase_sample_terms) > MAX_PHASE_SAMPLE_TERMS:
        exceeded.append(f"phase_sample_terms>{MAX_PHASE_SAMPLE_TERMS}")
    if exceeded:
        raise ValueError(
            "probe safety limit exceeded ("
            + ", ".join(exceeded)
            + "); pass --full-scan to acknowledge the larger external calculation"
        )


def zeta_critical_probe(
    *,
    db_path: Path,
    sigma: float,
    t: float,
    hasse_terms: int,
    ladder_terms: Optional[Sequence[int]],
    control_delta: float,
    near_zero_tolerance: float,
    stability_tolerance: float = DEFAULT_STABILITY_TOLERANCE,
    target_kind: str,
    target_label: Optional[str],
    pascal_max_row: int,
    phase_max_denominator: int,
    phase_sample_terms: int,
    edge_limit: int,
    full_scan: bool = False,
) -> Dict[str, object]:
    if str(target_kind) not in TARGET_KINDS:
        raise ValueError(
            "target_kind must be one of " + ", ".join(sorted(TARGET_KINDS))
        )
    domain = _input_domain(float(sigma))
    if str(target_kind) in {
        "numerical_candidate",
        "user_supplied_reference_zero",
    } and not bool(domain["inside_open_critical_strip"]):
        raise ValueError(
            "nontrivial-zero candidate/reference modes require 0 < sigma < 1; "
            "use target_kind='control' outside the critical strip"
        )
    if (
        str(target_kind) == "user_supplied_reference_zero"
        and not str(target_label or "").strip()
    ):
        raise ValueError("user_supplied_reference_zero requires target_label")
    checkpoints = (
        sorted(set(int(value) for value in ladder_terms))
        if ladder_terms is not None
        else _default_ladder(int(hasse_terms))
    )
    if int(hasse_terms) not in checkpoints:
        checkpoints.append(int(hasse_terms))
        checkpoints.sort()
    _validate_probe_limits(
        sigma=float(sigma),
        t=float(t),
        hasse_terms=int(hasse_terms),
        ladder_terms=checkpoints,
        control_delta=float(control_delta),
        near_zero_tolerance=float(near_zero_tolerance),
        stability_tolerance=float(stability_tolerance),
        pascal_max_row=int(pascal_max_row),
        phase_max_denominator=int(phase_max_denominator),
        phase_sample_terms=int(phase_sample_terms),
        edge_limit=int(edge_limit),
        full_scan=bool(full_scan),
    )

    s = complex(float(sigma), float(t))
    target = hasse_zeta(s, int(hasse_terms))
    target_report = _target_evaluation(
        target,
        target_kind=str(target_kind),
        target_label=target_label,
        near_zero_tolerance=float(near_zero_tolerance),
        stability_tolerance=float(stability_tolerance),
        ladder_terms=checkpoints,
    )
    controls = _controls(target, control_delta=float(control_delta))

    with closing(connect_readonly(Path(db_path))) as conn:
        alignment = require_strict_alignment(conn)
        corpus = _corpus_payload(conn, alignment=alignment)
        latest = corpus["latest_stage"]
        corpus_stage = int(latest["stage"]) if isinstance(latest, dict) else None
        inspector = CriticalGraphInspector(
            conn,
            corpus_stage=corpus_stage,
            edge_limit=int(edge_limit),
        )
        calibration = _complex_calibration(inspector)
        source_audit = _source_audit(
            inspector,
            target,
            phase_max_denominator=int(phase_max_denominator),
            phase_sample_terms=int(phase_sample_terms),
        )
        pascal = _pascal_audit(
            inspector,
            requested_max_row=int(pascal_max_row),
            required_max_row=max(0, int(hasse_terms) - 1),
        )

    target_residual = target_report["zero_diagnostic"]["absolute_residual"]  # type: ignore[index]
    below_tolerance = bool(
        target_report["zero_diagnostic"]["below_tolerance"]  # type: ignore[index]
    )
    cutoff_stable = bool(
        target_report["zero_diagnostic"][  # type: ignore[index]
            "two_terminal_changes_below_stability_threshold"
        ]
    )
    preflight_ok = bool(
        target_report["numeric_preflight"][  # type: ignore[index]
            "configured_meets_empirical_recommendation"
        ]
    )
    roundoff_ok = bool(
        target_report["zero_diagnostic"][  # type: ignore[index]
            "roundoff_proxy_below_residual_tolerance"
        ]
    )
    controls_pass = bool(controls["calibration_suite"]["passes"])  # type: ignore[index]
    nearby = controls["nearby_cross_controls"]  # type: ignore[assignment]
    nearby_magnitudes = [
        nearby[name]["zeta"]["magnitude"]  # type: ignore[index]
        for name in ("lower_t", "upper_t", "lower_sigma", "upper_sigma")
    ]
    neighbor_values = [
        float(value) for value in nearby_magnitudes if value is not None
    ]
    local_control_cross_complete = len(neighbor_values) == 4
    neighbor_min = min(neighbor_values) if neighbor_values else None
    separation_ratio = (
        float(neighbor_min / float(target_residual))
        if neighbor_min is not None
        and target_residual is not None
        and float(target_residual) > 0.0
        else None
    )
    source_summary = source_audit["summary"]  # type: ignore[assignment]
    return {
        "report_type": "zeta_external_hasse_probe",
        "input_domain": domain,
        "config": {
            "sigma": float(sigma),
            "t": float(t),
            "hasse_terms": int(hasse_terms),
            "ladder_terms": checkpoints,
            "control_delta": float(control_delta),
            "near_zero_tolerance": float(near_zero_tolerance),
            "stability_tolerance": float(stability_tolerance),
            "target_kind": str(target_kind),
            "target_label": target_label,
            "pascal_max_row": int(pascal_max_row),
            "phase_max_denominator": int(phase_max_denominator),
            "phase_sample_terms": int(phase_sample_terms),
            "edge_limit": int(edge_limit),
            "full_scan": bool(full_scan),
        },
        "claim_boundary": _claim_boundary(),
        "corpus": corpus,
        "complex_calibration": calibration,
        "method": _method_payload(),
        "target_evaluation": target_report,
        "graph_source_audit": source_audit,
        "pascal_coefficient_audit": pascal,
        "controls": controls,
        "summary": {
            "target_absolute_residual": target_residual,
            "below_configured_tolerance": below_tolerance,
            "two_terminal_cutoff_changes_below_stability_threshold": (
                cutoff_stable
            ),
            "configured_meets_empirical_term_recommendation": preflight_ok,
            "roundoff_proxy_below_residual_tolerance": roundoff_ok,
            "calibration_control_suite_passes": controls_pass,
            "target_certified_zero": False,
            "minimum_nearby_control_residual": neighbor_min,
            "nearby_to_target_residual_ratio": separation_ratio,
            "local_control_cross_complete": local_control_cross_complete,
            "control_separation_observed": bool(
                below_tolerance
                and cutoff_stable
                and preflight_ok
                and roundoff_ok
                and controls_pass
                and local_control_cross_complete
                and neighbor_min is not None
                and neighbor_min > float(near_zero_tolerance)
            ),
            "index_nodes": source_summary["index_nodes"],
            "reciprocal_precursor_nodes": source_summary[
                "reciprocal_precursor_nodes"
            ],
            "reciprocal_precursor_edges": source_summary[
                "reciprocal_precursor_edges"
            ],
            "pascal_relations": pascal["summary"],
            "quarter_turn_is_runtime_i": False,
            "interpretation": (
                "external numerical complex cancellation over graph-audited rational and integer sources"
            ),
        },
    }


def finite_float(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("must be finite")
    return value


def positive_float(raw: str) -> float:
    value = finite_float(raw)
    if value <= 0.0:
        raise argparse.ArgumentTypeError("must be > 0")
    return value


def parse_ladder(raw: str) -> List[int]:
    values: List[int] = []
    for part in str(raw).split(","):
        text = part.strip()
        if not text:
            continue
        try:
            value = int(text)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                "ladder terms must be comma-separated integers"
            ) from exc
        if value < 1:
            raise argparse.ArgumentTypeError("ladder terms must be >= 1")
        values.append(value)
    if not values:
        raise argparse.ArgumentTypeError("at least one ladder term is required")
    return sorted(set(values))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate a finite external Hasse/eta approximation to zeta(s) and "
            "audit its rational and integer source evidence against a strict MoO graph corpus."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--sigma", type=finite_float, required=True)
    parser.add_argument("--t", type=finite_float, required=True)
    parser.add_argument(
        "--hasse-terms",
        "--terms",
        dest="hasse_terms",
        type=positive_int,
        default=64,
    )
    parser.add_argument(
        "--ladder-terms",
        type=parse_ladder,
        help="Comma-separated Hasse cutoffs; the final --hasse-terms cutoff is added automatically.",
    )
    parser.add_argument("--control-delta", type=positive_float, default=0.01)
    parser.add_argument(
        "--near-zero-tolerance", type=positive_float, default=1e-10
    )
    parser.add_argument(
        "--stability-tolerance",
        type=positive_float,
        default=DEFAULT_STABILITY_TOLERANCE,
        help=(
            "Independent relative cutoff-stability threshold; it is not the "
            "near-zero residual tolerance."
        ),
    )
    parser.add_argument(
        "--target-kind",
        choices=sorted(TARGET_KINDS),
        default="numerical_candidate",
    )
    parser.add_argument("--target-label")
    parser.add_argument("--pascal-max-row", type=positive_int, default=8)
    parser.add_argument("--phase-max-denominator", type=positive_int, default=80)
    parser.add_argument("--phase-sample-terms", type=positive_int, default=12)
    parser.add_argument("--edge-limit", type=positive_int, default=4)
    parser.add_argument("--full-scan", action="store_true")
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
    payload = zeta_critical_probe(
        db_path=Path(args.db),
        sigma=float(args.sigma),
        t=float(args.t),
        hasse_terms=int(args.hasse_terms),
        ladder_terms=args.ladder_terms,
        control_delta=float(args.control_delta),
        near_zero_tolerance=float(args.near_zero_tolerance),
        stability_tolerance=float(args.stability_tolerance),
        target_kind=str(args.target_kind),
        target_label=str(args.target_label) if args.target_label else None,
        pascal_max_row=int(args.pascal_max_row),
        phase_max_denominator=int(args.phase_max_denominator),
        phase_sample_terms=int(args.phase_sample_terms),
        edge_limit=int(args.edge_limit),
        full_scan=bool(args.full_scan),
    )
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_zeta_critical_probe.v1",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
