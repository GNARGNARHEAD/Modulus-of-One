"""Bounded exact gate for a fixed-seed, norm-one branch construction.

The pair algebra is an external geometry lens. A separate, small MoO graph
records the integer shell and ratio witnesses; speculative ratios are never
used as operands in that graph. No core runtime or corpus is changed.
"""

from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import json
from math import log
from pathlib import Path
from typing import Sequence

from moo.constructionist_math import Graph
from moo.quadratic_form_probe import gaussian_multiply, gaussian_norm, quarter_turn

Pair = tuple[int, int]
Powers = tuple[int, int]
MAX_SUBSET_PATHS = 1024


def pair_power(pair: Pair, exponent: int) -> Pair:
    if type(exponent) is not int or exponent < 0:
        raise ValueError("exponent must be a nonnegative integer")
    result = (1, 0)
    for _ in range(exponent):
        result = gaussian_multiply(result, pair)
    return result


def unit_shell(k5: int, k13: int) -> set[Pair]:
    """All integer (x,y) with x*x+y*y=(5**k5 * 13**k13)**2.

    Gaussian unique factorization gives this complete list, including all
    signs and quarter turns, not just the selected construction directions.
    """
    for exponent in (k5, k13):
        if type(exponent) is not int or not 0 <= exponent <= 10:
            raise ValueError("shell exponents must be integers between 0 and 10")
    directions: set[Pair] = set()
    for j in range(2 * k5 + 1):
        five = gaussian_multiply(pair_power((2, 1), j),
                                 pair_power((2, -1), 2 * k5 - j))
        for ell in range(2 * k13 + 1):
            thirteen = gaussian_multiply(pair_power((3, 2), ell),
                                         pair_power((3, -2), 2 * k13 - ell))
            pair = gaussian_multiply(five, thirteen)
            for _ in range(4):
                directions.add(pair)
                pair = quarter_turn(pair)
    return directions


def triangular_generators(depth: int) -> tuple[int, list[Powers], list[Pair]]:
    """V_k = {u**a v**b : a,b >= 0, a+b <= k}, scaled by D=65**k."""
    if type(depth) is not int or not 0 <= depth <= 3:
        raise ValueError("this bounded gate permits depths 0 through 3")
    denominator = 65 ** depth
    powers = [(a, total - a) for total in range(depth + 1)
              for a in range(total, -1, -1)]
    generators = []
    for a, b in powers:
        x, y = gaussian_multiply(pair_power((3, 4), a), pair_power((5, 12), b))
        scale = denominator // (5 ** a * 13 ** b)
        generators.append((scale * x, scale * y))
    return denominator, powers, generators


def count_subset_geometry(
    generators: Sequence[Pair], denominator: int, shell: set[Pair],
    *, retain_graph: bool = False,
) -> dict:
    """Count geometric points/pairs, retaining duplicate construction paths.

    Every subset mask is an occurrence, while equal coordinates share one
    point ID. Coordinate-flip witnesses are counted separately from unique
    geometric edges. The caller supplies the complete denominator-lattice
    unit shell; use unit_shell for this experiment's denominators.
    """
    if type(denominator) is not int or denominator < 1:
        raise ValueError("denominator must be a positive integer")
    if not generators or 2 ** len(generators) > MAX_SUBSET_PATHS:
        raise ValueError("use between 1 and 10 generators in this bounded gate")
    if any(type(c) is not int for pair in [*generators, *shell] for c in pair):
        raise ValueError("scaled coordinates must be exact integers")
    squared_radius = denominator ** 2
    if any(gaussian_norm(pair) != squared_radius for pair in [*generators, *shell]):
        raise ValueError("all generators and shell vectors must have length one")
    if not set(generators).issubset(shell):
        raise ValueError("the shell must include every generator")
    if any((-x, -y) not in shell for x, y in shell):
        raise ValueError("the shell must include opposite directions")

    points = [(0, 0)]
    point_ids = {(0, 0): 0}
    mask_to_point = [0]
    addition_occurrences = []
    for j, (dx, dy) in enumerate(generators):
        for mask in range(1 << j):
            source = mask_to_point[mask]
            x, y = points[source]
            target_pair = (x + dx, y + dy)
            if target_pair not in point_ids:
                point_ids[target_pair] = len(points)
                points.append(target_pair)
            target = point_ids[target_pair]
            mask_to_point.append(target)
            if retain_graph:
                addition_occurrences.append([source, j, target, mask, mask | (1 << j)])

    masks_by_point: list[list[int]] = [[] for _ in points]
    for mask, point_id in enumerate(mask_to_point):
        masks_by_point[point_id].append(mask)

    flip_counts: Counter[tuple[int, int]] = Counter()
    for j in range(len(generators)):
        bit = 1 << j
        for mask, source in enumerate(mask_to_point):
            if not mask & bit:
                target = mask_to_point[mask | bit]
                flip_counts[tuple(sorted((source, target)))] += 1

    edges = []
    extras = []
    used_directions = set()
    forward = sorted((x, y) for x, y in shell if x > 0 or (x == 0 and y > 0))
    for source, (x, y) in enumerate(points):
        for dx, dy in forward:
            target = point_ids.get((x + dx, y + dy))
            if target is None:
                continue
            key = tuple(sorted((source, target)))
            witnesses = flip_counts[key]
            row = [source, target, dx, dy, witnesses]
            edges.append(row)
            used_directions.add((dx, dy))
            if not witnesses:
                source_mask, target_mask = masks_by_point[source][0], masks_by_point[target][0]
                signed_terms = [[j, ((target_mask >> j) & 1) - ((source_mask >> j) & 1)]
                                for j in range(len(generators))
                                if (source_mask ^ target_mask) & (1 << j)]
                extras.append({
                    "point_ids": [source, target],
                    "subset_masks": [source_mask, target_mask],
                    "scaled_displacement": [dx, dy],
                    "rational_displacement": [str(Fraction(dx, denominator)),
                                              str(Fraction(dy, denominator))],
                    "signed_generator_terms": signed_terms,
                })

    result = {
        "denominator": denominator,
        "generator_count": len(generators),
        "raw_subset_paths": len(mask_to_point),
        "distinct_points": len(points),
        "duplicate_subset_paths": len(mask_to_point) - len(points),
        "max_paths_at_one_point": max(map(len, masks_by_point)),
        "coordinate_flip_occurrences": sum(flip_counts.values()),
        "distinct_coordinate_flip_edges": len(flip_counts),
        "distinct_unit_pairs": len(edges),
        "extra_unit_pairs": len(extras),
        "ambient_oriented_unit_directions": len(shell),
        "used_unoriented_unit_directions": len(used_directions),
        "finite_log_E_over_log_N_approx": log(len(edges)) / log(len(points)),
        "extra_pair_witnesses": extras,
    }
    if retain_graph:
        result["point_graph"] = {
            "evidence_layer": "external_pair_geometry",
            "coordinates": "integer pairs divided by denominator",
            "point_columns": ["point_id", "scaled_x", "scaled_y", "subset_masks"],
            "points": [[j, x, y, masks_by_point[j]] for j, (x, y) in enumerate(points)],
            "addition_occurrence_columns": ["source", "generator", "target",
                                             "input_subset_mask", "output_subset_mask"],
            "addition_occurrences": addition_occurrences,
            "unit_edge_columns": ["source", "target", "scaled_dx", "scaled_dy",
                                  "coordinate_flip_witness_count"],
            "unit_edges": edges,
        }
    return result


def two_seed_stage(depth: int, *, retain_graph: bool = False) -> dict:
    denominator, powers, generators = triangular_generators(depth)
    result = count_subset_geometry(generators, denominator, unit_shell(depth, depth),
                                   retain_graph=retain_graph)
    ids = {power: j for j, power in enumerate(powers)}
    direction_edges = []
    for j, (a, b) in enumerate(powers):
        if a:
            direction_edges.append([ids[(a - 1, b)], "u", j])
        if b:
            direction_edges.append([ids[(a, b - 1)], "v", j])
    result.update({
        "depth": depth,
        "direction_node_columns": ["direction_id", "u_power", "v_power", "scaled_x", "scaled_y"],
        "direction_nodes": [[j, a, b, *generators[j]] for j, (a, b) in enumerate(powers)],
        "direction_edge_columns": ["input_direction_id", "multiply_by_seed", "output_direction_id"],
        "direction_construction_edges": direction_edges,
        "analytic_unit_pair_upper_bound": 2 * result["distinct_points"] * (2 * depth + 1) ** 2,
    })
    return result


def single_seed_stage(length: int) -> dict:
    if type(length) is not int or not 1 <= length <= 10:
        raise ValueError("the control permits lengths 1 through 10")
    denominator = 5 ** (length - 1)
    generators = [tuple(c * (denominator // 5 ** j) for c in pair_power((3, 4), j))
                  for j in range(length)]
    result = count_subset_geometry(generators, denominator, unit_shell(length - 1, 0))
    result.update({
        "length": length,
        "predicted_points": 2 ** length,
        "predicted_unit_pairs": length * 2 ** (length - 1),
        "matches_exact_formula": (result["distinct_points"], result["distinct_unit_pairs"])
        == (2 ** length, length * 2 ** (length - 1)),
    })
    return result


def collision_witness() -> dict:
    """Check one later-stage collision directly, without enumerating P_5.

    This consequence was extracted from the eight extra P_3 edges; it is
    follow-up evidence, not a preregistered independent discovery.
    """
    left = [(1, 1), (2, 1)]
    right = [(0, 0), (2, 0), (0, 2), (3, 0), (1, 2), (3, 2)]
    denominator = 65 ** 5

    def total(terms: list[Powers]) -> Pair:
        x = y = 0
        for a, b in terms:
            dx, dy = gaussian_multiply(pair_power((3, 4), a), pair_power((5, 12), b))
            scale = denominator // (5 ** a * 13 ** b)
            x, y = x + scale * dx, y + scale * dy
        return x, y

    lhs, rhs = total(left), total(right)
    return {
        "first_stage_containing_all_terms": 5,
        "left_subset_exponents": left,
        "right_subset_exponents": right,
        "denominator": denominator,
        "left_scaled_coordinates": lhs,
        "right_scaled_coordinates": rhs,
        "verified_equal": lhs == rhs,
        "full_stage_enumerated": False,
    }


def moo_seed_calibration() -> dict:
    """Actual scalar construction edges, with strict operand eligibility."""
    graph = Graph(max_nodes=180, operation_budget=185)
    graph.advance_frontier_max_to(13)
    squares = {}
    for n in (3, 4, 5, 12, 13):
        operand = graph.get_or_create_ref(n)
        result = graph.mul(operand, operand)
        squares[n] = {
            "input_uid": operand.node_uid, "output_uid": result.node_uid,
            "edge_uid": graph.edges[-1].edge_uid,
            "output_status_when_squared": result.status,
        }
    graph.advance_frontier_max_to(169)
    shells = []
    for a, b, radius in ((3, 4, 5), (5, 12, 13)):
        result = graph.add(graph.get_or_create_ref(a * a), graph.get_or_create_ref(b * b))
        shells.append({
            "integer_shell": [a, b, radius],
            "square_edge_uids": [squares[a]["edge_uid"], squares[b]["edge_uid"],
                                 squares[radius]["edge_uid"]],
            "sum_edge_uid": graph.edges[-1].edge_uid,
            "common_squared_radius_uid": result.node_uid,
            "matches_radius_square": result.node_uid == squares[radius]["output_uid"],
        })
    ratios = []
    for numerator, denominator in ((3, 5), (4, 5), (5, 13), (12, 13)):
        result = graph.div(graph.get_or_create_ref(numerator), graph.get_or_create_ref(denominator))
        ratios.append({"value": [numerator, denominator], "node_uid": result.node_uid,
                       "edge_uid": graph.edges[-1].edge_uid, "status": result.status})
    return {
        "evidence_layer": "positive_spine_scalar_witness_graph",
        "frontier": graph.frontier(),
        "allow_speculative_operands": graph.allow_speculative_operands,
        "limits": {"max_nodes": 180, "operation_budget": 185},
        "square_witnesses": squares,
        "shell_witnesses": shells,
        "ratio_outputs": ratios,
        "interpretation": "Integer shell edges and speculative ratio outputs only. "
        "Complex products, subset sums, and geometric distances belong to the external lens.",
        "graph": graph.to_jsonable(),
    }


def build_report(max_depth: int = 3, max_control_length: int = 10) -> dict:
    # Validate limits before any construction, including the calibration graph.
    triangular_generators(max_depth)
    if type(max_control_length) is not int or not 1 <= max_control_length <= 10:
        raise ValueError("control length must be an integer between 1 and 10")
    return {
        "schema": "moo_fixed_seed_unit_direction_gate_v1",
        "rule": {"u": ["3/5", "4/5"], "v": ["5/13", "12/13"],
                 "directions": "u^a v^b, a,b >= 0, a+b <= k",
                 "points": "distinct binary subset sums of those directions",
                 "distance": "exact Euclidean unit distance; unordered distinct point pairs"},
        "limits": {"max_depth": max_depth, "max_control_length": max_control_length,
                   "max_subset_paths_per_stage": MAX_SUBSET_PATHS},
        "two_seed_stages": [two_seed_stage(k, retain_graph=(k == max_depth))
                            for k in range(max_depth + 1)],
        "single_seed_control": [single_seed_stage(m) for m in range(1, max_control_length + 1)],
        "later_collision_witness": collision_witness(),
        "moo_seed_calibration": moo_seed_calibration(),
        "analytic_conclusions": {
            "single_seed": "N_m=2^m; E_m=m*2^(m-1) exactly for every m>=1",
            "two_seed": "N_k>=2^(k+1); N_k-1<=E_k<=2*N_k*(2*k+1)^2",
            "limiting_log_E_over_log_N": 1,
            "scope": "These specified fixed-seed families; no global unit-distance upper bound",
            "decision": "Stop scaling these fixed seeds to seek a positive power gain. "
            "Retain the local relation; a successor must change the structural growth mechanism.",
            "proof_location": "research/geometry/erdos_unit_distance/FIXED_SEED_BRANCH_GATE_NOTE.md",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-depth", type=int, choices=range(4), default=3)
    parser.add_argument("--control-length", type=int, choices=range(1, 11), default=10)
    parser.add_argument("--output", type=Path, help="new versioned JSON path; existing files are refused")
    args = parser.parse_args()
    report = build_report(args.max_depth, args.control_length)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
    summary = {
        "two_seed_stages": [{key: row[key] for key in (
            "depth", "generator_count", "raw_subset_paths", "distinct_points",
            "distinct_unit_pairs", "extra_unit_pairs", "duplicate_subset_paths")}
            for row in report["two_seed_stages"]],
        "all_single_seed_controls_match": all(row["matches_exact_formula"]
                                               for row in report["single_seed_control"]),
        "later_collision_verified": report["later_collision_witness"]["verified_equal"],
        "limiting_exponent_of_specified_families": 1,
        "output": str(args.output) if args.output else None,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
