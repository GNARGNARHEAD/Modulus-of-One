"""Verify shared norm and direction nodes in the existing 241 constructions.

This is bounded external arithmetic, not a core MoO expansion. Universal
identities and their scope are proved in SHARED_241_NODE_NOTE.md.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import gcd, prod
from pathlib import Path
from moo.paths import PROJECT_ROOT

from moo.split_prime_branch_probe import CyclotomicRing, Vector, make_level
from moo.variable_denominator_probe import make_case


def embed(value: Vector, source: int, target: int) -> Vector:
    """Map zeta_source to zeta_target**(target/source)."""
    if (source, target) not in ((4, 8), (8, 24), (4, 24)):
        raise ValueError("only the three declared field inclusions are supported")
    if len(value) != CyclotomicRing(source).degree:
        raise ValueError("source basis dimension does not match")
    ring = CyclotomicRing(target)
    out = [0] * ring.degree
    for j, a in enumerate(value):
        for i, c in enumerate(ring.powers[j * (target // source) % target]):
            out[i] += a * c
    return tuple(out)


def power(ring: CyclotomicRing, value: Vector, exponent: int) -> Vector:
    result = ring.one
    for _ in range(exponent):
        result = ring.multiply(result, value)
    return result


def factor_integer(value: int) -> list[tuple[int, int]]:
    factors = []
    divisor = 2
    while divisor * divisor <= value:
        exponent = 0
        while value % divisor == 0:
            value //= divisor
            exponent += 1
        if exponent:
            factors.append((divisor, exponent))
        divisor += 1
    if value > 1:
        factors.append((value, 1))
    return factors


def build_report() -> dict:
    rings = {m: CyclotomicRing(m) for m in (4, 8, 24)}
    family = []
    for x in range(2, 11):
        seeds = {24: (x, 1, 0, 0, 0, 0, 0, 0),
                 8: (x * x, 0, -1, -x), 4: (x**4 - 1, -x * x)}
        assert rings[24].multiply(seeds[24], rings[24].sigma(seeds[24], 17)) == embed(seeds[8], 8, 24)
        assert rings[8].multiply(seeds[8], rings[8].sigma(seeds[8], 5)) == embed(seeds[4], 4, 8)
        value = x**8 - x**4 + 1
        assert value == seeds[4][0]**2 + seeds[4][1]**2
        for m, ring in rings.items():
            for k in range(1, 5):
                assert ring.norm(power(ring, seeds[m], k)) == value**k
        factors = factor_integer(value)
        assert prod(p**k for p, k in factors) == value
        for p, _ in factors:
            assert p % 24 == 1 and pow(x, 24, p) == 1
            assert all(pow(x, d, p) != 1 for d in (1, 2, 3, 4, 6, 8, 12))
        family.append({"x": x, "seeds_by_root_order": seeds, "common_norm": value,
                       "prime_factorization": factors, "norm_power_checks": [1, 2, 3, 4]})

    levels = {m: make_level(m) for m in rings}
    route_matches = []
    for k in range(1, 6):
        v4 = power(rings[4], levels[4].generators[0], k)
        q81, q83 = levels[8].generators
        v8 = rings[8].multiply(power(rings[8], q81, k),
                              power(rings[8], rings[8].sigma(q83, -1), k))
        q241, q245, q247, q2411 = levels[24].generators
        v24 = rings[24].product([
            power(rings[24], q241, k), power(rings[24], q245, k),
            power(rings[24], rings[24].sigma(q247, -1), k),
            power(rings[24], rings[24].sigma(q2411, -1), k)])
        assert v8 == tuple(241**k * c for c in embed(v4, 4, 8))
        assert v24 == tuple(241**(3*k) * c for c in embed(v4, 4, 24))
        assert gcd(241**k, *v4) == 1
        assert v4[0]**2 + v4[1]**2 == 241**(2*k)
        route_matches.append({
            "k": k, "gaussian_numerator": v4, "least_denominator": 241**k,
            "K8_route": {"rule": "q_8,1^k / q_8,3^k",
                          "numerator_before_cancellation": v8,
                          "denominator_before_cancellation": 241**(2*k),
                          "common_cancelled_factor": 241**k},
            "K24_route": {"rule": "q_24,1^k * q_24,5^k / (q_24,7^k * q_24,11^k)",
                           "numerator_before_cancellation": v24,
                           "denominator_before_cancellation": 241**(4*k),
                           "common_cancelled_factor": 241**(3*k)},
            "common_value_in_K24": {"basis_numerator": embed(v4, 4, 24),
                                    "denominator": 241**k}})

    cases = {m: make_case(m, ((241, 2),)) for m in rings}
    inclusions = []
    for small, large in ((4, 8), (8, 24), (4, 24)):
        smaller_set = {embed(v, small, large) for v in cases[small].directions}
        intersection = smaller_set & cases[large].directions
        assert len(intersection) == len(cases[small].directions)
        inclusions.append({"source_root_order": small, "target_root_order": large,
                           "source_count": len(smaller_set), "shared_direction_count": len(intersection),
                           "target_count": len(cases[large].directions),
                           "new_direction_count": len(cases[large].directions) - len(intersection)})

    a = levels[24].seed
    repeated = rings[24].multiply(a, a)
    distinct = rings[24].multiply(a, rings[24].sigma(a, 17))
    assert repeated != distinct
    assert rings[24].norm(repeated) == rings[24].norm(distinct) == 241**2
    repeated_ratio = rings[24].multiply(levels[24].generators[0], levels[24].generators[0])
    distinct_ratio = embed(levels[8].generators[0], 8, 24)
    assert gcd(241**2, *repeated_ratio) == gcd(241, *distinct_ratio) == 1
    # Independently match each candidate ratio to its declared seed numerator.
    assert rings[24].multiply(repeated_ratio, rings[24].sigma(repeated, -1)) == tuple(241**2 * c for c in repeated)
    assert rings[24].multiply(distinct_ratio, rings[24].sigma(distinct, -1)) == tuple(241 * c for c in distinct)
    projection_example = {
        "ambient_root_order": 24, "common_absolute_field_norm": 241**2,
        "repeated_factor": {"rule": "a*a", "seed_coefficients": repeated,
                            "ratio_numerator": repeated_ratio, "ratio_least_denominator": 241**2},
        "distinct_factors": {"rule": "a*sigma_17(a)", "seed_coefficients": distinct,
                             "ratio_numerator": distinct_ratio, "ratio_least_denominator": 241},
        "equal_seed_elements": False,
        "interpretation": "Equal norm projection, different elements and denominator requirements."}

    modular_lifts = []
    residue = 2
    for k in range(1, 7):
        modulus = 241**k
        value = residue**8 - residue**4 + 1
        assert value % modulus == 0 and pow(residue, 24, modulus) == 1
        assert all(pow(residue, d, 241) != 1 for d in (1, 2, 3, 4, 6, 8, 12))
        derivative = (8 * residue**7 - 4 * residue**3) % 241
        assert derivative == 28
        correction = (-(value // modulus) * pow(derivative, -1, 241)) % 241
        modular_lifts.append({"k": k, "modulus": modulus, "residue": residue,
                              "F_remainder": value % modulus, "next_base_241_digit": correction})
        residue += correction * modulus

    frozen_path = PROJECT_ROOT / "research/geometry/erdos_unit_distance/results/2026-09-11-variable-denominator-v1.json"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    calibration = frozen["scalar_calibration"]
    square = next(row for row in calibration["products"] if row["value"] == 241**2)
    incoming = [edge for edge in calibration["graph"]["edges"] if edge["output_uid"] == square["output_uid"]]
    assert square["status"] == "S" and len(incoming) == 1
    assert incoming[0]["op"] == "*" and incoming[0]["inputs"] == [241, 241]
    assert not any(square["output_uid"] in edge["input_uids"] for edge in calibration["graph"]["edges"])

    source_paths = [Path(__file__), (PROJECT_ROOT / 'moo/split_prime_branch_probe.py'),
                    (PROJECT_ROOT / 'moo/variable_denominator_probe.py'), frozen_path]
    return {
        "schema": "moo_shared_241_nodes_v1", "date": "2026-09-11",
        "evidence_layer": "external_exact_arithmetic_with_explicit_embeddings",
        "source_sha256": {path.name: sha256(path.read_bytes()).hexdigest() for path in source_paths},
        "seed_family": family, "direction_power_route_matches": route_matches,
        "denominator_58081_set_inclusions": inclusions,
        "same_norm_different_directions": projection_example,
        "modular_root_lifts": modular_lifts,
        "existing_core_square_node": {"product": square, "incoming_edges": incoming,
                                      "used_as_operand": False,
                                      "multiple_incoming_paths_observed": False},
        "scope": [
            "The repeated denominator 241^2 was a supplied comparison parameter.",
            "A norm match alone does not identify a direction or determine a least denominator.",
            "The direction route matches verify full embedded values, including denominator cancellation.",
            "The script reuses the probes' cyclotomic arithmetic; symbolic proofs are in the note.",
            "The finite checks do not by themselves prove universal identities or prime infinitude.",
            "The root lifts converge in the 241-adic metric, not in ordinary planar distance.",
            "No core speculative node was used, promoted, or expanded; no point-density claim is made."]}


def main() -> None:
    if not __debug__:
        raise RuntimeError("Run without -O: arithmetic assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report()
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    print(json.dumps({"checked_seed_parameters": len(report["seed_family"]),
                      "checked_power_route_matches": len(report["direction_power_route_matches"]),
                      "checked_modular_lifts": len(report["modular_root_lifts"]),
                      "same_norm_example": report["same_norm_different_directions"],
                      "set_inclusions": report["denominator_58081_set_inclusions"]}, indent=2))


if __name__ == "__main__":
    main()
