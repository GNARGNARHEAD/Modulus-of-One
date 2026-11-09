from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import statistics
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from moo.research_utils import (
    connect_readonly,
    emit_json,
    file_sha256,
    positive_int,
    report_metadata,
    require_strict_alignment,
)
from moo.zeta_critical_probe import (
    HasseApproximation,
    approximation_payload,
    complex_input_payload,
    complex_payload,
    finite_float,
    fraction_payload,
    hasse_zeta,
    positive_float,
    recommended_hasse_terms,
)


MASK_KINDS = (
    "source_node_present",
    "source_operand_ready",
    "reciprocal_node_present",
    "direct_reciprocal_edge_present",
    "operational_source_and_reciprocal_edge",
)
TARGET_KINDS = {
    "user_supplied_reference_zero",
    "numerical_candidate",
    "control",
}
DEFAULT_HEIGHT_CONTROLS = (10.0, 11.0, 12.0, 13.0, 15.0, 16.0, 17.0, 18.0, 19.0, 20.0)
DEFAULT_PERMUTATION_SAMPLES = 256
MAX_HASSE_TERMS = 64
HARD_MAX_HASSE_TERMS = 256
MAX_PERMUTATION_SAMPLES = 512
HARD_MAX_PERMUTATION_SAMPLES = 4096
MAX_HEIGHT_CONTROLS = 32
HARD_MAX_STAGE_HORIZON = 10_000
PERMUTATION_SALT = "moo-zeta-arrival-v1"
DEFAULT_STABILITY_TOLERANCE = 1e-12
DEFAULT_NEAR_ZERO_TOLERANCE = 1e-10
MIN_RADIAL_INWARD_FRACTION = 0.95
MIN_RADIAL_EFFICIENCY = 0.95
MAX_PRIMARY_NULL_TAIL_FRACTION = 0.01


@dataclass(frozen=True)
class SourceSchedule:
    source: int
    source_node_present_stage: Optional[int]
    source_operand_ready_stage: Optional[int]
    reciprocal_node_present_stage: Optional[int]
    reciprocal_node_operand_ready_stage: Optional[int]
    direct_reciprocal_edge_present_stage: Optional[int]
    operational_source_and_reciprocal_edge_stage: Optional[int]
    reciprocal_witness_stages: Tuple[int, ...]
    source_first_witness: Dict[str, object]

    def stage_for(self, mask_kind: str) -> Optional[int]:
        if mask_kind not in MASK_KINDS:
            raise ValueError(f"unknown mask_kind: {mask_kind}")
        return getattr(self, f"{mask_kind}_stage")


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row is not None else None


def _corpus_payload(
    conn: sqlite3.Connection,
    *,
    db_path: Path,
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
        "db_path": str(db_path),
        "schema_version": _meta_value(conn, "schema_version"),
        "config": config,
        "latest_stage": dict(latest) if latest is not None else None,
        "nodes": int(conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()["n"]),
        "edges": int(conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()["n"]),
        "alignment": alignment,
    }


def _validate_stage_prefix(
    conn: sqlite3.Connection,
    *,
    stage_horizon: int,
    config: object,
) -> Dict[str, object]:
    if not isinstance(config, dict):
        raise ValueError("strict-stage corpus config_json must decode to an object")
    if config.get("generator") != "strict_stage_moo_graph":
        raise ValueError(
            "zeta arrival analysis requires generator=strict_stage_moo_graph"
        )

    rows = list(
        conn.execute(
            "SELECT * FROM stages WHERE stage <= ? ORDER BY stage",
            (int(stage_horizon),),
        )
    )
    observed_stages = [int(row["stage"]) for row in rows]
    expected_stages = list(range(1, int(stage_horizon) + 1))
    errors: List[str] = []
    if observed_stages != expected_stages:
        errors.append(
            f"recorded stages {observed_stages!r} are not contiguous {expected_stages!r}"
        )

    stage_checks: List[Dict[str, object]] = []
    for row in rows:
        stage = int(row["stage"])
        expected_candidates = 8 * stage - 4
        non_seed_edges = int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM edges WHERE stage = ? AND op != 'seed'",
                (stage,),
            ).fetchone()["n"]
        )
        cumulative_edges = int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM edges WHERE stage <= ?",
                (stage,),
            ).fetchone()["n"]
        )
        cumulative_nodes = int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM nodes WHERE first_stage <= ?",
                (stage,),
            ).fetchone()["n"]
        )
        checks = {
            "candidate_events_complete": int(row["candidate_events"])
            == expected_candidates,
            "retained_events_equal_new_edges": int(row["retained_events"])
            == int(row["new_edges"]),
            "retained_events_equal_recorded_non_seed_edges": int(
                row["retained_events"]
            )
            == non_seed_edges,
            "total_edges_match_prefix": int(row["total_edges"])
            == cumulative_edges,
            "total_nodes_match_first_stage_prefix": int(row["total_nodes"])
            == cumulative_nodes,
        }
        failed = [name for name, passes in checks.items() if not passes]
        if failed:
            errors.append(f"stage {stage} failed {', '.join(failed)}")
        stage_checks.append(
            {
                "stage": stage,
                "expected_candidate_events": expected_candidates,
                "recorded_candidate_events": int(row["candidate_events"]),
                "recorded_non_seed_edges": non_seed_edges,
                **checks,
            }
        )
    if errors:
        raise ValueError("strict-stage prefix validation failed: " + "; ".join(errors))
    return {
        "status": "complete_strict_stage_prefix",
        "generator": "strict_stage_moo_graph",
        "validated_through_stage": int(stage_horizon),
        "stage_count": len(rows),
        "candidate_event_formula": "8*stage-4",
        "stage_checks": stage_checks,
    }


def _fraction_payload(p: int, q: int) -> Dict[str, object]:
    return {
        "p": int(p),
        "q": int(q),
        "frac": str(p) if int(q) == 1 else f"{p}/{q}",
    }


def _first_witness_payload(row: sqlite3.Row) -> Dict[str, object]:
    edge_id = row["first_edge_id"]
    if edge_id is None:
        return {
            "present": False,
            "reason": "node has no retained first-edge reference",
        }
    left = (
        _fraction_payload(int(row["left_p"]), int(row["left_q"]))
        if row["left_p"] is not None
        else None
    )
    right = (
        _fraction_payload(int(row["right_p"]), int(row["right_q"]))
        if row["right_p"] is not None
        else None
    )
    source_key = (int(row["source"]), 1)
    left_key = (
        (int(row["left_p"]), int(row["left_q"]))
        if row["left_p"] is not None
        else None
    )
    right_key = (
        (int(row["right_p"]), int(row["right_q"]))
        if row["right_p"] is not None
        else None
    )
    uses_result_as_operand = source_key in {left_key, right_key}
    confirmed_stage = row["confirmed_stage"]
    is_seed = str(row["edge_op"]) == "seed"
    return {
        "present": True,
        "edge_id": int(edge_id),
        "stage": int(row["edge_stage"]),
        "op": str(row["edge_op"]),
        "left": left,
        "right": right,
        "uses_result_as_left_or_right_operand": uses_result_as_operand,
        "precedes_source_confirmation": bool(
            confirmed_stage is not None
            and int(row["edge_stage"]) < int(confirmed_stage)
        ),
        "independent_construction_witness": bool(
            not uses_result_as_operand and not is_seed
        ),
    }


def _load_source_schedules(
    conn: sqlite3.Connection,
    *,
    hasse_terms: int,
) -> List[SourceSchedule]:
    source_rows = {
        int(row["source"]): row
        for row in conn.execute(
            """
            SELECT
              n.p AS source,
              n.first_stage,
              n.confirmed_stage,
              n.first_edge_id,
              e.stage AS edge_stage,
              e.op AS edge_op,
              l.p AS left_p,
              l.q AS left_q,
              r.p AS right_p,
              r.q AS right_q
            FROM nodes n
            LEFT JOIN edges e ON e.edge_id = n.first_edge_id
            LEFT JOIN nodes l ON l.node_id = e.left_node_id
            LEFT JOIN nodes r ON r.node_id = e.right_node_id
            WHERE n.q = 1 AND n.p BETWEEN 1 AND ?
            ORDER BY n.p
            """,
            (int(hasse_terms),),
        )
    }
    reciprocal_rows = {
        int(row["source"]): row
        for row in conn.execute(
            """
            SELECT
              CASE WHEN p = 1 AND q = 1 THEN 1 ELSE q END AS source,
              first_stage,
              confirmed_stage
            FROM nodes
            WHERE (p = 1 AND q = 1)
               OR (p = 1 AND q BETWEEN 2 AND ?)
            """,
            (int(hasse_terms),),
        )
    }
    direct_reciprocal_edge_stages = {
        int(row["source"]): int(row["first_stage"])
        for row in conn.execute(
            """
            SELECT r.p AS source, MIN(e.stage) AS first_stage
            FROM edges e
            JOIN nodes l ON l.node_id = e.left_node_id
            JOIN nodes r ON r.node_id = e.right_node_id
            JOIN nodes z ON z.node_id = e.result_node_id
            WHERE e.op = '/'
              AND l.p = 1 AND l.q = 1
              AND r.q = 1 AND r.p BETWEEN 1 AND ?
              AND z.p = 1 AND z.q = r.p
            GROUP BY r.p
            """,
            (int(hasse_terms),),
        )
    }
    reciprocal_witnesses: Dict[int, List[int]] = defaultdict(list)
    for row in conn.execute(
            """
            SELECT CASE WHEN z.q = 1 THEN 1 ELSE z.q END AS source, e.stage
            FROM edges e
            JOIN nodes z ON z.node_id = e.result_node_id
            WHERE e.op = '/'
              AND z.p = 1 AND z.q BETWEEN 1 AND ?
            ORDER BY source, e.stage, e.edge_id
            """,
            (int(hasse_terms),),
        ):
        reciprocal_witnesses[int(row["source"])].append(int(row["stage"]))
    schedules: List[SourceSchedule] = []
    for source in range(1, int(hasse_terms) + 1):
        source_row = source_rows.get(source)
        reciprocal_row = reciprocal_rows.get(source)
        present_stage = (
            int(source_row["first_stage"]) if source_row is not None else None
        )
        ready_stage = (
            int(source_row["confirmed_stage"])
            if source_row is not None and source_row["confirmed_stage"] is not None
            else None
        )
        reciprocal_stage = (
            int(reciprocal_row["first_stage"])
            if reciprocal_row is not None
            else None
        )
        reciprocal_ready_stage = (
            int(reciprocal_row["confirmed_stage"])
            if reciprocal_row is not None
            and reciprocal_row["confirmed_stage"] is not None
            else None
        )
        witness_stages = tuple(reciprocal_witnesses.get(source, []))
        edge_stage = direct_reciprocal_edge_stages.get(source)
        operational_stage = (
            max(int(ready_stage), int(edge_stage))
            if ready_stage is not None and edge_stage is not None
            else None
        )
        schedules.append(
            SourceSchedule(
                source=source,
                source_node_present_stage=present_stage,
                source_operand_ready_stage=ready_stage,
                reciprocal_node_present_stage=reciprocal_stage,
                reciprocal_node_operand_ready_stage=reciprocal_ready_stage,
                direct_reciprocal_edge_present_stage=edge_stage,
                operational_source_and_reciprocal_edge_stage=operational_stage,
                reciprocal_witness_stages=witness_stages,
                source_first_witness=(
                    _first_witness_payload(source_row)
                    if source_row is not None
                    else {
                        "present": False,
                        "reason": "source integer node absent from selected corpus",
                    }
                ),
            )
        )
    return schedules


def _balanced_presence_prediction(source: int) -> int:
    n = int(source)
    if n <= 1:
        return 1
    candidates = [int(math.ceil(n / 2.0))]
    for divisor in range(1, int(math.isqrt(n)) + 1):
        if n % divisor == 0:
            candidates.append(max(divisor, n // divisor))
    return min(candidates)


def _schedule_rows_payload(
    schedules: Sequence[SourceSchedule],
    *,
    stage_horizon: int,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for schedule in schedules:
        present = schedule.source_node_present_stage
        ready = schedule.source_operand_ready_stage
        prediction = _balanced_presence_prediction(schedule.source)
        witness_stages = [
            int(stage)
            for stage in schedule.reciprocal_witness_stages
            if int(stage) <= int(stage_horizon)
        ]
        operational_stage = (
            schedule.operational_source_and_reciprocal_edge_stage
        )
        raw_first_witness = schedule.source_first_witness
        first_witness_stage = raw_first_witness.get("stage")
        first_witness_observed = bool(
            raw_first_witness.get("present")
            and first_witness_stage is not None
            and int(first_witness_stage) <= int(stage_horizon)
        )

        def observed_stage(stage: Optional[int]) -> Optional[int]:
            return (
                int(stage)
                if stage is not None and int(stage) <= int(stage_horizon)
                else None
            )

        rows.append(
            {
                "source_integer": int(schedule.source),
                "schedule_scope": "retrospective_full_corpus_with_horizon_censoring",
                "raw_stage_fields_beyond_horizon_validation_status": (
                    "not_prefix_validated; use observed_by_horizon fields for analysis"
                ),
                "source_node_present_stage": present,
                "source_node_present_stage_observed_by_horizon": observed_stage(present),
                "source_operand_ready_stage": ready,
                "source_operand_ready_stage_observed_by_horizon": observed_stage(ready),
                "reciprocal_node_present_stage": (
                    schedule.reciprocal_node_present_stage
                ),
                "reciprocal_node_present_stage_observed_by_horizon": observed_stage(
                    schedule.reciprocal_node_present_stage
                ),
                "reciprocal_node_operand_ready_stage": (
                    schedule.reciprocal_node_operand_ready_stage
                ),
                "direct_reciprocal_edge_present_stage": (
                    schedule.direct_reciprocal_edge_present_stage
                ),
                "direct_reciprocal_edge_present_stage_observed_by_horizon": (
                    observed_stage(schedule.direct_reciprocal_edge_present_stage)
                ),
                "operational_source_and_reciprocal_edge_stage": (
                    operational_stage
                ),
                "operational_stage_observed_by_horizon": observed_stage(
                    operational_stage
                ),
                "reciprocal_result_is_operand_ready_at_operational_arrival": bool(
                    operational_stage is not None
                    and schedule.reciprocal_node_operand_ready_stage is not None
                    and int(schedule.reciprocal_node_operand_ready_stage)
                    <= int(operational_stage)
                ),
                "speculative_lead_stages": (
                    int(ready) - int(present)
                    if present is not None and ready is not None and present < ready
                    else 0
                ),
                "balanced_add_or_multiply_presence_prediction": prediction,
                "presence_matches_balanced_prediction": (
                    present == prediction if present is not None else None
                ),
                "source_first_witness": schedule.source_first_witness,
                "source_first_witness_observed_by_horizon": (
                    schedule.source_first_witness
                    if first_witness_observed
                    else {
                        "present": False,
                        "reason": "absent or right-censored at the requested horizon",
                    }
                ),
                "reciprocal_witness_stages_through_horizon": witness_stages,
                "reciprocal_witness_count_through_horizon": len(witness_stages),
                "reciprocal_expected_divisor_ladder_through_horizon": [
                    multiple
                    for multiple in range(
                        int(schedule.source),
                        int(stage_horizon) + 1,
                        int(schedule.source),
                    )
                ],
                "reciprocal_witness_ladder_matches_divisibility": witness_stages
                == [
                    multiple
                    for multiple in range(
                        int(schedule.source),
                        int(stage_horizon) + 1,
                        int(schedule.source),
                    )
                ],
            }
        )
    return rows


def _arrival_stages(
    schedules: Sequence[SourceSchedule],
    mask_kind: str,
) -> Tuple[Optional[int], ...]:
    return tuple(schedule.stage_for(mask_kind) for schedule in schedules)


def _schedule_summary(
    schedules: Sequence[SourceSchedule],
    *,
    stage_horizon: int,
) -> Dict[str, object]:
    signatures: Dict[Tuple[Optional[int], ...], List[str]] = defaultdict(list)
    masks: Dict[str, Dict[str, object]] = {}
    for mask_kind in MASK_KINDS:
        full_stages = _arrival_stages(schedules, mask_kind)
        stages = tuple(
            int(stage)
            if stage is not None and int(stage) <= int(stage_horizon)
            else None
            for stage in full_stages
        )
        signatures[stages].append(mask_kind)
        observed = [
            int(stage)
            for stage in stages
            if stage is not None and int(stage) <= int(stage_horizon)
        ]
        masks[mask_kind] = {
            "arrived_source_count_at_horizon": len(observed),
            "missing_or_beyond_horizon_source_count": len(stages) - len(observed),
            "completion_stage": max(observed) if len(observed) == len(stages) else None,
            "runtime_eligibility": (
                "aligned_operational_gate"
                if mask_kind == "operational_source_and_reciprocal_edge"
                else (
                    "confirmed_source_only_but_reciprocal_evidence_not_required"
                    if mask_kind == "source_operand_ready"
                    else "inspection_contrast_not_runtime_eligibility"
                )
            ),
        }
    early = [
        schedule
        for schedule in schedules
        if schedule.source_node_present_stage is not None
        and int(schedule.source_node_present_stage) <= int(stage_horizon)
        and schedule.source_operand_ready_stage is not None
        and schedule.source_node_present_stage < schedule.source_operand_ready_stage
    ]
    witness_mismatches = [
        schedule.source
        for schedule in schedules
        if [
            stage
            for stage in schedule.reciprocal_witness_stages
            if stage <= int(stage_horizon)
        ]
        != list(
            range(
                schedule.source,
                int(stage_horizon) + 1,
                schedule.source,
            )
        )
    ]
    pair_observed_equal: List[int] = []
    pair_mismatches: List[int] = []
    pair_jointly_censored: List[int] = []
    for schedule in schedules:
        ready = schedule.source_operand_ready_stage
        edge = schedule.direct_reciprocal_edge_present_stage
        ready_observed = ready is not None and int(ready) <= int(stage_horizon)
        edge_observed = edge is not None and int(edge) <= int(stage_horizon)
        if not ready_observed and not edge_observed:
            pair_jointly_censored.append(schedule.source)
        elif ready_observed and edge_observed and ready == edge:
            pair_observed_equal.append(schedule.source)
        else:
            pair_mismatches.append(schedule.source)

    expected_observed_sources = list(
        range(1, min(len(schedules), int(stage_horizon)) + 1)
    )
    operational_observed = [
        schedule
        for schedule in schedules
        if schedule.operational_source_and_reciprocal_edge_stage is not None
        and int(schedule.operational_source_and_reciprocal_edge_stage)
        <= int(stage_horizon)
    ]
    operational_observed_sources = [row.source for row in operational_observed]
    observed_natural_prefix = (
        operational_observed_sources == expected_observed_sources
        and all(
            row.operational_source_and_reciprocal_edge_stage == row.source
            for row in operational_observed
        )
    )
    full_pair_identity = not pair_mismatches and not pair_jointly_censored
    full_natural_order = observed_natural_prefix and len(operational_observed) == len(
        schedules
    )
    pair_status = (
        "full_schedule_identical"
        if full_pair_identity
        else (
            "observed_pairs_identical_with_joint_right_censoring"
            if not pair_mismatches
            else "observed_schedule_mismatch"
        )
    )
    natural_status = (
        "full_natural_source_order"
        if full_natural_order
        else (
            "observed_natural_prefix_with_later_sources_right_censored"
            if observed_natural_prefix
            else "observed_schedule_is_not_natural_prefix"
        )
    )
    reciprocal_reinforcement_reading = (
        "source n receives one retained 1/n witness at each stage divisible by n; "
        "reinforcement annotates the node and never duplicates its analytic term"
        if not witness_mismatches
        else (
            "the expected retained-witness ladder is n,2n,... through the horizon, "
            "but the reported mismatch sources are missing at least one rung under "
            "this corpus aperture; reinforcement never duplicates an analytic term"
        )
    )
    return {
        "masks": masks,
        "equivalent_mask_groups": [
            {
                "mask_kinds": kinds,
                "arrival_stages_observed_by_horizon": [
                    stage for stage in signature
                ],
            }
            for signature, kinds in signatures.items()
        ],
        "operand_ready_and_direct_reciprocal_stage_identical": full_pair_identity,
        "operand_ready_and_direct_reciprocal_comparison": {
            "status": pair_status,
            "observed_equal_source_count": len(pair_observed_equal),
            "observed_equal_sources": pair_observed_equal,
            "mismatch_source_count": len(pair_mismatches),
            "mismatch_sources": pair_mismatches,
            "jointly_right_censored_source_count": len(pair_jointly_censored),
            "jointly_right_censored_sources": pair_jointly_censored,
        },
        "operational_schedule_is_natural_source_order": full_natural_order,
        "operational_schedule_is_observed_natural_prefix_through_horizon": (
            observed_natural_prefix
        ),
        "operational_schedule_status": natural_status,
        "operational_observed_sources": operational_observed_sources,
        "speculative_sources_present_before_confirmation": len(early),
        "speculative_early_source_integers": [schedule.source for schedule in early],
        "maximum_speculative_lead_stages": max(
            (
                int(schedule.source_operand_ready_stage)
                - int(schedule.source_node_present_stage)
                for schedule in early
            ),
            default=0,
        ),
        "all_reciprocal_witness_ladders_match_divisibility": not witness_mismatches,
        "reciprocal_witness_ladder_mismatch_sources": witness_mismatches,
        "reciprocal_reinforcement_reading": reciprocal_reinforcement_reading,
        "operational_reciprocal_boundary": (
            "the primary mask is an external-analysis gate: source n is confirmed "
            "and a retained 1/n edge exists; the reciprocal result itself remains "
            "non-operand-ready for n>1"
        ),
    }


def _sum_complex(values: Sequence[complex]) -> complex:
    return complex(
        math.fsum(value.real for value in values),
        math.fsum(value.imag for value in values),
    )


def _persistent_capture_stage(
    rows: Sequence[Dict[str, object]],
    *,
    key: str,
    threshold: float,
) -> Optional[int]:
    for index, row in enumerate(rows):
        if all(float(later[key]) <= float(threshold) for later in rows[index:]):
            return int(row["stage"])
    return None


def _first_persistent_boolean(
    rows: Sequence[Dict[str, object]],
    *,
    key: str,
) -> Optional[int]:
    for index, row in enumerate(rows):
        if all(bool(later[key]) for later in rows[index:]):
            return int(row["stage"])
    return None


def _trajectory(
    approximation: HasseApproximation,
    *,
    schedules: Sequence[SourceSchedule],
    mask_kind: str,
    stage_horizon: int,
    envelope_guard: float,
    assigned_contributions: Optional[Sequence[complex]] = None,
) -> List[Dict[str, object]]:
    if approximation.zeta is None:
        raise ValueError(
            f"trajectory input is not finite under the eta bridge: {approximation.status}"
        )
    arrivals = _arrival_stages(schedules, mask_kind)
    contributions = tuple(
        assigned_contributions
        if assigned_contributions is not None
        else approximation.source_contributions
    )
    if len(contributions) != len(arrivals):
        raise ValueError("assigned contribution count must match source schedule")
    bridge_magnitude = float(abs(approximation.bridge_denominator))
    if bridge_magnitude == 0.0:
        raise ValueError("eta bridge magnitude must be nonzero")
    total_mass = float(math.fsum(abs(value) for value in contributions))
    full_eta = _sum_complex(contributions)
    full_zeta = full_eta / approximation.bridge_denominator
    radial_scale = total_mass / bridge_magnitude
    rows: List[Dict[str, object]] = []
    previous_zeta = 0j
    for stage in range(1, int(stage_horizon) + 1):
        active_indices = [
            index
            for index, arrival in enumerate(arrivals)
            if arrival is not None and int(arrival) <= stage
        ]
        active_set = set(active_indices)
        newly_arrived = [
            index + 1
            for index, arrival in enumerate(arrivals)
            if arrival is not None and int(arrival) == stage
        ]
        active_values = [contributions[index] for index in active_indices]
        missing_values = [
            value
            for index, value in enumerate(contributions)
            if index not in active_set
        ]
        eta = _sum_complex(active_values)
        zeta = eta / approximation.bridge_denominator
        active_mass = float(math.fsum(abs(value) for value in active_values))
        remaining_mass = float(math.fsum(abs(value) for value in missing_values))
        remaining_capacity = remaining_mass / bridge_magnitude
        magnitude = float(abs(zeta))
        normalized_radius = (
            float(magnitude / radial_scale) if radial_scale > 0.0 else 0.0
        )
        normalized_tail_to_full = (
            float(abs(full_zeta - zeta) / radial_scale)
            if radial_scale > 0.0
            else 0.0
        )
        rows.append(
            {
                "stage": stage,
                "newly_arrived_sources": newly_arrived,
                "active_source_count": len(active_indices),
                "active_mass_fraction": (
                    float(active_mass / total_mass) if total_mass > 0.0 else 0.0
                ),
                "masked_zeta": complex_payload(zeta),
                "normalized_radius": normalized_radius,
                "normalized_tail_to_full": normalized_tail_to_full,
                "remaining_absolute_cancellation_capacity": remaining_capacity,
                "remaining_mass_fraction": (
                    float(remaining_mass / total_mass) if total_mass > 0.0 else 0.0
                ),
                "envelope_guard": float(envelope_guard),
                "inside_cancellation_envelope": bool(
                    magnitude <= remaining_capacity + float(envelope_guard)
                ),
                "cancellation_envelope_margin": float(
                    remaining_capacity + float(envelope_guard) - magnitude
                ),
                "step_magnitude": float(abs(zeta - previous_zeta)),
                "new_reciprocal_reinforcement_sources": [
                    schedule.source
                    for schedule in schedules
                    if stage in schedule.reciprocal_witness_stages
                ],
            }
        )
        previous_zeta = zeta
    return rows


def _radial_diagnostics(radii: Sequence[float]) -> Dict[str, object]:
    if not radii:
        raise ValueError("radial series must contain at least one value")
    radial_guard = float(max(64, len(radii))) * math.ulp(1.0)
    peak_index = max(range(len(radii)), key=lambda index: radii[index])
    deltas = [radii[index] - radii[index - 1] for index in range(1, len(radii))]
    after_peak = deltas[peak_index:]
    resolved = [delta for delta in after_peak if abs(delta) > radial_guard]
    inward = [delta for delta in resolved if delta < 0.0]
    outward = [delta for delta in resolved if delta > 0.0]
    longest_inward = 0
    current_inward = 0
    for delta in after_peak:
        if delta < -radial_guard:
            current_inward += 1
            longest_inward = max(longest_inward, current_inward)
        elif delta > radial_guard:
            current_inward = 0
    radial_path = float(math.fsum(abs(delta) for delta in after_peak))
    radial_efficiency = (
        float((radii[peak_index] - radii[-1]) / radial_path)
        if radial_path > 0.0
        else None
    )
    return {
        "peak_index": peak_index,
        "peak_normalized_radius": float(radii[peak_index]),
        "resolved_post_peak_step_count": len(resolved),
        "resolved_inward_step_count": len(inward),
        "resolved_outward_step_count": len(outward),
        "resolved_inward_fraction": (
            float(len(inward) / len(resolved)) if resolved else None
        ),
        "longest_resolved_inward_streak": longest_inward,
        "post_peak_radial_efficiency": radial_efficiency,
        "radial_resolution_guard": radial_guard,
    }


def _trajectory_metrics(
    rows: Sequence[Dict[str, object]],
    *,
    completion_stage: Optional[int],
) -> Dict[str, object]:
    if not rows:
        raise ValueError("trajectory must contain at least one stage")
    radii = [float(row["normalized_radius"]) for row in rows]
    radial = _radial_diagnostics(radii)
    peak_index = int(radial.pop("peak_index"))
    exit_stage = None
    for index, row in enumerate(rows):
        if not bool(row["inside_cancellation_envelope"]) and all(
            not bool(later["inside_cancellation_envelope"])
            for later in rows[index:]
        ):
            exit_stage = int(row["stage"])
            break
    metrics: Dict[str, object] = {
        "stage_horizon": int(rows[-1]["stage"]),
        "completion_stage": completion_stage,
        "active_sources_at_horizon": int(rows[-1]["active_source_count"]),
        "terminal_masked_magnitude": float(rows[-1]["masked_zeta"]["magnitude"]),  # type: ignore[index]
        "peak_stage": int(rows[peak_index]["stage"]),
        **radial,
        "normalized_radius_auc": float(math.fsum(radii) / len(radii)),
        "normalized_tail_to_full_auc": float(
            math.fsum(float(row["normalized_tail_to_full"]) for row in rows)
            / len(rows)
        ),
        "inside_cancellation_envelope_at_all_stages": all(
            bool(row["inside_cancellation_envelope"]) for row in rows
        ),
        "first_irreversible_cancellation_envelope_exit_stage": exit_stage,
        "persistent_radius_capture_stages": {
            f"{threshold:g}": _persistent_capture_stage(
                rows,
                key="normalized_radius",
                threshold=threshold,
            )
            for threshold in (1e-2, 1e-3, 1e-4)
        },
        "persistent_tail_to_full_capture_stages": {
            f"{threshold:g}": _persistent_capture_stage(
                rows,
                key="normalized_tail_to_full",
                threshold=threshold,
            )
            for threshold in (1e-2, 1e-3, 1e-4)
        },
    }
    if "target_below_all_local_controls" in rows[0]:
        metrics["first_persistent_below_all_local_controls_stage"] = (
            _first_persistent_boolean(
                rows,
                key="target_below_all_local_controls",
            )
        )
        metrics["first_persistent_below_all_height_controls_stage"] = (
            _first_persistent_boolean(
                rows,
                key="target_below_all_height_controls",
            )
        )
        metrics["persistent_local_separation_ratio_stages"] = {
            f"{threshold:g}": next(
                (
                    int(row["stage"])
                    for index, row in enumerate(rows)
                    if row["local_control_to_target_ratio"] is not None
                    and float(row["local_control_to_target_ratio"]) >= threshold
                    and all(
                        later["local_control_to_target_ratio"] is not None
                        and float(later["local_control_to_target_ratio"]) >= threshold
                        for later in rows[index:]
                    )
                ),
                None,
            )
            for threshold in (1.0, 10.0, 100.0, 1000.0)
        }
    return metrics


def _local_control_approximations(
    target: HasseApproximation,
    *,
    control_delta: float,
) -> Dict[str, HasseApproximation]:
    sigma = float(target.s.real)
    t = float(target.s.imag)
    terms = int(target.terms)
    return {
        "lower_t": hasse_zeta(complex(sigma, t - float(control_delta)), terms),
        "upper_t": hasse_zeta(complex(sigma, t + float(control_delta)), terms),
        "lower_sigma": hasse_zeta(complex(sigma - float(control_delta), t), terms),
        "upper_sigma": hasse_zeta(complex(sigma + float(control_delta), t), terms),
    }


def _height_control_approximations(
    target: HasseApproximation,
    *,
    control_ts: Sequence[float],
) -> Dict[str, HasseApproximation]:
    return {
        f"height_{index:02d}_t={float(t)!r}": hasse_zeta(
            complex(float(target.s.real), float(t)),
            int(target.terms),
        )
        for index, t in enumerate(control_ts)
    }


def _enrich_target_trajectory(
    target_rows: List[Dict[str, object]],
    *,
    local_rows: Dict[str, Sequence[Dict[str, object]]],
    height_rows: Dict[str, Sequence[Dict[str, object]]],
) -> None:
    for index, target_row in enumerate(target_rows):
        target_magnitude = float(target_row["masked_zeta"]["magnitude"])  # type: ignore[index]
        local_magnitudes = [
            float(rows[index]["masked_zeta"]["magnitude"])  # type: ignore[index]
            for rows in local_rows.values()
        ]
        height_magnitudes = [
            float(rows[index]["masked_zeta"]["magnitude"])  # type: ignore[index]
            for rows in height_rows.values()
        ]
        local_min = min(local_magnitudes)
        height_min = min(height_magnitudes)
        target_row.update(
            {
                "minimum_local_control_magnitude": local_min,
                "maximum_local_control_magnitude": max(local_magnitudes),
                "target_below_all_local_controls": target_magnitude < local_min,
                "local_control_to_target_ratio": (
                    float(local_min / target_magnitude)
                    if target_magnitude > 0.0
                    else None
                ),
                "minimum_height_control_magnitude": height_min,
                "maximum_height_control_magnitude": max(height_magnitudes),
                "target_below_all_height_controls": target_magnitude < height_min,
                "height_control_to_target_ratio": (
                    float(height_min / target_magnitude)
                    if target_magnitude > 0.0
                    else None
                ),
                "target_rank_among_height_grid_plus_target": 1
                + sum(value < target_magnitude for value in height_magnitudes),
            }
        )


def _control_summary(
    controls: Dict[str, HasseApproximation],
    trajectories: Dict[str, Sequence[Dict[str, object]]],
    *,
    completion_stage: Optional[int],
) -> Dict[str, object]:
    return {
        name: {
            "evaluation": approximation_payload(approximation),
            "trajectory_metrics": _trajectory_metrics(
                rows,
                completion_stage=completion_stage,
            ),
        }
        for name, approximation in controls.items()
        for rows in [trajectories[name]]
    }


def _deterministic_block_permutation(
    count: int,
    *,
    sample_index: int,
    block_size: int,
) -> List[int]:
    permutation: List[int] = []
    for start in range(0, int(count), int(block_size)):
        block = list(range(start, min(start + int(block_size), int(count))))
        block.sort(
            key=lambda index: hashlib.sha256(
                (
                    f"{PERMUTATION_SALT}:{sample_index}:{block_size}:"
                    f"{start}:{index}"
                ).encode("ascii")
            ).digest()
        )
        permutation.extend(block)
    return permutation


def _radii_for_assigned_contributions(
    approximation: HasseApproximation,
    *,
    arrival_stages: Sequence[Optional[int]],
    assigned_contributions: Sequence[complex],
    stage_horizon: int,
) -> List[float]:
    bridge_magnitude = float(abs(approximation.bridge_denominator))
    total_mass = float(math.fsum(abs(value) for value in assigned_contributions))
    radial_scale = total_mass / bridge_magnitude
    radii: List[float] = []
    for stage in range(1, int(stage_horizon) + 1):
        active_values = [
            contribution
            for arrival, contribution in zip(
                arrival_stages,
                assigned_contributions,
            )
            if arrival is not None and int(arrival) <= stage
        ]
        eta = _sum_complex(active_values)
        magnitude = float(abs(eta / approximation.bridge_denominator))
        radii.append(float(magnitude / radial_scale) if radial_scale > 0.0 else 0.0)
    return radii


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("cannot take a quantile of an empty sequence")
    position = (len(ordered) - 1) * float(probability)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return float(ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction)


def _null_metric_payload(
    values: Sequence[float],
    *,
    natural_value: float,
    higher_is_more_extreme: bool,
) -> Dict[str, object]:
    if higher_is_more_extreme:
        extreme_count = sum(value >= float(natural_value) for value in values)
        tail = "upper"
    else:
        extreme_count = sum(value <= float(natural_value) for value in values)
        tail = "lower"
    return {
        "natural_value": float(natural_value),
        "null_minimum": min(values),
        "null_q05": _quantile(values, 0.05),
        "null_median": _quantile(values, 0.5),
        "null_q95": _quantile(values, 0.95),
        "null_maximum": max(values),
        "null_mean": float(statistics.fmean(values)),
        "null_population_stdev": float(statistics.pstdev(values)),
        "extreme_tail": tail,
        "null_samples_at_least_as_extreme": int(extreme_count),
        "add_one_monte_carlo_tail_fraction": float(
            (extreme_count + 1) / (len(values) + 1)
        ),
        "minimum_attainable_add_one_tail_fraction": float(
            1.0 / (len(values) + 1)
        ),
        "reading": "exploratory deterministic null rank, not a formal p-value",
    }


def _block_local_permutation_null(
    approximation: HasseApproximation,
    *,
    arrival_stages: Sequence[Optional[int]],
    stage_horizon: int,
    sample_count: int,
    block_size: int,
) -> Dict[str, object]:
    complete = all(
        stage is not None and int(stage) <= int(stage_horizon)
        for stage in arrival_stages
    )
    if not complete:
        return {
            "status": "not_run_incomplete_arrival_schedule_at_horizon",
            "sample_count": 0,
            "block_size": int(block_size),
        }
    natural_radii = _radii_for_assigned_contributions(
        approximation,
        arrival_stages=arrival_stages,
        assigned_contributions=approximation.source_contributions,
        stage_horizon=int(stage_horizon),
    )
    natural = _radial_diagnostics(natural_radii)
    canonical_endpoint = (
        _sum_complex(approximation.source_contributions)
        / approximation.bridge_denominator
    )
    radial_scale = float(
        approximation.absolute_contribution_mass
        / abs(approximation.bridge_denominator)
    )
    normalized_endpoint_guard = float(
        max(64, int(stage_horizon)) * math.ulp(1.0)
    )
    streaks: List[float] = []
    inward_fractions: List[float] = []
    efficiencies: List[float] = []
    endpoint_differences: List[float] = []
    for sample_index in range(int(sample_count)):
        permutation = _deterministic_block_permutation(
            len(approximation.source_contributions),
            sample_index=sample_index,
            block_size=int(block_size),
        )
        assigned = [
            approximation.source_contributions[index] for index in permutation
        ]
        radii = _radii_for_assigned_contributions(
            approximation,
            arrival_stages=arrival_stages,
            assigned_contributions=assigned,
            stage_horizon=int(stage_horizon),
        )
        metrics = _radial_diagnostics(radii)
        permuted_endpoint = _sum_complex(assigned) / approximation.bridge_denominator
        endpoint_differences.append(float(abs(permuted_endpoint - canonical_endpoint)))
        streaks.append(float(metrics["longest_resolved_inward_streak"]))
        inward_value = metrics["resolved_inward_fraction"]
        efficiency_value = metrics["post_peak_radial_efficiency"]
        inward_fractions.append(float(inward_value) if inward_value is not None else 0.0)
        efficiencies.append(
            float(efficiency_value) if efficiency_value is not None else 0.0
        )
    natural_inward = natural["resolved_inward_fraction"]
    natural_efficiency = natural["post_peak_radial_efficiency"]
    natural_inward_value = (
        float(natural_inward) if natural_inward is not None else 0.0
    )
    natural_efficiency_value = (
        float(natural_efficiency) if natural_efficiency is not None else 0.0
    )
    maximum_endpoint_difference = max(endpoint_differences, default=0.0)
    maximum_normalized_endpoint_difference = (
        float(maximum_endpoint_difference / radial_scale)
        if radial_scale > 0.0
        else 0.0
    )
    return {
        "status": "complete",
        "sample_count": int(sample_count),
        "block_size": int(block_size),
        "null_hypothesis": (
            "permute whole external contribution values only within adjacent "
            "source blocks while preserving the graph arrival-stage slots, "
            "the full finite endpoint, and the coarse amplitude envelope"
        ),
        "permutation_algorithm": (
            "SHA-256 ordering with fixed salt; deterministic across Python versions; "
            "each prefix is accumulated with real/imaginary math.fsum"
        ),
        "terminal_endpoint_invariance": {
            "canonical_endpoint": complex_payload(canonical_endpoint),
            "maximum_absolute_zeta_difference": maximum_endpoint_difference,
            "maximum_normalized_difference": maximum_normalized_endpoint_difference,
            "normalized_binary64_guard": normalized_endpoint_guard,
            "absolute_binary64_guard": float(
                normalized_endpoint_guard * radial_scale
            ),
            "passes": maximum_normalized_endpoint_difference
            <= normalized_endpoint_guard,
        },
        "primary_fixed_v1_metric": "longest_resolved_inward_streak",
        "design_status": (
            "fixed_in_v1_after_exploratory_calibration_not_preregistered"
        ),
        "metrics": {
            "longest_resolved_inward_streak": _null_metric_payload(
                streaks,
                natural_value=float(natural["longest_resolved_inward_streak"]),
                higher_is_more_extreme=True,
            ),
            "resolved_inward_fraction": _null_metric_payload(
                inward_fractions,
                natural_value=natural_inward_value,
                higher_is_more_extreme=True,
            ),
            "post_peak_radial_efficiency": _null_metric_payload(
                efficiencies,
                natural_value=natural_efficiency_value,
                higher_is_more_extreme=True,
            ),
        },
        "claim_limit": (
            "an extreme rank shows sensitivity to the source-phase association; "
            "it does not make the ordering graph-unique or certify a zero"
        ),
        "degenerate_scoring_rule": (
            "trajectories with no resolved post-peak radial path receive zero "
            "inward fraction and zero radial efficiency"
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
    }


def _method_payload() -> Dict[str, object]:
    return {
        "name": "fixed_terminal_K_hasse_source_reveal",
        "formula": (
            "P_u(s) = sum_{n: arrival_mask(n)<=u} A_(K,n)*n^(-s) "
            "/ (1-2^(1-s))"
        ),
        "fixed_basis_warning": (
            "the exact A_(K,n) weights use terminal outer rows k=0..K-1 at "
            "every graph stage; P_u is not a stage-u Hasse approximation"
        ),
        "calculation_layer": "external_binary64_complex_over_graph_recorded_arrival_masks",
        "primary_mask": "operational_source_and_reciprocal_edge",
        "primary_mask_rule": (
            "source confirmed_stage<=u AND direct retained edge 1/n at stage<=u"
        ),
        "primary_mask_scope": (
            "confirmed-source plus reciprocal-witness gate for external analysis; "
            "the reciprocal result is not treated as an operand"
        ),
        "speculative_presence_mask_is_runtime_computation": False,
        "normalized_radius": (
            "rho_u = abs(P_u) / [sum_n abs(A_(K,n)*n^(-s)) / abs(1-2^(1-s))]"
        ),
        "cancellation_envelope": (
            "remaining unarrived L1 mass divided by eta-bridge magnitude; "
            "outside means the remaining finite terms cannot reach zero, while "
            "inside is necessary but never sufficient"
        ),
        "permutation_null": (
            "endpoint-preserving permutations of whole contributions inside "
            "predeclared adjacent source blocks of sizes 2 and 4"
        ),
        "error_model": {
            "rigorous_interval_bound": False,
            "binary64_step_guard": "max(64, stage_count)*epsilon in normalized units",
            "envelope_guard": "configured absolute zeta-magnitude guard",
            "monte_carlo_status": "deterministic exploratory rank_not_formal_p_value",
            "cutoff_stability": (
                "last two named finite-K changes must be below an independent "
                "relative stability threshold"
            ),
        },
    }


def _cutoff_stability(
    s: complex,
    *,
    hasse_terms: int,
    stability_tolerance: float,
) -> Dict[str, object]:
    count = int(hasse_terms)
    checkpoints = sorted(
        {
            max(2, count // 2),
            max(2, count - 16),
            max(2, count - 8),
            max(2, count - 4),
            count,
        }
    )
    rows: List[Dict[str, object]] = []
    previous: Optional[complex] = None
    changes: List[float] = []
    for terms in checkpoints:
        approximation = hasse_zeta(s, terms)
        change = (
            float(abs(approximation.zeta - previous))
            if approximation.zeta is not None and previous is not None
            else None
        )
        if change is not None:
            changes.append(change)
        rows.append(
            {
                "hasse_terms": terms,
                "status": approximation.status,
                "zeta": complex_payload(approximation.zeta),
                "change_from_previous_zeta": change,
            }
        )
        if approximation.zeta is not None:
            previous = approximation.zeta
    terminal = rows[-1]["zeta"]
    terminal_magnitude = (
        float(terminal["magnitude"])  # type: ignore[index]
        if isinstance(terminal, dict) and terminal["magnitude"] is not None
        else 0.0
    )
    threshold = float(stability_tolerance) * (1.0 + terminal_magnitude)
    final_two = changes[-2:]
    passes = len(final_two) == 2 and all(value <= threshold for value in final_two)
    return {
        "checkpoints": checkpoints,
        "rows": rows,
        "relative_stability_tolerance": float(stability_tolerance),
        "absolute_stability_threshold": threshold,
        "two_terminal_changes": final_two,
        "passes": passes,
        "status": "empirical_binary64_cutoff_check_not_error_bound",
    }


def _claim_boundary() -> Dict[str, object]:
    return {
        "evidence_layer": "external_complex_analysis_conditioned_on_strict_graph_arrival",
        "claim_status": "empirical_cancellation_trajectory_only",
        "allowed_claim_language": [
            "The report shows when fixed external Hasse source terms become visible under named graph-recorded masks.",
            "The aligned operational mask may be compared with speculative-presence and local-coordinate controls.",
            "An unusually monotone radial collapse may be reported as an empirical property of the fixed finite source order.",
            "Reciprocal witness reinforcement may annotate a source without counting its analytic contribution more than once.",
        ],
        "disallowed_claim_language": [
            "Do not describe source-node presence as operand availability before confirmed_stage.",
            "Do not call fixed-K source reveal a stage-u zeta approximation or runtime zeta calculation.",
            "Do not call the natural n-prefix graph-unique while readiness and reciprocal schedules both equal n.",
            "Do not claim a graph-constructed zero, zero discovery, zero certification, or evidence for the Riemann hypothesis.",
            "Do not treat an inside-envelope reading or exploratory permutation rank as proof.",
            "Do not multiply an external source contribution by its reciprocal witness count.",
        ],
        "kill_criteria": [
            "Reject the primary reading if the operational terminal mask fails to reconstruct the finite Hasse endpoint.",
            "Reject any claimed computational effect confined to the speculative node-presence mask.",
            "Attribute tail-to-endpoint behavior shared by local controls to the Hasse amplitude envelope.",
            "Reject graph-topology language while confirmed-ready and reciprocal-backed schedules remain identical.",
            "Treat differing matched-prefix schedules as a corpus or instrumentation fault.",
        ],
    }


def _validate_inputs(
    *,
    sigma: float,
    t: float,
    hasse_terms: int,
    control_delta: float,
    height_control_ts: Sequence[float],
    envelope_guard: float,
    stability_tolerance: float,
    near_zero_tolerance: float,
    permutation_samples: int,
    target_kind: str,
    target_label: Optional[str],
    full_scan: bool,
) -> Dict[str, object]:
    numeric = [
        sigma,
        t,
        control_delta,
        envelope_guard,
        stability_tolerance,
        near_zero_tolerance,
        *height_control_ts,
    ]
    if not all(math.isfinite(float(value)) for value in numeric):
        raise ValueError("all numeric inputs must be finite")
    if int(hasse_terms) < 2:
        raise ValueError("hasse_terms must be >= 2")
    if int(hasse_terms) > HARD_MAX_HASSE_TERMS:
        raise ValueError(
            f"hasse_terms>{HARD_MAX_HASSE_TERMS} exceeds the hard finite-source limit"
        )
    if int(permutation_samples) < 1:
        raise ValueError("permutation_samples must be >= 1")
    if int(permutation_samples) > HARD_MAX_PERMUTATION_SAMPLES:
        raise ValueError(
            f"permutation_samples>{HARD_MAX_PERMUTATION_SAMPLES} exceeds the hard workload limit"
        )
    if float(control_delta) <= 0.0:
        raise ValueError("control_delta must be > 0")
    if float(envelope_guard) <= 0.0:
        raise ValueError("envelope_guard must be > 0")
    if float(stability_tolerance) <= 0.0:
        raise ValueError("stability_tolerance must be > 0")
    if float(near_zero_tolerance) <= 0.0:
        raise ValueError("near_zero_tolerance must be > 0")
    if not height_control_ts:
        raise ValueError("height_control_ts must not be empty")
    if len(height_control_ts) > MAX_HEIGHT_CONTROLS:
        raise ValueError(
            f"at most {MAX_HEIGHT_CONTROLS} height controls are allowed"
        )
    if len(set(float(value) for value in height_control_ts)) != len(height_control_ts):
        raise ValueError("height_control_ts must be distinct")
    if any(float(value) == float(t) for value in height_control_ts):
        raise ValueError("height controls must not equal the target t")
    if str(target_kind) not in TARGET_KINDS:
        raise ValueError(
            "target_kind must be one of " + ", ".join(sorted(TARGET_KINDS))
        )
    domain = _input_domain(float(sigma))
    if str(target_kind) in {
        "user_supplied_reference_zero",
        "numerical_candidate",
    } and not bool(domain["inside_open_critical_strip"]):
        raise ValueError(
            "nontrivial-zero reference/candidate modes require 0 < sigma < 1"
        )
    if (
        str(target_kind) == "user_supplied_reference_zero"
        and not str(target_label or "").strip()
    ):
        raise ValueError("user_supplied_reference_zero requires target_label")
    if not full_scan:
        exceeded: List[str] = []
        if int(hasse_terms) > MAX_HASSE_TERMS:
            exceeded.append(f"hasse_terms>{MAX_HASSE_TERMS}")
        if int(permutation_samples) > MAX_PERMUTATION_SAMPLES:
            exceeded.append(f"permutation_samples>{MAX_PERMUTATION_SAMPLES}")
        if exceeded:
            raise ValueError(
                "probe workload limit exceeded ("
                + ", ".join(exceeded)
                + "); pass --full-scan to acknowledge the larger external calculation"
            )
    return domain


def zeta_arrival_probe(
    *,
    db_path: Path,
    sigma: float,
    t: float,
    hasse_terms: int = 64,
    stage_horizon: Optional[int] = None,
    control_delta: float = 0.01,
    height_control_ts: Sequence[float] = DEFAULT_HEIGHT_CONTROLS,
    envelope_guard: float = 1e-12,
    stability_tolerance: float = DEFAULT_STABILITY_TOLERANCE,
    near_zero_tolerance: float = DEFAULT_NEAR_ZERO_TOLERANCE,
    permutation_samples: int = DEFAULT_PERMUTATION_SAMPLES,
    target_kind: str = "numerical_candidate",
    target_label: Optional[str] = None,
    full_scan: bool = False,
) -> Dict[str, object]:
    domain = _validate_inputs(
        sigma=float(sigma),
        t=float(t),
        hasse_terms=int(hasse_terms),
        control_delta=float(control_delta),
        height_control_ts=height_control_ts,
        envelope_guard=float(envelope_guard),
        stability_tolerance=float(stability_tolerance),
        near_zero_tolerance=float(near_zero_tolerance),
        permutation_samples=int(permutation_samples),
        target_kind=str(target_kind),
        target_label=target_label,
        full_scan=bool(full_scan),
    )
    target = hasse_zeta(complex(float(sigma), float(t)), int(hasse_terms))
    if target.zeta is None:
        raise ValueError(f"target is not finite under eta bridge: {target.status}")
    cutoff_stability = _cutoff_stability(
        target.s,
        hasse_terms=int(hasse_terms),
        stability_tolerance=float(stability_tolerance),
    )
    local_controls = _local_control_approximations(
        target,
        control_delta=float(control_delta),
    )
    height_controls = _height_control_approximations(
        target,
        control_ts=height_control_ts,
    )
    all_controls = {**local_controls, **height_controls}
    unavailable = [
        name for name, approximation in all_controls.items() if approximation.zeta is None
    ]
    if unavailable:
        raise ValueError(
            "control points are not finite under eta bridge: " + ", ".join(unavailable)
        )

    with closing(connect_readonly(Path(db_path))) as conn:
        alignment = require_strict_alignment(conn)
        corpus = _corpus_payload(
            conn,
            db_path=Path(db_path),
            alignment=alignment,
        )
        latest = corpus["latest_stage"]
        if not isinstance(latest, dict):
            raise ValueError("selected corpus has no recorded stages")
        latest_stage = int(latest["stage"])
        horizon = (
            min(int(hasse_terms), latest_stage)
            if stage_horizon is None
            else int(stage_horizon)
        )
        if horizon < 1:
            raise ValueError("stage_horizon must be >= 1")
        if horizon > latest_stage:
            raise ValueError("stage_horizon must not exceed the latest recorded stage")
        if horizon > int(hasse_terms):
            raise ValueError(
                "stage_horizon must not exceed hasse_terms; later flat stages "
                "would dilute trajectory metrics"
            )
        if horizon > HARD_MAX_STAGE_HORIZON:
            raise ValueError(
                f"stage_horizon>{HARD_MAX_STAGE_HORIZON} exceeds the hard report limit"
            )
        corpus["stage_prefix_validation"] = _validate_stage_prefix(
            conn,
            stage_horizon=horizon,
            config=corpus["config"],
        )
        schedules = _load_source_schedules(conn, hasse_terms=int(hasse_terms))

    schedule_summary = _schedule_summary(
        schedules,
        stage_horizon=horizon,
    )
    schedule_rows = _schedule_rows_payload(
        schedules,
        stage_horizon=horizon,
    )
    for row, weight, contribution in zip(
        schedule_rows,
        target.source_weights,
        target.source_contributions,
    ):
        row["exact_external_hasse_weight"] = fraction_payload(weight)
        row["external_target_contribution"] = complex_payload(contribution)

    mask_results: Dict[str, Dict[str, object]] = {}
    for mask_kind in MASK_KINDS:
        mask_summary = schedule_summary["masks"][mask_kind]  # type: ignore[index]
        completion_stage = mask_summary["completion_stage"]  # type: ignore[index]
        target_rows = _trajectory(
            target,
            schedules=schedules,
            mask_kind=mask_kind,
            stage_horizon=horizon,
            envelope_guard=float(envelope_guard),
        )
        local_rows = {
            name: _trajectory(
                approximation,
                schedules=schedules,
                mask_kind=mask_kind,
                stage_horizon=horizon,
                envelope_guard=float(envelope_guard),
            )
            for name, approximation in local_controls.items()
        }
        height_rows = {
            name: _trajectory(
                approximation,
                schedules=schedules,
                mask_kind=mask_kind,
                stage_horizon=horizon,
                envelope_guard=float(envelope_guard),
            )
            for name, approximation in height_controls.items()
        }
        _enrich_target_trajectory(
            target_rows,
            local_rows=local_rows,
            height_rows=height_rows,
        )
        mask_results[mask_kind] = {
            "mask_status": mask_summary,
            "target_trajectory_metrics": _trajectory_metrics(
                target_rows,
                completion_stage=completion_stage,
            ),
            "target_trajectory": target_rows,
            "local_control_trajectory_metrics": {
                name: _trajectory_metrics(
                    rows,
                    completion_stage=completion_stage,
                )
                for name, rows in local_rows.items()
            },
            "height_control_trajectory_metrics": {
                name: _trajectory_metrics(
                    rows,
                    completion_stage=completion_stage,
                )
                for name, rows in height_rows.items()
            },
        }

    signature_groups: Dict[Tuple[Optional[int], ...], List[str]] = defaultdict(list)
    for mask_kind in MASK_KINDS:
        full_signature = _arrival_stages(schedules, mask_kind)
        observed_signature = tuple(
            int(stage)
            if stage is not None and int(stage) <= int(horizon)
            else None
            for stage in full_signature
        )
        signature_groups[observed_signature].append(mask_kind)
    permutation_nulls: List[Dict[str, object]] = []
    for signature, mask_kinds in signature_groups.items():
        permutation_nulls.append(
            {
                "mask_kinds_with_identical_schedule": mask_kinds,
                "representative_mask": mask_kinds[0],
                "block_size_2": _block_local_permutation_null(
                    target,
                    arrival_stages=signature,
                    stage_horizon=horizon,
                    sample_count=int(permutation_samples),
                    block_size=2,
                ),
                "block_size_4_sensitivity": _block_local_permutation_null(
                    target,
                    arrival_stages=signature,
                    stage_horizon=horizon,
                    sample_count=int(permutation_samples),
                    block_size=4,
                ),
            }
        )

    operational = mask_results["operational_source_and_reciprocal_edge"]
    operational_metrics = operational["target_trajectory_metrics"]
    present = mask_results["source_node_present"]
    present_metrics = present["target_trajectory_metrics"]
    operational_rows = operational["target_trajectory"]
    reconstructed = operational_rows[-1]["masked_zeta"]  # type: ignore[index]
    endpoint_difference = math.hypot(
        float(reconstructed["real"]) - float(target.zeta.real),
        float(reconstructed["imag"]) - float(target.zeta.imag),
    )
    local_tail_controls = operational["local_control_trajectory_metrics"]
    target_tail_captures = operational_metrics[
        "persistent_tail_to_full_capture_stages"
    ]
    tail_capture_matches = {
        name: metrics["persistent_tail_to_full_capture_stages"]
        == target_tail_captures
        for name, metrics in local_tail_controls.items()  # type: ignore[union-attr]
    }
    tail_capture_differences = [
        abs(int(control_stages[key]) - int(target_stage))
        for metrics in local_tail_controls.values()  # type: ignore[union-attr]
        for control_stages in [metrics["persistent_tail_to_full_capture_stages"]]
        for key, target_stage in target_tail_captures.items()
        if target_stage is not None and control_stages[key] is not None
    ]
    radial_scale = float(
        target.absolute_contribution_mass / abs(target.bridge_denominator)
    )
    preflight_passes = int(hasse_terms) >= recommended_hasse_terms(t)
    endpoint_normalized_difference = (
        float(endpoint_difference / radial_scale) if radial_scale > 0.0 else 0.0
    )
    endpoint_normalized_guard = float(
        max(64, int(hasse_terms)) * math.ulp(1.0)
    )
    reconstruction_passes = (
        endpoint_normalized_difference <= endpoint_normalized_guard
    )
    operational_mask_status = schedule_summary["masks"][
        "operational_source_and_reciprocal_edge"
    ]
    operational_complete = bool(
        operational_mask_status["completion_stage"] is not None  # type: ignore[index]
        and int(operational_mask_status["arrived_source_count_at_horizon"])  # type: ignore[index]
        == int(hasse_terms)
    )
    minimum_resolved_steps = max(8, int(hasse_terms) // 2)
    inward_fraction = operational_metrics["resolved_inward_fraction"]
    radial_efficiency = operational_metrics["post_peak_radial_efficiency"]
    radial_criteria_pass = bool(
        int(operational_metrics["resolved_post_peak_step_count"])
        >= minimum_resolved_steps
        and int(operational_metrics["resolved_outward_step_count"]) == 0
        and inward_fraction is not None
        and float(inward_fraction) >= MIN_RADIAL_INWARD_FRACTION
        and radial_efficiency is not None
        and float(radial_efficiency) >= MIN_RADIAL_EFFICIENCY
    )
    local_control_separation_pass = bool(
        operational_metrics.get("first_persistent_below_all_local_controls_stage")
        is not None
    )
    primary_null_group = next(
        row
        for row in permutation_nulls
        if "operational_source_and_reciprocal_edge"
        in row["mask_kinds_with_identical_schedule"]
    )
    primary_block_null = primary_null_group["block_size_2"]
    primary_null_complete = primary_block_null["status"] == "complete"
    primary_null_tail_fraction: Optional[float] = None
    primary_null_minimum_tail_fraction: Optional[float] = None
    primary_null_endpoint_invariance_pass = False
    if primary_null_complete:
        primary_metric = primary_block_null["metrics"][
            "longest_resolved_inward_streak"
        ]
        primary_null_tail_fraction = float(
            primary_metric["add_one_monte_carlo_tail_fraction"]
        )
        primary_null_minimum_tail_fraction = float(
            primary_metric["minimum_attainable_add_one_tail_fraction"]
        )
        primary_null_endpoint_invariance_pass = bool(
            primary_block_null["terminal_endpoint_invariance"]["passes"]
        )
    primary_null_rank_resolution_sufficient = bool(
        primary_null_minimum_tail_fraction is not None
        and primary_null_minimum_tail_fraction <= MAX_PRIMARY_NULL_TAIL_FRACTION
    )
    primary_null_rank_pass = bool(
        primary_null_complete
        and primary_null_endpoint_invariance_pass
        and primary_null_rank_resolution_sufficient
        and primary_null_tail_fraction is not None
        and primary_null_tail_fraction <= MAX_PRIMARY_NULL_TAIL_FRACTION
    )
    residual_below_tolerance = bool(
        abs(target.zeta) <= float(near_zero_tolerance)
    )
    is_control = target_kind == "control"
    if not operational_complete:
        trajectory_classification = (
            "incomplete_control_trajectory"
            if is_control
            else "incomplete_operational_schedule_arrival_exploration"
        )
    elif not preflight_passes:
        trajectory_classification = (
            "underresolved_control_trajectory"
            if is_control
            else "underresolved_finite_hasse_exploration"
        )
    elif not bool(cutoff_stability["passes"]):
        trajectory_classification = (
            "cutoff_unstable_control_trajectory"
            if is_control
            else "cutoff_unstable_arrival_exploration"
        )
    elif not reconstruction_passes:
        trajectory_classification = (
            "control_terminal_reconstruction_failed"
            if is_control
            else "terminal_reconstruction_failed"
        )
    elif is_control:
        trajectory_classification = "complete_numerically_stable_control_trajectory"
    elif not residual_below_tolerance:
        trajectory_classification = (
            "residual_above_configured_near_zero_tolerance"
        )
    elif not radial_criteria_pass:
        trajectory_classification = (
            "near_zero_without_configured_v1_radial_collapse"
        )
    elif not local_control_separation_pass:
        trajectory_classification = (
            "radial_collapse_without_persistent_local_control_separation"
        )
    elif not primary_null_rank_resolution_sufficient:
        trajectory_classification = (
            "primary_block_null_sample_resolution_insufficient"
        )
    elif not primary_null_rank_pass:
        trajectory_classification = (
            "radial_collapse_not_extreme_under_primary_block_null"
        )
    elif target_kind == "user_supplied_reference_zero":
        trajectory_classification = (
            "empirical_radial_collapse_at_caller_supplied_reference_coordinate"
        )
    else:
        trajectory_classification = (
            "empirical_radial_collapse_at_numerical_candidate_coordinate"
        )

    full_natural_order = bool(
        schedule_summary["operational_schedule_is_natural_source_order"]
    )
    observed_natural_prefix = bool(
        schedule_summary[
            "operational_schedule_is_observed_natural_prefix_through_horizon"
        ]
    )
    pair_comparison = schedule_summary[
        "operand_ready_and_direct_reciprocal_comparison"
    ]
    if full_natural_order and pair_comparison["status"] == "full_schedule_identical":
        graph_specificity_reading = (
            "the completed aligned trajectory is the ordinary n-prefix; no "
            "additional graph topology orders the external analytic terms"
        )
    elif observed_natural_prefix:
        graph_specificity_reading = (
            "the aligned schedule is the ordinary observed n-prefix through the "
            "requested horizon; later sources are right-censored, so a full-order "
            "claim is not available"
        )
    else:
        graph_specificity_reading = (
            "the observed aligned schedule is not the ordinary natural prefix; "
            "inspect the reported schedule mismatches before interpretation"
        )

    maximum_tail_capture_difference = max(tail_capture_differences, default=None)
    if tail_capture_matches and all(tail_capture_matches.values()):
        tail_capture_reading = (
            "all local controls exactly match target tail-to-endpoint capture stages; "
            "attribute this to the fixed Hasse amplitude envelope"
        )
    elif maximum_tail_capture_difference is not None and maximum_tail_capture_difference <= 1:
        tail_capture_reading = (
            "local-control tail-to-endpoint captures differ by at most one stage; "
            "attribute this near-match to the fixed Hasse amplitude envelope"
        )
    else:
        tail_capture_reading = (
            "local-control tail-to-endpoint captures materially differ from the "
            "target in this report; no shared-envelope match is claimed"
        )
    return {
        "report_type": "zeta_cancellation_arrival_external_probe",
        "config": {
            "sigma": float(sigma),
            "t": float(t),
            "hasse_terms": int(hasse_terms),
            "stage_horizon": horizon,
            "control_delta": float(control_delta),
            "height_control_ts": [float(value) for value in height_control_ts],
            "envelope_guard": float(envelope_guard),
            "stability_tolerance": float(stability_tolerance),
            "near_zero_tolerance": float(near_zero_tolerance),
            "permutation_samples_per_block_size": int(permutation_samples),
            "target_kind": str(target_kind),
            "target_label": target_label,
            "full_scan": bool(full_scan),
        },
        "input_domain": domain,
        "claim_boundary": _claim_boundary(),
        "method": _method_payload(),
        "corpus": corpus,
        "source_schedule": {
            "scope": (
                "retrospective schedule metadata with explicit horizon-censored "
                "fields; raw stages after the horizon are not prefix-validated"
            ),
            "summary": schedule_summary,
            "rows": schedule_rows,
        },
        "coordinate_evaluations": {
            "target": {
                "evaluation": approximation_payload(target),
                "target_kind": str(target_kind),
                "target_label": target_label,
                "reference_status": (
                    "caller_supplied_not_independently_verified_by_probe"
                    if target_kind == "user_supplied_reference_zero"
                    else "not_designated_as_reference"
                ),
                "radial_normalization_scale": radial_scale,
                "numeric_preflight": {
                    "empirical_recommended_hasse_terms": recommended_hasse_terms(t),
                    "configured_hasse_terms": int(hasse_terms),
                    "configured_meets_empirical_recommendation": preflight_passes,
                    "status": "heuristic_only_not_an_error_bound",
                },
                "cutoff_stability": cutoff_stability,
            },
            "local_controls": {
                name: approximation_payload(approximation)
                for name, approximation in local_controls.items()
            },
            "height_controls": {
                name: approximation_payload(approximation)
                for name, approximation in height_controls.items()
            },
        },
        "mask_results": mask_results,
        "endpoint_preserving_permutation_nulls": permutation_nulls,
        "summary": {
            "classification": trajectory_classification,
            "target_full_finite_residual": float(abs(target.zeta)),
            "near_zero_tolerance": float(near_zero_tolerance),
            "target_residual_below_near_zero_tolerance": residual_below_tolerance,
            "target_radial_normalization_scale": radial_scale,
            "operational_terminal_reconstruction_difference": endpoint_difference,
            "operational_terminal_reconstruction_normalized_difference": (
                endpoint_normalized_difference
            ),
            "operational_terminal_reconstruction_normalized_binary64_guard": (
                endpoint_normalized_guard
            ),
            "operational_terminal_reconstruction_absolute_binary64_guard": (
                endpoint_normalized_guard * radial_scale
            ),
            "operational_terminal_reconstruction_passes_binary64_guard": (
                reconstruction_passes
            ),
            "operational_schedule_complete_at_horizon": operational_complete,
            "operational_schedule_is_natural_source_order": schedule_summary[
                "operational_schedule_is_natural_source_order"
            ],
            "operand_ready_and_reciprocal_schedules_identical": schedule_summary[
                "operand_ready_and_direct_reciprocal_stage_identical"
            ],
            "graph_specificity_reading": graph_specificity_reading,
            "operational_target_metrics": operational_metrics,
            "configured_v1_collapse_criteria": {
                "design_status": (
                    "fixed_in_v1_after_exploratory_calibration_not_preregistered"
                ),
                "minimum_resolved_post_peak_steps": minimum_resolved_steps,
                "minimum_resolved_inward_fraction": MIN_RADIAL_INWARD_FRACTION,
                "maximum_resolved_outward_steps": 0,
                "minimum_post_peak_radial_efficiency": MIN_RADIAL_EFFICIENCY,
                "require_persistent_below_all_local_controls": True,
                "maximum_primary_block_2_add_one_tail_fraction": (
                    MAX_PRIMARY_NULL_TAIL_FRACTION
                ),
                "radial_metrics_pass": radial_criteria_pass,
                "local_control_separation_pass": local_control_separation_pass,
                "primary_block_null_complete": primary_null_complete,
                "primary_block_null_endpoint_invariance_pass": (
                    primary_null_endpoint_invariance_pass
                ),
                "primary_block_null_minimum_attainable_add_one_tail_fraction": (
                    primary_null_minimum_tail_fraction
                ),
                "primary_block_null_rank_resolution_sufficient": (
                    primary_null_rank_resolution_sufficient
                ),
                "primary_block_2_add_one_tail_fraction": (
                    primary_null_tail_fraction
                ),
                "primary_block_null_rank_pass": primary_null_rank_pass,
            },
            "speculative_presence_target_metrics": present_metrics,
            "speculative_presence_effect_is_admissible_runtime_computation": False,
            "speculative_presence_reading": (
                "source_node_present is a speculative, aperture-conditioned "
                "visibility mask; assess any effect only in a matched-aperture "
                "comparison and never promote it to runtime computation"
            ),
            "tail_capture_exact_match_by_local_control": tail_capture_matches,
            "tail_capture_maximum_local_control_stage_difference": (
                maximum_tail_capture_difference
            ),
            "tail_capture_reading": tail_capture_reading,
            "target_certified_zero": False,
            "runtime_complex_semantics_added": False,
        },
    }


def parse_float_list(raw: str) -> List[float]:
    values: List[float] = []
    for part in str(raw).split(","):
        text = part.strip()
        if not text:
            continue
        try:
            value = float(text)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                "must be a comma-separated list of numbers"
            ) from exc
        if not math.isfinite(value):
            raise argparse.ArgumentTypeError("all list values must be finite")
        values.append(value)
    if not values:
        raise argparse.ArgumentTypeError("at least one value is required")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Reveal fixed external Hasse source contributions through strict graph "
            "arrival masks and compare aligned, speculative, coordinate, and "
            "endpoint-preserving permutation controls."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--sigma", type=finite_float, required=True)
    parser.add_argument("--t", type=finite_float, required=True)
    parser.add_argument("--hasse-terms", type=positive_int, default=64)
    parser.add_argument("--stage-horizon", type=positive_int)
    parser.add_argument("--control-delta", type=positive_float, default=0.01)
    parser.add_argument(
        "--height-control-ts",
        type=parse_float_list,
        default=list(DEFAULT_HEIGHT_CONTROLS),
    )
    parser.add_argument("--envelope-guard", type=positive_float, default=1e-12)
    parser.add_argument(
        "--stability-tolerance",
        type=positive_float,
        default=DEFAULT_STABILITY_TOLERANCE,
    )
    parser.add_argument(
        "--near-zero-tolerance",
        type=positive_float,
        default=DEFAULT_NEAR_ZERO_TOLERANCE,
    )
    parser.add_argument(
        "--permutation-samples",
        type=positive_int,
        default=DEFAULT_PERMUTATION_SAMPLES,
    )
    parser.add_argument(
        "--target-kind",
        choices=sorted(TARGET_KINDS),
        default="numerical_candidate",
    )
    parser.add_argument("--target-label")
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
    payload = zeta_arrival_probe(
        db_path=Path(args.db),
        sigma=float(args.sigma),
        t=float(args.t),
        hasse_terms=int(args.hasse_terms),
        stage_horizon=(
            int(args.stage_horizon) if args.stage_horizon is not None else None
        ),
        control_delta=float(args.control_delta),
        height_control_ts=args.height_control_ts,
        envelope_guard=float(args.envelope_guard),
        stability_tolerance=float(args.stability_tolerance),
        near_zero_tolerance=float(args.near_zero_tolerance),
        permutation_samples=int(args.permutation_samples),
        target_kind=str(args.target_kind),
        target_label=str(args.target_label) if args.target_label else None,
        full_scan=bool(args.full_scan),
    )
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_zeta_arrival_probe.v1",
        include_checksums=bool(args.write or args.with_checksums),
    )
    payload["report_metadata"]["source_db_sha256"] = (  # type: ignore[index]
        file_sha256(Path(args.db)) if bool(args.write or args.with_checksums) else None
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
