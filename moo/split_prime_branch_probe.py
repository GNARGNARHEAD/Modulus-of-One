"""Exact three-level example of split-prime branch growth and point assembly.

External cyclotomic arithmetic is kept separate from the scalar MoO witness
graph. Only the 2, 4, and 8 degree fields with root orders 4, 8, and 24 are
implemented. Large coefficient boxes are counted by a finite exact formula;
their points are not enumerated.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations, product
import json
from math import gcd, isqrt, prod
from pathlib import Path

from moo.constructionist_math import Graph

Vector = tuple[int, ...]
PRIME = 241
ORDERS = (4, 8, 24)
MAX_COMPARISON_T = 512


class CyclotomicRing:
    """Integer power-basis arithmetic modulo Phi_m, for three declared m."""

    def __init__(self, order: int) -> None:
        if type(order) is not int or order not in ORDERS:
            raise ValueError("supported root orders are 4, 8, and 24")
        self.order = order
        self.degree = {4: 2, 8: 4, 24: 8}[order]
        self.zero = (0,) * self.degree
        self.one = (1,) + (0,) * (self.degree - 1)
        self.powers = [self.one]
        for _ in range(1, order):
            coefficients = [0] + list(self.powers[-1])
            top = coefficients.pop()
            coefficients[0] -= top
            if order == 24:
                coefficients[4] += top
            self.powers.append(tuple(coefficients))
        self.automorphisms = tuple(t for t in range(order) if gcd(t, order) == 1)

    def scalar(self, value: int) -> Vector:
        return (value,) + (0,) * (self.degree - 1)

    def multiply(self, left: Vector, right: Vector) -> Vector:
        result = [0] * self.degree
        for j, x in enumerate(left):
            if not x:
                continue
            for k, y in enumerate(right):
                if not y:
                    continue
                for i, coefficient in enumerate(self.powers[(j + k) % self.order]):
                    result[i] += x * y * coefficient
        return tuple(result)

    def product(self, terms: list[Vector]) -> Vector:
        result = self.one
        for term in terms:
            result = self.multiply(result, term)
        return result

    def sigma(self, value: Vector, exponent: int) -> Vector:
        if gcd(exponent, self.order) != 1:
            raise ValueError("an automorphism exponent must be coprime to the root order")
        result = [0] * self.degree
        for j, x in enumerate(value):
            for i, coefficient in enumerate(self.powers[(j * exponent) % self.order]):
                result[i] += x * coefficient
        return tuple(result)

    def norm(self, value: Vector) -> int:
        result = self.product([self.sigma(value, t) for t in self.automorphisms])
        if any(result[1:]):
            raise ArithmeticError("field norm did not land in the rational subfield")
        return result[0]

    def evaluate_mod_prime(self, value: Vector, root: int) -> int:
        return sum(c * pow(root, j, PRIME) for j, c in enumerate(value)) % PRIME


@dataclass
class Level:
    ring: CyclotomicRing
    seed: Vector
    representatives: tuple[int, ...]
    pairs: list[tuple[Vector, Vector]]
    directions: dict[Vector, tuple[tuple[int, ...], int]]
    generators: list[Vector]


def make_level(order: int) -> Level:
    ring = CyclotomicRing(order)
    seed = {4: (15, -4), 8: (4, 0, -1, -2),
            24: (2, 1, 0, 0, 0, 0, 0, 0)}[order]
    representatives = {4: (1,), 8: (1, 3), 24: (1, 5, 7, 11)}[order]
    pairs = [(ring.sigma(seed, t), ring.sigma(seed, -t)) for t in representatives]
    if ring.product([v for pair in pairs for v in pair]) != ring.scalar(PRIME):
        raise ArithmeticError("conjugate factors failed to multiply to the fixed prime")
    directions = {}
    for exponents in product((-1, 0, 1), repeat=len(pairs)):
        factors = []
        for exponent, (alpha, alpha_bar) in zip(exponents, pairs):
            factors.extend([alpha, alpha] if exponent == 1 else
                           [alpha_bar, alpha_bar] if exponent == -1 else [alpha, alpha_bar])
        numerator = ring.product(factors)
        for root_exponent, root in enumerate(ring.powers):
            value = ring.multiply(numerator, root)
            if value in directions:
                raise ArithmeticError("different branch choices collided")
            if ring.multiply(value, ring.sigma(value, -1)) != ring.scalar(PRIME ** 2):
                raise ArithmeticError("a direction failed its exact unit-norm identity")
            directions[value] = (exponents, root_exponent)
    by_witness = {witness: value for value, witness in directions.items()}
    generators = [by_witness[(tuple(int(i == j) for i in range(len(pairs))), 0)]
                  for j in range(len(pairs))]
    return Level(ring, seed, representatives, pairs, directions, generators)


def inverse_matrix(matrix: list[list[int]]) -> list[list[Fraction]]:
    size = len(matrix)
    rows = [[Fraction(c) for c in row] + [Fraction(int(i == j)) for j in range(size)]
            for i, row in enumerate(matrix)]
    for column in range(size):
        pivot = next((j for j in range(column, size) if rows[j][column]), None)
        if pivot is None:
            raise ValueError("singular matrix")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [c / divisor for c in rows[column]]
        for j in range(size):
            if j != column:
                scale = rows[j][column]
                rows[j] = [a - scale * b for a, b in zip(rows[j], rows[column])]
    return [row[size:] for row in rows]


def generator_span(level: Level) -> dict:
    """Intersect the complete finite unit set with the integer generator span."""
    size = len(level.generators)
    for pivots in combinations(range(level.ring.degree), size):
        matrix = [[g[i] for g in level.generators] for i in pivots]
        try:
            inverse = inverse_matrix(matrix)
            break
        except ValueError:
            continue
    else:
        raise ArithmeticError("selected generators are not rationally independent")
    rational_count = 0
    integer_steps = []
    for value in level.directions:
        coefficients = [sum(c * value[i] for c, i in zip(row, pivots)) for row in inverse]
        reconstructed = tuple(sum(c * g[i] for c, g in zip(coefficients, level.generators))
                              for i in range(level.ring.degree))
        if reconstructed != value:
            continue
        rational_count += 1
        if all(c.denominator == 1 for c in coefficients):
            integer_steps.append(tuple(int(c) for c in coefficients))
    return {"rank": size, "pivot_rows": pivots,
            "unit_directions_in_rational_span": rational_count,
            "unit_steps_in_integer_span": sorted(integer_steps)}


def count_coefficient_box(steps: list[Vector], side: int, dimension: int) -> int:
    """Unordered unit pairs: one exact overlap product per oriented step."""
    if type(side) is not int or side < 1:
        raise ValueError("box side must be a positive integer")
    if type(dimension) is not int or dimension < 1 or any(len(step) != dimension for step in steps):
        raise ValueError("every step must match the declared box dimension")
    ordered = sum(prod(max(side - abs(c), 0) for c in step) for step in steps)
    if ordered % 2:
        raise ArithmeticError("oriented count was odd; opposite steps are missing")
    return ordered // 2


def ratio_payload(value: Fraction) -> dict:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator),
            "approx": float(value)}


def box_row(level: Level, t: int) -> dict:
    dimension = level.ring.degree
    side = t ** (8 // dimension)
    points = side ** dimension
    edges = count_coefficient_box(list(level.directions), side, dimension)
    return {"root_order": level.ring.order, "basis_dimension": dimension, "T": t,
            "coefficient_side": side, "point_count_decimal": str(points),
            "unit_pair_count_decimal": str(edges),
            "active_oriented_directions": sum(all(abs(c) < side for c in step)
                                               for step in level.directions),
            "average_unit_neighbors": ratio_payload(Fraction(2 * edges, points)),
            "direction_retention": ratio_payload(Fraction(2 * edges, points * len(level.directions)))}


def small_point_graph(level: Level, side: int = 3) -> dict:
    if side not in (3, 5):
        raise ValueError("only small side-3 and side-5 generator boxes are enumerated")
    coefficient_nodes = list(product(range(side), repeat=len(level.generators)))
    ids = {c: j for j, c in enumerate(coefficient_nodes)}
    nodes = []
    edges = []
    for j, coefficients in enumerate(coefficient_nodes):
        numerator = tuple(sum(c * g[i] for c, g in zip(coefficients, level.generators))
                          for i in range(level.ring.degree))
        nodes.append([j, coefficients, numerator])
        for axis in range(len(level.generators)):
            if coefficients[axis] + 1 < side:
                target = list(coefficients)
                target[axis] += 1
                edges.append([j, axis, ids[tuple(target)]])
    return {"evidence_layer": "external_cyclotomic_geometry", "denominator": PRIME,
            "point_columns": ["point_id", "generator_coefficients", "basis_numerator"],
            "points": nodes, "addition_edge_columns": ["source", "generator_index", "target"],
            "addition_edges": edges}


def direction_graph(level: Level) -> dict:
    nodes = [[j, exponents, root, value]
             for j, (value, (exponents, root)) in enumerate(level.directions.items())]
    ids = {(tuple(exponents), root): j for j, exponents, root, _ in nodes}
    edges = []
    for j, exponents, root, _ in nodes:
        edges.append([j, "zeta", ids[(tuple(exponents), (root + 1) % level.ring.order)]])
        for axis, exponent in enumerate(exponents):
            if exponent < 1:
                target = list(exponents)
                target[axis] += 1
                edges.append([j, "q_" + str(level.representatives[axis]), ids[(tuple(target), root)]])
    return {"evidence_layer": "external_cyclotomic_construction", "denominator": PRIME,
            "node_columns": ["direction_id", "prime_pair_exponents", "root_exponent", "basis_numerator"],
            "nodes": nodes, "edge_columns": ["source", "multiply_by", "target"], "edges": edges}


def splitting_witnesses(level: Level) -> dict:
    ring = level.ring
    base_root = pow(-2, 24 // ring.order, PRIME)
    roots = [(t, pow(base_root, t, PRIME)) for t in ring.automorphisms]
    factors = []
    for t in ring.automorphisms:
        value = ring.sigma(level.seed, t)
        zeros = [root for _, root in roots if ring.evaluate_mod_prime(value, root) == 0]
        factors.append({"automorphism": t, "basis_coefficients": value,
                        "field_norm": ring.norm(value), "zero_mod_prime": zeros})
    return {"prime": PRIME, "primitive_root_for_zeta": base_root,
            "roots_mod_prime": roots, "prime_generators": factors,
            "product_of_all_generators": ring.product([tuple(f["basis_coefficients"]) for f in factors])}


def embed(value: Vector, source_order: int, target: CyclotomicRing) -> Vector:
    if target.order % source_order:
        raise ValueError("root orders must divide under this embedding")
    result = [0] * target.degree
    for j, coefficient in enumerate(value):
        for i, c in enumerate(target.powers[(j * (target.order // source_order)) % target.order]):
            result[i] += coefficient * c
    return tuple(result)


def refinement_witnesses(levels: list[Level]) -> list[dict]:
    by_order = {level.ring.order: level for level in levels}
    specs = [(4, 1, 8, 1, 3), (8, 1, 24, 1, 7), (8, 3, 24, 11, 5)]
    result = []
    for parent_order, parent_t, child_order, plus_t, minus_t in specs:
        parent, child = by_order[parent_order], by_order[child_order]
        ring = child.ring
        parent_q = parent.generators[parent.representatives.index(parent_t)]
        plus_q = child.generators[child.representatives.index(plus_t)]
        minus_q = child.generators[child.representatives.index(minus_t)]
        embedded = embed(parent_q, parent_order, ring)
        product_numerator = ring.multiply(plus_q, ring.sigma(minus_q, -1))
        result.append({"parent_order": parent_order, "parent_branch": parent_t,
                       "child_order": child_order, "positive_child": plus_t,
                       "inverse_child": minus_t,
                       "identity": "embedded parent q = positive child q / inverse child q",
                       "embedded_parent_numerator_over_p": embedded,
                       "child_ratio_numerator_over_p_squared": product_numerator,
                       "verified": product_numerator == tuple(PRIME * c for c in embedded)})
    return result


def equal_point_comparison(levels: list[Level], max_t: int = MAX_COMPARISON_T) -> dict:
    if type(max_t) is not int or not 1 <= max_t <= MAX_COMPARISON_T:
        raise ValueError("comparison T must be between 1 and 512")
    rows = []
    exact_counts = []
    first_wins = {}
    permanent = {}
    runs = []
    previous_winners = None
    for t in range(1, max_t + 1):
        counts = [count_coefficient_box(list(level.directions), t ** (8 // level.ring.degree),
                                       level.ring.degree) for level in levels]
        points = t ** 8
        exact_counts.append({"T": t, "point_count_decimal": str(points),
                             "unit_pair_counts_decimal": {str(level.ring.order): str(count)
                                                          for level, count in zip(levels, counts)}})
        winners = [level.ring.order for level, count in zip(levels, counts) if count == max(counts)]
        if winners != previous_winners:
            runs.append({"from_T": t, "through_T": t, "winning_root_orders": winners})
            previous_winners = winners
        else:
            runs[-1]["through_T"] = t
        for larger in (1, 2):
            if counts[larger] > max(counts[:larger]):
                first_wins.setdefault(str(levels[larger].ring.order), t)
            # The average degree is increasing with side. Exceeding every
            # smaller field's total direction count certifies all larger T too.
            if 2 * counts[larger] > points * max(len(level.directions) for level in levels[:larger]):
                permanent.setdefault(str(levels[larger].ring.order), t)
        if t in (3, 4, 17, 18, 32, 64, 128, 256, 258, 259, 512):
            rows.append({"T": t, "levels": [box_row(level, t) for level in levels]})
    return {"comparison_rule": "all point counts equal T^8; coefficient sides T^4, T^2, T",
            "searched_T_inclusive": [1, max_t], "winner_runs": runs,
            "first_strict_win_over_all_smaller_fields": first_wins,
            "permanent_dominance_from_direction_cap": permanent, "selected_rows": rows,
            "exact_count_rows": exact_counts}


def cyclotomic_growth_ceiling() -> dict:
    conductors = [m for m in range(1, PRIME) if (PRIME - 1) % m == 0]
    degrees = {m: sum(gcd(a, m) == 1 for a in range(1, m + 1)) for m in conductors}
    return {"condition": "241 splits completely and is unramified in Q(zeta_m) iff m divides 240",
            "compatible_conductors": conductors, "degrees": degrees,
            "maximum_degree": max(degrees.values()),
            "scope": "Cyclotomic fields only; this does not exclude other infinite number-field towers"}


def scalar_witness_graph() -> dict:
    graph = Graph(max_nodes=270, operation_budget=280)
    graph.advance_frontier_max_to(16)
    squares = {}
    for n in (2, 4, 15, 16):
        node = graph.get_or_create_ref(n)
        result = graph.mul(node, node)
        squares[n] = {"edge_uid": graph.edges[-1].edge_uid, "output_uid": result.node_uid,
                      "status_when_squared": result.status}
    graph.advance_frontier_max_to(256)
    shell = graph.add(graph.get_or_create_ref(225), graph.get_or_create_ref(16))
    shell_edge = graph.edges[-1].edge_uid
    difference = graph.sub(graph.get_or_create_ref(256), graph.get_or_create_ref(16))
    difference_edge = graph.edges[-1].edge_uid
    polynomial = graph.add(difference, graph.get_or_create_ref(1))
    return {"evidence_layer": "positive_spine_scalar_witness_graph",
            "identities": ["15^2+4^2=241", "2^8-2^4+1=241"],
            "allow_speculative_operands": graph.allow_speculative_operands,
            "square_witnesses": squares, "shell_sum_edge_uid": shell_edge,
            "polynomial_difference_edge_uid": difference_edge,
            "polynomial_sum_edge_uid": graph.edges[-1].edge_uid,
            "shared_output_uid": shell.node_uid, "outputs_identical": shell is polynomial,
            "scope": "Scalar witnesses only; roots of unity and number fields are external objects.",
            "graph": graph.to_jsonable()}


def build_report() -> dict:
    levels = [make_level(order) for order in ORDERS]
    reports = []
    for level in levels:
        span = generator_span(level)
        small_boxes = []
        for side in (3, 5):
            small_boxes.append({"side": side, "points": side ** len(level.generators),
                                "unit_pairs": count_coefficient_box(span["unit_steps_in_integer_span"],
                                                                      side, len(level.generators))})
        reports.append({"root_order": level.ring.order, "degree": level.ring.degree,
                        "conjugate_prime_pairs": len(level.pairs),
                        "unit_directions": len(level.directions), "denominator": PRIME,
                        "root_of_unity_factor": level.ring.order,
                        "independent_prime_choice_factor": 3 ** len(level.pairs),
                        "splitting_witnesses": splitting_witnesses(level),
                        "direction_graph": direction_graph(level), "generator_span": span,
                        "generator_boxes": small_boxes,
                        "small_point_graph": small_point_graph(level),
                        "max_absolute_direction_coefficient": max(abs(c) for v in level.directions for c in v)})
    return {"schema": "moo_split_prime_branch_gate_v1", "prime": PRIME,
            "prime_trial_remainders": {str(d): PRIME % d for d in range(2, isqrt(PRIME) + 1)},
            "levels": reports, "branch_refinements": refinement_witnesses(levels),
            "equal_point_comparison": equal_point_comparison(levels),
            "cyclotomic_growth_ceiling": cyclotomic_growth_ceiling(),
            "scalar_calibration": scalar_witness_graph(),
            "claims": {
                "scope": "Three explicit finite fields; no asserted continuation as an infinite tower",
                "complete_unit_directions": "m*3^(degree/2) in (1/241) Z[zeta_m]",
                "box_count": "2E=sum_over_unit_numerators product_j max(side-|numerator_j|,0)",
                "fixed_field_limit": "2E/N tends to its unit-direction count as side tends to infinity; exponent tends to 1",
                "next_obligation": "Control arithmetic degree, direction growth, and window retention along a justified infinite field family",
                "proof_location": "research/geometry/erdos_unit_distance/SPLIT_PRIME_BRANCH_GROWTH_NOTE.md"}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="new versioned JSON path; existing paths are refused")
    args = parser.parse_args()
    report = build_report()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps({
        "levels": [{key: row[key] for key in ("root_order", "degree", "conjugate_prime_pairs",
                                               "unit_directions", "generator_boxes")}
                   for row in report["levels"]],
        "winner_runs": report["equal_point_comparison"]["winner_runs"],
        "permanent_dominance": report["equal_point_comparison"]["permanent_dominance_from_direction_cap"],
        "refinements_verified": all(row["verified"] for row in report["branch_refinements"]),
        "output": str(args.output) if args.output else None,
    }, indent=2))


if __name__ == "__main__":
    main()
