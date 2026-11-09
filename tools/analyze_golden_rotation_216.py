#!/usr/bin/env python3
"""Golden-ratio modulus-one analysis around 72/144/216.

This is an external-probe tool. It does not make MoO runtime claims. It records
deterministic circle-rotation facts that can later be compared with strict
graph witnesses.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


TARGET_STEPS = (72, 144, 216, 231, 233)


@dataclass(frozen=True)
class RotationPoint:
    n: int
    frac: float
    distance_to_identity: float
    distance_to_half_turn: float


@dataclass(frozen=True)
class StepRank:
    n: int
    identity_rank: int
    half_turn_rank: int
    frac: float
    distance_to_identity: float
    distance_to_half_turn: float


def frac(x: float) -> float:
    return x - math.floor(x)


def distance_to_identity(x: float) -> float:
    y = frac(x)
    return min(y, 1.0 - y)


def distance_to_half_turn(x: float) -> float:
    return abs(frac(x) - 0.5)


def rotation_point(n: int, alpha: float) -> RotationPoint:
    y = frac(n * alpha)
    return RotationPoint(
        n=n,
        frac=y,
        distance_to_identity=min(y, 1.0 - y),
        distance_to_half_turn=abs(y - 0.5),
    )


def fibonacci_pairs(max_denominator: int) -> list[dict[str, int | str]]:
    """Return phi convergents F(n+1)/F(n) up to max denominator."""

    pairs: list[dict[str, int | str]] = []
    a, b = 1, 1
    index = 1
    while a <= max_denominator:
        pairs.append(
            {
                "index": index,
                "numerator": b,
                "denominator": a,
                "fraction": f"{b}/{a}",
            }
        )
        a, b = b, a + b
        index += 1
    return pairs


def continued_fraction(x: float, terms: int) -> list[int]:
    out: list[int] = []
    y = x
    for _ in range(terms):
        a = math.floor(y)
        out.append(a)
        r = y - a
        if abs(r) < 1e-15:
            break
        y = 1.0 / r
    return out


def convergents_from_cf(cf: Iterable[int]) -> list[dict[str, int | str]]:
    p_nm2, p_nm1 = 0, 1
    q_nm2, q_nm1 = 1, 0
    out: list[dict[str, int | str]] = []
    for i, a in enumerate(cf):
        p = a * p_nm1 + p_nm2
        q = a * q_nm1 + q_nm2
        out.append({"index": i, "numerator": p, "denominator": q, "fraction": f"{p}/{q}"})
        p_nm2, p_nm1 = p_nm1, p
        q_nm2, q_nm1 = q_nm1, q
    return out


def ranks_for_steps(alpha: float, limit: int, steps: Iterable[int]) -> list[StepRank]:
    points = [rotation_point(n, alpha) for n in range(1, limit + 1)]
    identity_order = sorted(points, key=lambda p: (p.distance_to_identity, p.n))
    half_order = sorted(points, key=lambda p: (p.distance_to_half_turn, p.n))
    identity_rank = {p.n: i + 1 for i, p in enumerate(identity_order)}
    half_rank = {p.n: i + 1 for i, p in enumerate(half_order)}
    by_n = {p.n: p for p in points}

    ranked = []
    for n in steps:
        p = by_n[n]
        ranked.append(
            StepRank(
                n=n,
                identity_rank=identity_rank[n],
                half_turn_rank=half_rank[n],
                frac=p.frac,
                distance_to_identity=p.distance_to_identity,
                distance_to_half_turn=p.distance_to_half_turn,
            )
        )
    return ranked


def top_points(alpha: float, limit: int, by: str, count: int = 12) -> list[RotationPoint]:
    points = [rotation_point(n, alpha) for n in range(1, limit + 1)]
    if by == "identity":
        return sorted(points, key=lambda p: (p.distance_to_identity, p.n))[:count]
    if by == "half_turn":
        return sorted(points, key=lambda p: (p.distance_to_half_turn, p.n))[:count]
    raise ValueError(f"unknown ranking field: {by}")


def compare_constants(limit: int) -> list[dict[str, object]]:
    constants = {
        "phi": (1.0 + math.sqrt(5.0)) / 2.0,
        "sqrt2": math.sqrt(2.0),
        "sqrt3": math.sqrt(3.0),
        "e": math.e,
        "pi": math.pi,
        "tau": math.tau,
        "ln2": math.log(2.0),
    }
    rows = []
    for name, value in constants.items():
        ranked = ranks_for_steps(value, limit, TARGET_STEPS)
        cf = continued_fraction(value, 14)
        rows.append(
            {
                "name": name,
                "value": value,
                "continued_fraction_prefix": cf,
                "target_step_ranks": [asdict(r) for r in ranked],
                "top_identity_returns": [asdict(p) for p in top_points(value, limit, "identity", 8)],
                "top_half_turns": [asdict(p) for p in top_points(value, limit, "half_turn", 8)],
            }
        )
    return rows


def write_plot(path: Path, alpha: float) -> str:
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local optional package
        return f"plot_skipped: matplotlib unavailable ({exc})"

    fig, axes = plt.subplots(1, 3, figsize=(12, 4), subplot_kw={"aspect": "equal"})
    for ax, n in zip(axes, (72, 144, 216)):
        xs = []
        ys = []
        for k in range(1, n + 1):
            angle = math.tau * frac(k * alpha)
            xs.append(math.cos(angle))
            ys.append(math.sin(angle))
        ax.scatter(xs, ys, s=8)
        final_angle = math.tau * frac(n * alpha)
        ax.scatter([math.cos(final_angle)], [math.sin(final_angle)], s=60, marker="x")
        ax.set_title(f"N={n}")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("Golden-ratio rotation: final point marked with x")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return str(path)


def markdown_report(payload: dict[str, object]) -> str:
    phi_data = payload["phi"]  # type: ignore[index]
    target_points = phi_data["target_points"]  # type: ignore[index]
    ranks = phi_data["target_step_ranks"]  # type: ignore[index]
    identity = phi_data["top_identity_returns"]  # type: ignore[index]
    half = phi_data["top_half_turns"]  # type: ignore[index]

    def row_for_points(row: dict[str, object]) -> str:
        return (
            f"| {row['n']} | {row['frac']:.15f} | "
            f"{row['distance_to_identity']:.15f} | {row['distance_to_half_turn']:.15f} |"
        )

    lines = [
        "# Golden Rotation 216 Analysis",
        "",
        "> evidence_layer: external_probe",
        ">",
        "> claim_status: lead",
        "",
        "## Phi Constants",
        "",
        f"- `phi = {phi_data['value']:.15f}`",
        f"- `phi^-12 = {phi_data['phi_inverse_12']:.15f}`",
        "- exact identity used: `144*phi = 233 - phi^-12`",
        "",
        "## Target Steps",
        "",
        "| n | frac(n*phi) | distance to identity | distance to half-turn |",
        "|---:|---:|---:|---:|",
    ]
    lines.extend(row_for_points(row) for row in target_points)  # type: ignore[arg-type]
    lines.extend(
        [
            "",
            "## Target Step Ranks Up To Limit",
            "",
            f"limit: `{payload['limit']}`",
            "",
            "| n | identity rank | half-turn rank |",
            "|---:|---:|---:|",
        ]
    )
    for row in ranks:  # type: ignore[assignment]
        lines.append(f"| {row['n']} | {row['identity_rank']} | {row['half_turn_rank']} |")
    lines.extend(
        [
            "",
            "## Best Identity Returns",
            "",
            "| n | frac(n*phi) | distance to identity | distance to half-turn |",
            "|---:|---:|---:|---:|",
        ]
    )
    lines.extend(row_for_points(row) for row in identity)  # type: ignore[arg-type]
    lines.extend(
        [
            "",
            "## Best Half-Turns",
            "",
            "| n | frac(n*phi) | distance to identity | distance to half-turn |",
            "|---:|---:|---:|---:|",
        ]
    )
    lines.extend(row_for_points(row) for row in half)  # type: ignore[arg-type]
    lines.extend(
        [
            "",
            "## MoO Reading",
            "",
            "`144` is the strong two-memory recurrence-frame / golden-rotation near-return.",
            "`72` and `216` are half-turn echoes around that return.",
            "`231` is not a phi return point; its value is mainly combinatorial unless another branch witnesses it.",
            "",
        ]
    )
    return "\n".join(lines)


def build_payload(limit: int, plot_path: Path | None) -> dict[str, object]:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    phi_points = [asdict(rotation_point(n, phi)) for n in TARGET_STEPS]
    payload: dict[str, object] = {
        "limit": limit,
        "target_steps": TARGET_STEPS,
        "phi": {
            "value": phi,
            "phi_inverse_12": phi ** -12,
            "identity_144": "144*phi = 233 - phi^-12",
            "target_points": phi_points,
            "target_step_ranks": [asdict(r) for r in ranks_for_steps(phi, limit, TARGET_STEPS)],
            "fibonacci_convergents": fibonacci_pairs(limit),
            "top_identity_returns": [asdict(p) for p in top_points(phi, limit, "identity", 12)],
            "top_half_turns": [asdict(p) for p in top_points(phi, limit, "half_turn", 12)],
        },
        "constant_comparison": compare_constants(limit),
    }
    if plot_path is not None:
        payload["plot"] = write_plot(plot_path, phi)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--json", type=Path, default=None, help="optional JSON output path")
    parser.add_argument("--markdown", type=Path, default=None, help="optional Markdown output path")
    parser.add_argument("--plot", type=Path, default=None, help="optional PNG plot path")
    args = parser.parse_args()

    payload = build_payload(args.limit, args.plot)

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
