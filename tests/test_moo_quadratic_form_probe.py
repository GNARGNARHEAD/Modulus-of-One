from __future__ import annotations

import tempfile
import unittest
from contextlib import closing
from fractions import Fraction
from pathlib import Path
from typing import Union

from moo.graph_corpus import GraphCorpus, GraphCorpusConfig, normalize_key
from moo.quadratic_form_probe import (
    BinaryQuadraticForm,
    D4_PRINCIPAL,
    D20_NONPRINCIPAL,
    D20_PRINCIPAL,
    ScalarGraphInspector,
    _relation_shadow_usable,
    d20_composition_event_ledger,
    d20_nonprincipal_nonprincipal,
    d20_principal_nonprincipal,
    d20_principal_principal,
    enumerate_representations,
    gaussian_multiply,
    gaussian_norm,
    multiplicativity_report,
    normalized_coefficients,
    positive_spine_evaluation_plan,
    proper_automorphism_images,
    proper_orbit_representatives,
    quadratic_form_probe,
    quarter_turn,
    reduced_primitive_forms,
)
from moo.research_utils import connect_readonly
from moo.strict_stage_moo import build_strict_stage_graph


Value = Union[int, Fraction]


def _create_fixture(path: Path, *, core_max: int = 12) -> None:
    config = GraphCorpusConfig(
        generator="strict_stage_moo_graph",
        max_stage=max(12, core_max),
        max_abs_p=1_000,
        max_abs_q=1_000,
        max_abs_value=1_000.0,
        retain_confirmed_edges=True,
    )
    with GraphCorpus(path) as corpus:
        corpus.init_schema()
        corpus.ensure_config(config)

        def node_id(value: Value, *, first_stage: int) -> int:
            fraction = value if isinstance(value, Fraction) else Fraction(value, 1)
            key = normalize_key(fraction.numerator, fraction.denominator)
            found, _ = corpus.ensure_node(key, first_stage=first_stage)
            return found

        def core(value: int) -> int:
            found, _ = corpus.ensure_core_integer(value)
            return found

        def add_edge(
            left: int,
            op: str,
            right: int,
            result: Value,
            *,
            stage: int,
        ) -> None:
            corpus.insert_edge(
                stage=stage,
                op=op,
                left_node_id=core(left),
                right_node_id=core(right),
                result_node_id=node_id(result, first_stage=stage),
            )

        for value in range(1, core_max + 1):
            core(value)
        corpus.insert_edge(
            stage=1,
            op="seed",
            left_node_id=None,
            right_node_id=None,
            result_node_id=core(1),
        )
        add_edge(1, "-", 1, 0, stage=1)
        for left, right, result in [
            (2, 3, 6),
            (2, 5, 10),
            (1, 5, 6),
        ]:
            if result > core_max:
                continue
            stage = max(left, right)
            add_edge(left, "*" if left != 1 else "+", right, result, stage=stage)
            add_edge(right, "*" if left != 1 else "+", left, result, stage=stage)
        corpus.record_stage(
            stage=max(12, core_max),
            candidate_events=0,
            retained_events=0,
            new_nodes=0,
            new_edges=0,
            elapsed_seconds=0.0,
        )


class QuadraticFormMathTests(unittest.TestCase):
    def test_form_metadata_and_reduced_enumeration(self) -> None:
        self.assertEqual(D4_PRINCIPAL.discriminant, -4)
        self.assertEqual(D20_PRINCIPAL.discriminant, -20)
        self.assertEqual(D20_NONPRINCIPAL.discriminant, -20)
        self.assertTrue(D4_PRINCIPAL.is_primitive)
        self.assertTrue(D20_PRINCIPAL.is_reduced)
        self.assertTrue(D20_NONPRINCIPAL.is_reduced)
        self.assertEqual(reduced_primitive_forms(-4), ((1, 0, 1),))
        self.assertEqual(
            reduced_primitive_forms(-20),
            ((1, 0, 5), (2, 2, 3)),
        )

    def test_completed_square_enumerator_matches_brute_force(self) -> None:
        forms = [
            D4_PRINCIPAL,
            D20_PRINCIPAL,
            D20_NONPRINCIPAL,
            BinaryQuadraticForm("negative_b", "control", 3, -2, 2, 2),
        ]
        max_n = 80
        for form in forms:
            exact = enumerate_representations(form, max_n)
            brute = {
                n: tuple(
                    sorted(
                        (x, y)
                        for x in range(-20, 21)
                        for y in range(-20, 21)
                        if form.evaluate(x, y) == n
                    )
                )
                for n in range(1, max_n + 1)
            }
            self.assertEqual(exact, brute, form.form_id)

    def test_d20_named_witnesses_and_holes_are_exact(self) -> None:
        principal = enumerate_representations(D20_PRINCIPAL, 6)
        nonprincipal = enumerate_representations(D20_NONPRINCIPAL, 6)
        self.assertEqual(principal[2], ())
        self.assertEqual(principal[3], ())
        self.assertEqual(
            principal[6],
            ((-1, -1), (-1, 1), (1, -1), (1, 1)),
        )
        self.assertEqual(nonprincipal[2], ((-1, 0), (1, 0)))
        self.assertEqual(
            nonprincipal[3],
            ((-1, 1), (0, -1), (0, 1), (1, -1)),
        )
        self.assertEqual(nonprincipal[6], ())

    def test_pair_operator_and_composition_identities(self) -> None:
        for x in range(-3, 4):
            for y in range(-3, 4):
                pair = (x, y)
                self.assertEqual(quarter_turn(quarter_turn(pair)), (-x, -y))
                self.assertEqual(gaussian_norm(quarter_turn(pair)), gaussian_norm(pair))
                for u in range(-3, 4):
                    for v in range(-3, 4):
                        other = (u, v)
                        self.assertEqual(
                            gaussian_norm(gaussian_multiply(pair, other)),
                            gaussian_norm(pair) * gaussian_norm(other),
                        )
                        self.assertEqual(
                            D20_PRINCIPAL.evaluate(
                                *d20_principal_principal(pair, other)
                            ),
                            D20_PRINCIPAL.evaluate(*pair)
                            * D20_PRINCIPAL.evaluate(*other),
                        )
                        self.assertEqual(
                            D20_NONPRINCIPAL.evaluate(
                                *d20_principal_nonprincipal(pair, other)
                            ),
                            D20_PRINCIPAL.evaluate(*pair)
                            * D20_NONPRINCIPAL.evaluate(*other),
                        )
                        self.assertEqual(
                            D20_PRINCIPAL.evaluate(
                                *d20_nonprincipal_nonprincipal(pair, other)
                            ),
                            D20_NONPRINCIPAL.evaluate(*pair)
                            * D20_NONPRINCIPAL.evaluate(*other),
                        )

    def test_proper_automorphism_orbits_partition_complete_fibres(self) -> None:
        for form in (D4_PRINCIPAL, D20_PRINCIPAL, D20_NONPRINCIPAL):
            representations = enumerate_representations(form, 80)
            orbits = proper_orbit_representatives(form, representations)
            for value, witnesses in representations.items():
                reconstructed = {
                    image
                    for representative in orbits[value]
                    for image in proper_automorphism_images(form, representative)
                }
                self.assertEqual(reconstructed, set(witnesses))
                self.assertEqual(
                    len(orbits[value]) * form.automorphism_normalization,
                    len(witnesses),
                )

    def test_positive_spine_plans_are_exact_and_never_use_zero_operands(self) -> None:
        for form in (D4_PRINCIPAL, D20_PRINCIPAL, D20_NONPRINCIPAL):
            representations = enumerate_representations(form, 80)
            for value, witnesses in representations.items():
                for x, y in witnesses:
                    plan = positive_spine_evaluation_plan(form, x, y)
                    self.assertEqual(plan["represented_value"], value)
                    self.assertEqual(plan["modulus_one_result_residue"], 0)
                    for step in plan["formula_step_occurrences"]:
                        self.assertGreaterEqual(min(
                            step["left"], step["right"], step["result"]
                        ), 1)

        same_sign = positive_spine_evaluation_plan(D20_NONPRINCIPAL, 1, 1)
        self.assertEqual(
            same_sign["coordinates"]["absolute_x_plus_y"]["construction"],
            "same-sign magnitudes add",
        )
        opposite = positive_spine_evaluation_plan(D20_NONPRINCIPAL, 2, -1)
        self.assertEqual(
            opposite["coordinates"]["absolute_x_plus_y"]["construction"],
            "opposite-sign magnitudes subtract",
        )
        cancellation = positive_spine_evaluation_plan(D20_NONPRINCIPAL, 1, -1)
        cancellation_payload = cancellation["coordinates"]["absolute_x_plus_y"]
        self.assertIn("cancel to zero", cancellation_payload["construction"])
        self.assertNotIn(
            "subtract:1:1:0",
            cancellation["distinct_formula_relation_ids"],
        )
        self.assertIn(
            "subtract:1:1:0",
            cancellation["distinct_coordinate_relation_ids"],
        )
        self.assertEqual(cancellation["coordinate_relation_occurrence_count"], 1)
        zero_coordinate = positive_spine_evaluation_plan(
            D20_NONPRINCIPAL,
            0,
            1,
        )
        self.assertIn(
            "zero-coordinate identity",
            zero_coordinate["coordinates"]["absolute_x_plus_y"]["construction"],
        )

        b_n200 = enumerate_representations(D20_NONPRINCIPAL, 200)
        cancellation_plans = [
            positive_spine_evaluation_plan(D20_NONPRINCIPAL, x, y)
            for witnesses in b_n200.values()
            for x, y in witnesses
            if x == -y and x != 0
        ]
        self.assertEqual(len(cancellation_plans), 16)
        cancellation_ids = {
            relation_id
            for plan in cancellation_plans
            for relation_id in plan["distinct_coordinate_relation_ids"]
            if relation_id.endswith(":0")
        }
        self.assertEqual(len(cancellation_ids), 8)

    def test_d20_normalized_and_raw_composition_counts_at_n200(self) -> None:
        principal = enumerate_representations(D20_PRINCIPAL, 200)
        nonprincipal = enumerate_representations(D20_NONPRINCIPAL, 200)
        ledger = d20_composition_event_ledger(
            principal,
            nonprincipal,
            max_n=200,
        )
        self.assertEqual(ledger["total_composition_events"], 961)
        self.assertEqual(
            ledger["normalized_class_signature_counts"],
            {
                "nonprincipal*nonprincipal->principal": 224,
                "principal*nonprincipal->nonprincipal": 466,
                "principal*principal->principal": 271,
            },
        )
        self.assertEqual(ledger["distinct_scalar_multiplication_relations"], 345)
        self.assertEqual(ledger["identity_failure_count"], 0)
        self.assertEqual(ledger["target_fibre_failure_count"], 0)
        self.assertTrue(ledger["all_normalized_events_verified_exactly"])
        self.assertTrue(ledger["complete_event_list_emitted"])
        self.assertEqual(
            ledger["raw_signed_witness_accounting"][
                "oriented_class_signature_counts"
            ],
            {
                "principal*principal->principal": 2_128,
                "principal*nonprincipal->nonprincipal": 1_864,
                "nonprincipal*principal->nonprincipal": 1_864,
                "nonprincipal*nonprincipal->principal": 1_756,
            },
        )
        self.assertEqual(
            ledger["raw_signed_witness_accounting"]["total_events"],
            7_612,
        )
        truncated = d20_composition_event_ledger(
            principal,
            nonprincipal,
            max_n=200,
            event_limit=10,
        )
        self.assertTrue(truncated["all_normalized_events_verified_exactly"])
        self.assertFalse(truncated["complete_event_list_emitted"])
        self.assertEqual(truncated["reported_event_count"], 10)
    def test_character_channels_restore_the_finite_multiplicativity_check(self) -> None:
        max_n = 200
        d4 = normalized_coefficients(
            D4_PRINCIPAL,
            enumerate_representations(D4_PRINCIPAL, max_n),
        )
        principal = normalized_coefficients(
            D20_PRINCIPAL,
            enumerate_representations(D20_PRINCIPAL, max_n),
        )
        nonprincipal = normalized_coefficients(
            D20_NONPRINCIPAL,
            enumerate_representations(D20_NONPRINCIPAL, max_n),
        )
        plus = {n: principal[n] + nonprincipal[n] for n in principal}
        minus = {n: principal[n] - nonprincipal[n] for n in principal}
        placebo = {n: principal[n] + 2 * nonprincipal[n] for n in principal}

        self.assertTrue(multiplicativity_report(d4, max_n=max_n)["passes_finite_test"])
        principal_report = multiplicativity_report(principal, max_n=max_n)
        self.assertFalse(principal_report["passes_finite_test"])
        self.assertEqual(
            principal_report["reported_defects"][0],
            {
                "left": 2,
                "right": 3,
                "product": 6,
                "coefficient_left": 0,
                "coefficient_right": 0,
                "coefficient_product": 2,
                "expected_product": 0,
            },
        )
        self.assertEqual(nonprincipal[1], 0)
        self.assertFalse(
            multiplicativity_report(nonprincipal, max_n=max_n)[
                "unit_condition_passes"
            ]
        )
        self.assertTrue(multiplicativity_report(plus, max_n=max_n)["passes_finite_test"])
        self.assertTrue(multiplicativity_report(minus, max_n=max_n)["passes_finite_test"])
        self.assertFalse(
            multiplicativity_report(placebo, max_n=max_n)["passes_finite_test"]
        )


class QuadraticFormCorpusTests(unittest.TestCase):
    def test_complete_paths_and_modulus_one_projection_on_strict_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "strict_u10.sqlite"
            build_strict_stage_graph(
                db_path=db_path,
                max_stage=10,
                max_abs_p=1_000,
                max_abs_q=1_000,
                max_abs_value=1_000.0,
                max_edges=None,
                time_limit_seconds=None,
                commit_every=10,
                retain_confirmed_edges=True,
                verbose=False,
            )
            report = quadratic_form_probe(
                db_path=db_path,
                max_n=10,
                edge_limit=4,
                graph_stage_cutoff=10,
            )

        paths = report["graph_audit"][
            "complete_positive_spine_evaluation_paths"
        ]
        self.assertTrue(paths["positive_spine_arithmetic_dags_complete"])
        self.assertTrue(paths["coordinate_side_ledgers_complete"])
        self.assertTrue(paths["all_scalar_references_complete"])
        self.assertEqual(paths["incomplete_arithmetic_dag_count"], 0)
        self.assertFalse(
            paths["forms"][D4_PRINCIPAL.form_id][
                "relational_zero_side_ledger"
            ]["applicable"]
        )
        self.assertIsNone(
            paths["forms"][D4_PRINCIPAL.form_id][
                "relational_zero_side_ledger"
            ]["all_edges_have_confirmed_operands"]
        )
        self.assertTrue(
            paths["forms"][D20_NONPRINCIPAL.form_id][
                "relational_zero_side_ledger"
            ]["applicable"]
        )
        composition = report["graph_audit"][
            "d20_composition_scalar_relation_audit"
        ]
        self.assertTrue(composition["all_scalar_multiplication_shadows_usable"])
        projection = report["modulus_one_projection"]
        d20 = projection["two_stage_metrics"][
            "gauss_determinant_minus_5_modern_discriminant_minus_20"
        ]
        self.assertEqual(d20["occupied_modulus_one_residues"], [0])
        self.assertTrue(
            projection["constant_bucket_control"][
                "matches_modulus_one_bare_signature"
            ]
        )
        self.assertTrue(
            projection["bare_modulus_one_topology"]["division_excluded"]
        )
        central = projection["central_class_composition_witness"]
        self.assertEqual(central["bare_quotient_identity"], "0*0=0")
        self.assertEqual(
            central["class_transition"],
            "nonprincipal*nonprincipal->principal",
        )

    def test_stage_cutoff_does_not_borrow_later_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "strict_u10.sqlite"
            build_strict_stage_graph(
                db_path=db_path,
                max_stage=10,
                max_abs_p=1_000,
                max_abs_q=1_000,
                max_abs_value=1_000.0,
                max_edges=None,
                time_limit_seconds=None,
                commit_every=10,
                retain_confirmed_edges=True,
                verbose=False,
            )
            report = quadratic_form_probe(
                db_path=db_path,
                max_n=10,
                edge_limit=4,
                graph_stage_cutoff=4,
            )

        audit = report["graph_audit"]
        self.assertEqual(audit["stage_censoring"]["effective_stage_cutoff"], 4)
        relation = audit["selected_scalar_relations"][
            "d4_norm_multiplicativity_shadow"
        ]
        self.assertFalse(relation["present"])
        self.assertFalse(
            audit["complete_positive_spine_evaluation_paths"][
                "positive_spine_arithmetic_dags_complete"
            ]
        )
        ten = audit["scalar_node_coverage"]["rows"][9]
        self.assertFalse(ten["present_at_stage_cutoff"])
        self.assertFalse(ten["confirmed_by_stage_cutoff"])
        self.assertEqual(
            ten["status_at_stage_cutoff"],
            "not_yet_present_at_stage_cutoff",
        )
        self.assertEqual(ten["eventual_confirmed_stage"], 10)
        five = audit["scalar_node_coverage"]["rows"][4]
        self.assertTrue(five["present_at_stage_cutoff"])
        self.assertFalse(five["confirmed_by_stage_cutoff"])
        self.assertEqual(
            five["status_at_stage_cutoff"],
            "speculative_at_stage_cutoff",
        )
        self.assertEqual(five["eventual_confirmed_stage"], 5)

    def test_requested_stage_cutoff_is_clamped_to_corpus_latest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "strict_u6.sqlite"
            build_strict_stage_graph(
                db_path=db_path,
                max_stage=6,
                max_abs_p=1_000,
                max_abs_q=1_000,
                max_abs_value=1_000.0,
                max_edges=None,
                time_limit_seconds=None,
                commit_every=6,
                retain_confirmed_edges=True,
                verbose=False,
            )
            report = quadratic_form_probe(
                db_path=db_path,
                max_n=6,
                edge_limit=4,
                graph_stage_cutoff=50,
            )
        self.assertEqual(report["config"]["requested_graph_stage_cutoff"], 50)
        self.assertEqual(report["config"]["effective_graph_stage_cutoff"], 6)
        self.assertEqual(
            report["graph_audit"]["stage_censoring"]["effective_stage_cutoff"],
            6,
        )

    def test_present_edge_with_unconfirmed_operand_is_not_usable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "malformed.sqlite"
            config = GraphCorpusConfig(
                generator="strict_stage_moo_graph",
                max_stage=1,
                max_abs_p=100,
                max_abs_q=100,
                max_abs_value=100.0,
                retain_confirmed_edges=True,
            )
            with GraphCorpus(db_path) as corpus:
                corpus.init_schema()
                corpus.ensure_config(config)
                one, _ = corpus.ensure_core_integer(1)
                two, _ = corpus.ensure_core_integer(2)
                three, _ = corpus.ensure_core_integer(3)
                corpus.insert_edge(
                    stage=1,
                    op="+",
                    left_node_id=two,
                    right_node_id=one,
                    result_node_id=three,
                )
                corpus.record_stage(
                    stage=1,
                    candidate_events=1,
                    retained_events=1,
                    new_nodes=0,
                    new_edges=1,
                    elapsed_seconds=0.0,
                )
            with closing(connect_readonly(db_path)) as conn:
                inspector = ScalarGraphInspector(
                    conn,
                    latest_stage=1,
                    edge_limit=4,
                    stage_cutoff=1,
                )
                evidence = inspector.relation(2, "+", 1, 3)

        self.assertTrue(evidence["present"])
        self.assertFalse(evidence["operand_confirmation_at_edge_passes"])
        self.assertFalse(
            _relation_shadow_usable(
                {"graph_evidence": evidence},
                require_ordered_direction=True,
            )
        )

    def test_report_keeps_form_structure_external_to_scalar_graph_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path)
            report = quadratic_form_probe(db_path=db_path, max_n=10, edge_limit=4)

        self.assertEqual(report["corpus"]["alignment"]["status"], "pass")
        self.assertEqual(report["config"]["requested_graph_stage_cutoff"], 10)
        self.assertEqual(report["config"]["effective_graph_stage_cutoff"], 10)
        self.assertFalse(report["config"]["graph_stage_cutoff_was_explicit"])
        self.assertTrue(report["summary"]["d4_reduced_form_enumeration_matches"])
        self.assertTrue(report["summary"]["d20_reduced_form_enumeration_matches"])
        self.assertFalse(
            report["summary"][
                "d20_principal_coefficients_pass_finite_multiplicativity"
            ]
        )
        self.assertTrue(
            report["summary"][
                "d20_trivial_character_channel_passes_finite_multiplicativity"
            ]
        )
        self.assertEqual(
            report["summary"]["d20_principal_first_reported_defect"]["product"],
            6,
        )

        audit = report["graph_audit"]
        relation = audit["selected_scalar_relations"]["d20_class_composition_shadow"]
        self.assertTrue(relation["present"])
        self.assertEqual(relation["directed_occurrence_count"], 2)
        self.assertFalse(audit["graph_native_quadratic_form_nodes"])
        self.assertFalse(audit["graph_native_form_class_labels"])
        self.assertFalse(
            audit["saturation_control"][
                "evaluation_relation_coverage_is_selective_evidence"
            ]
        )

        b_two = next(
            row
            for row in audit["named_external_representation_witnesses"]
            if row["form_id"] == D20_NONPRINCIPAL.form_id
            and row["value"] == 2
        )
        self.assertTrue(b_two["coordinate_nodes"]["y"]["present"])
        self.assertFalse(
            b_two["coordinate_nodes"]["y"]["operand_ready_at_latest_stage"]
        )
        self.assertFalse(b_two["representation_edge_present"])
        self.assertFalse(report["analytic_boundary"]["epstein_zeta_evaluated"])
        self.assertFalse(report["analytic_boundary"]["riemann_hypothesis_claim"])

    def test_missing_scalar_support_remains_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "fixture.sqlite"
            _create_fixture(db_path, core_max=6)
            report = quadratic_form_probe(db_path=db_path, max_n=10, edge_limit=4)
        coverage = report["graph_audit"]["scalar_node_coverage"]
        self.assertEqual(coverage["present_values"], 6)
        self.assertEqual(coverage["missing_values"], 4)
        absent = coverage["rows"][6]
        self.assertEqual(absent["status_at_stage_cutoff"], "absent_from_corpus")
        self.assertFalse(absent["confirmed_by_stage_cutoff"])
        self.assertIsNone(absent["full_corpus_lifecycle_status"])
        self.assertIsNone(absent["eventual_confirmed_stage"])

    def test_limits_fail_before_database_access(self) -> None:
        with self.assertRaisesRegex(ValueError, "pass --full-scan"):
            quadratic_form_probe(
                db_path=Path("unused.sqlite"),
                max_n=1_001,
            )
        with self.assertRaisesRegex(ValueError, "hard report-size"):
            quadratic_form_probe(
                db_path=Path("unused.sqlite"),
                max_n=10_001,
                full_scan=True,
            )
        with self.assertRaisesRegex(ValueError, "edge_limit must be >= 1"):
            quadratic_form_probe(
                db_path=Path("unused.sqlite"),
                max_n=10,
                edge_limit=0,
            )
        with self.assertRaisesRegex(ValueError, "composition_event_limit"):
            quadratic_form_probe(
                db_path=Path("unused.sqlite"),
                max_n=10,
                composition_event_limit=0,
            )
        with self.assertRaisesRegex(ValueError, "graph_stage_cutoff"):
            quadratic_form_probe(
                db_path=Path("unused.sqlite"),
                max_n=10,
                graph_stage_cutoff=0,
            )


if __name__ == "__main__":
    unittest.main()
