from __future__ import annotations

import argparse
import json
import math
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from moo.research_utils import (
    connect_readonly,
    emit_json,
    positive_int,
    report_metadata,
    require_strict_alignment,
)


SCHEMA_VERSION = "moo-congruence-quotient-probe-v1"
DEFAULT_MODULI = (1, 2, 3, 4, 5, 6, 8, 12)
DEFAULT_CHECKPOINTS = (1, 2, 3, 5, 10, 20, 40, 80, 160, 300)
OPS = ("seed", "+", "-", "*", "/")
Signature = Tuple[str, Optional[int], Optional[int], int]


def parse_positive_csv(raw: str, *, field_name: str) -> List[int]:
    values: List[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            value = int(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(
                f"{field_name} must be a comma-separated list of integers"
            ) from exc
        if value < 1:
            raise argparse.ArgumentTypeError(f"{field_name} entries must be >= 1")
        values.append(value)
    if not values:
        raise argparse.ArgumentTypeError(f"{field_name} must not be empty")
    return sorted(set(values))


def least_residue(value: int, modulus: int) -> int:
    if modulus < 1:
        raise ValueError("modulus must be >= 1")
    return int(value) % int(modulus)


def gauss_totient(modulus: int) -> int:
    """Gauss Art. 39 endpoint convention: 1 <= a <= m and gcd(a, m) = 1."""
    if modulus < 1:
        raise ValueError("modulus must be >= 1")
    return sum(1 for value in range(1, modulus + 1) if math.gcd(value, modulus) == 1)


def _strict_below_totient(modulus: int) -> int:
    return sum(1 for value in range(1, modulus) if math.gcd(value, modulus) == 1)


def _divisors(value: int) -> List[int]:
    small: List[int] = []
    large: List[int] = []
    for divisor in range(1, math.isqrt(value) + 1):
        if value % divisor != 0:
            continue
        small.append(divisor)
        paired = value // divisor
        if paired != divisor:
            large.append(paired)
    return small + list(reversed(large))


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row is not None else None


def _json_meta(conn: sqlite3.Connection, key: str) -> Optional[object]:
    raw = _meta_value(conn, key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _corpus_payload(
    conn: sqlite3.Connection, alignment: Mapping[str, object]
) -> Dict[str, object]:
    latest = conn.execute(
        "SELECT * FROM stages ORDER BY stage DESC LIMIT 1"
    ).fetchone()
    return {
        "schema_version": _meta_value(conn, "schema_version"),
        "config": _json_meta(conn, "config_json"),
        "latest_stage": dict(latest) if latest is not None else None,
        "nodes": int(conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()["n"]),
        "edges": int(conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()["n"]),
        "alignment": dict(alignment),
    }


def _checkpoint_status(row: Mapping[str, object], checkpoint: int) -> str:
    p = int(row["p"])
    confirmed_stage = row["confirmed_stage"]
    if p == 1:
        return "certainty"
    if p <= 0:
        return "relational_nonpositive"
    if confirmed_stage is not None and int(confirmed_stage) <= checkpoint:
        return "confirmed_positive_spine"
    return "speculative_positive_after_checkpoint"


def _event_status(row: Mapping[str, object]) -> str:
    p = int(row["result_p"])
    confirmed_stage = row["result_confirmed_stage"]
    stage = int(row["stage"])
    if p == 1:
        return "certainty_at_event"
    if p <= 0:
        return "relational_nonpositive_at_event"
    if confirmed_stage is not None and int(confirmed_stage) <= stage:
        return "confirmed_at_event"
    return "speculative_positive_at_event"


def _node_record(row: Mapping[str, object], checkpoint: int) -> Dict[str, object]:
    return {
        "node_id": int(row["node_id"]),
        "value": str(row["label"]),
        "p": int(row["p"]),
        "q": int(row["q"]),
        "kind": str(row["kind"]),
        "first_stage": int(row["first_stage"]),
        "confirmed_stage": (
            int(row["confirmed_stage"])
            if row["confirmed_stage"] is not None
            else None
        ),
        "derivation_events_through_checkpoint": int(row["derivation_events"]),
        "status_at_checkpoint": _checkpoint_status(row, checkpoint),
    }


def _edge_value(row: Mapping[str, object], side: str) -> Optional[Dict[str, object]]:
    node_id = row[f"{side}_node_id"]
    if node_id is None:
        return None
    return {
        "node_id": int(node_id),
        "value": str(row[f"{side}_label"]),
        "p": int(row[f"{side}_p"]),
        "q": int(row[f"{side}_q"]),
    }


def _edge_record(
    row: Mapping[str, object], modulus: int, checkpoint: int
) -> Dict[str, object]:
    left = _edge_value(row, "left")
    right = _edge_value(row, "right")
    result = _edge_value(row, "result")
    assert result is not None
    return {
        "edge_id": int(row["edge_id"]),
        "stage": int(row["stage"]),
        "op": str(row["op"]),
        "left": left,
        "right": right,
        "result": result,
        "projected": {
            "left_residue": least_residue(int(left["p"]), modulus) if left else None,
            "right_residue": least_residue(int(right["p"]), modulus) if right else None,
            "result_residue": least_residue(int(result["p"]), modulus),
        },
        "result_status_at_event": _event_status(row),
        "result_status_at_checkpoint": _checkpoint_status(
            {
                "p": row["result_p"],
                "confirmed_stage": row["result_confirmed_stage"],
            },
            checkpoint,
        ),
    }


def _load_integer_nodes(conn: sqlite3.Connection, checkpoint: int) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          n.node_id, n.p, n.q, n.label, n.kind, n.first_stage,
          n.confirmed_stage, COUNT(e.edge_id) AS derivation_events
        FROM nodes n
        LEFT JOIN edges e
          ON e.result_node_id = n.node_id AND e.stage <= ?
        WHERE n.q = 1 AND n.first_stage <= ?
        GROUP BY
          n.node_id, n.p, n.q, n.label, n.kind, n.first_stage,
          n.confirmed_stage
        ORDER BY n.first_stage, n.node_id
        """,
        (checkpoint, checkpoint),
    ).fetchall()


def _load_integer_result_edges(
    conn: sqlite3.Connection, checkpoint: int
) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
          e.edge_id, e.stage, e.op,
          l.node_id AS left_node_id, l.p AS left_p, l.q AS left_q,
          l.label AS left_label,
          r.node_id AS right_node_id, r.p AS right_p, r.q AS right_q,
          r.label AS right_label,
          o.node_id AS result_node_id, o.p AS result_p, o.q AS result_q,
          o.label AS result_label, o.first_stage AS result_first_stage,
          o.confirmed_stage AS result_confirmed_stage
        FROM edges e
        LEFT JOIN nodes l ON l.node_id = e.left_node_id
        LEFT JOIN nodes r ON r.node_id = e.right_node_id
        JOIN nodes o ON o.node_id = e.result_node_id
        WHERE e.stage <= ? AND o.q = 1
        ORDER BY e.stage, e.edge_id
        """,
        (checkpoint,),
    ).fetchall()


def _excluded_rational_edges(
    conn: sqlite3.Connection, checkpoint: int
) -> Dict[str, object]:
    rows = conn.execute(
        """
        SELECT e.op, COUNT(*) AS n
        FROM edges e
        JOIN nodes o ON o.node_id = e.result_node_id
        WHERE e.stage <= ? AND o.q != 1
        GROUP BY e.op
        ORDER BY e.op
        """,
        (checkpoint,),
    ).fetchall()
    by_op = {str(row["op"]): int(row["n"]) for row in rows}
    return {
        "count": sum(by_op.values()),
        "by_operation": by_op,
        "reason": (
            "Gauss's congruence definition is restricted to integers; rational "
            "results remain in the source graph but are outside this projection."
        ),
    }


def _domain_rows(
    nodes: Sequence[sqlite3.Row],
    edges: Sequence[sqlite3.Row],
    checkpoint: int,
) -> Dict[str, Tuple[List[sqlite3.Row], List[sqlite3.Row]]]:
    all_nodes = list(nodes)
    all_edges = list(edges)
    confirmed_nodes = [
        row
        for row in nodes
        if int(row["p"]) >= 1
        and row["confirmed_stage"] is not None
        and int(row["confirmed_stage"]) <= checkpoint
    ]
    confirmed_ids = {int(row["node_id"]) for row in confirmed_nodes}
    confirmed_edges = [
        row
        for row in edges
        if int(row["result_node_id"]) in confirmed_ids
    ]
    return {
        "all_integer_shadow": (all_nodes, all_edges),
        "confirmed_positive_spine": (confirmed_nodes, confirmed_edges),
    }


def _operation_counter(edges: Iterable[Mapping[str, object]]) -> Dict[str, int]:
    counts = Counter(str(row["op"]) for row in edges)
    return {op: int(counts[op]) for op in OPS if counts[op]}


def _source_domain_summary(
    nodes: Sequence[sqlite3.Row],
    edges: Sequence[sqlite3.Row],
    checkpoint: int,
) -> Dict[str, object]:
    node_statuses = Counter(_checkpoint_status(row, checkpoint) for row in nodes)
    event_statuses: Dict[str, Counter[str]] = defaultdict(Counter)
    for row in edges:
        event_statuses[str(row["op"])][_event_status(row)] += 1
    return {
        "node_count": len(nodes),
        "node_status_at_checkpoint": dict(sorted(node_statuses.items())),
        "edge_occurrence_count": len(edges),
        "edge_occurrences_by_operation": _operation_counter(edges),
        "result_status_at_event_by_operation": {
            op: dict(sorted(counts.items()))
            for op, counts in sorted(event_statuses.items())
        },
    }


def _divisor_summatory(checkpoint: int) -> int:
    return sum(checkpoint // value for value in range(1, checkpoint + 1))


def _completeness_payload(
    domain_name: str,
    edges: Sequence[sqlite3.Row],
    checkpoint: int,
) -> Dict[str, object]:
    observed = Counter(
        str(row["op"]) for row in edges if str(row["op"]) != "seed"
    )
    divisor_sum = _divisor_summatory(checkpoint)
    if domain_name == "all_integer_shadow":
        expected = {
            "+": checkpoint * checkpoint,
            "-": checkpoint * checkpoint,
            "*": checkpoint * checkpoint,
            "/": divisor_sum,
        }
        expectation = (
            "Broad-bound expectation for every directed positive-spine operand "
            "pair through U whose result is an integer."
        )
    elif domain_name == "confirmed_positive_spine":
        triangle = checkpoint * (checkpoint - 1) // 2
        expected = {"+": triangle, "-": triangle, "*": divisor_sum, "/": divisor_sum}
        expectation = (
            "Induced positive-spine expectation for results in 1..U; seed is "
            "reported separately."
        )
    else:
        raise ValueError(f"unknown domain: {domain_name}")
    checks = {
        op: {
            "expected": int(expected[op]),
            "observed": int(observed[op]),
            "complete": int(observed[op]) == int(expected[op]),
        }
        for op in ("+", "-", "*", "/")
    }
    return {
        "expectation": expectation,
        "seed_occurrences": sum(1 for row in edges if str(row["op"]) == "seed"),
        "operation_checks": checks,
        "status": "pass" if all(check["complete"] for check in checks.values()) else "bounded",
        "bounded_reading": (
            "A bounded result means the source corpus aperture removed some integer "
            "results; it does not invalidate the retained edge evidence."
        ),
    }


def _edge_signature(row: Mapping[str, object], modulus: int) -> Signature:
    op = str(row["op"])
    result = least_residue(int(row["result_p"]), modulus)
    if op == "seed":
        return op, None, None, result
    return (
        op,
        least_residue(int(row["left_p"]), modulus),
        least_residue(int(row["right_p"]), modulus),
        result,
    )


def _signature_record(signature: Signature, count: int) -> Dict[str, object]:
    op, left, right, result = signature
    return {
        "op": op,
        "left_residue": left,
        "right_residue": right,
        "result_residue": result,
        "edge_occurrences": int(count),
    }


def _edge_relation_holds(row: Mapping[str, object], modulus: int) -> bool:
    op = str(row["op"])
    if op == "seed":
        return True
    left = int(row["left_p"])
    right = int(row["right_p"])
    result = int(row["result_p"])
    if op == "+":
        difference = left + right - result
    elif op == "-":
        difference = left - right - result
    elif op == "*":
        difference = left * right - result
    elif op == "/":
        # Division is recorded as the exact integer relation right * result = left.
        difference = right * result - left
    else:
        return False
    return difference % modulus == 0


def quotient_projection(
    nodes: Sequence[sqlite3.Row],
    edges: Sequence[sqlite3.Row],
    *,
    modulus: int,
    checkpoint: int,
    sample_limit: int,
) -> Dict[str, object]:
    fibers: Dict[int, List[sqlite3.Row]] = defaultdict(list)
    for row in nodes:
        fibers[least_residue(int(row["p"]), modulus)].append(row)

    fiber_records: List[Dict[str, object]] = []
    for residue in range(modulus):
        rows = fibers.get(residue, [])
        statuses = Counter(_checkpoint_status(row, checkpoint) for row in rows)
        fiber_records.append(
            {
                "residue": residue,
                "source_node_count": len(rows),
                "status_at_checkpoint": dict(sorted(statuses.items())),
                "node_samples": [
                    _node_record(row, checkpoint) for row in rows[:sample_limit]
                ],
            }
        )

    signatures = Counter(_edge_signature(row, modulus) for row in edges)
    top_signatures = sorted(
        signatures.items(), key=lambda item: (-item[1], repr(item[0]))
    )[:sample_limit]
    edge_samples_by_op: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    validation_failure_count = 0
    validation_failures: List[Dict[str, object]] = []
    for row in edges:
        op = str(row["op"])
        if len(edge_samples_by_op[op]) < sample_limit:
            edge_samples_by_op[op].append(_edge_record(row, modulus, checkpoint))
        if not _edge_relation_holds(row, modulus):
            validation_failure_count += 1
            if len(validation_failures) < sample_limit:
                validation_failures.append(_edge_record(row, modulus, checkpoint))

    nonseed_topology = {
        (
            signature[1],
            signature[2],
            signature[3],
        )
        for signature in signatures
        if signature[0] != "seed"
    }
    occupied = sum(1 for rows in fibers.values() if rows)
    nonseed_decorated = {signature for signature in signatures if signature[0] != "seed"}
    return {
        "modulus": modulus,
        "source_node_count": len(nodes),
        "theoretical_residue_count": modulus,
        "occupied_residue_count": occupied,
        "empty_residue_count": modulus - occupied,
        "node_collapse_count": len(nodes) - occupied,
        "node_compression_ratio": (occupied / len(nodes)) if nodes else None,
        "residue_fibers": fiber_records,
        "edge_occurrence_count": len(edges),
        "edge_occurrences_by_operation": _operation_counter(edges),
        "edge_occurrences_retained_after_projection": len(edges),
        "distinct_operation_decorated_signatures": len(signatures),
        "distinct_nonseed_operation_decorated_signatures": len(nonseed_decorated),
        "distinct_unlabeled_nonseed_topologies": len(nonseed_topology),
        "top_operation_decorated_signatures": [
            _signature_record(signature, count)
            for signature, count in top_signatures
        ],
        "edge_samples_by_operation": dict(edge_samples_by_op),
        "algebra_validation": {
            "checked_edge_occurrences": len(edges),
            "failure_count": validation_failure_count,
            "failure_samples": validation_failures,
            "division_rule": (
                "For exact integer division a/b=c, validate b*c congruent to a; "
                "division is not treated as a general quotient-ring operation."
            ),
        },
    }


def _compact_projection(payload: Mapping[str, object]) -> Dict[str, object]:
    return {
        key: payload[key]
        for key in (
            "modulus",
            "source_node_count",
            "occupied_residue_count",
            "node_collapse_count",
            "edge_occurrence_count",
            "edge_occurrences_by_operation",
            "distinct_operation_decorated_signatures",
            "distinct_nonseed_operation_decorated_signatures",
            "distinct_unlabeled_nonseed_topologies",
        )
    }


def _refinement_checks(
    nodes: Sequence[sqlite3.Row], moduli: Sequence[int]
) -> List[Dict[str, object]]:
    checks: List[Dict[str, object]] = []
    for coarse in moduli:
        for fine in moduli:
            if coarse == fine or fine % coarse != 0:
                continue
            failures = [
                int(row["node_id"])
                for row in nodes
                if least_residue(least_residue(int(row["p"]), fine), coarse)
                != least_residue(int(row["p"]), coarse)
            ]
            checks.append(
                {
                    "coarse_modulus": coarse,
                    "fine_modulus": fine,
                    "fine_refines_coarse": not failures,
                    "checked_source_nodes": len(nodes),
                    "failure_count": len(failures),
                    "failure_node_ids": failures[:4],
                }
            )
    return checks


def _crt_modulus_one_checks(
    nodes: Sequence[sqlite3.Row], moduli: Sequence[int]
) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    for modulus in moduli:
        if modulus == 1:
            continue
        residues = {least_residue(int(row["p"]), modulus) for row in nodes}
        paired = {
            (
                least_residue(int(row["p"]), 1),
                least_residue(int(row["p"]), modulus),
            )
            for row in nodes
        }
        records.append(
            {
                "other_modulus": modulus,
                "lcm_with_one": math.lcm(1, modulus),
                "observed_classes_without_mod_1_coordinate": len(residues),
                "observed_classes_with_mod_1_coordinate": len(paired),
                "mod_1_coordinate_is_neutral": len(residues) == len(paired),
            }
        )
    return records


def _arithmetic_boundary_checks(moduli: Sequence[int]) -> Dict[str, object]:
    totients: List[Dict[str, object]] = []
    quadratic: List[Dict[str, object]] = []
    for modulus in moduli:
        divisors = _divisors(modulus)
        inclusive = gauss_totient(modulus)
        strict_below = _strict_below_totient(modulus)
        divisor_sum = sum(gauss_totient(divisor) for divisor in divisors)
        residues = sorted({(value * value) % modulus for value in range(modulus)})
        totients.append(
            {
                "modulus": modulus,
                "strictly_below_count": strict_below,
                "not_greater_than_count": inclusive,
                "divisors": divisors,
                "sum_phi_over_divisors": divisor_sum,
                "divisor_sum_identity_holds": divisor_sum == modulus,
            }
        )
        quadratic.append(
            {
                "modulus": modulus,
                "square_residues": residues,
                "nonresidue_count": modulus - len(residues),
            }
        )
    return {
        "totient_endpoint": {
            "records": totients,
            "modulus_one_reading": (
                "The strict-below count is 0 at 1; Gauss Art. 39 changes the "
                "endpoint so phi(1)=1 and the divisor-sum identity remains uniform."
            ),
        },
        "quadratic_residues": {
            "records": quadratic,
            "modulus_one_reading": (
                "The sole class modulo 1 is represented by a square, so this "
                "modulus has no quadratic nonresidue obstruction."
            ),
        },
    }


def _fractional_phase_boundary() -> Dict[str, object]:
    equivalent_left = Fraction(1, 2)
    equivalent_right = Fraction(3, 2)
    zero = Fraction(0, 1)
    multiplier = Fraction(1, 2)
    return {
        "integer_congruence_mod_1": {
            "domain": "integers",
            "classes": 1,
            "multiplication_compatible": True,
        },
        "fractional_phase_mod_1": {
            "domain": "rationals under x~y iff x-y is an integer",
            "classes": "infinitely_many",
            "addition_compatible": True,
            "general_multiplication_compatible": False,
            "counterexample": {
                "equivalent_pair": [str(equivalent_left), str(equivalent_right)],
                "difference": str(equivalent_right - equivalent_left),
                "multiplier": str(multiplier),
                "products": [
                    str(equivalent_left * multiplier),
                    str(equivalent_right * multiplier),
                ],
                "product_difference": str(
                    equivalent_right * multiplier - equivalent_left * multiplier
                ),
            },
            "zero_comparison": {
                "pair": [str(equivalent_left), str(zero)],
                "difference": str(equivalent_left - zero),
                "equivalent": False,
            },
        },
        "total_value_collapse": {
            "domain": "all graph values",
            "classes": 1,
            "status": "generic graph abstraction, not Gaussian integer congruence",
        },
    }


def _first_operator_fan(
    conn: sqlite3.Connection, checkpoint: int
) -> Dict[str, object]:
    rows = conn.execute(
        """
        SELECT
          e.edge_id, e.stage, e.op,
          l.node_id AS left_node_id, l.p AS left_p, l.q AS left_q,
          l.label AS left_label,
          r.node_id AS right_node_id, r.p AS right_p, r.q AS right_q,
          r.label AS right_label,
          o.node_id AS result_node_id, o.p AS result_p, o.q AS result_q,
          o.label AS result_label, o.first_stage AS result_first_stage,
          o.confirmed_stage AS result_confirmed_stage
        FROM edges e
        JOIN nodes l ON l.node_id = e.left_node_id
        JOIN nodes r ON r.node_id = e.right_node_id
        JOIN nodes o ON o.node_id = e.result_node_id
        WHERE e.stage = 1
          AND l.p = 1 AND l.q = 1
          AND r.p = 1 AND r.q = 1
          AND e.op IN ('+', '-', '*', '/')
        ORDER BY CASE e.op WHEN '+' THEN 1 WHEN '-' THEN 2 WHEN '*' THEN 3 ELSE 4 END,
                 e.edge_id
        """
    ).fetchall()
    records = [_edge_record(row, 1, checkpoint) for row in rows]
    return {
        "query": "stage=1 and left=right=1 for +,-,*,/",
        "source_result_values": [record["result"]["value"] for record in records],
        "projected_result_residues_mod_1": [
            record["projected"]["result_residue"] for record in records
        ],
        "edge_occurrences": records,
        "reading": (
            "The value projection identifies 0, 1, and 2, but retained operation, "
            "edge, stage, and confirmation fields keep the fan asymmetric."
        ),
    }


def congruence_quotient_report(
    *,
    db_path: Path,
    moduli: Sequence[int],
    checkpoints: Optional[Sequence[int]],
    sample_limit: int,
    include_checksums: bool,
    argv: Optional[Sequence[str]] = None,
) -> Dict[str, object]:
    moduli = sorted(set(int(value) for value in moduli))
    if not moduli or min(moduli) < 1:
        raise ValueError("moduli must contain integers >= 1")
    if 1 not in moduli:
        raise ValueError("moduli must include 1 for the modulus-one control")

    with closing(connect_readonly(db_path)) as conn:
        alignment = require_strict_alignment(conn)
        corpus = _corpus_payload(conn, alignment)
        latest = corpus["latest_stage"]
        if not isinstance(latest, dict) or latest.get("stage") is None:
            raise SystemExit("Corpus has no completed stage")
        corpus_max_stage = int(latest["stage"])
        if checkpoints is None:
            selected = [value for value in DEFAULT_CHECKPOINTS if value <= corpus_max_stage]
            if corpus_max_stage not in selected:
                selected.append(corpus_max_stage)
        else:
            selected = sorted(set(int(value) for value in checkpoints))
            if not selected or min(selected) < 1:
                raise ValueError("checkpoints must contain integers >= 1")
            beyond = [value for value in selected if value > corpus_max_stage]
            if beyond:
                raise SystemExit(
                    "Requested checkpoints exceed corpus stage "
                    f"{corpus_max_stage}: {beyond}"
                )

        checkpoint_summaries: List[Dict[str, object]] = []
        focus: Optional[Dict[str, object]] = None
        focus_nodes: Optional[List[sqlite3.Row]] = None
        for checkpoint in selected:
            nodes = _load_integer_nodes(conn, checkpoint)
            edges = _load_integer_result_edges(conn, checkpoint)
            excluded = _excluded_rational_edges(conn, checkpoint)
            domains = _domain_rows(nodes, edges, checkpoint)
            domain_details: Dict[str, object] = {}
            compact_domains: Dict[str, object] = {}
            for name, (domain_nodes, domain_edges) in domains.items():
                source_summary = _source_domain_summary(
                    domain_nodes, domain_edges, checkpoint
                )
                projections = [
                    quotient_projection(
                        domain_nodes,
                        domain_edges,
                        modulus=modulus,
                        checkpoint=checkpoint,
                        sample_limit=sample_limit,
                    )
                    for modulus in moduli
                ]
                compact_domains[name] = {
                    "source": source_summary,
                    "completeness": _completeness_payload(
                        name, domain_edges, checkpoint
                    ),
                    "projections": [
                        _compact_projection(projection) for projection in projections
                    ],
                }
                if checkpoint == selected[-1]:
                    domain_details[name] = {
                        "source": source_summary,
                        "completeness": _completeness_payload(
                            name, domain_edges, checkpoint
                        ),
                        "projections": projections,
                    }
            checkpoint_summaries.append(
                {
                    "checkpoint": checkpoint,
                    "excluded_rational_result_edges": excluded,
                    "domains": compact_domains,
                }
            )
            if checkpoint == selected[-1]:
                focus_nodes = nodes
                focus = {
                    "checkpoint": checkpoint,
                    "excluded_rational_result_edges": excluded,
                    "domains": domain_details,
                    "refinement_checks": _refinement_checks(nodes, moduli),
                    "crt_modulus_one_identity_checks": _crt_modulus_one_checks(
                        nodes, moduli
                    ),
                }

        assert focus is not None and focus_nodes is not None
        first_fan = _first_operator_fan(conn, selected[-1])

    all_integer = focus["domains"]["all_integer_shadow"]  # type: ignore[index]
    q1_projection = next(
        projection
        for projection in all_integer["projections"]  # type: ignore[index]
        if projection["modulus"] == 1
    )
    payload: Dict[str, object] = {
        "metadata": report_metadata(
            tool_path=Path(__file__),
            db_path=db_path,
            argv=argv,
            schema_version=SCHEMA_VERSION,
            include_checksums=include_checksums,
        ),
        "tool_name": "integer congruence quotient probe",
        "graph_corpus": corpus,
        "projection_or_filter": {
            "primary_projection": "integer node label n maps to least residue n mod m",
            "primary_domain": (
                "all integer-valued source nodes first seen by the checkpoint and "
                "all retained integer-result edge occurrences"
            ),
            "strict_control_domain": (
                "confirmed positive-spine nodes through the checkpoint and edge "
                "occurrences whose results are among those nodes"
            ),
            "edge_policy": (
                "Decorate every retained source edge with residues; never deduplicate "
                "edge occurrences into a bare quotient edge."
            ),
            "excluded_domain": "non-integer rational results",
        },
        "candidate_id": "integer_congruence_modulus_one_negative_control",
        "why_flagged": (
            "Modulo 1 erases every integer value distinction. It therefore tests "
            "whether MoO reports preserve construction evidence independently of value."
        ),
        "nodes": {
            "focus_checkpoint_integer_source_nodes": q1_projection["source_node_count"],
            "mod_1_quotient_nodes": q1_projection["occupied_residue_count"],
        },
        "edges": {
            "focus_checkpoint_integer_result_occurrences": q1_projection[
                "edge_occurrence_count"
            ],
            "retained_after_mod_1_projection": q1_projection[
                "edge_occurrences_retained_after_projection"
            ],
            "operation_decorated_signatures_mod_1": q1_projection[
                "distinct_operation_decorated_signatures"
            ],
            "nonseed_operation_decorated_signatures_mod_1": q1_projection[
                "distinct_nonseed_operation_decorated_signatures"
            ],
            "unlabeled_nonseed_topologies_mod_1": q1_projection[
                "distinct_unlabeled_nonseed_topologies"
            ],
        },
        "neighborhood_query": {
            "source_edges": (
                "SELECT e.edge_id,e.stage,e.op,l.label,r.label,o.label FROM edges e "
                "LEFT JOIN nodes l ON l.node_id=e.left_node_id LEFT JOIN nodes r ON "
                "r.node_id=e.right_node_id JOIN nodes o ON o.node_id=e.result_node_id "
                "WHERE e.stage<=:U AND o.q=1 ORDER BY e.stage,e.edge_id"
            ),
            "interpretation": (
                "Inspect the source edge ids and node statuses inside each residue "
                "fiber; the quotient node alone has no neighborhood resolution at m=1."
            ),
        },
        "confirmation_status": {
            "projection_status": "external read-only observation",
            "source_alignment": alignment["status"],
            "result_status_fields_retained": True,
        },
        "claim_boundary": {
            "evidence_layer": "external_probe_over_strict_corpus",
            "claim_status": "observation",
            "allowed_claim_language": [
                "Modulo 1 collapses every integer value in the named source domain.",
                "Retained edge occurrences expose provenance that the residue quotient erases.",
                "The quotient topology at modulus 1 is a negative control, not a discovered structure.",
            ],
            "disallowed_claim_language": [
                "Do not say modulo 1 proves that 0 and 1 are identical in the source graph.",
                "Do not call a collapse of all rational nodes Gaussian congruence.",
                "Do not attribute retained graph diversity to arithmetic inside Z/1Z.",
                "Do not treat an external Gauss framing as MoO runtime semantics or validation.",
            ],
        },
        "domain_separation": _fractional_phase_boundary(),
        "arithmetic_boundary_checks": _arithmetic_boundary_checks(moduli),
        "checkpoint_summaries": checkpoint_summaries,
        "focus_checkpoint": focus,
        "first_operator_fan": first_fan,
        "one_bucket_control": {
            "quotient_node_count": q1_projection["occupied_residue_count"],
            "unlabeled_nonseed_topology_count": q1_projection[
                "distinct_unlabeled_nonseed_topologies"
            ],
            "source_edge_occurrences_retained": q1_projection[
                "edge_occurrences_retained_after_projection"
            ],
            "control_result": (
                "Any one-bucket value projection has the same bare one-node loop "
                "topology. Modulus 1 contributes no topology-specific signal; only "
                "source fibers and retained decorations carry information."
            ),
        },
        "interpretation_limits": [
            "Gauss's congruence is applied only to integer-valued nodes and results.",
            "The all-integer shadow includes unconfirmed and relational integers; its status fields must not be erased.",
            "The confirmed-positive domain is a corpus-specific control, not all of Z.",
            "Non-integer rational phase modulo 1 is Q/Z and is not a one-class ring quotient.",
            "Exact integer division is checked as b*c congruent to a, not as unrestricted residue division.",
            "All findings are conditioned on the named finite corpus and checkpoints.",
            "A singleton quotient does not imply 0=1 in the unprojected source graph.",
        ],
    }
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Project integer nodes and retained integer-result edges from a strict "
            "MoO graph corpus into congruence classes without erasing witnesses."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument(
        "--moduli",
        default=",".join(str(value) for value in DEFAULT_MODULI),
        help="Comma-separated positive moduli (default: 1,2,3,4,5,6,8,12).",
    )
    parser.add_argument(
        "--checkpoints",
        help=(
            "Comma-separated stage checkpoints. By default, standard checkpoints "
            "are clipped to the completed corpus and its final stage is included."
        ),
    )
    parser.add_argument("--sample-limit", type=positive_int, default=4)
    parser.add_argument("--include-checksums", action="store_true")
    parser.add_argument("--write", type=Path)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    raw_argv = list(argv) if argv is not None else None
    args = parser.parse_args(raw_argv)
    try:
        moduli = parse_positive_csv(args.moduli, field_name="moduli")
        checkpoints = (
            parse_positive_csv(args.checkpoints, field_name="checkpoints")
            if args.checkpoints
            else None
        )
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
    payload = congruence_quotient_report(
        db_path=Path(args.db),
        moduli=moduli,
        checkpoints=checkpoints,
        sample_limit=int(args.sample_limit),
        include_checksums=bool(args.include_checksums),
        argv=raw_argv,
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
