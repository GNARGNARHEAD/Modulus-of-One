from __future__ import annotations

import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from moo.graph_corpus import strict_stage_expected_candidate_events
from moo.graph_evidence import GraphEvidence
from moo.pascal_edge_probe import (
    CorpusLookup,
    _edge_status,
    _expected_directed,
    _parse_int_list,
    _prime_lattice_threshold_report,
    _right_triangle_cubic_report,
)
from moo.strict_stage_moo import build_strict_stage_graph
from moo.route_identity_probe import (
    RouteCertificate,
    RouteStep,
    _canonical_inputs,
    _strict_integer_multiplicity_control,
    build_report,
    canonical_route_expression,
    compare_route_certificates,
    cubic_216_route_certificates,
    evaluate_route_certificate,
    incoming_route_profile,
    main,
    validate_route_certificate,
)


def _key(value: int) -> tuple[int, int]:
    return value, 1


def _create_profile_fixture(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE stages("
            "stage INTEGER PRIMARY KEY, candidate_events INTEGER, retained_events INTEGER, "
            "new_nodes INTEGER, new_edges INTEGER, total_nodes INTEGER, total_edges INTEGER, "
            "elapsed_seconds REAL)"
        )
        conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute(
            "CREATE TABLE nodes("
            "node_id INTEGER PRIMARY KEY, p INTEGER, q INTEGER, label TEXT, kind TEXT, "
            "first_stage INTEGER, confirmed_stage INTEGER)"
        )
        conn.execute(
            "CREATE TABLE edges("
            "edge_id INTEGER PRIMARY KEY, stage INTEGER, op TEXT, "
            "left_node_id INTEGER, right_node_id INTEGER, result_node_id INTEGER)"
        )
        conn.execute("CREATE INDEX idx_edges_result ON edges(result_node_id)")
        conn.executemany(
            "INSERT INTO stages VALUES(?, ?, 0, 0, 0, 0, 0, 0.0)",
            [
                (stage, strict_stage_expected_candidate_events(stage))
                for stage in range(1, 7)
            ],
        )
        conn.execute(
            "INSERT INTO meta VALUES('config_json', ?)",
            (
                json.dumps(
                    {
                        "generator": "strict_stage_moo_graph",
                        "max_stage": 6,
                        "max_abs_p": 100,
                        "max_abs_q": 100,
                        "max_abs_value": 100.0,
                        "retain_confirmed_edges": True,
                    }
                ),
            ),
        )
        nodes = [
            (1, 1, 1, "1", "certainty", 1, 1),
            (2, 2, 1, "2", "positive_integer", 2, 2),
            (3, 3, 1, "3", "positive_integer", 3, 3),
            (4, 5, 1, "5", "positive_integer", 3, 5),
            (5, 6, 1, "6", "positive_integer", 3, 6),
        ]
        conn.executemany("INSERT INTO nodes VALUES(?, ?, ?, ?, ?, ?, ?)", nodes)
        edges = [
            (1, 3, "+", 2, 3, 4),
            (2, 3, "+", 3, 2, 4),
            (3, 3, "+", 2, 3, 4),
            (4, 5, "*", 1, 4, 4),
            (5, 5, "*", 4, 1, 4),
            (6, 6, "-", 5, 1, 4),
        ]
        conn.executemany("INSERT INTO edges VALUES(?, ?, ?, ?, ?, ?)", edges)
        conn.commit()
    finally:
        conn.close()


def _create_cubic_fixture(path: Path) -> None:
    routes = cubic_216_route_certificates()
    unique_steps: dict[str, RouteStep] = {}
    keys = {_key(1)}
    for route in routes:
        for step in (*route.steps, *route.premise_steps):
            unique_steps.setdefault(
                f"{step.op}:{sorted((step.left, step.right)) if step.op in {'+', '*'} else (step.left, step.right)}:{step.result}",
                step,
            )
            keys.update((step.left, step.right, step.result))

    ordered_keys = sorted(keys, key=lambda key: (abs(key[0]), key[1], key[0]))
    node_ids = {key: index + 1 for index, key in enumerate(ordered_keys)}
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            "CREATE TABLE stages("
            "stage INTEGER PRIMARY KEY, candidate_events INTEGER, retained_events INTEGER, "
            "new_nodes INTEGER, new_edges INTEGER, total_nodes INTEGER, total_edges INTEGER, "
            "elapsed_seconds REAL)"
        )
        conn.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute(
            "CREATE TABLE nodes("
            "node_id INTEGER PRIMARY KEY, p INTEGER, q INTEGER, label TEXT, kind TEXT, "
            "first_stage INTEGER, confirmed_stage INTEGER)"
        )
        conn.execute(
            "CREATE TABLE edges("
            "edge_id INTEGER PRIMARY KEY, stage INTEGER, op TEXT, "
            "left_node_id INTEGER, right_node_id INTEGER, result_node_id INTEGER)"
        )
        conn.execute("CREATE INDEX idx_edges_result ON edges(result_node_id)")
        conn.executemany(
            "INSERT INTO stages VALUES(?, ?, 0, 0, 0, 0, 0, 0.0)",
            [
                (stage, strict_stage_expected_candidate_events(stage))
                for stage in range(1, 126)
            ],
        )
        conn.execute("INSERT INTO meta VALUES('schema_version', 'moo_graph_corpus.v1')")
        conn.execute(
            "INSERT INTO meta VALUES('config_json', ?)",
            (
                json.dumps(
                    {
                        "generator": "strict_stage_moo_graph",
                        "max_stage": 125,
                        "max_abs_p": 1000,
                        "max_abs_q": 1000,
                        "max_abs_value": 1000.0,
                        "retain_confirmed_edges": True,
                    }
                ),
            ),
        )
        first_construction: dict[tuple[int, int], int] = {}
        for step in unique_steps.values():
            stage = max(step.left[0], step.right[0])
            first_construction[step.result] = min(
                stage,
                first_construction.get(step.result, stage),
            )
        nodes = []
        for key in ordered_keys:
            value = key[0]
            confirmed_stage = value if value <= 125 else None
            candidate_stages = [first_construction[key]] if key in first_construction else []
            if confirmed_stage is not None:
                candidate_stages.append(confirmed_stage)
            first_stage = min(candidate_stages) if candidate_stages else value
            nodes.append(
                (
                    node_ids[key],
                    key[0],
                    key[1],
                    str(value),
                    "certainty" if value == 1 else "positive_integer",
                    first_stage,
                    confirmed_stage,
                )
            )
        conn.executemany("INSERT INTO nodes VALUES(?, ?, ?, ?, ?, ?, ?)", nodes)

        edge_rows = []
        edge_id = 1
        for step in unique_steps.values():
            stage = max(step.left[0], step.right[0])
            orientations = [(step.left, step.right)]
            if step.op in {"+", "*"} and step.left != step.right:
                orientations.append((step.right, step.left))
            for left, right in orientations:
                edge_rows.append(
                    (
                        edge_id,
                        stage,
                        step.op,
                        node_ids[left],
                        node_ids[right],
                        node_ids[step.result],
                    )
                )
                edge_id += 1
        conn.executemany("INSERT INTO edges VALUES(?, ?, ?, ?, ?, ?)", edge_rows)
        conn.commit()
    finally:
        conn.close()


class RouteIdentityProbeTests(unittest.TestCase):
    def test_pascal_prime_lists_reject_hanging_or_invalid_bases(self) -> None:
        self.assertEqual(_parse_int_list("2,3,5", name="mod-prime"), [2, 3, 5])
        for raw in ("1", "4", "2,2"):
            with self.subTest(raw=raw):
                with self.assertRaises(SystemExit):
                    _parse_int_list(raw, name="mod-prime")

    def test_prime_lattice_threshold_control_does_not_claim_visibility(self) -> None:
        report = _prime_lattice_threshold_report(
            corpus_stage=300,
            prime_limit=31,
            dimensions=(4,),
        )

        self.assertFalse(report["retention_evaluated"])
        self.assertFalse(report["graph_edges_evaluated"])
        dimension = report["by_dimension"]["4"]
        self.assertEqual(dimension["stage_eligible_by_corpus_stage"], 7)
        self.assertNotIn("complete_by_corpus_stage", dimension)

    def test_pascal_lookup_does_not_promote_partial_frontier_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "partial.sqlite"
            build_strict_stage_graph(
                db_path=db_path,
                max_stage=10,
                max_abs_p=100,
                max_abs_q=100,
                max_abs_value=None,
                max_edges=7,
                time_limit_seconds=None,
                commit_every=10,
                retain_confirmed_edges=True,
                verbose=False,
            )
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                lookup = CorpusLookup(conn)
                edge = lookup.edge_summary(
                    left_value=2,
                    op="*",
                    right_value=1,
                    result_value=2,
                    allow_commuted=True,
                )
                node = lookup.node_payload(3)
            finally:
                conn.close()

        self.assertFalse(edge["eligible_by_stage"])
        self.assertNotEqual(
            _edge_status(edge, _expected_directed(2, 1, "*")),
            "complete_directed",
        )
        if node["present"]:
            self.assertFalse(node["visible_in_complete_corpus"])

    def test_strict_integer_null_model_explains_u1000_collision_mass(self) -> None:
        control = _strict_integer_multiplicity_control(
            target=_key(216),
            stage=1000,
            config={
                "generator": "strict_stage_moo_graph",
                "max_abs_p": 1_000_000_000,
                "max_abs_q": 1000,
                "max_abs_value": 1_000_000_000.0,
            },
            observed_profile={
                "incoming_edge_occurrences": 1019,
                "commutative_normalized_witnesses": 904,
            },
        )

        self.assertEqual(control["tau_n"], 16)
        self.assertEqual(control["expected_edge_occurrences"], 1019)
        self.assertEqual(control["expected_commutative_normalized_witnesses"], 904)
        self.assertTrue(control["observed_matches_closed_form"])

    def test_incoming_profile_collapses_reversals_and_duplicate_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "profile.sqlite"
            _create_profile_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                evidence = GraphEvidence(conn)
                profile = incoming_route_profile(
                    conn,
                    evidence,
                    _key(5),
                    as_of_stage=6,
                    witness_limit=10,
                    edge_ref_limit=10,
                    include_witnesses=True,
                )
            finally:
                conn.close()

        self.assertEqual(profile["incoming_edge_occurrences"], 6)
        self.assertEqual(profile["directed_algebraic_witnesses"], 5)
        self.assertEqual(profile["commutative_normalized_witnesses"], 3)
        self.assertEqual(profile["commutative_collapse_count"], 2)
        self.assertEqual(
            profile["operation_signature"]["normalized_witnesses"],
            {"*": 1, "+": 1, "-": 1},
        )
        plus = next(row for row in profile["witness_groups"] if row["op"] == "+")
        self.assertEqual(plus["edge_occurrences"], 3)
        self.assertEqual(plus["directed_witnesses"], 2)
        self.assertTrue(plus["commutative_reversal_collapsed"])

    def test_only_commutative_operations_sort_inputs(self) -> None:
        self.assertEqual(
            _canonical_inputs("*", _key(6), _key(36)),
            _canonical_inputs("*", _key(36), _key(6)),
        )
        self.assertNotEqual(
            _canonical_inputs("-", _key(6), _key(1)),
            _canonical_inputs("-", _key(1), _key(6)),
        )
        self.assertNotEqual(
            _canonical_inputs("/", _key(6), _key(1)),
            _canonical_inputs("/", _key(1), _key(6)),
        )

    def test_profile_does_not_expose_a_future_node_at_earlier_aperture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "profile.sqlite"
            _create_profile_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                profile = incoming_route_profile(
                    conn,
                    GraphEvidence(conn),
                    _key(5),
                    as_of_stage=2,
                    witness_limit=1,
                    edge_ref_limit=1,
                    include_witnesses=False,
                )
            finally:
                conn.close()

        self.assertTrue(profile["present"])
        self.assertFalse(profile["visible_as_of_stage"])
        self.assertEqual(profile["confirmation_status_as_of_stage"], "absent_at_aperture")
        self.assertEqual(profile["incoming_edge_occurrences"], 0)

    def test_surface_and_volume_collapse_but_side_cubes_do_not(self) -> None:
        routes = {route.route_id: route for route in cubic_216_route_certificates()}
        alias = compare_route_certificates(routes["cube_volume_6"], routes["cube_surface_6"])
        distinct = compare_route_certificates(
            routes["cube_volume_6"], routes["right_triangle_side_cubes"]
        )

        self.assertTrue(alias["same_associative_commutative_expression"])
        self.assertEqual(alias["independence_status"], "collapsed_by_graph_route_quotient")
        self.assertFalse(distinct["same_associative_commutative_expression"])
        self.assertEqual(distinct["classification"], "distinct_at_declared_certificate_cut")

    def test_associative_regroupings_have_one_ac_expression(self) -> None:
        left = RouteCertificate(
            "left_grouping",
            "test",
            "(2+3)+4",
            _key(9),
            (
                RouteStep("a", _key(2), "+", _key(3), _key(5)),
                RouteStep("b", _key(5), "+", _key(4), _key(9)),
            ),
            "test",
        )
        right = RouteCertificate(
            "right_grouping",
            "test",
            "2+(3+4)",
            _key(9),
            (
                RouteStep("a", _key(3), "+", _key(4), _key(7)),
                RouteStep("b", _key(2), "+", _key(7), _key(9)),
            ),
            "test",
        )

        self.assertEqual(canonical_route_expression(left), canonical_route_expression(right))
        self.assertEqual(
            compare_route_certificates(left, right)["classification"],
            "same_route_under_associative_commutative_quotient",
        )

    def test_noncanonical_rational_keys_are_rejected(self) -> None:
        route = RouteCertificate(
            "noncanonical",
            "test",
            "2/2 + 1 = 2",
            _key(2),
            (
                RouteStep("sum", (2, 2), "+", _key(1), _key(2)),
            ),
            "test",
        )

        with self.assertRaisesRegex(ValueError, "noncanonical"):
            validate_route_certificate(route)

    def test_self_referential_certificate_is_rejected(self) -> None:
        cyclic = RouteCertificate(
            "cycle",
            "test",
            "2+0=2",
            _key(2),
            (RouteStep("cycle", _key(2), "+", _key(0), _key(2)),),
            "test",
        )
        with self.assertRaisesRegex(ValueError, "construction cycle"):
            validate_route_certificate(cyclic)

    def test_certificate_rejects_steps_outside_target_ancestry(self) -> None:
        route = RouteCertificate(
            "unused",
            "test",
            "2+3 with unrelated 4+5",
            _key(5),
            (
                RouteStep("target", _key(2), "+", _key(3), _key(5)),
                RouteStep("unrelated", _key(4), "+", _key(5), _key(9)),
            ),
            "test",
        )
        with self.assertRaisesRegex(ValueError, "outside the target ancestry"):
            validate_route_certificate(route)

    def test_route_visibility_respects_aperture(self) -> None:
        route = next(
            route
            for route in cubic_216_route_certificates()
            if route.route_id == "right_triangle_side_cubes"
        )
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "cubic.sqlite"
            _create_cubic_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                evidence = GraphEvidence(conn)
                at_124 = evaluate_route_certificate(
                    evidence, route, as_of_stage=124, edge_ref_limit=8
                )
                at_125 = evaluate_route_certificate(
                    evidence, route, as_of_stage=125, edge_ref_limit=8
                )
            finally:
                conn.close()

        self.assertEqual(at_125["graph_support"]["earliest_complete_stage"], 125)
        self.assertFalse(at_124["graph_support"]["visible_as_of_stage"])
        self.assertTrue(at_125["graph_support"]["visible_as_of_stage"])
        premise = next(edge for edge in at_125["edges"] if edge["role"] == "premise")
        self.assertEqual(premise["step_id"], "pythagorean_square_relation")
        self.assertTrue(premise["commutative_orbit"]["present"])

    def test_incomplete_certificate_has_no_complete_stage(self) -> None:
        route = RouteCertificate(
            "incomplete",
            "test",
            "construct 10 through a missing edge",
            _key(10),
            (
                RouteStep("five", _key(2), "+", _key(3), _key(5)),
                RouteStep("ten", _key(5), "+", _key(5), _key(10)),
            ),
            "test",
        )
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "profile.sqlite"
            _create_profile_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                evaluated = evaluate_route_certificate(
                    GraphEvidence(conn),
                    route,
                    as_of_stage=6,
                    edge_ref_limit=4,
                )
            finally:
                conn.close()

        self.assertFalse(evaluated["graph_support"]["all_commutative_orbits_present"])
        self.assertIsNone(evaluated["graph_support"]["earliest_complete_stage"])

    def test_report_timeline_does_not_add_future_first_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "profile.sqlite"
            _create_profile_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                report = build_report(
                    conn,
                    db_path=db_path,
                    target=_key(5),
                    controls=(),
                    case_id=None,
                    requested_as_of_stage=2,
                    milestones=(),
                    control_radius=0,
                    witness_limit=4,
                    edge_ref_limit=4,
                    argv=(),
                    include_checksums=False,
                )
            finally:
                conn.close()

        self.assertEqual(
            [row["as_of_stage"] for row in report["aperture_timeline"]],
            [2],
        )

    def test_pascal_cubic_report_exposes_surface_volume_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "cubic.sqlite"
            _create_cubic_fixture(db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            try:
                report = _right_triangle_cubic_report(
                    CorpusLookup(conn),
                    max_scale=1,
                    primitive_hypotenuse_limit=5,
                )
            finally:
                conn.close()

        identity = report["scale_branch"][0]["route_identity"]
        self.assertTrue(identity["surface_volume_same_commutative_terminal_witness"])
        self.assertEqual(identity["assessment"], "projection_alias_not_independent_routes")
        self.assertEqual(len(identity["surface_volume_edge_ref_overlap"]), 2)
        alias_name_sets = {
            frozenset(group["named_witnesses"])
            for group in identity["named_witness_alias_groups"]
        }
        self.assertIn(frozenset(("surface_6s2", "volume_s3")), alias_name_sets)
        self.assertIn(frozenset(("area_half", "semiperimeter")), alias_name_sets)
        controls = report["primitive_defect_controls"]
        self.assertIn("zero_defect_all_scales", controls)
        self.assertIn("zero_defect_primitive", controls)
        self.assertNotIn("zero_defect", controls)

    def test_cli_writes_v1_report_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "cubic.sqlite"
            report_path = Path(tmp) / "report.json"
            _create_cubic_fixture(db_path)
            argv = [
                "--db",
                str(db_path),
                "--target",
                "216",
                "--case",
                "cubic-216",
                "--write",
                str(report_path),
            ]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(argv), 0)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["metadata"]["schema_version"],
                "moo_route_identity_probe.report.v1",
            )
            self.assertEqual(payload["route_case"]["case_id"], "cubic_216_route_calibration")
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(SystemExit, "Refusing to overwrite"):
                    main(argv)


if __name__ == "__main__":
    unittest.main()
