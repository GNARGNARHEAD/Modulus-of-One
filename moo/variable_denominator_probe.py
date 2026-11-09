"""Exact bounded comparisons with varying primes and denominator exponents.

The arithmetic is external to MoO. Symbolic Cartesian-product graphs preserve
direction construction without serializing nearly a million repeated edges.
Full coefficient-box point sets are counted, never enumerated.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from math import gcd, isqrt, prod
from pathlib import Path

from moo.constructionist_math import Graph
from moo.split_prime_branch_probe import CyclotomicRing, Vector, ratio_payload

SEEDS = {
    (4, 5): (2, 1), (4, 13): (3, 2), (4, 241): (15, -4),
    (8, 17): (1, 2, 0, 0), (8, 41): (1, 1, 1, 2), (8, 241): (4, 0, -1, -2),
    (24, 73): (1, 1, 0, 2, 0, 0, 0, 0),
    (24, 97): (1, 1, 1, 0, 1, 0, 0, 0),
    (24, 241): (2, 1, 0, 0, 0, 0, 0, 0),
}
REPRESENTATIVES = {4: (1,), 8: (1, 3), 24: (1, 5, 7, 11)}
CASE_SPECS = (
    (4, ((241, 1),)), (4, ((241, 2),)), (4, ((5, 1), (13, 1))),
    (8, ((241, 1),)), (8, ((241, 2),)), (8, ((17, 1), (41, 1))),
    (24, ((73, 1),)), (24, ((97, 1),)), (24, ((241, 1),)),
    (24, ((73, 2),)), (24, ((241, 2),)), (24, ((73, 1), (97, 1))),
)
MAX_DIRECTIONS = 200_000
COMPARISON_T = (64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536)


def prime_witness(order: int, prime: int) -> dict:
    ring = CyclotomicRing(order)
    seed = SEEDS[order, prime]
    assert prime > 2 and all(prime % j for j in range(2, isqrt(prime) + 1))
    assert (prime - 1) % order == 0
    polynomial = {4: (1, 0, 1), 8: (1, 0, 0, 0, 1),
                  24: (1, 0, 0, 0, -1, 0, 0, 0, 1)}[order]
    roots = [r for r in range(prime) if sum(c * pow(r, j, prime)
             for j, c in enumerate(polynomial)) % prime == 0]
    assert len(roots) == ring.degree
    factors = []
    for t in ring.automorphisms:
        value = ring.sigma(seed, t)
        zeros = [r for r in roots if sum(c * pow(r, j, prime)
                 for j, c in enumerate(value)) % prime == 0]
        assert ring.norm(value) == prime and len(zeros) == 1
        factors.append({"automorphism": t, "basis_coefficients": value,
                        "field_norm": prime, "zero_mod_prime": zeros[0]})
    assert {row["zero_mod_prime"] for row in factors} == set(roots)
    assert ring.product([row["basis_coefficients"] for row in factors]) == ring.scalar(prime)
    return {"root_order": order, "prime": prime, "seed": seed, "roots_mod_prime": roots,
            "prime_factors": factors, "representative_automorphisms": REPRESENTATIVES[order]}


def choice_block(order: int, prime: int, depth: int) -> dict:
    """Materialized graph of exponent choices for one prime, without root phases."""
    if type(depth) is not int or depth not in (1, 2):
        raise ValueError("this bounded probe supports exponent budgets 1 and 2")
    ring = CyclotomicRing(order)
    witness = prime_witness(order, prime)
    by_t = {row["automorphism"]: tuple(row["basis_coefficients"]) for row in witness["prime_factors"]}
    pairs = [(by_t[t], by_t[-t % order]) for t in REPRESENTATIVES[order]]
    nodes, ids = [], {}
    for exponents in product(range(-depth, depth + 1), repeat=len(pairs)):
        terms = []
        for exponent, (a, b) in zip(exponents, pairs):
            terms.extend([a] * (depth + exponent) + [b] * (depth - exponent))
        numerator = ring.product(terms)
        assert ring.multiply(numerator, ring.sigma(numerator, -1)) == ring.scalar(prime ** (2 * depth))
        ids[exponents] = len(nodes)
        nodes.append([len(nodes), exponents, numerator])
    generators = []
    for axis in range(len(pairs)):
        terms = []
        for j, (a, b) in enumerate(pairs):
            terms.extend([a, a] if j == axis else [a, b])
        generators.append(ring.product(terms))
    edges = []
    for source, exponents, numerator in nodes:
        for axis, exponent in enumerate(exponents):
            if exponent < depth:
                target_exponents = list(exponents)
                target_exponents[axis] += 1
                target = ids[tuple(target_exponents)]
                assert ring.multiply(numerator, generators[axis]) == tuple(prime * c for c in nodes[target][2])
                edges.append([source, axis, target])
    return {"prime": prime, "depth": depth, "denominator": prime ** depth,
            "factor_witness": witness, "node_columns": ["node_id", "exponents", "basis_numerator"],
            "nodes": nodes, "edge_columns": ["source", "ratio_axis", "target"], "edges": edges,
            "ratio_numerators_over_prime": generators}


@dataclass
class DenominatorCase:
    order: int
    factors: tuple[tuple[int, int], ...]
    denominator: int
    directions: set[Vector]
    profiles: Counter
    construction: dict
    digest: str

    @property
    def label(self) -> str:
        return "m" + str(self.order) + "_" + "_".join(str(p) + "pow" + str(k) for p, k in self.factors)


def make_case(order: int, factors: tuple[tuple[int, int], ...]) -> DenominatorCase:
    ring = CyclotomicRing(order)
    if not factors or len(factors) > 2 or len({p for p, _ in factors}) != len(factors):
        raise ValueError("use one or two distinct registered primes")
    if any((order, p) not in SEEDS or type(k) is not int or k not in (1, 2) for p, k in factors):
        raise ValueError("unregistered prime or unsupported exponent budget")
    expected = order * prod((2 * k + 1) ** (ring.degree // 2) for _, k in factors)
    if expected > MAX_DIRECTIONS:
        raise ValueError("direction count exceeds the bounded experiment cap")
    blocks = [choice_block(order, p, k) for p, k in factors]
    denominator = prod(block["denominator"] for block in blocks)
    directions, profiles, samples = set(), Counter(), []
    digest = sha256()
    for choices in product(*(block["nodes"] for block in blocks)):
        numerator = ring.product([tuple(row[2]) for row in choices])
        assert ring.multiply(numerator, ring.sigma(numerator, -1)) == ring.scalar(denominator ** 2)
        exponents = tuple(e for row in choices for e in row[1])
        for phase, root in enumerate(ring.powers):
            value = ring.multiply(numerator, root)
            assert value not in directions
            directions.add(value)
            profiles[tuple(sorted(abs(c) for c in value))] += 1
            digest.update((",".join(map(str, value)) + "\n").encode("ascii"))
            if len(samples) < 32:
                samples.append({"prime_pair_exponents": exponents, "root_exponent": phase,
                                "basis_numerator": value})
    assert len(directions) == expected
    assert all(tuple(-c for c in value) in directions for value in directions)
    edges = expected + sum(expected * (ring.degree // 2) * (2 * k) // (2 * k + 1) for _, k in factors)
    construction = {
        "evidence_layer": "external_symbolic_direction_graph",
        "prime_choice_blocks": blocks,
        "phase_cycle": {"nodes": ring.powers, "edges": [[t, (t + 1) % order] for t in range(order)]},
        "product_node_rule": "Choose one node from each prime block and one phase; multiply their values.",
        "product_edge_rule": "Advance one block edge, or one phase edge, leaving all other coordinates fixed.",
        "product_node_count": expected, "product_edge_count": edges,
        "materialization": "Factor graphs and phase cycle are explicit; the full product graph is symbolic.",
        "sample_direction_nodes": samples,
    }
    return DenominatorCase(order, factors, denominator, directions, profiles, construction, digest.hexdigest())


def box_pairs(case: DenominatorCase, side: int) -> int:
    if type(side) is not int or side < 1:
        raise ValueError("side must be a positive integer")
    ordered = sum(multiplicity * prod(side - shift for shift in profile)
                  for profile, multiplicity in case.profiles.items() if profile[-1] < side)
    assert ordered % 2 == 0
    return ordered // 2


def box_row(case: DenominatorCase, t: int) -> dict:
    degree = {4: 2, 8: 4, 24: 8}[case.order]
    side = t ** (8 // degree)
    points, edges = t ** 8, box_pairs(case, side)
    return {"T": t, "coefficient_side": side, "point_count_decimal": str(points),
            "unit_pair_count_decimal": str(edges),
            "average_unit_neighbors": ratio_payload(Fraction(2 * edges, points)),
            "direction_retention": ratio_payload(Fraction(2 * edges, points * len(case.directions))),
            "active_directions": sum(n for profile, n in case.profiles.items() if profile[-1] < side)}


def first_average_above(case: DenominatorCase, cap: int) -> dict:
    """First coefficient side exceeding a direction cap; monotonicity certifies the tail."""
    if type(cap) is not int or not 0 <= cap < len(case.directions):
        raise ValueError("cap must be nonnegative and below the complete direction count")
    degree = {4: 2, 8: 4, 24: 8}[case.order]
    low, high = 1, 2
    while 2 * box_pairs(case, high) <= cap * high ** degree:
        low, high = high, 2 * high
    while high - low > 1:
        middle = (low + high) // 2
        if 2 * box_pairs(case, middle) > cap * middle ** degree:
            high = middle
        else:
            low = middle
    witnesses = []
    for side in (high - 1, high):
        edges, points = box_pairs(case, side), side ** degree
        witnesses.append({"side": side, "point_count_decimal": str(points),
                          "twice_unit_pairs_decimal": str(2 * edges),
                          "cap_times_points_decimal": str(cap * points),
                          "average": ratio_payload(Fraction(2 * edges, points))})
    return {"cap": cap, "first_coefficient_side": high, "exact_boundary_witnesses": witnesses,
            "scope": "First crossing of a constant direction cap, not the first pairwise crossover or a global optimum."}


def scalar_witness_graph() -> dict:
    graph = Graph(max_nodes=270, operation_budget=280)
    graph.advance_frontier_max_to(241)
    products = []
    for a, b in ((5, 13), (17, 41), (73, 73), (73, 97), (241, 241)):
        result = graph.mul(graph.get_or_create_ref(a), graph.get_or_create_ref(b))
        products.append({"inputs": [a, b], "value": a * b, "output_uid": result.node_uid,
                         "status": result.status, "edge_uid": graph.edges[-1].edge_uid})
    return {"evidence_layer": "scalar_positive_spine_with_speculative_outputs",
            "allow_speculative_operands": graph.allow_speculative_operands,
            "products": products, "graph": graph.to_jsonable(),
            "scope": "Large products remain speculative in core and are never used as operands; external exact arithmetic has separate status."}


def build_report() -> dict:
    rows = []
    for order, factors in CASE_SPECS:
        case = make_case(order, factors)
        row = {"case": case.label, "root_order": order, "factors": factors,
               "denominator": case.denominator, "complete_unit_directions": len(case.directions),
               "least_denominator_counts": dict(sorted(Counter(
                   case.denominator // gcd(case.denominator, *vector)
                   for vector in case.directions).items())),
               "direction_sha256_in_construction_order": case.digest,
               "absolute_profile_count": len(case.profiles),
               "smallest_side_with_an_edge": min(profile[-1] for profile in case.profiles) + 1,
               "smallest_side_using_all_directions": max(profile[-1] for profile in case.profiles) + 1,
               "construction_graph": case.construction,
               "equal_point_rows": [box_row(case, t) for t in COMPARISON_T]}
        if order == 24 and factors == ((73, 1), (97, 1)):
            row["permanent_direction_cap_comparisons"] = [first_average_above(case, cap) for cap in (1944, 15000)]
        rows.append(row)
    return {"schema": "moo_variable_denominator_gate_v1", "date": "2026-09-11",
            "comparison_rule": "Each row T uses N=T^8 points; coefficient side is T^(8/degree).",
            "cases": rows, "scalar_calibration": scalar_witness_graph(),
            "claims": {
                "complete_count": "m * product_p (2*k_p+1)^(degree/2), for the verified principal split primes only",
                "fixed_CM_upper_bound": "M_K(D) <= roots_of_unity(K) * tau(D^2)^(degree/2), for all integer D>=1",
                "full_box_upper_bound": "For fixed CM field and fixed integral basis, E <= C_epsilon N^(1+epsilon) uniformly over all denominators and full rectangular boxes",
                "necessary_denominator_growth": "In a fixed CM field, a sequence with E >= c*N^(1+delta) for fixed c,delta>0 requires log(D(P-P))/log(N) -> infinity along that sequence",
                "denominator_class_caps_K24": "Prime denominators give average degree <=1944; prime-square denominators give <=15000, for any prime and any point selection in a translate of the corresponding module",
                "scope": "No new record exponent; no impossibility claim for arbitrary selected points or growing fields",
                "proof_location": "research/geometry/erdos_unit_distance/VARIABLE_DENOMINATOR_BRANCH_NOTE.md",
            }}


def main() -> None:
    if not __debug__:
        raise RuntimeError("Run without -O: arithmetic assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report()
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
    summary = [{"case": row["case"], "denominator": row["denominator"],
                "directions": row["complete_unit_directions"],
                "profile_count": row["absolute_profile_count"],
                "first_edge_side": row["smallest_side_with_an_edge"],
                "average_at_T8192": next(r["average_unit_neighbors"]["approx"] for r in row["equal_point_rows"] if r["T"] == 8192),
                "cap_comparisons": row.get("permanent_direction_cap_comparisons", [])}
               for row in report["cases"]]
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
