from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from contextlib import closing
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from moo.graph_corpus import format_key
from moo.graph_evidence import GraphEvidence, node_status
from moo.phase import (
    additive_return_order,
    fraction_key as _key,
    fraction_payload,
    phase_fraction,
    phase_payload,
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
MAX_PHASE_CLASSES = 512
MAX_SAMPLE_LIFTS = 64
MAX_TRANSLATION_PAIRS = 64
MAX_CYCLE_POINTS = 256


def euler_totient(value: int) -> int:
    """Count reduced phases of exact additive order value."""

    n = int(value)
    if n < 1:
        raise ValueError("totient input must be >= 1")
    result = n
    factor = 2
    remainder = n
    while factor * factor <= remainder:
        if remainder % factor == 0:
            while remainder % factor == 0:
                remainder //= factor
            result -= result // factor
        factor += 1
    if remainder > 1:
        result -= result // remainder
    return int(result)


def phase_cycle(value: Fraction | int) -> List[Fraction]:
    """List the distinct additive phases before the first return to zero."""

    phase = phase_fraction(value)
    order = additive_return_order(phase)
    cycle = [phase_fraction(index * phase) for index in range(order)]
    if len(set(cycle)) != order:
        raise AssertionError("phase cycle returned before its reduced denominator")
    if phase_fraction(order * phase) != 0:
        raise AssertionError("phase cycle did not return at its reduced denominator")
    return cycle


def cyclotomic_closure_payload(
    value: Fraction | int,
    *,
    cycle_point_limit: int,
) -> Dict[str, object]:
    phase = phase_fraction(value)
    order = additive_return_order(phase)
    cycle = phase_cycle(phase)
    include_cycle = order <= int(cycle_point_limit)
    if phase == 0:
        return {
            "return_order": 1,
            "returns_to_identity": True,
            "distinct_phase_count": 1,
            "cycle": [fraction_payload(point) for point in cycle]
            if include_cycle
            else None,
            "full_minimal_orbit_sum": "1",
            "cancellation_status": "identity_does_not_cancel",
            "exact_external_identity": (
                "Repeating the identity point q times sums to q; the zero-sum "
                "geometric identity requires a non-identity root of unity."
            ),
        }
    return {
        "return_order": int(order),
        "returns_to_identity": phase_fraction(order * phase) == 0,
        "distinct_phase_count": len(cycle),
        "cycle": [fraction_payload(point) for point in cycle]
        if include_cycle
        else None,
        "cycle_omitted_reason": None
        if include_cycle
        else f"return_order exceeds cycle_point_limit={cycle_point_limit}",
        "full_minimal_orbit_sum": "0",
        "cancellation_status": "exact_external_cyclotomic_identity",
        "exact_external_identity": (
            "For z = exp(2*pi*i*r/q) of reduced order q > 1, "
            "1 + z + ... + z^(q-1) = (1-z^q)/(1-z) = 0."
        ),
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


def _phase_node_rows(
    conn: sqlite3.Connection,
    *,
    max_denominator: int,
) -> List[sqlite3.Row]:
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
              COALESCE(SUM(CASE WHEN e.op = '/' THEN 1 ELSE 0 END), 0) AS divide_count
            FROM nodes n
            LEFT JOIN edges e ON e.result_node_id = n.node_id
            WHERE n.q <= ?
            GROUP BY n.node_id
            ORDER BY n.q, n.p
            """,
            (int(max_denominator),),
        ).fetchall()
    )


def _row_value(row: sqlite3.Row) -> Fraction:
    return Fraction(int(row["p"]), int(row["q"]))


def _lift_payload(row: sqlite3.Row) -> Dict[str, object]:
    value = _row_value(row)
    phase = phase_fraction(value)
    lift = value - phase
    if lift.denominator != 1:
        raise AssertionError("quotient lift difference must be an integer")
    return {
        "value": fraction_payload(value),
        "integer_lift": int(lift),
        "node_id": int(row["node_id"]),
        "kind": str(row["kind"]),
        "status": node_status(row),
        "first_stage": int(row["first_stage"]),
        "confirmed_stage": int(row["confirmed_stage"])
        if row["confirmed_stage"] is not None
        else None,
        "incoming_edge_count": int(row["incoming_edge_count"]),
        "incoming_operation_counts": {
            "+": int(row["plus_count"]),
            "-": int(row["minus_count"]),
            "*": int(row["multiply_count"]),
            "/": int(row["divide_count"]),
        },
    }


def _sample_rows(
    rows: Iterable[sqlite3.Row],
    *,
    is_identity: bool,
    limit: int,
) -> List[sqlite3.Row]:
    ordered = sorted(rows, key=_row_value)
    if is_identity:
        positive = [row for row in ordered if _row_value(row) >= 1]
        remainder = [row for row in ordered if _row_value(row) < 1]
        ordered = positive + remainder
    return ordered[: int(limit)]


def _translation_pairs(
    rows: Iterable[sqlite3.Row],
    *,
    evidence: GraphEvidence,
    pair_limit: int,
    edge_limit: int,
) -> Dict[str, object]:
    by_value = {_row_value(row): row for row in rows}
    candidates = [
        (value, value + 1)
        for value in by_value
        if value + 1 in by_value
    ]
    candidates.sort(
        key=lambda pair: (
            0
            if pair[0].denominator == 1 and pair[0] >= 1
            else 1,
            pair[0],
        )
    )
    selected = candidates[: int(pair_limit)]
    payloads: List[Dict[str, object]] = []
    blockers: Counter[str] = Counter()
    present = 0
    for left, result in selected:
        witness = evidence.edge_witness(
            left=left,
            op="+",
            right=1,
            result=result,
            allow_commuted=True,
            claim_id="unit_translation_same_phase",
            relation=f"{format_key(_key(left))} + 1 -> {format_key(_key(result))}",
            edge_limit=int(edge_limit),
        )
        if bool(witness["present"]):
            present += 1
        elif witness["blocker"] is not None:
            blockers[str(witness["blocker"])] += 1
        payloads.append(
            {
                "from": fraction_payload(left),
                "to": fraction_payload(result),
                "same_phase": phase_fraction(left) == phase_fraction(result),
                "graph": {
                    "present": bool(witness["present"]),
                    "status": str(witness["status"]),
                    "blocker": witness["blocker"],
                    "edge_count": int(witness["edge_count"]),
                    "expected_directed_edges": int(witness["expected_directed_edges"]),
                    "first_edge_stage": witness["first_edge_stage"],
                    "edge_refs": witness["edge_refs"],
                },
            }
        )
    return {
        "candidate_pairs_in_observed_fibre": len(candidates),
        "reported_pairs": len(payloads),
        "witnessed_pairs": int(present),
        "blocked_or_absent_pairs": len(payloads) - int(present),
        "blockers": dict(sorted(blockers.items())),
        "rows": payloads,
    }


def _phase_class_payload(
    phase_key: Key,
    rows: List[sqlite3.Row],
    *,
    evidence: GraphEvidence,
    sample_lifts: int,
    translation_pair_limit: int,
    edge_limit: int,
    cycle_point_limit: int,
) -> Dict[str, object]:
    phase = Fraction(int(phase_key[0]), int(phase_key[1]))
    first_stages = [int(row["first_stage"]) for row in rows]
    incoming_counts = [int(row["incoming_edge_count"]) for row in rows]
    status_counts = Counter(node_status(row) for row in rows)
    sampled_rows = _sample_rows(
        rows,
        is_identity=phase == 0,
        limit=int(sample_lifts),
    )
    return {
        "phase": phase_payload(phase),
        "quotient_fibre": {
            "description": "all observed rational nodes in phase + Z",
            "observed_lift_count": len(rows),
            "has_multiple_observed_lifts": len(rows) > 1,
            "minimum_lift": fraction_payload(min(_row_value(row) for row in rows)),
            "maximum_lift": fraction_payload(max(_row_value(row) for row in rows)),
            "first_stage_min": min(first_stages),
            "first_stage_max": max(first_stages),
            "first_stage_spread": max(first_stages) - min(first_stages),
            "incoming_edge_count_min": min(incoming_counts),
            "incoming_edge_count_max": max(incoming_counts),
            "status_counts": dict(sorted(status_counts.items())),
            "sample_lifts": [_lift_payload(row) for row in sampled_rows],
        },
        "unit_translation": _translation_pairs(
            rows,
            evidence=evidence,
            pair_limit=int(translation_pair_limit),
            edge_limit=int(edge_limit),
        ),
        "finite_return_cycle": cyclotomic_closure_payload(
            phase,
            cycle_point_limit=int(cycle_point_limit),
        ),
    }


def _claim_boundary() -> Dict[str, object]:
    return {
        "evidence_layer": "external_exact_quotient_over_strict_graph",
        "claim_status": "exploratory_observation",
        "allowed_claim_language": [
            "The rational residue map exactly partitions observed graph nodes into Q/Z phase fibres.",
            "Nodes in one reported fibre differ by integer lifts and map to one U(1) phase under the external exponential map.",
            "Recorded +1 edges show which same-phase lift translations are actually witnessed by the selected strict corpus.",
            "A reduced phase p/q has external additive return order q, and its complete root-of-unity orbit satisfies the finite geometric cancellation identity.",
        ],
        "disallowed_claim_language": [
            "Do not claim that the strict MoO runtime contains a circle, U(1), complex numbers, or a completed quotient space.",
            "Do not identify phase-fibre multiplicity with construction-witness multiplicity without an explicit representation map.",
            "Do not treat an external q-step phase cycle as graph-witnessed when rational nodes are not operands.",
            "Do not claim that return to the identity point proves the remembered lift or winding count with Order-1 certainty.",
            "Do not infer circle structure from cycles alone; path composition and path equivalence are not yet MoO runtime semantics.",
        ],
        "interpretation_limits": [
            "Q/Z is a countable dense subgroup of R/Z, not the completed circle by itself.",
            "The quotient preserves rational phase and discards integer lift; the graph may retain lift-dependent provenance outside the quotient.",
            "The cyclotomic geometric-series identity is standard external algebra used as a testable framing relation.",
            "The current positive-spine rule generally blocks +1 translation edges whose left operand is a speculative rational node.",
        ],
    }


def _validate_limits(
    *,
    max_denominator: int,
    max_phase_classes: int,
    sample_lifts: int,
    translation_pair_limit: int,
    cycle_point_limit: int,
    full_scan: bool,
) -> None:
    if full_scan:
        return
    limits = [
        ("max_denominator", int(max_denominator), MAX_DENOMINATOR),
        ("max_phase_classes", int(max_phase_classes), MAX_PHASE_CLASSES),
        ("sample_lifts", int(sample_lifts), MAX_SAMPLE_LIFTS),
        ("translation_pair_limit", int(translation_pair_limit), MAX_TRANSLATION_PAIRS),
        ("cycle_point_limit", int(cycle_point_limit), MAX_CYCLE_POINTS),
    ]
    exceeded = [f"{name}>{cap}" for name, value, cap in limits if value > cap]
    if exceeded:
        raise ValueError(
            "probe safety limit exceeded ("
            + ", ".join(exceeded)
            + "); pass --full-scan to acknowledge the larger query"
        )


def circle_as_one_probe(
    *,
    db_path: Path,
    max_denominator: int,
    max_phase_classes: int,
    sample_lifts: int,
    translation_pair_limit: int,
    edge_limit: int,
    cycle_point_limit: int,
    full_scan: bool = False,
) -> Dict[str, object]:
    _validate_limits(
        max_denominator=int(max_denominator),
        max_phase_classes=int(max_phase_classes),
        sample_lifts=int(sample_lifts),
        translation_pair_limit=int(translation_pair_limit),
        cycle_point_limit=int(cycle_point_limit),
        full_scan=bool(full_scan),
    )
    with closing(connect_readonly(Path(db_path))) as conn:
        alignment = require_strict_alignment(conn)
        corpus = _corpus_payload(conn, alignment=alignment)
        latest = corpus["latest_stage"]
        corpus_stage = int(latest["stage"]) if isinstance(latest, dict) else None
        evidence = GraphEvidence(conn, corpus_stage=corpus_stage)
        node_rows = _phase_node_rows(
            conn,
            max_denominator=int(max_denominator),
        )
        classes: Dict[Key, List[sqlite3.Row]] = {}
        for row in node_rows:
            phase_key = _key(phase_fraction(_row_value(row)))
            classes.setdefault(phase_key, []).append(row)

        identity_key = (0, 1)
        ordered_keys = sorted(
            classes,
            key=lambda key: (
                0 if key == identity_key else 1,
                -len(classes[key]),
                int(key[1]),
                int(key[0]),
            ),
        )
        selected_keys = ordered_keys[: int(max_phase_classes)]
        class_payloads = [
            _phase_class_payload(
                key,
                classes[key],
                evidence=evidence,
                sample_lifts=int(sample_lifts),
                translation_pair_limit=int(translation_pair_limit),
                edge_limit=int(edge_limit),
                cycle_point_limit=int(cycle_point_limit),
            )
            for key in selected_keys
        ]

    class_sizes = [len(rows) for rows in classes.values()]
    order_histogram = Counter(
        additive_return_order(Fraction(key[0], key[1])) for key in classes
    )
    expected_order_histogram = {
        order: euler_totient(order)
        for order in range(1, int(max_denominator) + 1)
    }
    expected_phase_classes = sum(expected_order_histogram.values())
    complete_return_orders = [
        order
        for order, expected in expected_order_histogram.items()
        if int(order_histogram.get(order, 0)) == int(expected)
    ]
    identity_lifts = len(classes.get(identity_key, []))
    return {
        "report_type": "circle_as_one_rational_quotient_probe",
        "config": {
            "max_denominator": int(max_denominator),
            "max_phase_classes": int(max_phase_classes),
            "sample_lifts": int(sample_lifts),
            "translation_pair_limit": int(translation_pair_limit),
            "edge_limit": int(edge_limit),
            "cycle_point_limit": int(cycle_point_limit),
            "full_scan": bool(full_scan),
        },
        "claim_boundary": _claim_boundary(),
        "foundation": {
            "proposal": (
                "The number 1 is the full-turn return and multiplicative identity; "
                "the circle model is the quotient generated by identifying x and x+1."
            ),
            "quotient": "Q/Z embeds as the roots of unity in R/Z ~= U(1)",
            "exact_phase_map": "p/q -> (p mod q)/q -> exp(2*pi*i*p/q)",
            "kernel": "Z",
            "fibre": "phase + Z",
            "identity_point": "all integers map to 1 in U(1)",
            "lost_information": "integer lift / winding count",
            "retained_graph_information": (
                "node identity, first stage, confirmation status, incoming edge "
                "history, and any witnessed translations"
            ),
            "operation_descent": {
                "addition": (
                    "well-defined on Q/Z; under the exponential map, phase "
                    "addition becomes multiplication in U(1)"
                ),
                "subtraction": (
                    "well-defined on Q/Z; under the exponential map, phase "
                    "subtraction becomes multiplication by an inverse"
                ),
                "multiplication": (
                    "not well-defined on Q/Z in general: 1/2 and 3/2 are "
                    "equivalent, but multiplying both by 1/2 gives inequivalent "
                    "phases 1/4 and 3/4"
                ),
                "division": (
                    "not well-defined on Q/Z in general: dividing the same "
                    "equivalent pair by 2 gives inequivalent phases 1/4 and 3/4"
                ),
            },
        },
        "corpus": corpus,
        "summary": {
            "scanned_nodes": len(node_rows),
            "observed_phase_classes": len(classes),
            "reported_phase_classes": len(class_payloads),
            "identity_lifts": int(identity_lifts),
            "nonidentity_phase_classes": len(classes) - (1 if identity_key in classes else 0),
            "multi_lift_phase_classes": sum(size > 1 for size in class_sizes),
            "maximum_observed_fibre_size": max(class_sizes) if class_sizes else 0,
            "expected_reduced_phase_classes_through_denominator": int(
                expected_phase_classes
            ),
            "phase_class_coverage": (
                len(classes) / expected_phase_classes
                if expected_phase_classes
                else None
            ),
            "return_order_histogram": {
                str(order): int(count)
                for order, count in sorted(order_histogram.items())
            },
            "expected_return_order_histogram": {
                str(order): int(count)
                for order, count in expected_order_histogram.items()
            },
            "complete_return_orders": complete_return_orders,
        },
        "phase_classes": class_payloads,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Project strict MoO rational nodes into exact Q/Z phase fibres, "
            "with 1 as the full-turn return point, and inspect retained graph evidence."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--max-denominator", type=positive_int, default=12)
    parser.add_argument("--max-phase-classes", type=positive_int, default=24)
    parser.add_argument("--sample-lifts", type=positive_int, default=6)
    parser.add_argument("--translation-pair-limit", type=positive_int, default=6)
    parser.add_argument("--edge-limit", type=positive_int, default=4)
    parser.add_argument("--cycle-point-limit", type=positive_int, default=24)
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
    payload = circle_as_one_probe(
        db_path=Path(args.db),
        max_denominator=int(args.max_denominator),
        max_phase_classes=int(args.max_phase_classes),
        sample_lifts=int(args.sample_lifts),
        translation_pair_limit=int(args.translation_pair_limit),
        edge_limit=int(args.edge_limit),
        cycle_point_limit=int(args.cycle_point_limit),
        full_scan=bool(args.full_scan),
    )
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_circle_as_one_probe.v1",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
