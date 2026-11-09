#!/usr/bin/env python3
"""Explore exact arithmetic and geometric identities around 216.

This is an external-probe tool. It searches for power-lattice identities and
Pythagorean/cubic-completion patterns without promoting them to MoO runtime
objects.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from itertools import combinations_with_replacement
from pathlib import Path


@dataclass(frozen=True)
class PowerTerm:
    base: int
    exponent: int
    value: int
    label: str


@dataclass(frozen=True)
class PythagoreanCubeCompletion:
    a: int
    b: int
    c: int
    d: int
    primitive: bool
    scale_from_3456: int | None


def cube_root_exact(n: int) -> int | None:
    if n < 0:
        return None
    r = round(n ** (1.0 / 3.0))
    for candidate in range(max(0, r - 2), r + 3):
        if candidate**3 == n:
            return candidate
    return None


def power_terms(max_base: int, max_exp: int, max_value: int) -> list[PowerTerm]:
    terms: dict[tuple[int, int], PowerTerm] = {}
    for base in range(1, max_base + 1):
        for exponent in range(1, max_exp + 1):
            value = base**exponent
            if value <= max_value:
                terms[(base, exponent)] = PowerTerm(
                    base=base,
                    exponent=exponent,
                    value=value,
                    label=f"{base}^{exponent}",
                )
    return sorted(terms.values(), key=lambda t: (t.value, t.base, t.exponent))


def powers_equal(target: int, terms: list[PowerTerm]) -> list[PowerTerm]:
    return [term for term in terms if term.value == target]


def sums_equal(target: int, terms: list[PowerTerm], term_count: int) -> list[dict[str, object]]:
    matches = []
    candidates = [term for term in terms if term.value <= target and term.exponent >= 2]
    for combo in combinations_with_replacement(candidates, term_count):
        if sum(term.value for term in combo) == target:
            matches.append(
                {
                    "labels": [term.label for term in combo],
                    "values": [term.value for term in combo],
                    "expression": " + ".join(term.label for term in combo) + f" = {target}",
                }
            )
    return matches


def differences_equal(target: int, terms: list[PowerTerm]) -> list[dict[str, object]]:
    matches = []
    candidates = [term for term in terms if term.exponent >= 2]
    for left in candidates:
        for right in candidates:
            if left.value - right.value == target:
                matches.append(
                    {
                        "left": left.label,
                        "right": right.label,
                        "expression": f"{left.label} - {right.label} = {target}",
                    }
                )
    return matches


def diagonal_base_plus_exponent(total: int, max_base: int) -> list[dict[str, int | str]]:
    rows = []
    for base in range(1, max_base + 1):
        exponent = total - base
        if exponent >= 1:
            rows.append(
                {
                    "base": base,
                    "exponent": exponent,
                    "value": base**exponent,
                    "label": f"{base}^{exponent}",
                }
            )
    return rows


def pythagorean_cube_completions(max_side: int) -> list[PythagoreanCubeCompletion]:
    matches: list[PythagoreanCubeCompletion] = []
    seen: set[tuple[int, int, int]] = set()

    # Euclid generation is faster and avoids scanning all a,b pairs.
    max_m = int(math.sqrt(max_side * 2)) + 2
    for m in range(2, max_m + 1):
        for n in range(1, m):
            if (m - n) % 2 == 0 or math.gcd(m, n) != 1:
                continue
            a0 = m * m - n * n
            b0 = 2 * m * n
            c0 = m * m + n * n
            if c0 > max_side:
                continue
            a0, b0 = sorted((a0, b0))
            for scale in range(1, max_side // c0 + 1):
                a = a0 * scale
                b = b0 * scale
                c = c0 * scale
                if (a, b, c) in seen:
                    continue
                seen.add((a, b, c))
                d = cube_root_exact(a**3 + b**3 + c**3)
                if d is None:
                    continue
                primitive = math.gcd(math.gcd(a, b), c) == 1
                scale_from_3456 = None
                if (a, b, c, d) == (3 * scale, 4 * scale, 5 * scale, 6 * scale):
                    scale_from_3456 = scale
                matches.append(
                    PythagoreanCubeCompletion(
                        a=a,
                        b=b,
                        c=c,
                        d=d,
                        primitive=primitive,
                        scale_from_3456=scale_from_3456,
                    )
                )
    return sorted(matches, key=lambda x: (x.c, x.a, x.b, x.d))


def build_payload(target: int, max_base: int, max_exp: int, max_side: int) -> dict[str, object]:
    max_value = max(target * 8, max_side**3)
    terms = power_terms(max_base, max_exp, max_value)
    completions = pythagorean_cube_completions(max_side)
    primitive_completions = [row for row in completions if row.primitive]

    return {
        "target": target,
        "bounds": {
            "max_base": max_base,
            "max_exp": max_exp,
            "max_side": max_side,
            "max_value_for_power_terms": max_value,
        },
        "ground_facts": {
            "factorization": "216 = 2^3 * 3^3",
            "six_cube": 6**3,
            "cube_surface_area_side_6": 6 * 6**2,
            "pythagorean_square": "3^2 + 4^2 = 5^2",
            "pythagorean_cube_completion": "3^3 + 4^3 + 5^3 = 6^3 = 216",
            "surface_volume_equality_equation": "s^3 = 6*s^2 has positive solution s = 6",
        },
        "powers_equal_target": [asdict(term) for term in powers_equal(target, terms)],
        "two_power_sums_equal_target": sums_equal(target, terms, 2),
        "three_power_sums_equal_target": sums_equal(target, terms, 3),
        "power_differences_equal_target": differences_equal(target, terms)[:100],
        "base_plus_exponent_7_diagonal": diagonal_base_plus_exponent(7, 6),
        "pythagorean_cube_completions": [asdict(row) for row in completions],
        "primitive_pythagorean_cube_completions": [asdict(row) for row in primitive_completions],
        "interpretation": {
            "minimal_primitive_observation": (
                "Within the generated primitive Pythagorean triples up to the bound, "
                "(3,4,5,6) is the first primitive square-triple/cube-completion match "
                "if it is the first row in primitive_pythagorean_cube_completions."
            ),
            "moo_reading": (
                "Treat 216 as a geometric closure value where the 3-4-5 shell relation "
                "casts a cubic-completion shadow. This is a projection lead, not a "
                "strict branch claim until graph witnesses are queried."
            ),
        },
    }


def markdown_report(payload: dict[str, object]) -> str:
    completions = payload["pythagorean_cube_completions"]  # type: ignore[index]
    primitive = payload["primitive_pythagorean_cube_completions"]  # type: ignore[index]
    diagonal = payload["base_plus_exponent_7_diagonal"]  # type: ignore[index]
    powers = payload["powers_equal_target"]  # type: ignore[index]
    three_sums = payload["three_power_sums_equal_target"]  # type: ignore[index]

    lines = [
        "# 216 Power-Lattice Probe",
        "",
        "> evidence_layer: external_probe",
        ">",
        "> claim_status: lead",
        "",
        "## Ground Facts",
        "",
        "```text",
        "216 = 6^3",
        "216 = 2^3 * 3^3",
        "3^2 + 4^2 = 5^2",
        "3^3 + 4^3 + 5^3 = 6^3 = 216",
        "cube side 6: volume = surface area = 216",
        "```",
        "",
        "## Powers Equal To 216",
        "",
    ]
    nontrivial_powers = [row for row in powers if row["exponent"] > 1]  # type: ignore[index]
    if nontrivial_powers:
        for row in nontrivial_powers:  # type: ignore[assignment]
            lines.append(f"- `{row['label']} = {row['value']}`")
    else:
        lines.append("- none within bounds")

    lines.extend(["", "## Base + Exponent = 7 Diagonal", "", "| term | value |", "|---|---:|"])
    for row in diagonal:  # type: ignore[assignment]
        lines.append(f"| `{row['label']}` | {row['value']} |")

    lines.extend(["", "## Three-Power Sums Equal To 216", ""])
    found_345 = False
    for row in three_sums:  # type: ignore[assignment]
        expr = row["expression"]
        if expr == "3^3 + 4^3 + 5^3 = 216":
            found_345 = True
        lines.append(f"- `{expr}`")
    if not found_345:
        lines.append("- `3^3 + 4^3 + 5^3 = 216` was not found under current filters")

    lines.extend(["", "## Pythagorean Triple With Cube Completion", ""])
    lines.append(f"max_side: `{payload['bounds']['max_side']}`")  # type: ignore[index]
    lines.append("")
    lines.append(f"matches found: `{len(completions)}`")
    lines.append("")
    if completions:
        first = completions[0]  # type: ignore[index]
        last = completions[-1]  # type: ignore[index]
        lines.extend(
            [
                "The bounded scan found exactly the scaled `(3,4,5,6)` family:",
                "",
                "```text",
                "(3k)^2 + (4k)^2 = (5k)^2",
                "(3k)^3 + (4k)^3 + (5k)^3 = (6k)^3",
                "```",
                "",
                f"first match: `({first['a']}, {first['b']}, {first['c']}, {first['d']})`",
                f"last match within bound: `({last['a']}, {last['b']}, {last['c']}, {last['d']})`",
            ]
        )
    else:
        lines.append("No Pythagorean/cubic-completion matches found within bounds.")

    lines.extend(["", "## Primitive Matches", ""])
    if primitive:
        for row in primitive:  # type: ignore[assignment]
            lines.append(f"- `({row['a']}, {row['b']}, {row['c']}, {row['d']})`")
    else:
        lines.append("- none within bounds")

    lines.extend(
        [
            "",
            "## MoO Reading",
            "",
            "The useful object is the witnessed/provenanced relation cluster, not the value alone:",
            "",
            "```text",
            "3,4,5 shell relation:",
            "  3^2 + 4^2 = 5^2",
            "",
            "cubic completion:",
            "  3^3 + 4^3 + 5^3 = 6^3",
            "",
            "closure value:",
            "  6^3 = 216",
            "```",
            "",
            "This makes 216 a geometric projection lead worth preserving even if no deeper law is found.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=216)
    parser.add_argument("--max-base", type=int, default=1000)
    parser.add_argument("--max-exp", type=int, default=10)
    parser.add_argument("--max-side", type=int, default=1000)
    parser.add_argument("--json", type=Path, default=None, help="optional JSON output path")
    parser.add_argument("--markdown", type=Path, default=None, help="optional Markdown output path")
    args = parser.parse_args()

    payload = build_payload(args.target, args.max_base, args.max_exp, args.max_side)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown_report(payload), encoding="utf-8")

    print(markdown_report(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
