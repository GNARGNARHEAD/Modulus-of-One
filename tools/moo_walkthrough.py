"""Follow 16 through a growing MoO field using only the standard library."""

from __future__ import annotations

import argparse
from contextlib import closing
from fractions import Fraction
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from moo.graph_evidence import GraphEvidence
from moo.research_utils import connect_readonly, file_sha256
from moo.strict_stage_moo import build_strict_stage_graph


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def build(path: Path, stage: int, bound: int) -> None:
    build_strict_stage_graph(
        db_path=path, max_stage=stage, max_abs_p=bound,
        max_abs_q=stage, max_abs_value=bound, max_edges=None,
        time_limit_seconds=None, commit_every=stage,
        retain_confirmed_edges=True, verbose=False,
    )


def incoming(conn, value: Fraction, stage: int) -> list[dict]:
    return [dict(row) for row in conn.execute(
        """
        SELECT e.edge_id, e.stage, l.label AS left, e.op, r.label AS right,
               v.label AS result, v.node_id AS result_node_id
        FROM edges e
        JOIN nodes l ON l.node_id = e.left_node_id
        JOIN nodes r ON r.node_id = e.right_node_id
        JOIN nodes v ON v.node_id = e.result_node_id
        WHERE v.p = ? AND v.q = ? AND e.stage <= ?
        ORDER BY e.stage, e.edge_id
        """, (value.numerator, value.denominator, stage)
    )]


def snapshot(conn, value: int, stage: int) -> dict:
    node = conn.execute(
        "SELECT * FROM nodes WHERE p = ? AND q = 1", (value,)
    ).fetchone()
    require(node is not None and node["first_stage"] <= stage,
            f"{value} has not appeared by U{stage}")
    threshold = node["confirmed_stage"]
    require(threshold == value, "Unexpected positive-spine confirmation threshold")
    return {
        "stage": stage, "value": str(value), "node_id": node["node_id"],
        "first_stage": node["first_stage"], "confirmation_threshold": threshold,
        "confirmed_at_checkpoint": threshold is not None and threshold <= stage,
        "incoming": incoming(conn, Fraction(value), stage),
    }


def check_full_field(conn) -> list[dict]:
    """Check the Cartesian product independently of the frontier generator."""
    arithmetic = {
        "+": lambda a, b: Fraction(a + b),
        "-": lambda a, b: Fraction(a - b),
        "*": lambda a, b: Fraction(a * b),
        "/": lambda a, b: Fraction(a, b),
    }
    rows = conn.execute(
        """
        SELECT e.stage, l.p AS a, l.q AS aq, e.op, r.p AS b, r.q AS bq,
               v.p, v.q
        FROM edges e
        JOIN nodes l ON l.node_id = e.left_node_id
        JOIN nodes r ON r.node_id = e.right_node_id
        JOIN nodes v ON v.node_id = e.result_node_id
        WHERE e.op != 'seed'
        """
    ).fetchall()
    for row in rows:
        require(row["aq"] == row["bq"] == 1, "Non-integer operand")
        require(row["stage"] == max(row["a"], row["b"]), "Wrong arrival stage")
        require(Fraction(row["p"], row["q"]) ==
                arithmetic[row["op"]](row["a"], row["b"]), "Wrong arithmetic result")
    checkpoints = []
    for stage in range(1, 17):
        observed = [(r["a"], r["op"], r["b"]) for r in rows if r["stage"] <= stage]
        expected = {(a, op, b) for a in range(1, stage + 1)
                    for b in range(1, stage + 1) for op in arithmetic}
        require(len(observed) == len(expected) and set(observed) == expected,
                f"Incomplete or duplicated operation field at U{stage}")
        checkpoints.append({"stage": stage, "arithmetic_edges": len(observed)})
    return checkpoints


def inspect(directory: Path) -> dict:
    field = directory / "field.sqlite"
    control = directory / "retention_control.sqlite"
    # These bounds retain every result of the four operations on 1..16.
    build(field, stage=16, bound=256)
    build(control, stage=8, bound=8)
    with closing(connect_readonly(field)) as conn:
        checkpoints = check_full_field(conn)
        fan = [w for value in (1, 2, 0)
               for w in incoming(conn, Fraction(value), 1)]
        half = incoming(conn, Fraction(1, 2), 4)
        require(len(half) == 2 and len({w["result_node_id"] for w in half}) == 1,
                "The half witnesses should share one value node")
        four = [snapshot(conn, 4, stage) for stage in (2, 4)]
        six = [snapshot(conn, 6, stage) for stage in (3, 6)]
        sixteen = [snapshot(conn, 16, stage) for stage in (4, 8, 16)]
        require(four[0]["first_stage"] == 2 and six[0]["first_stage"] == 3
                and sixteen[0]["first_stage"] == 4,
                "Unexpected first appearance")
        for value, observations, confirmed in (
            (4, four, [False, True]), (6, six, [False, True]),
            (16, sixteen, [False, False, True]),
        ):
            require([s["confirmed_at_checkpoint"] for s in observations] == confirmed,
                    f"Construction of {value} was confused with confirmation")
            require(len({s["node_id"] for s in observations}) == 1,
                    f"Node identity changed for {value}")
            for earlier, later in zip(observations, observations[1:]):
                require({w["edge_id"] for w in earlier["incoming"]}
                        <= {w["edge_id"] for w in later["incoming"]},
                        f"Earlier witnesses disappeared for {value}")
        require({(w["left"], w["op"], w["right"]) for w in four[0]["incoming"]}
                == {("2", "+", "2"), ("2", "*", "2")},
                "4 should have both additive and product witnesses at U2")
        require([(w["left"], w["op"], w["right"]) for w in sixteen[0]["incoming"]]
                == [("4", "*", "4")],
                "Unexpected witness for 16 at U4")
        require({(w["left"], w["op"], w["right"]) for w in sixteen[1]["incoming"]}
                == {("4", "*", "4"), ("8", "+", "8"),
                    ("2", "*", "8"), ("8", "*", "2")},
                "Unexpected witnesses for 16 at U8")
    with closing(connect_readonly(control)) as conn:
        bounded = GraphEvidence(conn).edge_witness(left=4, op="*", right=4, result=16)
        require(bounded["edge_count"] == 0 and bounded["eligible_by_stage"]
                and bounded["eligible_by_retention"] is False,
                "The bounded control should exclude 4*4 by retention")
    sources = ('moo/strict_stage_moo.py', 'moo/graph_corpus.py', 'moo/graph_evidence.py',
               'moo/research_utils.py', "tools/moo_walkthrough.py")
    report = {
        "scope": "fresh positive-spine demonstration; not a historical reproduction",
        "python_version": sys.version.split()[0],
        "source_sha256": {p: file_sha256(ROOT / p) for p in sources},
        "corpora": {p.name: {"bytes": p.stat().st_size, "sha256": file_sha256(p)}
                    for p in (field, control)},
        "full_field_checkpoints": checkpoints, "first_fan": fan,
        "four": four, "shared_half": half, "six": six, "sixteen": sixteen,
        "retention_control": bounded,
    }
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        help="Keep the databases and report in a new directory")
    args = parser.parse_args()
    if args.output_dir is None:
        with TemporaryDirectory(prefix="moo-walkthrough-") as scratch:
            inspect(Path(scratch))
    else:
        try:
            args.output_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            parser.error(f"Output directory already exists: {args.output_dir}")
        inspect(args.output_dir)
    print("Checked all four operations on every ordered pair at U1 through U16.")
    print("U1: 1+1 -> 2; 1-1 -> 0; 1*1 -> 1; 1/1 -> 1.")
    print("U2: 2+2 and 2*2 reach 4; 4 is recorded but cannot yet be an operand.")
    print("U4: recurrence confirms 4; 4*4 first reaches 16, still unconfirmed.")
    print("U8: 8+8, 2*8, and 8*2 join 4*4 at the same node for 16, still unconfirmed.")
    print("U16: recurrence confirms 16 for use as an operand; earlier witnesses remain.")
    print("This is second-order support, not the immediate certainty of 1.")
    print("The U16 field retains 1024 arithmetic witnesses plus its seed edge.")
    print("A separate bounded U8 excludes 4*4 -> 16: a storage bound, not a missing relation.")
    if args.output_dir is None:
        print("Temporary files removed. Use --output-dir to keep the evidence.")
    else:
        print(f"Evidence saved in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
