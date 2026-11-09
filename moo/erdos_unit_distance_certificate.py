"""External analysis of Sawin's unit-distance certificate, equation (11).

This module does not read or modify a MoO graph. It validates finite arithmetic
data, searches the original formula, and bounds that formula from above.
Its upper bounds are NOT upper bounds for the planar unit-distance problem.

Source: https://arxiv.org/html/2605.20579v1, Lemma 12 and equation (11).
Only Python's standard library is required.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN
from fractions import Fraction
from functools import lru_cache
import json
import math
from pathlib import Path
from typing import Iterable


SAWIN_T = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43)
SAWIN_S = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 47, 71, 79, 97,
           101, 107, 109, 139, 151, 163, 167, 179)
SAWIN_K = (50, 31, 21, 17, 14, 13, 12, 11, 10, 10, 8, 7, 7, 7, 7, 7,
           7, 6, 6, 6, 6, 6)
MAX_PRIME_LIMIT = 2_000_000


def primes_up_to(limit: int) -> list[int]:
    if limit < 2:
        return []
    if limit > MAX_PRIME_LIMIT:
        raise ValueError(f"Prime limit exceeds the explicit resource cap {MAX_PRIME_LIMIT}.")
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[:2] = b"\x00\x00"
    for p in range(2, math.isqrt(limit) + 1):
        if sieve[p]:
            sieve[p * p:limit + 1:p] = b"\x00" * ((limit - p * p) // p + 1)
    return [p for p in range(2, limit + 1) if sieve[p]]


def is_prime(n: int) -> bool:
    return (type(n) is int and n >= 2
            and all(n % d for d in range(2, math.isqrt(n) + 1)))


def legendre(a: int, p: int) -> int:
    """For an odd prime p, return the exact Legendre symbol (a/p)."""
    residue = pow(a % p, (p - 1) // 2, p)
    return -1 if residue == p - 1 else residue


def prime_data(p: int, t_primes: tuple[int, ...]) -> tuple[int, int | None, int]:
    """Return ramification index, admissibility witness, and budget cost.

    Witness 1 denotes p = 1 mod 4. None denotes failure. For p=2 the
    inertness witness is q=5 mod 8. Split primes are allowed and cost two.
    """
    ramification = 2 if p == 2 or p in t_primes else 1
    if p % 4 == 1:
        witness = 1
    elif p == 2:
        witness = next((q for q in t_primes if q % 8 == 5), None)
    else:
        witness = next((q for q in t_primes if legendre(q, p) == -1), None)
    if ramification == 2:
        cost = 1
    else:
        symbol = math.prod(legendre(q, p) for q in t_primes)
        cost = 2 if symbol == 1 else 1
    return ramification, witness, cost


def gs_budget(t: int) -> int:
    """Integer version of |S| + split(S) <= (t-1)^2/4 - t - 1."""
    return ((t - 1) ** 2 - 4 * t - 4) // 4


def validate_t(t_primes: Iterable[int]) -> tuple[int, ...]:
    values = tuple(t_primes)
    if not values or len(set(values)) != len(values):
        raise ValueError("T must be nonempty and contain distinct primes.")
    if any(not is_prime(q) or q == 2 for q in values):
        raise ValueError("T must consist of odd primes.")
    if sum(q % 4 == 3 for q in values) % 2 != 1:
        raise ValueError("T must have an odd number of primes congruent to 3 mod 4.")
    if gs_budget(len(values)) < 0:
        raise ValueError("T does not supply a nonnegative Golod-Shafarevich budget.")
    return tuple(sorted(values))


def validate_certificate(
    t_primes: Iterable[int], multiplicities: dict[int, int], radius: Fraction
) -> dict:
    values = validate_t(t_primes)
    if not isinstance(radius, Fraction) or radius <= 1:
        raise ValueError("R must be an exact rational greater than one.")
    if not multiplicities:
        raise ValueError("S must be nonempty.")
    entries = []
    for p, k in sorted(multiplicities.items()):
        if not is_prime(p) or type(k) is not int or k < 1:
            raise ValueError("S must contain primes with positive integer multiplicities.")
        e, witness, cost = prime_data(p, values)
        if witness is None:
            raise ValueError(f"Prime {p} lacks a Lemma 12 admissibility witness.")
        entries.append({"p": p, "k": k, "e": e, "witness_q_or_1_mod_4": witness,
                        "budget_cost": cost})
    used = sum(row["budget_cost"] for row in entries)
    budget = gs_budget(len(values))
    if used > budget:
        raise ValueError(f"Golod-Shafarevich budget exceeded: {used} > {budget}.")
    return {"T": list(values), "T_size": len(values), "S_size": len(entries),
            "split_count": sum(row["budget_cost"] == 2 for row in entries),
            "budget": budget, "budget_used": used, "R": str(radius),
            "multiplicity_histogram": dict(sorted(Counter(multiplicities.values()).items())),
            "entries": entries}


@dataclass(frozen=True)
class Interval:
    lo: Decimal
    hi: Decimal

    def serializable(self) -> dict[str, str]:
        return {"lower": str(self.lo), "upper": str(self.hi)}


class IntervalArithmetic:
    """Directed decimal arithmetic; ln/exp are correctly rounded by Decimal.

    One adjacent representable number on either side encloses a correctly
    rounded transcendental result. No binary floats enter interval endpoints.
    """

    def __init__(self, precision: int = 60):
        if precision < 25:
            raise ValueError("Use at least 25 significant decimal digits.")
        self.precision = precision
        self.down = Context(prec=precision, rounding=ROUND_FLOOR)
        self.up = Context(prec=precision, rounding=ROUND_CEILING)
        self.near = Context(prec=precision, rounding=ROUND_HALF_EVEN)

    def number(self, value: int | str | Fraction) -> Interval:
        if isinstance(value, Fraction):
            a, b = Decimal(value.numerator), Decimal(value.denominator)
            return Interval(self.down.divide(a, b), self.up.divide(a, b))
        if isinstance(value, float):
            raise TypeError("Use an exact string or Fraction, not a binary float.")
        decimal = Decimal(value)
        return Interval(decimal, decimal)

    def add(self, x: Interval, y: Interval) -> Interval:
        return Interval(self.down.add(x.lo, y.lo), self.up.add(x.hi, y.hi))

    def sub(self, x: Interval, y: Interval) -> Interval:
        return Interval(self.down.subtract(x.lo, y.hi), self.up.subtract(x.hi, y.lo))

    def mul(self, x: Interval, y: Interval) -> Interval:
        pairs = [(a, b) for a in (x.lo, x.hi) for b in (y.lo, y.hi)]
        return Interval(min(self.down.multiply(a, b) for a, b in pairs),
                        max(self.up.multiply(a, b) for a, b in pairs))

    def div(self, x: Interval, y: Interval) -> Interval:
        if y.lo <= 0 <= y.hi:
            raise ValueError("Interval division by an interval containing zero.")
        pairs = [(a, b) for a in (x.lo, x.hi) for b in (y.lo, y.hi)]
        return Interval(min(self.down.divide(a, b) for a, b in pairs),
                        max(self.up.divide(a, b) for a, b in pairs))

    def ln(self, x: Interval) -> Interval:
        if x.lo <= 0:
            raise ValueError("Logarithm requires a positive interval.")
        return Interval(self.near.next_minus(self.near.ln(x.lo)),
                        self.near.next_plus(self.near.ln(x.hi)))

    def exp(self, x: Interval) -> Interval:
        return Interval(self.near.next_minus(self.near.exp(x.lo)),
                        self.near.next_plus(self.near.exp(x.hi)))

    def scale(self, x: Interval, value: int | Fraction) -> Interval:
        return self.mul(x, self.number(value))


@lru_cache(maxsize=None)
def pi_bounds(terms: int) -> tuple[Fraction, Fraction]:
    """Machin's identity with exact alternating-series remainder bounds."""
    def atan_bounds(n: int) -> tuple[Fraction, Fraction]:
        total = sum((Fraction((-1) ** j, (2 * j + 1) * n ** (2 * j + 1))
                     for j in range(terms)), Fraction())
        remainder = Fraction(1, (2 * terms + 1) * n ** (2 * terms + 1))
        return (total, total + remainder) if terms % 2 == 0 else (total - remainder, total)
    a, b = atan_bounds(5), atan_bounds(239)
    return 16 * a[0] - 4 * b[1], 16 * a[1] - 4 * b[0]


def evaluate_certificate(
    t_primes: Iterable[int], multiplicities: dict[int, int], radius: Fraction,
    precision: int = 60,
) -> dict:
    result = validate_certificate(t_primes, multiplicities, radius)
    ar = IntervalArithmetic(precision)
    one = ar.number(1)
    pi_lo, pi_hi = pi_bounds(precision + 5)
    pi = Interval(ar.number(pi_lo).lo, ar.number(pi_hi).hi)
    log_disc = ar.ln(ar.number(4))
    for q in result["T"]:
        log_disc = ar.add(log_disc, ar.ln(ar.number(q)))
    numerator = ar.ln(ar.number(1 - 1 / radius))
    numerator = ar.add(numerator, ar.scale(ar.sub(ar.ln(ar.scale(pi, 2)), one), Fraction(1, 2)))
    numerator = ar.sub(numerator, ar.scale(log_disc, Fraction(1, 8)))
    numerator = ar.sub(numerator, ar.scale(ar.ln(ar.scale(log_disc, Fraction(1, 2))), Fraction(1, 2)))
    log_size = ar.ln(ar.number(2 * radius))
    for row in result["entries"]:
        p, k, e = row["p"], row["k"], row["e"]
        numerator = ar.add(numerator, ar.scale(ar.ln(ar.number(k + 1)), Fraction(1, 4 * e)))
        log_size = ar.add(log_size, ar.scale(ar.ln(ar.number(p)), Fraction(k, 2 * e)))
    # Retain the +1 in equation (11), including when it is below float resolution.
    correction = ar.ln(ar.add(one, ar.exp(ar.scale(log_size, -1))))
    denominator = ar.add(log_size, correction)
    delta = ar.div(numerator, denominator)
    result.update({"precision": precision, "numerator": numerator.serializable(),
                   "denominator": denominator.serializable(),
                   "delta": delta.serializable(),
                   "exponent": ar.add(one, delta).serializable(),
                   "arithmetic_conditions_valid": True,
                   "scope": "Sawin equation (11); theorem assumptions supplied by Lemma 12"})
    return result


def best_multiplicity_float(p: int, delta: float) -> int:
    """Optimizer of log(k+1) - 2*delta*k*log(p), including k=0."""
    return max(0, math.floor(1 / math.expm1(2 * delta * math.log(p))))


def choose_weighted(items: list[tuple[float, int, int, int]], budget: int
                    ) -> tuple[float, list[tuple[float, int, int, int]]]:
    """Exact combinatorial optimization for supplied float profits, weights 1/2.

    Each row is (profit, weight, prime, multiplicity). Numeric profit comparisons
    are exploratory; the returned finite certificate is checked independently.
    """
    groups = [sorted((r for r in items if r[1] == w and r[0] > 0),
                     key=lambda r: (-r[0], r[2])) for w in (1, 2)]
    prefixes = []
    for rows in groups:
        values = [0.0]
        for row in rows:
            values.append(values[-1] + row[0])
        prefixes.append(values)
    best = (0.0, 0, 0)
    for count_two in range(min(len(groups[1]), budget // 2) + 1):
        count_one = min(len(groups[0]), budget - 2 * count_two)
        score = prefixes[0][count_one] + prefixes[1][count_two]
        if score > best[0]:
            best = (score, count_one, count_two)
    return best[0], groups[0][:best[1]] + groups[1][:best[2]]


def optimize_fixed_t(t_primes: Iterable[int], prime_limit: int = 100_000,
                     precision: int = 60) -> dict:
    """Deterministic fixed-T search, followed by interval certificate validation.

    Search maximizes N-delta*D0 where D0 omits the final +1 inside the logarithm.
    This is an upper relaxation, not an exact optimizer of the original ratio.
    The evaluated returned certificate DOES retain the +1.
    """
    values = validate_t(t_primes)
    if prime_limit < max(values):
        raise ValueError("Candidate prime limit must cover T.")
    candidates = []
    for p in primes_up_to(prime_limit):
        e, witness, cost = prime_data(p, values)
        if witness is not None:
            candidates.append((p, e, cost))
    log_disc = math.log(4) + math.fsum(math.log(q) for q in values)
    constant = math.log(2 * math.pi / math.e) / 2 - log_disc / 8 - math.log(log_disc / 2) / 2

    def objective(delta: float) -> tuple[float, list[tuple[float, int, int, int]]]:
        items = []
        for p, e, cost in candidates:
            k = best_multiplicity_float(p, delta)
            if k:
                profit = (math.log(k + 1) - 2 * delta * k * math.log(p)) / (4 * e)
                items.append((profit, cost, p, k))
        gain, chosen = choose_weighted(items, gs_budget(len(values)))
        radius = 1 + 1 / delta
        residual = constant + math.log1p(-1 / radius) - delta * math.log(2 * radius) + gain
        return residual, chosen

    lower, upper = 0.001, 0.1
    if objective(lower)[0] <= 0 or objective(upper)[0] >= 0:
        raise ValueError("Search root is outside the declared delta bracket.")
    for _ in range(55):
        mid = (lower + upper) / 2
        if objective(mid)[0] > 0:
            lower = mid
        else:
            upper = mid
    delta = (lower + upper) / 2
    chosen = objective(delta)[1]
    radius = Fraction(str(1 + 1 / delta)).limit_denominator(10 ** 12)
    result = evaluate_certificate(values, {r[2]: r[3] for r in chosen}, radius, precision)
    result["search"] = {"candidate_prime_limit": prime_limit,
                        "relaxed_root_float": delta,
                        "global_optimality_claim": False,
                        "method": "fractional objective; weight-1/2 prefix optimization"}
    return result


def profitable_prime_cutoff(delta: Fraction) -> int:
    """Largest integer p satisfying p^(2*delta) < 2, using exact integers."""
    if not isinstance(delta, Fraction) or delta <= 0:
        raise ValueError("delta must be a positive Fraction.")
    power = 2 * delta
    a, b = power.numerator, power.denominator
    if max(a, b) > 100_000:
        raise ValueError("Rational exponent is too large for this exact-power check.")
    rhs = 2 ** b
    if MAX_PRIME_LIMIT ** a < rhs:
        raise ValueError("Profitable-prime cutoff exceeds the resource cap.")
    lo, hi = 1, MAX_PRIME_LIMIT
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if mid ** a < rhs:
            lo = mid
        else:
            hi = mid
    return lo


def best_multiplicity_exact(p: int, delta: Fraction) -> int:
    """Verify the maximizing integer by exact adjacent-increment comparisons."""
    power = 2 * delta
    a, b = power.numerator, power.denominator
    p_power = p ** a
    k = best_multiplicity_float(p, float(delta))
    # Equality permits either neighbor; choose the larger maximizer.
    while (k + 2) ** b >= (k + 1) ** b * p_power:
        k += 1
    while k > 0 and (k + 1) ** b < k ** b * p_power:
        k -= 1
    return k


def bound_original_formula(delta: Fraction, precision: int = 60) -> dict:
    """Uniform upper certificate for equation (11), across ALL valid finite T.

    Replace every budget cost by 1, every e(p) by 1, and T's discriminant by
    that of the first |T| odd primes. These changes all enlarge N-delta*D0.
    For fixed t, the largest K(t) positive profits come from the smallest primes.
    Once K(t) covers every positive-profit prime, the tail decreases forever.
    A negative upper endpoint therefore excludes this delta in equation (11).
    """
    cutoff = profitable_prime_cutoff(delta)
    primes = primes_up_to(cutoff)
    ar = IntervalArithmetic(precision)
    radius = 1 + 1 / delta
    radius_term = ar.sub(ar.ln(ar.number(1 - 1 / radius)),
                         ar.scale(ar.ln(ar.number(2 * radius)), delta))
    # pi < 22/7 is deliberately a generous upper bound on the constant.
    constant = ar.scale(ar.sub(ar.ln(ar.number(Fraction(44, 7))), ar.number(1)), Fraction(1, 2))
    prefix = [ar.number(0)]
    multiplicities = []
    for p in primes:
        k = best_multiplicity_exact(p, delta)
        profit = ar.scale(ar.sub(ar.ln(ar.number(k + 1)),
                                ar.scale(ar.ln(ar.number(p)), 2 * delta * k)), Fraction(1, 4))
        if profit.lo <= 0:
            raise ArithmeticError("Insufficient precision to certify positive prime profit.")
        prefix.append(ar.add(prefix[-1], profit))
        multiplicities.append(k)
    # The cutoff has at least the small primes for all intended thresholds.
    t_stop = 7
    while gs_budget(t_stop) < len(primes):
        t_stop += 1
    odd_primes = primes_up_to(max(1000, cutoff))[1:]
    if len(odd_primes) < t_stop:
        raise ValueError("Prime inventory is insufficient for the tail certificate.")
    log_disc = ar.ln(ar.number(4))
    rows = []
    for t, q in enumerate(odd_primes[:t_stop], 1):
        log_disc = ar.add(log_disc, ar.ln(ar.number(q)))
        budget = gs_budget(t)
        if budget < 0:
            continue
        residual = ar.add(radius_term, constant)
        residual = ar.sub(residual, ar.scale(log_disc, Fraction(1, 8)))
        residual = ar.sub(residual, ar.scale(ar.ln(ar.scale(log_disc, Fraction(1, 2))), Fraction(1, 2)))
        residual = ar.add(residual, prefix[min(budget, len(primes))])
        rows.append({"t": t, "budget": budget, "residual": residual.serializable()})
    worst = max(rows, key=lambda row: Decimal(row["residual"]["upper"]))
    return {"scope": "Upper bound on Sawin equation (11), NOT on u(n)",
            "target_delta": str(delta), "excluded_exponent_if_certified": str(1 + delta),
            "precision": precision, "prime_cutoff_inclusive": cutoff,
            "positive_profit_prime_count": len(primes), "last_profitable_prime": primes[-1] if primes else None,
            "max_multiplicity": max(multiplicities, default=0), "tail_starts_at_t": t_stop,
            "pi_upper_bound": "22/7", "worst_case": worst,
            "excluded": Decimal(worst["residual"]["upper"]) < 0,
            "tail_reason": "All positive prime profits included; discriminant penalty strictly increases with t.",
            "rows": rows}


def run_investigation(precision: int, target_delta: Fraction) -> dict:
    baseline = evaluate_certificate(SAWIN_T, dict(zip(SAWIN_S, SAWIN_K)), Fraction(72), precision)
    first_74 = primes_up_to(1000)[1:75]
    forum_t = sorted((set(first_74) - {347, 353, 379}) | {503, 601, 631})
    optimized = optimize_fixed_t(forum_t, precision=precision)
    return {"schema_version": 1, "evidence_layer": "external_probe",
            "source_formula": "https://arxiv.org/html/2605.20579v1",
            "forum_T_source": "https://mathoverflow.net/questions/511514/what-is-the-unit-distance-exponent",
            "sawin_reproduction": baseline, "forum_T_reoptimization": optimized,
            "original_formula_upper_certificate": bound_original_formula(target_delta, precision)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--precision", type=int, default=60)
    parser.add_argument("--target-delta", type=Fraction, default=Fraction(351, 10_000))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error("Output already exists; use a new versioned filename.")
    result = run_investigation(args.precision, args.target_delta)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    summary = {name: {key: value[key] for key in ("T_size", "S_size", "split_count", "exponent")}
               for name, value in result.items() if name.endswith(("reproduction", "reoptimization"))}
    bound = result["original_formula_upper_certificate"]
    summary["original_formula_upper_certificate"] = {
        key: bound[key] for key in ("target_delta", "excluded", "prime_cutoff_inclusive",
                                   "positive_profit_prime_count", "tail_starts_at_t", "worst_case")}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
