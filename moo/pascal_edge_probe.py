from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
from contextlib import closing
from itertools import combinations
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from moo.graph_evidence import GraphEvidence
from moo.research_utils import (
    connect_readonly,
    emit_json,
    positive_int,
    report_metadata,
    require_strict_alignment,
)


COMMUTATIVE_OPS = {"+", "*"}


class CorpusLookup:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.evidence = GraphEvidence(conn)

    def node_id(self, value: int) -> Optional[int]:
        row = self.evidence.node_row((int(value), 1))
        return None if row is None else int(row["node_id"])

    def node_payload(self, value: int) -> Dict[str, object]:
        row = self.evidence.node_row((int(value), 1))
        if row is None:
            return {"present": False, "value": int(value)}
        complete_stage = self.evidence.corpus_stage
        visible_in_complete_corpus = (
            complete_stage is not None and int(row["first_stage"]) <= int(complete_stage)
        )
        stats = self.conn.execute(
            """
            SELECT
              COUNT(edge_id) AS derivation_events,
              SUM(CASE WHEN op = '+' THEN 1 ELSE 0 END) AS plus_count,
              SUM(CASE WHEN op = '-' THEN 1 ELSE 0 END) AS minus_count,
              SUM(CASE WHEN op = '*' THEN 1 ELSE 0 END) AS multiply_count,
              SUM(CASE WHEN op = '/' THEN 1 ELSE 0 END) AS divide_count
            FROM edges INDEXED BY idx_edges_result
            WHERE result_node_id = ?
              AND stage <= ?
            """,
            (int(row["node_id"]), int(complete_stage or 0)),
        ).fetchone()
        return {
            "present": True,
            "visible_in_complete_corpus": visible_in_complete_corpus,
            "complete_corpus_stage": complete_stage,
            "node_id": int(row["node_id"]),
            "value": int(row["p"]),
            "kind": str(row["kind"]),
            "first_stage": int(row["first_stage"]),
            "confirmed_stage": int(row["confirmed_stage"])
            if row["confirmed_stage"] is not None
            else None,
            "incoming_derivation_events": int(stats["derivation_events"]),
            "operation_signature": {
                "+": int(stats["plus_count"] or 0),
                "-": int(stats["minus_count"] or 0),
                "*": int(stats["multiply_count"] or 0),
                "/": int(stats["divide_count"] or 0),
            },
        }

    def edge_summary(
        self,
        *,
        left_value: int,
        op: str,
        right_value: int,
        result_value: int,
        allow_commuted: bool,
    ) -> Dict[str, object]:
        witness = self.evidence.edge_witness(
            left=(int(left_value), 1),
            op=str(op),
            right=(int(right_value), 1),
            result=(int(result_value), 1),
            allow_commuted=bool(allow_commuted),
        )
        return {
            "present": bool(witness["present"]),
            "count": int(witness["edge_count"]),
            "first_stage": witness["first_edge_stage"],
            "missing_nodes": list(witness["missing_nodes"]),
            "edge_refs": list(witness["edge_refs"]),
            "candidate_stage": witness["candidate_stage"],
            "eligible_by_stage": witness["eligible_by_stage"],
            "eligible_by_retention": witness["eligible_by_retention"],
            "eligible": witness["eligible"],
            "stage_aperture": witness["stage_aperture"],
            "blocker": witness["blocker"],
        }


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return None if row is None else str(row["value"])


def _json_meta(conn: sqlite3.Connection, key: str) -> Optional[object]:
    value = _meta_value(conn, key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _corpus_payload(conn: sqlite3.Connection) -> Dict[str, object]:
    latest_stage = conn.execute(
        "SELECT * FROM stages ORDER BY stage DESC LIMIT 1"
    ).fetchone()
    node_count = conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()
    edge_count = conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()
    return {
        "schema_version": _meta_value(conn, "schema_version"),
        "config": _json_meta(conn, "config_json"),
        "latest_stage": dict(latest_stage) if latest_stage is not None else None,
        "nodes": int(node_count["n"]),
        "edges": int(edge_count["n"]),
        "alignment": require_strict_alignment(conn),
    }


def _complete_corpus_stage(lookup: CorpusLookup) -> int:
    stage = lookup.evidence.complete_corpus_stage
    if stage is None:
        raise SystemExit("Pascal probe requires verified strict-stage telemetry.")
    return int(stage)


def _claim_boundary() -> Dict[str, object]:
    return {
        "evidence_layer": "strict",
        "claim_status": "lead",
        "object_language": "pascal_recurrence_lattice_and_lift_lens",
        "meaning_status": "graph_inspection_lens_only",
        "allowed_claim_language": [
            "This report checks where Pascal-style recurrence, ranked subset lattices, and cubic lift defects are witnessed by exact strict MoO nodes and edges.",
            "Complete edge hits are corpus- and aperture-conditioned, not absolute mathematical discoveries.",
            "Aperture misses are first-class data when the predicted operand stage exceeds the corpus stage.",
            "Subset-lattice rank counts are Pascal shadows only when cover edges and commuting diamonds are reported.",
            "Cubic closure is reported as exact graph visibility of a classical defect/closure lens.",
        ],
        "disallowed_claim_language": [
            "Do not claim Pascal is a confirmed MoO branch from this report alone.",
            "Do not treat value presence as graph evidence without exact edge witnesses.",
            "Do not treat strict positive-spine evidence as the full signed operator-fan field.",
            "Do not operate on speculative nodes; missing ratio or closure edges may simply require later confirmation.",
            "Do not claim new number theory from classical Pascal or Pythagorean identities.",
            "Do not count commutative reversals or different external labels on one normalized witness as independent routes.",
        ],
    }


def _expected_directed(left: int, right: int, op: str) -> int:
    if op in COMMUTATIVE_OPS and int(left) != int(right):
        return 2
    return 1


def _commutative_witness_signature(
    left: int,
    op: str,
    right: int,
    result: int,
) -> Dict[str, object]:
    inputs = [int(left), int(right)]
    if str(op) in COMMUTATIVE_OPS:
        inputs.sort()
    return {
        "op": str(op),
        "inputs": inputs,
        "result": int(result),
    }


def _edge_status(edge: Dict[str, object], expected: int) -> str:
    count = int(edge["count"])
    if count == 0:
        if edge.get("eligible_by_stage") is False:
            return "outside_complete_stage_aperture"
        if edge.get("eligible_by_retention") is False:
            return "outside_retention_aperture"
        if edge.get("eligible") is False and edge.get("blocker") is not None:
            return f"ineligible_{edge['blocker']}"
        return "absent"
    if edge.get("eligible_by_stage") is False:
        return "recorded_outside_complete_aperture"
    if edge.get("eligible_by_retention") is False:
        return "recorded_outside_retention_aperture"
    if count == int(expected):
        return "complete_directed"
    return "partial_or_unexpected"


def _carries_for_binom(n: int, k: int, prime: int) -> int:
    a = int(k)
    b = int(n) - int(k)
    carry = 0
    count = 0
    while a or b or carry:
        digit_sum = (a % prime) + (b % prime) + carry
        if digit_sum >= prime:
            count += 1
            carry = 1
        else:
            carry = 0
        a //= prime
        b //= prime
    return count


def _valuation(value: int, prime: int) -> int:
    value = abs(int(value))
    count = 0
    while value and value % int(prime) == 0:
        count += 1
        value //= int(prime)
    return count


def _parse_int_list(raw: str, *, name: str) -> List[int]:
    values: List[int] = []
    for part in str(raw).split(","):
        text = part.strip()
        if not text:
            continue
        try:
            values.append(int(text))
        except ValueError as exc:
            raise SystemExit(f"{name} values must be integers.") from exc
    if not values:
        raise SystemExit(f"At least one {name} value is required.")
    if any(value < 2 for value in values):
        raise SystemExit(f"{name} values must be primes >= 2.")
    nonprimes = [
        value
        for value in values
        if any(value % divisor == 0 for divisor in range(2, math.isqrt(value) + 1))
    ]
    if nonprimes:
        raise SystemExit(
            f"{name} values must be prime; rejected: "
            + ",".join(str(value) for value in nonprimes)
        )
    if len(set(values)) != len(values):
        raise SystemExit(f"{name} values must be distinct.")
    return values


def _coefficient_recurrence_report(
    conn: sqlite3.Connection,
    lookup: CorpusLookup,
    *,
    max_row: int,
    diagonal_depth: int,
    mod_primes: Sequence[int],
) -> Dict[str, object]:
    corpus_stage = _complete_corpus_stage(lookup)
    adjacent_rows: List[Dict[str, object]] = []
    row_summary: List[Dict[str, object]] = []
    mod_groups: Dict[str, Dict[str, Dict[str, object]]] = {
        str(prime): {} for prime in mod_primes
    }

    for n in range(2, int(max_row) + 1):
        for k in range(1, n):
            left = math.comb(n - 1, k - 1)
            right = math.comb(n - 1, k)
            result = math.comb(n, k)
            candidate_stage = max(left, right)
            expected = _expected_directed(left, right, "+")
            edge = lookup.edge_summary(
                left_value=left,
                op="+",
                right_value=right,
                result_value=result,
                allow_commuted=True,
            )
            status = _edge_status(edge, expected)
            row = {
                "n": n,
                "k": k,
                "left": left,
                "right": right,
                "result": result,
                "candidate_stage": candidate_stage,
                "eligible_by_stage": bool(edge["eligible_by_stage"]),
                "eligible_by_retention": edge["eligible_by_retention"],
                "eligible": bool(edge["eligible"]),
                "expected_directed_edges": expected,
                "exact_plus_edges": int(edge["count"]),
                "first_edge_stage": edge["first_stage"],
                "edge_status": status,
                "missing_nodes": edge["missing_nodes"],
                "blocker": edge["blocker"],
                "edge_refs": edge["edge_refs"],
            }
            adjacent_rows.append(row)
            for prime in mod_primes:
                group_key = (
                    f"v{_valuation(result, prime)}_"
                    f"carries{_carries_for_binom(n, k, prime)}"
                )
                groups = mod_groups[str(prime)]
                payload = groups.setdefault(
                    group_key,
                    {
                        "count": 0,
                        "complete": 0,
                        "eligible": 0,
                        "eligible_complete": 0,
                        "examples": [],
                    },
                )
                payload["count"] = int(payload["count"]) + 1
                payload["complete"] = int(payload["complete"]) + int(
                    status == "complete_directed"
                )
                payload["eligible"] = int(payload["eligible"]) + int(
                    bool(edge["eligible"])
                )
                payload["eligible_complete"] = int(payload["eligible_complete"]) + int(
                    bool(edge["eligible"]) and status == "complete_directed"
                )
                if len(payload["examples"]) < 4:
                    payload["examples"].append(
                        {
                            "n": n,
                            "k": k,
                            "result": result,
                            "edge_status": status,
                            "candidate_stage": candidate_stage,
                        }
                    )

    for n in range(0, int(max_row) + 1):
        rows = [row for row in adjacent_rows if int(row["n"]) == n]
        row_summary.append(
            {
                "row": n,
                "interior_positions": len(rows),
                "complete_directed": sum(
                    1 for row in rows if row["edge_status"] == "complete_directed"
                ),
                "absent": sum(1 for row in rows if row["edge_status"] == "absent"),
                "eligible_by_stage": sum(1 for row in rows if row["eligible_by_stage"]),
                "eligible": sum(1 for row in rows if row["eligible"]),
                "eligible_complete": sum(
                    1
                    for row in rows
                    if row["eligible"]
                    and row["edge_status"] == "complete_directed"
                ),
                "max_coefficient": max(math.comb(n, k) for k in range(n + 1)),
            }
        )

    for groups in mod_groups.values():
        for payload in groups.values():
            count = int(payload["count"])
            eligible = int(payload["eligible"])
            payload["complete_rate"] = (
                float(int(payload["complete"]) / count) if count else 0.0
            )
            payload["eligible_complete_rate"] = (
                float(int(payload["eligible_complete"]) / eligible)
                if eligible
                else None
            )

    diagonal_reports: List[Dict[str, object]] = []
    for depth in range(1, min(int(diagonal_depth), int(max_row)) + 1):
        addition_cases = []
        subtraction_cases = []
        for m in range(depth, int(max_row)):
            same_depth = math.comb(m, depth)
            prior_depth = math.comb(m, depth - 1)
            next_same = math.comb(m + 1, depth)
            add_edge = lookup.edge_summary(
                left_value=same_depth,
                op="+",
                right_value=prior_depth,
                result_value=next_same,
                allow_commuted=True,
            )
            add_expected = _expected_directed(same_depth, prior_depth, "+")
            addition_cases.append(
                {
                    "m": m,
                    "values": [same_depth, prior_depth, next_same],
                    "candidate_stage": max(same_depth, prior_depth),
                    "eligible_by_stage": bool(add_edge["eligible_by_stage"]),
                    "eligible_by_retention": add_edge["eligible_by_retention"],
                    "eligible": bool(add_edge["eligible"]),
                    "edge_status": _edge_status(add_edge, add_expected),
                    "edge_count": int(add_edge["count"]),
                    "first_stage": add_edge["first_stage"],
                    "blocker": add_edge["blocker"],
                }
            )
            sub_edge = lookup.edge_summary(
                left_value=next_same,
                op="-",
                right_value=same_depth,
                result_value=prior_depth,
                allow_commuted=False,
            )
            subtraction_cases.append(
                {
                    "m": m,
                    "values": [next_same, same_depth, prior_depth],
                    "candidate_stage": max(next_same, same_depth),
                    "eligible_by_stage": bool(sub_edge["eligible_by_stage"]),
                    "eligible_by_retention": sub_edge["eligible_by_retention"],
                    "eligible": bool(sub_edge["eligible"]),
                    "edge_status": _edge_status(sub_edge, 1),
                    "edge_count": int(sub_edge["count"]),
                    "first_stage": sub_edge["first_stage"],
                    "blocker": sub_edge["blocker"],
                }
            )
        diagonal_reports.append(
            {
                "depth": depth,
                "addition": _case_summary(addition_cases),
                "subtraction": _case_summary(subtraction_cases),
            }
        )

    control = _coefficient_value_control(
        conn,
        max_row=max_row,
        corpus_stage=corpus_stage,
    )
    return {
        "mode": "coefficient_recurrence",
        "max_row": int(max_row),
        "corpus_stage": corpus_stage,
        "summary": {
            "interior_positions": len(adjacent_rows),
            "complete_directed": sum(
                1 for row in adjacent_rows if row["edge_status"] == "complete_directed"
            ),
            "absent": sum(1 for row in adjacent_rows if row["edge_status"] == "absent"),
            "eligible_by_stage": sum(
                1 for row in adjacent_rows if row["eligible_by_stage"]
            ),
            "eligible": sum(1 for row in adjacent_rows if row["eligible"]),
            "eligible_complete": sum(
                1
                for row in adjacent_rows
                if row["eligible"]
                and row["edge_status"] == "complete_directed"
            ),
            "directed_plus_edge_occurrences": sum(
                int(row["exact_plus_edges"]) for row in adjacent_rows
            ),
        },
        "row_summary": row_summary,
        "first_absent_cases": [
            row for row in adjacent_rows if row["edge_status"] == "absent"
        ][:12],
        "first_unexpected_eligible_misses": [
            row
            for row in adjacent_rows
            if row["eligible"] and row["edge_status"] != "complete_directed"
        ][:12],
        "diagonal_difference_reports": diagonal_reports,
        "mod_prime_overlay": mod_groups,
        "value_control": control,
    }


def _case_summary(cases: Sequence[Dict[str, object]]) -> Dict[str, object]:
    def is_eligible(case: Dict[str, object]) -> bool:
        return bool(case.get("eligible", case["eligible_by_stage"]))

    return {
        "total": len(cases),
        "complete_directed": sum(
            1 for case in cases if case["edge_status"] == "complete_directed"
        ),
        "eligible_by_stage": sum(1 for case in cases if case["eligible_by_stage"]),
        "eligible": sum(1 for case in cases if is_eligible(case)),
        "eligible_complete": sum(
            1
            for case in cases
            if is_eligible(case) and case["edge_status"] == "complete_directed"
        ),
        "first_miss": next(
            (case for case in cases if case["edge_status"] != "complete_directed"),
            None,
        ),
        "first_unexpected_eligible_miss": next(
            (
                case
                for case in cases
                if is_eligible(case) and case["edge_status"] != "complete_directed"
            ),
            None,
        ),
        "first_hits": [
            case for case in cases if case["edge_status"] == "complete_directed"
        ][:6],
    }


def _coefficient_value_control(
    conn: sqlite3.Connection,
    *,
    max_row: int,
    corpus_stage: int,
) -> Dict[str, object]:
    values = {
        math.comb(n, k)
        for n in range(2, int(max_row) + 1)
        for k in range(1, n)
    }
    if not values:
        return {"available": False}
    max_value = max(values)
    rows = conn.execute(
        """
        WITH target(value) AS (
          SELECT CAST(value AS INTEGER)
          FROM json_each(?)
        ),
        node_metrics AS (
          SELECT
            n.node_id,
            n.p AS value,
            n.first_stage,
            CASE
              WHEN n.confirmed_stage <= ? THEN n.confirmed_stage - n.first_stage
              ELSE NULL
            END AS confirmation_lag,
            COUNT(e.edge_id) AS derivation_events,
            SUM(CASE WHEN e.op = '+' THEN 1 ELSE 0 END) AS plus_count,
            SUM(CASE WHEN e.op = '-' THEN 1 ELSE 0 END) AS minus_count,
            SUM(CASE WHEN e.op = '*' THEN 1 ELSE 0 END) AS multiply_count,
            SUM(CASE WHEN e.op = '/' THEN 1 ELSE 0 END) AS divide_count
          FROM nodes n
          LEFT JOIN edges e
            ON e.result_node_id = n.node_id
           AND e.stage <= ?
          WHERE n.q = 1
            AND n.p BETWEEN 2 AND ?
            AND n.first_stage <= ?
          GROUP BY n.node_id
        ),
        metrics AS (
          SELECT
            CASE WHEN target.value IS NULL
              THEN 'non_pascal_integer_same_range'
              ELSE 'pascal_interior_unique'
            END AS cohort,
            node_metrics.*
          FROM node_metrics
          LEFT JOIN target ON target.value = node_metrics.value
        )
        SELECT
          cohort,
          COUNT(*) AS nodes,
          AVG(derivation_events) AS avg_incoming_derivation_events,
          AVG(plus_count * 1.0 / NULLIF(derivation_events, 0)) AS avg_plus_share,
          AVG(multiply_count * 1.0 / NULLIF(derivation_events, 0)) AS avg_multiply_share,
          AVG(confirmation_lag * 1.0) AS avg_confirmation_lag,
          MIN(value) AS min_value,
          MAX(value) AS max_value
        FROM metrics
        GROUP BY cohort
        ORDER BY cohort
        """,
        (
            json.dumps(sorted(values)),
            int(corpus_stage),
            int(corpus_stage),
            int(max_value),
            int(corpus_stage),
        ),
    ).fetchall()
    return {
        "available": True,
        "control_type": "coarse_same_integer_value_range",
        "corpus_stage": int(corpus_stage),
        "interpretation_limit": (
            "This is a coarse screen only; tighter controls should match value, "
            "stage, degree, factorization, and operation exposure."
        ),
        "cohorts": [dict(row) for row in rows],
    }


def _build_additive_triangle(
    *,
    rows: int,
    left_boundary: Sequence[int],
    right_boundary: Sequence[int],
) -> List[List[int]]:
    if int(rows) < 0:
        raise ValueError("rows must be non-negative")
    if len(left_boundary) < int(rows) + 1 or len(right_boundary) < int(rows) + 1:
        raise ValueError("boundary sequences must cover every row")
    triangle: List[List[int]] = [[int(left_boundary[0])]]
    for n in range(1, int(rows) + 1):
        row = [int(left_boundary[n])]
        for k in range(1, n):
            row.append(triangle[n - 1][k - 1] + triangle[n - 1][k])
        row.append(int(right_boundary[n]))
        triangle.append(row)
    return triangle


def _additive_triangle_edge_summary(
    lookup: CorpusLookup,
    triangle: Sequence[Sequence[int]],
    *,
    corpus_stage: int,
) -> Dict[str, object]:
    cases: List[Dict[str, object]] = []
    for n in range(2, len(triangle)):
        for k in range(1, n):
            left = int(triangle[n - 1][k - 1])
            right = int(triangle[n - 1][k])
            result = int(triangle[n][k])
            candidate_stage = max(left, right)
            expected = _expected_directed(left, right, "+")
            edge = lookup.edge_summary(
                left_value=left,
                op="+",
                right_value=right,
                result_value=result,
                allow_commuted=True,
            )
            cases.append(
                {
                    "n": n,
                    "k": k,
                    "left": left,
                    "right": right,
                    "result": result,
                    "candidate_stage": candidate_stage,
                    "eligible_by_stage": bool(edge["eligible_by_stage"]),
                    "eligible_by_retention": edge["eligible_by_retention"],
                    "eligible": bool(edge["eligible"]),
                    "edge_status": _edge_status(edge, expected),
                    "edge_count": int(edge["count"]),
                    "first_stage": edge["first_stage"],
                    "blocker": edge["blocker"],
                    "edge_refs": edge["edge_refs"],
                }
            )
    eligible = [case for case in cases if bool(case["eligible"])]
    complete = [
        case for case in cases if case["edge_status"] == "complete_directed"
    ]
    eligible_complete = [
        case
        for case in eligible
        if case["edge_status"] == "complete_directed"
    ]
    return {
        "total": len(cases),
        "eligible_by_stage": sum(1 for case in cases if bool(case["eligible_by_stage"])),
        "eligible": len(eligible),
        "complete_directed": len(complete),
        "eligible_complete": len(eligible_complete),
        "max_value": max(
            (int(value) for row in triangle for value in row),
            default=None,
        ),
        "first_miss": next(
            (case for case in cases if case["edge_status"] != "complete_directed"),
            None,
        ),
        "first_unexpected_eligible_miss": next(
            (
                case
                for case in cases
                if case["eligible"]
                and case["edge_status"] != "complete_directed"
            ),
            None,
        ),
    }


def _first_primes(limit: int) -> List[int]:
    primes: List[int] = []
    for candidate in range(2, int(limit) + 1):
        root = math.isqrt(candidate)
        if all(candidate % prime for prime in primes if prime <= root):
            primes.append(candidate)
    return primes


def _lattice_cover_threshold(atoms: Sequence[int]) -> int:
    atoms = [int(atom) for atom in atoms]
    threshold = 1
    for mask in range(1 << len(atoms)):
        source = 1
        for index, atom in enumerate(atoms):
            if mask & (1 << index):
                source *= atom
        for index, atom in enumerate(atoms):
            if mask & (1 << index):
                continue
            threshold = max(threshold, source, atom)
    return threshold


def _prime_lattice_threshold_report(
    *,
    corpus_stage: int,
    prime_limit: int,
    dimensions: Sequence[int],
) -> Dict[str, object]:
    primes = _first_primes(int(prime_limit))
    by_dimension: Dict[str, object] = {}
    for dimension in dimensions:
        rows = []
        for atoms in combinations(primes, int(dimension)):
            product = math.prod(atoms)
            threshold = _lattice_cover_threshold(atoms)
            rows.append(
                {
                    "atoms": list(atoms),
                    "rank_counts": [
                        math.comb(int(dimension), rank)
                        for rank in range(int(dimension) + 1)
                    ],
                    "product": product,
                    "cover_threshold_stage": threshold,
                    "stage_eligible_by_corpus_stage": threshold <= int(corpus_stage),
                }
            )
        rows.sort(key=lambda row: (int(row["cover_threshold_stage"]), row["atoms"]))
        by_dimension[str(dimension)] = {
            "candidate_count": len(rows),
            "stage_eligible_by_corpus_stage": sum(
                1 for row in rows if bool(row["stage_eligible_by_corpus_stage"])
            ),
            "first_stage_eligible": [
                row for row in rows if bool(row["stage_eligible_by_corpus_stage"])
            ][:12],
            "first_stage_ineligible": [
                row for row in rows if not bool(row["stage_eligible_by_corpus_stage"])
            ][:12],
        }
    return {
        "control_type": "prime_subset_lattice_aperture_thresholds",
        "prime_limit": int(prime_limit),
        "corpus_stage": int(corpus_stage),
        "retention_evaluated": False,
        "graph_edges_evaluated": False,
        "interpretation": (
            "Binomial rank counts are generic for independent atom subset lattices. "
            "This control asks only which prime-atom lattice cover candidates are "
            "early enough for the strict-stage aperture. It does not claim complete "
            "visibility: corpus retention bounds and exact graph edge witnesses are "
            "not evaluated here."
        ),
        "by_dimension": by_dimension,
    }


def _null_control_report(
    conn: sqlite3.Connection,
    lookup: CorpusLookup,
    *,
    max_row: int,
    random_runs: int,
    boundary_max: int,
    seed: int,
    prime_limit: int,
) -> Dict[str, object]:
    corpus_stage = _complete_corpus_stage(lookup)
    rng = random.Random(int(seed))
    pascal = _build_additive_triangle(
        rows=int(max_row),
        left_boundary=[1] * (int(max_row) + 1),
        right_boundary=[1] * (int(max_row) + 1),
    )
    random_summaries = []
    for run in range(int(random_runs)):
        top = rng.randint(1, int(boundary_max))
        left_boundary = [top] + [
            rng.randint(1, int(boundary_max)) for _ in range(int(max_row))
        ]
        right_boundary = [top] + [
            rng.randint(1, int(boundary_max)) for _ in range(int(max_row))
        ]
        triangle = _build_additive_triangle(
            rows=int(max_row),
            left_boundary=left_boundary,
            right_boundary=right_boundary,
        )
        summary = _additive_triangle_edge_summary(
            lookup,
            triangle,
            corpus_stage=corpus_stage,
        )
        summary["run"] = run
        summary["top"] = top
        random_summaries.append(summary)
    return {
        "mode": "null_controls",
        "corpus_stage": corpus_stage,
        "additive_edge_control": {
            "control_type": "random_positive_additive_triangles",
            "interpretation": (
                "If random triangles generated by child=left+right have the "
                "same eligible plus-edge completion as Pascal, then local "
                "Pascal recurrence edges are not a specific MoO signal."
            ),
            "pascal_all_one_boundary": _additive_triangle_edge_summary(
                lookup,
                pascal,
                corpus_stage=corpus_stage,
            ),
            "random_runs": int(random_runs),
            "boundary_max": int(boundary_max),
            "seed": int(seed),
            "all_random_eligible_complete": all(
                summary["eligible"] == summary["eligible_complete"]
                for summary in random_summaries
            ),
            "samples": random_summaries[:12],
        },
        "prime_lattice_thresholds": _prime_lattice_threshold_report(
            corpus_stage=corpus_stage,
            prime_limit=int(prime_limit),
            dimensions=(4, 5),
        ),
    }


def _subset_lattice_report(
    lookup: CorpusLookup,
    *,
    primes: Sequence[int],
) -> Dict[str, object]:
    primes = [int(prime) for prime in primes]
    subset_rows = []
    for mask in range(1 << len(primes)):
        product = 1
        members: List[int] = []
        for index, prime in enumerate(primes):
            if mask & (1 << index):
                product *= prime
                members.append(prime)
        node = lookup.node_payload(product)
        subset_rows.append(
            {
                "mask": mask,
                "rank": len(members),
                "members": members,
                "product": product,
                "node": node,
            }
        )

    covers = []
    for row in subset_rows:
        mask = int(row["mask"])
        for index, prime in enumerate(primes):
            if mask & (1 << index):
                continue
            source = int(row["product"])
            target = source * prime
            expected = _expected_directed(source, prime, "*")
            edge = lookup.edge_summary(
                left_value=source,
                op="*",
                right_value=prime,
                result_value=target,
                allow_commuted=True,
            )
            covers.append(
                {
                    "from": source,
                    "prime": prime,
                    "to": target,
                    "from_rank": int(row["rank"]),
                    "expected_directed_edges": expected,
                    "edge_count": int(edge["count"]),
                    "first_stage": edge["first_stage"],
                    "edge_status": _edge_status(edge, expected),
                    "candidate_stage": edge["candidate_stage"],
                    "eligible_by_stage": edge["eligible_by_stage"],
                    "eligible_by_retention": edge["eligible_by_retention"],
                    "eligible": edge["eligible"],
                    "blocker": edge["blocker"],
                    "edge_refs": edge["edge_refs"],
                }
            )

    diamonds = []
    for row in subset_rows:
        mask = int(row["mask"])
        missing = [
            index for index, _prime in enumerate(primes) if not (mask & (1 << index))
        ]
        for first, second in combinations(missing, 2):
            base = int(row["product"])
            p = primes[first]
            q = primes[second]
            edges = [
                lookup.edge_summary(
                    left_value=base,
                    op="*",
                    right_value=p,
                    result_value=base * p,
                    allow_commuted=True,
                ),
                lookup.edge_summary(
                    left_value=base,
                    op="*",
                    right_value=q,
                    result_value=base * q,
                    allow_commuted=True,
                ),
                lookup.edge_summary(
                    left_value=base * p,
                    op="*",
                    right_value=q,
                    result_value=base * p * q,
                    allow_commuted=True,
                ),
                lookup.edge_summary(
                    left_value=base * q,
                    op="*",
                    right_value=p,
                    result_value=base * p * q,
                    allow_commuted=True,
                ),
            ]
            statuses = [
                _edge_status(edge, _expected_directed(1, 2, "*"))
                for edge in edges
            ]
            diamonds.append(
                {
                    "base": base,
                    "added_primes": [p, q],
                    "top": base * p * q,
                    "present": all(edge["present"] for edge in edges),
                    "complete": all(status == "complete_directed" for status in statuses),
                    "eligible": all(bool(edge["eligible"]) for edge in edges),
                    "edge_statuses": statuses,
                    "candidate_stages": [edge["candidate_stage"] for edge in edges],
                    "blockers": [edge["blocker"] for edge in edges],
                    "edge_refs": [edge["edge_refs"] for edge in edges],
                }
            )

    rank_summary = []
    for rank in range(len(primes) + 1):
        rank_nodes = [row for row in subset_rows if int(row["rank"]) == rank]
        rank_covers = [row for row in covers if int(row["from_rank"]) == rank]
        rank_summary.append(
            {
                "rank": rank,
                "expected_pascal_count": math.comb(len(primes), rank),
                "nodes": len(rank_nodes),
                "nodes_present": sum(1 for row in rank_nodes if row["node"]["present"]),
                "nodes_visible_in_complete_corpus": sum(
                    1
                    for row in rank_nodes
                    if row["node"].get("visible_in_complete_corpus", False)
                ),
                "cover_relations": len(rank_covers),
                "complete_covers": sum(
                    1
                    for row in rank_covers
                    if row["edge_status"] == "complete_directed"
                ),
                "directed_cover_edge_occurrences": sum(
                    int(row["edge_count"]) for row in rank_covers
                ),
            }
        )

    return {
        "mode": "subset_lattice",
        "primes": primes,
        "rank_summary": rank_summary,
        "summary": {
            "subset_nodes": len(subset_rows),
            "subset_nodes_present": sum(
                1 for row in subset_rows if row["node"]["present"]
            ),
            "subset_nodes_visible_in_complete_corpus": sum(
                1
                for row in subset_rows
                if row["node"].get("visible_in_complete_corpus", False)
            ),
            "cover_relations": len(covers),
            "complete_covers": sum(
                1 for row in covers if row["edge_status"] == "complete_directed"
            ),
            "directed_cover_edge_occurrences": sum(
                int(row["edge_count"]) for row in covers
            ),
            "diamonds": len(diamonds),
            "complete_diamonds": sum(1 for row in diamonds if row["complete"]),
        },
        "first_cover_misses": [
            row for row in covers if row["edge_status"] != "complete_directed"
        ][:12],
        "first_diamond_misses": [row for row in diamonds if not row["complete"]][:12],
    }


def _right_triangle_cubic_report(
    lookup: CorpusLookup,
    *,
    max_scale: int,
    primitive_hypotenuse_limit: int,
) -> Dict[str, object]:
    scale_rows = []
    for scale in range(1, int(max_scale) + 1):
        a = 3 * scale
        b = 4 * scale
        c = 5 * scale
        semiperimeter = 6 * scale
        inradius = scale
        perimeter = 12 * scale
        area = 6 * scale * scale
        surface = 216 * scale * scale
        volume = 216 * scale * scale * scale
        relations = {
            "pythagorean_square_sum": (a * a, "+", b * b, c * c, True),
            "area_half": (a * b, "/", 2, area, False),
            "semiperimeter": (perimeter, "/", 2, semiperimeter, False),
            "surface_6s2": (6, "*", semiperimeter * semiperimeter, surface, True),
            "volume_s3": (
                semiperimeter * semiperimeter,
                "*",
                semiperimeter,
                volume,
                True,
            ),
            "side_cube_sum_ab": (a**3, "+", b**3, a**3 + b**3, True),
            "side_cube_sum_abc": (a**3 + b**3, "+", c**3, volume, True),
            "volume_over_surface": (volume, "/", surface, inradius, False),
        }
        witness_rows = {}
        for name, (left, op, right, result, commuted) in relations.items():
            edge = lookup.edge_summary(
                left_value=left,
                op=op,
                right_value=right,
                result_value=result,
                allow_commuted=bool(commuted),
            )
            expected = _expected_directed(left, right, op) if commuted else 1
            normalized_signature = _commutative_witness_signature(
                left,
                op,
                right,
                result,
            )
            witness_rows[name] = {
                "relation": f"{left} {op} {right} -> {result}",
                "commutative_normalized_signature": normalized_signature,
                "candidate_stage": max(left, right),
                "expected_directed_edges": expected,
                "edge_count": int(edge["count"]),
                "first_stage": edge["first_stage"],
                "edge_status": _edge_status(edge, expected),
                "edge_refs": edge["edge_refs"],
                "missing_nodes": edge["missing_nodes"],
                "eligible_by_stage": edge["eligible_by_stage"],
                "eligible_by_retention": edge["eligible_by_retention"],
                "eligible": edge["eligible"],
                "blocker": edge["blocker"],
            }
        surface_signature = witness_rows["surface_6s2"][
            "commutative_normalized_signature"
        ]
        volume_signature = witness_rows["volume_s3"][
            "commutative_normalized_signature"
        ]
        surface_volume_alias = surface_signature == volume_signature
        alias_index: Dict[Tuple[str, Tuple[int, ...], int], List[str]] = {}
        for witness_name, witness in witness_rows.items():
            signature = witness["commutative_normalized_signature"]
            signature_key = (
                str(signature["op"]),
                tuple(int(value) for value in signature["inputs"]),
                int(signature["result"]),
            )
            alias_index.setdefault(signature_key, []).append(witness_name)
        named_alias_groups = []
        for (op, inputs, result), names in sorted(alias_index.items()):
            if len(names) < 2:
                continue
            shared_refs: Optional[set[int]] = None
            for name in names:
                refs = {int(ref["edge_id"]) for ref in witness_rows[name]["edge_refs"]}
                shared_refs = refs if shared_refs is None else shared_refs & refs
            named_alias_groups.append(
                {
                    "named_witnesses": sorted(names),
                    "commutative_normalized_signature": {
                        "op": op,
                        "inputs": list(inputs),
                        "result": result,
                    },
                    "shared_edge_refs": sorted(shared_refs or set()),
                    "assessment": "external_role_alias_on_one_normalized_witness",
                }
            )
        scale_rows.append(
            {
                "scale": scale,
                "a_b_c_s_r": [a, b, c, semiperimeter, inradius],
                "perimeter": perimeter,
                "area": area,
                "cube_surface": surface,
                "cube_volume": volume,
                "surface_node": lookup.node_payload(surface),
                "volume_node": lookup.node_payload(volume),
                "witnesses": witness_rows,
                "route_identity": {
                    "quotient": "sort operands for + and *; preserve - and / order",
                    "surface_volume_same_commutative_terminal_witness": surface_volume_alias,
                    "surface_volume_edge_ref_overlap": sorted(
                        {
                            int(ref["edge_id"])
                            for ref in witness_rows["surface_6s2"]["edge_refs"]
                        }
                        & {
                            int(ref["edge_id"])
                            for ref in witness_rows["volume_s3"]["edge_refs"]
                        }
                    ),
                    "assessment": (
                        "projection_alias_not_independent_routes"
                        if surface_volume_alias
                        else "different_terminal_results_or_witnesses"
                    ),
                    "named_witness_alias_groups": named_alias_groups,
                },
            }
        )

    primitive_controls = _primitive_right_triangle_controls(
        int(primitive_hypotenuse_limit)
    )
    return {
        "mode": "right_triangle_cubic_lift",
        "max_scale": int(max_scale),
        "primitive_hypotenuse_limit": int(primitive_hypotenuse_limit),
        "scale_branch": scale_rows,
        "primitive_defect_controls": primitive_controls,
        "defect_formula": "Delta_3 = s^3 - (a^3+b^3+c^3) = s^2(5r-c)",
        "route_identity_rule": (
            "Named geometric roles do not create separate MoO routes when their "
            "commutative-normalized edge certificates are identical."
        ),
        "closure_reading": (
            "Zero defect is graph-relevant only when the required square, cube, "
            "addition, multiplication, and ratio witnesses are visible under the "
            "strict positive-spine operand rule."
        ),
    }


def _primitive_right_triangle_controls(limit: int) -> Dict[str, object]:
    triples = []
    for a in range(1, int(limit) + 1):
        for b in range(a + 1, int(limit) + 1):
            c2 = a * a + b * b
            c = math.isqrt(c2)
            if c * c != c2 or c > int(limit):
                continue
            common = math.gcd(math.gcd(a, b), c)
            semiperimeter_num = a + b + c
            area_num = a * b
            # For right triangles, r = A/s = ab/(a+b+c).
            r_num = area_num
            r_den = semiperimeter_num
            delta_num = semiperimeter_num**3 - 8 * (a**3 + b**3 + c**3)
            zero_defect = delta_num == 0
            triples.append(
                {
                    "a": a,
                    "b": b,
                    "c": c,
                    "primitive": common == 1,
                    "semiperimeter": semiperimeter_num / 2,
                    "inradius": r_num / r_den,
                    "c_over_r": c * r_den / r_num,
                    "delta3_times_8": delta_num,
                    "zero_defect": zero_defect,
                    "square_sum_candidate_stage": max(a * a, b * b),
                    "cube_sum_candidate_stage": max(a**3 + b**3, c**3),
                }
            )
    primitive = [row for row in triples if row["primitive"]]
    nearest = sorted(
        primitive,
        key=lambda row: (
            abs(float(row["delta3_times_8"])) / max(1.0, row["semiperimeter"] ** 3),
            row["c"],
        ),
    )[:12]
    return {
        "primitive_count": len(primitive),
        "zero_defect_all_scales": [
            row for row in triples if row["zero_defect"]
        ][:12],
        "zero_defect_primitive": [
            row for row in primitive if row["zero_defect"]
        ][:12],
        "nearest_primitive_by_relative_defect": nearest,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe Pascal-style edge/lattice/lift structure in a strict MoO graph corpus."
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=("all", "coefficient", "subset", "cubic", "controls"),
        default="all",
    )
    parser.add_argument("--max-row", type=positive_int, default=30)
    parser.add_argument("--diagonal-depth", type=positive_int, default=6)
    parser.add_argument("--mod-primes", default="2,3,5")
    parser.add_argument("--subset-primes", default="2,3,5,7")
    parser.add_argument("--max-scale", type=positive_int, default=4)
    parser.add_argument("--primitive-hypotenuse-limit", type=positive_int, default=100)
    parser.add_argument("--control-runs", type=positive_int, default=20)
    parser.add_argument("--control-row", type=positive_int, default=15)
    parser.add_argument("--control-boundary-max", type=positive_int, default=50)
    parser.add_argument("--control-seed", type=int, default=1729)
    parser.add_argument("--prime-threshold-limit", type=positive_int, default=31)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--write", type=Path)
    parser.add_argument("--include-checksums", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    mod_primes = _parse_int_list(args.mod_primes, name="mod-prime")
    subset_primes = _parse_int_list(args.subset_primes, name="subset-prime")
    with closing(connect_readonly(Path(args.db))) as conn:
        lookup = CorpusLookup(conn)
        reports: Dict[str, object] = {}
        if args.mode in {"all", "coefficient"}:
            reports["coefficient_recurrence"] = _coefficient_recurrence_report(
                conn,
                lookup,
                max_row=int(args.max_row),
                diagonal_depth=int(args.diagonal_depth),
                mod_primes=mod_primes,
            )
        if args.mode in {"all", "subset"}:
            reports["subset_lattice"] = _subset_lattice_report(
                lookup,
                primes=subset_primes,
            )
        if args.mode in {"all", "cubic"}:
            reports["right_triangle_cubic_lift"] = _right_triangle_cubic_report(
                lookup,
                max_scale=int(args.max_scale),
                primitive_hypotenuse_limit=int(args.primitive_hypotenuse_limit),
            )
        if args.mode in {"all", "controls"}:
            reports["null_controls"] = _null_control_report(
                conn,
                lookup,
                max_row=int(args.control_row),
                random_runs=int(args.control_runs),
                boundary_max=int(args.control_boundary_max),
                seed=int(args.control_seed),
                prime_limit=int(args.prime_threshold_limit),
            )
        payload = {
            "metadata": report_metadata(
                tool_path=Path(__file__),
                db_path=Path(args.db),
                argv=argv,
                schema_version="pascal_edge_probe.v3",
                include_checksums=bool(args.include_checksums),
            ),
            "claim_boundary": _claim_boundary(),
            "corpus": _corpus_payload(conn),
            "reports": reports,
        }
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
