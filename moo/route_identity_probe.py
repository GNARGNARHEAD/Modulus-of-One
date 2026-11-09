from __future__ import annotations

import argparse
import json
import math
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Tuple

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
Expression = Tuple[object, ...]
COMMUTATIVE_OPS = {"+", "*"}
ASSOCIATIVE_COMMUTATIVE_OPS = {"+", "*"}


@dataclass(frozen=True)
class RouteStep:
    step_id: str
    left: Key
    op: str
    right: Key
    result: Key


@dataclass(frozen=True)
class RouteCertificate:
    route_id: str
    external_family: str
    description: str
    target: Key
    steps: Tuple[RouteStep, ...]
    interpretation_limit: str
    dependency_tags: Tuple[str, ...] = ()
    premise_steps: Tuple[RouteStep, ...] = ()


def _integer_key(value: int) -> Key:
    return normalize_key(int(value), 1)


def parse_key(raw: str) -> Key:
    value = Fraction(str(raw))
    return normalize_key(int(value.numerator), int(value.denominator))


def _key_sort(key: Key) -> Tuple[int, int, int]:
    return abs(int(key[0])), int(key[1]), int(key[0])


def _canonical_inputs(op: str, left: Key, right: Key) -> Tuple[Key, Key]:
    if str(op) in COMMUTATIVE_OPS:
        ordered = sorted((left, right), key=_key_sort)
        return ordered[0], ordered[1]
    return left, right


def _directed_step_fingerprint(step: RouteStep) -> str:
    return (
        f"{format_key(step.left)} {step.op} {format_key(step.right)}"
        f" -> {format_key(step.result)}"
    )


def _normalized_step_fingerprint(step: RouteStep) -> str:
    left, right = _canonical_inputs(step.op, step.left, step.right)
    return (
        f"{format_key(left)} {step.op} {format_key(right)}"
        f" -> {format_key(step.result)}"
    )


def _apply_operation(left: Key, op: str, right: Key) -> Key:
    a = Fraction(int(left[0]), int(left[1]))
    b = Fraction(int(right[0]), int(right[1]))
    if op == "+":
        result = a + b
    elif op == "-":
        result = a - b
    elif op == "*":
        result = a * b
    elif op == "/":
        if b == 0:
            raise ValueError("route certificate contains division by zero")
        result = a / b
    else:
        raise ValueError(f"unsupported route operation: {op}")
    return normalize_key(int(result.numerator), int(result.denominator))


def _require_canonical_key(key: Key, *, field: str, route_id: str) -> None:
    normalized = normalize_key(int(key[0]), int(key[1]))
    if tuple(key) != normalized:
        raise ValueError(
            f"route {route_id!r} has noncanonical {field} key "
            f"{key!r}; use {normalized!r}"
        )


def validate_route_certificate(route: RouteCertificate) -> None:
    if not route.steps:
        raise ValueError(f"route {route.route_id!r} has no steps")
    _require_canonical_key(
        route.target,
        field="target",
        route_id=route.route_id,
    )
    produced: Dict[Key, RouteStep] = {}
    step_ids: set[str] = set()
    for step in route.steps:
        for field, key in (
            (f"step {step.step_id!r} left", step.left),
            (f"step {step.step_id!r} right", step.right),
            (f"step {step.step_id!r} result", step.result),
        ):
            _require_canonical_key(key, field=field, route_id=route.route_id)
        if step.step_id in step_ids:
            raise ValueError(
                f"route {route.route_id!r} repeats step id {step.step_id!r}"
            )
        step_ids.add(step.step_id)
        if step.op not in {"+", "-", "*", "/"}:
            raise ValueError(f"route {route.route_id!r} uses unsupported op {step.op!r}")
        expected = _apply_operation(step.left, step.op, step.right)
        if expected != step.result:
            raise ValueError(
                f"route {route.route_id!r} step {step.step_id!r} is false: "
                f"expected {format_key(expected)}, got {format_key(step.result)}"
            )
        if step.result in produced:
            raise ValueError(
                f"route {route.route_id!r} produces {format_key(step.result)} more than once"
            )
        produced[step.result] = step
    for step in route.premise_steps:
        for field, key in (
            (f"premise {step.step_id!r} left", step.left),
            (f"premise {step.step_id!r} right", step.right),
            (f"premise {step.step_id!r} result", step.result),
        ):
            _require_canonical_key(key, field=field, route_id=route.route_id)
        if step.step_id in step_ids:
            raise ValueError(
                f"route {route.route_id!r} repeats step id {step.step_id!r}"
            )
        step_ids.add(step.step_id)
        if step.op not in {"+", "-", "*", "/"}:
            raise ValueError(f"route {route.route_id!r} uses unsupported op {step.op!r}")
        expected = _apply_operation(step.left, step.op, step.right)
        if expected != step.result:
            raise ValueError(
                f"route {route.route_id!r} premise {step.step_id!r} is false: "
                f"expected {format_key(expected)}, got {format_key(step.result)}"
            )
    if route.target not in produced:
        raise ValueError(
            f"route {route.route_id!r} does not construct target {format_key(route.target)}"
        )

    active: set[Key] = set()
    complete: set[Key] = set()

    def visit(key: Key) -> None:
        if key not in produced or key in complete:
            return
        if key in active:
            raise ValueError(f"route {route.route_id!r} contains a construction cycle")
        active.add(key)
        step = produced[key]
        visit(step.left)
        visit(step.right)
        active.remove(key)
        complete.add(key)

    visit(route.target)
    unused_results = set(produced) - complete
    if unused_results:
        labels = ", ".join(
            format_key(key) for key in sorted(unused_results, key=_key_sort)
        )
        raise ValueError(
            f"route {route.route_id!r} contains steps outside the target ancestry: {labels}"
        )


def canonical_route_expression(route: RouteCertificate) -> Expression:
    """Return the target expression modulo associativity/commutativity of + and *."""
    validate_route_certificate(route)
    produced = {step.result: step for step in route.steps}
    active: set[Key] = set()

    def expand(key: Key) -> Expression:
        step = produced.get(key)
        if step is None:
            return "leaf", int(key[0]), int(key[1])
        if key in active:
            raise ValueError(f"route {route.route_id!r} contains a construction cycle")
        active.add(key)
        children = [expand(step.left), expand(step.right)]
        active.remove(key)
        if step.op in ASSOCIATIVE_COMMUTATIVE_OPS:
            flattened: List[Expression] = []
            for child in children:
                if child[0] == "op" and child[1] == step.op:
                    flattened.extend(child[2])  # type: ignore[arg-type]
                else:
                    flattened.append(child)
            flattened.sort(key=repr)
            return "op", step.op, tuple(flattened)
        return "op", step.op, tuple(children)

    return expand(route.target)


def _expression_fingerprint(expression: Expression) -> str:
    if expression[0] == "leaf":
        return format_key((int(expression[1]), int(expression[2])))
    op = str(expression[1])
    children = expression[2]
    return f"{op}(" + ",".join(_expression_fingerprint(child) for child in children) + ")"


def _expression_payload(expression: Expression) -> Dict[str, object]:
    if expression[0] == "leaf":
        key = int(expression[1]), int(expression[2])
        return {"leaf": format_key(key), "key": [int(key[0]), int(key[1])]}
    return {
        "op": str(expression[1]),
        "children": [_expression_payload(child) for child in expression[2]],
    }


def _expression_leaf_keys(expression: Expression) -> List[Key]:
    if expression[0] == "leaf":
        return [(int(expression[1]), int(expression[2]))]
    leaves: List[Key] = []
    for child in expression[2]:
        leaves.extend(_expression_leaf_keys(child))
    return leaves


def cubic_216_route_certificates() -> Tuple[RouteCertificate, ...]:
    k = _integer_key
    return (
        RouteCertificate(
            route_id="cube_volume_6",
            external_family="geometry_cube_volume",
            description="Build the side-6 cube volume as (6 * 6) * 6.",
            target=k(216),
            steps=(
                RouteStep("side_square", k(6), "*", k(6), k(36)),
                RouteStep("volume", k(36), "*", k(6), k(216)),
            ),
            interpretation_limit=(
                "The geometry label is external; the graph records only the exact multiplication witnesses."
            ),
            dependency_tags=("six_cube_identity",),
        ),
        RouteCertificate(
            route_id="cube_surface_6",
            external_family="geometry_cube_surface",
            description="Build the side-6 cube surface expression as 6 * (6 * 6).",
            target=k(216),
            steps=(
                RouteStep("side_square", k(6), "*", k(6), k(36)),
                RouteStep("surface", k(6), "*", k(36), k(216)),
            ),
            interpretation_limit=(
                "The coefficient 6 and side 6 are the same value node; semantic roles are not graph identity."
            ),
            dependency_tags=("six_cube_identity", "coefficient_side_role_alias"),
        ),
        RouteCertificate(
            route_id="prime_cube_product",
            external_family="factorization",
            description="Build 216 as 2^3 * 3^3.",
            target=k(216),
            steps=(
                RouteStep("square_2", k(2), "*", k(2), k(4)),
                RouteStep("cube_2", k(4), "*", k(2), k(8)),
                RouteStep("square_3", k(3), "*", k(3), k(9)),
                RouteStep("cube_3", k(9), "*", k(3), k(27)),
                RouteStep("cube_product", k(8), "*", k(27), k(216)),
            ),
            interpretation_limit=(
                "Prime factorization is an external algebraic reading of an exact graph certificate."
            ),
            dependency_tags=("six_cube_identity", "factorization_6_as_2_times_3"),
        ),
        RouteCertificate(
            route_id="right_triangle_side_cubes",
            external_family="right_triangle_cubic_closure",
            description="Build 216 as 3^3 + 4^3 + 5^3.",
            target=k(216),
            steps=(
                RouteStep("square_3", k(3), "*", k(3), k(9)),
                RouteStep("cube_3", k(9), "*", k(3), k(27)),
                RouteStep("square_4", k(4), "*", k(4), k(16)),
                RouteStep("cube_4", k(16), "*", k(4), k(64)),
                RouteStep("square_5", k(5), "*", k(5), k(25)),
                RouteStep("cube_5", k(25), "*", k(5), k(125)),
                RouteStep("sum_3_4", k(27), "+", k(64), k(91)),
                RouteStep("sum_3_4_5", k(91), "+", k(125), k(216)),
            ),
            interpretation_limit=(
                "The equality is classical and theorem-dependent; graph distinction is not statistical independence."
            ),
            dependency_tags=("right_triangle_cubic_closure",),
            premise_steps=(
                RouteStep(
                    "pythagorean_square_relation",
                    k(9),
                    "+",
                    k(16),
                    k(25),
                ),
            ),
        ),
        RouteCertificate(
            route_id="binomial_3_plus_3_cube_expansion",
            external_family="binomial_expansion",
            description="Build the value side of (3 + 3)^3 as 27 + 81 + 81 + 27.",
            target=k(216),
            steps=(
                RouteStep("square_3", k(3), "*", k(3), k(9)),
                RouteStep("cube_3", k(9), "*", k(3), k(27)),
                RouteStep("mixed_term", k(9), "*", k(9), k(81)),
                RouteStep("half_expansion", k(27), "+", k(81), k(108)),
                RouteStep("full_expansion", k(108), "+", k(108), k(216)),
            ),
            interpretation_limit=(
                "Equal binomial terms collapse to shared value nodes; coefficient roles are external annotations."
            ),
            dependency_tags=("six_cube_identity", "binomial_expansion_3_plus_3"),
        ),
    )


def _row_key(row: sqlite3.Row, prefix: str) -> Key:
    return int(row[f"{prefix}_p"]), int(row[f"{prefix}_q"])


def _incoming_rows(
    conn: sqlite3.Connection,
    *,
    node_id: int,
    as_of_stage: Optional[int],
) -> List[sqlite3.Row]:
    sql = """
        SELECT
          e.edge_id,
          e.stage,
          e.op,
          l.p AS left_p,
          l.q AS left_q,
          r.p AS right_p,
          r.q AS right_q
        FROM edges e
        JOIN nodes l ON l.node_id = e.left_node_id
        JOIN nodes r ON r.node_id = e.right_node_id
        WHERE e.result_node_id = ?
          AND e.op != 'seed'
    """
    params: List[int] = [int(node_id)]
    if as_of_stage is not None:
        sql += " AND e.stage <= ?"
        params.append(int(as_of_stage))
    sql += " ORDER BY e.stage, e.edge_id"
    return list(conn.execute(sql, params).fetchall())


def _witness_group_payload(
    rows: Sequence[sqlite3.Row],
    *,
    evidence: GraphEvidence,
    target: Key,
    edge_ref_limit: int,
) -> Dict[str, object]:
    first = rows[0]
    op = str(first["op"])
    original_left = _row_key(first, "left")
    original_right = _row_key(first, "right")
    left, right = _canonical_inputs(op, original_left, original_right)
    orientations: DefaultDict[Tuple[Key, Key], List[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        orientations[(_row_key(row, "left"), _row_key(row, "right"))].append(row)
    orientation_payload = []
    for (directed_left, directed_right), directed_rows in sorted(
        orientations.items(), key=lambda item: (_key_sort(item[0][0]), _key_sort(item[0][1]))
    ):
        orientation_payload.append(
            {
                "relation": (
                    f"{format_key(directed_left)} {op} {format_key(directed_right)}"
                    f" -> {format_key(target)}"
                ),
                "edge_count": len(directed_rows),
                "edge_refs": [
                    {"edge_id": int(row["edge_id"]), "stage": int(row["stage"])}
                    for row in directed_rows[: int(edge_ref_limit)]
                ],
                "edge_refs_truncated": len(directed_rows) > int(edge_ref_limit),
            }
        )
    return {
        "normalized_relation": (
            f"{format_key(left)} {op} {format_key(right)} -> {format_key(target)}"
        ),
        "op": op,
        "left": evidence.node_payload(left),
        "right": evidence.node_payload(right),
        "result": evidence.node_payload(target),
        "edge_occurrences": len(rows),
        "directed_witnesses": len(orientations),
        "first_edge_stage": min(int(row["stage"]) for row in rows),
        "orientations": orientation_payload,
        "commutative_reversal_collapsed": op in COMMUTATIVE_OPS and len(orientations) > 1,
    }


def incoming_route_profile(
    conn: sqlite3.Connection,
    evidence: GraphEvidence,
    key: Key,
    *,
    as_of_stage: Optional[int],
    witness_limit: int,
    edge_ref_limit: int,
    include_witnesses: bool,
) -> Dict[str, object]:
    normalized = normalize_key(*key)
    node = evidence.node_payload(normalized)
    if not bool(node["present"]):
        return {
            "present": False,
            "visible_as_of_stage": False,
            "key": [int(normalized[0]), int(normalized[1])],
            "label": format_key(normalized),
            "as_of_stage": as_of_stage,
        }

    visible_as_of_stage = (
        as_of_stage is None or int(node["first_stage"]) <= int(as_of_stage)
    )
    if not visible_as_of_stage:
        confirmation_status_as_of_stage = "absent_at_aperture"
    elif as_of_stage is None:
        confirmation_status_as_of_stage = str(node["status"])
    elif normalized == (1, 1):
        confirmation_status_as_of_stage = "certainty"
    elif (
        node["confirmed_stage"] is not None
        and int(node["confirmed_stage"]) <= int(as_of_stage)
    ):
        confirmation_status_as_of_stage = "confirmed_by_core_loop_at_aperture"
    else:
        confirmation_status_as_of_stage = "unconfirmed_at_aperture"

    rows = _incoming_rows(
        conn,
        node_id=int(node["node_id"]),
        as_of_stage=as_of_stage,
    )
    directed = set()
    normalized_groups: DefaultDict[Tuple[str, Key, Key], List[sqlite3.Row]] = defaultdict(list)
    event_ops: Counter[str] = Counter()
    normalized_ops: Counter[str] = Counter()
    for row in rows:
        op = str(row["op"])
        left = _row_key(row, "left")
        right = _row_key(row, "right")
        directed.add((op, left, right))
        canonical_left, canonical_right = _canonical_inputs(op, left, right)
        normalized_groups[(op, canonical_left, canonical_right)].append(row)
        event_ops[op] += 1
    for op, _, _ in normalized_groups:
        normalized_ops[op] += 1

    ordered_groups = sorted(
        normalized_groups.values(),
        key=lambda group: (
            min(int(row["stage"]) for row in group),
            str(group[0]["op"]),
            _key_sort(_row_key(group[0], "left")),
            _key_sort(_row_key(group[0], "right")),
        ),
    )
    selected: List[Sequence[sqlite3.Row]] = []
    if include_witnesses and ordered_groups:
        seen_ops: set[str] = set()
        for group in ordered_groups:
            if len(selected) >= int(witness_limit):
                break
            op = str(group[0]["op"])
            if op not in seen_ops:
                selected.append(group)
                seen_ops.add(op)
        selected_ids = {id(group) for group in selected}
        for group in ordered_groups:
            if len(selected) >= int(witness_limit):
                break
            if id(group) not in selected_ids:
                selected.append(group)
                selected_ids.add(id(group))
        selected.sort(
            key=lambda group: (
                min(int(row["stage"]) for row in group),
                str(group[0]["op"]),
            )
        )

    normalized_count = len(normalized_groups)
    profile: Dict[str, object] = {
        "present": True,
        "visible_as_of_stage": visible_as_of_stage,
        "confirmation_status_as_of_stage": confirmation_status_as_of_stage,
        "node": node,
        "as_of_stage": as_of_stage,
        "incoming_edge_occurrences": len(rows),
        "directed_algebraic_witnesses": len(directed),
        "commutative_normalized_witnesses": normalized_count,
        "commutative_collapse_count": len(directed) - normalized_count,
        "commutative_reversal_orbits": sum(
            1
            for (op, _, _), group in normalized_groups.items()
            if op in COMMUTATIVE_OPS
            and len({(_row_key(row, "left"), _row_key(row, "right")) for row in group}) > 1
        ),
        "operation_signature": {
            "edge_occurrences": {op: int(event_ops[op]) for op in sorted(event_ops)},
            "normalized_witnesses": {
                op: int(normalized_ops[op]) for op in sorted(normalized_ops)
            },
            "operator_family_count": len(normalized_ops),
        },
        "first_incoming_edge_stage": min((int(row["stage"]) for row in rows), default=None),
    }
    if include_witnesses:
        profile["witness_groups"] = [
            _witness_group_payload(
                group,
                evidence=evidence,
                target=normalized,
                edge_ref_limit=int(edge_ref_limit),
            )
            for group in selected
        ]
        profile["witness_groups_displayed"] = len(selected)
        profile["witness_groups_total"] = len(ordered_groups)
        profile["witness_groups_truncated"] = len(selected) < len(ordered_groups)
    return profile


def _compact_witness(witness: Dict[str, object]) -> Dict[str, object]:
    return {
        "present": bool(witness["present"]),
        "edge_count": int(witness["edge_count"]),
        "expected_directed_edges": int(witness["expected_directed_edges"]),
        "status": witness["status"],
        "first_edge_stage": witness["first_edge_stage"],
        "edge_refs": witness["edge_refs"],
        "edge_refs_truncated": witness["edge_refs_truncated"],
        "missing_nodes": witness["missing_nodes"],
        "candidate_stage": witness["candidate_stage"],
        "eligible_by_stage": witness["eligible_by_stage"],
        "blocker": witness["blocker"],
    }


def evaluate_route_certificate(
    evidence: GraphEvidence,
    route: RouteCertificate,
    *,
    as_of_stage: Optional[int],
    edge_ref_limit: int,
) -> Dict[str, object]:
    validate_route_certificate(route)
    expression = canonical_route_expression(route)
    edge_rows = []
    completion_stages: List[int] = []
    directed_supported = True
    quotient_supported = True
    visible_as_of_stage = True
    node_keys: set[Key] = {route.target}
    required_steps = (
        [("construction", step) for step in route.steps]
        + [("premise", step) for step in route.premise_steps]
    )
    for role, step in required_steps:
        node_keys.update((step.left, step.right, step.result))
        directed = evidence.edge_witness(
            left=step.left,
            op=step.op,
            right=step.right,
            result=step.result,
            allow_commuted=False,
            edge_limit=int(edge_ref_limit),
        )
        quotient = directed
        if step.op in COMMUTATIVE_OPS:
            quotient = evidence.edge_witness(
                left=step.left,
                op=step.op,
                right=step.right,
                result=step.result,
                allow_commuted=True,
                edge_limit=int(edge_ref_limit),
            )
        directed_supported = directed_supported and bool(directed["present"])
        quotient_supported = quotient_supported and bool(quotient["present"])
        first_stage = quotient["first_edge_stage"]
        if first_stage is None:
            visible_as_of_stage = False
        else:
            completion_stages.append(int(first_stage))
            if as_of_stage is not None and int(first_stage) > int(as_of_stage):
                visible_as_of_stage = False
        edge_rows.append(
            {
                "role": role,
                "step_id": step.step_id,
                "specified_relation": _directed_step_fingerprint(step),
                "commutative_normalized_relation": _normalized_step_fingerprint(step),
                "specified_direction": _compact_witness(directed),
                "commutative_orbit": _compact_witness(quotient),
                "visible_as_of_stage": (
                    first_stage is not None
                    and (as_of_stage is None or int(first_stage) <= int(as_of_stage))
                ),
            }
        )

    normalized_edges = sorted(_normalized_step_fingerprint(step) for step in route.steps)
    directed_edges = sorted(_directed_step_fingerprint(step) for step in route.steps)
    terminal_step = next(step for step in route.steps if step.result == route.target)
    intermediate_keys = sorted(
        {step.result for step in route.steps if step.result != route.target},
        key=_key_sort,
    )
    leaf_keys = _expression_leaf_keys(expression)
    return {
        "route_id": route.route_id,
        "external_family": route.external_family,
        "description": route.description,
        "declared_dependency_tags": list(route.dependency_tags),
        "target": evidence.node_payload(route.target),
        "nodes": [evidence.node_payload(key) for key in sorted(node_keys, key=_key_sort)],
        "edges": edge_rows,
        "graph_support": {
            "all_specified_directions_present": directed_supported,
            "all_commutative_orbits_present": quotient_supported,
            "visible_as_of_stage": quotient_supported and visible_as_of_stage,
            "earliest_complete_stage": (
                max(completion_stages)
                if quotient_supported and len(completion_stages) == len(required_steps)
                else None
            ),
            "as_of_stage": as_of_stage,
        },
        "fingerprints": {
            "directed_edge_multiset": directed_edges,
            "commutative_edge_multiset": normalized_edges,
            "terminal_directed_witness": _directed_step_fingerprint(terminal_step),
            "terminal_commutative_witness": _normalized_step_fingerprint(terminal_step),
            "associative_commutative_expression": _expression_fingerprint(expression),
        },
        "associative_commutative_expression": _expression_payload(expression),
        "declared_leaf_cut": [format_key(key) for key in leaf_keys],
        "intermediate_nodes": [format_key(key) for key in intermediate_keys],
        "premise_step_ids": [step.step_id for step in route.premise_steps],
        "interpretation_limit": route.interpretation_limit,
    }


def compare_route_certificates(
    left: RouteCertificate,
    right: RouteCertificate,
) -> Dict[str, object]:
    left_expression = canonical_route_expression(left)
    right_expression = canonical_route_expression(right)
    left_directed = sorted(_directed_step_fingerprint(step) for step in left.steps)
    right_directed = sorted(_directed_step_fingerprint(step) for step in right.steps)
    left_normalized = sorted(_normalized_step_fingerprint(step) for step in left.steps)
    right_normalized = sorted(_normalized_step_fingerprint(step) for step in right.steps)
    left_terminal = next(step for step in left.steps if step.result == left.target)
    right_terminal = next(step for step in right.steps if step.result == right.target)
    left_intermediate = {step.result for step in left.steps if step.result != left.target}
    right_intermediate = {step.result for step in right.steps if step.result != right.target}
    left_leaves = set(_expression_leaf_keys(left_expression))
    right_leaves = set(_expression_leaf_keys(right_expression))
    shared_steps = sorted(set(left_normalized) & set(right_normalized))
    same_ac_expression = left_expression == right_expression
    same_commutative_route = left_normalized == right_normalized
    same_final_witness = (
        _normalized_step_fingerprint(left_terminal)
        == _normalized_step_fingerprint(right_terminal)
    )
    shared_intermediate = left_intermediate & right_intermediate
    shared_leaves = left_leaves & right_leaves
    shared_dependency_tags = sorted(set(left.dependency_tags) & set(right.dependency_tags))

    if same_ac_expression:
        classification = "same_route_under_associative_commutative_quotient"
        independence_status = "collapsed_by_graph_route_quotient"
    elif same_commutative_route:
        classification = "same_commutative_edge_certificate"
        independence_status = "collapsed_by_graph_route_quotient"
    elif shared_dependency_tags:
        classification = "distinct_graph_certificate_with_declared_algebraic_dependency"
        independence_status = "dependent_rewrite_or_projection"
    elif same_final_witness:
        classification = "same_terminal_witness_with_distinct_upstream_certificate"
        independence_status = "not_independent_at_terminal_cut"
    elif shared_steps or shared_intermediate or shared_leaves:
        classification = "distinct_certificates_with_explicit_dependency_overlap"
        independence_status = "not_independent_at_declared_leaf_cut"
    else:
        classification = "distinct_at_declared_certificate_cut"
        independence_status = "distinct_at_cut_only_not_global_independence"

    return {
        "left_route": left.route_id,
        "right_route": right.route_id,
        "same_directed_edge_multiset": left_directed == right_directed,
        "same_commutative_edge_multiset": same_commutative_route,
        "same_associative_commutative_expression": same_ac_expression,
        "same_terminal_commutative_witness": same_final_witness,
        "shared_commutative_steps": shared_steps,
        "shared_intermediate_nodes": [
            format_key(key) for key in sorted(shared_intermediate, key=_key_sort)
        ],
        "shared_declared_leaf_nodes": [
            format_key(key) for key in sorted(shared_leaves, key=_key_sort)
        ],
        "shared_declared_dependency_tags": shared_dependency_tags,
        "classification": classification,
        "independence_status": independence_status,
    }


def _route_case_payload(
    evidence: GraphEvidence,
    *,
    case_id: str,
    as_of_stage: Optional[int],
    edge_ref_limit: int,
) -> Dict[str, object]:
    if case_id != "cubic-216":
        raise ValueError(f"unsupported route case: {case_id}")
    routes = cubic_216_route_certificates()
    evaluated = [
        evaluate_route_certificate(
            evidence,
            route,
            as_of_stage=as_of_stage,
            edge_ref_limit=int(edge_ref_limit),
        )
        for route in routes
    ]
    comparisons = [compare_route_certificates(left, right) for left, right in combinations(routes, 2)]
    node_payloads: Dict[int, Dict[str, object]] = {}
    edge_payloads: List[Dict[str, object]] = []
    for route in evaluated:
        for node in route["nodes"]:
            if bool(node["present"]):
                node_payloads[int(node["node_id"])] = node
        for edge in route["edges"]:
            edge_payloads.append({"route_id": route["route_id"], **edge})
    return {
        "case_id": "cubic_216_route_calibration",
        "case_status": "external_calibration_not_branch_evidence",
        "target": evidence.node_payload(_integer_key(216)),
        "routes": evaluated,
        "pairwise_comparisons": comparisons,
        "nodes": [node_payloads[node_id] for node_id in sorted(node_payloads)],
        "edges": edge_payloads,
        "machine_reading": [
            "cube_surface_6 and cube_volume_6 collapse to one associative/commutative graph route.",
            "right_triangle_side_cubes reaches 216 through a different declared graph certificate.",
            "prime_cube_product shares an explicit 3^3 subcertificate with the side-cube route.",
            "binomial expansion is graph-distinct but algebraically dependent on the same cube identity.",
            "No pairwise result certifies semantic or causal independence beyond its declared leaf cut.",
        ],
    }


def _divisor_count(value: int) -> int:
    count = 0
    root = math.isqrt(int(value))
    for divisor in range(1, root + 1):
        if int(value) % divisor == 0:
            count += 1 if divisor * divisor == int(value) else 2
    return count


def _strict_integer_multiplicity_control(
    *,
    target: Key,
    stage: int,
    config: Optional[object],
    observed_profile: Dict[str, object],
) -> Dict[str, object]:
    if target[1] != 1 or target[0] < 1 or target[0] > int(stage):
        return {
            "available": False,
            "reason": "closed form requires a positive integer target n with 1 <= n <= U",
        }
    if not isinstance(config, dict) or config.get("generator") != "strict_stage_moo_graph":
        return {"available": False, "reason": "unsupported or missing corpus config"}
    n = int(target[0])
    max_abs_value = config.get("max_abs_value")
    wide_enough = (
        int(config.get("max_abs_p", 0)) >= n
        and int(config.get("max_abs_q", 0)) >= 1
        and (max_abs_value is None or float(max_abs_value) >= float(n))
    )
    if not wide_enough:
        return {
            "available": False,
            "reason": "corpus retention bounds can remove target-result edges",
        }

    divisor_count = _divisor_count(n)
    raw_by_op = {
        "+": n - 1,
        "-": int(stage) - n,
        "*": divisor_count,
        "/": int(stage) // n,
    }
    normalized_by_op = {
        "+": n // 2,
        "-": int(stage) - n,
        "*": (divisor_count + 1) // 2,
        "/": int(stage) // n,
    }
    expected_raw = sum(raw_by_op.values())
    expected_normalized = sum(normalized_by_op.values())
    observed_raw = int(observed_profile["incoming_edge_occurrences"])
    observed_normalized = int(observed_profile["commutative_normalized_witnesses"])
    return {
        "available": True,
        "scope": "complete wide strict positive-integer corpus through stage U",
        "U": int(stage),
        "n": n,
        "tau_n": divisor_count,
        "raw_formula": "D_U(n) = (n-1) + (U-n) + tau(n) + floor(U/n)",
        "commutative_normalized_formula": (
            "Q_U(n) = floor(n/2) + (U-n) + ceil(tau(n)/2) + floor(U/n)"
        ),
        "expected_edge_occurrences_by_op": raw_by_op,
        "expected_normalized_witnesses_by_op": normalized_by_op,
        "expected_edge_occurrences": expected_raw,
        "observed_edge_occurrences": observed_raw,
        "expected_commutative_normalized_witnesses": expected_normalized,
        "observed_commutative_normalized_witnesses": observed_normalized,
        "observed_matches_closed_form": (
            observed_raw == expected_raw and observed_normalized == expected_normalized
        ),
        "null_reading": (
            "When the closed form matches, aggregate one-step collision mass is fully explained by generator mechanics; inspect explicit route certificates instead."
        ),
    }


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (str(key),)).fetchone()
    return None if row is None else str(row["value"])


def _json_meta(conn: sqlite3.Connection, key: str) -> Optional[object]:
    raw = _meta_value(conn, key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _corpus_payload(
    conn: sqlite3.Connection,
    evidence: GraphEvidence,
    alignment: Dict[str, object],
) -> Dict[str, object]:
    latest = conn.execute("SELECT * FROM stages ORDER BY stage DESC LIMIT 1").fetchone()
    return {
        "schema_version": _meta_value(conn, "schema_version"),
        "config": _json_meta(conn, "config_json"),
        "recorded_corpus_stage": evidence.recorded_corpus_stage,
        "complete_corpus_stage": evidence.complete_corpus_stage,
        "latest_stage": dict(latest) if latest is not None else None,
        "nodes": int(conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]),
        "edges": int(conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]),
        "alignment": alignment,
    }


def _profile_metric(profile: Dict[str, object], metric: str) -> Optional[float]:
    if not bool(profile.get("present")) or profile.get("visible_as_of_stage") is False:
        return None
    node = profile["node"]
    if metric == "first_stage":
        return float(node["first_stage"])
    if metric == "confirmation_lag":
        confirmed = node["confirmed_stage"]
        return None if confirmed is None else float(int(confirmed) - int(node["first_stage"]))
    if metric == "multiplicative_normalized_witnesses":
        return float(profile["operation_signature"]["normalized_witnesses"].get("*", 0))
    return float(profile[metric])


def _directional_rank(
    rows: Sequence[Dict[str, object]],
    *,
    target_label: str,
    metric: str,
    direction: str,
) -> Dict[str, object]:
    values = [
        (str(row["label"]), _profile_metric(row["profile"], metric))
        for row in rows
    ]
    values = [(label, value) for label, value in values if value is not None]
    target_value = next((value for label, value in values if label == target_label), None)
    if target_value is None:
        return {"available": False, "metric": metric, "direction": direction}
    if direction == "high":
        outranked = sum(1 for _, value in values if float(value) > float(target_value))
        percentile = sum(1 for _, value in values if float(value) <= float(target_value)) / len(values)
    else:
        outranked = sum(1 for _, value in values if float(value) < float(target_value))
        percentile = sum(1 for _, value in values if float(value) >= float(target_value)) / len(values)
    return {
        "available": True,
        "metric": metric,
        "direction": direction,
        "target_value": target_value,
        "cohort_size": len(values),
        "directional_rank": outranked + 1,
        "directional_percentile": percentile,
    }


def _local_control_window(
    conn: sqlite3.Connection,
    evidence: GraphEvidence,
    target: Key,
    *,
    radius: int,
    as_of_stage: Optional[int],
) -> Dict[str, object]:
    if int(radius) < 1 or target[1] != 1 or target[0] < 1:
        return {
            "available": False,
            "reason": "requires a positive-integer target and control_radius >= 1",
        }
    start = max(1, int(target[0]) - int(radius))
    stop = int(target[0]) + int(radius)
    rows = []
    for value in range(start, stop + 1):
        key = _integer_key(value)
        profile = incoming_route_profile(
            conn,
            evidence,
            key,
            as_of_stage=as_of_stage,
            witness_limit=1,
            edge_ref_limit=1,
            include_witnesses=False,
        )
        rows.append(
            {
                "label": format_key(key),
                "role": "target" if key == target else "local_control",
                "profile": profile,
            }
        )
    metrics = {
        "commutative_normalized_witnesses": "high",
        "commutative_collapse_count": "high",
        "multiplicative_normalized_witnesses": "high",
        "first_stage": "low",
        "confirmation_lag": "high",
    }
    return {
        "available": True,
        "control_rule": "all positive integers in the symmetric value window",
        "radius": int(radius),
        "range": [start, stop],
        "as_of_stage": as_of_stage,
        "target_ranks": {
            metric: _directional_rank(
                rows,
                target_label=format_key(target),
                metric=metric,
                direction=direction,
            )
            for metric, direction in metrics.items()
        },
        "rows": rows,
        "interpretation_limit": (
            "This local value-window control reduces gross scale drift but does not match every graph baseline."
        ),
    }


def _claim_boundary() -> Dict[str, object]:
    return {
        "evidence_layer": "strict_graph_with_external_route_annotations",
        "claim_status": "controlled_calibration",
        "allowed_claim_language": [
            "Exact incoming edge occurrences and declared multi-edge certificates are present or absent at a named corpus aperture.",
            "Commutative reversals and associative regroupings can be identified by explicit quotient rules.",
            "Two certificates can be distinct at a declared leaf cut while sharing named dependencies.",
        ],
        "disallowed_claim_language": [
            "Do not count x+y and y+x, or x*y and y*x, as independent routes.",
            "Do not infer semantic independence from external family labels.",
            "Do not treat route multiplicity or the value 216 as special without controls.",
            "Do not promote external family labels into MoO runtime semantics.",
            "Do not interpret distinct-at-cut as global causal or statistical independence; all strict routes ultimately share the positive spine from 1.",
        ],
    }


def build_report(
    conn: sqlite3.Connection,
    *,
    db_path: Path,
    target: Key,
    controls: Sequence[Key],
    case_id: Optional[str],
    requested_as_of_stage: Optional[int],
    milestones: Sequence[int],
    control_radius: int,
    witness_limit: int,
    edge_ref_limit: int,
    argv: Optional[Sequence[str]],
    include_checksums: bool,
) -> Dict[str, object]:
    alignment = require_strict_alignment(conn)
    evidence = GraphEvidence(conn)
    if evidence.complete_corpus_stage is None:
        raise SystemExit("Route identity probe requires verified strict-stage telemetry")
    effective_stage = int(evidence.complete_corpus_stage)
    if requested_as_of_stage is not None:
        effective_stage = min(effective_stage, int(requested_as_of_stage))
    target = normalize_key(*target)
    if case_id == "cubic-216" and target != _integer_key(216):
        raise SystemExit("--case cubic-216 requires --target 216")

    target_profile = incoming_route_profile(
        conn,
        evidence,
        target,
        as_of_stage=effective_stage,
        witness_limit=int(witness_limit),
        edge_ref_limit=int(edge_ref_limit),
        include_witnesses=True,
    )
    config = _json_meta(conn, "config_json")
    multiplicity_control = _strict_integer_multiplicity_control(
        target=target,
        stage=effective_stage,
        config=config,
        observed_profile=target_profile,
    ) if bool(target_profile.get("present")) else {
        "available": False,
        "reason": "target node is absent",
    }
    route_case = (
        _route_case_payload(
            evidence,
            case_id=case_id,
            as_of_stage=effective_stage,
            edge_ref_limit=int(edge_ref_limit),
        )
        if case_id is not None
        else None
    )

    milestone_set = {int(stage) for stage in milestones if int(stage) <= effective_stage}
    if bool(target_profile.get("present")):
        node = target_profile["node"]
        if int(node["first_stage"]) <= effective_stage:
            milestone_set.add(int(node["first_stage"]))
        if node["confirmed_stage"] is not None and int(node["confirmed_stage"]) <= effective_stage:
            milestone_set.add(int(node["confirmed_stage"]))
    if route_case is not None:
        for route in route_case["routes"]:
            stage = route["graph_support"]["earliest_complete_stage"]
            if stage is not None and int(stage) <= effective_stage:
                milestone_set.add(int(stage))
    milestone_set.add(effective_stage)
    timeline = [
        incoming_route_profile(
            conn,
            evidence,
            target,
            as_of_stage=stage,
            witness_limit=1,
            edge_ref_limit=1,
            include_witnesses=False,
        )
        for stage in sorted(milestone_set)
    ]

    explicit_controls = [
        incoming_route_profile(
            conn,
            evidence,
            normalize_key(*key),
            as_of_stage=effective_stage,
            witness_limit=1,
            edge_ref_limit=1,
            include_witnesses=False,
        )
        for key in controls
    ]
    target_node = evidence.node_payload(target)
    neighborhood_query = (
        f"python3 moo_graph_query.py --db {db_path} --node {format_key(target)} "
        "--neighborhood --pretty"
    )
    nodes = [target_node] if bool(target_node["present"]) else []
    edges: List[Dict[str, object]] = []
    if route_case is not None:
        nodes = route_case["nodes"]
        edges = route_case["edges"]

    return {
        "tool_name": "moo_route_identity_probe",
        "metadata": report_metadata(
            tool_path=Path(__file__),
            db_path=Path(db_path),
            argv=argv,
            schema_version="moo_route_identity_probe.report.v1",
            include_checksums=bool(include_checksums),
        ),
        "graph_corpus": _corpus_payload(conn, evidence, alignment),
        "projection_or_filter": {
            "requested_as_of_stage": requested_as_of_stage,
            "effective_as_of_stage": effective_stage,
            "equivalence_ladder": [
                "edge_occurrence: edge_id and direction remain distinct",
                "directed_witness: repeated occurrences of the same op/left/right/result collapse",
                "commutative_witness: operand reversal collapses for + and *",
                "associative_commutative_expression: declared +/* expression trees flatten and sort",
                "semantic_family: external annotation only; no automatic independence claim",
            ],
        },
        "claim_boundary": _claim_boundary(),
        "candidate_id": f"route_profile:{format_key(target)}",
        "why_flagged": (
            "External 216/Pascal exploration proposed this node as a calibration case for route identity, dependency, and projection collapse."
        ),
        "nodes": nodes,
        "edges": edges,
        "neighborhood_query": neighborhood_query,
        "confirmation_status": target_node.get("status") if bool(target_node["present"]) else "absent",
        "confirmation_status_as_of_stage": target_profile.get(
            "confirmation_status_as_of_stage",
            "absent",
        ),
        "target_profile": target_profile,
        "strict_generator_multiplicity_control": multiplicity_control,
        "aperture_timeline": timeline,
        "explicit_control_profiles": explicit_controls,
        "local_control_window": _local_control_window(
            conn,
            evidence,
            target,
            radius=int(control_radius),
            as_of_stage=effective_stage,
        ),
        "route_case": route_case,
        "interpretation_limits": [
            "The graph is primary; external route names annotate exact nodes and edges but do not alter runtime semantics.",
            "A commutative or associative quotient intentionally erases direction or parenthesization and reports that loss.",
            "Declared certificates are finite cuts through a much denser graph, not unique derivations of their values.",
            "Local controls are aperture-conditioned and do not establish universal exceptionalness.",
            "Distinct graph certificates do not by themselves prove semantic, causal, or statistical independence.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Profile exact MoO construction routes under directed, commutative, and associative/commutative identity rules."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--target", type=parse_key, required=True)
    parser.add_argument("--control", type=parse_key, action="append", default=[])
    parser.add_argument("--case", choices=("cubic-216",))
    parser.add_argument("--as-of-stage", type=positive_int)
    parser.add_argument("--milestone", type=positive_int, action="append", default=[])
    parser.add_argument("--control-radius", type=int, default=0)
    parser.add_argument("--witness-limit", type=positive_int, default=24)
    parser.add_argument("--edge-ref-limit", type=positive_int, default=4)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--write", type=Path)
    parser.add_argument("--include-checksums", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if int(args.control_radius) < 0:
        parser.error("--control-radius must be >= 0")
    if int(args.control_radius) > 1000:
        parser.error("--control-radius must be <= 1000")
    with closing(connect_readonly(args.db)) as conn:
        report = build_report(
            conn,
            db_path=args.db,
            target=args.target,
            controls=args.control,
            case_id=args.case,
            requested_as_of_stage=args.as_of_stage,
            milestones=args.milestone,
            control_radius=int(args.control_radius),
            witness_limit=int(args.witness_limit),
            edge_ref_limit=int(args.edge_ref_limit),
            argv=argv,
            include_checksums=bool(args.include_checksums),
        )
    emit_json(report, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
