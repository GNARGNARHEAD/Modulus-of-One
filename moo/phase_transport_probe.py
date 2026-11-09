from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from moo.paths import PROJECT_ROOT
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

from moo.graph_corpus import format_key
from moo.phase import classify_phase_operation, integer_division_branch
from moo.research_utils import (
    connect_readonly,
    emit_json,
    file_sha256,
    positive_int,
    report_metadata,
)


SCHEMA_VERSION = "moo_phase_transport_probe.v1"
MIN_DENOMINATOR = 3
DEFAULT_MAX_DENOMINATOR = 24
DEFAULT_PATH_LENGTH = 8
DEFAULT_MAX_OCCURRENCES_PER_Q = 512
DEFAULT_MAX_OUT_DEGREE = 32
DEFAULT_MAX_PATHS_PER_Q = 64
DEFAULT_NULL_SAMPLES = 4096
DEFAULT_STAGE_BIN_WIDTH = 1
DEFAULT_SEED = 1729
FROZEN_PRIMARY_EXPERIMENT_ID = "phase_provenance_transport_u40_q24_l8_v1"
FROZEN_PRIMARY_PREREG_RELATIVE_PATH = Path(
    "out/experiments/geometry/quarantined_phase_transport/"
    "phase_provenance_transport_u40_q24_l8_v1.pre.md"
)
FROZEN_PRIMARY_PREREG_SHA256 = (
    "5b292f2b446ecc6452b288ed811ec12d5e1bbbd2eb9161c0acc777b35a5da4b1"
)
FROZEN_PRIMARY_DB_SHA256 = (
    "12d358def1827b217a603a6da1aa793aa3525eb28b135fd3991af1bbcdc279ad"
)
FROZEN_PRIMARY_CORPUS_CONFIG = {
    "generator": "strict_stage_moo_graph",
    "max_abs_p": 200,
    "max_abs_q": 200,
    "max_abs_value": 40.0,
    "max_stage": 40,
    "retain_confirmed_edges": True,
}
FROZEN_PRIMARY_CORPUS_SCHEMA_VERSION = "1"
FROZEN_FOLLOWUP_EXPERIMENT_ID = (
    "phase_provenance_transport_u80_q24_l8_v1_followup"
)
FROZEN_FOLLOWUP_PREREG_RELATIVE_PATH = Path(
    "out/experiments/geometry/quarantined_phase_transport/"
    "phase_provenance_transport_u80_q24_l8_v1_followup.pre.md"
)
FROZEN_FOLLOWUP_PREREG_SHA256 = (
    "a7007fe5e4e20a0bacd6b02b098b7f25923ddf449a7e0dc549c91eaf5aaeb354"
)
FROZEN_FOLLOWUP_DB_SHA256 = (
    "796e043087eee8908c840d21f1c14235310c0093e816927bbab8374fbd0d4780"
)
FROZEN_FOLLOWUP_CORPUS_CONFIG = {
    "generator": "strict_stage_moo_graph",
    "max_abs_p": 200,
    "max_abs_q": 200,
    "max_abs_value": 4.0,
    "max_stage": 80,
    "retain_confirmed_edges": True,
}
FROZEN_FOLLOWUP_CORPUS_SCHEMA_VERSION = "1"

FROZEN_EXPERIMENTS: Mapping[str, Mapping[str, object]] = {
    FROZEN_PRIMARY_EXPERIMENT_ID: {
        "role": "primary",
        "configuration_status": "frozen_u40_q24_l8_primary",
        "database_suffix": "out/experiments/circle_as_one_u40_wide.sqlite",
        "database_sha256": FROZEN_PRIMARY_DB_SHA256,
        "corpus_config": FROZEN_PRIMARY_CORPUS_CONFIG,
        "corpus_schema_version": FROZEN_PRIMARY_CORPUS_SCHEMA_VERSION,
        "prereg_relative_path": FROZEN_PRIMARY_PREREG_RELATIVE_PATH,
        "prereg_sha256": FROZEN_PRIMARY_PREREG_SHA256,
        "checkpoint": 40,
    },
    FROZEN_FOLLOWUP_EXPERIMENT_ID: {
        "role": "aperture_resolution_followup",
        "configuration_status": "frozen_u80_q24_l8_aperture_followup",
        "database_suffix": "out/experiments/circle_as_one_u80.sqlite",
        "database_sha256": FROZEN_FOLLOWUP_DB_SHA256,
        "corpus_config": FROZEN_FOLLOWUP_CORPUS_CONFIG,
        "corpus_schema_version": FROZEN_FOLLOWUP_CORPUS_SCHEMA_VERSION,
        "prereg_relative_path": FROZEN_FOLLOWUP_PREREG_RELATIVE_PATH,
        "prereg_sha256": FROZEN_FOLLOWUP_PREREG_SHA256,
        "checkpoint": 80,
    },
}

# These are unconditional safety ceilings, not tunable CLI defaults.
MAX_DENOMINATOR = 128
MAX_PATH_LENGTH = 16
# Frozen provenance caps are also the absolute ceilings in every mode.
MAX_OCCURRENCES_PER_Q = DEFAULT_MAX_OCCURRENCES_PER_Q
MAX_OUT_DEGREE = DEFAULT_MAX_OUT_DEGREE
MAX_PATHS_PER_Q = DEFAULT_MAX_PATHS_PER_Q
MAX_NULL_SAMPLES = 16_384
MAX_DIVISION_EDGE_SCAN = 500_000
MAX_MATERIALIZED_EXPOSURE_RESULTS = 250_000
MAX_ADJACENCY_CANDIDATES = 5_000_000
MAX_DFS_STATES_PER_SEED = 100_000
MAX_TOTAL_DFS_STATES = 5_000_000
MAX_NULL_POSITION_EVALUATIONS = 125_000_000

MIN_HOLDOUT_PATHS = 32
MIN_HOLDOUT_DENOMINATORS = 4
MIN_MUTABLE_POSITIONS = 16
MIN_MUTABLE_FRACTION = Fraction(1, 4)
MIN_DECISION_NULL_SAMPLES = 100


@dataclass(frozen=True)
class NodeValue:
    node_id: int
    p: int
    q: int
    first_stage: int
    confirmed_stage: Optional[int]

    @property
    def value(self) -> Fraction:
        return Fraction(self.p, self.q)


@dataclass(frozen=True)
class DivisionOccurrence:
    edge_id: int
    stage: int
    left: NodeValue
    right: NodeValue
    result: NodeValue
    residue: int
    exposure: int

    @property
    def q(self) -> int:
        return self.result.q

    @property
    def input_ids(self) -> Tuple[int, ...]:
        return tuple(sorted({self.left.node_id, self.right.node_id}))

    @property
    def semantic_key(self) -> Tuple[int, ...]:
        """Insertion-order-independent identity for one strict division occurrence."""

        return (
            self.stage,
            self.left.p,
            self.left.q,
            self.right.p,
            self.right.q,
            self.result.p,
            self.result.q,
        )


@dataclass(frozen=True)
class ProvenancePath:
    q: int
    occurrences: Tuple[DivisionOccurrence, ...]
    transitions: Tuple[Tuple[int, ...], ...]
    split: str
    path_hash: str


def _hash_digest(seed: int, purpose: str, *parts: object) -> bytes:
    material = "|".join([str(int(seed)), purpose, *(str(part) for part in parts)])
    return hashlib.sha256(material.encode("ascii")).digest()


def _hash_rank(seed: int, purpose: str, *parts: object) -> Tuple[bytes, Tuple[str, ...]]:
    return (_hash_digest(seed, purpose, *parts), tuple(str(part) for part in parts))


def _fraction_payload(value: Fraction) -> Dict[str, object]:
    return {
        "frac": format_key((int(value.numerator), int(value.denominator))),
        "p": int(value.numerator),
        "q": int(value.denominator),
    }


def _node_payload(node: NodeValue, checkpoint_stage: int) -> Dict[str, object]:
    confirmed = (
        node.confirmed_stage is not None
        and node.confirmed_stage <= checkpoint_stage
        and node.q == 1
        and node.p >= 1
    )
    return {
        "node_id": node.node_id,
        "value": _fraction_payload(node.value),
        "first_stage": node.first_stage,
        "confirmed_stage": node.confirmed_stage,
        "status_at_checkpoint": (
            "confirmed_positive_spine" if confirmed else "speculative_rational"
        ),
    }


def _latest_stage(conn: sqlite3.Connection) -> int:
    stage_row = conn.execute(
        "SELECT COALESCE(MAX(stage), 0) AS stage FROM stages"
    ).fetchone()
    edge_row = conn.execute(
        "SELECT COALESCE(MAX(stage), 0) AS stage FROM edges"
    ).fetchone()
    return max(int(stage_row["stage"]), int(edge_row["stage"]))


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row is not None else None


def _checkpoint_alignment_audit(
    conn: sqlite3.Connection,
    checkpoint_stage: int,
    *,
    require_frontier_stage_contract: bool,
) -> Dict[str, object]:
    null_operands = int(
        conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM edges
            WHERE stage <= ? AND op != 'seed'
              AND (left_node_id IS NULL OR right_node_id IS NULL)
            """,
            (checkpoint_stage,),
        ).fetchone()["n"]
    )
    dangling_operands = int(
        conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM edges e
            LEFT JOIN nodes l ON l.node_id = e.left_node_id
            LEFT JOIN nodes r ON r.node_id = e.right_node_id
            WHERE e.stage <= ? AND e.op != 'seed'
              AND e.left_node_id IS NOT NULL AND e.right_node_id IS NOT NULL
              AND (l.node_id IS NULL OR r.node_id IS NULL)
            """,
            (checkpoint_stage,),
        ).fetchone()["n"]
    )
    dangling_results = int(
        conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM edges e
            LEFT JOIN nodes z ON z.node_id = e.result_node_id
            WHERE e.stage <= ? AND z.node_id IS NULL
            """,
            (checkpoint_stage,),
        ).fetchone()["n"]
    )
    operand_arrival_mismatches = int(
        conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM edges e
            JOIN nodes l ON l.node_id = e.left_node_id
            JOIN nodes r ON r.node_id = e.right_node_id
            WHERE e.stage <= ? AND e.op != 'seed'
              AND (l.first_stage > e.stage OR r.first_stage > e.stage)
            """,
            (checkpoint_stage,),
        ).fetchone()["n"]
    )
    result_arrival_mismatches = int(
        conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM edges e
            JOIN nodes z ON z.node_id = e.result_node_id
            WHERE e.stage <= ? AND z.first_stage > e.stage
            """,
            (checkpoint_stage,),
        ).fetchone()["n"]
    )
    row = conn.execute(
        """
        SELECT
          SUM(CASE WHEN NOT (
            l.q = 1 AND l.p >= 1 AND l.p <= e.stage
            AND r.q = 1 AND r.p >= 1 AND r.p <= e.stage
          ) THEN 1 ELSE 0 END) AS non_core,
          SUM(CASE WHEN NOT (
            l.confirmed_stage IS NOT NULL AND l.confirmed_stage <= e.stage
            AND r.confirmed_stage IS NOT NULL AND r.confirmed_stage <= e.stage
          ) THEN 1 ELSE 0 END) AS unconfirmed
        FROM edges e
        JOIN nodes l ON l.node_id = e.left_node_id
        JOIN nodes r ON r.node_id = e.right_node_id
        WHERE e.stage <= ? AND e.op != 'seed'
        """,
        (checkpoint_stage,),
    ).fetchone()
    non_core = int(row["non_core"] or 0)
    unconfirmed = int(row["unconfirmed"] or 0)
    frontier_stage_mismatches = int(
        conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM edges e
            JOIN nodes l ON l.node_id = e.left_node_id
            JOIN nodes r ON r.node_id = e.right_node_id
            WHERE e.stage <= ? AND e.op != 'seed'
              AND l.q = 1 AND r.q = 1
              AND e.stage != CASE WHEN l.p >= r.p THEN l.p ELSE r.p END
            """,
            (checkpoint_stage,),
        ).fetchone()["n"]
    )
    status = (
        "pass"
        if not (
            null_operands
            or dangling_operands
            or dangling_results
            or operand_arrival_mismatches
            or result_arrival_mismatches
            or non_core
            or unconfirmed
            or (
                require_frontier_stage_contract
                and frontier_stage_mismatches
            )
        )
        else "fail"
    )
    payload = {
        "scope": f"source edges with stage <= {checkpoint_stage}",
        "operand_rule": (
            "both operands must be confirmed positive-spine integers no later "
            "than the source edge stage"
        ),
        "speculative_nodes_are_operands": False,
        "null_operand_edges": null_operands,
        "dangling_operand_edges": dangling_operands,
        "dangling_result_edges": dangling_results,
        "operand_arrival_mismatch_edges": operand_arrival_mismatches,
        "result_arrival_mismatch_edges": result_arrival_mismatches,
        "non_core_operand_edges": non_core,
        "unconfirmed_operand_edges": unconfirmed,
        "declared_strict_generator_requires_frontier_stage_contract": (
            bool(require_frontier_stage_contract)
        ),
        "frontier_stage_rule": "edge.stage = max(left integer, right integer)",
        "frontier_stage_mismatch_edges": frontier_stage_mismatches,
        "frontier_stage_contract_status": (
            "pass"
            if frontier_stage_mismatches == 0
            else (
                "fail"
                if require_frontier_stage_contract
                else "diagnostic_fixture_not_enforced"
            )
        ),
        "status": status,
    }
    if status != "pass":
        raise ValueError(
            "checkpoint failed strict operand alignment: "
            f"null={null_operands}, dangling_operands={dangling_operands}, "
            f"dangling_results={dangling_results}, non_core={non_core}, "
            f"unconfirmed={unconfirmed}, "
            f"operand_arrival={operand_arrival_mismatches}, "
            f"result_arrival={result_arrival_mismatches}, "
            f"frontier_stage={frontier_stage_mismatches}"
        )
    return payload


def _division_rows(
    conn: sqlite3.Connection, checkpoint_stage: int
) -> List[sqlite3.Row]:
    count = int(
        conn.execute(
            "SELECT COUNT(*) AS n FROM edges WHERE stage <= ? AND op = '/'",
            (checkpoint_stage,),
        ).fetchone()["n"]
    )
    if count > MAX_DIVISION_EDGE_SCAN:
        raise ValueError(
            f"division edge scan would read {count} rows, above the hard safety "
            f"cap {MAX_DIVISION_EDGE_SCAN}"
        )
    return list(
        conn.execute(
            """
            SELECT
              e.edge_id, e.stage,
              l.node_id AS left_node_id, l.p AS left_p, l.q AS left_q,
              l.first_stage AS left_first_stage,
              l.confirmed_stage AS left_confirmed_stage,
              r.node_id AS right_node_id, r.p AS right_p, r.q AS right_q,
              r.first_stage AS right_first_stage,
              r.confirmed_stage AS right_confirmed_stage,
              z.node_id AS result_node_id, z.p AS result_p, z.q AS result_q,
              z.first_stage AS result_first_stage,
              z.confirmed_stage AS result_confirmed_stage
            FROM edges e
            JOIN nodes l ON l.node_id = e.left_node_id
            JOIN nodes r ON r.node_id = e.right_node_id
            JOIN nodes z ON z.node_id = e.result_node_id
            WHERE e.stage <= ? AND e.op = '/'
            ORDER BY e.stage, e.edge_id
            """,
            (checkpoint_stage,),
        ).fetchall()
    )


def _row_node(row: sqlite3.Row, prefix: str) -> NodeValue:
    confirmed = row[f"{prefix}_confirmed_stage"]
    return NodeValue(
        node_id=int(row[f"{prefix}_node_id"]),
        p=int(row[f"{prefix}_p"]),
        q=int(row[f"{prefix}_q"]),
        first_stage=int(row[f"{prefix}_first_stage"]),
        confirmed_stage=int(confirmed) if confirmed is not None else None,
    )


def _audit_and_extract_occurrences(
    conn: sqlite3.Connection,
    *,
    checkpoint_stage: int,
    max_denominator: int,
) -> Tuple[Dict[str, object], List[DivisionOccurrence]]:
    rows = _division_rows(conn, checkpoint_stage)
    arithmetic_failures: List[Dict[str, object]] = []
    residue_failures: List[Dict[str, object]] = []
    preimage_branch_failures: List[Dict[str, object]] = []
    noncanonical_results: List[int] = []
    q_counts: Counter[int] = Counter()
    eligible_records: List[
        Tuple[int, int, NodeValue, NodeValue, NodeValue, int]
    ] = []

    for row in rows:
        edge_id = int(row["edge_id"])
        left = _row_node(row, "left")
        right = _row_node(row, "right")
        result = _row_node(row, "result")
        if result.q <= 0 or math.gcd(result.p, result.q) != 1:
            noncanonical_results.append(edge_id)
            continue
        if right.value == 0:
            arithmetic_failures.append(
                {"edge_id": edge_id, "reason": "division_by_zero_source_operand"}
            )
            continue
        expected = left.value / right.value
        if expected != result.value:
            arithmetic_failures.append(
                {
                    "edge_id": edge_id,
                    "left": _fraction_payload(left.value),
                    "right": _fraction_payload(right.value),
                    "recorded_result": _fraction_payload(result.value),
                    "expected_result": _fraction_payload(expected),
                }
            )
            continue

        # Under the strict operand aperture both operands are positive integers.
        # Reducing a/b predicts both the result branch q and its C_q residue.
        divisor = math.gcd(abs(left.p), abs(right.p))
        predicted_q = abs(right.p) // divisor
        predicted_numerator = left.p // divisor
        predicted_residue = predicted_numerator % predicted_q
        recorded_residue = result.p % result.q
        if predicted_q != result.q or predicted_residue != recorded_residue:
            residue_failures.append(
                {
                    "edge_id": edge_id,
                    "predicted_q": predicted_q,
                    "recorded_q": result.q,
                    "predicted_residue": predicted_residue,
                    "recorded_residue": recorded_residue,
                }
            )
            continue
        branch = integer_division_branch(
            left.value,
            right.p,
            result.value,
            materialization_limit=0,
        )
        expected_full_branch = left.p % abs(right.p)
        if (
            int(branch["preimage_count"]) != abs(right.p)
            or int(branch["selected_branch_index"]) != expected_full_branch
            or not bool(branch["phase_relation_holds"])
        ):
            preimage_branch_failures.append(
                {
                    "edge_id": edge_id,
                    "retained_integer_divisor": right.p,
                    "expected_preimage_count": abs(right.p),
                    "reported_preimage_count": branch["preimage_count"],
                    "expected_selected_branch_index": expected_full_branch,
                    "reported_selected_branch_index": branch[
                        "selected_branch_index"
                    ],
                }
            )
            continue
        q_counts[result.q] += 1
        if MIN_DENOMINATOR <= result.q <= max_denominator:
            eligible_records.append(
                (
                    edge_id,
                    int(row["stage"]),
                    left,
                    right,
                    result,
                    recorded_residue,
                )
            )

    eligible_result_ids = sorted(
        {record[4].node_id for record in eligible_records}
    )
    if len(eligible_result_ids) > MAX_MATERIALIZED_EXPOSURE_RESULTS:
        raise ValueError(
            "eligible division-result exposure materialization would read "
            f"{len(eligible_result_ids)} result ids, above the hard safety cap "
            f"{MAX_MATERIALIZED_EXPOSURE_RESULTS}"
        )
    exposure_by_result: Dict[int, int] = {}
    for start in range(0, len(eligible_result_ids), 800):
        chunk = eligible_result_ids[start : start + 800]
        placeholders = ",".join("?" for _ in chunk)
        if not placeholders:
            continue
        for exposure_row in conn.execute(
            f"""
            SELECT result_node_id, COUNT(*) AS n
            FROM edges
            WHERE stage <= ? AND result_node_id IN ({placeholders})
            GROUP BY result_node_id
            """,
            (checkpoint_stage, *chunk),
        ):
            exposure_by_result[int(exposure_row["result_node_id"])] = int(
                exposure_row["n"]
            )
    occurrences = [
        DivisionOccurrence(
            edge_id=edge_id,
            stage=stage,
            left=left,
            right=right,
            result=result,
            residue=residue,
            exposure=exposure_by_result.get(result.node_id, 0),
        )
        for edge_id, stage, left, right, result, residue in eligible_records
    ]

    audit = {
        "scope": f"all recorded division occurrences with stage <= {checkpoint_stage}",
        "division_edge_count": len(rows),
        "arithmetic_rule": "recorded result must equal the exact Fraction(left)/Fraction(right)",
        "division_branch_prediction": (
            "for strict integer a/b, g=gcd(abs(a),abs(b)), predicted q=abs(b)/g, "
            "and predicted C_q residue=(a/g) mod q; this reduced transport "
            "coordinate is distinct from the full abs(b)-branch torsion fibre"
        ),
        "full_torsion_preimage_prediction": (
            "retaining integer divisor b gives abs(b) preimages under mu_b, "
            "and integer source lift a selects branch a mod abs(b)"
        ),
        "arithmetic_failure_count": len(arithmetic_failures),
        "arithmetic_failures": arithmetic_failures[:32],
        "residue_prediction_failure_count": len(residue_failures),
        "residue_prediction_failures": residue_failures[:32],
        "preimage_branch_failure_count": len(preimage_branch_failures),
        "preimage_branch_failures": preimage_branch_failures[:32],
        "noncanonical_result_count": len(noncanonical_results),
        "noncanonical_result_edge_ids": noncanonical_results[:32],
        "division_counts_by_exact_result_denominator": {
            str(q): int(q_counts[q]) for q in sorted(q_counts)
        },
        "eligible_q_range": [MIN_DENOMINATOR, int(max_denominator)],
        "eligible_occurrence_count_before_caps": len(occurrences),
        "eligible_result_exposure_count": len(eligible_result_ids),
        "eligible_result_exposure_hard_cap": MAX_MATERIALIZED_EXPOSURE_RESULTS,
        "exposure_scope": (
            "checkpoint-scoped incoming edges only for eligible division result ids"
        ),
        "status": (
            "pass"
            if not arithmetic_failures
            and not residue_failures
            and not preimage_branch_failures
            and not noncanonical_results
            else "fail"
        ),
    }
    if audit["status"] != "pass":
        raise ValueError(
            "division edge audit failed: "
            f"arithmetic={len(arithmetic_failures)}, "
            f"residue={len(residue_failures)}, "
            f"preimage_branch={len(preimage_branch_failures)}, "
            f"canonical={len(noncanonical_results)}"
        )
    return audit, occurrences


def _cap_occurrences(
    occurrences: Sequence[DivisionOccurrence],
    *,
    seed: int,
    max_per_q: int,
) -> Tuple[Dict[int, List[DivisionOccurrence]], Dict[str, object]]:
    by_q: Dict[int, List[DivisionOccurrence]] = defaultdict(list)
    for occurrence in occurrences:
        by_q[occurrence.q].append(occurrence)
    selected: Dict[int, List[DivisionOccurrence]] = {}
    rows: List[Dict[str, object]] = []
    for q in sorted(by_q):
        eligible = by_q[q]
        ranked = sorted(
            eligible,
            key=lambda occurrence: _hash_rank(
                seed, "occurrence-cap", q, occurrence.semantic_key
            ),
        )
        kept = ranked[:max_per_q]
        selected[q] = sorted(
            kept,
            key=lambda occurrence: (occurrence.stage, occurrence.semantic_key),
        )
        rows.append(
            {
                "q": q,
                "eligible": len(eligible),
                "selected": len(kept),
                "excluded_by_occurrence_cap": max(0, len(eligible) - len(kept)),
            }
        )
    return selected, {
        "policy": (
            "lowest deterministic SHA-256 ranks of q and canonical source-edge "
            "content; residue labels and SQLite insertion ids are unused"
        ),
        "max_occurrences_per_q": max_per_q,
        "by_q": rows,
        "total_selected": sum(len(items) for items in selected.values()),
        "total_excluded": sum(max(0, len(items) - max_per_q) for items in by_q.values()),
    }


def _build_provenance_dag(
    by_q: Mapping[int, Sequence[DivisionOccurrence]],
    *,
    seed: int,
    max_out_degree: int,
) -> Tuple[
    Dict[int, Dict[int, Tuple[int, ...]]],
    Dict[int, Dict[Tuple[int, int], Tuple[int, ...]]],
    Dict[int, int],
    Dict[str, object],
]:
    all_adjacency: Dict[int, Dict[int, Tuple[int, ...]]] = {}
    all_witnesses: Dict[int, Dict[Tuple[int, int], Tuple[int, ...]]] = {}
    hub_degree_by_edge: Dict[int, int] = {}
    q_rows: List[Dict[str, object]] = []
    total_upper_bound = 0
    total_before_cap = 0
    total_after_cap = 0

    for q in sorted(by_q):
        occurrences = list(by_q[q])
        by_edge = {occurrence.edge_id: occurrence for occurrence in occurrences}
        input_buckets: Dict[int, List[DivisionOccurrence]] = defaultdict(list)
        for occurrence in occurrences:
            for input_id in occurrence.input_ids:
                input_buckets[input_id].append(occurrence)
        for bucket in input_buckets.values():
            bucket.sort(
                key=lambda occurrence: (occurrence.stage, occurrence.semantic_key)
            )
            total_upper_bound += len(bucket) * (len(bucket) - 1) // 2
            if total_upper_bound > MAX_ADJACENCY_CANDIDATES:
                raise ValueError(
                    "shared-input adjacency upper bound exceeds the hard safety "
                    f"cap {MAX_ADJACENCY_CANDIDATES}"
                )
        candidate_witnesses: Dict[int, Dict[int, Set[int]]] = defaultdict(
            lambda: defaultdict(set)
        )
        undirected_neighbors: Dict[int, Set[int]] = defaultdict(set)
        for input_id, bucket in input_buckets.items():
            for index, source in enumerate(bucket):
                for target in bucket[index + 1 :]:
                    if source.stage >= target.stage:
                        continue
                    # Same-stage insertion order is not time. Only a strict
                    # source-stage increase creates an oriented provenance arc.
                    candidate_witnesses[source.edge_id][target.edge_id].add(input_id)
                    undirected_neighbors[source.edge_id].add(target.edge_id)
                    undirected_neighbors[target.edge_id].add(source.edge_id)
        for occurrence in occurrences:
            hub_degree_by_edge[occurrence.edge_id] = len(
                undirected_neighbors.get(occurrence.edge_id, set())
            )

        adjacency: Dict[int, Tuple[int, ...]] = {}
        witnesses: Dict[Tuple[int, int], Tuple[int, ...]] = {}
        q_before = 0
        q_after = 0
        q_dropped = 0
        for source in occurrences:
            candidates = candidate_witnesses.get(source.edge_id, {})
            ranked_targets = sorted(
                candidates,
                key=lambda target_id: _hash_rank(
                    seed,
                    "out-neighbor",
                    q,
                    source.semantic_key,
                    by_edge[target_id].semantic_key,
                ),
            )
            q_before += len(ranked_targets)
            kept_targets = ranked_targets[:max_out_degree]
            q_after += len(kept_targets)
            q_dropped += max(0, len(ranked_targets) - len(kept_targets))
            adjacency[source.edge_id] = tuple(kept_targets)
            for target_id in kept_targets:
                source_occurrence = by_edge[source.edge_id]
                target_occurrence = by_edge[target_id]
                if not source_occurrence.stage < target_occurrence.stage:
                    raise AssertionError("provenance adjacency must be acyclic")
                witnesses[(source.edge_id, target_id)] = tuple(
                    sorted(candidates[target_id])
                )
        total_before_cap += q_before
        total_after_cap += q_after
        all_adjacency[q] = adjacency
        all_witnesses[q] = witnesses
        q_rows.append(
            {
                "q": q,
                "selected_occurrences": len(occurrences),
                "shared_input_nodes": len(input_buckets),
                "candidate_arcs_before_degree_cap": q_before,
                "arcs_after_degree_cap": q_after,
                "arcs_excluded_by_degree_cap": q_dropped,
                "maximum_shared_input_hub_degree": max(
                    (
                        hub_degree_by_edge[occurrence.edge_id]
                        for occurrence in occurrences
                    ),
                    default=0,
                ),
            }
        )

    return all_adjacency, all_witnesses, hub_degree_by_edge, {
        "definition": (
            "occurrences are adjacent iff their exact source division edges share "
            "a confirmed input node; arcs require a strictly increasing source stage"
        ),
        "hub_degree_definition": (
            "number of distinct other selected occurrences sharing either exact "
            "input, before orientation and outgoing-degree truncation"
        ),
        "residue_blind_conditional_on_q": True,
        "same_stage_sqlite_insertion_order_used_as_time": False,
        "orientation": "strictly increasing source stage; same-stage pairs are unoriented",
        "neighbor_ranking": (
            "deterministic SHA-256 of seed, q, and canonical source/target edge "
            "content; residue, return state, and SQLite insertion ids are excluded"
        ),
        "max_out_degree": max_out_degree,
        "candidate_arcs_before_degree_cap": total_before_cap,
        "arcs_after_degree_cap": total_after_cap,
        "arcs_excluded_by_degree_cap": total_before_cap - total_after_cap,
        "candidate_pair_upper_bound_including_duplicate_witnesses": total_upper_bound,
        "by_q": q_rows,
    }


def _find_path_from_seed(
    seed_edge_id: int,
    *,
    by_edge: Mapping[int, DivisionOccurrence],
    adjacency: Mapping[int, Tuple[int, ...]],
    globally_used: Set[int],
    path_length: int,
    remaining_global_states: int,
) -> Tuple[Optional[Tuple[int, ...]], int]:
    states_examined = 0

    def visit(
        edge_ids: Tuple[int, ...], result_ids: frozenset[Tuple[int, int]]
    ) -> Optional[Tuple[int, ...]]:
        nonlocal states_examined
        states_examined += 1
        if states_examined > MAX_DFS_STATES_PER_SEED:
            raise ValueError(
                "q-conditioned residue-blind path search exceeded the hard "
                "per-seed DFS state "
                f"cap {MAX_DFS_STATES_PER_SEED}"
            )
        if states_examined > remaining_global_states:
            raise ValueError(
                "q-conditioned residue-blind path search exceeded the hard "
                "aggregate DFS state "
                f"cap {MAX_TOTAL_DFS_STATES}"
            )
        if len(edge_ids) == path_length:
            return edge_ids
        current = edge_ids[-1]
        for target_id in adjacency.get(current, ()):
            if target_id in globally_used or target_id in edge_ids:
                continue
            target = by_edge[target_id]
            target_result = (target.result.p, target.result.q)
            if target_result in result_ids:
                continue
            found = visit(edge_ids + (target_id,), result_ids | {target_result})
            if found is not None:
                return found
        return None

    occurrence = by_edge[seed_edge_id]
    result = visit(
        (seed_edge_id,),
        frozenset({(occurrence.result.p, occurrence.result.q)}),
    )
    return result, states_examined


def _extract_paths(
    by_q: Mapping[int, Sequence[DivisionOccurrence]],
    *,
    adjacency_by_q: Mapping[int, Mapping[int, Tuple[int, ...]]],
    witnesses_by_q: Mapping[int, Mapping[Tuple[int, int], Tuple[int, ...]]],
    seed: int,
    path_length: int,
    max_paths_per_q: int,
) -> Tuple[List[ProvenancePath], Dict[str, object]]:
    paths: List[ProvenancePath] = []
    q_rows: List[Dict[str, object]] = []
    total_dfs_states = 0
    total_unconsidered_due_to_path_cap = 0
    for q in sorted(by_q):
        occurrences = list(by_q[q])
        by_edge = {occurrence.edge_id: occurrence for occurrence in occurrences}
        globally_used: Set[int] = set()
        ranked_seeds = sorted(
            by_edge,
            key=lambda edge_id: _hash_rank(
                seed, "path-seed", q, by_edge[edge_id].semantic_key
            ),
        )
        q_paths: List[ProvenancePath] = []
        attempted = 0
        seed_entries_considered = 0
        for seed_edge_id in ranked_seeds:
            if len(q_paths) >= max_paths_per_q:
                break
            seed_entries_considered += 1
            if seed_edge_id in globally_used:
                continue
            attempted += 1
            edge_ids, states_examined = _find_path_from_seed(
                seed_edge_id,
                by_edge=by_edge,
                adjacency=adjacency_by_q.get(q, {}),
                globally_used=globally_used,
                path_length=path_length,
                remaining_global_states=MAX_TOTAL_DFS_STATES - total_dfs_states,
            )
            total_dfs_states += states_examined
            if edge_ids is None:
                continue
            result_keys = [
                (by_edge[edge_id].result.p, by_edge[edge_id].result.q)
                for edge_id in edge_ids
            ]
            if len(set(edge_ids)) != path_length or len(set(result_keys)) != path_length:
                raise AssertionError("accepted path violated occurrence/result distinctness")
            transition_witnesses = tuple(
                witnesses_by_q[q][(source_id, target_id)]
                for source_id, target_id in zip(edge_ids, edge_ids[1:])
            )
            if any(not witness for witness in transition_witnesses):
                raise AssertionError("accepted transition lacks a shared-input witness")
            digest = _hash_digest(
                seed,
                "path-split",
                q,
                *(by_edge[edge_id].semantic_key for edge_id in edge_ids),
            )
            split = "discovery" if digest[-1] % 2 == 0 else "holdout"
            path = ProvenancePath(
                q=q,
                occurrences=tuple(by_edge[edge_id] for edge_id in edge_ids),
                transitions=transition_witnesses,
                split=split,
                path_hash=digest.hex(),
            )
            q_paths.append(path)
            globally_used.update(edge_ids)
        paths.extend(q_paths)
        unconsidered_due_to_cap = (
            len(ranked_seeds) - seed_entries_considered
            if len(q_paths) >= max_paths_per_q
            else 0
        )
        total_unconsidered_due_to_path_cap += unconsidered_due_to_cap
        q_rows.append(
            {
                "q": q,
                "seed_attempts": attempted,
                "accepted_paths": len(q_paths),
                "discovery_paths": sum(path.split == "discovery" for path in q_paths),
                "holdout_paths": sum(path.split == "holdout" for path in q_paths),
                "used_occurrences": len(globally_used),
                "unused_selected_occurrences": len(occurrences) - len(globally_used),
                "path_cap_reached": len(q_paths) == max_paths_per_q,
                "seed_entries_unconsidered_due_to_path_cap": unconsidered_due_to_cap,
            }
        )
    return paths, {
        "path_length_occurrences": path_length,
        "occurrence_disjoint_within_q": True,
        "distinct_result_nodes_within_path": True,
        "seed_policy": (
            "deterministic SHA-256 rank of seed, q, and canonical source-edge "
            "content; DFS follows the q-conditioned residue-blind degree-capped "
            "neighbor order"
        ),
        "split_policy": (
            "SHA-256(seed, q, complete canonical source-edge sequence) parity: "
            "even discovery, odd holdout; SQLite insertion ids are excluded"
        ),
        "max_paths_per_q": max_paths_per_q,
        "hard_dfs_states_per_seed": MAX_DFS_STATES_PER_SEED,
        "hard_total_dfs_states": MAX_TOTAL_DFS_STATES,
        "dfs_states_examined": total_dfs_states,
        "accepted_path_count": len(paths),
        "discovery_path_count": sum(path.split == "discovery" for path in paths),
        "holdout_path_count": sum(path.split == "holdout" for path in paths),
        "seed_entries_unconsidered_due_to_path_cap": (
            total_unconsidered_due_to_path_cap
        ),
        "by_q": q_rows,
    }


def _proper_prefix_return(
    residues: Sequence[int], q: int
) -> Tuple[int, List[int], List[int]]:
    state = 0
    states = [0]
    return_positions: List[int] = []
    for index, residue in enumerate(residues, start=1):
        state = (state + int(residue)) % int(q)
        states.append(state)
        if index < len(residues) and state == 0:
            return_positions.append(index)
    return len(return_positions), return_positions, states


def _aggregate_statistic(
    paths: Sequence[ProvenancePath],
    residues_by_path: Mapping[str, Sequence[int]],
) -> Tuple[Optional[Fraction], Dict[int, Fraction]]:
    by_q: Dict[int, List[Fraction]] = defaultdict(list)
    for path in paths:
        residues = residues_by_path[path.path_hash]
        count, _, _ = _proper_prefix_return(residues, path.q)
        by_q[path.q].append(Fraction(count, len(residues) - 1))
    q_means: Dict[int, Fraction] = {}
    for q, scores in by_q.items():
        q_means[q] = sum(scores, Fraction(0, 1)) / len(scores)
    if not q_means:
        return None, {}
    aggregate = sum(q_means.values(), Fraction(0, 1)) / len(q_means)
    return aggregate, q_means


def _fraction_stat_payload(value: Optional[Fraction]) -> Optional[Dict[str, object]]:
    if value is None:
        return None
    payload = _fraction_payload(value)
    payload["decimal"] = float(value)
    return payload


def _floor_log2_at_least_one(value: int) -> int:
    return max(1, int(value)).bit_length() - 1


Stratum = Tuple[int, int, int, int]


def _stratum_key(
    occurrence: DivisionOccurrence,
    *,
    stage_bin_width: int,
    hub_degree: int,
) -> Stratum:
    stage_bin = (
        occurrence.stage
        if stage_bin_width == 1
        else ((occurrence.stage - 1) // stage_bin_width) * stage_bin_width + 1
    )
    return (
        occurrence.q,
        stage_bin,
        _floor_log2_at_least_one(occurrence.exposure),
        _floor_log2_at_least_one(hub_degree),
    )


def _quantile(
    values: Sequence[Fraction], numerator: int, denominator: int
) -> Optional[Fraction]:
    if not values:
        return None
    if denominator <= 0 or numerator < 0 or numerator > denominator:
        raise ValueError("quantile probability must lie in [0, 1]")
    ordered = sorted(values)
    index = max(0, (numerator * len(ordered) + denominator - 1) // denominator - 1)
    return ordered[index]


def _null_summary(
    observed: Optional[Fraction], samples: Sequence[Fraction]
) -> Dict[str, object]:
    if observed is None or not samples:
        return {
            "sample_count": len(samples),
            "mean": None,
            "percentile_99": None,
            "upper_tail_p_plus_one": None,
            "observed_exceeds_mean": False,
            "observed_above_percentile_99": False,
            "aggregate_histogram": {},
        }
    mean = sum(samples, Fraction(0, 1)) / len(samples)
    percentile_99 = _quantile(samples, 99, 100)
    upper_tail = Fraction(
        1 + sum(value >= observed for value in samples),
        len(samples) + 1,
    )
    histogram = Counter(samples)
    return {
        "sample_count": len(samples),
        "mean": _fraction_stat_payload(mean),
        "percentile_99": _fraction_stat_payload(percentile_99),
        "upper_tail_p_plus_one": _fraction_stat_payload(upper_tail),
        "observed_exceeds_mean": observed > mean,
        "observed_above_percentile_99": (
            percentile_99 is not None and observed > percentile_99
        ),
        "comparison_arithmetic": "exact Fraction; decimals are serialization aids only",
        "aggregate_histogram": {
            format_key((value.numerator, value.denominator)): int(histogram[value])
            for value in sorted(histogram)
        },
    }


def _run_nulls(
    *,
    holdout_paths: Sequence[ProvenancePath],
    selected_by_q: Mapping[int, Sequence[DivisionOccurrence]],
    hub_degree_by_edge: Mapping[int, int],
    seed: int,
    null_samples: int,
    stage_bin_width: int,
) -> Tuple[Dict[str, object], Dict[str, object], Dict[str, object]]:
    observed_residues = {
        path.path_hash: [occurrence.residue for occurrence in path.occurrences]
        for path in holdout_paths
    }
    observed, observed_by_q = _aggregate_statistic(
        holdout_paths, observed_residues
    )

    all_selected = [
        occurrence
        for q in sorted(selected_by_q)
        for occurrence in selected_by_q[q]
    ]
    estimated_position_work = null_samples * (
        2 * sum(len(path.occurrences) for path in holdout_paths)
        + len(all_selected)
    )
    if estimated_position_work > MAX_NULL_POSITION_EVALUATIONS:
        raise ValueError(
            "configured null evaluation would exceed the hard safety cap: "
            f"estimated={estimated_position_work}, "
            f"cap={MAX_NULL_POSITION_EVALUATIONS}"
        )

    exact_step_samples: List[Fraction] = []
    ordered_paths = sorted(holdout_paths, key=lambda path: (path.q, path.path_hash))
    for replicate in range(null_samples):
        rng = random.Random(
            int.from_bytes(
                _hash_digest(seed, "exact-step-null", replicate)[:16], "big"
            )
        )
        permuted: Dict[str, Sequence[int]] = {}
        for path in ordered_paths:
            residues = list(observed_residues[path.path_hash])
            rng.shuffle(residues)
            permuted[path.path_hash] = residues
        aggregate, _ = _aggregate_statistic(ordered_paths, permuted)
        if aggregate is not None:
            exact_step_samples.append(aggregate)

    pools: Dict[Stratum, List[DivisionOccurrence]] = defaultdict(list)
    stratum_by_edge: Dict[int, Stratum] = {}
    for occurrence in all_selected:
        stratum = _stratum_key(
            occurrence,
            stage_bin_width=stage_bin_width,
            hub_degree=hub_degree_by_edge.get(occurrence.edge_id, 1),
        )
        pools[stratum].append(occurrence)
        stratum_by_edge[occurrence.edge_id] = stratum
    for pool in pools.values():
        pool.sort(key=lambda occurrence: occurrence.semantic_key)
    mutable_strata = {
        stratum
        for stratum, pool in pools.items()
        if len(pool) >= 2 and len({occurrence.residue for occurrence in pool}) >= 2
    }
    holdout_positions = [
        occurrence for path in holdout_paths for occurrence in path.occurrences
    ]
    mutable_position_count = sum(
        stratum_by_edge[occurrence.edge_id] in mutable_strata
        for occurrence in holdout_positions
    )
    mutable_fraction = Fraction(
        mutable_position_count, len(holdout_positions)
    ) if holdout_positions else Fraction(0, 1)

    shuffled_samples: List[Fraction] = []
    for replicate in range(null_samples):
        rng = random.Random(
            int.from_bytes(
                _hash_digest(seed, "stratified-label-null", replicate)[:16], "big"
            )
        )
        shuffled_residue_by_edge: Dict[int, int] = {}
        for stratum in sorted(pools):
            pool = pools[stratum]
            labels = [occurrence.residue for occurrence in pool]
            if stratum in mutable_strata:
                rng.shuffle(labels)
            for occurrence, label in zip(pool, labels):
                shuffled_residue_by_edge[occurrence.edge_id] = label
        shuffled_paths = {
            path.path_hash: [
                shuffled_residue_by_edge[occurrence.edge_id]
                for occurrence in path.occurrences
            ]
            for path in ordered_paths
        }
        aggregate, _ = _aggregate_statistic(ordered_paths, shuffled_paths)
        if aggregate is not None:
            shuffled_samples.append(aggregate)

    observed_payload = {
        "definition": (
            "proper-prefix return count divided by path_length-1, averaged within "
            "q and then equally across holdout q values"
        ),
        "proper_prefix_excludes_endpoint": True,
        "holdout_path_count": len(holdout_paths),
        "holdout_q_count": len(observed_by_q),
        "holdout_q_values": sorted(observed_by_q),
        "aggregate": _fraction_stat_payload(observed),
        "by_q": {
            str(q): _fraction_stat_payload(observed_by_q[q])
            for q in sorted(observed_by_q)
        },
    }
    exact_step = {
        "name": "exact_step_multiset_order_permutation",
        "conditioning": (
            "each path keeps q, length, graph selection, endpoint, and its exact "
            "residue multiset; only within-path order is permuted independently"
        ),
        "ordinary_cyclic_group_baseline": True,
        "seed": seed,
        **_null_summary(observed, exact_step_samples),
    }
    stratum_rows = []
    for stratum in sorted(pools):
        q, stage_bin, exposure_bin, hub_bin = stratum
        pool = pools[stratum]
        stratum_rows.append(
            {
                "q": q,
                "stage_bin_start": stage_bin,
                "stage_bin_width": stage_bin_width,
                "exposure_floor_log2": exposure_bin,
                "hub_degree_floor_log2": hub_bin,
                "occurrence_count": len(pool),
                "distinct_residue_count": len(
                    {occurrence.residue for occurrence in pool}
                ),
                "residue_counts": {
                    str(residue): count
                    for residue, count in sorted(
                        Counter(occurrence.residue for occurrence in pool).items()
                    )
                },
                "mutable": stratum in mutable_strata,
            }
        )
    stratified = {
        "name": "q_stage_exposure_hub_stratified_label_shuffle",
        "conditioning": (
            "paths remain fixed; residues are shuffled only among selected "
            "occurrences with equal q, source-stage bin, floor(log2 exposure), "
            "and floor(log2 distinct-other shared-input hub degree)"
        ),
        "stage_bin_width": stage_bin_width,
        "exact_stage_stratification": stage_bin_width == 1,
        "seed": seed,
        "stratum_count": len(pools),
        "mutable_stratum_count": len(mutable_strata),
        "holdout_position_count": len(holdout_positions),
        "mutable_holdout_position_count": mutable_position_count,
        "mutable_holdout_fraction": _fraction_stat_payload(mutable_fraction),
        "strata": stratum_rows,
        **_null_summary(observed, shuffled_samples),
    }
    return observed_payload, exact_step, stratified


def _path_payload(
    path: ProvenancePath,
    *,
    checkpoint_stage: int,
) -> Dict[str, object]:
    residues = [occurrence.residue for occurrence in path.occurrences]
    return_count, return_positions, states = _proper_prefix_return(residues, path.q)
    occurrence_rows: List[Dict[str, object]] = []
    for occurrence in path.occurrences:
        divisor = math.gcd(abs(occurrence.left.p), abs(occurrence.right.p))
        branch = integer_division_branch(
            occurrence.left.value,
            occurrence.right.p,
            occurrence.result.value,
            materialization_limit=0,
        )
        occurrence_rows.append(
            {
                "edge_id": occurrence.edge_id,
                "stage": occurrence.stage,
                "op": "/",
                "left_input": _node_payload(occurrence.left, checkpoint_stage),
                "right_input": _node_payload(occurrence.right, checkpoint_stage),
                "result": _node_payload(occurrence.result, checkpoint_stage),
                "exact_arithmetic": {
                    "relation": "left / right = result",
                    "validated": occurrence.left.value / occurrence.right.value
                    == occurrence.result.value,
                },
                "division_branch_prediction": {
                    "operator_relation": "integer_torsion_preimage_selection",
                    "global_binary_division_descends_to_q_mod_z": False,
                    "retained_integer_divisor": occurrence.right.p,
                    "full_preimage_count": branch["preimage_count"],
                    "selected_full_preimage_branch_index": branch[
                        "selected_branch_index"
                    ],
                    "selection_uses_retained_source_lift": branch[
                        "selection_uses_retained_source_lift"
                    ],
                    "full_preimage_relation_validated": branch[
                        "phase_relation_holds"
                    ],
                    "reduction_gcd": divisor,
                    "predicted_q": abs(occurrence.right.p) // divisor,
                    "predicted_residue": (occurrence.left.p // divisor)
                    % occurrence.q,
                    "recorded_q": occurrence.q,
                    "recorded_residue": occurrence.residue,
                    "validated": True,
                    "coordinate_boundary": (
                        "recorded_q/residue is the reduced transport label; it "
                        "is not the full preimage count/branch index when gcd(a,b)>1"
                    ),
                },
                "phase_label": {
                    "residue": occurrence.residue,
                    "q": occurrence.q,
                    "phase": _fraction_payload(
                        Fraction(occurrence.residue, occurrence.q)
                    ),
                },
                "incoming_witness_exposure_at_checkpoint": occurrence.exposure,
            }
        )
    transition_rows: List[Dict[str, object]] = []
    for source, target, witness_ids in zip(
        path.occurrences, path.occurrences[1:], path.transitions
    ):
        input_nodes = {
            node.node_id: node
            for node in (source.left, source.right, target.left, target.right)
        }
        transition_rows.append(
            {
                "from_edge_id": source.edge_id,
                "to_edge_id": target.edge_id,
                "ordered_by": {
                    "from_stage": source.stage,
                    "to_stage": target.stage,
                    "strictly_increasing_source_stage": source.stage < target.stage,
                    "same_stage_insertion_order_used_as_time": False,
                },
                "shared_confirmed_input_node_ids": list(witness_ids),
                "shared_confirmed_inputs": [
                    _node_payload(input_nodes[node_id], checkpoint_stage)
                    for node_id in witness_ids
                ],
                "source_graph_relation": "shared_input_between_two_recorded_division_occurrences",
                "runtime_transport_edge": False,
            }
        )
    return {
        "path_id": path.path_hash,
        "split": path.split,
        "q": path.q,
        "edge_id_sequence": [
            occurrence.edge_id for occurrence in path.occurrences
        ],
        "result_node_id_sequence": [
            occurrence.result.node_id for occurrence in path.occurrences
        ],
        "occurrence_count": len(path.occurrences),
        "occurrences_distinct": len(
            {occurrence.edge_id for occurrence in path.occurrences}
        )
        == len(path.occurrences),
        "result_nodes_distinct": len(
            {occurrence.result.node_id for occurrence in path.occurrences}
        )
        == len(path.occurrences),
        "source_occurrence_evidence": occurrence_rows,
        "transition_witnesses": transition_rows,
        "external_counterfactual_transport": {
            "runtime_operational": False,
            "path_semantics": (
                "external_counterfactual_transport_over_q_conditioned_"
                "residue_blind_provenance_walk"
            ),
            "initial_state": 0,
            "residues": residues,
            "states_including_initial": states,
            "proper_prefix_return_positions": return_positions,
            "proper_prefix_return_count": return_count,
            "normalized_score": _fraction_stat_payload(
                Fraction(return_count, len(residues) - 1)
            ),
            "endpoint_state": states[-1],
            "endpoint_excluded_from_statistic": True,
        },
    }


def _validate_config(
    *,
    max_denominator: int,
    path_length: int,
    max_occurrences_per_q: int,
    max_out_degree: int,
    max_paths_per_q: int,
    null_samples: int,
    stage_bin_width: int,
) -> None:
    checks = [
        (
            MIN_DENOMINATOR <= max_denominator <= MAX_DENOMINATOR,
            f"max_denominator must be in [{MIN_DENOMINATOR}, {MAX_DENOMINATOR}]",
        ),
        (
            2 <= path_length <= MAX_PATH_LENGTH,
            f"path_length must be in [2, {MAX_PATH_LENGTH}]",
        ),
        (
            1 <= max_occurrences_per_q <= MAX_OCCURRENCES_PER_Q,
            "max_occurrences_per_q must be in "
            f"[1, {MAX_OCCURRENCES_PER_Q}]",
        ),
        (
            1 <= max_out_degree <= MAX_OUT_DEGREE,
            f"max_out_degree must be in [1, {MAX_OUT_DEGREE}]",
        ),
        (
            1 <= max_paths_per_q <= MAX_PATHS_PER_Q,
            f"max_paths_per_q must be in [1, {MAX_PATHS_PER_Q}]",
        ),
        (
            1 <= null_samples <= MAX_NULL_SAMPLES,
            f"null_samples must be in [1, {MAX_NULL_SAMPLES}]",
        ),
        (
            1 <= stage_bin_width <= 1_000_000,
            "stage_bin_width must be in [1, 1000000]",
        ),
    ]
    for valid, message in checks:
        if not valid:
            raise ValueError(message)


def _require_int_parameter(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return int(value)


def phase_transport_probe(
    *,
    db_path: Path,
    max_denominator: int = DEFAULT_MAX_DENOMINATOR,
    path_length: int = DEFAULT_PATH_LENGTH,
    max_occurrences_per_q: int = DEFAULT_MAX_OCCURRENCES_PER_Q,
    max_out_degree: int = DEFAULT_MAX_OUT_DEGREE,
    max_paths_per_q: int = DEFAULT_MAX_PATHS_PER_Q,
    null_samples: int = DEFAULT_NULL_SAMPLES,
    stage_bin_width: int = DEFAULT_STAGE_BIN_WIDTH,
    seed: int = DEFAULT_SEED,
    checkpoint_stage: Optional[int] = None,
    experiment_id: str = FROZEN_PRIMARY_EXPERIMENT_ID,
) -> Dict[str, object]:
    max_denominator = _require_int_parameter("max_denominator", max_denominator)
    path_length = _require_int_parameter("path_length", path_length)
    max_occurrences_per_q = _require_int_parameter(
        "max_occurrences_per_q", max_occurrences_per_q
    )
    max_out_degree = _require_int_parameter("max_out_degree", max_out_degree)
    max_paths_per_q = _require_int_parameter(
        "max_paths_per_q", max_paths_per_q
    )
    null_samples = _require_int_parameter("null_samples", null_samples)
    stage_bin_width = _require_int_parameter("stage_bin_width", stage_bin_width)
    seed = _require_int_parameter("seed", seed)
    if checkpoint_stage is not None:
        checkpoint_stage = _require_int_parameter(
            "checkpoint_stage", checkpoint_stage
        )
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise TypeError("experiment_id must be a nonempty string")
    _validate_config(
        max_denominator=max_denominator,
        path_length=path_length,
        max_occurrences_per_q=max_occurrences_per_q,
        max_out_degree=max_out_degree,
        max_paths_per_q=max_paths_per_q,
        null_samples=null_samples,
        stage_bin_width=stage_bin_width,
    )
    db_path = Path(db_path)
    with closing(connect_readonly(db_path)) as conn:
        conn.execute("PRAGMA query_only = ON")
        latest_stage = _latest_stage(conn)
        checkpoint = latest_stage if checkpoint_stage is None else checkpoint_stage
        if checkpoint < 1 or checkpoint > latest_stage:
            raise ValueError(
                f"checkpoint_stage must be between 1 and latest stage {latest_stage}"
            )
        config_raw = _meta_value(conn, "config_json")
        corpus_schema_version = _meta_value(conn, "schema_version")
        try:
            corpus_config: object = (
                json.loads(config_raw) if config_raw is not None else None
            )
        except json.JSONDecodeError:
            corpus_config = config_raw
        declares_strict_generator = (
            isinstance(corpus_config, dict)
            and corpus_config.get("generator") == "strict_stage_moo_graph"
        )
        alignment = _checkpoint_alignment_audit(
            conn,
            checkpoint,
            require_frontier_stage_contract=bool(declares_strict_generator),
        )
        division_audit, eligible_occurrences = _audit_and_extract_occurrences(
            conn,
            checkpoint_stage=checkpoint,
            max_denominator=int(max_denominator),
        )
        operator_counts = {
            str(row["op"]): int(row["n"])
            for row in conn.execute(
                """
                SELECT op, COUNT(*) AS n
                FROM edges
                WHERE stage <= ?
                GROUP BY op
                ORDER BY op
                """,
                (checkpoint,),
            )
        }
        nodes_at_checkpoint = int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM nodes WHERE first_stage <= ?",
                (checkpoint,),
            ).fetchone()["n"]
        )
        edges_at_checkpoint = int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM edges WHERE stage <= ?",
                (checkpoint,),
            ).fetchone()["n"]
        )

    selected_by_q, occurrence_cap = _cap_occurrences(
        eligible_occurrences,
        seed=int(seed),
        max_per_q=int(max_occurrences_per_q),
    )
    (
        adjacency_by_q,
        witnesses_by_q,
        hub_degree_by_edge,
        dag_audit,
    ) = _build_provenance_dag(
        selected_by_q,
        seed=int(seed),
        max_out_degree=int(max_out_degree),
    )
    paths, path_audit = _extract_paths(
        selected_by_q,
        adjacency_by_q=adjacency_by_q,
        witnesses_by_q=witnesses_by_q,
        seed=int(seed),
        path_length=int(path_length),
        max_paths_per_q=int(max_paths_per_q),
    )
    holdout_paths = [path for path in paths if path.split == "holdout"]
    discovery_paths = [path for path in paths if path.split == "discovery"]
    observed, exact_step_null, stratified_null = _run_nulls(
        holdout_paths=holdout_paths,
        selected_by_q=selected_by_q,
        hub_degree_by_edge=hub_degree_by_edge,
        seed=int(seed),
        null_samples=int(null_samples),
        stage_bin_width=int(stage_bin_width),
    )

    holdout_q_values = sorted({path.q for path in holdout_paths})
    mutable_positions = int(stratified_null["mutable_holdout_position_count"])
    holdout_positions = int(stratified_null["holdout_position_count"])
    mutable_fraction = (
        Fraction(mutable_positions, holdout_positions)
        if holdout_positions
        else Fraction(0, 1)
    )
    aperture_checks = {
        "holdout_paths_at_least_32": len(holdout_paths) >= MIN_HOLDOUT_PATHS,
        "holdout_denominators_at_least_4": (
            len(holdout_q_values) >= MIN_HOLDOUT_DENOMINATORS
        ),
        "mutable_positions_at_least_16": (
            mutable_positions >= MIN_MUTABLE_POSITIONS
        ),
        "mutable_fraction_at_least_25_percent": (
            mutable_fraction >= MIN_MUTABLE_FRACTION
        ),
    }
    aperture_sufficient = all(aperture_checks.values())
    retention_checks = {
        "observed_exceeds_exact_step_null_mean": bool(
            exact_step_null["observed_exceeds_mean"]
        ),
        "observed_above_exact_step_null_99th_percentile": bool(
            exact_step_null["observed_above_percentile_99"]
        ),
        "observed_exceeds_stratified_null_mean": bool(
            stratified_null["observed_exceeds_mean"]
        ),
        "observed_above_stratified_null_99th_percentile": bool(
            stratified_null["observed_above_percentile_99"]
        ),
    }

    db_sha256 = file_sha256(db_path)
    frozen_profile = FROZEN_EXPERIMENTS.get(experiment_id)
    prereg_relative_path = (
        frozen_profile.get("prereg_relative_path")
        if frozen_profile is not None
        else None
    )
    prereg_path = (
        PROJECT_ROOT / "research/experiments"
        / prereg_relative_path.relative_to("out/experiments")
        if isinstance(prereg_relative_path, Path)
        else None
    )
    prereg_exists = bool(prereg_path is not None and prereg_path.is_file())
    prereg_sha256 = (
        file_sha256(prereg_path)
        if prereg_path is not None and prereg_exists
        else None
    )
    frozen_identity_checks = {
        "experiment_id_matches_known_frozen_profile": frozen_profile is not None,
        "database_path_matches": bool(
            frozen_profile is not None
            and db_path.as_posix().endswith(
                str(frozen_profile["database_suffix"])
            )
        ),
        "database_sha256_matches": bool(
            frozen_profile is not None
            and db_sha256 == frozen_profile["database_sha256"]
        ),
        "corpus_schema_matches": bool(
            frozen_profile is not None
            and corpus_schema_version == frozen_profile["corpus_schema_version"]
        ),
        "corpus_config_matches": bool(
            frozen_profile is not None
            and corpus_config == frozen_profile["corpus_config"]
        ),
        "frontier_stage_contract_matches": (
            int(alignment["frontier_stage_mismatch_edges"]) == 0
        ),
        "preregistration_exists": prereg_exists,
        "preregistration_sha256_matches": bool(
            frozen_profile is not None
            and prereg_sha256 == frozen_profile["prereg_sha256"]
        ),
        "checkpoint_matches": bool(
            frozen_profile is not None
            and checkpoint == frozen_profile["checkpoint"]
        ),
        "max_denominator_matches": max_denominator == DEFAULT_MAX_DENOMINATOR,
        "path_length_matches": path_length == DEFAULT_PATH_LENGTH,
        "occurrence_cap_matches": (
            max_occurrences_per_q == DEFAULT_MAX_OCCURRENCES_PER_Q
        ),
        "degree_cap_matches": max_out_degree == DEFAULT_MAX_OUT_DEGREE,
        "path_cap_matches": max_paths_per_q == DEFAULT_MAX_PATHS_PER_Q,
        "null_samples_match": null_samples == DEFAULT_NULL_SAMPLES,
        "stage_bin_width_matches": stage_bin_width == DEFAULT_STAGE_BIN_WIDTH,
        "seed_matches": seed == DEFAULT_SEED,
    }
    adequate_null_resolution = null_samples >= MIN_DECISION_NULL_SAMPLES
    frozen_experiment_eligible = all(frozen_identity_checks.values()) and bool(
        adequate_null_resolution
    )

    if not aperture_sufficient:
        primary_rule_outcome = "insufficient_aperture"
        primary_rule_class = "insufficient"
    elif all(retention_checks.values()):
        primary_rule_outcome = "retain_provenance_conditioned_candidate"
        primary_rule_class = "retain"
    else:
        primary_rule_outcome = "kill_current_hypothesis"
        primary_rule_class = "kill"

    if frozen_experiment_eligible:
        decision = primary_rule_outcome
        decision_class = primary_rule_class
    elif primary_rule_class == "insufficient":
        decision = "diagnostic_insufficient_aperture"
        decision_class = "diagnostic"
    elif primary_rule_class == "retain":
        decision = "diagnostic_pattern_meets_retention_rule"
        decision_class = "diagnostic"
    else:
        decision = "diagnostic_pattern_fails_retention_rule"
        decision_class = "diagnostic"

    path_payloads = [
        _path_payload(path, checkpoint_stage=checkpoint)
        for path in sorted(paths, key=lambda item: (item.q, item.path_hash))
    ]
    selection_material = json.dumps(
        {
            "config": {
                "checkpoint": checkpoint,
                "max_denominator": int(max_denominator),
                "path_length": int(path_length),
                "max_occurrences_per_q": int(max_occurrences_per_q),
                "max_out_degree": int(max_out_degree),
                "max_paths_per_q": int(max_paths_per_q),
                "stage_bin_width": int(stage_bin_width),
                "seed": int(seed),
            },
            "paths": [
                [list(occurrence.semantic_key) for occurrence in path.occurrences]
                for path in sorted(paths, key=lambda item: (item.q, item.path_hash))
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    selection_checksum = hashlib.sha256(
        selection_material.encode("utf-8")
    ).hexdigest()
    return {
        "tool_name": "moo_phase_transport_probe",
        "report_type": "provenance_ordered_cq_prefix_return_test",
        "schema_version": SCHEMA_VERSION,
        "experiment_id": experiment_id,
        "config": {
            "checkpoint_stage": checkpoint,
            "q_range_inclusive": [MIN_DENOMINATOR, int(max_denominator)],
            "path_length": int(path_length),
            "max_occurrences_per_q": int(max_occurrences_per_q),
            "max_out_degree": int(max_out_degree),
            "max_paths_per_q": int(max_paths_per_q),
            "null_samples": int(null_samples),
            "stage_bin_width": int(stage_bin_width),
            "exact_stage_stratification": int(stage_bin_width) == 1,
            "seed": int(seed),
            "frozen_experiment_eligible": frozen_experiment_eligible,
        },
        "frozen_experiment_identity": {
            "experiment_role": (
                frozen_profile["role"] if frozen_profile is not None else None
            ),
            "expected_experiment_id": (
                experiment_id if frozen_profile is not None else None
            ),
            "expected_database_sha256": (
                frozen_profile["database_sha256"]
                if frozen_profile is not None
                else None
            ),
            "observed_database_sha256": db_sha256,
            "expected_preregistration_path": (
                str(prereg_relative_path)
                if prereg_relative_path is not None
                else None
            ),
            "expected_preregistration_sha256": (
                frozen_profile["prereg_sha256"]
                if frozen_profile is not None
                else None
            ),
            "observed_preregistration_sha256": prereg_sha256,
            "minimum_decision_null_samples": MIN_DECISION_NULL_SAMPLES,
            "adequate_null_resolution": adequate_null_resolution,
            "checks": frozen_identity_checks,
            "eligible": frozen_experiment_eligible,
        },
        "claim_boundary": {
            "evidence_layer": "quarantined_counterfactual_over_read_only_strict_graph",
            "claim_status": (
                "make_or_break_exploratory_test"
                if frozen_experiment_eligible
                else "diagnostic_only_outside_frozen_primary_configuration"
            ),
            "configuration_status": (
                frozen_profile["configuration_status"]
                if frozen_experiment_eligible and frozen_profile is not None
                else "bounded_counterfactual_diagnostic_configuration"
            ),
            "allowed": (
                "the external C_q accumulator over these q-conditioned, "
                "residue-blind provenance walks did or did not exceed the two "
                "frozen cyclic controls"
            ),
            "runtime_operational": False,
            "provenance_walk_is_runtime_path": False,
            "rational_results_used_as_source_operands": False,
            "does_not_claim": [
                "rational phases operate in aligned MoO",
                "the provenance walk is a runtime path or orbit",
                "Q/Z is a ring under rational multiplication or division",
                "a return excess proves circle geometry",
                "failure in this aperture disproves every phase lens",
            ],
        },
        "graph_corpus": {
            "db_path": str(db_path),
            "db_sha256_used_for_primary_identity": db_sha256,
            "schema_version": corpus_schema_version,
            "config": corpus_config,
            "latest_stage": latest_stage,
            "checkpoint_stage": checkpoint,
            "nodes_at_checkpoint": nodes_at_checkpoint,
            "edges_at_checkpoint": edges_at_checkpoint,
            "connection": "SQLite URI mode=ro with PRAGMA query_only=ON",
            "mutated": False,
            "checkpoint_scope": (
                "every source-node, source-edge, exposure, and witness query is "
                "restricted to stage <= checkpoint"
            ),
            "strict_alignment": alignment,
        },
        "operator_boundary_audit": {
            "global_qz_descent": {
                op: classify_phase_operation(op) for op in ("+", "-", "*", "/")
            },
            "source_operation_counts_at_checkpoint": operator_counts,
            "selected_source_operation": "/",
            "selected_edge_relation": "retained_integer_torsion_preimage_selection",
            "other_operations_excluded_from_transport_labels": True,
            "division": division_audit,
            "status": "pass",
        },
        "graph_selection": {
            "occurrence_cap": occurrence_cap,
            "provenance_dag": dag_audit,
            "paths": path_audit,
            "selection_checksum_sha256": selection_checksum,
            "phase_residue_used_for_selection_or_tie_breaking": False,
            "phase_order_q_used_as_conditioning_stratum": True,
            "selection_description": "residue-blind conditional on exact order q",
            "sqlite_insertion_ids_used_for_selection_hashes": False,
        },
        "external_transport_definition": {
            "group": "ordinary finite cyclic additive group C_q",
            "initial_state": "X_0 = 0",
            "recurrence": "X_t = (X_(t-1) + s_t) mod q",
            "path_score": (
                "R(P) = count of t in [1, path_length-1] for which X_t = 0"
            ),
            "endpoint_excluded": True,
            "reason_endpoint_excluded": (
                "the endpoint is invariant under permutations of the exact step multiset"
            ),
            "counterfactual_only": True,
        },
        "aperture": {
            "holdout_path_count": len(holdout_paths),
            "discovery_path_count": len(discovery_paths),
            "holdout_q_values": holdout_q_values,
            "mutable_holdout_position_count": mutable_positions,
            "holdout_position_count": holdout_positions,
            "mutable_holdout_fraction": _fraction_stat_payload(mutable_fraction),
            "fixed_minimums": {
                "holdout_paths": MIN_HOLDOUT_PATHS,
                "holdout_denominators": MIN_HOLDOUT_DENOMINATORS,
                "mutable_positions": MIN_MUTABLE_POSITIONS,
                "mutable_fraction": _fraction_stat_payload(MIN_MUTABLE_FRACTION),
            },
            "checks": aperture_checks,
            "sufficient": aperture_sufficient,
        },
        "observed_holdout_statistic": observed,
        "controls": {
            "exact_step_permutation": exact_step_null,
            "stratified_label_shuffle": stratified_null,
        },
        "decision": {
            "status": decision,
            "class": decision_class,
            "frozen_experiment_eligible": frozen_experiment_eligible,
            "primary_rule_outcome": primary_rule_outcome,
            "primary_rule_class": primary_rule_class,
            "aperture_checks": aperture_checks,
            "retention_checks": retention_checks,
            "kill_interpretation": (
                "the current provenance-order hypothesis is killed in this frozen "
                "aperture only when primary identity and resolution checks pass, "
                "the aperture is sufficient, and either cyclic control is not exceeded"
            ),
        },
        "paths": path_payloads,
        "failure_modes_and_limits": [
            "caps can truncate occurrences, outgoing arcs, or accepted paths; all truncation is reported",
            "exact-stage/exposure/hub strata can make labels immutable, triggering the aperture guard",
            "shared-input adjacency is a graph-composable evidence relation, not a recorded rational transition",
            "paths are q-conditioned and residue-blind, not phase-blind across denominators",
            "occurrence-disjoint paths can still share input or result neighborhoods and are not independent runtime trials",
            "a negative result is aperture-specific; a positive result remains counterfactual and non-runtime",
            "the probe aborts rather than silently relaxing hard scan, adjacency, path, or null-work caps",
        ],
        "summary": {
            "eligible_division_occurrences_before_caps": len(eligible_occurrences),
            "selected_division_occurrences": int(occurrence_cap["total_selected"]),
            "accepted_paths": len(paths),
            "holdout_paths": len(holdout_paths),
            "holdout_q_count": len(holdout_q_values),
            "frozen_experiment_eligible": frozen_experiment_eligible,
            "decision": decision,
            "decision_class": decision_class,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the preregistered q-conditioned, residue-blind provenance-ordered "
            "C_q proper-prefix return test over a read-only strict MoO checkpoint."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument(
        "--max-q",
        "--max-denominator",
        dest="max_denominator",
        type=positive_int,
        default=DEFAULT_MAX_DENOMINATOR,
    )
    parser.add_argument("--path-length", type=positive_int, default=DEFAULT_PATH_LENGTH)
    parser.add_argument(
        "--max-occurrences-per-q",
        type=positive_int,
        default=DEFAULT_MAX_OCCURRENCES_PER_Q,
    )
    parser.add_argument(
        "--max-out-degree", type=positive_int, default=DEFAULT_MAX_OUT_DEGREE
    )
    parser.add_argument(
        "--max-paths-per-q", type=positive_int, default=DEFAULT_MAX_PATHS_PER_Q
    )
    parser.add_argument("--null-samples", type=positive_int, default=DEFAULT_NULL_SAMPLES)
    parser.add_argument(
        "--stage-bin-width", type=positive_int, default=DEFAULT_STAGE_BIN_WIDTH
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--checkpoint-stage", type=positive_int)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--write",
        type=Path,
        help="Also write the JSON report. Existing files are never overwritten.",
    )
    parser.add_argument(
        "--experiment-id",
        default=FROZEN_PRIMARY_EXPERIMENT_ID,
    )
    parser.add_argument(
        "--with-checksums",
        action="store_true",
        help="Include SHA-256 hashes for the source corpus and probe tool.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    payload = phase_transport_probe(
        db_path=Path(args.db),
        max_denominator=int(args.max_denominator),
        path_length=int(args.path_length),
        max_occurrences_per_q=int(args.max_occurrences_per_q),
        max_out_degree=int(args.max_out_degree),
        max_paths_per_q=int(args.max_paths_per_q),
        null_samples=int(args.null_samples),
        stage_bin_width=int(args.stage_bin_width),
        seed=int(args.seed),
        checkpoint_stage=(
            int(args.checkpoint_stage) if args.checkpoint_stage is not None else None
        ),
        experiment_id=str(args.experiment_id),
    )
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version=SCHEMA_VERSION,
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
