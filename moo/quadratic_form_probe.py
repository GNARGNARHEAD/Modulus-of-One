from __future__ import annotations

import argparse
import json
import math
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from moo.graph_invariants import node_for_key, node_payload
from moo.research_utils import (
    connect_readonly,
    emit_json,
    positive_int,
    report_metadata,
    require_strict_alignment,
)


Pair = Tuple[int, int]
RepresentationTable = Dict[int, Tuple[Pair, ...]]
OrbitTable = Dict[int, Tuple[Pair, ...]]

DEFAULT_MAX_N = 200
SOFT_MAX_N = 1_000
HARD_MAX_N = 10_000
DEFAULT_EDGE_LIMIT = 8
DEFAULT_COMPOSITION_EVENT_LIMIT = 10_000


@dataclass(frozen=True)
class BinaryQuadraticForm:
    form_id: str
    class_label: str
    a: int
    b: int
    c: int
    automorphism_normalization: int

    def __post_init__(self) -> None:
        if self.a <= 0:
            raise ValueError("positive-definite forms require a > 0")
        if self.discriminant >= 0:
            raise ValueError("positive-definite forms require b^2 - 4ac < 0")
        if self.automorphism_normalization < 1:
            raise ValueError("automorphism_normalization must be >= 1")

    @property
    def discriminant(self) -> int:
        return self.b * self.b - 4 * self.a * self.c

    @property
    def determinant_numerator(self) -> int:
        return 4 * self.a * self.c - self.b * self.b

    @property
    def is_primitive(self) -> bool:
        return math.gcd(math.gcd(abs(self.a), abs(self.b)), abs(self.c)) == 1

    @property
    def is_reduced(self) -> bool:
        boundary_sign_ok = not (
            (abs(self.b) == self.a or self.a == self.c) and self.b < 0
        )
        return abs(self.b) <= self.a <= self.c and boundary_sign_ok

    def evaluate(self, x: int, y: int) -> int:
        return self.a * x * x + self.b * x * y + self.c * y * y

    def payload(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "form_id": self.form_id,
            "class_label": self.class_label,
            "coefficients": {"a": self.a, "b": self.b, "c": self.c},
            "formula": f"{self.a}*x^2 + {self.b}*x*y + {self.c}*y^2",
            "discriminant": self.discriminant,
            "positive_definite": True,
            "primitive": self.is_primitive,
            "reduced": self.is_reduced,
            "automorphism_normalization": self.automorphism_normalization,
            "completed_square_identity": (
                f"4*{self.a}*Q(x,y) = "
                f"(2*{self.a}*x + {self.b}*y)^2 + "
                f"{self.determinant_numerator}*y^2"
            ),
        }
        if self.b % 2 == 0:
            gauss_middle = self.b // 2
            payload["gauss_notation"] = {
                "coefficients_a_b_c": [self.a, gauss_middle, self.c],
                "formula_convention": "a*x^2 + 2*b*x*y + c*y^2",
                "determinant_b2_minus_ac": (
                    gauss_middle * gauss_middle - self.a * self.c
                ),
                "modern_discriminant_relation": "Delta=4*d_Gauss",
            }
        return payload


D4_PRINCIPAL = BinaryQuadraticForm(
    form_id="d4_principal_x2_plus_y2",
    class_label="principal",
    a=1,
    b=0,
    c=1,
    automorphism_normalization=4,
)
D20_PRINCIPAL = BinaryQuadraticForm(
    form_id="d20_principal_x2_plus_5y2",
    class_label="principal",
    a=1,
    b=0,
    c=5,
    automorphism_normalization=2,
)
D20_NONPRINCIPAL = BinaryQuadraticForm(
    form_id="d20_nonprincipal_2x2_plus_2xy_plus_3y2",
    class_label="nonprincipal",
    a=2,
    b=2,
    c=3,
    automorphism_normalization=2,
)


def _ceil_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return -((-numerator) // denominator)


def enumerate_representations(
    form: BinaryQuadraticForm,
    max_n: int,
) -> RepresentationTable:
    """Enumerate every integer pair with 0 < Q(x,y) <= max_n exactly."""
    if int(max_n) < 1:
        raise ValueError("max_n must be >= 1")

    limit = int(max_n)
    delta = form.determinant_numerator
    four_a_n = 4 * form.a * limit
    max_abs_y = math.isqrt(four_a_n // delta)
    found: Dict[int, List[Pair]] = {n: [] for n in range(1, limit + 1)}

    # 4aQ = (2ax+by)^2 + (4ac-b^2)y^2.  The bounds below are
    # therefore necessary and sufficient for the finite search box.
    for y in range(-max_abs_y, max_abs_y + 1):
        remaining = four_a_n - delta * y * y
        if remaining < 0:
            continue
        radius = math.isqrt(remaining)
        denominator = 2 * form.a
        min_x = _ceil_div(-radius - form.b * y, denominator)
        max_x = (radius - form.b * y) // denominator
        for x in range(min_x, max_x + 1):
            value = form.evaluate(x, y)
            if 0 < value <= limit:
                found[value].append((x, y))

    return {
        n: tuple(sorted(found[n]))
        for n in range(1, limit + 1)
    }


def normalized_coefficients(
    form: BinaryQuadraticForm,
    representations: Mapping[int, Sequence[Pair]],
) -> Dict[int, int]:
    coefficients: Dict[int, int] = {}
    divisor = form.automorphism_normalization
    for n in sorted(representations):
        count = len(representations[n])
        if count % divisor != 0:
            raise AssertionError(
                f"representation count {count} for n={n} is not divisible by {divisor}"
            )
        coefficients[int(n)] = count // divisor
    return coefficients


def proper_automorphism_images(
    form: BinaryQuadraticForm,
    pair: Pair,
) -> Tuple[Pair, ...]:
    """Return the proper-automorphism orbit used by the configured forms."""
    x, y = pair
    if form.form_id == D4_PRINCIPAL.form_id:
        images = ((x, y), (-y, x), (-x, -y), (y, -x))
    elif form.form_id in {
        D20_PRINCIPAL.form_id,
        D20_NONPRINCIPAL.form_id,
    }:
        images = ((x, y), (-x, -y))
    else:
        raise ValueError(f"no configured automorphism action for {form.form_id}")
    unique = tuple(sorted(set(images)))
    if len(unique) != form.automorphism_normalization:
        raise AssertionError(
            f"unexpected orbit size for {form.form_id} at {pair}: {len(unique)}"
        )
    if any(form.evaluate(*image) != form.evaluate(x, y) for image in unique):
        raise AssertionError(f"automorphism orbit changed {form.form_id}")
    return unique


def canonical_proper_orbit_representative(
    form: BinaryQuadraticForm,
    pair: Pair,
) -> Pair:
    return min(proper_automorphism_images(form, pair))


def proper_orbit_representatives(
    form: BinaryQuadraticForm,
    representations: Mapping[int, Sequence[Pair]],
) -> OrbitTable:
    table: OrbitTable = {}
    for value in sorted(representations):
        witnesses = set(representations[value])
        representatives = {
            canonical_proper_orbit_representative(form, pair)
            for pair in witnesses
        }
        reconstructed = {
            image
            for representative in representatives
            for image in proper_automorphism_images(form, representative)
        }
        if reconstructed != witnesses:
            raise AssertionError(
                f"proper automorphism orbits do not partition {form.form_id} "
                f"at n={value}"
            )
        if len(representatives) * form.automorphism_normalization != len(witnesses):
            raise AssertionError(
                f"orbit normalization mismatch for {form.form_id} at n={value}"
            )
        table[int(value)] = tuple(sorted(representatives))
    return table


def representation_rows(
    form: BinaryQuadraticForm,
    representations: Mapping[int, Sequence[Pair]],
) -> List[Dict[str, object]]:
    coefficients = normalized_coefficients(form, representations)
    return [
        {
            "n": int(n),
            "represented": bool(representations[n]),
            "representation_count": len(representations[n]),
            "normalized_coefficient": coefficients[n],
            "witnesses": [
                {"x": int(x), "y": int(y)}
                for x, y in representations[n]
            ],
        }
        for n in sorted(representations)
    ]


def reduced_primitive_forms(discriminant: int) -> Tuple[Tuple[int, int, int], ...]:
    """Enumerate standard reduced primitive positive forms of negative D."""
    d = int(discriminant)
    if d >= 0 or d % 4 not in {0, 1}:
        raise ValueError("discriminant must be negative and congruent to 0 or 1 mod 4")

    forms: List[Tuple[int, int, int]] = []
    abs_d = abs(d)
    a = 1
    while 3 * a * a <= abs_d:
        for b in range(-a, a + 1):
            numerator = b * b - d
            denominator = 4 * a
            if numerator % denominator:
                continue
            c = numerator // denominator
            if not (abs(b) <= a <= c):
                continue
            if (abs(b) == a or a == c) and b < 0:
                continue
            if math.gcd(math.gcd(a, abs(b)), c) != 1:
                continue
            forms.append((a, b, c))
        a += 1
    return tuple(sorted(forms))


def quarter_turn(pair: Pair) -> Pair:
    x, y = pair
    return -y, x


def gaussian_multiply(left: Pair, right: Pair) -> Pair:
    x, y = left
    u, v = right
    return x * u - y * v, x * v + y * u


def gaussian_norm(pair: Pair) -> int:
    x, y = pair
    return x * x + y * y


def d20_principal_principal(left: Pair, right: Pair) -> Pair:
    x, y = left
    u, v = right
    return x * u - 5 * y * v, x * v + y * u


def d20_principal_nonprincipal(left: Pair, right: Pair) -> Pair:
    x, y = left
    u, v = right
    return x * u - y * u - 3 * y * v, x * v + 2 * y * u + y * v


def d20_nonprincipal_nonprincipal(left: Pair, right: Pair) -> Pair:
    x, y = left
    u, v = right
    return (
        2 * x * u + x * v + y * u - 2 * y * v,
        x * v + y * u + y * v,
    )


def _relation_id(left: int, op: str, right: int, result: int) -> str:
    names = {"+": "add", "-": "subtract", "*": "multiply"}
    if op not in names:
        raise ValueError(f"unsupported evaluation operation: {op}")
    return f"{names[op]}:{left}:{right}:{result}"


def _commutative_relation_key(
    left: int,
    op: str,
    right: int,
    result: int,
) -> str:
    if op not in {"+", "*"}:
        return _relation_id(left, op, right, result)
    if right < left:
        left, right = right, left
    return _relation_id(left, op, right, result)


def _relation_spec_from_id(relation_id: str) -> Tuple[int, str, int, int]:
    parts = str(relation_id).split(":")
    if len(parts) != 4:
        raise ValueError(f"invalid scalar relation id: {relation_id}")
    operations = {"add": "+", "subtract": "-", "multiply": "*"}
    if parts[0] not in operations:
        raise ValueError(f"invalid scalar relation operation: {parts[0]}")
    return int(parts[1]), operations[parts[0]], int(parts[2]), int(parts[3])


def _evaluation_step(
    *,
    left: int,
    op: str,
    right: int,
    result: int,
    role: str,
) -> Dict[str, object]:
    if min(left, right, result) < 1:
        raise ValueError("positive-spine evaluation steps require positive values")
    if op == "+":
        exact = left + right == result
    elif op == "-":
        exact = left - right == result
    elif op == "*":
        exact = left * right == result
    else:
        raise ValueError(f"unsupported evaluation operation: {op}")
    if not exact:
        raise AssertionError(f"inexact evaluation step: {left}{op}{right}!={result}")
    return {
        "relation_id": _relation_id(left, op, right, result),
        "role": role,
        "left": int(left),
        "op": op,
        "right": int(right),
        "result": int(result),
    }


def _coordinate_relation_step(
    *,
    left: int,
    op: str,
    right: int,
    result: int,
    role: str,
) -> Dict[str, object]:
    if min(left, right) < 1 or result < 0:
        raise ValueError(
            "coordinate-rewrite relations require positive operands and a "
            "nonnegative result"
        )
    if op == "+":
        exact = left + right == result
    elif op == "-":
        exact = left - right == result
    else:
        raise ValueError(f"unsupported coordinate operation: {op}")
    if not exact:
        raise AssertionError(f"inexact coordinate relation: {left}{op}{right}!={result}")
    return {
        "relation_id": _relation_id(left, op, right, result),
        "role": role,
        "left": int(left),
        "op": op,
        "right": int(right),
        "result": int(result),
        "status": (
            "external signed-coordinate rewrite with an exact graph scalar shadow; "
            "not a chronological form-evaluation operand step"
        ),
    }


def _square_term(
    magnitude: int,
    *,
    role: str,
    steps: List[Dict[str, object]],
) -> int:
    value = abs(int(magnitude))
    if value == 0:
        return 0
    square = value * value
    steps.append(
        _evaluation_step(
            left=value,
            op="*",
            right=value,
            result=square,
            role=role,
        )
    )
    return square


def _scaled_term(
    coefficient: int,
    value: int,
    *,
    role: str,
    steps: List[Dict[str, object]],
) -> int:
    if value == 0:
        return 0
    if coefficient == 1:
        return value
    result = coefficient * value
    steps.append(
        _evaluation_step(
            left=coefficient,
            op="*",
            right=value,
            result=result,
            role=role,
        )
    )
    return result


def _sum_terms(
    terms: Sequence[Tuple[str, int]],
    *,
    steps: List[Dict[str, object]],
) -> int:
    positive = [(label, value) for label, value in terms if value > 0]
    if not positive:
        raise AssertionError("a positive-definite representation needs a positive term")
    accumulated_label, accumulated = positive[0]
    for label, value in positive[1:]:
        result = accumulated + value
        steps.append(
            _evaluation_step(
                left=accumulated,
                op="+",
                right=value,
                result=result,
                role=f"sum:{accumulated_label}+{label}",
            )
        )
        accumulated_label = f"({accumulated_label}+{label})"
        accumulated = result
    return accumulated


def _absolute_linear_sum(
    x: int,
    y: int,
    *,
    coordinate_steps: List[Dict[str, object]],
) -> Tuple[int, Dict[str, object]]:
    abs_x = abs(int(x))
    abs_y = abs(int(y))
    target = abs(int(x) + int(y))
    payload: Dict[str, object] = {
        "source": "x+y",
        "x": int(x),
        "y": int(y),
        "absolute_target": target,
        "sign_normalization": "external_exact_coordinate_normalization",
    }
    if abs_x == 0 or abs_y == 0:
        payload["construction"] = "zero-coordinate identity; no graph edge required"
        return target, payload
    if (x > 0 and y > 0) or (x < 0 and y < 0):
        step = _coordinate_relation_step(
            left=abs_x,
            op="+",
            right=abs_y,
            result=target,
            role="absolute_linear_coordinate:|x+y|",
        )
        coordinate_steps.append(step)
        payload["construction"] = "same-sign magnitudes add"
        payload["relation_id"] = step["relation_id"]
        return target, payload

    larger = max(abs_x, abs_y)
    smaller = min(abs_x, abs_y)
    if larger == smaller:
        step = _coordinate_relation_step(
            left=larger,
            op="-",
            right=smaller,
            result=0,
            role="absolute_linear_coordinate:|x+y|:zero_cancellation",
        )
        coordinate_steps.append(step)
        payload["construction"] = (
            "opposite magnitudes cancel to zero; the zero term is omitted from "
            "the positive-spine evaluation DAG"
        )
        payload["omitted_relational_identity"] = f"{larger}-{smaller}=0"
        payload["relation_id"] = step["relation_id"]
        return 0, payload
    step = _coordinate_relation_step(
        left=larger,
        op="-",
        right=smaller,
        result=target,
        role="absolute_linear_coordinate:|x+y|",
    )
    coordinate_steps.append(step)
    payload["construction"] = "opposite-sign magnitudes subtract"
    payload["relation_id"] = step["relation_id"]
    return target, payload


def positive_spine_evaluation_plan(
    form: BinaryQuadraticForm,
    x: int,
    y: int,
) -> Dict[str, object]:
    """Build a canonical positive-spine scalar DAG for one external form witness."""
    steps: List[Dict[str, object]] = []
    coordinate_steps: List[Dict[str, object]] = []
    value = form.evaluate(int(x), int(y))
    if value < 1:
        raise ValueError("evaluation plans require a positive represented value")

    coordinate_payload: Dict[str, object] = {
        "x": int(x),
        "y": int(y),
        "absolute_x": abs(int(x)),
        "absolute_y": abs(int(y)),
        "status": (
            "the association between signed coordinates and this positive-spine "
            "scalar DAG is an external exact quadratic-form annotation"
        ),
    }
    x_square = _square_term(x, role="x_square", steps=steps)

    if form.form_id in {
        D4_PRINCIPAL.form_id,
        D20_PRINCIPAL.form_id,
    }:
        y_square = _square_term(y, role="y_square", steps=steps)
        y_term = _scaled_term(
            form.c,
            y_square,
            role=f"scale_y_square_by_{form.c}",
            steps=steps,
        )
        result = _sum_terms(
            (("x_square", x_square), ("scaled_y_square", y_term)),
            steps=steps,
        )
        rewrite = f"{form.a}*x^2 + {form.c}*y^2"
        zero_term_labels = [
            label
            for label, term in (("x_square", x), ("y_square", y))
            if term == 0
        ]
    elif form.form_id == D20_NONPRINCIPAL.form_id:
        linear, linear_payload = _absolute_linear_sum(
            x,
            y,
            coordinate_steps=coordinate_steps,
        )
        coordinate_payload["absolute_x_plus_y"] = linear_payload
        linear_square = _square_term(
            linear,
            role="x_plus_y_square",
            steps=steps,
        )
        y_square = _square_term(y, role="y_square", steps=steps)
        two_y_square = _scaled_term(
            2,
            y_square,
            role="scale_y_square_by_2",
            steps=steps,
        )
        result = _sum_terms(
            (
                ("x_square", x_square),
                ("x_plus_y_square", linear_square),
                ("two_y_square", two_y_square),
            ),
            steps=steps,
        )
        rewrite = "x^2 + (x+y)^2 + 2*y^2"
        zero_term_labels = [
            label
            for label, term in (
                ("x_square", x),
                ("x_plus_y_square", x + y),
                ("two_y_square", y),
            )
            if term == 0
        ]
    else:
        raise ValueError(f"no canonical evaluation plan for form {form.form_id}")

    if result != value:
        raise AssertionError(
            f"evaluation plan for {form.form_id} produced {result}, expected {value}"
        )
    formula_relation_ids = [str(step["relation_id"]) for step in steps]
    coordinate_relation_ids = [
        str(step["relation_id"]) for step in coordinate_steps
    ]
    relation_ids = formula_relation_ids + coordinate_relation_ids
    return {
        "form_id": form.form_id,
        "class_label": form.class_label,
        "coordinates": coordinate_payload,
        "represented_value": value,
        "positive_rewrite": rewrite,
        "zero_term_omission_policy": (
            "zero-valued terms are recorded by label and never used as operands"
        ),
        "zero_term_omission_occurred": bool(zero_term_labels),
        "omitted_zero_term_labels": zero_term_labels,
        "formula_step_occurrences": steps,
        "formula_step_occurrence_count": len(steps),
        "coordinate_relation_occurrences": coordinate_steps,
        "coordinate_relation_occurrence_count": len(coordinate_steps),
        "relation_role_occurrence_count": len(steps) + len(coordinate_steps),
        "distinct_formula_relation_ids": sorted(set(formula_relation_ids)),
        "distinct_coordinate_relation_ids": sorted(set(coordinate_relation_ids)),
        "distinct_relation_ids": sorted(set(relation_ids)),
        "modulus_one_result_residue": 0,
    }


def d20_composition_event_ledger(
    principal_representations: RepresentationTable,
    nonprincipal_representations: RepresentationTable,
    *,
    max_n: int,
    event_limit: int = DEFAULT_COMPOSITION_EVENT_LIMIT,
) -> Dict[str, object]:
    if event_limit < 1:
        raise ValueError("composition event_limit must be >= 1")
    principal_orbits = proper_orbit_representatives(
        D20_PRINCIPAL,
        principal_representations,
    )
    nonprincipal_orbits = proper_orbit_representatives(
        D20_NONPRINCIPAL,
        nonprincipal_representations,
    )
    by_target_orbit = {
        D20_PRINCIPAL.form_id: principal_orbits,
        D20_NONPRINCIPAL.form_id: nonprincipal_orbits,
    }
    configurations = (
        (
            D20_PRINCIPAL,
            principal_orbits,
            D20_PRINCIPAL,
            principal_orbits,
            D20_PRINCIPAL,
            "principal*principal->principal",
            d20_principal_principal,
            True,
        ),
        (
            D20_PRINCIPAL,
            principal_orbits,
            D20_NONPRINCIPAL,
            nonprincipal_orbits,
            D20_NONPRINCIPAL,
            "principal*nonprincipal->nonprincipal",
            d20_principal_nonprincipal,
            False,
        ),
        (
            D20_NONPRINCIPAL,
            nonprincipal_orbits,
            D20_NONPRINCIPAL,
            nonprincipal_orbits,
            D20_PRINCIPAL,
            "nonprincipal*nonprincipal->principal",
            d20_nonprincipal_nonprincipal,
            True,
        ),
    )
    records: List[Dict[str, object]] = []
    signature_counts: Dict[str, int] = {}
    scalar_relation_ids = set()
    total_events = 0
    identity_failures = 0
    target_fibre_failures = 0

    for (
        left_form,
        left_table,
        right_form,
        right_table,
        target_form,
        signature,
        compose,
        unordered_sources,
    ) in configurations:
        for left_value in range(1, max_n + 1):
            left_orbits = left_table[left_value]
            if not left_orbits:
                continue
            for right_value in range(1, max_n // left_value + 1):
                right_orbits = right_table[right_value]
                if not right_orbits:
                    continue
                product = left_value * right_value
                relation_id = _commutative_relation_key(
                    left_value,
                    "*",
                    right_value,
                    product,
                )
                for left_pair in left_orbits:
                    for right_pair in right_orbits:
                        if unordered_sources and (
                            left_value,
                            left_pair,
                        ) > (
                            right_value,
                            right_pair,
                        ):
                            continue
                        output_pair = compose(left_pair, right_pair)
                        output_value = target_form.evaluate(*output_pair)
                        canonical_output = canonical_proper_orbit_representative(
                            target_form,
                            output_pair,
                        )
                        identity_holds = output_value == product
                        target_fibre_contains = canonical_output in by_target_orbit[
                            target_form.form_id
                        ][product]
                        total_events += 1
                        signature_counts[signature] = signature_counts.get(signature, 0) + 1
                        scalar_relation_ids.add(relation_id)
                        if not identity_holds:
                            identity_failures += 1
                        if not target_fibre_contains:
                            target_fibre_failures += 1
                        if len(records) < event_limit:
                            records.append(
                                {
                                    "event_id": total_events,
                                    "class_signature": signature,
                                    "left": {
                                        "form_id": left_form.form_id,
                                        "class_label": left_form.class_label,
                                        "value": left_value,
                                        "orbit_id": (
                                            f"{left_form.form_id}:{left_value}:"
                                            f"{left_pair[0]}:{left_pair[1]}"
                                        ),
                                        "representative_coordinates": list(left_pair),
                                    },
                                    "right": {
                                        "form_id": right_form.form_id,
                                        "class_label": right_form.class_label,
                                        "value": right_value,
                                        "orbit_id": (
                                            f"{right_form.form_id}:{right_value}:"
                                            f"{right_pair[0]}:{right_pair[1]}"
                                        ),
                                        "representative_coordinates": list(right_pair),
                                    },
                                    "result": {
                                        "form_id": target_form.form_id,
                                        "class_label": target_form.class_label,
                                        "value": output_value,
                                        "raw_coordinates": list(output_pair),
                                        "canonical_orbit_representative": list(
                                            canonical_output
                                        ),
                                        "orbit_id": (
                                            f"{target_form.form_id}:{product}:"
                                            f"{canonical_output[0]}:{canonical_output[1]}"
                                        ),
                                    },
                                    "bilinear_map_id": signature,
                                    "scalar_relation_id": relation_id,
                                    "identity_holds": identity_holds,
                                    "target_orbit_in_complete_fibre": (
                                        target_fibre_contains
                                    ),
                                    "reduction_provenance": {
                                        "method": (
                                            "direct_bilinear_landing_in_configured_"
                                            "reduced_form_then_proper_automorphism_"
                                            "orbit_normalization"
                                        ),
                                        "form_reduction_steps": [],
                                        "proper_automorphism_normalization": (
                                            "canonical lexicographic representative "
                                            "of the configured form's proper orbit"
                                        ),
                                        "general_gauss_composition_reduction_engine_used": (
                                            False
                                        ),
                                    },
                                    "modulus_one_projection": {
                                        "left_residue": 0,
                                        "right_residue": 0,
                                        "result_residue": 0,
                                    },
                                }
                            )

    raw_tables = {
        "principal": principal_representations,
        "nonprincipal": nonprincipal_representations,
    }

    def raw_ordered_count(left_label: str, right_label: str) -> int:
        left_table = raw_tables[left_label]
        right_table = raw_tables[right_label]
        return sum(
            len(left_table[left_value]) * len(right_table[right_value])
            for left_value in range(1, max_n + 1)
            for right_value in range(1, max_n // left_value + 1)
        )

    raw_signature_counts = {
        "principal*principal->principal": raw_ordered_count(
            "principal", "principal"
        ),
        "principal*nonprincipal->nonprincipal": raw_ordered_count(
            "principal", "nonprincipal"
        ),
        "nonprincipal*principal->nonprincipal": raw_ordered_count(
            "nonprincipal", "principal"
        ),
        "nonprincipal*nonprincipal->principal": raw_ordered_count(
            "nonprincipal", "nonprincipal"
        ),
    }

    return {
        "bound": int(max_n),
        "event_definition": (
            "proper-automorphism orbit representatives with product <= max_n; "
            "same-class source pairs are unordered and A*B fixes A on the left"
        ),
        "total_composition_events": total_events,
        "reported_events": records,
        "reported_event_count": len(records),
        "events_truncated": total_events > len(records),
        "event_limit": int(event_limit),
        "normalized_class_signature_counts": dict(sorted(signature_counts.items())),
        "commutative_class_signatures": [
            "principal*principal->principal",
            "principal*nonprincipal->nonprincipal",
            "nonprincipal*nonprincipal->principal",
        ],
        "distinct_scalar_multiplication_relations": len(scalar_relation_ids),
        "scalar_relation_ids": sorted(scalar_relation_ids),
        "identity_failure_count": identity_failures,
        "target_fibre_failure_count": target_fibre_failures,
        "all_normalized_events_verified_exactly": (
            identity_failures == 0 and target_fibre_failures == 0
        ),
        "complete_event_list_emitted": total_events <= event_limit,
        "raw_signed_witness_accounting": {
            "event_definition": (
                "all ordered signed-witness pairs for four oriented class signatures"
            ),
            "oriented_class_signature_counts": raw_signature_counts,
            "total_events": sum(raw_signature_counts.values()),
            "status": (
                "counted exactly from complete representation fibres; normalized "
                "orbit events are the primary emitted ledger"
            ),
        },
        "computation_status": (
            "all normalized bounded events were checked even if the emitted event "
            "list is truncated"
        ),
    }


def multiplicativity_report(
    coefficients: Mapping[int, int],
    *,
    max_n: int,
    defect_limit: int = 20,
) -> Dict[str, object]:
    bound = int(max_n)
    if bound < 1:
        raise ValueError("max_n must be >= 1")
    missing = [n for n in range(1, bound + 1) if n not in coefficients]
    if missing:
        raise ValueError(f"coefficient table is missing n={missing[0]}")

    defects: List[Dict[str, int]] = []
    checked = 0
    total_defects = 0
    for left in range(2, bound + 1):
        for right in range(left, bound // left + 1):
            if math.gcd(left, right) != 1:
                continue
            checked += 1
            product = left * right
            observed = int(coefficients[product])
            expected = int(coefficients[left]) * int(coefficients[right])
            if observed != expected:
                total_defects += 1
                if len(defects) < int(defect_limit):
                    defects.append(
                        {
                            "left": left,
                            "right": right,
                            "product": product,
                            "coefficient_left": int(coefficients[left]),
                            "coefficient_right": int(coefficients[right]),
                            "coefficient_product": observed,
                            "expected_product": expected,
                        }
                    )

    coefficient_at_one = int(coefficients[1])
    unit_passes = coefficient_at_one == 1
    return {
        "definition_tested": "a(1)=1 and a(m*n)=a(m)*a(n) when gcd(m,n)=1",
        "finite_bound": bound,
        "coefficient_at_one": coefficient_at_one,
        "unit_condition_passes": unit_passes,
        "checked_nontrivial_unordered_coprime_pairs": checked,
        "nontrivial_pair_defect_count": total_defects,
        "reported_defects": defects,
        "reported_defects_truncated": total_defects > len(defects),
        "passes_finite_test": unit_passes and total_defects == 0,
        "proof_status": "finite_exact_check_not_a_general_proof",
    }


def _form_report(
    form: BinaryQuadraticForm,
    representations: RepresentationTable,
) -> Dict[str, object]:
    coefficients = normalized_coefficients(form, representations)
    orbits = proper_orbit_representatives(form, representations)
    represented_values = [n for n, witnesses in representations.items() if witnesses]
    max_n = max(representations)
    max_abs_y = math.isqrt(
        (4 * form.a * max_n) // form.determinant_numerator
    )
    return {
        "form": form.payload(),
        "enumeration_method": {
            "status": "complete_exact_integer_enumeration_through_max_n",
            "identity": (
                "4aQ=(2ax+by)^2+(4ac-b^2)y^2"
            ),
            "max_n": max_n,
            "certified_max_abs_y": max_abs_y,
            "caller_coordinate_cutoff_used": False,
            "candidate_filter": "retain exactly 0 < Q(x,y) <= max_n",
        },
        "representation_ledger": representation_rows(form, representations),
        "proper_automorphism_orbit_ledger": [
            {
                "n": int(n),
                "orbit_count": len(orbits[n]),
                "orbit_representatives": [list(pair) for pair in orbits[n]],
            }
            for n in sorted(orbits)
        ],
        "proper_automorphism_normalization": {
            "group_order_for_configured_form": form.automorphism_normalization,
            "raw_witnesses_partition_exactly": True,
            "normalized_coefficients_equal_orbit_counts": all(
                coefficients[n] == len(orbits[n]) for n in orbits
            ),
        },
        "summary": {
            "max_n": max_n,
            "represented_value_count": len(represented_values),
            "hole_count": len(representations) - len(represented_values),
            "total_integer_pair_witnesses": sum(
                len(witnesses) for witnesses in representations.values()
            ),
            "total_proper_automorphism_orbits": sum(
                len(representatives) for representatives in orbits.values()
            ),
        },
        "multiplicativity": multiplicativity_report(
            coefficients,
            max_n=max(representations),
        ),
    }


def _d4_algebra_payload() -> Dict[str, object]:
    sample = (2, 3)
    first_turn = quarter_turn(sample)
    second_turn = quarter_turn(first_turn)
    left = (1, 1)
    right = (1, 2)
    product = gaussian_multiply(left, right)
    return {
        "quarter_turn_operator": {
            "definition": "J(x,y)=(-y,x)",
            "square_identity": "J(J(x,y))=(-x,-y)",
            "matrix_identity": "J^2=-I",
            "sample": {
                "input": list(sample),
                "J_input": list(first_turn),
                "J_squared_input": list(second_turn),
            },
            "norm_invariance_identity": "x^2+y^2 = (-y)^2+x^2",
            "sample_norm_preserved": gaussian_norm(sample)
            == gaussian_norm(first_turn),
            "representation_status": "exact_external_pair_operator_not_runtime_complex_scalar",
        },
        "gaussian_pair_multiplication": {
            "definition": "(x,y)*(u,v)=(x*u-y*v, x*v+y*u)",
            "norm_identity": (
                "Q((x,y)*(u,v))=(x^2+y^2)*(u^2+v^2)"
            ),
            "symbolic_expansion": (
                "(xu-yv)^2+(xv+yu)^2=(x^2+y^2)(u^2+v^2)"
            ),
            "sample": {
                "left": list(left),
                "right": list(right),
                "product": list(product),
                "left_norm": gaussian_norm(left),
                "right_norm": gaussian_norm(right),
                "product_norm": gaussian_norm(product),
                "identity_holds": gaussian_norm(product)
                == gaussian_norm(left) * gaussian_norm(right),
            },
            "representation_status": "exact_external_pair_algebra",
        },
    }


def _d20_composition_payload() -> Dict[str, object]:
    bb_left = (1, 0)
    bb_right = (0, 1)
    bb_result = d20_nonprincipal_nonprincipal(bb_left, bb_right)
    aa_left = (1, 1)
    aa_right = (2, 1)
    aa_result = d20_principal_principal(aa_left, aa_right)
    ab_result = d20_principal_nonprincipal(aa_left, bb_left)
    return {
        "class_labels": ["principal", "nonprincipal"],
        "composition_table": {
            "principal*principal": "principal",
            "principal*nonprincipal": "nonprincipal",
            "nonprincipal*nonprincipal": "principal",
        },
        "exact_bilinear_identities": [
            {
                "classes": "principal*principal->principal",
                "coordinate_map": "X=xu-5yv; Y=xv+yu",
                "identity": "A(x,y)A(u,v)=A(X,Y)",
                "sample_holds": (
                    D20_PRINCIPAL.evaluate(*aa_left)
                    * D20_PRINCIPAL.evaluate(*aa_right)
                    == D20_PRINCIPAL.evaluate(*aa_result)
                ),
            },
            {
                "classes": "principal*nonprincipal->nonprincipal",
                "coordinate_map": "U=xu-yu-3yv; V=xv+2yu+yv",
                "identity": "A(x,y)B(u,v)=B(U,V)",
                "sample_holds": (
                    D20_PRINCIPAL.evaluate(*aa_left)
                    * D20_NONPRINCIPAL.evaluate(*bb_left)
                    == D20_NONPRINCIPAL.evaluate(*ab_result)
                ),
            },
            {
                "classes": "nonprincipal*nonprincipal->principal",
                "coordinate_map": (
                    "X=2xu+xv+yu-2yv; Y=xv+yu+yv"
                ),
                "identity": "B(x,y)B(u,v)=A(X,Y)",
                "sample": {
                    "left": list(bb_left),
                    "right": list(bb_right),
                    "left_value": D20_NONPRINCIPAL.evaluate(*bb_left),
                    "right_value": D20_NONPRINCIPAL.evaluate(*bb_right),
                    "result": list(bb_result),
                    "result_value": D20_PRINCIPAL.evaluate(*bb_result),
                },
                "sample_holds": (
                    D20_NONPRINCIPAL.evaluate(*bb_left)
                    * D20_NONPRINCIPAL.evaluate(*bb_right)
                    == D20_PRINCIPAL.evaluate(*bb_result)
                ),
            },
        ],
        "norm_derivation": {
            "quadratic_ring_symbol": "r with r^2=-5",
            "principal_form": "A(x,y)=Norm(x+y*r)",
            "nonprincipal_form": (
                "B(x,y)=Norm(2*x+(1+r)*y)/2"
            ),
            "explanation": (
                "multiplying the displayed ring expressions and collecting the "
                "real and r coefficients gives the three bilinear coordinate maps"
            ),
            "runtime_status": "external_exact_derivation_not_a_graph_ring_object",
        },
        "status": (
            "the displayed polynomial identities are exact; identifying these labels "
            "with proper ideal classes uses the classical form-class correspondence"
        ),
    }


def _d4_family(max_n: int) -> Tuple[Dict[str, object], RepresentationTable]:
    representations = enumerate_representations(D4_PRINCIPAL, max_n)
    reduced = reduced_primitive_forms(-4)
    report = {
        "family_id": "discriminant_minus_4_control",
        "discriminant": -4,
        "standard_reduced_primitive_forms": [list(item) for item in reduced],
        "configured_forms_match_enumeration": reduced == ((1, 0, 1),),
        "form_reports": [_form_report(D4_PRINCIPAL, representations)],
        "exact_pair_algebra": _d4_algebra_payload(),
        "series_bridge": {
            "theta_coefficient_identity": (
                "Theta_Q(t)=1+sum_{n>=1} r_Q(n)*exp(-pi*t*n)"
            ),
            "epstein_coefficient_identity": (
                "E_Q(s)=sum_{n>=1} r_Q(n)*n^(-s)"
            ),
            "normalization_here": "r_Q(n)=4*a_Q(n)",
            "analytic_evaluation_performed": False,
        },
    }
    return report, representations


def _d20_family(
    max_n: int,
    *,
    composition_event_limit: int,
) -> Tuple[Dict[str, object], RepresentationTable, RepresentationTable]:
    principal_reps = enumerate_representations(D20_PRINCIPAL, max_n)
    nonprincipal_reps = enumerate_representations(D20_NONPRINCIPAL, max_n)
    principal = normalized_coefficients(D20_PRINCIPAL, principal_reps)
    nonprincipal = normalized_coefficients(D20_NONPRINCIPAL, nonprincipal_reps)
    plus = {n: principal[n] + nonprincipal[n] for n in range(1, max_n + 1)}
    minus = {n: principal[n] - nonprincipal[n] for n in range(1, max_n + 1)}
    placebo = {
        n: principal[n] + 2 * nonprincipal[n]
        for n in range(1, max_n + 1)
    }
    transform_rows = [
        {
            "n": n,
            "principal_coefficient": principal[n],
            "nonprincipal_coefficient": nonprincipal[n],
            "trivial_character_channel": plus[n],
            "sign_character_channel": minus[n],
        }
        for n in range(1, max_n + 1)
    ]
    reduced = reduced_primitive_forms(-20)
    configured = tuple(
        sorted(
            (
                (D20_PRINCIPAL.a, D20_PRINCIPAL.b, D20_PRINCIPAL.c),
                (
                    D20_NONPRINCIPAL.a,
                    D20_NONPRINCIPAL.b,
                    D20_NONPRINCIPAL.c,
                ),
            )
        )
    )
    report = {
        "family_id": "discriminant_minus_20_two_class_control",
        "discriminant": -20,
        "gauss_determinant": -5,
        "notation_bridge": {
            "gauss": "(a,b,c)_G means a*x^2+2*b*x*y+c*y^2; d_G=b^2-a*c",
            "modern": "[a,B,c] means a*x^2+B*x*y+c*y^2; Delta=B^2-4*a*c",
            "relation": "B=2*b and Delta=4*d_G",
            "configured_representatives": {
                "principal": "(1,0,5)_G=[1,0,5]",
                "nonprincipal": "(2,1,3)_G=[2,2,3]",
            },
        },
        "standard_reduced_primitive_forms": [list(item) for item in reduced],
        "configured_forms_match_enumeration": reduced == configured,
        "class_group_model": {
            "finite_group": "C2",
            "basis": ["principal", "nonprincipal"],
            "character_table": {
                "trivial": {"principal": 1, "nonprincipal": 1},
                "sign": {"principal": 1, "nonprincipal": -1},
            },
            "external_phase_view": {
                "trivial_character_on_nonprincipal": {
                    "root_of_unity": "+1",
                    "Q_mod_Z_phase": "0",
                },
                "sign_character_on_nonprincipal": {
                    "root_of_unity": "-1",
                    "Q_mod_Z_phase": "1/2",
                },
                "status": "character-label view_not_graph_native_phase_construction",
            },
        },
        "form_reports": [
            _form_report(D20_PRINCIPAL, principal_reps),
            _form_report(D20_NONPRINCIPAL, nonprincipal_reps),
        ],
        "class_composition": _d20_composition_payload(),
        "bounded_composition_event_ledger": d20_composition_event_ledger(
            principal_reps,
            nonprincipal_reps,
            max_n=max_n,
            event_limit=composition_event_limit,
        ),
        "character_transform": {
            "forward": "a_plus=a_principal+a_nonprincipal; a_minus=a_principal-a_nonprincipal",
            "inverse": "a_principal=(a_plus+a_minus)/2; a_nonprincipal=(a_plus-a_minus)/2",
            "rows": transform_rows,
            "finite_multiplicativity": {
                "trivial_character_channel": multiplicativity_report(
                    plus,
                    max_n=max_n,
                ),
                "sign_character_channel": multiplicativity_report(
                    minus,
                    max_n=max_n,
                ),
                "noncharacter_weight_1_2_placebo": multiplicativity_report(
                    placebo,
                    max_n=max_n,
                ),
            },
            "interpretation": (
                "the finite C2 character transform diagonalizes the two class labels; "
                "the observed coefficient multiplicativity is checked exactly only through max_n"
            ),
        },
        "two_times_three_witness": {
            "scalar_identity": "2*3=6",
            "principal_coefficients": {
                "a(2)": principal[2] if max_n >= 2 else None,
                "a(3)": principal[3] if max_n >= 3 else None,
                "a(6)": principal[6] if max_n >= 6 else None,
            },
            "nonprincipal_coefficients": {
                "a(2)": nonprincipal[2] if max_n >= 2 else None,
                "a(3)": nonprincipal[3] if max_n >= 3 else None,
                "a(6)": nonprincipal[6] if max_n >= 6 else None,
            },
            "available": max_n >= 6,
            "meaning": (
                "B represents 2 and 3 while A represents their product 6; "
                "this is an exact instance of the B*B->A bilinear identity"
            ) if max_n >= 6 else "increase max_n to at least 6",
        },
    }
    return report, principal_reps, nonprincipal_reps


def _meta_value(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row is not None else None


class ScalarGraphInspector:
    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        latest_stage: Optional[int],
        edge_limit: int,
        stage_cutoff: Optional[int] = None,
    ) -> None:
        self.conn = conn
        self.latest_stage = latest_stage
        self.edge_limit = int(edge_limit)
        self.requested_stage_cutoff = (
            int(stage_cutoff) if stage_cutoff is not None else None
        )
        if latest_stage is None:
            self.stage_cutoff = self.requested_stage_cutoff
        elif self.requested_stage_cutoff is None:
            self.stage_cutoff = int(latest_stage)
        else:
            self.stage_cutoff = min(
                int(latest_stage),
                self.requested_stage_cutoff,
            )
        self._node_cache: Dict[int, Dict[str, object]] = {}
        self._relation_cache: Dict[str, Dict[str, object]] = {}

    def node(self, value: int) -> Dict[str, object]:
        cached = self._node_cache.get(int(value))
        if cached is not None:
            return cached
        row = node_for_key(self.conn, (int(value), 1))
        if row is None:
            payload = {
                "value": int(value),
                "present": False,
                "present_in_corpus": False,
                "present_at_stage_cutoff": False,
                "graph_stage_cutoff": self.stage_cutoff,
                "status_at_stage_cutoff": "absent_from_corpus",
                "confirmed_by_stage_cutoff": False,
                "full_corpus_lifecycle_status": None,
                "eventual_confirmed_stage": None,
                "operand_ready_at_latest_stage": False,
                "operand_ready_at_stage_cutoff": False,
            }
            self._node_cache[int(value)] = payload
            return payload
        first_stage = int(row["first_stage"])
        present_at_cutoff = bool(
            self.stage_cutoff is None or first_stage <= self.stage_cutoff
        )
        full_lifecycle_payload = node_payload(row)
        full_lifecycle_status = str(full_lifecycle_payload.pop("status"))
        eventual_confirmed_stage = full_lifecycle_payload.pop("confirmed_stage")
        confirmed = row["confirmed_stage"]
        confirmed_by_cutoff = bool(
            confirmed is not None
            and self.stage_cutoff is not None
            and int(confirmed) <= self.stage_cutoff
        )
        if not present_at_cutoff:
            status_at_cutoff = "not_yet_present_at_stage_cutoff"
        elif int(row["p"]) == 1 and int(row["q"]) == 1:
            status_at_cutoff = "certainty"
        elif confirmed_by_cutoff:
            status_at_cutoff = "confirmed_at_or_before_stage_cutoff"
        else:
            status_at_cutoff = "speculative_at_stage_cutoff"
        stage_params: Tuple[object, ...] = (int(row["node_id"]),)
        stage_clause = ""
        if self.stage_cutoff is not None:
            stage_clause = " AND stage <= ?"
            stage_params = (int(row["node_id"]), int(self.stage_cutoff))
        incoming = int(
            self.conn.execute(
                "SELECT COUNT(*) AS n FROM edges WHERE result_node_id = ?"
                + stage_clause,
                stage_params,
            ).fetchone()["n"]
        )
        if self.stage_cutoff is None:
            outgoing_query = (
                "SELECT COUNT(*) AS n FROM edges "
                "WHERE left_node_id = ? OR right_node_id = ?"
            )
            outgoing_params: Tuple[object, ...] = (
                int(row["node_id"]),
                int(row["node_id"]),
            )
        else:
            outgoing_query = (
                "SELECT COUNT(*) AS n FROM edges "
                "WHERE (left_node_id = ? OR right_node_id = ?) AND stage <= ?"
            )
            outgoing_params = (
                int(row["node_id"]),
                int(row["node_id"]),
                int(self.stage_cutoff),
            )
        outgoing = int(
            self.conn.execute(outgoing_query, outgoing_params).fetchone()["n"]
        )
        result = {
            "value": int(value),
            "present": present_at_cutoff,
            "present_in_corpus": True,
            "present_at_stage_cutoff": present_at_cutoff,
            "graph_stage_cutoff": self.stage_cutoff,
            **full_lifecycle_payload,
            "status_at_stage_cutoff": status_at_cutoff,
            "confirmed_by_stage_cutoff": confirmed_by_cutoff,
            "full_corpus_lifecycle_status": full_lifecycle_status,
            "eventual_confirmed_stage": eventual_confirmed_stage,
            "incoming_edge_count": incoming,
            "outgoing_edge_count": outgoing,
            "operand_ready_at_latest_stage": bool(
                confirmed is not None
                and self.latest_stage is not None
                and int(confirmed) <= self.latest_stage
            ),
            "operand_ready_at_stage_cutoff": bool(
                confirmed_by_cutoff
            ),
        }
        self._node_cache[int(value)] = result
        return result

    def relation(
        self,
        left: int,
        op: str,
        right: int,
        result: int,
    ) -> Dict[str, object]:
        commutative = op in {"+", "*"}
        relation_id = _relation_id(int(left), str(op), int(right), int(result))
        cached = self._relation_cache.get(relation_id)
        if cached is not None:
            return cached
        params: List[object] = [str(op), int(result)]
        stage_clause = ""
        if self.stage_cutoff is not None:
            stage_clause = "AND e.stage <= ?"
            params.append(int(self.stage_cutoff))
        predicate = "(l.p = ? AND r.p = ?)"
        params.extend((int(left), int(right)))
        if commutative and left != right:
            predicate = "((l.p = ? AND r.p = ?) OR (l.p = ? AND r.p = ?))"
            params.extend((int(right), int(left)))
        query = f"""
            SELECT e.edge_id, e.stage, e.op,
                   l.p AS left_p, l.q AS left_q,
                   l.confirmed_stage AS left_eventual_confirmed_stage,
                   r.p AS right_p, r.q AS right_q,
                   r.confirmed_stage AS right_eventual_confirmed_stage,
                   z.p AS result_p, z.q AS result_q,
                   z.confirmed_stage AS result_eventual_confirmed_stage
            FROM edges e
            JOIN nodes l ON l.node_id = e.left_node_id
            JOIN nodes r ON r.node_id = e.right_node_id
            JOIN nodes z ON z.node_id = e.result_node_id
            WHERE e.op = ? AND z.p = ? AND z.q = 1
              {stage_clause}
              AND l.q = 1 AND r.q = 1 AND {predicate}
            ORDER BY e.stage, e.edge_id
        """
        rows = self.conn.execute(query, params).fetchall()
        ordered_rows = [
            row
            for row in rows
            if int(row["left_p"]) == int(left)
            and int(row["right_p"]) == int(right)
        ]
        shown = rows[: self.edge_limit]
        payload = {
            "relation_id": relation_id,
            "commutative_normalized_key": _commutative_relation_key(
                int(left),
                str(op),
                int(right),
                int(result),
            ),
            "relation": f"{left}{op}{right}={result}",
            "present": bool(rows),
            "graph_stage_cutoff": self.stage_cutoff,
            "directed_occurrence_count": len(rows),
            "directed_edge_ids": [int(row["edge_id"]) for row in rows],
            "ordered_direction_present": bool(ordered_rows),
            "ordered_directed_occurrence_count": len(ordered_rows),
            "ordered_directed_edge_ids": [
                int(row["edge_id"]) for row in ordered_rows
            ],
            "minimum_evidence_stage": (
                min(int(row["stage"]) for row in rows) if rows else None
            ),
            "maximum_evidence_stage": (
                max(int(row["stage"]) for row in rows) if rows else None
            ),
            "operand_confirmation_at_edge_passes": bool(rows) and all(
                row["left_eventual_confirmed_stage"] is not None
                and int(row["left_eventual_confirmed_stage"]) <= int(row["stage"])
                and row["right_eventual_confirmed_stage"] is not None
                and int(row["right_eventual_confirmed_stage"]) <= int(row["stage"])
                for row in rows
            ),
            "ordered_operand_confirmation_at_edge_passes": bool(
                ordered_rows
            ) and all(
                row["left_eventual_confirmed_stage"] is not None
                and int(row["left_eventual_confirmed_stage"]) <= int(row["stage"])
                and row["right_eventual_confirmed_stage"] is not None
                and int(row["right_eventual_confirmed_stage"]) <= int(row["stage"])
                for row in ordered_rows
            ),
            "result_status_at_edge_counts": {
                "grounded": sum(
                    row["result_eventual_confirmed_stage"] is not None
                    and int(row["result_eventual_confirmed_stage"]) <= int(row["stage"])
                    for row in rows
                ),
                "speculative": sum(
                    row["result_eventual_confirmed_stage"] is None
                    or int(row["result_eventual_confirmed_stage"]) > int(row["stage"])
                    for row in rows
                ),
            },
            "rows": [dict(row) for row in shown],
            "rows_truncated": len(rows) > len(shown),
            "edge_limit": self.edge_limit,
        }
        self._relation_cache[relation_id] = payload
        return payload


def _corpus_payload(
    conn: sqlite3.Connection,
    *,
    alignment: Dict[str, object],
) -> Dict[str, object]:
    config_raw = _meta_value(conn, "config_json")
    try:
        config: object = json.loads(config_raw) if config_raw is not None else None
    except json.JSONDecodeError:
        config = config_raw
    latest = conn.execute(
        "SELECT * FROM stages ORDER BY stage DESC LIMIT 1"
    ).fetchone()
    return {
        "schema_version": _meta_value(conn, "schema_version"),
        "config": config,
        "latest_stage": dict(latest) if latest is not None else None,
        "nodes": int(conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()["n"]),
        "edges": int(conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()["n"]),
        "alignment": alignment,
    }


def _relation_evidence_catalog(
    inspector: ScalarGraphInspector,
    relation_ids: Sequence[str],
) -> Tuple[List[Dict[str, object]], Dict[str, Dict[str, object]]]:
    rows: List[Dict[str, object]] = []
    by_id: Dict[str, Dict[str, object]] = {}
    for relation_id in sorted(set(str(item) for item in relation_ids)):
        left, op, right, result = _relation_spec_from_id(relation_id)
        evidence = inspector.relation(left, op, right, result)
        row = {
            "relation_id": relation_id,
            "left": left,
            "op": op,
            "right": right,
            "result": result,
            "graph_evidence": evidence,
        }
        rows.append(row)
        by_id[relation_id] = row
    return rows, by_id


def _relation_shadow_usable(
    relation_row: Mapping[str, object],
    *,
    require_ordered_direction: bool,
) -> bool:
    evidence = relation_row["graph_evidence"]  # type: ignore[index]
    if not bool(evidence["present"]):  # type: ignore[index]
        return False
    if not bool(evidence["operand_confirmation_at_edge_passes"]):  # type: ignore[index]
        return False
    if require_ordered_direction:
        return bool(evidence["ordered_direction_present"]) and bool(  # type: ignore[index]
            evidence["ordered_operand_confirmation_at_edge_passes"]  # type: ignore[index]
        )
    return True


def _normalized_relation_keys(relation_ids: Sequence[str]) -> set[str]:
    keys: set[str] = set()
    for relation_id in relation_ids:
        left, op, right, result = _relation_spec_from_id(relation_id)
        keys.add(_commutative_relation_key(left, op, right, result))
    return keys


def _directed_edge_ids(
    relation_ids: Sequence[str],
    relation_by_id: Mapping[str, Mapping[str, object]],
) -> set[int]:
    return {
        int(edge_id)
        for relation_id in relation_ids
        for edge_id in relation_by_id[relation_id]["graph_evidence"][  # type: ignore[index]
            "directed_edge_ids"
        ]
    }


def _evaluation_path_audit(
    inspector: ScalarGraphInspector,
    *,
    form_representations: Mapping[str, RepresentationTable],
) -> Dict[str, object]:
    forms = {
        D4_PRINCIPAL.form_id: D4_PRINCIPAL,
        D20_PRINCIPAL.form_id: D20_PRINCIPAL,
        D20_NONPRINCIPAL.form_id: D20_NONPRINCIPAL,
    }
    plans_by_form: Dict[str, List[Dict[str, object]]] = {}
    relation_ids_by_form: Dict[str, set[str]] = {}
    evaluation_relation_ids_by_form: Dict[str, set[str]] = {}
    coordinate_relation_ids_by_form: Dict[str, set[str]] = {}
    role_occurrences_by_form: Dict[str, Dict[str, int]] = {}
    operation_occurrences_by_form: Dict[str, Dict[str, int]] = {}

    for form_id, representations in form_representations.items():
        form = forms[form_id]
        plans: List[Dict[str, object]] = []
        relation_ids: set[str] = set()
        evaluation_ids: set[str] = set()
        coordinate_ids: set[str] = set()
        role_counts: Dict[str, int] = {}
        operation_counts: Dict[str, int] = {}
        witness_number = 0
        for value in sorted(representations):
            for x, y in representations[value]:
                witness_number += 1
                plan = positive_spine_evaluation_plan(form, x, y)
                if int(plan["represented_value"]) != int(value):
                    raise AssertionError(
                        f"evaluation plan value mismatch for {form_id} at {(x, y)}"
                    )
                plan["witness_id"] = f"{form_id}:{value}:{x}:{y}"
                for category, occurrences in (
                    ("evaluation", plan["formula_step_occurrences"]),
                    ("coordinate", plan["coordinate_relation_occurrences"]),
                ):
                    for step in occurrences:  # type: ignore[assignment]
                        relation_id = str(step["relation_id"])
                        role = str(step["role"])
                        op = str(step["op"])
                        relation_ids.add(relation_id)
                        role_counts[role] = role_counts.get(role, 0) + 1
                        operation_counts[op] = operation_counts.get(op, 0) + 1
                        if category == "coordinate":
                            coordinate_ids.add(relation_id)
                        else:
                            evaluation_ids.add(relation_id)
                plans.append(plan)
        plans_by_form[form_id] = plans
        relation_ids_by_form[form_id] = relation_ids
        evaluation_relation_ids_by_form[form_id] = evaluation_ids
        coordinate_relation_ids_by_form[form_id] = coordinate_ids
        role_occurrences_by_form[form_id] = role_counts
        operation_occurrences_by_form[form_id] = operation_counts

    all_relation_ids = sorted(
        set().union(*(ids for ids in relation_ids_by_form.values()))
    )
    relation_catalog, relation_by_id = _relation_evidence_catalog(
        inspector,
        all_relation_ids,
    )
    form_reports: Dict[str, object] = {}
    total_witnesses = 0
    total_arithmetic_complete = 0
    total_coordinate_complete = 0
    total_all_references_complete = 0
    total_occurrences = 0
    global_operation_counts: Dict[str, int] = {}
    global_role_counts: Dict[str, int] = {}

    for form_id, plans in plans_by_form.items():
        arithmetic_complete = 0
        coordinate_complete = 0
        all_references_complete = 0
        occurrence_count = 0
        for plan in plans:
            unusable_formula = [
                relation_id
                for relation_id in plan["distinct_formula_relation_ids"]  # type: ignore[assignment]
                if not _relation_shadow_usable(
                    relation_by_id[str(relation_id)],
                    require_ordered_direction=True,
                )
            ]
            unusable_coordinate = [
                relation_id
                for relation_id in plan["distinct_coordinate_relation_ids"]  # type: ignore[assignment]
                if not _relation_shadow_usable(
                    relation_by_id[str(relation_id)],
                    require_ordered_direction=True,
                )
            ]
            value_node = inspector.node(int(plan["represented_value"]))
            plan["unusable_formula_relation_ids"] = unusable_formula
            plan["unusable_coordinate_relation_ids"] = unusable_coordinate
            plan["unusable_relation_ids"] = sorted(
                set(unusable_formula) | set(unusable_coordinate)
            )
            plan["represented_value_node_present"] = bool(value_node["present"])
            plan["positive_spine_arithmetic_dag_complete"] = (
                not unusable_formula and bool(value_node["present"])
            )
            plan["coordinate_side_ledger_complete"] = not unusable_coordinate
            plan["all_scalar_references_complete"] = bool(
                plan["positive_spine_arithmetic_dag_complete"]
                and plan["coordinate_side_ledger_complete"]
            )
            plan["graph_native_representation_edge"] = False
            if plan["positive_spine_arithmetic_dag_complete"]:
                arithmetic_complete += 1
            if plan["coordinate_side_ledger_complete"]:
                coordinate_complete += 1
            if plan["all_scalar_references_complete"]:
                all_references_complete += 1
            occurrence_count += int(plan["relation_role_occurrence_count"])

        unusable_formula_distinct = sorted(
            relation_id
            for relation_id in evaluation_relation_ids_by_form[form_id]
            if not _relation_shadow_usable(
                relation_by_id[relation_id],
                require_ordered_direction=True,
            )
        )
        unusable_coordinate_distinct = sorted(
            relation_id
            for relation_id in coordinate_relation_ids_by_form[form_id]
            if not _relation_shadow_usable(
                relation_by_id[relation_id],
                require_ordered_direction=True,
            )
        )
        stages = [
            relation_by_id[relation_id]["graph_evidence"]["maximum_evidence_stage"]  # type: ignore[index]
            for relation_id in relation_ids_by_form[form_id]
            if relation_by_id[relation_id]["graph_evidence"]["maximum_evidence_stage"]  # type: ignore[index]
            is not None
        ]
        normalized_keys = _normalized_relation_keys(
            sorted(relation_ids_by_form[form_id])
        )
        directed_edge_ids = _directed_edge_ids(
            sorted(relation_ids_by_form[form_id]),
            relation_by_id,
        )
        coordinate_case_counts: Dict[str, int] = {}
        for plan in plans:
            coordinates = plan["coordinates"]
            linear = coordinates.get("absolute_x_plus_y")  # type: ignore[union-attr]
            if linear is None:
                continue
            construction = str(linear["construction"])
            if construction.startswith("zero-coordinate identity"):
                case = "zero_coordinate_alias_no_edge"
            elif construction == "same-sign magnitudes add":
                case = "same_sign_addition"
            elif construction == "opposite-sign magnitudes subtract":
                case = "opposite_sign_positive_subtraction"
            elif "cancel to zero" in construction:
                case = "opposite_equal_relational_zero"
            else:
                raise AssertionError(f"unknown coordinate rewrite case: {construction}")
            coordinate_case_counts[case] = coordinate_case_counts.get(case, 0) + 1

        zero_relation_ids = sorted(
            relation_id
            for relation_id in coordinate_relation_ids_by_form[form_id]
            if _relation_spec_from_id(relation_id)[3] == 0
        )
        zero_edge_ids = _directed_edge_ids(zero_relation_ids, relation_by_id)
        zero_grounded_edges = sum(
            int(
                relation_by_id[relation_id]["graph_evidence"][  # type: ignore[index]
                    "result_status_at_edge_counts"
                ]["grounded"]
            )
            for relation_id in zero_relation_ids
        )
        zero_speculative_edges = sum(
            int(
                relation_by_id[relation_id]["graph_evidence"][  # type: ignore[index]
                    "result_status_at_edge_counts"
                ]["speculative"]
            )
            for relation_id in zero_relation_ids
        )
        form_reports[form_id] = {
            "raw_witness_count": len(plans),
            "complete_positive_spine_arithmetic_dag_count": arithmetic_complete,
            "incomplete_positive_spine_arithmetic_dag_count": (
                len(plans) - arithmetic_complete
            ),
            "complete_coordinate_side_ledger_count": coordinate_complete,
            "incomplete_coordinate_side_ledger_count": (
                len(plans) - coordinate_complete
            ),
            "complete_all_scalar_references_count": all_references_complete,
            "incomplete_all_scalar_references_count": (
                len(plans) - all_references_complete
            ),
            "relation_role_occurrence_count": occurrence_count,
            "arithmetic_evaluation_step_occurrence_count": sum(
                int(plan["formula_step_occurrence_count"]) for plan in plans
            ),
            "coordinate_rewrite_relation_occurrence_count": sum(
                int(plan["coordinate_relation_occurrence_count"]) for plan in plans
            ),
            "distinct_ordered_relation_id_count": len(
                relation_ids_by_form[form_id]
            ),
            "distinct_commutative_normalized_key_count": len(normalized_keys),
            "distinct_directed_graph_edge_id_count": len(directed_edge_ids),
            "distinct_arithmetic_evaluation_relation_count": len(
                evaluation_relation_ids_by_form[form_id]
            ),
            "distinct_coordinate_rewrite_relation_count": len(
                coordinate_relation_ids_by_form[form_id]
            ),
            "unusable_distinct_formula_relation_ids": unusable_formula_distinct,
            "unusable_distinct_coordinate_relation_ids": (
                unusable_coordinate_distinct
            ),
            "coordinate_rewrite_case_counts": dict(
                sorted(coordinate_case_counts.items())
            ),
            "relational_zero_side_ledger": {
                "applicable": bool(zero_relation_ids),
                "role_occurrence_count": coordinate_case_counts.get(
                    "opposite_equal_relational_zero", 0
                ),
                "distinct_ordered_relation_ids": zero_relation_ids,
                "distinct_ordered_relation_count": len(zero_relation_ids),
                "distinct_directed_graph_edge_ids": sorted(zero_edge_ids),
                "distinct_directed_graph_edge_count": len(zero_edge_ids),
                "all_edges_have_confirmed_operands": (
                    all(
                        _relation_shadow_usable(
                            relation_by_id[relation_id],
                            require_ordered_direction=True,
                        )
                        for relation_id in zero_relation_ids
                    )
                    if zero_relation_ids
                    else None
                ),
                "result_status_at_edge_counts": {
                    "grounded": zero_grounded_edges,
                    "speculative": zero_speculative_edges,
                },
                "zero_reused_as_operand": False,
            },
            "operation_occurrence_counts": dict(
                sorted(operation_occurrences_by_form[form_id].items())
            ),
            "role_occurrence_counts": dict(
                sorted(role_occurrences_by_form[form_id].items())
            ),
            "maximum_evidence_stage": max(stages) if stages else None,
            "witness_plans": plans,
        }
        total_witnesses += len(plans)
        total_arithmetic_complete += arithmetic_complete
        total_coordinate_complete += coordinate_complete
        total_all_references_complete += all_references_complete
        total_occurrences += occurrence_count
        for op, count in operation_occurrences_by_form[form_id].items():
            global_operation_counts[op] = global_operation_counts.get(op, 0) + count
        for role, count in role_occurrences_by_form[form_id].items():
            global_role_counts[role] = global_role_counts.get(role, 0) + count

    global_unusable = [
        row["relation_id"]
        for row in relation_catalog
        if not _relation_shadow_usable(
            row,
            require_ordered_direction=True,
        )
    ]
    global_stages = [
        row["graph_evidence"]["maximum_evidence_stage"]  # type: ignore[index]
        for row in relation_catalog
        if row["graph_evidence"]["maximum_evidence_stage"] is not None  # type: ignore[index]
    ]
    global_normalized_keys = _normalized_relation_keys(all_relation_ids)
    global_directed_edge_ids = _directed_edge_ids(
        all_relation_ids,
        relation_by_id,
    )
    return {
        "construction_method": (
            "positive-spine scalar DAGs; zero terms are omitted and signed "
            "coordinates remain external exact annotations"
        ),
        "graph_stage_cutoff": inspector.stage_cutoff,
        "positive_spine_arithmetic_dags_complete": (
            total_arithmetic_complete == total_witnesses
        ),
        "coordinate_side_ledgers_complete": (
            total_coordinate_complete == total_witnesses
        ),
        "all_scalar_references_complete": (
            total_all_references_complete == total_witnesses
        ),
        "graph_native_representation_edge": False,
        "raw_witness_count": total_witnesses,
        "complete_arithmetic_dag_count": total_arithmetic_complete,
        "incomplete_arithmetic_dag_count": (
            total_witnesses - total_arithmetic_complete
        ),
        "complete_coordinate_side_ledger_count": total_coordinate_complete,
        "incomplete_coordinate_side_ledger_count": (
            total_witnesses - total_coordinate_complete
        ),
        "complete_all_scalar_references_count": total_all_references_complete,
        "incomplete_all_scalar_references_count": (
            total_witnesses - total_all_references_complete
        ),
        "relation_role_occurrence_count": total_occurrences,
        "distinct_ordered_relation_id_count": len(all_relation_ids),
        "distinct_commutative_normalized_key_count": len(global_normalized_keys),
        "distinct_directed_graph_edge_id_count": len(global_directed_edge_ids),
        "unusable_distinct_relation_ids": global_unusable,
        "operation_occurrence_counts": dict(sorted(global_operation_counts.items())),
        "role_occurrence_counts": dict(sorted(global_role_counts.items())),
        "maximum_evidence_stage": max(global_stages) if global_stages else None,
        "relation_catalog": relation_catalog,
        "forms": form_reports,
        "interpretation": (
            "ordered relation-role references can repeat within one witness; "
            "commutative normalized keys and directed graph edge IDs are counted "
            "separately; coordinate-side completeness cannot change arithmetic-DAG "
            "completeness"
        ),
    }


def _composition_relation_graph_audit(
    inspector: ScalarGraphInspector,
    composition_ledger: Mapping[str, object],
) -> Dict[str, object]:
    relation_ids = [
        str(item) for item in composition_ledger["scalar_relation_ids"]  # type: ignore[index]
    ]
    catalog, _ = _relation_evidence_catalog(inspector, relation_ids)
    unusable = [
        str(row["relation_id"])
        for row in catalog
        if not _relation_shadow_usable(
            row,
            require_ordered_direction=False,
        )
    ]
    stages = [
        row["graph_evidence"]["maximum_evidence_stage"]  # type: ignore[index]
        for row in catalog
        if row["graph_evidence"]["maximum_evidence_stage"] is not None  # type: ignore[index]
    ]
    directed_edge_ids = {
        int(edge_id)
        for row in catalog
        for edge_id in row["graph_evidence"]["directed_edge_ids"]  # type: ignore[index]
    }
    directed_occurrences = sum(
        int(row["graph_evidence"]["directed_occurrence_count"])  # type: ignore[index]
        for row in catalog
    )
    return {
        "graph_stage_cutoff": inspector.stage_cutoff,
        "normalized_composition_event_count": int(
            composition_ledger["total_composition_events"]
        ),
        "distinct_commutative_scalar_relation_count": len(relation_ids),
        "usable_relations": len(relation_ids) - len(unusable),
        "unusable_relations": len(unusable),
        "unusable_relation_ids": unusable,
        "all_scalar_multiplication_shadows_usable": not unusable,
        "directed_graph_edge_occurrence_count": directed_occurrences,
        "distinct_directed_graph_edge_id_count": len(directed_edge_ids),
        "distinct_directed_graph_edge_ids": sorted(directed_edge_ids),
        "maximum_evidence_stage": max(stages) if stages else None,
        "relation_catalog": catalog,
        "interpretation": (
            "a scalar multiplication edge witnesses only m*n=mn; the form-class "
            "transition and bilinear coordinate map remain external decorations"
        ),
    }


def _graph_audit(
    inspector: ScalarGraphInspector,
    *,
    max_n: int,
    form_representations: Mapping[str, RepresentationTable],
    d20_composition_ledger: Mapping[str, object],
) -> Dict[str, object]:
    scalar_rows = [inspector.node(n) for n in range(1, max_n + 1)]
    present = sum(bool(row["present"]) for row in scalar_rows)
    coverage: Dict[str, object] = {}
    for form_id, representations in form_representations.items():
        represented = [n for n, witnesses in representations.items() if witnesses]
        represented_present = sum(
            bool(scalar_rows[n - 1]["present"])
            for n in represented
        )
        coverage[form_id] = {
            "represented_values": len(represented),
            "represented_values_with_scalar_graph_node": represented_present,
            "represented_values_missing_scalar_graph_node": (
                len(represented) - represented_present
            ),
        }

    named = [
        (D4_PRINCIPAL, 1, 1, 2),
        (D4_PRINCIPAL, 1, 2, 5),
        (D4_PRINCIPAL, 1, 3, 10),
        (D20_NONPRINCIPAL, 1, 0, 2),
        (D20_NONPRINCIPAL, 0, 1, 3),
        (D20_PRINCIPAL, 1, 1, 6),
    ]
    witness_rows = []
    for form, x, y, expected in named:
        actual = form.evaluate(x, y)
        witness_rows.append(
            {
                "form_id": form.form_id,
                "coordinates": {"x": x, "y": y},
                "value": actual,
                "expected_value": expected,
                "exact_identity_holds": actual == expected,
                "coordinate_nodes": {
                    "x": inspector.node(x),
                    "y": inspector.node(y),
                },
                "value_node": inspector.node(actual),
                "representation_edge_present": False,
                "representation_status": (
                    "external_form_witness_over_graph_scalar_nodes; "
                    "the corpus has no quadratic-form representation edge type"
                ),
            }
        )

    evaluation_paths = _evaluation_path_audit(
        inspector,
        form_representations=form_representations,
    )
    composition_relations = _composition_relation_graph_audit(
        inspector,
        d20_composition_ledger,
    )

    return {
        "stage_censoring": {
            "requested_stage_cutoff": inspector.requested_stage_cutoff,
            "effective_stage_cutoff": inspector.stage_cutoff,
            "corpus_latest_stage": inspector.latest_stage,
            "status": "all node and edge counts in this audit obey the effective cutoff",
        },
        "scalar_node_coverage": {
            "requested_values": max_n,
            "present_values": present,
            "missing_values": max_n - present,
            "rows": scalar_rows,
        },
        "represented_value_coverage_by_form": coverage,
        "named_external_representation_witnesses": witness_rows,
        "complete_positive_spine_evaluation_paths": evaluation_paths,
        "d20_composition_scalar_relation_audit": composition_relations,
        "selected_scalar_relations": {
            "d4_norm_multiplicativity_shadow": inspector.relation(2, "*", 5, 10),
            "d20_class_composition_shadow": inspector.relation(2, "*", 3, 6),
            "d20_principal_representation_scalar_path": inspector.relation(
                1,
                "+",
                5,
                6,
            ),
        },
        "neighborhood_queries": [
            "python3 moo_graph_query.py --db <same-corpus.sqlite> --node 6 --neighborhood --pretty",
            "python3 moo_graph_query.py --db <same-corpus.sqlite> --node 10 --neighborhood --pretty",
        ],
        "graph_native_quadratic_form_nodes": False,
        "graph_native_form_class_labels": False,
        "graph_native_class_character_transform": False,
        "saturation_control": {
            "expected_result": (
                "every exact in-range operation on confirmed positive operands is "
                "available in the strict positive-spine corpus"
            ),
            "evaluation_relation_coverage_is_selective_evidence": False,
            "composition_relation_coverage_is_selective_evidence": False,
            "meaning": (
                "complete scalar-shadow coverage calibrates the attachment; it does "
                "not show that the graph independently selects Gauss forms"
            ),
        },
        "interpretation": (
            "the strict graph supplies scalar nodes and selected construction edges; "
            "form evaluations, representation fibres, class labels, and character transforms "
            "remain exact external annotations"
        ),
    }


def _family_projection_metrics(
    forms: Sequence[BinaryQuadraticForm],
    representations: Mapping[str, RepresentationTable],
    evaluation_audit: Mapping[str, object],
) -> Dict[str, object]:
    value_sets = {
        form.form_id: {
            int(value)
            for value, witnesses in representations[form.form_id].items()
            if witnesses
        }
        for form in forms
    }
    all_values = set().union(*value_sets.values())
    raw_witnesses = sum(
        len(witnesses)
        for form in forms
        for witnesses in representations[form.form_id].values()
    )
    proper_orbits = sum(
        len(proper_orbit_representatives(form, representations[form.form_id])[value])
        for form in forms
        for value in representations[form.form_id]
    )
    path_forms = evaluation_audit["forms"]  # type: ignore[index]
    relation_occurrences = sum(
        int(path_forms[form.form_id]["relation_role_occurrence_count"])
        for form in forms
    )
    relation_ids = set()
    for form in forms:
        for plan in path_forms[form.form_id]["witness_plans"]:
            relation_ids.update(str(item) for item in plan["distinct_relation_ids"])
    normalized_keys = _normalized_relation_keys(sorted(relation_ids))
    catalog_by_id = {
        str(row["relation_id"]): row
        for row in evaluation_audit["relation_catalog"]  # type: ignore[index]
    }
    directed_edge_ids = _directed_edge_ids(
        sorted(relation_ids),
        catalog_by_id,
    )
    pairwise_overlaps = []
    for index, left in enumerate(forms):
        for right in forms[index + 1 :]:
            overlap = sorted(value_sets[left.form_id] & value_sets[right.form_id])
            pairwise_overlaps.append(
                {
                    "left_form_id": left.form_id,
                    "right_form_id": right.form_id,
                    "overlap_count": len(overlap),
                    "overlap_values": overlap,
                }
            )
    return {
        "form_ids": [form.form_id for form in forms],
        "class_labels": sorted(set(form.class_label for form in forms)),
        "raw_integer_pair_witnesses": raw_witnesses,
        "proper_automorphism_orbits": proper_orbits,
        "form_value_memberships": sum(len(values) for values in value_sets.values()),
        "distinct_represented_integers": len(all_values),
        "represented_integer_values": sorted(all_values),
        "pairwise_form_value_overlaps": pairwise_overlaps,
        "strict_scalar_relation_role_occurrences": relation_occurrences,
        "distinct_ordered_strict_scalar_relation_id_count": len(relation_ids),
        "distinct_commutative_normalized_relation_key_count": len(normalized_keys),
        "distinct_directed_graph_edge_id_count": len(directed_edge_ids),
        "occupied_modulus_one_residues": [0] if all_values else [],
        "occupied_modulus_one_residue_count": 1 if all_values else 0,
        "projection_chain": (
            f"{raw_witnesses} raw witnesses -> {proper_orbits} proper-automorphism "
            f"orbits -> {len(all_values)} represented integers -> "
            f"{1 if all_values else 0} residue"
        ),
    }


def _modulus_one_projection(
    *,
    max_n: int,
    d4_representations: RepresentationTable,
    d20_principal_representations: RepresentationTable,
    d20_nonprincipal_representations: RepresentationTable,
    graph_audit: Mapping[str, object],
) -> Dict[str, object]:
    evaluation_audit = graph_audit["complete_positive_spine_evaluation_paths"]  # type: ignore[index]
    representations = {
        D4_PRINCIPAL.form_id: d4_representations,
        D20_PRINCIPAL.form_id: d20_principal_representations,
        D20_NONPRINCIPAL.form_id: d20_nonprincipal_representations,
    }
    d4_metrics = _family_projection_metrics(
        (D4_PRINCIPAL,),
        representations,
        evaluation_audit,
    )
    d20_metrics = _family_projection_metrics(
        (D20_PRINCIPAL, D20_NONPRINCIPAL),
        representations,
        evaluation_audit,
    )
    named_available = max_n >= 6
    class_transition: Dict[str, object] = {
        "available": named_available,
        "identity": "B(1,0)*B(0,1)=2*3=6=A(1,1)",
        "class_transition": "nonprincipal*nonprincipal->principal",
        "integer_values": {"left": 2, "right": 3, "result": 6},
        "modulus_one_values": {"left": 0, "right": 0, "result": 0},
        "bare_quotient_identity": "0*0=0",
        "survival_status": (
            "class transition survives only as retained provenance decoration"
        ),
    }
    if named_available:
        class_transition["strict_graph_scalar_relation"] = graph_audit[
            "selected_scalar_relations"
        ]["d20_class_composition_shadow"]  # type: ignore[index]

    bare_signature = {
        "residue_nodes": [0],
        "algebraic_signature": "ring operations {+, -, *}",
        "operator_labelled_self_loops": ["0+0=0", "0-0=0", "0*0=0"],
        "division_excluded": True,
        "division_exclusion_reason": (
            "division is not a total operation on Z/1Z because its only "
            "putative denominator is 0; 0/0 is undefined"
        ),
        "operation_erased_topology": "one node with one self-loop",
    }
    return {
        "name": "integer_values_modulo_one",
        "domain_and_codomain": (
            "decorated quadratic-form witnesses -> positive represented integers "
            "-> the singleton quotient Z/1Z"
        ),
        "map": "rho_1(n)=n mod 1=0 for every integer n",
        "primary_projection_scope": (
            "only the represented integer is quotiented; form, class, coordinate, "
            "composition, and graph references are retained solely as fibre decorations"
        ),
        "two_stage_metrics": {
            "discriminant_minus_4_one_class_control": d4_metrics,
            "gauss_determinant_minus_5_modern_discriminant_minus_20": d20_metrics,
        },
        "central_class_composition_witness": class_transition,
        "singleton_residue_fibre": {
            "residue": 0,
            "d4_decorated_preimage_size_raw_witnesses": d4_metrics[
                "raw_integer_pair_witnesses"
            ],
            "d20_decorated_preimage_size_raw_witnesses": d20_metrics[
                "raw_integer_pair_witnesses"
            ],
            "interpretation": (
                "the fibre can be richly decorated even though the quotient has no "
                "nontrivial scalar distinction"
            ),
        },
        "bare_modulus_one_topology": bare_signature,
        "constant_bucket_control": {
            "control_map": "replace every represented integer by one arbitrary token",
            "bare_signature": bare_signature,
            "matches_modulus_one_bare_signature": True,
            "meaning": (
                "any surviving distinction comes from retained decorations, not from "
                "the residue arithmetic"
            ),
        },
        "one_class_vs_two_class_control": {
            "bare_topologies_identical": True,
            "d4_retained_class_labels": ["principal"],
            "d20_retained_class_labels": ["principal", "nonprincipal"],
            "meaning": (
                "class number changes the decorated preimage, never the singleton "
                "residue topology"
            ),
        },
        "coefficientwise_erasure_audit": {
            "example": (
                "[2,2,3], (1,0), Delta=-20, and Q=2 all project "
                "coordinatewise to zero"
            ),
            "status": "exact_integer_projection_illustration",
            "guardrail": (
                "this is not asserted to be a developed theory of binary quadratic "
                "forms over the zero ring"
            ),
        },
        "phase_separation_guardrail": {
            "integer_modulus_one": "n in Z maps to 0 in Z/1Z",
            "auxiliary_class_character_phase": (
                "the sign character value -1 may be labelled by 1/2 in Q/Z"
            ),
            "same_construction": False,
        },
        "candidate": (
            "Gauss composition supplies a nontrivial provenance channel inside the "
            "singleton fibre"
        ),
        "falsifier": (
            "strip form labels and bilinear witnesses; no class distinction may remain "
            "in the scalar graph or bare modulus-one quotient"
        ),
    }


def _gauss_source_map() -> Dict[str, object]:
    return {
        "primary_work": "Gauss, Disquisitiones Arithmeticae, Section V",
        "article_map": {
            "153-154": "form notation, representation, and determinant",
            "157-159": "transformations, proper equivalence, and opposite forms",
            "171-176": "reduction and enumeration for negative determinant",
            "223-226": "fixed-determinant classes and primitive conventions",
            "231": "principal form and principal class",
            "234-244": "composition construction and its laws",
            "249": "composition of classes and inverse/opposite classes",
        },
        "historical_minimality": (
            "d_G=-5 is the first clean Gauss-convention case with two positive "
            "properly primitive classes in the same order; this is not the modern "
            "claim that Delta=-20 is the first nontrivial primitive class group"
        ),
        "source_urls": {
            "first_edition_scan": (
                "https://www.e-rara.ch/zut/content/structure/1254642"
            ),
            "springer_english_section_v": (
                "https://link.springer.com/chapter/10.1007/978-1-4939-7560-0_5"
            ),
            "timorin_article_235_reconstruction": (
                "https://arxiv.org/html/1309.4879v3"
            ),
        },
        "status": (
            "article references are historical anchors; computations in this report "
            "use explicit modern integer formulas"
        ),
    }


def _claim_boundary() -> Dict[str, object]:
    return {
        "evidence_layer": "exact_external_quadratic_form_analysis_over_strict_graph",
        "claim_status": "finite_exact_algebraic_probe_not_analytic_proof",
        "allowed_claim_language": [
            "The probe exhaustively enumerates integer-pair witnesses for the named positive-definite forms through max_n using an exact completed-square bound.",
            "The displayed D=-4 norm and D=-20 bilinear composition identities are exact polynomial identities.",
            "The D=-20 principal coefficient ledger has the displayed finite multiplicativity defect, while its two C2 character channels pass the same finite test through max_n when reported as passing.",
            "Selected scalar nodes and multiplication edges are audited against the strict graph independently of the external form labels.",
            "Modulo one, every represented integer occupies the sole residue 0; any retained form-class distinction is provenance in that singleton fibre.",
        ],
        "disallowed_claim_language": [
            "Do not claim that the strict graph contains binary quadratic forms, Gaussian integers, ideal classes, Hecke characters, theta functions, or Epstein zeta functions as runtime objects.",
            "Do not treat scalar node presence or a scalar multiplication edge as a graph-native representation or form-composition edge.",
            "Do not infer an infinite Euler product from a finite multiplicativity check.",
            "Do not infer analytic continuation, a functional equation, zero locations, or the Riemann hypothesis from these coefficient ledgers.",
            "Do not infer a general class-group theorem solely from the two configured discriminants.",
            "Do not identify the nontrivial C2 character phase 1/2 in Q/Z with reduction of integer values modulo one.",
            "Do not describe the retained decorated fibre as nontrivial arithmetic internal to Z/1Z.",
            "Do not treat complete in-range scalar-edge coverage as selective evidence for quadratic forms; saturation is expected from the strict positive spine.",
        ],
        "interpretation_limits": [
            "The standard reduced-form enumeration is exact, but identifying reduced forms with proper equivalence classes uses the classical reduction theorem.",
            "The class-character names use the classical form-ideal-class correspondence; the probe itself computes representation counts and a finite C2 linear transform.",
            "Theta and Epstein series are recorded only as coefficient bridges and are not numerically evaluated here.",
            "Positive theta coefficients, self-duality, or a Riemann-like functional equation would not by themselves force critical-line zeros.",
        ],
    }


def _analytic_boundary() -> Dict[str, object]:
    return {
        "exact_positive_index_theta_coefficient_prefix": True,
        "theta_constant_term_included": False,
        "infinite_theta_series_evaluated": False,
        "epstein_zeta_evaluated": False,
        "analytic_continuation_used": False,
        "functional_equation_used": False,
        "euler_product_proved_by_probe": False,
        "zero_computation_performed": False,
        "riemann_hypothesis_claim": False,
    }


def _validate_limits(
    *,
    max_n: int,
    edge_limit: int,
    composition_event_limit: int,
    graph_stage_cutoff: Optional[int],
    full_scan: bool,
) -> None:
    if int(max_n) < 1:
        raise ValueError("max_n must be >= 1")
    if int(max_n) > HARD_MAX_N:
        raise ValueError(f"max_n>{HARD_MAX_N} exceeds the hard report-size limit")
    if int(edge_limit) < 1:
        raise ValueError("edge_limit must be >= 1")
    if int(composition_event_limit) < 1:
        raise ValueError("composition_event_limit must be >= 1")
    if graph_stage_cutoff is not None and int(graph_stage_cutoff) < 1:
        raise ValueError("graph_stage_cutoff must be >= 1")
    if int(max_n) > SOFT_MAX_N and not full_scan:
        raise ValueError(
            f"max_n>{SOFT_MAX_N} exceeds the normal probe limit; "
            "pass --full-scan to acknowledge the larger exact report"
        )


def quadratic_form_probe(
    *,
    db_path: Path,
    max_n: int = DEFAULT_MAX_N,
    edge_limit: int = DEFAULT_EDGE_LIMIT,
    composition_event_limit: int = DEFAULT_COMPOSITION_EVENT_LIMIT,
    graph_stage_cutoff: Optional[int] = None,
    full_scan: bool = False,
) -> Dict[str, object]:
    _validate_limits(
        max_n=int(max_n),
        edge_limit=int(edge_limit),
        composition_event_limit=int(composition_event_limit),
        graph_stage_cutoff=(
            int(graph_stage_cutoff) if graph_stage_cutoff is not None else None
        ),
        full_scan=bool(full_scan),
    )
    bound = int(max_n)
    requested_graph_stage_cutoff = (
        int(graph_stage_cutoff) if graph_stage_cutoff is not None else bound
    )
    d4, d4_reps = _d4_family(bound)
    d20, d20_principal_reps, d20_nonprincipal_reps = _d20_family(
        bound,
        composition_event_limit=int(composition_event_limit),
    )
    d20_composition_ledger = d20["bounded_composition_event_ledger"]

    with closing(connect_readonly(Path(db_path))) as conn:
        alignment = require_strict_alignment(conn)
        corpus = _corpus_payload(conn, alignment=alignment)
        latest = corpus["latest_stage"]
        latest_stage = int(latest["stage"]) if isinstance(latest, dict) else None
        inspector = ScalarGraphInspector(
            conn,
            latest_stage=latest_stage,
            edge_limit=int(edge_limit),
            stage_cutoff=requested_graph_stage_cutoff,
        )
        graph_audit = _graph_audit(
            inspector,
            max_n=bound,
            form_representations={
                D4_PRINCIPAL.form_id: d4_reps,
                D20_PRINCIPAL.form_id: d20_principal_reps,
                D20_NONPRINCIPAL.form_id: d20_nonprincipal_reps,
            },
            d20_composition_ledger=d20_composition_ledger,  # type: ignore[arg-type]
        )

    modulus_one_projection = _modulus_one_projection(
        max_n=bound,
        d4_representations=d4_reps,
        d20_principal_representations=d20_principal_reps,
        d20_nonprincipal_representations=d20_nonprincipal_reps,
        graph_audit=graph_audit,
    )

    d4_mult = d4["form_reports"][0]["multiplicativity"]  # type: ignore[index]
    d20_forms = d20["form_reports"]  # type: ignore[assignment]
    d20_principal_mult = d20_forms[0]["multiplicativity"]  # type: ignore[index]
    transform_mult = d20["character_transform"]["finite_multiplicativity"]  # type: ignore[index]
    return {
        "report_type": "quadratic_form_class_channel_probe",
        "config": {
            "max_n": bound,
            "edge_limit": int(edge_limit),
            "composition_event_limit": int(composition_event_limit),
            "requested_graph_stage_cutoff": requested_graph_stage_cutoff,
            "effective_graph_stage_cutoff": graph_audit["stage_censoring"][
                "effective_stage_cutoff"
            ],
            "graph_stage_cutoff_was_explicit": graph_stage_cutoff is not None,
            "full_scan": bool(full_scan),
        },
        "gauss_source_map": _gauss_source_map(),
        "claim_boundary": _claim_boundary(),
        "analytic_boundary": _analytic_boundary(),
        "corpus": corpus,
        "families": {
            "discriminant_minus_4": d4,
            "discriminant_minus_20": d20,
        },
        "graph_audit": graph_audit,
        "modulus_one_projection": modulus_one_projection,
        "summary": {
            "d4_reduced_form_enumeration_matches": d4[
                "configured_forms_match_enumeration"
            ],
            "d20_reduced_form_enumeration_matches": d20[
                "configured_forms_match_enumeration"
            ],
            "d4_normalized_coefficients_pass_finite_multiplicativity": d4_mult[
                "passes_finite_test"
            ],
            "d20_principal_coefficients_pass_finite_multiplicativity": d20_principal_mult[
                "passes_finite_test"
            ],
            "d20_trivial_character_channel_passes_finite_multiplicativity": transform_mult[
                "trivial_character_channel"
            ]["passes_finite_test"],
            "d20_sign_character_channel_passes_finite_multiplicativity": transform_mult[
                "sign_character_channel"
            ]["passes_finite_test"],
            "d20_principal_first_reported_defect": (
                d20_principal_mult["reported_defects"][0]
                if d20_principal_mult["reported_defects"]
                else None
            ),
            "graph_scalar_coverage": {
                key: graph_audit["scalar_node_coverage"][key]  # type: ignore[index]
                for key in ("requested_values", "present_values", "missing_values")
            },
            "all_form_witnesses_have_complete_positive_spine_arithmetic_dags": (
                graph_audit["complete_positive_spine_evaluation_paths"][
                    "positive_spine_arithmetic_dags_complete"
                ]
            ),
            "all_coordinate_side_ledgers_complete": graph_audit[
                "complete_positive_spine_evaluation_paths"
            ]["coordinate_side_ledgers_complete"],
            "all_d20_composition_scalar_relations_usable": (
                graph_audit["d20_composition_scalar_relation_audit"][
                    "all_scalar_multiplication_shadows_usable"
                ]
            ),
            "d20_modulus_one_projection_chain": modulus_one_projection[
                "two_stage_metrics"
            ]["gauss_determinant_minus_5_modern_discriminant_minus_20"][
                "projection_chain"
            ],
            "bare_modulus_one_class_distinction": False,
            "constructive_rh_proof_status": "not_attempted_and_not_supported_by_this_probe",
            "next_analytic_obligation": (
                "continue with moo_theta_weil_probe.py, then compute an independent "
                "arithmetic explicit-formula matrix with interval errors and a proved "
                "dense test-space exhaustion"
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Enumerate exact quadratic-form representation fibres, test D=-4 and "
            "D=-20 coefficient channels, and audit their scalar support against a "
            "strict MoO graph corpus."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--max-n", type=positive_int, default=DEFAULT_MAX_N)
    parser.add_argument("--edge-limit", type=positive_int, default=DEFAULT_EDGE_LIMIT)
    parser.add_argument(
        "--composition-event-limit",
        type=positive_int,
        default=DEFAULT_COMPOSITION_EVENT_LIMIT,
        help="Maximum normalized D=-20 composition events emitted in the report.",
    )
    parser.add_argument(
        "--graph-stage-cutoff",
        type=positive_int,
        help=(
            "Censor graph nodes and edges to this stage. max_n is used when omitted."
        ),
    )
    parser.add_argument("--full-scan", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--write",
        type=Path,
        help="Also write the JSON report. Existing files are never overwritten.",
    )
    parser.add_argument("--experiment-id")
    parser.add_argument(
        "--with-checksums",
        action="store_true",
        help="Include SHA-256 hashes for the corpus DB and probe tool.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    payload = quadratic_form_probe(
        db_path=Path(args.db),
        max_n=int(args.max_n),
        edge_limit=int(args.edge_limit),
        composition_event_limit=int(args.composition_event_limit),
        graph_stage_cutoff=(
            int(args.graph_stage_cutoff)
            if args.graph_stage_cutoff is not None
            else None
        ),
        full_scan=bool(args.full_scan),
    )
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_quadratic_form_probe.v2",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
