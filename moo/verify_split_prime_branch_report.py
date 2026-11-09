"""Audit the frozen three-field report using independent radical arithmetic.

No imports from the probe or its tests. The calculation uses the basis
1, sqrt(2), sqrt(3), sqrt(6), i, i*sqrt(2), i*sqrt(3), i*sqrt(6), and obtains
factor ratios by solving division equations. Completeness and infinite-tail
claims still require the mathematical arguments in the research note.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction as F
from hashlib import sha256
from itertools import combinations, product
import json
from math import gcd, isqrt, prod
from pathlib import Path
from moo.paths import PROJECT_ROOT

Radical = tuple[F, ...]
PRIME = 241
ZERO = (F(0),) * 8
ONE = (F(1),) + (F(0),) * 7
RADICANDS = (2, 3, -1)
FACTORS = tuple(prod(RADICANDS[b] for b in range(3) if j >> b & 1) for j in range(8))
RADICAL_BASIS = tuple(tuple(F(int(j == k)) for j in range(8)) for k in range(8))
DEFAULT_REPORT = PROJECT_ROOT / (
    "research/geometry/erdos_unit_distance/results/2026-09-10-split-prime-branch-v1.json"
)


def element(coefficients: dict[int, int | F]) -> Radical:
    return tuple(F(coefficients.get(j, 0)) for j in range(8))


def add(left: Radical, right: Radical) -> Radical:
    return tuple(x + y for x, y in zip(left, right))


def scale(value: Radical, scalar: int | F) -> Radical:
    return tuple(x * scalar for x in value)


def multiply(left: Radical, right: Radical) -> Radical:
    result = [F(0)] * 8
    for j, x in enumerate(left):
        if x:
            for k, y in enumerate(right):
                if y:
                    result[j ^ k] += x * y * FACTORS[j & k]
    return tuple(result)


def multiply_all(values) -> Radical:
    result = ONE
    for value in values:
        result = multiply(result, value)
    return result


def conjugate(value: Radical) -> Radical:
    return tuple(-x if j & 4 else x for j, x in enumerate(value))


def solve(columns: list[Radical] | tuple[Radical, ...], target: Radical) -> tuple[F, ...] | None:
    """Solve an eight-row rational system, including consistency of extra rows."""
    size = len(columns)
    rows = [[columns[c][r] for c in range(size)] + [target[r]] for r in range(8)]
    for column in range(size):
        pivot = next((r for r in range(column, 8) if rows[r][column]), None)
        assert pivot is not None, "dependent basis"
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [v / divisor for v in rows[column]]
        for r in range(8):
            if r != column:
                scalar = rows[r][column]
                rows[r] = [v - scalar * w for v, w in zip(rows[r], rows[column])]
    if any(all(v == 0 for v in row[:-1]) and row[-1] for row in rows):
        return None
    return tuple(rows[r][-1] for r in range(size))


def divide(numerator: Radical, denominator: Radical) -> Radical:
    coefficients = solve([multiply(denominator, e) for e in RADICAL_BASIS], numerator)
    assert coefficients is not None
    assert multiply(coefficients, denominator) == numerator
    return coefficients


def from_basis(coefficients, basis: list[Radical]) -> Radical:
    assert len(coefficients) == len(basis)
    result = ZERO
    for coefficient, vector in zip(coefficients, basis):
        result = add(result, scale(vector, coefficient))
    return result


@dataclass
class IndependentLevel:
    order: int
    basis: list[Radical]
    powers: list[Radical]
    seeds: dict[int, Radical]
    ratios: dict[int, Radical]
    directions: dict[tuple[int, ...], Radical]
    by_witness: dict[tuple[tuple[int, ...], int], Radical]


def build_level(order: int) -> IndependentLevel:
    degree = {4: 2, 8: 4, 24: 8}[order]
    root = {
        4: element({4: 1}),
        8: element({1: F(1, 2), 5: F(1, 2)}),
        24: element({1: F(1, 4), 3: F(1, 4), 5: F(-1, 4), 7: F(1, 4)}),
    }[order]
    powers = [ONE]
    for _ in range(order):
        powers.append(multiply(powers[-1], root))
    assert powers[-1] == ONE and len(set(powers[:-1])) == order
    powers.pop()
    coefficients = {4: (15, -4), 8: (4, 0, -1, -2), 24: (2, 1)}[order]
    seeds = {}
    for t in range(order):
        if gcd(t, order) == 1:
            value = ZERO
            for j, coefficient in enumerate(coefficients):
                value = add(value, scale(powers[j * t % order], coefficient))
            seeds[t] = value
    assert multiply_all(seeds.values()) == scale(ONE, PRIME)
    for t in seeds:
        assert multiply_all(seeds[t * a % order] for a in seeds) == scale(ONE, PRIME)
    representatives = {4: (1,), 8: (1, 3), 24: (1, 5, 7, 11)}[order]
    ratios = {t: divide(seeds[t], conjugate(seeds[t])) for t in representatives}
    assert all(multiply(q, conjugate(q)) == ONE for q in ratios.values())
    basis = powers[:degree]
    directions, by_witness = {}, {}
    for exponents in product((-1, 0, 1), repeat=len(ratios)):
        value = multiply_all(q if e == 1 else conjugate(q) if e == -1 else ONE
                             for e, q in zip(exponents, ratios.values()))
        for phase in range(order):
            numerator = scale(multiply(value, powers[phase]), PRIME)
            assert multiply(numerator, conjugate(numerator)) == scale(ONE, PRIME ** 2)
            coordinates = solve(basis, numerator)
            assert coordinates is not None and all(c.denominator == 1 for c in coordinates)
            coordinates = tuple(map(int, coordinates))
            assert coordinates not in directions
            directions[coordinates] = numerator
            by_witness[exponents, phase] = numerator
    assert len(directions) == order * 3 ** len(ratios)
    return IndependentLevel(order, basis, powers, seeds, ratios, directions, by_witness)


def check_level(level: IndependentLevel, saved: dict) -> dict:
    order, degree = level.order, len(level.basis)
    assert saved["degree"] == degree and saved["denominator"] == PRIME
    assert saved["unit_directions"] == len(level.directions)
    graph = saved["direction_graph"]
    assert graph["denominator"] == PRIME
    assert len(graph["nodes"]) == len(level.directions)
    nodes = {j: level.directions[tuple(v)] for j, _, _, v in graph["nodes"]}
    assert len(nodes) == len(level.directions)
    assert {tuple(v) for _, _, _, v in graph["nodes"]} == set(level.directions)
    witness_ids = {}
    for j, exponents, phase, _ in graph["nodes"]:
        witness = (tuple(exponents), phase)
        assert nodes[j] == level.by_witness[witness]
        witness_ids[witness] = j
    assert len(witness_ids) == len(nodes)
    expected_edges = set()
    for (exponents, phase), source in witness_ids.items():
        expected_edges.add((source, "zeta", witness_ids[exponents, (phase + 1) % order]))
        for axis, t in enumerate(level.ratios):
            if exponents[axis] < 1:
                target = list(exponents)
                target[axis] += 1
                expected_edges.add((source, "q_" + str(t), witness_ids[tuple(target), phase]))
    edges = {tuple(e) for e in graph["edges"]}
    assert len(edges) == len(graph["edges"]) and edges == expected_edges
    multipliers = {"zeta": level.powers[1], **{"q_" + str(t): q for t, q in level.ratios.items()}}
    for source, label, target in edges:
        assert multiply(nodes[source], multipliers[label]) == nodes[target]

    generators = [scale(q, PRIME) for q in level.ratios.values()]
    spans = [solve(generators, value) for value in level.directions.values()]
    rational = [c for c in spans if c is not None]
    integer = {c for c in rational if all(x.denominator == 1 for x in c)}
    axes = {tuple(sign if j == axis else 0 for j in range(len(generators)))
            for axis in range(len(generators)) for sign in (-1, 1)}
    assert integer == axes
    assert len(rational) == saved["generator_span"]["unit_directions_in_rational_span"]
    assert integer == {tuple(v) for v in saved["generator_span"]["unit_steps_in_integer_span"]}

    polynomial = {4: (1, 0, 1), 8: (1, 0, 0, 0, 1), 24: (1, 0, 0, 0, -1, 0, 0, 0, 1)}[order]
    roots = [x for x in range(PRIME) if sum(c * pow(x, j, PRIME)
             for j, c in enumerate(polynomial)) % PRIME == 0]
    splitting = saved["splitting_witnesses"]
    assert len(roots) == degree
    assert set(roots) == {v for _, v in splitting["roots_mod_prime"]}
    assert {f["automorphism"] for f in splitting["prime_generators"]} == set(level.seeds)
    zero_roots = []
    for factor in splitting["prime_generators"]:
        coordinates = factor["basis_coefficients"]
        assert from_basis(coordinates, level.basis) == level.seeds[factor["automorphism"]]
        assert factor["field_norm"] == PRIME
        zeros = [r for r in roots if sum(c * pow(r, j, PRIME)
                 for j, c in enumerate(coordinates)) % PRIME == 0]
        assert len(zeros) == 1 and zeros == factor["zero_mod_prime"]
        zero_roots.extend(zeros)
    assert set(zero_roots) == set(roots)

    point_graph = saved["small_point_graph"]
    assert point_graph["denominator"] == PRIME
    points = {}
    coefficient_ids = {}
    for j, coefficients, coordinates in point_graph["points"]:
        value = from_basis(coordinates, level.basis)
        assert value == from_basis(coefficients, generators)
        points[j] = value
        coefficient_ids[tuple(coefficients)] = j
    assert len(points) == len(set(points.values())) == 3 ** len(generators)
    assert set(coefficient_ids) == set(product(range(3), repeat=len(generators)))
    expected_pairs = set()
    for left, right in combinations(points, 2):
        difference = add(points[right], scale(points[left], -1))
        if multiply(difference, conjugate(difference)) == scale(ONE, PRIME ** 2):
            expected_pairs.add(tuple(sorted((left, right))))
    actual_pairs = set()
    for left, axis, right in point_graph["addition_edges"]:
        assert add(points[left], generators[axis]) == points[right]
        actual_pairs.add(tuple(sorted((left, right))))
    assert len(actual_pairs) == len(point_graph["addition_edges"])
    assert actual_pairs == expected_pairs
    for box in saved["generator_boxes"]:
        side, f = box["side"], len(generators)
        assert box["points"] == side ** f and box["unit_pairs"] == f * (side - 1) * side ** (f - 1)
    maximum = max(abs(c) for vector in level.directions for c in vector)
    assert maximum == saved["max_absolute_direction_coefficient"]
    return {"root_order": order, "directions": len(nodes), "direction_edges": len(edges),
            "rational_span_unit_count": len(rational), "integer_span_unit_count": len(integer),
            "small_points": len(points), "small_unit_pairs": len(expected_pairs),
            "max_direction_coefficient": maximum, "roots_mod_241": roots}


def verify(report: dict) -> dict:
    assert report["prime"] == PRIME and all(PRIME % d for d in range(2, isqrt(PRIME) + 1))
    assert [row["root_order"] for row in report["levels"]] == [4, 8, 24]
    levels = {m: build_level(m) for m in (4, 8, 24)}
    checked = [check_level(levels[row["root_order"]], row) for row in report["levels"]]
    for parent, child, automorphism in ((4, 8, 5), (8, 24, 17)):
        assert multiply(levels[child].seeds[1], levels[child].seeds[automorphism]) == levels[parent].seeds[1]
    refinements = report["branch_refinements"]
    assert [(r["parent_order"], r["parent_branch"], r["child_order"], r["positive_child"], r["inverse_child"])
            for r in refinements] == [(4, 1, 8, 1, 3), (8, 1, 24, 1, 7), (8, 3, 24, 11, 5)]
    for row in refinements:
        parent, child = levels[row["parent_order"]], levels[row["child_order"]]
        q = parent.ratios[row["parent_branch"]]
        assert q == divide(child.ratios[row["positive_child"]], child.ratios[row["inverse_child"]])
        assert from_basis(row["embedded_parent_numerator_over_p"], child.basis) == scale(q, PRIME)
        assert from_basis(row["child_ratio_numerator_over_p_squared"], child.basis) == scale(q, PRIME ** 2)
        assert row["verified"] is True

    comparison = report["equal_point_comparison"]
    rows = comparison["exact_count_rows"]
    assert [row["T"] for row in rows] == list(range(1, 513))
    counts, first_wins, permanent = {}, {}, {}
    for row in rows:
        t = row["T"]
        assert int(row["point_count_decimal"]) == t ** 8
        counts[t] = {}
        for m, level in levels.items():
            side = t ** (8 // len(level.basis))
            ordered = sum(prod(side - abs(c) for c in vector) for vector in level.directions
                          if all(abs(c) < side for c in vector))
            assert ordered % 2 == 0
            assert ordered // 2 == int(row["unit_pair_counts_decimal"][str(m)])
            counts[t][m] = ordered // 2
        for m, smaller in ((8, (4,)), (24, (4, 8))):
            if counts[t][m] > max(counts[t][s] for s in smaller):
                first_wins.setdefault(str(m), t)
            if 2 * counts[t][m] > t ** 8 * max(len(levels[s].directions) for s in smaller):
                permanent.setdefault(str(m), t)
    assert first_wins == comparison["first_strict_win_over_all_smaller_fields"] == {"8": 18, "24": 259}
    assert permanent == comparison["permanent_dominance_from_direction_cap"] == {"8": 18, "24": 259}
    for t, pairs in counts.items():
        expected = [4, 8, 24] if t < 4 else [4] if t < 18 else [8] if t < 259 else [24]
        assert [m for m, count in pairs.items() if count == max(pairs.values())] == expected
    ceiling = report["cyclotomic_growth_ceiling"]
    conductors = [m for m in range(1, PRIME) if (PRIME - 1) % m == 0]
    degrees = {str(m): sum(gcd(j, m) == 1 for j in range(1, m + 1)) for m in conductors}
    assert conductors == ceiling["compatible_conductors"] and degrees == ceiling["degrees"]
    assert max(degrees.values()) == ceiling["maximum_degree"] == 64
    squared = multiply(levels[4].ratios[1], levels[4].ratios[1])
    assert squared == element({0: F(29281, 58081), 4: F(-50160, 58081)})
    assert gcd(gcd(29281, 50160), 58081) == 1
    return {"status": "passed", "arithmetic": "independent multiquadratic Fraction basis and division solver",
            "levels": checked, "refinement_identities": len(refinements), "comparison_rows": len(rows),
            "first_crossovers": first_wins, "permanent_direction_cap_thresholds": permanent,
            "cyclotomic_maximum_degree": 64,
            "repeated_branch_square": {"real_numerator": 29281, "imaginary_numerator": -50160,
                                       "minimal_denominator_in_Zi": 58081},
            "limits": "Numerical witnesses checked. Completeness and infinite-tail proofs are reviewed separately; no infinite family is certified."}


def main() -> None:
    if not __debug__:
        raise RuntimeError("Run without -O: this verifier requires assertions")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw = args.report.read_bytes()
    result = verify(json.loads(raw))
    result["input_sha256"] = sha256(raw).hexdigest()
    result["verifier_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    result["input_report"] = args.report.name
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
