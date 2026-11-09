from __future__ import annotations

import argparse
import heapq
import json
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from fractions import Fraction
from itertools import combinations, combinations_with_replacement
from pathlib import Path
from statistics import median
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from moo.graph_corpus import format_key
from moo.graph_evidence import node_status
from moo.phase import (
    additive_return_order,
    circular_distance,
    circular_length,
    fraction_key,
    fraction_payload,
    phase_fraction,
    phase_key,
    phase_payload,
    sampled_path_payload,
)
from moo.research_utils import (
    connect_readonly,
    emit_json,
    positive_int,
    report_metadata,
    require_strict_alignment,
)


Key = Tuple[int, int]
MAX_DENOMINATOR = 512
MAX_PHASE_CLASSES = 128
MAX_PAIRS_PER_PHASE = 16
MAX_NEIGHBORHOOD_SAMPLE = 32
MAX_EDGE_REF_LIMIT = 32
MAX_SLACK_SAMPLE = 64
MAX_NODE_SCAN = 250_000
MAX_ADDITIVE_EDGE_SCAN = 500_000
MAX_MATERIALIZED_NEIGHBORHOOD_ENTRIES = 2_000_000
RETURN_POINT_LIMIT = 24


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row is not None else None


def _latest_stage(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(stage), 0) AS stage FROM stages").fetchone()
    return int(row["stage"]) if row is not None else 0


def _corpus_payload(
    conn: sqlite3.Connection,
    *,
    alignment: Dict[str, object],
    checkpoint_stage: int,
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
        "checkpoint_stage": int(checkpoint_stage),
        "nodes_at_checkpoint": int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM nodes WHERE first_stage <= ?",
                (int(checkpoint_stage),),
            ).fetchone()["n"]
        ),
        "edges_at_checkpoint": int(
            conn.execute(
                "SELECT COUNT(*) AS n FROM edges WHERE stage <= ?",
                (int(checkpoint_stage),),
            ).fetchone()["n"]
        ),
        "alignment": alignment,
    }


def _checkpoint_status(row: sqlite3.Row, checkpoint_stage: int) -> str:
    p = int(row["p"])
    q = int(row["q"])
    confirmed_stage = row["confirmed_stage"]
    if (p, q) == (1, 1):
        return "certainty"
    if q == 1 and p <= 0:
        return "relational_nonpositive"
    if (
        q == 1
        and p > 0
        and confirmed_stage is not None
        and int(confirmed_stage) <= int(checkpoint_stage)
    ):
        return "confirmed_positive_spine"
    if q == 1 and p > 0:
        return "speculative_positive_at_checkpoint"
    return "speculative_rational"


def _node_rows(
    conn: sqlite3.Connection,
    *,
    checkpoint_stage: int,
    max_denominator: int,
) -> List[sqlite3.Row]:
    node_count = int(
        conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM nodes
            WHERE first_stage <= ? AND q <= ?
            """,
            (int(checkpoint_stage), int(max_denominator)),
        ).fetchone()["n"]
    )
    if node_count > MAX_NODE_SCAN:
        raise ValueError(
            f"phase node scan would read {node_count} rows, above the safety "
            f"cap {MAX_NODE_SCAN}; reduce --max-denominator or use a smaller corpus"
        )
    return list(
        conn.execute(
            """
            SELECT
              n.node_id,
              n.p,
              n.q,
              n.label,
              n.kind,
              n.first_stage,
              n.confirmed_stage,
              n.first_edge_id,
              COUNT(e.edge_id) AS incoming_edge_count,
              COALESCE(SUM(CASE WHEN e.op = '+' THEN 1 ELSE 0 END), 0) AS plus_count,
              COALESCE(SUM(CASE WHEN e.op = '-' THEN 1 ELSE 0 END), 0) AS minus_count,
              COALESCE(SUM(CASE WHEN e.op = '*' THEN 1 ELSE 0 END), 0) AS multiply_count,
              COALESCE(SUM(CASE WHEN e.op = '/' THEN 1 ELSE 0 END), 0) AS divide_count,
              COALESCE(SUM(CASE WHEN e.op = 'seed' THEN 1 ELSE 0 END), 0) AS seed_count
            FROM nodes n
            LEFT JOIN edges e
              ON e.result_node_id = n.node_id AND e.stage <= ?
            WHERE n.first_stage <= ? AND n.q <= ?
            GROUP BY n.node_id
            ORDER BY n.q, n.p, n.node_id
            """,
            (
                int(checkpoint_stage),
                int(checkpoint_stage),
                int(max_denominator),
            ),
        ).fetchall()
    )


def _row_value(row: sqlite3.Row) -> Fraction:
    return Fraction(int(row["p"]), int(row["q"]))


def _row_phase(row: sqlite3.Row) -> Fraction:
    return phase_fraction(_row_value(row))


def _integer_lift(row: sqlite3.Row) -> int:
    lift = _row_value(row) - _row_phase(row)
    if lift.denominator != 1:
        raise AssertionError("phase fibre lift difference must be an integer")
    return int(lift)


def _operation_counts(row: sqlite3.Row) -> Dict[str, int]:
    return {
        "seed": int(row["seed_count"]),
        "+": int(row["plus_count"]),
        "-": int(row["minus_count"]),
        "*": int(row["multiply_count"]),
        "/": int(row["divide_count"]),
    }


def _node_payload(row: sqlite3.Row, *, checkpoint_stage: int) -> Dict[str, object]:
    value = _row_value(row)
    return {
        "node_id": int(row["node_id"]),
        "value": fraction_payload(value),
        "phase": phase_payload(value),
        "integer_lift": _integer_lift(row),
        "kind": str(row["kind"]),
        "historical_status": node_status(row),
        "status_at_checkpoint": _checkpoint_status(row, int(checkpoint_stage)),
        "first_stage": int(row["first_stage"]),
        "confirmed_stage": (
            int(row["confirmed_stage"])
            if row["confirmed_stage"] is not None
            else None
        ),
        "confirmed_stage_scope": (
            "eventual corpus field; status_at_checkpoint controls checkpoint claims"
        ),
        "first_edge_id": (
            int(row["first_edge_id"])
            if row["first_edge_id"] is not None
            else None
        ),
        "incoming_edge_count_at_checkpoint": int(row["incoming_edge_count"]),
        "incoming_operation_counts_at_checkpoint": _operation_counts(row),
    }


def _direct_input_ids(
    conn: sqlite3.Connection,
    *,
    node_id: int,
    checkpoint_stage: int,
) -> Set[int]:
    rows = conn.execute(
        """
        SELECT left_node_id AS node_id
        FROM edges
        WHERE result_node_id = ? AND stage <= ? AND left_node_id IS NOT NULL
        UNION
        SELECT right_node_id AS node_id
        FROM edges
        WHERE result_node_id = ? AND stage <= ? AND right_node_id IS NOT NULL
        """,
        (
            int(node_id),
            int(checkpoint_stage),
            int(node_id),
            int(checkpoint_stage),
        ),
    ).fetchall()
    return {int(row["node_id"]) for row in rows}


def _shared_input_neighborhood_ids(
    conn: sqlite3.Connection,
    *,
    node_id: int,
    checkpoint_stage: int,
) -> Set[int]:
    rows = conn.execute(
        """
        WITH input_nodes(node_id) AS (
          SELECT left_node_id
          FROM edges
          WHERE result_node_id = ? AND stage <= ? AND left_node_id IS NOT NULL
          UNION
          SELECT right_node_id
          FROM edges
          WHERE result_node_id = ? AND stage <= ? AND right_node_id IS NOT NULL
        ),
        neighbor_results(result_node_id) AS (
          SELECT e.result_node_id
          FROM input_nodes i
          JOIN edges e ON e.left_node_id = i.node_id
          WHERE e.stage <= ?
          UNION
          SELECT e.result_node_id
          FROM input_nodes i
          JOIN edges e ON e.right_node_id = i.node_id
          WHERE e.stage <= ?
        )
        SELECT result_node_id
        FROM neighbor_results
        WHERE result_node_id != ?
        ORDER BY result_node_id
        """,
        (
            int(node_id),
            int(checkpoint_stage),
            int(node_id),
            int(checkpoint_stage),
            int(checkpoint_stage),
            int(checkpoint_stage),
            int(node_id),
        ),
    ).fetchall()
    return {int(row["result_node_id"]) for row in rows}


def _chunks(values: Sequence[int], size: int = 800) -> Iterable[List[int]]:
    for start in range(0, len(values), int(size)):
        yield list(values[start : start + int(size)])


def _bulk_populate_graph_caches(
    conn: sqlite3.Connection,
    *,
    node_ids: Iterable[int],
    checkpoint_stage: int,
    direct_input_cache: Dict[int, Set[int]],
    neighborhood_cache: Dict[int, Set[int]],
) -> None:
    missing = sorted(
        {
            int(node_id)
            for node_id in node_ids
            if int(node_id) not in direct_input_cache
            or int(node_id) not in neighborhood_cache
        }
    )
    if not missing:
        return
    for node_id in missing:
        direct_input_cache.setdefault(node_id, set())
        neighborhood_cache.setdefault(node_id, set())

    materialized_entries = sum(len(values) for values in neighborhood_cache.values())
    if materialized_entries > MAX_MATERIALIZED_NEIGHBORHOOD_ENTRIES:
        raise ValueError(
            "exact graph-neighborhood materialization exceeded the hard cap "
            f"{MAX_MATERIALIZED_NEIGHBORHOOD_ENTRIES}; reduce phase or pair limits"
        )

    input_to_targets: Dict[int, Set[int]] = defaultdict(set)
    for chunk in _chunks(missing):
        placeholders = ",".join("?" for _ in chunk)
        rows = conn.execute(
            f"""
            SELECT result_node_id, left_node_id, right_node_id
            FROM edges
            WHERE stage <= ? AND result_node_id IN ({placeholders})
            """,
            (int(checkpoint_stage), *chunk),
        ).fetchall()
        for row in rows:
            target = int(row["result_node_id"])
            for raw_input in (row["left_node_id"], row["right_node_id"]):
                if raw_input is None:
                    continue
                input_id = int(raw_input)
                direct_input_cache[target].add(input_id)
                input_to_targets[input_id].add(target)

    input_ids = sorted(input_to_targets)
    for chunk in _chunks(input_ids):
        placeholders = ",".join("?" for _ in chunk)
        queries = (
            f"""
            SELECT left_node_id AS input_node_id, result_node_id
            FROM edges
            WHERE stage <= ? AND left_node_id IN ({placeholders})
            """,
            f"""
            SELECT right_node_id AS input_node_id, result_node_id
            FROM edges
            WHERE stage <= ? AND right_node_id IN ({placeholders})
            """,
        )
        for query in queries:
            for row in conn.execute(query, (int(checkpoint_stage), *chunk)):
                input_id = int(row["input_node_id"])
                result_id = int(row["result_node_id"])
                for target in input_to_targets[input_id]:
                    if result_id == target:
                        continue
                    neighborhood = neighborhood_cache[target]
                    if result_id in neighborhood:
                        continue
                    if materialized_entries >= MAX_MATERIALIZED_NEIGHBORHOOD_ENTRIES:
                        raise ValueError(
                            "exact graph-neighborhood materialization exceeded the hard cap "
                            f"{MAX_MATERIALIZED_NEIGHBORHOOD_ENTRIES}; "
                            "reduce phase or pair limits"
                        )
                    neighborhood.add(result_id)
                    materialized_entries += 1


def _incoming_edge_refs(
    conn: sqlite3.Connection,
    *,
    node_id: int,
    checkpoint_stage: int,
    edge_ref_limit: int,
) -> List[Dict[str, object]]:
    rows = conn.execute(
        """
        SELECT edge_id, stage, op, left_node_id, right_node_id, result_node_id
        FROM edges
        WHERE result_node_id = ? AND stage <= ?
        ORDER BY stage, edge_id
        LIMIT ?
        """,
        (int(node_id), int(checkpoint_stage), int(edge_ref_limit)),
    ).fetchall()
    return [
        {
            "edge_id": int(row["edge_id"]),
            "stage": int(row["stage"]),
            "op": str(row["op"]),
            "left_node_id": (
                int(row["left_node_id"])
                if row["left_node_id"] is not None
                else None
            ),
            "right_node_id": (
                int(row["right_node_id"])
                if row["right_node_id"] is not None
                else None
            ),
            "result_node_id": int(row["result_node_id"]),
        }
        for row in rows
    ]


def _set_overlap_payload(
    left: Set[int],
    right: Set[int],
    *,
    sample_limit: int,
) -> Dict[str, object]:
    intersection = left & right
    union = left | right
    left_only = left - right
    right_only = right - left
    if union:
        similarity = Fraction(len(intersection), len(union))
        distance = Fraction(1, 1) - similarity
        similarity_payload: Optional[Dict[str, object]] = fraction_payload(similarity)
        distance_payload: Optional[Dict[str, object]] = fraction_payload(distance)
        similarity_decimal: Optional[float] = float(similarity)
        distance_decimal: Optional[float] = float(distance)
    else:
        similarity_payload = None
        distance_payload = None
        similarity_decimal = None
        distance_decimal = None
    return {
        "left_count": len(left),
        "right_count": len(right),
        "intersection_count": len(intersection),
        "union_count": len(union),
        "jaccard_similarity": similarity_payload,
        "jaccard_distance": distance_payload,
        "jaccard_similarity_decimal": similarity_decimal,
        "jaccard_distance_decimal": distance_decimal,
        "empty_union": not bool(union),
        "shared_node_ids_sample": sorted(intersection)[: int(sample_limit)],
        "left_only_node_ids_sample": sorted(left_only)[: int(sample_limit)],
        "right_only_node_ids_sample": sorted(right_only)[: int(sample_limit)],
    }


def _operation_divergence(left: sqlite3.Row, right: sqlite3.Row) -> Dict[str, object]:
    left_counts = _operation_counts(left)
    right_counts = _operation_counts(right)
    operations = sorted(set(left_counts) | set(right_counts))
    raw_l1 = sum(abs(left_counts[op] - right_counts[op]) for op in operations)
    left_total = sum(left_counts.values())
    right_total = sum(right_counts.values())
    if left_total == 0 and right_total == 0:
        total_variation = Fraction(0, 1)
    elif left_total == 0 or right_total == 0:
        total_variation = Fraction(1, 1)
    else:
        total_variation = sum(
            (
                abs(
                    Fraction(left_counts[op], left_total)
                    - Fraction(right_counts[op], right_total)
                )
                for op in operations
            ),
            Fraction(0, 1),
        ) / 2
    return {
        "left_counts": left_counts,
        "right_counts": right_counts,
        "raw_count_l1": int(raw_l1),
        "total_variation": fraction_payload(total_variation),
        "total_variation_decimal": float(total_variation),
    }


def _metadata_divergence(
    left: sqlite3.Row,
    right: sqlite3.Row,
    *,
    checkpoint_stage: int,
) -> Dict[str, object]:
    left_status = _checkpoint_status(left, int(checkpoint_stage))
    right_status = _checkpoint_status(right, int(checkpoint_stage))
    left_eventual_confirmed = left["confirmed_stage"]
    right_eventual_confirmed = right["confirmed_stage"]
    left_confirmed = (
        int(left_eventual_confirmed)
        if left_eventual_confirmed is not None
        and int(left_eventual_confirmed) <= int(checkpoint_stage)
        else None
    )
    right_confirmed = (
        int(right_eventual_confirmed)
        if right_eventual_confirmed is not None
        and int(right_eventual_confirmed) <= int(checkpoint_stage)
        else None
    )
    confirmation_gap = (
        abs(int(left_confirmed) - int(right_confirmed))
        if left_confirmed is not None and right_confirmed is not None
        else None
    )
    operation = _operation_divergence(left, right)
    return {
        "status_mismatch": left_status != right_status,
        "confirmation_presence_mismatch_at_checkpoint": (left_confirmed is None)
        != (right_confirmed is None),
        "first_stage_gap": abs(int(left["first_stage"]) - int(right["first_stage"])),
        "confirmation_stage_gap_at_checkpoint": confirmation_gap,
        "incoming_edge_count_gap": abs(
            int(left["incoming_edge_count"]) - int(right["incoming_edge_count"])
        ),
        "operation_signature": operation,
    }


def _candidate_priority(
    left: sqlite3.Row,
    right: sqlite3.Row,
    *,
    checkpoint_stage: int,
) -> Tuple[object, ...]:
    divergence = _metadata_divergence(
        left,
        right,
        checkpoint_stage=int(checkpoint_stage),
    )
    return (
        int(bool(divergence["status_mismatch"])),
        int(bool(divergence["confirmation_presence_mismatch_at_checkpoint"])),
        int(divergence["operation_signature"]["raw_count_l1"]),
        int(divergence["incoming_edge_count_gap"]),
        int(divergence["first_stage_gap"]),
        abs(_integer_lift(left) - _integer_lift(right)),
    )


def _candidate_pairs(
    rows: Sequence[sqlite3.Row],
    *,
    checkpoint_stage: int,
    pair_limit: int,
) -> Dict[str, object]:
    ordered = sorted(rows, key=lambda row: (_integer_lift(row), int(row["node_id"])))
    possible_pair_count = len(ordered) * (len(ordered) - 1) // 2
    candidates: Dict[Tuple[int, int], Dict[str, object]] = {}

    def add(left: sqlite3.Row, right: sqlite3.Row, reason: str) -> None:
        if int(left["node_id"]) == int(right["node_id"]):
            return
        if _row_value(left) > _row_value(right):
            left, right = right, left
        key = int(left["node_id"]), int(right["node_id"])
        record = candidates.setdefault(
            key,
            {"left": left, "right": right, "reasons": set()},
        )
        record["reasons"].add(str(reason))

    for left, right in zip(ordered, ordered[1:]):
        add(left, right, "adjacent_observed_lifts")

    landmarks: Dict[int, sqlite3.Row] = {}
    if ordered:
        for row in (
            ordered[0],
            ordered[-1],
            min(ordered, key=lambda item: (int(item["first_stage"]), int(item["node_id"]))),
            max(ordered, key=lambda item: (int(item["first_stage"]), int(item["node_id"]))),
            min(
                ordered,
                key=lambda item: (int(item["incoming_edge_count"]), int(item["node_id"])),
            ),
            max(
                ordered,
                key=lambda item: (int(item["incoming_edge_count"]), int(item["node_id"])),
            ),
        ):
            landmarks[int(row["node_id"])] = row
        status_representatives: Dict[str, sqlite3.Row] = {}
        for row in ordered:
            status_representatives.setdefault(
                _checkpoint_status(row, int(checkpoint_stage)),
                row,
            )
        for row in status_representatives.values():
            landmarks[int(row["node_id"])] = row

    for left, right in combinations(landmarks.values(), 2):
        add(left, right, "landmark_pair")

    ranked = sorted(
        candidates.values(),
        key=lambda item: (
            _candidate_priority(
                item["left"],
                item["right"],
                checkpoint_stage=int(checkpoint_stage),
            ),
            -int(item["left"]["node_id"]),
            -int(item["right"]["node_id"]),
        ),
        reverse=True,
    )
    selected = ranked[: int(pair_limit)]
    adjacent_ranked = [
        item for item in ranked if "adjacent_observed_lifts" in item["reasons"]
    ]
    if (
        selected
        and adjacent_ranked
        and not any(
            "adjacent_observed_lifts" in item["reasons"] for item in selected
        )
    ):
        selected[-1] = adjacent_ranked[0]
        selected.sort(
            key=lambda item: _candidate_priority(
                item["left"],
                item["right"],
                checkpoint_stage=int(checkpoint_stage),
            ),
            reverse=True,
        )
    for item in selected:
        item["reasons"] = sorted(item["reasons"])
    if possible_pair_count == len(candidates) and len(selected) == len(candidates):
        completeness = "exhaustive"
    elif len(selected) == len(candidates):
        completeness = "adjacent_plus_landmarks_complete"
    else:
        completeness = "bounded_adjacent_plus_landmarks"
    return {
        "possible_pair_count": int(possible_pair_count),
        "adjacent_lift_pair_count": max(0, len(ordered) - 1),
        "landmark_count": len(landmarks),
        "candidate_pair_count": len(candidates),
        "selected_pair_count": len(selected),
        "selected_adjacent_pair_count": sum(
            "adjacent_observed_lifts" in item["reasons"] for item in selected
        ),
        "search_completeness": completeness,
        "selected": selected,
    }


def _translation_witness(
    conn: sqlite3.Connection,
    *,
    left: sqlite3.Row,
    right: sqlite3.Row,
    checkpoint_stage: int,
    edge_ref_limit: int,
) -> Dict[str, object]:
    left_value = _row_value(left)
    right_value = _row_value(right)
    if right_value - left_value != 1:
        return {
            "applicable": False,
            "reason": "reported pair is not separated by one integer lift",
        }
    one = conn.execute("SELECT node_id FROM nodes WHERE p = 1 AND q = 1").fetchone()
    if one is None:
        return {"applicable": True, "present": False, "blocker": "missing_ref_one"}
    one_id = int(one["node_id"])
    rows = conn.execute(
        """
        SELECT edge_id, stage, left_node_id, right_node_id
        FROM edges
        WHERE result_node_id = ?
          AND op = '+'
          AND stage <= ?
          AND (
            (left_node_id = ? AND right_node_id = ?)
            OR
            (left_node_id = ? AND right_node_id = ?)
          )
        ORDER BY stage, edge_id
        """,
        (
            int(right["node_id"]),
            int(checkpoint_stage),
            int(left["node_id"]),
            one_id,
            one_id,
            int(left["node_id"]),
        ),
    ).fetchall()
    expected = 1 if int(left["node_id"]) == one_id else 2
    present = bool(rows)
    if present:
        blocker = None
    elif not (
        int(left["q"]) == 1
        and int(left["p"]) >= 1
        and left["confirmed_stage"] is not None
        and int(left["confirmed_stage"]) <= int(checkpoint_stage)
    ):
        blocker = "operand_not_confirmed_positive_spine"
    else:
        blocker = "edge_absent_at_checkpoint"
    return {
        "applicable": True,
        "relation": f"{left['label']} + 1 -> {right['label']}",
        "present": present,
        "edge_count": len(rows),
        "expected_directed_edges": expected,
        "status": (
            "complete_directed"
            if len(rows) == expected
            else "absent"
            if not rows
            else "partial_or_unexpected"
        ),
        "blocker": blocker,
        "edge_refs": [
            {
                "edge_id": int(row["edge_id"]),
                "stage": int(row["stage"]),
                "left_node_id": int(row["left_node_id"]),
                "right_node_id": int(row["right_node_id"]),
            }
            for row in rows[: int(edge_ref_limit)]
        ],
    }


def _pair_payload(
    conn: sqlite3.Connection,
    *,
    left: sqlite3.Row,
    right: sqlite3.Row,
    relationship: str,
    reasons: Sequence[str],
    checkpoint_stage: int,
    latest_stage: int,
    db_path: Path,
    direct_input_cache: Dict[int, Set[int]],
    neighborhood_cache: Dict[int, Set[int]],
    edge_ref_cache: Dict[int, List[Dict[str, object]]],
    neighborhood_sample_limit: int,
    edge_ref_limit: int,
) -> Dict[str, object]:
    left_id = int(left["node_id"])
    right_id = int(right["node_id"])
    for node_id in (left_id, right_id):
        if node_id not in direct_input_cache:
            direct_input_cache[node_id] = _direct_input_ids(
                conn,
                node_id=node_id,
                checkpoint_stage=int(checkpoint_stage),
            )
        if node_id not in neighborhood_cache:
            neighborhood_cache[node_id] = _shared_input_neighborhood_ids(
                conn,
                node_id=node_id,
                checkpoint_stage=int(checkpoint_stage),
            )
        if node_id not in edge_ref_cache:
            edge_ref_cache[node_id] = _incoming_edge_refs(
                conn,
                node_id=node_id,
                checkpoint_stage=int(checkpoint_stage),
                edge_ref_limit=int(edge_ref_limit),
            )

    left_value = _row_value(left)
    right_value = _row_value(right)
    phase_distance = circular_distance(left_value, right_value)
    source_distance = abs(left_value - right_value)
    contraction = source_distance - phase_distance
    if contraction < 0:
        raise AssertionError("phase quotient expanded source absolute distance")
    metadata = _metadata_divergence(
        left,
        right,
        checkpoint_stage=int(checkpoint_stage),
    )
    direct_input = _set_overlap_payload(
        direct_input_cache[left_id],
        direct_input_cache[right_id],
        sample_limit=int(neighborhood_sample_limit),
    )
    neighborhood = _set_overlap_payload(
        neighborhood_cache[left_id],
        neighborhood_cache[right_id],
        sample_limit=int(neighborhood_sample_limit),
    )
    left_phase_key = phase_key(phase_fraction(left_value))
    candidate_id = (
        f"{relationship}:{format_key(left_phase_key)}:"
        f"{format_key(fraction_key(left_value))}->{format_key(fraction_key(right_value))}:"
        f"{left_id}-{right_id}"
    )
    payload = {
        "candidate_id": candidate_id,
        "relationship": relationship,
        "why_flagged": list(reasons),
        "projection_or_filter": "exact rational phase modulo one",
        "phase_metric": {
            "left_phase": phase_payload(left_value),
            "right_phase": phase_payload(right_value),
            "distance_turns": fraction_payload(phase_distance),
            "zero_distance": phase_distance == 0,
            "source_absolute_distance": fraction_payload(source_distance),
            "distance_contracted_by": fraction_payload(contraction),
        },
        "nodes": {
            "left": _node_payload(left, checkpoint_stage=int(checkpoint_stage)),
            "right": _node_payload(right, checkpoint_stage=int(checkpoint_stage)),
        },
        "edges": {
            "left_incoming_edge_refs": edge_ref_cache[left_id],
            "right_incoming_edge_refs": edge_ref_cache[right_id],
            "unit_translation": _translation_witness(
                conn,
                left=left,
                right=right,
                checkpoint_stage=int(checkpoint_stage),
                edge_ref_limit=int(edge_ref_limit),
            ),
        },
        "graph_divergence": {
            "status_and_arrival": metadata,
            "direct_input_set": {
                "metric": "direct_input_set_jaccard",
                **direct_input,
            },
            "shared_input_result_neighborhood": {
                "metric": "shared_input_result_neighborhood_jaccard",
                **neighborhood,
            },
            "ranking_is_not_a_composite_metric": True,
        },
        "neighborhood_query": {
            "checkpoint_exact": int(checkpoint_stage) == int(latest_stage),
            "commands": (
                [
                    f'python3 moo_graph_query.py --db "{db_path}" --node "{left["label"]}" --neighborhood --pretty',
                    f'python3 moo_graph_query.py --db "{db_path}" --node "{right["label"]}" --neighborhood --pretty',
                ]
                if int(checkpoint_stage) == int(latest_stage)
                else []
            ),
            "limit": (
                None
                if int(checkpoint_stage) == int(latest_stage)
                else "moo_graph_query.py has no checkpoint filter; the report's exact checkpoint-scoped node and edge references must be used instead"
            ),
        },
        "confirmation_status": {
            "left": _checkpoint_status(left, int(checkpoint_stage)),
            "right": _checkpoint_status(right, int(checkpoint_stage)),
        },
        "interpretation_limits": [
            "Zero phase distance is quotient identity, not source-node identity.",
            "Neighborhood divergence is graph evidence at the named checkpoint, not circle geometry inside the runtime.",
        ],
    }
    return payload


def _pair_rank_key(payload: Dict[str, object]) -> Tuple[object, ...]:
    divergence = payload["graph_divergence"]
    neighborhood = divergence["shared_input_result_neighborhood"]
    direct_input = divergence["direct_input_set"]
    metadata = divergence["status_and_arrival"]
    neighborhood_distance = neighborhood["jaccard_distance_decimal"]
    direct_distance = direct_input["jaccard_distance_decimal"]
    return (
        int(neighborhood_distance is not None),
        float(neighborhood_distance) if neighborhood_distance is not None else -1.0,
        min(int(neighborhood["left_count"]), int(neighborhood["right_count"])),
        int(direct_distance is not None),
        float(direct_distance) if direct_distance is not None else -1.0,
        float(metadata["operation_signature"]["total_variation_decimal"]),
        int(bool(metadata["status_mismatch"])),
        int(metadata["incoming_edge_count_gap"]),
        int(metadata["first_stage_gap"]),
    )


def _control_index(rows: Iterable[sqlite3.Row]) -> Dict[Tuple[int, int], List[sqlite3.Row]]:
    index: Dict[Tuple[int, int], List[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        index[(int(row["q"]), _integer_lift(row))].append(row)
    return index


def _matched_control(
    left: sqlite3.Row,
    right: sqlite3.Row,
    *,
    checkpoint_stage: int,
    index: Dict[Tuple[int, int], List[sqlite3.Row]],
) -> Dict[str, object]:
    phase = _row_phase(left)
    denominator = int(right["q"])
    target_lift = _integer_lift(right)
    if denominator in {1, 2}:
        return {
            "status": "structurally_not_applicable",
            "reason": (
                "this reduced denominator has only one exact-order phase, so no "
                "different-phase control exists in the exact denominator/lift stratum"
            ),
            "row": None,
        }
    candidates = [
        row
        for row in index.get((denominator, target_lift), [])
        if _row_phase(row) != phase
    ]
    if not candidates:
        return {
            "status": "corpus_match_missing",
            "reason": (
                "a different phase is mathematically available at this denominator, "
                "but the checkpoint has no node in the exact denominator/lift stratum"
            ),
            "row": None,
        }
    right_status = _checkpoint_status(right, int(checkpoint_stage))
    selected = min(
        candidates,
        key=lambda row: (
            _checkpoint_status(row, int(checkpoint_stage)) != right_status,
            abs(int(row["first_stage"]) - int(right["first_stage"])),
            abs(int(row["incoming_edge_count"]) - int(right["incoming_edge_count"])),
            abs(_row_value(row) - _row_value(right)),
            int(row["node_id"]),
        ),
    )
    selected_status = _checkpoint_status(selected, int(checkpoint_stage))
    stage_gap = abs(int(selected["first_stage"]) - int(right["first_stage"]))
    incoming_gap = abs(
        int(selected["incoming_edge_count"]) - int(right["incoming_edge_count"])
    )
    return {
        "status": "matched",
        "reason": None,
        "row": selected,
        "match_quality": {
            "denominator_exact": True,
            "integer_lift_exact": True,
            "checkpoint_status_exact": selected_status == right_status,
            "first_stage_gap": int(stage_gap),
            "incoming_edge_count_gap": int(incoming_gap),
            "exposure_match_exact": (
                selected_status == right_status and stage_gap == 0 and incoming_gap == 0
            ),
            "caliper_policy": "none in v1; exact gaps are reported",
        },
    }


def _metric_calibration(phases: Sequence[Fraction]) -> Dict[str, object]:
    route_checks = 0
    tight = 0
    strict = 0
    violations: List[Dict[str, object]] = []
    triple_count = 0
    for first, second, third in combinations_with_replacement(phases, 3):
        triple_count += 1
        routes = (
            (first, second, third),
            (first, third, second),
            (second, first, third),
        )
        for start, via, end in routes:
            route_checks += 1
            first_leg = circular_distance(start, via)
            second_leg = circular_distance(via, end)
            direct = circular_distance(start, end)
            slack = first_leg + second_leg - direct
            if slack < 0:
                violations.append(
                    {
                        "start": fraction_payload(start),
                        "via": fraction_payload(via),
                        "end": fraction_payload(end),
                        "slack": fraction_payload(slack),
                    }
                )
            elif slack == 0:
                tight += 1
            else:
                strict += 1
    distinct_phase_count = len(set(phases))
    if violations:
        status = "fail"
    elif distinct_phase_count < 3:
        status = "insufficient_scope"
    else:
        status = "pass"
    return {
        "scope": "all routed inequalities over unordered triples of reported phases",
        "phase_count": len(phases),
        "distinct_phase_count": int(distinct_phase_count),
        "unordered_triple_count_with_repetition": int(triple_count),
        "route_check_count": int(route_checks),
        "tight_route_count": int(tight),
        "strict_route_count": int(strict),
        "violation_count": len(violations),
        "violations": violations[:8],
        "status": status,
        "interpretation": (
            "This calibrates the exact implementation; triangle-inequality success "
            "is a theorem, not a corpus discovery."
        ),
    }


def _external_return_walk(phase: Fraction) -> Dict[str, object]:
    order = additive_return_order(phase)
    canonical_net_lift = order * phase
    if canonical_net_lift.denominator != 1:
        raise AssertionError("reduced phase did not return to an integer lift")
    if order <= RETURN_POINT_LIMIT:
        lift_points = [index * phase for index in range(order + 1)]
        payload = sampled_path_payload(lift_points, include_points=True)
    else:
        phase_path_length = order * circular_length(phase)
        lift_path_length = canonical_net_lift
        payload = {
            "sample_count": order + 1,
            "points": None,
            "projected_phase_points": None,
            "points_omitted": True,
            "lift_path_length": fraction_payload(lift_path_length),
            "sampled_phase_path_length": fraction_payload(phase_path_length),
            "lift_endpoint_distance": fraction_payload(lift_path_length),
            "phase_endpoint_distance": fraction_payload(0),
            "sampled_step_contraction": fraction_payload(
                lift_path_length - phase_path_length
            ),
            "endpoint_contraction": fraction_payload(lift_path_length),
            "phase_detour": fraction_payload(phase_path_length),
            "phase_return": True,
            "sampled_net_integer_lift": int(canonical_net_lift),
            "sampling_limit": (
                "Endpoint sampling can alias a continuous full turn to zero length; "
                "path length is preserved only to the resolution of the retained steps."
            ),
        }
    return {
        "phase": phase_payload(phase),
        "step_length_turns": fraction_payload(circular_length(phase)),
        "canonical_representative_convention": (
            "Use the unique phase p/q in [0,1); repeated lifts are k*p/q. "
            "The resulting net lift is convention-dependent, not a Q/Z invariant."
        ),
        "canonical_representative_net_lift": int(canonical_net_lift),
        "shortest_arc_orientation_ambiguous": phase == Fraction(1, 2),
        "sampled_canonical_lift_orbit": payload,
        "quotient_invariants": [
            "phase sequence modulo one",
            "additive return order",
            "return to the identity phase",
        ],
        "graph_witness_status": (
            "identity_only_trivial"
            if phase == 0
            else "external_not_graph_witnessed_under_strict_operand_rule"
        ),
        "interpretation_limit": (
            "The orbit is exact external Q/Z arithmetic. It is not a runtime path, "
            "and shortest-arc sampled steps can alias orientation or winding."
        ),
    }


def _fraction_histogram(counter: Counter[Fraction]) -> Dict[str, int]:
    return {
        fraction_payload(value)["frac"]: int(count)
        for value, count in sorted(counter.items())
    }


def _edge_route_payload(
    row: sqlite3.Row,
    *,
    left: Fraction,
    right: Fraction,
    result: Fraction,
) -> Dict[str, object]:
    phase_first = circular_length(left)
    phase_second = circular_distance(left, result)
    phase_direct = circular_length(result)
    phase_slack = phase_first + phase_second - phase_direct
    source_first = abs(left)
    source_second = abs(result - left)
    source_direct = abs(result)
    source_slack = source_first + source_second - source_direct
    return {
        "edge_id": int(row["edge_id"]),
        "stage": int(row["stage"]),
        "op": str(row["op"]),
        "nodes": {
            "left": {
                "node_id": int(row["left_node_id"]),
                "value": fraction_payload(left),
            },
            "right": {
                "node_id": int(row["right_node_id"]),
                "value": fraction_payload(right),
            },
            "result": {
                "node_id": int(row["result_node_id"]),
                "value": fraction_payload(result),
            },
        },
        "source_absolute_route": {
            "first_leg": fraction_payload(source_first),
            "second_leg": fraction_payload(source_second),
            "direct_distance": fraction_payload(source_direct),
            "triangle_slack": fraction_payload(source_slack),
            "status": "tight" if source_slack == 0 else "strict",
        },
        "phase_route": {
            "first_leg": fraction_payload(phase_first),
            "second_leg": fraction_payload(phase_second),
            "direct_distance": fraction_payload(phase_direct),
            "triangle_slack": fraction_payload(phase_slack),
            "status": "tight" if phase_slack == 0 else "strict",
        },
    }


def _push_largest_sample(
    heap: List[Tuple[Fraction, int, Dict[str, object]]],
    *,
    score: Fraction,
    edge_id: int,
    payload: Dict[str, object],
    limit: int,
) -> None:
    item = score, int(edge_id), payload
    if len(heap) < int(limit):
        heapq.heappush(heap, item)
    elif (score, int(edge_id)) > (heap[0][0], heap[0][1]):
        heapq.heapreplace(heap, item)


def _additive_triangle_audit(
    conn: sqlite3.Connection,
    *,
    checkpoint_stage: int,
    slack_sample_limit: int,
    full_scan: bool,
) -> Dict[str, object]:
    edge_count = int(
        conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM edges
            WHERE stage <= ? AND op IN ('+', '-')
            """,
            (int(checkpoint_stage),),
        ).fetchone()["n"]
    )
    if edge_count > MAX_ADDITIVE_EDGE_SCAN and not bool(full_scan):
        raise ValueError(
            f"additive triangle audit would scan {edge_count} edges, above the "
            f"safety cap {MAX_ADDITIVE_EDGE_SCAN}; pass --full-scan to acknowledge it"
        )

    by_op: Dict[str, Dict[str, object]] = {}
    for op in ("+", "-"):
        by_op[op] = {
            "edge_count": 0,
            "validated_edge_count": 0,
            "operation_relation_failure_count": 0,
            "phase_step_relation_failure_count": 0,
            "source_step_relation_failure_count": 0,
            "nonidentity_phase_operand_edge_count": 0,
            "nonidentity_phase_result_edge_count": 0,
            "phase_tight_edge_count": 0,
            "phase_strict_edge_count": 0,
            "phase_triangle_violation_count": 0,
            "source_tight_edge_count": 0,
            "source_strict_edge_count": 0,
            "source_triangle_violation_count": 0,
            "source_strict_phase_tight_erasure_count": 0,
            "phase_slack_sum": Fraction(0, 1),
            "source_slack_sum": Fraction(0, 1),
            "phase_slack_max": Fraction(0, 1),
            "source_slack_max": Fraction(0, 1),
            "phase_slack_histogram": Counter(),
            "source_slack_histogram": Counter(),
            "erasure_samples": [],
            "phase_strict_samples": [],
            "validation_failure_samples": [],
        }

    rows = conn.execute(
        """
        SELECT
          e.edge_id,
          e.stage,
          e.op,
          l.node_id AS left_node_id,
          l.p AS left_p,
          l.q AS left_q,
          r.node_id AS right_node_id,
          r.p AS right_p,
          r.q AS right_q,
          z.node_id AS result_node_id,
          z.p AS result_p,
          z.q AS result_q
        FROM edges e
        JOIN nodes l ON l.node_id = e.left_node_id
        JOIN nodes r ON r.node_id = e.right_node_id
        JOIN nodes z ON z.node_id = e.result_node_id
        WHERE e.stage <= ? AND e.op IN ('+', '-')
        ORDER BY e.edge_id
        """,
        (int(checkpoint_stage),),
    )
    for row in rows:
        op = str(row["op"])
        stats = by_op[op]
        left = Fraction(int(row["left_p"]), int(row["left_q"]))
        right = Fraction(int(row["right_p"]), int(row["right_q"]))
        result = Fraction(int(row["result_p"]), int(row["result_q"]))
        expected = left + right if op == "+" else left - right
        stats["edge_count"] += 1
        if result != expected:
            stats["operation_relation_failure_count"] += 1
            if len(stats["validation_failure_samples"]) < int(slack_sample_limit):
                failure = _edge_route_payload(
                    row,
                    left=left,
                    right=right,
                    result=result,
                )
                failure["expected_result"] = fraction_payload(expected)
                stats["validation_failure_samples"].append(failure)
            continue
        stats["validated_edge_count"] += 1

        phase_first = circular_length(left)
        phase_second = circular_distance(left, result)
        phase_direct = circular_length(result)
        phase_slack = phase_first + phase_second - phase_direct
        source_first = abs(left)
        source_second = abs(result - left)
        source_direct = abs(result)
        source_slack = source_first + source_second - source_direct

        if phase_second != circular_length(right):
            stats["phase_step_relation_failure_count"] += 1
        if source_second != abs(right):
            stats["source_step_relation_failure_count"] += 1
        if phase_fraction(left) != 0 or phase_fraction(right) != 0:
            stats["nonidentity_phase_operand_edge_count"] += 1
        if phase_fraction(result) != 0:
            stats["nonidentity_phase_result_edge_count"] += 1

        if phase_slack < 0:
            stats["phase_triangle_violation_count"] += 1
        elif phase_slack == 0:
            stats["phase_tight_edge_count"] += 1
        else:
            stats["phase_strict_edge_count"] += 1
        if source_slack < 0:
            stats["source_triangle_violation_count"] += 1
        elif source_slack == 0:
            stats["source_tight_edge_count"] += 1
        else:
            stats["source_strict_edge_count"] += 1

        stats["phase_slack_sum"] += phase_slack
        stats["source_slack_sum"] += source_slack
        stats["phase_slack_max"] = max(stats["phase_slack_max"], phase_slack)
        stats["source_slack_max"] = max(stats["source_slack_max"], source_slack)
        stats["phase_slack_histogram"][phase_slack] += 1
        stats["source_slack_histogram"][source_slack] += 1

        payload: Optional[Dict[str, object]] = None
        if source_slack > 0 and phase_slack == 0:
            stats["source_strict_phase_tight_erasure_count"] += 1
            payload = _edge_route_payload(
                row,
                left=left,
                right=right,
                result=result,
            )
            _push_largest_sample(
                stats["erasure_samples"],
                score=source_slack,
                edge_id=int(row["edge_id"]),
                payload=payload,
                limit=int(slack_sample_limit),
            )
        if phase_slack > 0:
            if payload is None:
                payload = _edge_route_payload(
                    row,
                    left=left,
                    right=right,
                    result=result,
                )
            _push_largest_sample(
                stats["phase_strict_samples"],
                score=phase_slack,
                edge_id=int(row["edge_id"]),
                payload=payload,
                limit=int(slack_sample_limit),
            )

    finalized: Dict[str, Dict[str, object]] = {}
    for op, stats in by_op.items():
        finalized[op] = {
            key: value
            for key, value in stats.items()
            if key
            not in {
                "phase_slack_sum",
                "source_slack_sum",
                "phase_slack_max",
                "source_slack_max",
                "phase_slack_histogram",
                "source_slack_histogram",
                "erasure_samples",
                "phase_strict_samples",
                "validation_failure_samples",
            }
        }
        finalized[op].update(
            {
                "phase_slack_sum": fraction_payload(stats["phase_slack_sum"]),
                "source_slack_sum": fraction_payload(stats["source_slack_sum"]),
                "phase_slack_max": fraction_payload(stats["phase_slack_max"]),
                "source_slack_max": fraction_payload(stats["source_slack_max"]),
                "phase_slack_histogram": _fraction_histogram(
                    stats["phase_slack_histogram"]
                ),
                "source_slack_histogram": _fraction_histogram(
                    stats["source_slack_histogram"]
                ),
                "largest_source_slack_erasure_samples": [
                    item[2]
                    for item in sorted(
                        stats["erasure_samples"],
                        key=lambda item: (item[0], item[1]),
                        reverse=True,
                    )
                ],
                "largest_phase_strict_samples": [
                    item[2]
                    for item in sorted(
                        stats["phase_strict_samples"],
                        key=lambda item: (item[0], item[1]),
                        reverse=True,
                    )
                ],
                "validation_failure_samples": stats[
                    "validation_failure_samples"
                ],
            }
        )

    nonidentity_operand_edges = sum(
        int(stats["nonidentity_phase_operand_edge_count"])
        for stats in finalized.values()
    )
    validation_failure_counts = {
        "operation_relation": sum(
            int(stats["operation_relation_failure_count"])
            for stats in finalized.values()
        ),
        "phase_step_relation": sum(
            int(stats["phase_step_relation_failure_count"])
            for stats in finalized.values()
        ),
        "source_step_relation": sum(
            int(stats["source_step_relation_failure_count"])
            for stats in finalized.values()
        ),
        "phase_triangle": sum(
            int(stats["phase_triangle_violation_count"])
            for stats in finalized.values()
        ),
        "source_triangle": sum(
            int(stats["source_triangle_violation_count"])
            for stats in finalized.values()
        ),
    }
    validation_status = (
        "pass" if sum(validation_failure_counts.values()) == 0 else "fail"
    )
    return {
        "scope": (
            "Every recorded + and - edge through the checkpoint. The phase route "
            "is 0 -> left -> result; source absolute distance is the real-line control."
        ),
        "scanned_edge_count": int(edge_count),
        "complete_scan": True,
        "validation": {
            "status": validation_status,
            "failure_counts": validation_failure_counts,
            "operation_specific_claims_valid": validation_status == "pass",
            "malformed_operation_edges_excluded_from_slack_aggregates": True,
        },
        "by_operation": finalized,
        "nonidentity_additive_edge_aperture": {
            "nonidentity_phase_operand_edge_count": int(nonidentity_operand_edges),
            "nontrivial_phase_additive_step_status": (
                "available"
                if nonidentity_operand_edges
                else "blocked_by_strict_positive_spine_operand_rule"
            ),
            "interpretation": (
                "The current strict corpus records rational phases as result nodes "
                "but does not reuse them as operands. A positive count would establish "
                "eligible additive edge steps, not a chained runtime path or orbit. "
                "Explicit edge chaining is required before any witnessed-path claim."
            ),
        },
    }


def _claim_boundary() -> Dict[str, object]:
    return {
        "evidence_layer": "exact_external_phase_metric_over_strict_graph",
        "claim_status": "observation",
        "allowed_claim_language": [
            "The named rational nodes have this exact circular phase distance in Q/Z.",
            "Distinct source nodes at zero phase distance retain the reported edge, status, arrival, and neighborhood differences.",
            "The phase projection erases the reported portion of source absolute triangle slack on recorded additive edges.",
            "The current strict operand rule blocks nonidentity additive edge steps when the aperture reports zero eligible operands.",
        ],
        "disallowed_claim_language": [
            "Do not claim that MoO has constructed a circle, metric space, or Euclidean triangle.",
            "Do not identify zero phase distance with source-node identity or equal construction history.",
            "Do not call an external rational return orbit a runtime path.",
            "Do not infer a chained construction path from one eligible additive edge.",
            "Do not treat triangle-inequality success as an empirical discovery.",
            "Do not apply the additive phase quotient claim to ordinary rational multiplication or division.",
        ],
        "interpretation_limits": [
            "Q/Z is the exact rational finite-return subgroup, not the completed circle R/Z.",
            "The circular distance is a metric on Q/Z and only a pseudometric when pulled back to source rationals.",
            "Jaccard comparisons rank bounded graph candidates; they are not phase geometry and are not global maxima unless search completeness is exhaustive.",
            "Endpoint-sampled phase paths can alias winding and backtracking without preserved oriented lift data.",
        ],
    }


def _validate_limits(
    *,
    max_denominator: int,
    max_phase_classes: int,
    pairs_per_phase: int,
    neighborhood_sample_limit: int,
    edge_ref_limit: int,
    slack_sample_limit: int,
    full_scan: bool,
) -> None:
    del full_scan
    limits = [
        ("max_denominator", int(max_denominator), MAX_DENOMINATOR),
        ("max_phase_classes", int(max_phase_classes), MAX_PHASE_CLASSES),
        ("pairs_per_phase", int(pairs_per_phase), MAX_PAIRS_PER_PHASE),
        (
            "neighborhood_sample_limit",
            int(neighborhood_sample_limit),
            MAX_NEIGHBORHOOD_SAMPLE,
        ),
        ("edge_ref_limit", int(edge_ref_limit), MAX_EDGE_REF_LIMIT),
        ("slack_sample_limit", int(slack_sample_limit), MAX_SLACK_SAMPLE),
    ]
    invalid = [name for name, value, _ in limits if value < 1]
    if invalid:
        raise ValueError(
            "phase metric probe limits must be >= 1 (" + ", ".join(invalid) + ")"
        )
    exceeded = [f"{name}>{cap}" for name, value, cap in limits if value > cap]
    if exceeded:
        raise ValueError(
            "phase metric probe safety limit exceeded ("
            + ", ".join(exceeded)
            + "); these are unconditional hard caps"
        )


def phase_metric_probe(
    *,
    db_path: Path,
    max_denominator: int = 12,
    max_phase_classes: int = 16,
    pairs_per_phase: int = 4,
    neighborhood_sample_limit: int = 6,
    edge_ref_limit: int = 4,
    slack_sample_limit: int = 8,
    checkpoint_stage: Optional[int] = None,
    full_scan: bool = False,
) -> Dict[str, object]:
    _validate_limits(
        max_denominator=int(max_denominator),
        max_phase_classes=int(max_phase_classes),
        pairs_per_phase=int(pairs_per_phase),
        neighborhood_sample_limit=int(neighborhood_sample_limit),
        edge_ref_limit=int(edge_ref_limit),
        slack_sample_limit=int(slack_sample_limit),
        full_scan=bool(full_scan),
    )
    with closing(connect_readonly(Path(db_path))) as conn:
        alignment = require_strict_alignment(conn)
        latest_stage = _latest_stage(conn)
        checkpoint = latest_stage if checkpoint_stage is None else int(checkpoint_stage)
        if checkpoint < 1 or checkpoint > latest_stage:
            raise ValueError(
                f"checkpoint_stage must be between 1 and latest stage {latest_stage}"
            )
        corpus = _corpus_payload(
            conn,
            alignment=alignment,
            checkpoint_stage=checkpoint,
        )
        rows = _node_rows(
            conn,
            checkpoint_stage=checkpoint,
            max_denominator=int(max_denominator),
        )
        classes: Dict[Key, List[sqlite3.Row]] = defaultdict(list)
        for row in rows:
            phase = _row_phase(row)
            classes[phase_key(phase)].append(row)

        multi_lift_keys = [key for key, members in classes.items() if len(members) > 1]
        identity_key = (0, 1)
        ordered_keys = sorted(
            multi_lift_keys,
            key=lambda key: (
                0 if key == identity_key else 1,
                int(key[1]),
                int(key[0]),
            ),
        )
        selected_keys = ordered_keys[: int(max_phase_classes)]

        control_index = _control_index(rows)
        direct_input_cache: Dict[int, Set[int]] = {}
        neighborhood_cache: Dict[int, Set[int]] = {}
        edge_ref_cache: Dict[int, List[Dict[str, object]]] = {}
        phase_class_payloads: List[Dict[str, object]] = []
        all_same_phase_pairs: List[Dict[str, object]] = []
        all_control_pairs: List[Dict[str, object]] = []
        paired_same_phase_pairs: List[Dict[str, object]] = []
        control_structurally_not_applicable = 0
        control_corpus_match_missing = 0

        for key in selected_keys:
            members = classes[key]
            phase = Fraction(int(key[0]), int(key[1]))
            candidates = _candidate_pairs(
                members,
                checkpoint_stage=checkpoint,
                pair_limit=int(pairs_per_phase),
            )
            pair_payloads: List[Dict[str, object]] = []
            candidate_matches: List[
                Tuple[Dict[str, object], Dict[str, object]]
            ] = []
            graph_node_ids: Set[int] = set()
            for candidate in candidates["selected"]:
                left = candidate["left"]
                right = candidate["right"]
                match = _matched_control(
                    left,
                    right,
                    checkpoint_stage=checkpoint,
                    index=control_index,
                )
                candidate_matches.append((candidate, match))
                graph_node_ids.update(
                    {int(left["node_id"]), int(right["node_id"])}
                )
                if match["row"] is not None:
                    graph_node_ids.add(int(match["row"]["node_id"]))

            _bulk_populate_graph_caches(
                conn,
                node_ids=graph_node_ids,
                checkpoint_stage=checkpoint,
                direct_input_cache=direct_input_cache,
                neighborhood_cache=neighborhood_cache,
            )

            for candidate, match in candidate_matches:
                left = candidate["left"]
                right = candidate["right"]
                pair = _pair_payload(
                    conn,
                    left=left,
                    right=right,
                    relationship="same_phase_zero_distance",
                    reasons=[
                        "distinct source nodes collapse to one Q/Z phase",
                        *candidate["reasons"],
                    ],
                    checkpoint_stage=checkpoint,
                    latest_stage=latest_stage,
                    db_path=Path(db_path),
                    direct_input_cache=direct_input_cache,
                    neighborhood_cache=neighborhood_cache,
                    edge_ref_cache=edge_ref_cache,
                    neighborhood_sample_limit=int(neighborhood_sample_limit),
                    edge_ref_limit=int(edge_ref_limit),
                )
                if not bool(pair["phase_metric"]["zero_distance"]):
                    raise AssertionError("same-phase candidate has nonzero phase distance")
                control_row = match["row"]
                if control_row is None:
                    if match["status"] == "structurally_not_applicable":
                        control_structurally_not_applicable += 1
                    else:
                        control_corpus_match_missing += 1
                    pair["matched_different_phase_control"] = {
                        "present": False,
                        "match_status": match["status"],
                        "reason": match["reason"],
                    }
                else:
                    control = _pair_payload(
                        conn,
                        left=left,
                        right=control_row,
                        relationship="matched_different_phase_control",
                        reasons=[
                            "same left anchor",
                            "right node matched on reduced denominator and integer lift",
                            "nearest checkpoint status, first stage, and incoming exposure",
                        ],
                        checkpoint_stage=checkpoint,
                        latest_stage=latest_stage,
                        db_path=Path(db_path),
                        direct_input_cache=direct_input_cache,
                        neighborhood_cache=neighborhood_cache,
                        edge_ref_cache=edge_ref_cache,
                        neighborhood_sample_limit=int(neighborhood_sample_limit),
                        edge_ref_limit=int(edge_ref_limit),
                    )
                    same_distance = pair["graph_divergence"][
                        "shared_input_result_neighborhood"
                    ]["jaccard_distance_decimal"]
                    control_distance = control["graph_divergence"][
                        "shared_input_result_neighborhood"
                    ]["jaccard_distance_decimal"]
                    pair["matched_different_phase_control"] = {
                        "present": True,
                        "match_policy": (
                            "same left anchor; right denominator and integer lift exact; "
                            "nearest checkpoint status, stage, and incoming exposure"
                        ),
                        "match_quality": match["match_quality"],
                        "pair": control,
                        "same_minus_control_neighborhood_distance": (
                            float(same_distance) - float(control_distance)
                            if same_distance is not None and control_distance is not None
                            else None
                        ),
                    }
                    all_control_pairs.append(control)
                    paired_same_phase_pairs.append(pair)
                pair_payloads.append(pair)
                all_same_phase_pairs.append(pair)

            pair_payloads.sort(key=_pair_rank_key, reverse=True)
            for rank, pair in enumerate(pair_payloads, start=1):
                pair["within_phase_observation_rank"] = rank
            statuses = Counter(
                _checkpoint_status(row, checkpoint) for row in members
            )
            phase_class_payloads.append(
                {
                    "phase": phase_payload(phase),
                    "observed_lift_count": len(members),
                    "minimum_lift": min(_integer_lift(row) for row in members),
                    "maximum_lift": max(_integer_lift(row) for row in members),
                    "status_counts_at_checkpoint": dict(sorted(statuses.items())),
                    "pair_search": {
                        key_name: value
                        for key_name, value in candidates.items()
                        if key_name != "selected"
                    },
                    "ranking_policy": (
                        "Lexicographic observation priority: defined shared-input "
                        "neighborhood Jaccard distance descending, then minimum "
                        "neighborhood support, direct-input distance, operation total "
                        "variation, status mismatch, incoming-count gap, and stage gap."
                    ),
                    "zero_distance_graph_pairs": pair_payloads,
                    "external_return_walk": _external_return_walk(phase),
                }
            )

        reported_calibration = _metric_calibration(
            [Fraction(int(key[0]), int(key[1])) for key in selected_keys]
        )
        fixed_calibration = _metric_calibration(
            [
                Fraction(0),
                Fraction(1, 6),
                Fraction(1, 3),
                Fraction(1, 2),
                Fraction(2, 3),
                Fraction(5, 6),
            ]
        )
        calibration = {
            "status": (
                "fail"
                if "fail"
                in {
                    str(reported_calibration["status"]),
                    str(fixed_calibration["status"]),
                }
                else "pass"
            ),
            "reported_phase_scope": reported_calibration,
            "fixed_reference_scope": fixed_calibration,
            "fixed_reference_purpose": (
                "Prevents an empty or one-phase corpus aperture from being reported "
                "as a substantive calibration pass; includes wrap, antipode, tight, "
                "and strict cases."
            ),
        }
        additive_audit = _additive_triangle_audit(
            conn,
            checkpoint_stage=checkpoint,
            slack_sample_limit=int(slack_sample_limit),
            full_scan=bool(full_scan),
        )

        integer_rows = [row for row in rows if int(row["q"]) == 1]
        integer_phase_failures = sum(_row_phase(row) != 0 for row in integer_rows)
        multiplication_control = {
            "equivalent_sources": [
                fraction_payload(Fraction(1, 2)),
                fraction_payload(Fraction(3, 2)),
            ],
            "source_phase_distance": fraction_payload(
                circular_distance(Fraction(1, 2), Fraction(3, 2))
            ),
            "multiplier": fraction_payload(Fraction(1, 2)),
            "products": [
                fraction_payload(Fraction(1, 4)),
                fraction_payload(Fraction(3, 4)),
            ],
            "product_phase_distance": fraction_payload(
                circular_distance(Fraction(1, 4), Fraction(3, 4))
            ),
            "conclusion": (
                "Ordinary rational multiplication does not descend through Q/Z; "
                "it is excluded from the additive triangle audit."
            ),
        }

    same_neighborhood_distances = [
        float(value)
        for pair in all_same_phase_pairs
        for value in [
            pair["graph_divergence"]["shared_input_result_neighborhood"][
                "jaccard_distance_decimal"
            ]
        ]
        if value is not None
    ]
    control_neighborhood_distances = [
        float(value)
        for pair in all_control_pairs
        for value in [
            pair["graph_divergence"]["shared_input_result_neighborhood"][
                "jaccard_distance_decimal"
            ]
        ]
        if value is not None
    ]
    paired_same_neighborhood_distances: List[float] = []
    paired_control_neighborhood_distances: List[float] = []
    paired_neighborhood_distance_deltas: List[float] = []
    for pair in paired_same_phase_pairs:
        same_distance = pair["graph_divergence"][
            "shared_input_result_neighborhood"
        ]["jaccard_distance_decimal"]
        control_block = pair["matched_different_phase_control"]
        control_distance = control_block["pair"]["graph_divergence"][
            "shared_input_result_neighborhood"
        ]["jaccard_distance_decimal"]
        if same_distance is None or control_distance is None:
            continue
        paired_same_neighborhood_distances.append(float(same_distance))
        paired_control_neighborhood_distances.append(float(control_distance))
        paired_neighborhood_distance_deltas.append(
            float(same_distance) - float(control_distance)
        )
    globally_ranked = sorted(all_same_phase_pairs, key=_pair_rank_key, reverse=True)

    def ranked_references(
        pairs: Sequence[Dict[str, object]],
        *,
        write_global_rank: bool,
    ) -> List[Dict[str, object]]:
        references = []
        for rank, pair in enumerate(pairs, start=1):
            if write_global_rank:
                pair["global_observation_rank"] = rank
            neighborhood = pair["graph_divergence"][
                "shared_input_result_neighborhood"
            ]
            references.append(
                {
                    "rank": rank,
                    "candidate_id": pair["candidate_id"],
                    "left": pair["nodes"]["left"]["value"],
                    "right": pair["nodes"]["right"]["value"],
                    "phase": pair["phase_metric"]["left_phase"],
                    "neighborhood_jaccard_distance": neighborhood[
                        "jaccard_distance"
                    ],
                    "minimum_neighborhood_support": min(
                        int(neighborhood["left_count"]),
                        int(neighborhood["right_count"]),
                    ),
                }
            )
        return references

    ranked_refs = ranked_references(globally_ranked, write_global_rank=True)
    nonidentity_ranked = [
        pair
        for pair in globally_ranked
        if not bool(pair["phase_metric"]["left_phase"]["is_identity"])
    ]
    identity_ranked = [
        pair
        for pair in globally_ranked
        if bool(pair["phase_metric"]["left_phase"]["is_identity"])
    ]
    nonidentity_ranked_refs = ranked_references(
        nonidentity_ranked,
        write_global_rank=False,
    )
    identity_ranked_refs = ranked_references(
        identity_ranked,
        write_global_rank=False,
    )

    class_sizes = [len(members) for members in classes.values()]
    possible_same_phase_pairs = sum(size * (size - 1) // 2 for size in class_sizes)
    adjacent_same_phase_pairs = sum(max(0, size - 1) for size in class_sizes)
    return {
        "tool_name": "moo_phase_metric_probe",
        "report_type": "phase_metric_triangle_inequality_probe",
        "config": {
            "max_denominator": int(max_denominator),
            "max_phase_classes": int(max_phase_classes),
            "pairs_per_phase": int(pairs_per_phase),
            "neighborhood_sample_limit": int(neighborhood_sample_limit),
            "edge_ref_limit": int(edge_ref_limit),
            "slack_sample_limit": int(slack_sample_limit),
            "checkpoint_stage": int(corpus["checkpoint_stage"]),
            "full_scan": bool(full_scan),
        },
        "claim_boundary": _claim_boundary(),
        "metric_definition": {
            "space": "Q/Z, pulled back to observed rational source nodes",
            "phase_map": "pi(x) = x mod 1 in [0,1)",
            "distance": "d_phase(x,y) = min over n in Z of abs(x-y-n)",
            "range_turns": "[0,1/2]",
            "exact_representation": "fractions.Fraction; no trigonometric floats",
            "quotient_status": (
                "metric on Q/Z; pseudometric on source rationals because distinct "
                "integer lifts have distance zero"
            ),
            "triangle_route": "d(start,end) <= d(start,via) + d(via,end)",
            "source_control": "ordinary absolute distance abs(x-y) on Q",
            "contraction": "d_phase(x,y) <= abs(x-y)",
        },
        "graph_corpus": corpus,
        "projection_or_filter": {
            "node_scope": (
                "nodes present by checkpoint with reduced denominator at most "
                f"{int(max_denominator)}"
            ),
            "pair_scope": (
                "bounded adjacent-lift plus landmark pairs inside reported multi-lift "
                "phase fibres"
            ),
            "edge_scope": "all recorded + and - occurrences through checkpoint",
        },
        "summary": {
            "scanned_nodes": len(rows),
            "observed_phase_classes": len(classes),
            "multi_lift_phase_classes": len(multi_lift_keys),
            "reported_phase_classes": len(phase_class_payloads),
            "metric_calibration_status": calibration["status"],
            "additive_triangle_validation_status": additive_audit["validation"][
                "status"
            ],
            "maximum_observed_fibre_size": max(class_sizes) if class_sizes else 0,
            "possible_same_phase_pairs": int(possible_same_phase_pairs),
            "adjacent_same_phase_pairs": int(adjacent_same_phase_pairs),
            "exact_scored_zero_distance_pairs": len(all_same_phase_pairs),
            "exact_scored_pair_fraction_of_all_possible": (
                len(all_same_phase_pairs) / possible_same_phase_pairs
                if possible_same_phase_pairs
                else None
            ),
            "exact_scored_unique_nodes": len(direct_input_cache),
            "materialized_neighborhood_entries": sum(
                len(values) for values in neighborhood_cache.values()
            ),
            "matched_different_phase_controls": len(all_control_pairs),
            "control_structurally_not_applicable": int(
                control_structurally_not_applicable
            ),
            "control_corpus_match_missing": int(control_corpus_match_missing),
            "zero_distance_pairs_with_status_mismatch": sum(
                bool(
                    pair["graph_divergence"]["status_and_arrival"][
                        "status_mismatch"
                    ]
                )
                for pair in all_same_phase_pairs
            ),
            "same_phase_neighborhood_distance_defined_count": len(
                same_neighborhood_distances
            ),
            "same_phase_neighborhood_distance_median": (
                median(same_neighborhood_distances)
                if same_neighborhood_distances
                else None
            ),
            "matched_control_neighborhood_distance_defined_count": len(
                control_neighborhood_distances
            ),
            "matched_control_neighborhood_distance_median": (
                median(control_neighborhood_distances)
                if control_neighborhood_distances
                else None
            ),
            "paired_neighborhood_comparison_count": len(
                paired_neighborhood_distance_deltas
            ),
            "paired_same_phase_neighborhood_distance_median": (
                median(paired_same_neighborhood_distances)
                if paired_same_neighborhood_distances
                else None
            ),
            "paired_control_neighborhood_distance_median": (
                median(paired_control_neighborhood_distances)
                if paired_control_neighborhood_distances
                else None
            ),
            "paired_same_minus_control_distance_median": (
                median(paired_neighborhood_distance_deltas)
                if paired_neighborhood_distance_deltas
                else None
            ),
            "descriptive_comparison_limit": (
                "Only paired medians compare the same selected population. Pair "
                "selection remains bounded and observation-ranked, so all medians "
                "are descriptive rather than inferential or global maxima."
            ),
        },
        "metric_calibration": calibration,
        "phase_fibres": phase_class_payloads,
        "ranked_zero_distance_pair_refs": ranked_refs,
        "ranked_nonidentity_zero_distance_pair_refs": nonidentity_ranked_refs,
        "ranked_identity_control_pair_refs": identity_ranked_refs,
        "additive_triangle_audit": additive_audit,
        "controls": {
            "integer_mod_one_negative_control": {
                "integer_node_count": len(integer_rows),
                "nonidentity_phase_failure_count": int(integer_phase_failures),
                "status": "pass" if integer_phase_failures == 0 else "fail",
                "triangle_status": "vacuous_all_integer_phase_distances_are_zero",
                "interpretation": (
                    "Z/1Z is the one-class negative control, not the rational circle."
                ),
            },
            "source_absolute_metric": {
                "location": "additive_triangle_audit.by_operation",
                "purpose": (
                    "Shows real-line cancellation slack that the modulo-one phase "
                    "projection can erase."
                ),
            },
            "multiplication_non_descent": multiplication_control,
            "matched_different_phase": {
                "policy": (
                    "Same left anchor; exact target denominator and integer lift; "
                    "nearest status, first stage, and incoming exposure."
                ),
                "match_count": len(all_control_pairs),
                "structurally_not_applicable_count": int(
                    control_structurally_not_applicable
                ),
                "corpus_match_missing_count": int(control_corpus_match_missing),
                "limit": (
                    "This is a deterministic local structural control, not a "
                    "randomized or preregistered null model."
                ),
            },
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Measure exact circular phase distance on strict MoO rational nodes, "
            "return zero-distance pairs to graph evidence, and audit additive "
            "triangle slack against the source absolute-distance control."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--max-denominator", type=positive_int, default=12)
    parser.add_argument("--max-phase-classes", type=positive_int, default=16)
    parser.add_argument("--pairs-per-phase", type=positive_int, default=4)
    parser.add_argument("--neighborhood-sample-limit", type=positive_int, default=6)
    parser.add_argument("--edge-ref-limit", type=positive_int, default=4)
    parser.add_argument("--slack-sample-limit", type=positive_int, default=8)
    parser.add_argument("--checkpoint-stage", type=positive_int)
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
    payload = phase_metric_probe(
        db_path=Path(args.db),
        max_denominator=int(args.max_denominator),
        max_phase_classes=int(args.max_phase_classes),
        pairs_per_phase=int(args.pairs_per_phase),
        neighborhood_sample_limit=int(args.neighborhood_sample_limit),
        edge_ref_limit=int(args.edge_ref_limit),
        slack_sample_limit=int(args.slack_sample_limit),
        checkpoint_stage=(
            int(args.checkpoint_stage) if args.checkpoint_stage is not None else None
        ),
        full_scan=bool(args.full_scan),
    )
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_phase_metric_probe.v1",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
