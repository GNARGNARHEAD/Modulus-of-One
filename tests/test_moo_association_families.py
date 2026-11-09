from __future__ import annotations

from fractions import Fraction
import unittest

from moo.association_families import generate_associations
from research.strict_stage.route_identity.pascal_shell_calibration import certificates


class AssociationSelectorTests(unittest.TestCase):
    def test_shell_selection_matches_independent_ordered_pair_search(self) -> None:
        cap = 25
        specs = generate_associations(square_height=0, max_radius=cap, spiral_steps=0)
        by_id = {spec["id"]: spec for spec in specs}
        expected = {
            (Fraction(x), Fraction(y), Fraction(r))
            for x in range(1, cap)
            for y in range(1, cap)
            for r in range(1, cap + 1)
            if x * x + y * y == r * r
        }
        actual = {
            tuple(Fraction(spec["parameters"][key]) for key in ("x", "y", "r"))
            for spec in specs if spec["parameters"]["r"] != "1"
        }
        self.assertEqual(actual, expected)
        self.assertNotIn("shell:3,4,6", by_id)
        for x, y, r in expected:
            raw = by_id[f"shell:{x},{y},{r}"]
            normalized = by_id[f"shell:{x/r},{y/r},1"]
            self.assertEqual(raw["relations"][0]["target"], normalized["id"])
            self.assertIn(raw["id"], {relation["target"] for relation in normalized["relations"]})
        self.assertNotEqual(by_id["shell:3/5,4/5,1"]["id"], by_id["shell:4/5,3/5,1"]["id"])
        normalization_ids = {c["id"] for c in by_id["shell:3/5,4/5,1"]["certificates"]}
        self.assertTrue({"normalize:3,4,5", "normalize:6,8,10"} <= normalization_ids)

    def test_signed_spiral_sources_keep_orientation_without_positive_encoding(self) -> None:
        specs = generate_associations(square_height=0, max_radius=0, spiral_steps=3)
        by_id = {spec["id"]: spec for spec in specs}
        negative = by_id["shell:-44/125,117/125,1"]
        self.assertEqual([certificate["id"] for certificate in negative["certificates"]], ["literal"])
        self.assertEqual(negative["relations"][0]["target"], "shell:-44,117,125")
        self.assertNotIn("shell:44/125,117/125,1", by_id)
        for spec in specs:
            for certificate in spec["certificates"]:
                if certificate["criterion"] == "integer_encoded_normalized_shell":
                    self.assertEqual(len(certificate["requests"]), 9)
                    for request in certificate["requests"]:
                        for operand in (request["left"], request["right"]):
                            value = Fraction(operand)
                            self.assertEqual(value.denominator, 1)
                            self.assertGreater(value, 0)

    def test_fixed_route_adapter_preserves_premises_and_selection_bounds(self) -> None:
        for height, expected_families in ((8, set()), (9, {"generic"}), (25, {"generic", "shell"})):
            specs = generate_associations(square_height=height, max_radius=0, spiral_steps=0)
            self.assertTrue(all(Fraction(spec["parameters"]["root"]) <= height for spec in specs))
            adapted = {
                certificate["parameters"]["route_id"]: (spec, certificate)
                for spec in specs for certificate in spec["certificates"]
                if certificate["criterion"] == "fixed_square_route_certificate"
            }
            expected = {route.route_id: route for route in certificates()
                        if route.external_family in expected_families}
            self.assertEqual(adapted.keys(), expected.keys())
            for identifier, route in expected.items():
                association, certificate = adapted[identifier]
                root = Fraction(association["parameters"]["root"])
                self.assertEqual(root * root, Fraction(*route.target))
                actual_requests = {
                    (request["role"], Fraction(request["left"]), request["op"],
                     Fraction(request["right"]), Fraction(request["result"]))
                    for request in certificate["requests"]
                }
                source_requests = {
                    (f"{prefix}:{step.step_id}", Fraction(*step.left), step.op,
                     Fraction(*step.right), Fraction(*step.result))
                    for prefix, steps in (("step", route.steps), ("premise", route.premise_steps))
                    for step in steps
                }
                expected_bindings = ({("binding:root_sum", Fraction(7), "+", Fraction(2), Fraction(9))}
                                     if identifier in {"generic_expanded_left", "generic_expanded_paired"} else set())
                self.assertEqual(actual_requests, source_requests | expected_bindings)
                self.assertTrue(any(root in (request[1], request[3], request[4])
                                    for request in actual_requests))
                self.assertEqual(certificate["parameters"]["dependency_tags"], list(route.dependency_tags))
            if "shell_composed_norm" in adapted:
                _, norm = adapted["shell_composed_norm"]
                self.assertIn(
                    ("premise:cross_reversed", "3", "*", "4", "12"),
                    {(r["role"], r["left"], r["op"], r["right"], r["result"])
                     for r in norm["requests"]},
                )


if __name__ == "__main__":
    unittest.main()
