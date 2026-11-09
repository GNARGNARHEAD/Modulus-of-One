from __future__ import annotations

import math
import unittest

from moo.quadratic_form_nested_math import (
    BILINEAR_MAPS_BY_DISCRIMINANT,
    D20_FAMILY,
    D23_BILINEAR_MAPS,
    D23_FAMILY,
    D23_NEGATIVE_ORIENTATION,
    D23_POSITIVE_ORIENTATION,
    D56_FAMILY,
    D56_NEGATIVE_ORIENTATION,
    D56_POSITIVE_ORIENTATION,
    BilinearMap,
    bounded_composition_ledger,
    canonical_pm_i_representative,
    class_table_report,
    default_modulus_ladder,
    derive_genus_cosets,
    direct_dirichlet_class_table,
    expected_cyclic_class_table,
    find_sl2_equivalence,
    form_coefficients,
    genus_character_audit_d56,
    inverse_reflection_report,
    local_residue_distribution,
    proper_pm_i_images,
    proper_pm_i_orbit_table,
    quotient_ladder_report,
    symbolic_bilinear_residual,
    symbolic_identity_report,
    transform_coefficients,
)
from moo.quadratic_form_probe import enumerate_representations, reduced_primitive_forms


class NestedQuadraticFormSpecificationTests(unittest.TestCase):
    def test_reduced_form_families_are_exact(self) -> None:
        expected = {
            -20: {(1, 0, 5), (2, 2, 3)},
            -23: {(1, 1, 6), (2, -1, 3), (2, 1, 3)},
            -56: {(1, 0, 14), (2, 0, 7), (3, -2, 5), (3, 2, 5)},
        }
        for family in (D20_FAMILY, D23_FAMILY, D56_FAMILY):
            configured = {form_coefficients(form) for form in family.forms}
            self.assertEqual(configured, expected[family.discriminant])
            self.assertEqual(
                set(reduced_primitive_forms(family.discriminant)),
                configured,
            )
            for form in family.forms:
                self.assertTrue(form.is_primitive)
                self.assertTrue(form.is_reduced)
                self.assertEqual(form.discriminant, family.discriminant)

        for form in D23_FAMILY.forms:
            self.assertNotIn("gauss_notation", form.payload())

    def test_generic_pm_i_orbits_partition_every_bounded_fibre(self) -> None:
        for family in (D20_FAMILY, D23_FAMILY, D56_FAMILY):
            for form in family.forms:
                representations = enumerate_representations(form, 40)
                orbits = proper_pm_i_orbit_table(form, representations)
                for value in range(1, 41):
                    self.assertEqual(
                        2 * len(orbits[value]),
                        len(representations[value]),
                    )

        pair = (1, 1)
        self.assertNotIn(
            (1, -1),
            proper_pm_i_images(D23_POSITIVE_ORIENTATION, pair),
        )
        self.assertEqual(
            canonical_pm_i_representative(D23_POSITIVE_ORIENTATION, pair),
            (-1, -1),
        )

    def test_inverse_reflection_is_exact_but_improper(self) -> None:
        for family in (D20_FAMILY, D23_FAMILY, D56_FAMILY):
            report = inverse_reflection_report(family, max_n=60)
            self.assertTrue(report["all_inverse_reflection_controls_exact"])
            for form_record in report["forms"]:
                self.assertTrue(form_record["witness_bijection_exact"])
                self.assertTrue(form_record["inverse_class_matches"])
                self.assertEqual(form_record["reflection_determinant"], -1)
                self.assertTrue(form_record["reflection_is_not_proper"])

        for positive, negative in (
            (D23_POSITIVE_ORIENTATION, D23_NEGATIVE_ORIENTATION),
            (D56_POSITIVE_ORIENTATION, D56_NEGATIVE_ORIENTATION),
        ):
            positive_table = enumerate_representations(positive, 100)
            negative_table = enumerate_representations(negative, 100)
            for value in range(1, 101):
                self.assertEqual(
                    {(x, -y) for x, y in positive_table[value]},
                    set(negative_table[value]),
                )


class NestedQuadraticFormCompositionTests(unittest.TestCase):
    def test_all_configured_bilinear_maps_are_symbolic_identities(self) -> None:
        for family in (D20_FAMILY, D23_FAMILY, D56_FAMILY):
            report = symbolic_identity_report(family)
            self.assertTrue(report["all_symbolic_identities_hold"])
            self.assertTrue(report["maps"])
            self.assertTrue(all(not row["nonzero_residual_terms"] for row in report["maps"]))

        valid = D23_BILINEAR_MAPS[0]
        broken = BilinearMap(
            map_id="deliberately_broken",
            left_form_id=valid.left_form_id,
            right_form_id=valid.right_form_id,
            target_form_id=valid.target_form_id,
            x_coefficients=(
                valid.x_coefficients[0] + 1,
                *valid.x_coefficients[1:],
            ),
            y_coefficients=valid.y_coefficients,
        )
        self.assertTrue(
            symbolic_bilinear_residual(broken, D23_FAMILY.forms_by_id)
        )

    def test_named_inverse_class_witnesses_multiply_exactly(self) -> None:
        maps = {
            bilinear_map.map_id: bilinear_map
            for bilinear_map in D23_BILINEAR_MAPS
        }
        pp_output = maps["d23_PP_to_M"].apply((1, 0), (0, 1))
        self.assertEqual(
            D23_NEGATIVE_ORIENTATION.evaluate(*pp_output),
            D23_POSITIVE_ORIENTATION.evaluate(1, 0)
            * D23_POSITIVE_ORIENTATION.evaluate(0, 1),
        )
        self.assertEqual(
            canonical_pm_i_representative(D23_NEGATIVE_ORIENTATION, pp_output),
            (-1, 1),
        )

    def test_direct_dirichlet_tables_match_the_fixed_cyclic_laws(self) -> None:
        for family in (D20_FAMILY, D23_FAMILY, D56_FAMILY):
            direct = direct_dirichlet_class_table(family)
            expected = expected_cyclic_class_table(family)
            self.assertEqual(direct, expected)
            report = class_table_report(family)
            self.assertTrue(report["matches_expected_cyclic_table"])

    def test_sl2_search_is_proper_and_exact(self) -> None:
        source = (6, 5, 2)
        target = (2, -1, 3)
        matrix = find_sl2_equivalence(source, target, bound=2)
        self.assertIsNotNone(matrix)
        assert matrix is not None
        self.assertEqual(matrix[0] * matrix[3] - matrix[1] * matrix[2], 1)
        self.assertEqual(transform_coefficients(source, matrix), target)
        with self.assertRaises(ValueError):
            transform_coefficients(source, (1, 0, 0, -1))

    def test_bounded_orbit_ledgers_land_in_complete_target_fibres(self) -> None:
        for family, bound in ((D23_FAMILY, 32), (D56_FAMILY, 28)):
            ledger = bounded_composition_ledger(
                family,
                max_n=bound,
                event_limit=20,
            )
            self.assertTrue(ledger["all_events_verified_exactly"])
            self.assertEqual(ledger["identity_failure_count"], 0)
            self.assertEqual(ledger["target_fibre_failure_count"], 0)
            self.assertEqual(ledger["class_target_failure_count"], 0)
            self.assertGreater(ledger["total_composition_events"], 20)
            self.assertTrue(ledger["events_truncated"])
            self.assertFalse(ledger["complete_event_list_emitted"])
            self.assertEqual(ledger["event_limit"], 20)
            self.assertEqual(
                ledger["distinct_scalar_relation_count"],
                len(ledger["scalar_relation_ids"]),
            )
            self.assertGreater(ledger["distinct_scalar_relation_count"], 0)
            self.assertEqual(
                set(ledger["signature_counts"]),
                {
                    bilinear_map.map_id
                    for bilinear_map in BILINEAR_MAPS_BY_DISCRIMINANT[
                        family.discriminant
                    ]
                },
            )
            self.assertTrue(all(ledger["signature_counts"].values()))

            no_examples = bounded_composition_ledger(
                family,
                max_n=bound,
                event_limit=0,
            )
            complete = bounded_composition_ledger(
                family,
                max_n=bound,
                event_limit=100_000,
            )
            for other in (no_examples, complete):
                self.assertEqual(
                    other["total_composition_events"],
                    ledger["total_composition_events"],
                )
                self.assertEqual(
                    other["signature_counts"],
                    ledger["signature_counts"],
                )
                self.assertEqual(
                    other["scalar_relation_ids"],
                    ledger["scalar_relation_ids"],
                )
                self.assertEqual(
                    other["distinct_scalar_relation_count"],
                    ledger["distinct_scalar_relation_count"],
                )
            self.assertEqual(no_examples["reported_event_count"], 0)
            self.assertTrue(no_examples["events_truncated"])
            self.assertFalse(no_examples["complete_event_list_emitted"])
            self.assertEqual(
                complete["reported_event_count"],
                complete["total_composition_events"],
            )
            self.assertFalse(complete["events_truncated"])
            self.assertTrue(complete["complete_event_list_emitted"])


class NestedQuadraticFormGenusAndQuotientTests(unittest.TestCase):
    def test_genus_cosets_are_derived_as_class_group_modulo_squares(self) -> None:
        d20 = derive_genus_cosets(D20_FAMILY)
        d23 = derive_genus_cosets(D23_FAMILY)
        d56 = derive_genus_cosets(D56_FAMILY)
        self.assertEqual(d20["genus_count"], 2)
        self.assertEqual(d23["genus_count"], 1)
        self.assertEqual(d56["genus_count"], 2)
        self.assertEqual(
            d23["cosets"],
            [[form.form_id for form in D23_FAMILY.forms]],
        )
        self.assertEqual(
            d56["cosets"],
            [
                [
                    D56_FAMILY.form_id_by_exponent[0],
                    D56_FAMILY.form_id_by_exponent[2],
                ],
                [
                    D56_FAMILY.form_id_by_exponent[1],
                    D56_FAMILY.form_id_by_exponent[3],
                ],
            ],
        )

    def test_d23_conductor_distribution_is_identical_across_classes(self) -> None:
        distributions = [
            local_residue_distribution(form, 23) for form in D23_FAMILY.forms
        ]
        self.assertTrue(all(distribution == distributions[0] for distribution in distributions))
        squares = {value * value % 23 for value in range(1, 23)}
        self.assertEqual(distributions[0][0], 23)
        for residue in range(1, 23):
            self.assertEqual(
                distributions[0][residue],
                46 if residue in squares else 0,
            )

    def test_d56_local_residues_split_exactly_by_genus(self) -> None:
        by_id_mod_7 = {
            form.form_id: local_residue_distribution(form, 7)
            for form in D56_FAMILY.forms
        }
        by_id_mod_8 = {
            form.form_id: local_residue_distribution(form, 8)
            for form in D56_FAMILY.forms
        }
        a_id = D56_FAMILY.form_id_by_exponent[0]
        p_id = D56_FAMILY.form_id_by_exponent[1]
        c_id = D56_FAMILY.form_id_by_exponent[2]
        m_id = D56_FAMILY.form_id_by_exponent[3]
        self.assertEqual(by_id_mod_7[a_id], by_id_mod_7[c_id])
        self.assertEqual(by_id_mod_7[p_id], by_id_mod_7[m_id])
        self.assertNotEqual(by_id_mod_7[a_id], by_id_mod_7[p_id])
        self.assertEqual(
            {residue for residue, count in by_id_mod_7[a_id].items() if count},
            {0, 1, 2, 4},
        )
        self.assertEqual(
            {residue for residue, count in by_id_mod_7[p_id].items() if count},
            {0, 3, 5, 6},
        )
        self.assertEqual(by_id_mod_8[a_id], by_id_mod_8[c_id])
        self.assertEqual(by_id_mod_8[p_id], by_id_mod_8[m_id])
        self.assertEqual(
            {
                residue
                for residue, count in by_id_mod_8[a_id].items()
                if count and residue % 2
            },
            {1, 7},
        )
        self.assertEqual(
            {
                residue
                for residue, count in by_id_mod_8[p_id].items()
                if count and residue % 2
            },
            {3, 5},
        )

        by_id_mod_56 = {
            form.form_id: local_residue_distribution(form, 56)
            for form in D56_FAMILY.forms
        }
        self.assertEqual(by_id_mod_56[a_id], by_id_mod_56[c_id])
        self.assertEqual(by_id_mod_56[p_id], by_id_mod_56[m_id])
        principal_coprime_support = {
            residue
            for residue, count in by_id_mod_56[a_id].items()
            if count and math.gcd(residue, 56) == 1
        }
        other_coprime_support = {
            residue
            for residue, count in by_id_mod_56[p_id].items()
            if count and math.gcd(residue, 56) == 1
        }
        self.assertTrue(principal_coprime_support)
        self.assertTrue(other_coprime_support)
        self.assertFalse(principal_coprime_support & other_coprime_support)

    def test_d56_coprime_scalar_character_matches_derived_genus(self) -> None:
        audit = genus_character_audit_d56(max_n=200)
        self.assertGreater(audit["checked_form_value_pairs"], 0)
        self.assertTrue(audit["all_coprime_values_match_derived_genus"])
        self.assertEqual(audit["mismatch_count"], 0)

    def test_quotient_ladder_has_singleton_and_injective_endpoints(self) -> None:
        bound = 40
        for family in (D23_FAMILY, D56_FAMILY):
            expected_moduli = default_modulus_ladder(family, max_n=bound)
            report = quotient_ladder_report(family, max_n=bound)
            self.assertEqual(tuple(report["moduli"]), expected_moduli)
            self.assertTrue(report["modulus_one_is_singleton"])
            by_modulus = {
                row["modulus"]: row for row in report["modulus_records"]
            }
            self.assertEqual(by_modulus[1]["bare_occupied_residues"], [0])
            injective = by_modulus[bound + 1]
            for form_record in injective["forms"]:
                for values in form_record["bounded_distinct_value_buckets"].values():
                    self.assertLessEqual(len(values), 1)


if __name__ == "__main__":
    unittest.main()
