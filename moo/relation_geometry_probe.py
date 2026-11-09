"""Bounded exact inspection of the seven-step unit-distance relation.

This external geometry lens changes direction selection, not the MoO runtime.
The search never exceeds ten generators or 1,024 binary construction paths.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from math import log2
from pathlib import Path
from moo.paths import PROJECT_ROOT

from moo.unit_direction_branch_probe import (
    Pair, count_subset_geometry, triangular_generators, unit_shell,
)

DELTA: Pair = (112359, -250588)
FIRST_TURN: Pair = (37700, -272025)
SECOND_TURN: Pair = (30420, 272935)
COUNT_FIELDS = (
    "generator_count", "raw_subset_paths", "distinct_points",
    "duplicate_subset_paths", "coordinate_flip_occurrences",
    "distinct_coordinate_flip_edges", "distinct_unit_pairs", "extra_unit_pairs",
)


def brief(result: dict) -> dict:
    n, e = result["distinct_points"], result["distinct_unit_pairs"]
    return {
        **{key: result[key] for key in COUNT_FIELDS},
        "average_degree_exact": str(Fraction(2 * e, n)),
        "copying_remainder_approx": 2 * e / n - log2(n),
    }


def exact_graph_audit(generators: list[Pair], result: dict) -> dict:
    """Rebuild all subset sums and test every pair without the unit shell."""
    d = result["denominator"]
    if not 1 <= len(generators) <= 10:
        raise ValueError("audit requires between one and ten generators")
    by_mask = [
        tuple(sum(g[j] for k, g in enumerate(generators) if mask >> k & 1)
              for j in (0, 1))
        for mask in range(1 << len(generators))
    ]
    points = sorted(set(by_mask))
    direct_edges = {
        (p, q) for p, q in combinations(points, 2)
        if (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 == d * d
    }
    flip_counts: Counter = Counter()
    for mask, point in enumerate(by_mask):
        for j in range(len(generators)):
            if not mask >> j & 1:
                flip_counts[tuple(sorted((point, by_mask[mask | (1 << j)])))] += 1

    graph = result["point_graph"]
    coords = {row[0]: tuple(row[1:3]) for row in graph["points"]}
    reported_edges = set()
    for source, target, dx, dy, count in graph["unit_edges"]:
        p, q = coords[source], coords[target]
        assert (q[0] - p[0], q[1] - p[1]) == (dx, dy)
        edge = tuple(sorted((p, q)))
        assert count == flip_counts[edge]
        reported_edges.add(edge)
    assert len(reported_edges) == len(graph["unit_edges"])
    assert direct_edges == reported_edges
    assert len(points) == len(coords) == result["distinct_points"]
    assert set(points) == set(coords.values())
    reported_masks = [mask for row in graph["points"] for mask in row[3]]
    assert sorted(reported_masks) == list(range(len(by_mask)))
    for point_id, x, y, masks in graph["points"]:
        assert all(by_mask[mask] == (x, y) for mask in masks)
    assert len(flip_counts) == result["distinct_coordinate_flip_edges"]
    assert sum(flip_counts.values()) == result["coordinate_flip_occurrences"]
    assert set(flip_counts).issubset(direct_edges)
    assert len(direct_edges) == result["distinct_unit_pairs"]
    assert len(direct_edges - flip_counts.keys()) == result["extra_unit_pairs"]
    return {
        "method": "independent direct subset sums and squared-distance tests; no shell",
        "unordered_pairs_tested": len(points) * (len(points) - 1) // 2,
        "distinct_points": len(points),
        "distinct_unit_pairs": len(direct_edges),
        "complete_edge_sets_match": True,
        "all_coordinate_flip_multiplicities_match": True,
        "all_subset_occurrences_match": True,
    }


def signed_terms(first: int, second: int, width: int) -> tuple:
    return tuple((j, ((second >> j) & 1) - ((first >> j) & 1))
                 for j in range(width) if (first ^ second) >> j & 1)


def relation_audit(generators: list[Pair], result: dict) -> dict:
    """Keep all endpoint witnesses, including overlaps between relations."""
    graph = result["point_graph"]
    masks = {row[0]: row[3] for row in graph["points"]}
    mask_point = {mask: point for point, occurrences in masks.items() for mask in occurrences}
    coords = {row[0]: tuple(row[1:3]) for row in graph["points"]}
    patterns: dict[tuple, set] = defaultdict(set)
    extra_edges = set()
    for source, target, dx, dy, count in graph["unit_edges"]:
        if count:
            continue
        edge = tuple(sorted((source, target)))
        extra_edges.add(edge)
        for first in masks[source]:
            for second in masks[target]:
                patterns[signed_terms(first, second, len(generators))].add(edge)

    families = []
    edge_sets = []
    for pattern, observed in sorted(patterns.items(), key=lambda item: (len(item[0]), item[0])):
        displacement = tuple(sum(c * generators[j][axis] for j, c in pattern)
                             for axis in (0, 1))
        assert sum(c * c for c in displacement) == result["denominator"] ** 2
        support = dict(pattern)
        free = [j for j in range(len(generators)) if j not in support]
        source_mask = sum(1 << j for j, c in pattern if c == -1)
        target_mask = sum(1 << j for j, c in pattern if c == 1)
        translated = []
        for bits in range(1 << len(free)):
            shift = sum(1 << j for k, j in enumerate(free) if bits >> k & 1)
            source, target = mask_point[source_mask | shift], mask_point[target_mask | shift]
            p, q = coords[source], coords[target]
            assert (q[0] - p[0], q[1] - p[1]) == displacement
            translated.append(tuple(sorted((source, target))))
        translated_set = set(translated)
        assert translated_set == observed
        edge_sets.append(translated_set)
        families.append({
            "signed_generator_terms": pattern,
            "support_size": len(pattern),
            "free_generator_indices": free,
            "scaled_displacement": displacement,
            "rational_displacement": [str(Fraction(c, result["denominator"]))
                                      for c in displacement],
            "translation_occurrences": len(translated),
            "distinct_edges": len(translated_set),
            "point_id_pairs": sorted(translated_set),
        })
    overlaps = []
    for i, j in combinations(range(len(edge_sets)), 2):
        shared = edge_sets[i] & edge_sets[j]
        if shared:
            overlaps.append({"family_indices": [i, j], "shared_edges": len(shared),
                             "point_id_pairs": sorted(shared)})
    assert set().union(*edge_sets) == extra_edges

    mergers = []
    for point, occurrences in masks.items():
        if len(occurrences) > 1:
            witnesses = [signed_terms(occurrences[0], other, len(generators))
                         for other in occurrences[1:]]
            for pattern in witnesses:
                assert all(sum(c * generators[j][axis] for j, c in pattern) == 0
                           for axis in (0, 1))
            mergers.append({"point_id": point, "subset_masks": occurrences,
                            "zero_relation_witnesses": witnesses})
    duplicated_edges = [row for row in graph["unit_edges"] if row[4] > 1]
    return {
        "relation_families": families,
        "pairwise_family_overlaps": overlaps,
        "union_distinct_extra_edges": len(extra_edges),
        "merged_points": mergers,
        "coordinate_edges_with_multiple_witnesses": duplicated_edges,
        "coordinate_edge_occurrence_loss": sum(row[4] - 1 for row in duplicated_edges),
        "interpretation": "Translation families can overlap and need not be algebraically independent.",
    }


def extension_scan(generators: list[Pair], denominator: int, shell: set[Pair]) -> list[dict]:
    rows = []
    candidates = sorted(p for p in shell if p[0] > 0 or (p[0] == 0 and p[1] > 0))
    for candidate in candidates:
        result = count_subset_geometry(generators + [candidate], denominator, shell)
        rows.append({"added_scaled_direction": candidate, **brief(result)})
    return sorted(rows, key=lambda row: (
        -row["copying_remainder_approx"],
        -Fraction(row["average_degree_exact"]), row["added_scaled_direction"],
    ))


def parametric_direction_check() -> dict:
    """Check the exact rational continuation; no growing point sets are built."""
    def multiply(z, w):
        return z[0] * w[0] - z[1] * w[1], z[0] * w[1] + z[1] * w[0]

    current = (Fraction(1), Fraction(0))
    rows = []
    longer_relation_residuals = []
    for n in range(13):
        denominator = 2 * n * n + 2 * n + 1
        expected = (Fraction(2 * n + 1, denominator),
                    Fraction(2 * n * (n + 1), denominator))
        assert current == expected
        assert sum(c * c for c in current) == 1
        rows.append({"n": n, "real": str(current[0]), "imaginary": str(current[1])})
        # T(z) = (1 + (1+i)*z)/(z + 1-i).
        product = multiply((1, 1), current)
        numerator = (1 + product[0], product[1])
        divisor = (current[0] + 1, current[1] - 1)
        norm = sum(c * c for c in divisor)
        following = tuple(c / norm for c in multiply(numerator, (divisor[0], -divisor[1])))
        uv = multiply(current, following)
        iu = multiply((1, 1), current)
        iv = multiply((1, -1), following)
        assert (uv[0] - iu[0] + iv[0] - 1, uv[1] - iu[1] + iv[1]) == (0, 0)
        u2 = multiply(current, current)
        u3 = multiply(u2, current)
        v2 = multiply(following, following)
        u2v = multiply(u2, following)
        uv2 = multiply(current, v2)
        u3v2 = multiply(u3, v2)
        residual = tuple(-(1 if axis == 0 else 0) - u2[axis] + uv[axis] - v2[axis]
                         - u3[axis] + u2v[axis] - uv2[axis] - u3v2[axis]
                         for axis in (0, 1))
        longer_relation_residuals.append({
            "n": n, "real": str(residual[0]), "imaginary": str(residual[1]),
            "zero_relation_holds": residual == (0, 0),
        })
        current = following
    return {
        "map": "T(z)=(1+(1+i)*z)/(z+1-i)",
        "start": "1",
        "exact_iterate": "T^n(1)=(n+1+n*i)/(n+1-n*i)",
        "checked_iterates": rows,
        "direction_limit": "i",
        "exact_squared_distance_to_i": "2/(2*n*n+2*n+1)",
        "longer_relation": "-1-u^2+u*v-v^2-u^3+u^2*v-u*v^2-u^3*v^2",
        "longer_relation_residuals": longer_relation_residuals,
        "scope": "direction convergence only; no point-count or unit-pair growth conclusion",
    }


def build_report() -> dict:
    if not __debug__:
        raise RuntimeError("run the evidence checks without Python's -O option")
    denominator, _, original = triangular_generators(3)
    shell = unit_shell(3, 3)
    support_indices = (0, 3, 4, 5, 6, 7, 8)
    seven = [original[j] for j in support_indices]
    closed = seven + [DELTA]
    first_scan = extension_scan(closed, denominator, shell)
    top_counts = (first_scan[0]["distinct_points"], first_scan[0]["distinct_unit_pairs"])
    tied = [row for row in first_scan
            if (row["distinct_points"], row["distinct_unit_pairs"]) == top_counts]
    assert len(tied) == 2
    second_scans = [{
        "first_added_scaled_direction": row["added_scaled_direction"],
        "candidates": extension_scan(closed + [row["added_scaled_direction"]], denominator, shell),
    } for row in tied]
    assert first_scan[0]["added_scaled_direction"] == FIRST_TURN
    assert second_scans[0]["candidates"][0]["added_scaled_direction"] == SECOND_TURN
    specs = [
        ("original_depth_3", original),
        ("seven_relation_directions", seven),
        ("seven_plus_u_copy_control", seven + [original[1]]),
        ("closed_eight", closed),
        ("closed_eight_plus_u", closed + [original[1]]),
        ("closed_eight_plus_u_v", closed + [original[1], original[2]]),
        ("first_quarter_turn", closed + [FIRST_TURN]),
        ("chosen_two_quarter_turns", closed + [FIRST_TURN, SECOND_TURN]),
    ]
    cases = []
    for name, generators in specs:
        result = count_subset_geometry(generators, denominator, shell, retain_graph=True)
        cases.append({"name": name, "scaled_generators": generators,
                      "summary": brief(result), "geometry": result,
                      "independent_audit": exact_graph_audit(generators, result),
                      "relation_audit": relation_audit(generators, result)})
    chosen = cases[-1]
    assert (chosen["summary"]["distinct_points"], chosen["summary"]["distinct_unit_pairs"]) == (1020, 5188)
    assert [r["distinct_edges"] for r in chosen["relation_audit"]["relation_families"]] == [32, 32, 8, 2]
    source_names = ('moo/relation_geometry_probe.py', 'moo/unit_direction_branch_probe.py',
                    'moo/quadratic_form_probe.py')
    root = PROJECT_ROOT
    return {
        "schema_version": 1,
        "date": "2026-09-11",
        "evidence_layer": "external_pair_geometry",
        "claim_status": "checked finite comparison, no extremal or asymptotic certificate",
        "source_sha256": {name: sha256((root / name).read_bytes()).hexdigest() for name in source_names},
        "denominator": denominator,
        "ambient_oriented_unit_directions": len(shell),
        "fixed_lattice_bound": "E <= 98*N for any finite point set in this denominator lattice",
        "search_protocol": {
            "kind": "exploratory bounded greedy selection, after observing the seven-step relation",
            "max_binary_paths": 1024,
            "candidate_unoriented_directions": len(first_scan),
            "candidate_extensions_evaluated": len(first_scan) + sum(len(s["candidates"]) for s in second_scans),
            "existing_generators_included_as_controls": True,
            "ranking": "descending approximate 2E/N-log2(N), then exact average degree, then coordinates",
            "first_tie_policy": "follow both first-stage candidates with the winning exact (N,E)",
            "coverage_limit": "not an exhaustive search of all candidate pairs or all point sets",
            "first_stage_candidates": first_scan,
            "second_stage_branches": second_scans,
        },
        "cases": cases,
        "chosen_generator_labels": ["1", "u^2", "u*v", "v^2", "u^3", "u^2*v", "u*v^2",
                                    "u^3*v^2", "i*u*v^2", "-i*u^2*v"],
        "generic_copying_control": {
            "hypothesis": "P and P+w disjoint, matching cross-pairs only; choose fresh nonexceptional unit w",
            "point_recurrence": "N_next=2*N", "edge_recurrence": "E_next=2*E+N",
            "invariant": "2*E/N-log2(N)", "limiting_log_E_over_log_N": 1,
            "rational_directions_possible": True,
        },
        "parametric_relation": {
            "hypothesis": "abs(u)=1; v=(1+(1+i)*u)/(u+1-i)",
            "identity": "u*v-(1+i)*u+(1-i)*v-1=0",
            "unit_proof": "numerator = u*conjugate(denominator); denominator never zero on unit circle",
            "scope": "explains one short relation, not all relations or the full finite gain",
        },
        "parametric_direction_continuation": parametric_direction_check(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new report path; refuses existing files")
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error("output already exists; choose a new versioned filename")
    report = build_report()
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    print(json.dumps({"cases": [{"name": c["name"], **c["summary"]} for c in report["cases"]],
                      "candidate_extensions_evaluated": report["search_protocol"]["candidate_extensions_evaluated"],
                      "output": str(args.output) if args.output else None}, indent=2))


if __name__ == "__main__":
    main()
