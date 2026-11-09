"""Finite Julia/phase calibrations over immutable strict MoO corpora.

This is an external inspection experiment, not a runtime extension. Arithmetic
orbits are calculated externally; every claimed graph witness is queried.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from moo_graph_evidence import GraphEvidence

EXPERIMENT = "julia_branch_localization_20260912_v1"
CORPORA = {
    "u300": "out/experiments/pascal_edge_probe_u300.sqlite",
    "u40": "out/experiments/circle_as_one_u40_wide.sqlite",
    "u80": "out/experiments/circle_as_one_u80.sqlite",
}
DENOMINATORS = list(range(2, 17)) + [31]
CHECKPOINTS = [2, 4, 8, 16, 40, 80, 256, 300]
F = Fraction


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def calculate(op: str, a: Fraction, b: Fraction) -> Fraction:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        return a / b
    raise ValueError(op)


def modular_orbit(seed: int, q: int, operation: str) -> dict:
    seen: dict[int, int] = {}
    values: list[int] = []
    n = seed % q
    while n not in seen:
        seen[n] = len(values)
        values.append(n)
        n = (2 * n if operation == "+" else n * n) % q
    return {
        "residues": values + [n],
        "phases": [str(F(v, q)) for v in values + [n]],
        "preperiod": seen[n],
        "period": len(values) - seen[n],
        "first_repeat_index": len(values),
        "evidence_layer": "external_probe",
    }


def doubling_baseline(seed: int, q: int) -> dict:
    denominator = F(seed, q).denominator
    odd = denominator
    tail = 0
    while odd % 2 == 0:
        odd //= 2
        tail += 1
    period = 1
    if odd > 1:
        residue = 2 % odd
        while residue != 1:
            residue = 2 * residue % odd
            period += 1
    return {"effective_denominator": denominator, "odd_part": odd,
            "preperiod": tail, "period": period}


def complex_orbit(c: tuple[Fraction, Fraction], budget: int = 8) -> dict:
    """Exact external critical orbit, with a conservative escape certificate."""
    a, b = c
    x, y = F(0), F(0)
    seen = {(x, y): 0}
    states = [{"real": "0", "imag": "0"}]
    radius_squared = max(F(4), a * a + b * b)
    outcome = "unresolved_after_budget"
    detail: dict = {}
    for k in range(1, budget + 1):
        x, y = x * x - y * y + a, 2 * x * y + b
        states.append({"real": str(x), "imag": str(y)})
        if x * x + y * y > radius_squared:
            outcome = "certified_escape"
            detail = {"escape_step": k, "radius_squared": str(radius_squared),
                      "norm_squared": str(x * x + y * y)}
            break
        if (x, y) in seen:
            outcome = "exact_cycle"
            detail = {"preperiod": seen[(x, y)], "period": k - seen[(x, y)]}
            break
        seen[(x, y)] = k
    return {"parameter": {"real": str(a), "imag": str(b)},
            "seed": {"real": "0", "imag": "0"}, "budget": budget,
            "states": states, "finite_detector": outcome, **detail,
            "evidence_layer": "external_probe", "runtime_orbit": False}


class WitnessRegistry:
    def __init__(self, evidence: GraphEvidence):
        self.evidence = evidence
        self.records: dict[str, dict] = {}

    def get(self, op: str, left: Fraction | int, right: Fraction | int) -> str:
        a, b = F(left), F(right)
        result = calculate(op, a, b)
        key = f"{a} {op} {b} -> {result}"
        if key not in self.records:
            record = self.evidence.edge_witness(
                left=a, op=op, right=b, result=result, edge_limit=4,
                claim_id=key, relation=key,
            )
            # Independent checks of the exact arithmetic and operand status.
            if record["present"]:
                assert record["edge_count"] == 1, (key, record)
                for side in ("left", "right"):
                    node = record[side]
                    assert node["q"] == 1 and node["p"] >= 1
                    assert node["confirmed_stage"] <= record["first_edge_stage"]
                assert F(record["result"]["p"], record["result"]["q"]) == result
                assert record["edge_refs"][0]["stage"] == record["first_edge_stage"]
            self.records[key] = record
        return key

    def complete_at(self, keys: list[str], stage: int) -> bool:
        # GraphEvidence presence is corpus-wide. Explicitly scope every record
        # by its actual edge stage instead of mistaking it for checkpoint data.
        return all(self.records[k]["present"] and
                   self.records[k]["first_edge_stage"] <= stage for k in keys)


def lift_case(registry: WitnessRegistry, q: int, operation: str) -> dict:
    n = 2
    states = []
    steps = []
    for k in range(5):
        division = registry.get("/", n, q)
        states.append({"step": k, "numerator": n, "divisor": q,
                       "rational": str(F(n, q)), "phase": str(F(n, q) % 1),
                       "division_witness": division})
        if k < 4:
            key = registry.get(operation, n, n)
            following = 2 * n if operation == "+" else n * n
            steps.append({"step": k + 1, "source": n, "target": following,
                          "witness": key})
            n = following
    cycle = modular_orbit(2, q, operation)
    needed = cycle["first_repeat_index"]
    cycle_keys = ([s["division_witness"] for s in states[:needed + 1]] +
                  [s["witness"] for s in steps[:needed]])
    cycle_coverage = {}
    for checkpoint in CHECKPOINTS:
        if checkpoint <= registry.evidence.corpus_stage:
            cycle_coverage[str(checkpoint)] = (
                needed <= 4 and registry.complete_at(cycle_keys, checkpoint))
    return {"operation": operation, "seed": 2, "denominator": q,
            "states": states, "steps": steps, "external_cycle": cycle,
            "cycle_witnessed_by_checkpoint": cycle_coverage,
            "cycle_in_declared_lift_budget": needed <= 4,
            "phase_projection_is_external": True}


def scalar_case(registry: WitnessRegistry, name: str, seed: Fraction,
                c: Fraction, budget: int = 4) -> dict:
    x = seed
    seen = {x: 0}
    states = [str(x)]
    steps = []
    cycle = None
    for k in range(1, budget + 1):
        square = x * x
        keys = [registry.get("*", x, x)]
        if c:
            # The chosen witness normal form uses subtraction for a negative
            # real constant; adding a speculative negative is not equivalent
            # as a graph witness. Zero offset omits the redundant addition.
            keys.append(registry.get("+" if c > 0 else "-", square, abs(c)))
        following = square + c
        steps.append({"step": k, "source": str(x), "square": str(square),
                      "target": str(following), "witnesses": keys})
        states.append(str(following))
        if following in seen:
            cycle = {"preperiod": seen[following], "period": k - seen[following]}
            break
        seen[following] = k
        x = following
    coverage = {}
    for checkpoint in CHECKPOINTS:
        if checkpoint <= registry.evidence.corpus_stage:
            prefix = 0
            first_blocker = None
            for step in steps:
                if registry.complete_at(step["witnesses"], checkpoint):
                    prefix += 1
                else:
                    first_blocker = next(
                        key for key in step["witnesses"]
                        if not registry.complete_at([key], checkpoint))
                    break
            coverage[str(checkpoint)] = {"complete_prefix_steps": prefix,
                                         "first_unwitnessed_operation": first_blocker}
    return {"name": name, "seed": str(seed), "c": str(c), "states": states,
            "steps": steps, "external_exact_cycle": cycle,
            "witness_coverage_by_checkpoint": coverage,
            "runtime_replay_performed": False}


def self_check() -> dict:
    checks = []
    for seed in (1, 2):
        for q in DENOMINATORS:
            measured = modular_orbit(seed, q, "+")
            baseline = doubling_baseline(seed, q)
            assert (measured["preperiod"], measured["period"]) == (
                baseline["preperiod"], baseline["period"])
    checks.append("32 doubling profiles equal the independent denominator baseline")
    assert modular_orbit(2, 7, "+")["period"] == 3
    assert modular_orbit(2, 7, "*")["period"] == 2
    checks.append("same initial integer 2 gives different mod-7 periods for + and *")
    assert complex_orbit((F(-1), F(0)))["period"] == 2
    assert complex_orbit((F(-2), F(0)))["preperiod"] == 2
    assert complex_orbit((F(0), F(1)))["period"] == 2
    assert complex_orbit((F(1), F(0)))["finite_detector"] == "certified_escape"
    assert complex_orbit((F(1, 4), F(0)))["finite_detector"] == "unresolved_after_budget"
    checks.append("critical-orbit detector distinguishes exact cycles, escape, and finite uncertainty")
    return {"passed": True, "checks": checks}


def build_report() -> dict:
    report: dict = {
        "report_type": "finite_julia_branch_localization_calibration",
        "experiment_id": EXPERIMENT,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_layer": "external_probe", "claim_status": "observation",
        "claim_boundary": "Exact finite external calibrations with attached strict witnesses; no Julia set, complex operand, new MoO branch, chaos, or predictive effect is established.",
        "exact_command": [sys.executable, "-B", *sys.argv],
        "checkpoints": CHECKPOINTS,
        "metric_definitions": {
            "complete_prefix_steps": "Consecutive declared recurrence steps whose exact primitive edges are retained by a checkpoint.",
            "witnessed_phase_return": "Every declared integer operation and quotient-output edge through the first external repeated phase is present by that checkpoint; never a rational runtime cycle.",
            "period": "Exact cycle length in the declared finite residue map, not graph multiplicity or additive order.",
        },
        "sources": {}, "corpora": {}, "validation": self_check(),
    }
    for relative in [str(Path(__file__).relative_to(ROOT)),
                     f"out/experiments/dynamics/{EXPERIMENT}.pre.md",
                     "moo_graph_evidence.py", "moo_graph_corpus.py"]:
        report["sources"][relative] = sha256(ROOT / relative)
    report["phase_baseline"] = [
        {"seed": seed, "q": q, "orbit": modular_orbit(seed, q, "+"),
         "baseline": doubling_baseline(seed, q)}
        for seed in (1, 2) for q in DENOMINATORS
    ]
    for name, relative in CORPORA.items():
        path = ROOT / relative
        before_hash = sha256(path)
        conn = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
        conn.row_factory = sqlite3.Row
        evidence = GraphEvidence(conn)
        registry = WitnessRegistry(evidence)
        lifts = [lift_case(registry, q, op) for q in DENOMINATORS for op in ("+", "*")]
        specs = [
            ("pure_square_fixed_one", F(1), F(0), 4),
            ("subtract_two_fixed_two", F(2), F(-2), 4),
            ("subtract_one_hits_zero", F(1), F(-1), 4),
            ("add_one_expands", F(1), F(1), 4),
            ("fractional_seed_square", F(1, 2), F(0), 3),
        ]
        scalars = [scalar_case(registry, *spec) for spec in specs]
        fixed_family = []
        for m in range(1, 7):
            c = m - m * m
            case = scalar_case(registry, f"fixed_m{m}", F(m), F(c), 1)
            case["parameter_witness"] = registry.get("-", m, m * m)
            case["external_derivative"] = 2 * m
            case["external_critical_orbit"] = complex_orbit((F(c), F(0)))
            fixed_family.append(case)
        representative_control = []
        for value in (F(1, 3), F(4, 3)):
            representative_control.append({
                "source": str(value), "phase": str(value % 1),
                "arithmetic_square": str(value * value),
                "squared_phase": str((value * value) % 1),
                "square_witness": registry.get("*", value, value),
            })
        meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        corpus = {
            "path": relative, "sha256": before_hash, "bytes": path.stat().st_size,
            "metadata": meta, "recorded_stage": evidence.recorded_corpus_stage,
            "complete_stage": evidence.complete_corpus_stage,
            "lifts": lifts, "scalar_cases": scalars, "fixed_point_family": fixed_family,
            "representative_control": representative_control, "witnesses": registry.records,
        }
        conn.close()
        after_hash = sha256(path)
        assert before_hash == after_hash, f"Input changed: {relative}"
        corpus["unchanged_after_read"] = True
        report["corpora"][name] = corpus
    parameters = [(F(0), F(0)), (F(-1), F(0)), (F(-2), F(0)),
                  (F(-6), F(0)), (F(1), F(0)), (F(1, 4), F(0)),
                  (F(1, 2), F(0)), (F(0), F(1))]
    report["critical_atlas"] = [complex_orbit(c) for c in parameters]
    report["quarter_parameter_certificate"] = {
        "evidence_layer": "external_probe", "interval": ["0", "1/2"],
        "image_interval": ["1/4", "1/2"], "seed": "0",
        "argument": "For 0 <= x <= 1/2, 1/4 <= x*x + 1/4 <= 1/2. The interval is forward invariant. This separately proves boundedness, while the eight-step cycle/escape detector remains unresolved.",
    }
    report["projection_identities"] = {
        "circle": "P(t)=exp(2*pi*i*t); P(2*t)=P(t)^2.",
        "folded_circle": "H(z)=z+1/z; H(z*z)=H(z)^2-2 for z != 0. On |z|=1, H(z)=2*cos(theta).",
        "distinct_numerator_square": "At fixed q, n -> n*n gives residue squaring modulo q. It is not the phase doubling action corresponding to complex squaring.",
        "finite_sampling_limit": "Rational phase samples are finite-period calibrations; no dense Julia boundary or general parameter-plane geometry is certified.",
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name(EXPERIMENT + ".json"))
    args = parser.parse_args()
    if args.self_check:
        print(json.dumps(self_check(), indent=2))
        return 0
    if args.output.exists():
        raise FileExistsError(f"Refusing to overwrite retained evidence: {args.output}")
    report = build_report()
    with args.output.open("x", encoding="utf-8") as target:
        json.dump(report, target, indent=2)
        target.write("\n")
    summary = {
        "report": str(args.output.resolve()), "validation": report["validation"],
        "corpora": {name: {"stage": c["complete_stage"],
                            "queried_relations": len(c["witnesses"]),
                            "retained_relations": sum(bool(w["present"]) for w in c["witnesses"].values()),
                            "unchanged": c["unchanged_after_read"]}
                    for name, c in report["corpora"].items()},
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
