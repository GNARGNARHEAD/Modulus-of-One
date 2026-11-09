from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from moo.quadratic_form_probe import (
    BinaryQuadraticForm,
    D20_NONPRINCIPAL,
    D20_PRINCIPAL,
    enumerate_representations,
    reduced_primitive_forms,
)


Pair = Tuple[int, int]
Matrix2 = Tuple[int, int, int, int]
FormCoefficients = Tuple[int, int, int]
Monomial = Tuple[int, int, int, int]
Polynomial = Dict[Monomial, int]
ClassTable = Dict[Tuple[str, str], str]


@dataclass(frozen=True)
class QuadraticFamilySpec:
    family_id: str
    discriminant: int
    forms: Tuple[BinaryQuadraticForm, ...]
    class_exponents: Tuple[Tuple[str, int], ...]
    cyclic_order: int
    local_moduli: Tuple[int, ...]

    @property
    def forms_by_id(self) -> Dict[str, BinaryQuadraticForm]:
        return {form.form_id: form for form in self.forms}

    @property
    def exponent_by_form_id(self) -> Dict[str, int]:
        return dict(self.class_exponents)

    @property
    def form_id_by_exponent(self) -> Dict[int, str]:
        return {exponent: form_id for form_id, exponent in self.class_exponents}

    @property
    def identity_form_id(self) -> str:
        return self.form_id_by_exponent[0]


D23_PRINCIPAL = BinaryQuadraticForm(
    form_id="d23_A_principal",
    class_label="A",
    a=1,
    b=1,
    c=6,
    automorphism_normalization=2,
)
D23_POSITIVE_ORIENTATION = BinaryQuadraticForm(
    form_id="d23_P_generator",
    class_label="P",
    a=2,
    b=1,
    c=3,
    automorphism_normalization=2,
)
D23_NEGATIVE_ORIENTATION = BinaryQuadraticForm(
    form_id="d23_M_inverse",
    class_label="M",
    a=2,
    b=-1,
    c=3,
    automorphism_normalization=2,
)

D56_PRINCIPAL = BinaryQuadraticForm(
    form_id="d56_A_principal",
    class_label="A",
    a=1,
    b=0,
    c=14,
    automorphism_normalization=2,
)
D56_ORDER_TWO = BinaryQuadraticForm(
    form_id="d56_C_order_two",
    class_label="C",
    a=2,
    b=0,
    c=7,
    automorphism_normalization=2,
)
D56_POSITIVE_ORIENTATION = BinaryQuadraticForm(
    form_id="d56_P_generator",
    class_label="P",
    a=3,
    b=2,
    c=5,
    automorphism_normalization=2,
)
D56_NEGATIVE_ORIENTATION = BinaryQuadraticForm(
    form_id="d56_M_inverse",
    class_label="M",
    a=3,
    b=-2,
    c=5,
    automorphism_normalization=2,
)


D20_FAMILY = QuadraticFamilySpec(
    family_id="modern_discriminant_minus_20",
    discriminant=-20,
    forms=(D20_PRINCIPAL, D20_NONPRINCIPAL),
    class_exponents=(
        (D20_PRINCIPAL.form_id, 0),
        (D20_NONPRINCIPAL.form_id, 1),
    ),
    cyclic_order=2,
    local_moduli=(1, 4, 5, 20),
)
D23_FAMILY = QuadraticFamilySpec(
    family_id="modern_discriminant_minus_23",
    discriminant=-23,
    forms=(
        D23_PRINCIPAL,
        D23_POSITIVE_ORIENTATION,
        D23_NEGATIVE_ORIENTATION,
    ),
    class_exponents=(
        (D23_PRINCIPAL.form_id, 0),
        (D23_POSITIVE_ORIENTATION.form_id, 1),
        (D23_NEGATIVE_ORIENTATION.form_id, 2),
    ),
    cyclic_order=3,
    local_moduli=(1, 23),
)
D56_FAMILY = QuadraticFamilySpec(
    family_id="modern_discriminant_minus_56",
    discriminant=-56,
    forms=(
        D56_PRINCIPAL,
        D56_POSITIVE_ORIENTATION,
        D56_ORDER_TWO,
        D56_NEGATIVE_ORIENTATION,
    ),
    class_exponents=(
        (D56_PRINCIPAL.form_id, 0),
        (D56_POSITIVE_ORIENTATION.form_id, 1),
        (D56_ORDER_TWO.form_id, 2),
        (D56_NEGATIVE_ORIENTATION.form_id, 3),
    ),
    cyclic_order=4,
    local_moduli=(1, 7, 8, 56),
)

FAMILIES_BY_DISCRIMINANT: Dict[int, QuadraticFamilySpec] = {
    family.discriminant: family
    for family in (D20_FAMILY, D23_FAMILY, D56_FAMILY)
}


def form_coefficients(form: BinaryQuadraticForm) -> FormCoefficients:
    return form.a, form.b, form.c


def expected_cyclic_class_table(spec: QuadraticFamilySpec) -> ClassTable:
    by_exponent = spec.form_id_by_exponent
    exponents = spec.exponent_by_form_id
    return {
        (left.form_id, right.form_id): by_exponent[
            (exponents[left.form_id] + exponents[right.form_id])
            % spec.cyclic_order
        ]
        for left in spec.forms
        for right in spec.forms
    }


def proper_pm_i_images(form: BinaryQuadraticForm, pair: Pair) -> Tuple[Pair, Pair]:
    """Return the proper {+I,-I} orbit used for all configured families."""
    if form.discriminant in {-3, -4}:
        raise ValueError("the generic +/-I orbit excludes exceptional discriminants")
    x, y = pair
    if x == 0 and y == 0:
        raise ValueError("the zero pair is excluded from positive representation orbits")
    images = tuple(sorted(((x, y), (-x, -y))))
    if len(set(images)) != 2:
        raise AssertionError("a nonzero +/-I orbit must have size two")
    if any(form.evaluate(*image) != form.evaluate(x, y) for image in images):
        raise AssertionError("proper +/-I action changed the represented value")
    return images


def canonical_pm_i_representative(form: BinaryQuadraticForm, pair: Pair) -> Pair:
    return proper_pm_i_images(form, pair)[0]


def proper_pm_i_orbit_table(
    form: BinaryQuadraticForm,
    representations: Mapping[int, Sequence[Pair]],
) -> Dict[int, Tuple[Pair, ...]]:
    table: Dict[int, Tuple[Pair, ...]] = {}
    for value in sorted(representations):
        witnesses = set(representations[value])
        representatives = {
            canonical_pm_i_representative(form, pair) for pair in witnesses
        }
        reconstructed = {
            image
            for representative in representatives
            for image in proper_pm_i_images(form, representative)
        }
        if reconstructed != witnesses:
            raise AssertionError(
                f"+/-I orbits do not partition {form.form_id} at n={value}"
            )
        if len(representatives) * 2 != len(witnesses):
            raise AssertionError(
                f"+/-I normalization failed for {form.form_id} at n={value}"
            )
        table[int(value)] = tuple(sorted(representatives))
    return table


@lru_cache(maxsize=None)
def sl2_matrices(bound: int) -> Tuple[Matrix2, ...]:
    limit = int(bound)
    if limit < 1:
        raise ValueError("SL2 search bound must be >= 1")
    matrices = [
        (p, q, r, s)
        for p in range(-limit, limit + 1)
        for q in range(-limit, limit + 1)
        for r in range(-limit, limit + 1)
        for s in range(-limit, limit + 1)
        if p * s - q * r == 1
    ]
    return tuple(
        sorted(
            matrices,
            key=lambda matrix: (
                max(abs(entry) for entry in matrix),
                sum(abs(entry) for entry in matrix),
                matrix,
            ),
        )
    )


def transform_coefficients(
    coefficients: FormCoefficients,
    matrix: Matrix2,
) -> FormCoefficients:
    """Apply Q(px+qy,rx+sy) for an SL2 matrix (p,q;r,s)."""
    a, b, c = coefficients
    p, q, r, s = matrix
    if p * s - q * r != 1:
        raise ValueError("proper equivalence requires determinant +1")
    return (
        a * p * p + b * p * r + c * r * r,
        2 * a * p * q + b * (p * s + q * r) + 2 * c * r * s,
        a * q * q + b * q * s + c * s * s,
    )


def find_sl2_equivalence(
    source: FormCoefficients,
    target: FormCoefficients,
    *,
    bound: int = 4,
) -> Optional[Matrix2]:
    for matrix in sl2_matrices(bound):
        if transform_coefficients(source, matrix) == target:
            return matrix
    return None


@dataclass(frozen=True)
class DirectCompositionResult:
    left_transformed: FormCoefficients
    right_transformed: FormCoefficients
    left_matrix: Matrix2
    right_matrix: Matrix2
    common_middle: int
    product: FormCoefficients


def _transformed_variants(
    form: BinaryQuadraticForm,
    bound: int,
) -> Tuple[Tuple[FormCoefficients, Matrix2], ...]:
    variants: Dict[FormCoefficients, Matrix2] = {}
    for matrix in sl2_matrices(bound):
        transformed = transform_coefficients(form_coefficients(form), matrix)
        variants.setdefault(transformed, matrix)
    return tuple(sorted(variants.items()))


def direct_dirichlet_compose(
    left: BinaryQuadraticForm,
    right: BinaryQuadraticForm,
    *,
    concordance_bound: int = 2,
) -> DirectCompositionResult:
    """Compose after an exact bounded search for concordant representatives.

    Concordant representatives have a common middle coefficient and coprime
    leading coefficients. Their direct Dirichlet product is [a1*a2,b,c].
    The fixed families in this module all find such representatives by bound 2.
    """
    if left.discriminant != right.discriminant:
        raise ValueError("Dirichlet composition requires a common discriminant")
    discriminant = left.discriminant
    candidates: List[
        Tuple[
            Tuple[object, ...],
            FormCoefficients,
            FormCoefficients,
            Matrix2,
            Matrix2,
            FormCoefficients,
        ]
    ] = []
    for left_coeffs, left_matrix in _transformed_variants(
        left, concordance_bound
    ):
        for right_coeffs, right_matrix in _transformed_variants(
            right, concordance_bound
        ):
            left_a, left_b, _ = left_coeffs
            right_a, right_b, _ = right_coeffs
            if left_b != right_b or math.gcd(left_a, right_a) != 1:
                continue
            product_a = left_a * right_a
            numerator = left_b * left_b - discriminant
            denominator = 4 * product_a
            if numerator % denominator:
                continue
            product = (product_a, left_b, numerator // denominator)
            key: Tuple[object, ...] = (
                abs(left_b),
                product_a,
                left_a + right_a,
                left_coeffs,
                right_coeffs,
                left_matrix,
                right_matrix,
            )
            candidates.append(
                (
                    key,
                    left_coeffs,
                    right_coeffs,
                    left_matrix,
                    right_matrix,
                    product,
                )
            )
    if not candidates:
        raise ValueError(
            "no concordant representatives found within the configured SL2 bound"
        )
    (
        _,
        left_coeffs,
        right_coeffs,
        left_matrix,
        right_matrix,
        product,
    ) = min(candidates, key=lambda candidate: candidate[0])
    return DirectCompositionResult(
        left_transformed=left_coeffs,
        right_transformed=right_coeffs,
        left_matrix=left_matrix,
        right_matrix=right_matrix,
        common_middle=left_coeffs[1],
        product=product,
    )


def reduce_product_by_sl2_search(
    product: FormCoefficients,
    reduced_forms: Sequence[BinaryQuadraticForm],
    *,
    equivalence_bound: int = 4,
) -> Tuple[BinaryQuadraticForm, Matrix2]:
    matches = []
    for target in reduced_forms:
        matrix = find_sl2_equivalence(
            product,
            form_coefficients(target),
            bound=equivalence_bound,
        )
        if matrix is not None:
            matches.append((target, matrix))
    if len(matches) != 1:
        raise AssertionError(
            f"expected one reduced proper class for {product}, found {len(matches)}"
        )
    return matches[0]


def direct_dirichlet_class_table(
    spec: QuadraticFamilySpec,
    *,
    concordance_bound: int = 2,
    equivalence_bound: int = 4,
) -> ClassTable:
    expected_reduced = {
        form_coefficients(form) for form in spec.forms
    }
    enumerated_reduced = set(reduced_primitive_forms(spec.discriminant))
    if enumerated_reduced != expected_reduced:
        raise AssertionError(
            f"configured reduced forms for D={spec.discriminant} do not match "
            "the independent enumeration"
        )
    table: ClassTable = {}
    for left in spec.forms:
        for right in spec.forms:
            direct = direct_dirichlet_compose(
                left,
                right,
                concordance_bound=concordance_bound,
            )
            target, _ = reduce_product_by_sl2_search(
                direct.product,
                spec.forms,
                equivalence_bound=equivalence_bound,
            )
            table[(left.form_id, right.form_id)] = target.form_id
    _validate_class_table(spec, table)
    return table


def _validate_class_table(
    spec: QuadraticFamilySpec,
    table: Mapping[Tuple[str, str], str],
) -> None:
    form_ids = tuple(form.form_id for form in spec.forms)
    identity = spec.identity_form_id
    for left in form_ids:
        for right in form_ids:
            if (left, right) not in table:
                raise AssertionError("class table is incomplete")
            if table[(left, right)] != table[(right, left)]:
                raise AssertionError("proper class table is not commutative")
    for form_id in form_ids:
        if table[(identity, form_id)] != form_id:
            raise AssertionError("configured principal form is not an identity")
        if not any(table[(form_id, candidate)] == identity for candidate in form_ids):
            raise AssertionError(f"class {form_id} has no inverse")
    for left in form_ids:
        for middle in form_ids:
            for right in form_ids:
                left_associated = table[(table[(left, middle)], right)]
                right_associated = table[(left, table[(middle, right)])]
                if left_associated != right_associated:
                    raise AssertionError("class table is not associative")


def class_table_report(
    spec: QuadraticFamilySpec,
    *,
    concordance_bound: int = 2,
    equivalence_bound: int = 4,
) -> Dict[str, object]:
    table = direct_dirichlet_class_table(
        spec,
        concordance_bound=concordance_bound,
        equivalence_bound=equivalence_bound,
    )
    expected = expected_cyclic_class_table(spec)
    return {
        "family_id": spec.family_id,
        "discriminant": spec.discriminant,
        "method": (
            "direct Dirichlet composition of bounded-search concordant proper "
            "representatives, followed by exact bounded SL2 equivalence"
        ),
        "concordance_bound": int(concordance_bound),
        "equivalence_bound": int(equivalence_bound),
        "matches_expected_cyclic_table": table == expected,
        "entries": [
            {
                "left_form_id": left.form_id,
                "right_form_id": right.form_id,
                "target_form_id": table[(left.form_id, right.form_id)],
            }
            for left in spec.forms
            for right in spec.forms
        ],
    }


def derive_genus_cosets(
    spec: QuadraticFamilySpec,
    table: Optional[Mapping[Tuple[str, str], str]] = None,
) -> Dict[str, object]:
    class_table = dict(table or direct_dirichlet_class_table(spec))
    _validate_class_table(spec, class_table)
    form_ids = tuple(form.form_id for form in spec.forms)
    identity = spec.identity_form_id
    square_values = {class_table[(form_id, form_id)] for form_id in form_ids}
    square_subgroup = {identity}
    changed = True
    while changed:
        changed = False
        for left in tuple(square_subgroup | square_values):
            for right in tuple(square_subgroup | square_values):
                product = class_table[(left, right)]
                if product not in square_subgroup:
                    square_subgroup.add(product)
                    changed = True

    class_order = {form.form_id: index for index, form in enumerate(spec.forms)}
    remaining = set(form_ids)
    cosets: List[Tuple[str, ...]] = []
    while remaining:
        representative = (
            identity
            if identity in remaining
            else min(remaining, key=lambda item: class_order[item])
        )
        coset = {
            class_table[(representative, square)] for square in square_subgroup
        }
        ordered_coset = tuple(sorted(coset, key=lambda item: class_order[item]))
        cosets.append(ordered_coset)
        remaining -= coset
    class_to_genus = {
        form_id: genus_index
        for genus_index, coset in enumerate(cosets)
        for form_id in coset
    }
    return {
        "family_id": spec.family_id,
        "discriminant": spec.discriminant,
        "derivation": "Cl(D) / Cl(D)^2 from the independently derived class table",
        "square_values": sorted(square_values, key=lambda item: class_order[item]),
        "squares_subgroup": sorted(
            square_subgroup, key=lambda item: class_order[item]
        ),
        "cosets": [list(coset) for coset in cosets],
        "class_to_genus_index": class_to_genus,
        "genus_count": len(cosets),
    }


def inverse_reflection_report(
    spec: QuadraticFamilySpec,
    *,
    max_n: int,
    equivalence_bound: int = 4,
) -> Dict[str, object]:
    if int(max_n) < 1:
        raise ValueError("max_n must be >= 1")
    records = []
    all_exact = True
    for source in spec.forms:
        inverse = BinaryQuadraticForm(
            form_id=f"{source.form_id}_raw_inverse",
            class_label=f"inverse({source.class_label})",
            a=source.a,
            b=-source.b,
            c=source.c,
            automorphism_normalization=2,
        )
        source_representations = enumerate_representations(source, max_n)
        inverse_representations = enumerate_representations(inverse, max_n)
        mismatches = []
        for value in range(1, max_n + 1):
            reflected = {
                (x, -y) for x, y in source_representations[value]
            }
            if reflected != set(inverse_representations[value]):
                mismatches.append(value)
        reduced_inverse, matrix = reduce_product_by_sl2_search(
            form_coefficients(inverse),
            spec.forms,
            equivalence_bound=equivalence_bound,
        )
        expected_inverse_exponent = (
            -spec.exponent_by_form_id[source.form_id]
        ) % spec.cyclic_order
        expected_inverse_id = spec.form_id_by_exponent[expected_inverse_exponent]
        class_matches = reduced_inverse.form_id == expected_inverse_id
        record_exact = not mismatches and class_matches
        all_exact = all_exact and record_exact
        records.append(
            {
                "source_form_id": source.form_id,
                "raw_inverse_coefficients": list(form_coefficients(inverse)),
                "reduced_inverse_form_id": reduced_inverse.form_id,
                "expected_inverse_form_id": expected_inverse_id,
                "proper_equivalence_matrix": list(matrix),
                "reflection_matrix": [1, 0, 0, -1],
                "reflection_determinant": -1,
                "reflection_is_not_proper": True,
                "witness_bijection_exact": not mismatches,
                "mismatch_values": mismatches,
                "inverse_class_matches": class_matches,
            }
        )
    return {
        "family_id": spec.family_id,
        "bound": int(max_n),
        "all_inverse_reflection_controls_exact": all_exact,
        "forms": records,
    }


@dataclass(frozen=True)
class BilinearMap:
    map_id: str
    left_form_id: str
    right_form_id: str
    target_form_id: str
    x_coefficients: Tuple[int, int, int, int]
    y_coefficients: Tuple[int, int, int, int]

    def apply(self, left: Pair, right: Pair) -> Pair:
        x, y = left
        u, v = right
        monomials = (x * u, x * v, y * u, y * v)
        return (
            sum(
                coefficient * monomial
                for coefficient, monomial in zip(
                    self.x_coefficients, monomials
                )
            ),
            sum(
                coefficient * monomial
                for coefficient, monomial in zip(
                    self.y_coefficients, monomials
                )
            ),
        )


def _bilinear_map(
    map_id: str,
    left: BinaryQuadraticForm,
    right: BinaryQuadraticForm,
    target: BinaryQuadraticForm,
    x_coefficients: Tuple[int, int, int, int],
    y_coefficients: Tuple[int, int, int, int],
) -> BilinearMap:
    return BilinearMap(
        map_id=map_id,
        left_form_id=left.form_id,
        right_form_id=right.form_id,
        target_form_id=target.form_id,
        x_coefficients=x_coefficients,
        y_coefficients=y_coefficients,
    )


D20_BILINEAR_MAPS = (
    _bilinear_map(
        "d20_AA_to_A", D20_PRINCIPAL, D20_PRINCIPAL, D20_PRINCIPAL,
        (1, 0, 0, -5), (0, 1, 1, 0),
    ),
    _bilinear_map(
        "d20_AB_to_B", D20_PRINCIPAL, D20_NONPRINCIPAL, D20_NONPRINCIPAL,
        (1, 0, -1, -3), (0, 1, 2, 1),
    ),
    _bilinear_map(
        "d20_BB_to_A", D20_NONPRINCIPAL, D20_NONPRINCIPAL, D20_PRINCIPAL,
        (2, 1, 1, -2), (0, 1, 1, 1),
    ),
)

D23_BILINEAR_MAPS = (
    _bilinear_map(
        "d23_AA_to_A", D23_PRINCIPAL, D23_PRINCIPAL, D23_PRINCIPAL,
        (1, 0, 0, -6), (0, 1, 1, 1),
    ),
    _bilinear_map(
        "d23_AP_to_P", D23_PRINCIPAL, D23_POSITIVE_ORIENTATION,
        D23_POSITIVE_ORIENTATION, (1, 0, 0, -3), (0, 1, 2, 1),
    ),
    _bilinear_map(
        "d23_AM_to_M", D23_PRINCIPAL, D23_NEGATIVE_ORIENTATION,
        D23_NEGATIVE_ORIENTATION, (1, 0, 0, 3), (0, 1, -2, 1),
    ),
    _bilinear_map(
        "d23_PP_to_M", D23_POSITIVE_ORIENTATION, D23_POSITIVE_ORIENTATION,
        D23_NEGATIVE_ORIENTATION, (-1, 1, 1, 2), (-1, -1, -1, 1),
    ),
    _bilinear_map(
        "d23_PM_to_A", D23_POSITIVE_ORIENTATION, D23_NEGATIVE_ORIENTATION,
        D23_PRINCIPAL, (2, -1, 0, -3), (0, 1, 1, 0),
    ),
    _bilinear_map(
        "d23_MM_to_P", D23_NEGATIVE_ORIENTATION, D23_NEGATIVE_ORIENTATION,
        D23_POSITIVE_ORIENTATION, (-1, -1, -1, 2), (1, -1, -1, -1),
    ),
)

D56_BILINEAR_MAPS = (
    _bilinear_map(
        "d56_AA_to_A", D56_PRINCIPAL, D56_PRINCIPAL, D56_PRINCIPAL,
        (1, 0, 0, -14), (0, 1, 1, 0),
    ),
    _bilinear_map(
        "d56_AC_to_C", D56_PRINCIPAL, D56_ORDER_TWO, D56_ORDER_TWO,
        (1, 0, 0, -7), (0, 1, 2, 0),
    ),
    _bilinear_map(
        "d56_AP_to_P", D56_PRINCIPAL, D56_POSITIVE_ORIENTATION,
        D56_POSITIVE_ORIENTATION, (1, 0, -1, -5), (0, 1, 3, 1),
    ),
    _bilinear_map(
        "d56_AM_to_M", D56_PRINCIPAL, D56_NEGATIVE_ORIENTATION,
        D56_NEGATIVE_ORIENTATION, (1, 0, 1, -5), (0, 1, 3, -1),
    ),
    _bilinear_map(
        "d56_CC_to_A", D56_ORDER_TWO, D56_ORDER_TWO, D56_PRINCIPAL,
        (2, 0, 0, -7), (0, 1, 1, 0),
    ),
    _bilinear_map(
        "d56_CP_to_M", D56_ORDER_TWO, D56_POSITIVE_ORIENTATION,
        D56_NEGATIVE_ORIENTATION, (-1, 1, 2, 3), (-1, -1, -1, 2),
    ),
    _bilinear_map(
        "d56_CM_to_P", D56_ORDER_TWO, D56_NEGATIVE_ORIENTATION,
        D56_POSITIVE_ORIENTATION, (-1, -1, -2, 3), (1, -1, -1, -2),
    ),
    _bilinear_map(
        "d56_PP_to_C", D56_POSITIVE_ORIENTATION, D56_POSITIVE_ORIENTATION,
        D56_ORDER_TWO, (1, -2, -2, -3), (1, 1, 1, -1),
    ),
    _bilinear_map(
        "d56_PM_to_A", D56_POSITIVE_ORIENTATION, D56_NEGATIVE_ORIENTATION,
        D56_PRINCIPAL, (3, -1, 1, -5), (0, 1, 1, 0),
    ),
    _bilinear_map(
        "d56_MM_to_C", D56_NEGATIVE_ORIENTATION, D56_NEGATIVE_ORIENTATION,
        D56_ORDER_TWO, (1, 2, 2, -3), (-1, 1, 1, 1),
    ),
)

BILINEAR_MAPS_BY_DISCRIMINANT: Dict[int, Tuple[BilinearMap, ...]] = {
    -20: D20_BILINEAR_MAPS,
    -23: D23_BILINEAR_MAPS,
    -56: D56_BILINEAR_MAPS,
}


def _poly_add(left: Polynomial, right: Polynomial) -> Polynomial:
    result = dict(left)
    for monomial, coefficient in right.items():
        result[monomial] = result.get(monomial, 0) + coefficient
        if result[monomial] == 0:
            del result[monomial]
    return result


def _poly_scale(polynomial: Polynomial, coefficient: int) -> Polynomial:
    if coefficient == 0:
        return {}
    return {
        monomial: coefficient * value
        for monomial, value in polynomial.items()
        if coefficient * value
    }


def _poly_multiply(left: Polynomial, right: Polynomial) -> Polynomial:
    result: Polynomial = {}
    for left_monomial, left_coefficient in left.items():
        for right_monomial, right_coefficient in right.items():
            monomial = tuple(
                left_power + right_power
                for left_power, right_power in zip(
                    left_monomial, right_monomial
                )
            )
            result[monomial] = (
                result.get(monomial, 0)
                + left_coefficient * right_coefficient
            )
            if result[monomial] == 0:
                del result[monomial]
    return result


def _form_polynomial(form: BinaryQuadraticForm, *, right: bool) -> Polynomial:
    if right:
        square_first = (0, 0, 2, 0)
        cross = (0, 0, 1, 1)
        square_second = (0, 0, 0, 2)
    else:
        square_first = (2, 0, 0, 0)
        cross = (1, 1, 0, 0)
        square_second = (0, 2, 0, 0)
    return {
        square_first: form.a,
        cross: form.b,
        square_second: form.c,
    }


def _bilinear_polynomial(coefficients: Sequence[int]) -> Polynomial:
    monomials = (
        (1, 0, 1, 0),
        (1, 0, 0, 1),
        (0, 1, 1, 0),
        (0, 1, 0, 1),
    )
    return {
        monomial: int(coefficient)
        for monomial, coefficient in zip(monomials, coefficients)
        if coefficient
    }


def symbolic_bilinear_residual(
    bilinear_map: BilinearMap,
    forms_by_id: Mapping[str, BinaryQuadraticForm],
) -> Polynomial:
    left = forms_by_id[bilinear_map.left_form_id]
    right = forms_by_id[bilinear_map.right_form_id]
    target = forms_by_id[bilinear_map.target_form_id]
    product = _poly_multiply(
        _form_polynomial(left, right=False),
        _form_polynomial(right, right=True),
    )
    output_x = _bilinear_polynomial(bilinear_map.x_coefficients)
    output_y = _bilinear_polynomial(bilinear_map.y_coefficients)
    target_polynomial = _poly_add(
        _poly_add(
            _poly_scale(_poly_multiply(output_x, output_x), target.a),
            _poly_scale(_poly_multiply(output_x, output_y), target.b),
        ),
        _poly_scale(_poly_multiply(output_y, output_y), target.c),
    )
    return _poly_add(product, _poly_scale(target_polynomial, -1))


def symbolic_identity_report(spec: QuadraticFamilySpec) -> Dict[str, object]:
    forms_by_id = spec.forms_by_id
    records = []
    for bilinear_map in BILINEAR_MAPS_BY_DISCRIMINANT[spec.discriminant]:
        residual = symbolic_bilinear_residual(bilinear_map, forms_by_id)
        records.append(
            {
                "map_id": bilinear_map.map_id,
                "identity_holds": not residual,
                "nonzero_residual_terms": [
                    {"powers_x_y_u_v": list(monomial), "coefficient": coefficient}
                    for monomial, coefficient in sorted(residual.items())
                ],
            }
        )
    return {
        "family_id": spec.family_id,
        "all_symbolic_identities_hold": all(
            record["identity_holds"] for record in records
        ),
        "maps": records,
    }


def bounded_composition_ledger(
    spec: QuadraticFamilySpec,
    *,
    max_n: int,
    event_limit: int = 1_000,
) -> Dict[str, object]:
    if int(max_n) < 1:
        raise ValueError("max_n must be >= 1")
    if int(event_limit) < 0:
        raise ValueError("event_limit must be >= 0")
    identity_report = symbolic_identity_report(spec)
    if not identity_report["all_symbolic_identities_hold"]:
        raise AssertionError("a configured bilinear identity is not exact")
    direct_table = direct_dirichlet_class_table(spec)
    representations = {
        form.form_id: enumerate_representations(form, max_n)
        for form in spec.forms
    }
    orbits = {
        form.form_id: proper_pm_i_orbit_table(
            form, representations[form.form_id]
        )
        for form in spec.forms
    }
    forms_by_id = spec.forms_by_id
    total_events = 0
    identity_failures = 0
    target_fibre_failures = 0
    class_target_failures = 0
    signature_counts: Dict[str, int] = {}
    scalar_relation_ids = set()
    records = []
    for bilinear_map in BILINEAR_MAPS_BY_DISCRIMINANT[spec.discriminant]:
        left_id = bilinear_map.left_form_id
        right_id = bilinear_map.right_form_id
        target_id = bilinear_map.target_form_id
        class_target_holds = direct_table[(left_id, right_id)] == target_id
        if not class_target_holds:
            class_target_failures += 1
        signature_counts[bilinear_map.map_id] = 0
        same_class = left_id == right_id
        for left_value in range(1, max_n + 1):
            for right_value in range(1, max_n // left_value + 1):
                product = left_value * right_value
                for left_pair in orbits[left_id][left_value]:
                    for right_pair in orbits[right_id][right_value]:
                        if same_class and (left_value, left_pair) > (
                            right_value,
                            right_pair,
                        ):
                            continue
                        output_pair = bilinear_map.apply(left_pair, right_pair)
                        output_value = forms_by_id[target_id].evaluate(*output_pair)
                        identity_holds = output_value == product
                        canonical_output = canonical_pm_i_representative(
                            forms_by_id[target_id], output_pair
                        )
                        target_contains = canonical_output in set(
                            orbits[target_id][product]
                        )
                        total_events += 1
                        signature_counts[bilinear_map.map_id] += 1
                        if not identity_holds:
                            identity_failures += 1
                        if not target_contains:
                            target_fibre_failures += 1
                        if identity_holds and target_contains and class_target_holds:
                            scalar_relation_ids.add(
                                "multiply:"
                                f"{min(left_value, right_value)}:"
                                f"{max(left_value, right_value)}:{product}"
                            )
                        if len(records) < event_limit:
                            records.append(
                                {
                                    "event_id": total_events,
                                    "map_id": bilinear_map.map_id,
                                    "left_form_id": left_id,
                                    "left_value": left_value,
                                    "left_orbit_representative": list(left_pair),
                                    "right_form_id": right_id,
                                    "right_value": right_value,
                                    "right_orbit_representative": list(right_pair),
                                    "target_form_id": target_id,
                                    "target_value": output_value,
                                    "raw_target_coordinates": list(output_pair),
                                    "canonical_target_orbit": list(canonical_output),
                                    "identity_holds": identity_holds,
                                    "target_orbit_in_complete_fibre": target_contains,
                                    "modulus_one_projection": [0, 0, 0],
                                }
                            )
    all_verified = (
        identity_failures == 0
        and target_fibre_failures == 0
        and class_target_failures == 0
    )
    return {
        "family_id": spec.family_id,
        "bound": int(max_n),
        "event_definition": (
            "+/-I proper-orbit representatives with product <= max_n; "
            "same-class source pairs are unordered"
        ),
        "total_composition_events": total_events,
        "signature_counts": signature_counts,
        "identity_failure_count": identity_failures,
        "target_fibre_failure_count": target_fibre_failures,
        "class_target_failure_count": class_target_failures,
        "all_events_verified_exactly": all_verified,
        "scalar_relation_ids": sorted(scalar_relation_ids),
        "distinct_scalar_relation_count": len(scalar_relation_ids),
        "event_limit": int(event_limit),
        "reported_event_count": len(records),
        "events_truncated": len(records) < total_events,
        "complete_event_list_emitted": total_events <= event_limit,
        "reported_events": records,
    }


def local_residue_distribution(
    form: BinaryQuadraticForm,
    modulus: int,
) -> Dict[int, int]:
    m = int(modulus)
    if m < 1:
        raise ValueError("modulus must be >= 1")
    counts = {residue: 0 for residue in range(m)}
    for x in range(m):
        for y in range(m):
            counts[form.evaluate(x, y) % m] += 1
    if sum(counts.values()) != m * m:
        raise AssertionError("local residue distribution lost coordinate pairs")
    return counts


def default_modulus_ladder(
    spec: QuadraticFamilySpec,
    *,
    max_n: int,
) -> Tuple[int, ...]:
    if int(max_n) < 1:
        raise ValueError("max_n must be >= 1")
    absolute_discriminant = abs(spec.discriminant)
    divisors = {
        divisor
        for divisor in range(1, absolute_discriminant + 1)
        if absolute_discriminant % divisor == 0
    }
    return tuple(sorted(divisors | {int(max_n) + 1}))


def quotient_ladder_report(
    spec: QuadraticFamilySpec,
    *,
    max_n: int,
    moduli: Optional[Iterable[int]] = None,
) -> Dict[str, object]:
    if int(max_n) < 1:
        raise ValueError("max_n must be >= 1")
    selected = tuple(
        sorted(
            set(
                int(modulus)
                for modulus in (
                    moduli
                    if moduli is not None
                    else default_modulus_ladder(spec, max_n=max_n)
                )
            )
        )
    )
    if not selected or selected[0] < 1:
        raise ValueError("all moduli must be >= 1")
    representations = {
        form.form_id: enumerate_representations(form, max_n)
        for form in spec.forms
    }
    modulus_records = []
    for modulus in selected:
        form_records = []
        union_residues = set()
        for form in spec.forms:
            represented_values = [
                value
                for value in range(1, max_n + 1)
                if representations[form.form_id][value]
            ]
            distinct_buckets = {residue: [] for residue in range(modulus)}
            raw_witness_counts = {residue: 0 for residue in range(modulus)}
            for value in represented_values:
                residue = value % modulus
                distinct_buckets[residue].append(value)
                raw_witness_counts[residue] += len(
                    representations[form.form_id][value]
                )
                union_residues.add(residue)
            local_counts = local_residue_distribution(form, modulus)
            form_records.append(
                {
                    "form_id": form.form_id,
                    "local_coordinate_residue_counts": local_counts,
                    "bounded_distinct_value_buckets": distinct_buckets,
                    "bounded_raw_witness_bucket_counts": raw_witness_counts,
                }
            )
        modulus_records.append(
            {
                "modulus": modulus,
                "bare_occupied_residues": sorted(union_residues),
                "bare_occupied_residue_count": len(union_residues),
                "forms": form_records,
            }
        )
    injective_candidates = [
        modulus for modulus in selected if modulus > int(max_n)
    ]
    return {
        "family_id": spec.family_id,
        "bound": int(max_n),
        "moduli": list(selected),
        "modulus_records": modulus_records,
        "modulus_one_is_singleton": any(
            record["modulus"] == 1
            and record["bare_occupied_residues"] == [0]
            for record in modulus_records
        ),
        "injective_modulus": (
            min(injective_candidates) if injective_candidates else None
        ),
    }


def genus_character_d56(value: int) -> Optional[int]:
    """Return the conductor-8 genus character on the coprime scalar slice."""
    n = int(value)
    if n < 1:
        raise ValueError("represented values must be positive")
    if math.gcd(n, 56) != 1:
        return None
    residue = n % 8
    if residue in {1, 7}:
        return 1
    if residue in {3, 5}:
        return -1
    raise AssertionError("a value coprime to 56 must have an odd residue mod 8")


def genus_character_audit_d56(*, max_n: int) -> Dict[str, object]:
    genus = derive_genus_cosets(D56_FAMILY)
    class_to_genus = genus["class_to_genus_index"]
    principal_genus = class_to_genus[D56_PRINCIPAL.form_id]
    mismatches = []
    checked = 0
    for form in D56_FAMILY.forms:
        expected = 1 if class_to_genus[form.form_id] == principal_genus else -1
        representations = enumerate_representations(form, max_n)
        for value in range(1, max_n + 1):
            if not representations[value] or math.gcd(value, 56) != 1:
                continue
            checked += 1
            observed = genus_character_d56(value)
            if observed != expected:
                mismatches.append(
                    {
                        "form_id": form.form_id,
                        "value": value,
                        "expected": expected,
                        "observed": observed,
                    }
                )
    return {
        "bound": int(max_n),
        "checked_form_value_pairs": checked,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "all_coprime_values_match_derived_genus": not mismatches,
    }


def nested_family_integrity_report(
    spec: QuadraticFamilySpec,
    *,
    max_n: int,
    event_limit: int = 100,
) -> Dict[str, object]:
    table = class_table_report(spec)
    report = {
        "family_id": spec.family_id,
        "discriminant": spec.discriminant,
        "forms": [form.payload() for form in spec.forms],
        "reduced_class_table": table,
        "genus": derive_genus_cosets(spec),
        "inverse_reflection": inverse_reflection_report(spec, max_n=max_n),
        "symbolic_composition": symbolic_identity_report(spec),
        "bounded_composition": bounded_composition_ledger(
            spec, max_n=max_n, event_limit=event_limit
        ),
        "quotient_ladder": quotient_ladder_report(spec, max_n=max_n),
    }
    if spec.discriminant == -56:
        report["genus_character_audit"] = genus_character_audit_d56(
            max_n=max_n
        )
    return report
