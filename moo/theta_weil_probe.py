from __future__ import annotations

import argparse
import cmath
import math
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from moo.quadratic_form_probe import (
    DEFAULT_EDGE_LIMIT,
    DEFAULT_MAX_N,
    HARD_MAX_N,
    SOFT_MAX_N,
    BinaryQuadraticForm,
    D4_PRINCIPAL,
    D20_NONPRINCIPAL,
    D20_PRINCIPAL,
    enumerate_representations,
    normalized_coefficients,
    quadratic_form_probe,
)
from moo.research_utils import emit_json, positive_int, report_metadata


Pair = Tuple[int, int]
RealMatrix = List[List[float]]

DEFAULT_THETA_T = (0.25, 0.5, 1.0, 2.0, 4.0)
DEFAULT_WEIL_BASIS_DIM = 6
DEFAULT_WEIL_SCALE = 16.0
DEFAULT_PSD_RELATIVE_TOLERANCE = 1e-10
DEFAULT_OFF_LINE_SIGMA = 0.7
DEFAULT_OFF_LINE_T = 3.0
SOFT_MAX_BASIS_DIM = 12
HARD_MAX_BASIS_DIM = 24
HARD_MAX_THETA_SAMPLES = 32


def _fraction_payload(value: Fraction) -> Dict[str, object]:
    return {
        "p": int(value.numerator),
        "q": int(value.denominator),
        "frac": (
            str(value.numerator)
            if value.denominator == 1
            else f"{value.numerator}/{value.denominator}"
        ),
        "value_float": float(value),
    }


def _exact_fraction_payload(value: Fraction) -> Dict[str, object]:
    """Serialize a rational without adding a floating-point approximation."""
    return {
        "p": int(value.numerator),
        "q": int(value.denominator),
        "frac": (
            str(value.numerator)
            if value.denominator == 1
            else f"{value.numerator}/{value.denominator}"
        ),
    }


def positive_form_radial_lower_bound(form: BinaryQuadraticForm) -> Fraction:
    """Return mu with Q(x,y) >= mu*(x^2+y^2), when this bound is positive."""
    numerator = min(
        2 * form.a - abs(form.b),
        2 * form.c - abs(form.b),
    )
    if numerator <= 0:
        raise ValueError(
            "the elementary 2|xy| bound is not positive for this form"
        )
    return Fraction(numerator, 2)


def theta_tail_envelope(
    form: BinaryQuadraticForm,
    *,
    max_n: int,
    t: float,
    eta: float = 0.5,
) -> Dict[str, object]:
    """Bound the raw positive theta tail beyond Q(x,y) > max_n."""
    if int(max_n) < 1:
        raise ValueError("max_n must be >= 1")
    if not math.isfinite(float(t)) or float(t) <= 0.0:
        raise ValueError("theta t must be finite and > 0")
    if not math.isfinite(float(eta)) or not 0.0 < float(eta) < 1.0:
        raise ValueError("eta must satisfy 0 < eta < 1")

    mu = positive_form_radial_lower_bound(form)
    t_value = float(t)
    eta_value = float(eta)
    log_exponential = -math.pi * t_value * (1.0 - eta_value) * int(max_n)
    lattice_envelope = (
        1.0 + 1.0 / math.sqrt(eta_value * t_value * float(mu))
    ) ** 2
    log_bound = log_exponential + math.log(lattice_envelope)
    bound = math.exp(log_bound)
    return {
        "form_id": form.form_id,
        "max_n": int(max_n),
        "t": t_value,
        "eta": eta_value,
        "radial_lower_bound_mu": _fraction_payload(mu),
        "radial_bound": "Q(x,y) >= mu*(x^2+y^2)",
        "formula": (
            "exp(-pi*t*(1-eta)*N) * "
            "(1 + 1/sqrt(eta*t*mu))^2"
        ),
        "analytic_bound_log_binary64": log_bound,
        "analytic_bound_formula_value_binary64": bound,
        "binary64_evaluation_underflowed_to_zero": bound == 0.0,
        "derivation": (
            "split exp(-pi*t*Q) at eta, use Q>N in one factor, "
            "Q>=mu*(x^2+y^2) in the other, and bound the integer "
            "Gaussian sum by 1+its real-line integral"
        ),
        "formula_is_analytic_bound": True,
        "numeric_value_is_certified_upper_bound": False,
        "numeric_interval_is_rigorous": False,
        "numeric_limitation": (
            "the formula is rigorous over exact reals, but this reported value "
            "uses ordinary binary64 exp, log, and sqrt without directed rounding"
        ),
    }


def theta_prefix_value(
    coefficients: Mapping[int, int],
    *,
    constant_term: float,
    t: float,
) -> float:
    if not math.isfinite(float(t)) or float(t) <= 0.0:
        raise ValueError("theta t must be finite and > 0")
    return float(constant_term) + math.fsum(
        int(coefficients[n]) * math.exp(-math.pi * float(t) * int(n))
        for n in sorted(coefficients)
    )


def _theta_sample(
    coefficients: Mapping[int, int],
    *,
    constant_term: float,
    t: float,
    absolute_tail_bound: float,
    signed: bool,
) -> Dict[str, object]:
    prefix = theta_prefix_value(
        coefficients,
        constant_term=float(constant_term),
        t=float(t),
    )
    if signed:
        interval = [prefix - absolute_tail_bound, prefix + absolute_tail_bound]
    else:
        interval = [prefix, prefix + absolute_tail_bound]
    return {
        "t": float(t),
        "finite_prefix": prefix,
        "absolute_tail_formula_value_binary64": float(absolute_tail_bound),
        "nonrigorous_interval_from_analytic_formula": interval,
        "signed_coefficients": bool(signed),
        "rigorous_interval": False,
    }


def _raw_coefficients(
    representations: Mapping[int, Sequence[Pair]],
) -> Dict[int, int]:
    return {int(n): len(representations[n]) for n in sorted(representations)}


def _formal_form_theta_prefix(
    form: BinaryQuadraticForm,
    representations: Mapping[int, Sequence[Pair]],
) -> Dict[str, object]:
    """Return an exact formal theta prefix before q is specialized."""
    raw = _raw_coefficients(representations)
    normalized = normalized_coefficients(form, representations)
    unit_count = int(form.automorphism_normalization)
    witness_field = {
        D4_PRINCIPAL.form_id: "d4_witnesses",
        D20_PRINCIPAL.form_id: "d20_principal_witnesses",
        D20_NONPRINCIPAL.form_id: "d20_nonprincipal_witnesses",
    }.get(form.form_id)
    if witness_field is None:
        raise ValueError(f"no shared witness-ledger field for {form.form_id}")
    return {
        "kernel_id": f"theta_prefix:{form.form_id}",
        "form": form.payload(),
        "formal_variable": "q",
        "external_specialization": "q=exp(-pi*t)",
        "specialization_performed_in_this_payload": False,
        "coverage": {
            "minimum_index": 0,
            "maximum_index": max(raw),
            "contiguous": True,
            "indices_above_maximum": "omitted_not_zero",
        },
        "constant_term": {
            "raw": _exact_fraction_payload(Fraction(1, 1)),
            "unit_normalized": _exact_fraction_payload(Fraction(1, unit_count)),
            "source": "unique_external_zero_lattice_vector_(0,0)",
            "coefficient_is_graph_derived": False,
        },
        "positive_index_rows": [
            {
                "n": int(n),
                "raw_coefficient": _exact_fraction_payload(Fraction(raw[n], 1)),
                "unit_normalized_coefficient": _exact_fraction_payload(
                    Fraction(normalized[n], 1)
                ),
                "representation_ledger_ref": (
                    f"theta_prefix_layer.coefficient_rows[n={n}].{witness_field}"
                ),
                "coefficient_source": "complete_external_representation_fibre",
                "graph_scalar_source_id": f"scalar:{n}",
                "coefficient_is_graph_derived": False,
            }
            for n in sorted(raw)
        ],
        "finite_prefix_exact": True,
        "infinite_theta_series_evaluated": False,
    }


def _formal_d20_character_prefixes(
    principal: Mapping[int, int],
    nonprincipal: Mapping[int, int],
) -> List[Dict[str, object]]:
    keys = sorted(principal)
    if sorted(nonprincipal) != keys:
        raise ValueError("D=-20 class coefficient indices must agree")
    channels = (
        ("trivial", 1),
        ("sign", -1),
    )
    payloads: List[Dict[str, object]] = []
    for channel_id, nonprincipal_weight in channels:
        constant = Fraction(1, 2) + nonprincipal_weight * Fraction(1, 2)
        payloads.append(
            {
                "kernel_id": f"theta_character_prefix:d20:{channel_id}",
                "channel_id": channel_id,
                "character_weights": {
                    "principal": 1,
                    "nonprincipal": nonprincipal_weight,
                },
                "formal_variable": "q",
                "external_specialization": "q=exp(-pi*t)",
                "specialization_performed_in_this_payload": False,
                "constant_term": _exact_fraction_payload(constant),
                "positive_index_rows": [
                    {
                        "n": int(n),
                        "coefficient": int(
                            principal[n]
                            + nonprincipal_weight * nonprincipal[n]
                        ),
                        "class_components": {
                            "principal": int(principal[n]),
                            "nonprincipal_weighted": int(
                                nonprincipal_weight * nonprincipal[n]
                            ),
                        },
                        "graph_scalar_source_id": f"scalar:{n}",
                    }
                    for n in keys
                ],
                "coverage": {
                    "minimum_index": 0,
                    "maximum_index": max(keys),
                    "contiguous": True,
                    "indices_above_maximum": "omitted_not_zero",
                },
                "finite_prefix_exact": True,
                "infinite_theta_series_evaluated": False,
            }
        )
    return payloads


def _witness_payload(witnesses: Sequence[Pair]) -> List[Dict[str, int]]:
    return [{"x": int(x), "y": int(y)} for x, y in witnesses]


def _coefficient_cross_matrix(
    channels: Sequence[Mapping[int, int]],
    *,
    weight_t: Optional[float],
) -> RealMatrix:
    if not channels:
        return []
    keys = sorted(channels[0])
    for channel in channels[1:]:
        if sorted(channel) != keys:
            raise ValueError("coefficient channels must have the same indices")
    matrix: RealMatrix = []
    for left in channels:
        row: List[float] = []
        for right in channels:
            if weight_t is None:
                value = float(sum(int(left[n]) * int(right[n]) for n in keys))
            else:
                value = math.fsum(
                    int(left[n])
                    * int(right[n])
                    * math.exp(-2.0 * math.pi * float(weight_t) * n)
                    for n in keys
                )
            row.append(value)
        matrix.append(row)
    return matrix


def _matrix_vector_product(matrix: RealMatrix, vector: Sequence[float]) -> List[float]:
    return [
        math.fsum(float(matrix[i][j]) * float(vector[j]) for j in range(len(vector)))
        for i in range(len(matrix))
    ]


def _rayleigh(matrix: RealMatrix, vector: Sequence[float]) -> float:
    denominator = math.fsum(float(value) * float(value) for value in vector)
    if denominator == 0.0:
        raise ValueError("Rayleigh vector must be nonzero")
    product = _matrix_vector_product(matrix, vector)
    numerator = math.fsum(
        float(vector[i]) * product[i] for i in range(len(vector))
    )
    return numerator / denominator


def jacobi_eigendecomposition(
    matrix: Sequence[Sequence[float]],
    *,
    relative_tolerance: float = 1e-13,
    max_sweeps: int = 100,
) -> Tuple[List[float], RealMatrix, Dict[str, object]]:
    """Compute eigenpairs of a small real symmetric matrix using Jacobi rotations."""
    n = len(matrix)
    if n < 1 or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be nonempty and square")
    if relative_tolerance <= 0.0 or not math.isfinite(relative_tolerance):
        raise ValueError("relative_tolerance must be finite and > 0")
    a = [[float(matrix[i][j]) for j in range(n)] for i in range(n)]
    symmetry_residual = max(
        abs(a[i][j] - a[j][i])
        for i in range(n)
        for j in range(n)
    )
    for i in range(n):
        for j in range(i + 1, n):
            value = 0.5 * (a[i][j] + a[j][i])
            a[i][j] = value
            a[j][i] = value
    vectors = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    rotations = 0
    converged = False
    max_rotations = max(1, int(max_sweeps)) * n * n

    for _ in range(max_rotations):
        p = 0
        q = 1 if n > 1 else 0
        max_off = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                candidate = abs(a[i][j])
                if candidate > max_off:
                    max_off = candidate
                    p, q = i, j
        scale = max(1.0, max(abs(a[i][i]) for i in range(n)))
        if max_off <= relative_tolerance * scale:
            converged = True
            break
        apq = a[p][q]
        if apq == 0.0:
            continue
        tau = (a[q][q] - a[p][p]) / (2.0 * apq)
        if tau >= 0.0:
            tangent = 1.0 / (tau + math.sqrt(1.0 + tau * tau))
        else:
            tangent = -1.0 / (-tau + math.sqrt(1.0 + tau * tau))
        cosine = 1.0 / math.sqrt(1.0 + tangent * tangent)
        sine = tangent * cosine

        app = a[p][p]
        aqq = a[q][q]
        a[p][p] = app - tangent * apq
        a[q][q] = aqq + tangent * apq
        a[p][q] = 0.0
        a[q][p] = 0.0
        for k in range(n):
            if k in {p, q}:
                continue
            akp = a[k][p]
            akq = a[k][q]
            new_kp = cosine * akp - sine * akq
            new_kq = sine * akp + cosine * akq
            a[k][p] = new_kp
            a[p][k] = new_kp
            a[k][q] = new_kq
            a[q][k] = new_kq
        for k in range(n):
            vkp = vectors[k][p]
            vkq = vectors[k][q]
            vectors[k][p] = cosine * vkp - sine * vkq
            vectors[k][q] = sine * vkp + cosine * vkq
        rotations += 1

    eigenpairs = sorted(
        (
            float(a[column][column]),
            [float(vectors[row][column]) for row in range(n)],
        )
        for column in range(n)
    )
    eigenvalues = [pair[0] for pair in eigenpairs]
    eigenvectors = [pair[1] for pair in eigenpairs]
    max_residual = 0.0
    for eigenvalue, vector in zip(eigenvalues, eigenvectors):
        product = _matrix_vector_product(
            [[float(matrix[i][j]) for j in range(n)] for i in range(n)],
            vector,
        )
        residual = math.sqrt(
            math.fsum(
                (product[i] - eigenvalue * vector[i]) ** 2
                for i in range(n)
            )
        )
        max_residual = max(max_residual, residual)
    return eigenvalues, eigenvectors, {
        "converged": converged,
        "rotations": rotations,
        "input_symmetry_residual": symmetry_residual,
        "maximum_eigenpair_residual": max_residual,
        "relative_rotation_tolerance": relative_tolerance,
    }


def weil_basis_transform(degree: int, s: complex, *, scale: float) -> complex:
    if int(degree) < 0:
        raise ValueError("degree must be >= 0")
    if not math.isfinite(float(scale)) or float(scale) <= 0.0:
        raise ValueError("scale must be finite and > 0")
    centered = complex(s) - 0.5
    return (
        complex(s)
        * (1.0 - complex(s))
        * (centered / math.sqrt(float(scale))) ** int(degree)
        * cmath.exp((centered * centered) / (4.0 * float(scale)))
    )


def critical_line_zero_pairs(ordinates: Sequence[float]) -> List[complex]:
    points: List[complex] = []
    for ordinate in ordinates:
        value = float(ordinate)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError("zero ordinates must be finite and > 0")
        points.extend((complex(0.5, value), complex(0.5, -value)))
    return points


def off_line_zero_quartet(*, sigma: float, t: float) -> List[complex]:
    sigma_value = float(sigma)
    t_value = float(t)
    if not math.isfinite(sigma_value) or not 0.0 < sigma_value < 1.0:
        raise ValueError("off-line sigma must satisfy 0 < sigma < 1")
    if sigma_value == 0.5:
        raise ValueError("off-line sigma must not equal 0.5")
    if not math.isfinite(t_value) or t_value <= 0.0:
        raise ValueError("off-line t must be finite and > 0")
    return [
        complex(sigma_value, t_value),
        complex(sigma_value, -t_value),
        complex(1.0 - sigma_value, t_value),
        complex(1.0 - sigma_value, -t_value),
    ]


def _complex_payload(value: complex) -> Dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


def _zero_symmetry_audit(points: Sequence[complex], *, tolerance: float = 1e-12) -> Dict[str, object]:
    def present(target: complex) -> bool:
        return any(abs(complex(candidate) - target) <= tolerance for candidate in points)

    rows = []
    for point in points:
        conjugate = complex(point).conjugate()
        functional_partner = 1.0 - complex(point)
        weil_partner = 1.0 - complex(point).conjugate()
        rows.append(
            {
                "point": _complex_payload(point),
                "conjugate_present": present(conjugate),
                "one_minus_point_present": present(functional_partner),
                "one_minus_conjugate_present": present(weil_partner),
                "fixed_by_weil_involution": abs(point - weil_partner) <= tolerance,
            }
        )
    return {
        "tolerance": tolerance,
        "closed_under_conjugation": all(row["conjugate_present"] for row in rows),
        "closed_under_functional_reflection": all(
            row["one_minus_point_present"] for row in rows
        ),
        "closed_under_weil_involution": all(
            row["one_minus_conjugate_present"] for row in rows
        ),
        "all_points_fixed_by_weil_involution": all(
            row["fixed_by_weil_involution"] for row in rows
        ),
        "rows": rows,
    }


def weil_zero_side_matrix(
    points: Sequence[complex],
    *,
    basis_dim: int,
    scale: float,
) -> Tuple[RealMatrix, Dict[str, object]]:
    if int(basis_dim) < 1:
        raise ValueError("basis_dim must be >= 1")
    if not points:
        raise ValueError("at least one zero point is required")
    symmetry = _zero_symmetry_audit(points)
    if not symmetry["closed_under_conjugation"]:
        raise ValueError("zero points must be closed under conjugation")
    if not symmetry["closed_under_weil_involution"]:
        raise ValueError(
            "zero points must be closed under rho -> 1-conj(rho)"
        )
    dimension = int(basis_dim)
    raw: List[List[complex]] = []
    for left_degree in range(dimension):
        row: List[complex] = []
        for right_degree in range(dimension):
            value = sum(
                (
                    weil_basis_transform(
                        left_degree,
                        rho,
                        scale=scale,
                    ).conjugate()
                    * weil_basis_transform(
                        right_degree,
                        1.0 - complex(rho).conjugate(),
                        scale=scale,
                    )
                    for rho in points
                ),
                0j,
            )
            row.append(value)
        raw.append(row)

    antihermitian_residual = max(
        abs(raw[i][j] - raw[j][i].conjugate())
        for i in range(dimension)
        for j in range(dimension)
    )
    hermitian = [
        [
            0.5 * (raw[i][j] + raw[j][i].conjugate())
            for j in range(dimension)
        ]
        for i in range(dimension)
    ]
    imaginary_residual = max(
        abs(hermitian[i][j].imag)
        for i in range(dimension)
        for j in range(dimension)
    )
    matrix_scale = max(
        1.0,
        max(abs(raw[i][j]) for i in range(dimension) for j in range(dimension)),
    )
    if antihermitian_residual > 1e-10 * matrix_scale:
        raise ArithmeticError(
            "zero-side matrix failed the Hermitian orbit-closure check"
        )
    if imaginary_residual > 1e-10 * matrix_scale:
        raise ArithmeticError(
            "configured real basis and conjugate-closed orbit did not yield a real matrix"
        )
    matrix = [
        [float(hermitian[i][j].real) for j in range(dimension)]
        for i in range(dimension)
    ]
    return matrix, {
        "raw_antihermitian_residual": antihermitian_residual,
        "hermitian_imaginary_residual": imaginary_residual,
        "matrix_scale": matrix_scale,
        "roundoff_projection_applied_after_residual_check": True,
        "matrix_formula": (
            "H_ij=sum_rho conj(G_i(rho))*G_j(1-conj(rho))"
        ),
        "quadratic_form_convention": "Q(c)=conj(c)^T*H*c",
    }


def same_point_zero_gram_matrix(
    points: Sequence[complex],
    *,
    basis_dim: int,
    scale: float,
) -> RealMatrix:
    """Return the deliberately wrong same-point Gram surrogate."""
    if int(basis_dim) < 1:
        raise ValueError("basis_dim must be >= 1")
    if not points:
        raise ValueError("at least one zero point is required")
    if not math.isfinite(float(scale)) or float(scale) <= 0.0:
        raise ValueError("scale must be finite and > 0")
    symmetry = _zero_symmetry_audit(points)
    if not symmetry["closed_under_conjugation"]:
        raise ValueError("same-point control requires conjugate-closed points")
    dimension = int(basis_dim)
    raw = [
        [
            sum(
                (
                    weil_basis_transform(i, rho, scale=scale).conjugate()
                    * weil_basis_transform(j, rho, scale=scale)
                    for rho in points
                ),
                0j,
            )
            for j in range(dimension)
        ]
        for i in range(dimension)
    ]
    matrix_scale = max(
        1.0,
        max(abs(value) for row in raw for value in row),
    )
    imaginary_residual = max(abs(value.imag) for row in raw for value in row)
    if imaginary_residual > 1e-10 * matrix_scale:
        raise ArithmeticError("same-point real control unexpectedly remained complex")
    return [[float(value.real) for value in row] for row in raw]


def _involution_pairing_fixture() -> Dict[str, object]:
    """Exact evaluation-vector fixture separating Weil pairing from a Gram."""
    true_matrix: RealMatrix = [[0.0, 2.0], [2.0, 0.0]]
    same_point: RealMatrix = [[2.0, 0.0], [0.0, 2.0]]
    negative_vector = [1.0 / math.sqrt(2.0), -1.0 / math.sqrt(2.0)]
    true_values, _, true_solver = jacobi_eigendecomposition(true_matrix)
    placebo_values, _, placebo_solver = jacobi_eigendecomposition(same_point)
    return {
        "status": "exact_algebraic_matrix_fixture",
        "evaluation_vectors": {
            "right_half_orbit": [1, 0],
            "left_half_orbit": [0, 1],
        },
        "true_weil_involution_matrix": true_matrix,
        "true_eigenvalues": true_values,
        "exact_negative_witness_vector": [1, -1],
        "exact_negative_rayleigh_quotient": -2,
        "normalized_negative_vector_binary64": negative_vector,
        "true_negative_rayleigh_quotient": _rayleigh(
            true_matrix,
            negative_vector,
        ),
        "true_solver": true_solver,
        "same_point_gram_surrogate": same_point,
        "same_point_eigenvalues": placebo_values,
        "same_point_solver": placebo_solver,
        "control_passes": (
            true_values[0] < 0.0 and placebo_values[0] > 0.0
        ),
        "interpretation": (
            "the true involution crosses the two half-orbits and is indefinite; "
            "same-point pairing deletes that information and is PSD by construction"
        ),
        "analytic_realization_claimed": False,
    }


def _matrix_report(
    points: Sequence[complex],
    *,
    label: str,
    basis_dim: int,
    scale: float,
    psd_relative_tolerance: float,
    point_status: str,
) -> Dict[str, object]:
    matrix, construction = weil_zero_side_matrix(
        points,
        basis_dim=int(basis_dim),
        scale=float(scale),
    )
    eigenvalues, eigenvectors, solver = jacobi_eigendecomposition(matrix)
    spectral_scale = max(1.0, max(abs(value) for value in eigenvalues))
    psd_tolerance = float(psd_relative_tolerance) * spectral_scale
    effective_nonzero = [
        abs(value) for value in eigenvalues if abs(value) > psd_tolerance
    ]
    numerical_rank = len(effective_nonzero)
    condition_number = (
        max(effective_nonzero) / min(effective_nonzero)
        if effective_nonzero
        else None
    )
    minimum = eigenvalues[0]
    minimum_vector = eigenvectors[0]
    diagonal_minimum = min(matrix[i][i] for i in range(len(matrix)))
    same_point_matrix = same_point_zero_gram_matrix(
        points,
        basis_dim=int(basis_dim),
        scale=float(scale),
    )
    same_point_eigenvalues, _, same_point_solver = jacobi_eigendecomposition(
        same_point_matrix
    )
    same_point_scale = max(1.0, max(abs(value) for value in same_point_eigenvalues))
    same_point_tolerance = float(psd_relative_tolerance) * same_point_scale
    off_diagonal = [
        abs(matrix[i][j])
        for i in range(len(matrix))
        for j in range(i + 1, len(matrix))
    ]
    return {
        "label": label,
        "point_status": point_status,
        "points": [_complex_payload(point) for point in points],
        "symmetry": _zero_symmetry_audit(points),
        "basis": {
            "dimension": int(basis_dim),
            "degrees": list(range(int(basis_dim))),
            "scale": float(scale),
            "mellin_transform": (
                "G_k(s)=s*(1-s)*((s-1/2)/sqrt(scale))^k*"
                "exp((s-1/2)^2/(4*scale))"
            ),
            "endpoint_constraints": {
                "G_k(0)=0": True,
                "G_k(1)=0": True,
            },
            "test_function_origin": (
                "inverse Mellin functions are log-Gaussians times polynomials; "
                "they lie in the admissible decay class"
            ),
        },
        "construction": construction,
        "matrix": matrix,
        "cross_terms": {
            "distinct_off_diagonal_entries": len(off_diagonal),
            "maximum_absolute_off_diagonal": max(off_diagonal) if off_diagonal else 0.0,
            "included_in_eigendecomposition": True,
            "real_polarization_identity": (
                "H_ij=(Q(e_i+e_j)-Q(e_i-e_j))/4"
            ),
        },
        "eigendecomposition": {
            "eigenvalues": eigenvalues,
            "minimum_eigenvalue": minimum,
            "relative_psd_tolerance": float(psd_relative_tolerance),
            "absolute_psd_tolerance": psd_tolerance,
            "passes_finite_psd_test": minimum >= -psd_tolerance,
            "minimum_eigenvector": minimum_vector,
            "minimum_vector_rayleigh_quotient": _rayleigh(
                matrix,
                minimum_vector,
            ),
            "numerical_rank_at_psd_tolerance": numerical_rank,
            "estimated_nonzero_spectral_condition_number": condition_number,
            "solver": solver,
            "interval_certified": False,
            "operator_norm_error_bound": None,
            "certification_rule": (
                "a negative direction would require lambda_min_tilde+eta<0 "
                "for a proved operator-norm error bound eta"
            ),
        },
        "diagonal_only_placebo": {
            "minimum_diagonal_entry": diagonal_minimum,
            "would_pass_nonnegative_diagonal_test": diagonal_minimum >= 0.0,
            "discarded_cross_terms": True,
            "valid_weil_matrix_test": False,
        },
        "same_point_gram_placebo": {
            "matrix": same_point_matrix,
            "eigenvalues": same_point_eigenvalues,
            "passes_finite_psd_test": (
                same_point_eigenvalues[0] >= -same_point_tolerance
            ),
            "solver": same_point_solver,
            "formula": "P_ij=sum_rho conj(G_i(rho))*G_j(rho)",
            "substitutes_rho_for_one_minus_conjugate_rho": True,
            "valid_weil_matrix_test": False,
            "warning": (
                "this is PSD by Gram construction for every supplied point set; "
                "it assumes away the off-line involutive pairing"
            ),
        },
        "claim_status": "finite_zero_side_calibration_only",
        "is_evidence_for_rh": False,
    }


def _c2_cross_term_controls(
    plus: Mapping[int, int],
    minus: Mapping[int, int],
) -> Dict[str, object]:
    """Expose exact cancellations hidden by a diagonal-only class transform."""
    fixtures = []
    for n, reconstructed_class in ((2, "principal"), (6, "nonprincipal")):
        if n not in plus or n not in minus:
            continue
        left = Fraction(int(plus[n]), 1)
        right = Fraction(int(minus[n]), 1)
        sign = 1 if reconstructed_class == "principal" else -1
        diagonal = (left * left + right * right) / 4
        cross = Fraction(sign, 2) * left * right
        total = diagonal + cross
        fixtures.append(
            {
                "n": n,
                "character_coefficients": {
                    "plus": int(left),
                    "minus": int(right),
                },
                "reconstructed_class": reconstructed_class,
                "formula": (
                    "((a_plus+a_minus)/2)^2"
                    if sign == 1
                    else "((a_plus-a_minus)/2)^2"
                ),
                "diagonal_only_contribution": _exact_fraction_payload(diagonal),
                "cross_term_contribution": _exact_fraction_payload(cross),
                "full_value": _exact_fraction_payload(total),
                "diagonal_only_is_wrong": diagonal != total,
            }
        )

    half = Fraction(1, 2)
    class_matrix = (
        (5 * half, -3 * half),
        (-3 * half, 5 * half),
    )
    return {
        "cancellation_fixtures": fixtures,
        "all_fixtures_require_cross_terms": bool(fixtures)
        and all(row["diagonal_only_is_wrong"] for row in fixtures),
        "basis_covariance_fixture": {
            "unitary_transform": "U=2^(-1/2)*[[1,1],[1,-1]]",
            "character_basis_matrix": [[1, 0], [0, 4]],
            "class_basis_matrix": [
                [_exact_fraction_payload(value) for value in row]
                for row in class_matrix
            ],
            "identity": "H_class=U^T*H_character*U",
            "shared_eigenvalues": [1, 4],
            "diagonal_only_class_surrogate": [
                [_exact_fraction_payload(Fraction(5, 2)), _exact_fraction_payload(Fraction(0, 1))],
                [_exact_fraction_payload(Fraction(0, 1)), _exact_fraction_payload(Fraction(5, 2))],
            ],
            "warning": (
                "deleting the -3/2 cross terms changes both character-direction "
                "quadratic values to 5/2"
            ),
        },
    }


def _theta_layer(
    *,
    max_n: int,
    theta_t: Sequence[float],
    graph_rows: Sequence[Mapping[str, object]],
) -> Dict[str, object]:
    d4_reps = enumerate_representations(D4_PRINCIPAL, max_n)
    principal_reps = enumerate_representations(D20_PRINCIPAL, max_n)
    nonprincipal_reps = enumerate_representations(D20_NONPRINCIPAL, max_n)
    d4_raw = _raw_coefficients(d4_reps)
    principal_raw = _raw_coefficients(principal_reps)
    nonprincipal_raw = _raw_coefficients(nonprincipal_reps)
    principal = normalized_coefficients(D20_PRINCIPAL, principal_reps)
    nonprincipal = normalized_coefficients(D20_NONPRINCIPAL, nonprincipal_reps)
    plus = {n: principal[n] + nonprincipal[n] for n in principal}
    minus = {n: principal[n] - nonprincipal[n] for n in principal}
    graph_by_n = {int(row["value"]): row for row in graph_rows}

    coefficient_rows = []
    for n in range(1, max_n + 1):
        coefficient_rows.append(
            {
                "n": n,
                "graph_scalar_source_id": f"scalar:{n}",
                "d4_raw_count": d4_raw[n],
                "d4_witnesses": _witness_payload(d4_reps[n]),
                "d20_principal_raw_count": principal_raw[n],
                "d20_principal_witnesses": _witness_payload(principal_reps[n]),
                "d20_nonprincipal_raw_count": nonprincipal_raw[n],
                "d20_nonprincipal_witnesses": _witness_payload(
                    nonprincipal_reps[n]
                ),
                "d20_principal_coefficient": principal[n],
                "d20_nonprincipal_coefficient": nonprincipal[n],
                "d20_trivial_character_coefficient": plus[n],
                "d20_sign_character_coefficient": minus[n],
                "graph_scalar_node": graph_by_n.get(
                    n,
                    {"value": n, "present": False},
                ),
                "theta_weight_is_graph_native": False,
            }
        )

    samples = []
    d4_transform = []
    weighted_kernels = []
    for t in theta_t:
        d4_tail = theta_tail_envelope(D4_PRINCIPAL, max_n=max_n, t=t)
        principal_tail = theta_tail_envelope(
            D20_PRINCIPAL,
            max_n=max_n,
            t=t,
        )
        nonprincipal_tail = theta_tail_envelope(
            D20_NONPRINCIPAL,
            max_n=max_n,
            t=t,
        )
        channel_tail = 0.5 * (
            float(principal_tail["analytic_bound_formula_value_binary64"])
            + float(nonprincipal_tail["analytic_bound_formula_value_binary64"])
        )
        samples.append(
            {
                "t": float(t),
                "d4_raw_theta": _theta_sample(
                    d4_raw,
                    constant_term=1.0,
                    t=t,
                    absolute_tail_bound=float(
                        d4_tail["analytic_bound_formula_value_binary64"]
                    ),
                    signed=False,
                ),
                "d20_principal_raw_theta": _theta_sample(
                    principal_raw,
                    constant_term=1.0,
                    t=t,
                    absolute_tail_bound=float(
                        principal_tail["analytic_bound_formula_value_binary64"]
                    ),
                    signed=False,
                ),
                "d20_nonprincipal_raw_theta": _theta_sample(
                    nonprincipal_raw,
                    constant_term=1.0,
                    t=t,
                    absolute_tail_bound=float(
                        nonprincipal_tail["analytic_bound_formula_value_binary64"]
                    ),
                    signed=False,
                ),
                "d20_trivial_character_theta": _theta_sample(
                    plus,
                    constant_term=1.0,
                    t=t,
                    absolute_tail_bound=channel_tail,
                    signed=False,
                ),
                "d20_sign_character_theta": _theta_sample(
                    minus,
                    constant_term=0.0,
                    t=t,
                    absolute_tail_bound=channel_tail,
                    signed=True,
                ),
                "raw_tail_envelopes": {
                    "d4": d4_tail,
                    "d20_principal": principal_tail,
                    "d20_nonprincipal": nonprincipal_tail,
                },
            }
        )

        reciprocal_t = 1.0 / float(t)
        left = theta_prefix_value(d4_raw, constant_term=1.0, t=t)
        right_prefix = theta_prefix_value(
            d4_raw,
            constant_term=1.0,
            t=reciprocal_t,
        )
        reciprocal_tail = theta_tail_envelope(
            D4_PRINCIPAL,
            max_n=max_n,
            t=reciprocal_t,
        )
        right = right_prefix / float(t)
        envelope = float(d4_tail["analytic_bound_formula_value_binary64"]) + (
            float(reciprocal_tail["analytic_bound_formula_value_binary64"])
            / float(t)
        )
        residual = abs(left - right)
        roundoff_guard = (
            32.0
            * math.ulp(1.0)
            * (int(max_n) + 1)
            * (abs(left) + abs(right) + 1.0)
        )
        d4_transform.append(
            {
                "t": float(t),
                "identity": "Theta_G(t)=t^(-1)*Theta_G(1/t)",
                "left_prefix": left,
                "right_transformed_prefix": right,
                "absolute_prefix_residual": residual,
                "combined_analytic_tail_formula_value_binary64": envelope,
                "binary64_roundoff_guard": roundoff_guard,
                "roundoff_guard_formula": (
                    "32*ulp(1)*(N+1)*(abs(left)+abs(right)+1)"
                ),
                "combined_nonrigorous_comparison_guard": (
                    envelope + roundoff_guard
                ),
                "residual_within_analytic_tail_only": residual <= envelope,
                "residual_within_tail_plus_roundoff_guard": (
                    residual <= envelope + roundoff_guard
                ),
                "identity_source": "classical_Jacobi_Poisson_transform",
                "identity_reference": "https://dlmf.nist.gov/20.7",
                "identity_proved_by_probe": False,
                "rigorous_interval_check": False,
                "roundoff_guard_is_certified": False,
            }
        )

        kernel = _coefficient_cross_matrix(
            (principal, nonprincipal),
            weight_t=float(t),
        )
        kernel_values, _, kernel_solver = jacobi_eigendecomposition(kernel)
        weighted_kernels.append(
            {
                "t": float(t),
                "basis": ["principal", "nonprincipal"],
                "formula": (
                    "K_ij=sum_n a_i(n)*a_j(n)*exp(-2*pi*t*n)"
                ),
                "matrix": kernel,
                "eigenvalues": kernel_values,
                "solver": kernel_solver,
                "psd_status": "positive_by_Gram_construction",
                "is_weil_positivity_evidence": False,
            }
        )

    exact_kernel = [
        [
            sum(int(left[n]) * int(right[n]) for n in sorted(principal))
            for right in (principal, nonprincipal)
        ]
        for left in (principal, nonprincipal)
    ]
    return {
        "coefficient_status": (
            "exact finite positive-index prefixes; exponential evaluations are external"
        ),
        "coefficient_rows": coefficient_rows,
        "exact_formal_theta_prefixes": {
            "status": (
                "exact external representation coefficients over graph-audited "
                "scalar sources"
            ),
            "coefficient_is_graph_derived": False,
            "form_class_basis": [
                _formal_form_theta_prefix(D4_PRINCIPAL, d4_reps),
                _formal_form_theta_prefix(D20_PRINCIPAL, principal_reps),
                _formal_form_theta_prefix(D20_NONPRINCIPAL, nonprincipal_reps),
            ],
            "d20_character_basis": _formal_d20_character_prefixes(
                principal,
                nonprincipal,
            ),
        },
        "class_character_transform": {
            "forward": "a_plus=a_principal+a_nonprincipal; a_minus=a_principal-a_nonprincipal",
            "constant_terms": {
                "raw_form_theta": 1,
                "trivial_character_theta": 1,
                "sign_character_theta": 0,
            },
            "all_rows_satisfy_transform": all(
                row["d20_trivial_character_coefficient"]
                == row["d20_principal_coefficient"]
                + row["d20_nonprincipal_coefficient"]
                and row["d20_sign_character_coefficient"]
                == row["d20_principal_coefficient"]
                - row["d20_nonprincipal_coefficient"]
                for row in coefficient_rows
            ),
        },
        "theta_samples": samples,
        "d4_poisson_transform_calibration": d4_transform,
        "coefficient_kernel_controls": {
            "exact_unweighted_class_basis_gram": exact_kernel,
            "binary64_exponentially_weighted": weighted_kernels,
            "warning": (
                "these matrices are PSD by their Gram construction; their positivity "
                "is a control against mistaking tautological feature-kernel positivity "
                "for Weil positivity"
            ),
        },
        "c2_cross_term_controls": _c2_cross_term_controls(plus, minus),
    }


def _transform_bridge() -> Dict[str, object]:
    return {
        "common_operation": "convolution_is_diagonalized_by_a_character_transform",
        "finite_class_side": {
            "domain": "C2 form-class group at discriminant -20",
            "transform": "finite group Fourier/Hadamard character transform",
            "effect": "class convolution becomes multiplication in the +/- channels",
        },
        "weil_side": {
            "domain": "multiplicative positive reals",
            "transform": "Mellin transform",
            "correlation": "f_g(x)=integral g(xy)*conj(g(y)) dy",
            "transform_identity": (
                "F_g(s)=G(s)*conj(G(1-conj(s)))"
            ),
            "critical_line_fixed_point": (
                "if Re(s)=1/2 then 1-conj(s)=s and F_g(s)=abs(G(s))^2"
            ),
        },
        "dimensional_collapse_warning": (
            "replacing the full involutive cross pairing by diagonal magnitudes "
            "assumes the critical-line fixed-point property that the criterion is "
            "supposed to test"
        ),
        "unification_status": (
            "shared harmonic-analysis structure only; no graph-native map from the "
            "D=-20 class channels to the Riemann-zeta Weil test has been derived"
        ),
    }


def _claim_boundary() -> Dict[str, object]:
    return {
        "evidence_layer": "exact_theta_prefix_and_external_zero_side_weil_calibration",
        "claim_status": "finite_calibration_not_rh_evidence",
        "allowed_claim_language": [
            "The representation witnesses and theta coefficients through max_n are exact.",
            "The displayed theta values use a finite binary64 exponential sum with an explicit analytic tail-envelope formula.",
            "The D=-4 finite prefixes are consistent with the classical self-dual theta transform within the displayed analytic-tail plus non-rigorous binary64 roundoff guard.",
            "The full finite zero-side matrix is PSD for the synthetic critical-line control and has a negative direction for the injected off-line control when reported.",
            "The diagonal-only placebo can miss the injected off-line control because it discards the involutive cross terms.",
        ],
        "disallowed_claim_language": [
            "Do not claim that theta exponentials, Mellin transforms, zeta zeros, or Weil test functions are MoO runtime objects.",
            "Do not claim that a finite theta prefix proves its transformation law or analytic continuation.",
            "Do not claim that PSD on finitely many supplied critical-line points or a finite basis is evidence for RH.",
            "Do not claim that the injected off-line quartet is a zeta zero or evidence against RH.",
            "Do not identify the class-character theta channels with the Riemann-zeta Weil form.",
            "Do not discard cross terms or treat a nonnegative diagonal as a positivity test.",
        ],
    }


def _missing_obligations() -> List[Dict[str, object]]:
    return [
        {
            "obligation": "arithmetic_explicit_formula_matrix",
            "status": "missing",
            "requirement": (
                "evaluate the prime-power and archimedean sides for the same "
                "admissible test functions with rigorous truncation bounds"
            ),
        },
        {
            "obligation": "complete_zero_set_or_zero_free_replacement",
            "status": "missing",
            "requirement": (
                "a finite caller-supplied zero list cannot represent the full Weil sum"
            ),
        },
        {
            "obligation": "test_space_density",
            "status": "missing",
            "requirement": (
                "specify a topology on the constrained Weil test space and prove "
                "the log-Gaussian polynomial basis is dense in it"
            ),
        },
        {
            "obligation": "uniform_all_dimensions_positivity",
            "status": "missing",
            "requirement": (
                "finite PSD at one dimension and scale must be replaced by a proof "
                "for every finite combination in a dense family"
            ),
        },
        {
            "obligation": "rigorous_numerics",
            "status": "missing",
            "requirement": (
                "replace binary64 envelopes and eigensolvers with directed interval "
                "bounds before any certification language"
            ),
        },
        {
            "obligation": "graph_native_selection_rule",
            "status": "missing",
            "requirement": (
                "derive which theta or Weil test functions are selected by graph "
                "structure rather than choosing them externally"
            ),
        },
    ]


def _validate_limits(
    *,
    max_n: int,
    theta_t: Sequence[float],
    basis_dim: int,
    scale: float,
    psd_relative_tolerance: float,
    off_line_sigma: float,
    off_line_t: float,
    edge_limit: int,
    full_scan: bool,
) -> None:
    if int(max_n) < 1:
        raise ValueError("max_n must be >= 1")
    if int(max_n) > HARD_MAX_N:
        raise ValueError(f"max_n>{HARD_MAX_N} exceeds the hard report-size limit")
    if int(max_n) > SOFT_MAX_N and not full_scan:
        raise ValueError(
            f"max_n>{SOFT_MAX_N} exceeds the normal probe limit; "
            "pass --full-scan to acknowledge the larger report"
        )
    if not theta_t or len(theta_t) > HARD_MAX_THETA_SAMPLES:
        raise ValueError(
            f"theta_t must contain 1..{HARD_MAX_THETA_SAMPLES} samples"
        )
    if any(not math.isfinite(float(t)) or float(t) <= 0.0 for t in theta_t):
        raise ValueError("all theta t samples must be finite and > 0")
    if int(basis_dim) < 2:
        raise ValueError(
            "basis_dim must be >= 2 so off-diagonal entries are evaluated"
        )
    if int(basis_dim) > HARD_MAX_BASIS_DIM:
        raise ValueError(
            f"basis_dim>{HARD_MAX_BASIS_DIM} exceeds the hard eigensolver limit"
        )
    if int(basis_dim) > SOFT_MAX_BASIS_DIM and not full_scan:
        raise ValueError(
            f"basis_dim>{SOFT_MAX_BASIS_DIM} exceeds the normal probe limit; "
            "pass --full-scan to acknowledge the larger matrix"
        )
    if not math.isfinite(float(scale)) or float(scale) <= 0.0:
        raise ValueError("scale must be finite and > 0")
    if (
        not math.isfinite(float(psd_relative_tolerance))
        or float(psd_relative_tolerance) <= 0.0
    ):
        raise ValueError("psd_relative_tolerance must be finite and > 0")
    off_line_zero_quartet(sigma=off_line_sigma, t=off_line_t)
    if int(edge_limit) < 1:
        raise ValueError("edge_limit must be >= 1")


def theta_weil_probe(
    *,
    db_path: Path,
    max_n: int = DEFAULT_MAX_N,
    theta_t: Sequence[float] = DEFAULT_THETA_T,
    weil_basis_dim: int = DEFAULT_WEIL_BASIS_DIM,
    weil_scale: float = DEFAULT_WEIL_SCALE,
    psd_relative_tolerance: float = DEFAULT_PSD_RELATIVE_TOLERANCE,
    reference_ordinates: Sequence[float] = (),
    off_line_sigma: float = DEFAULT_OFF_LINE_SIGMA,
    off_line_t: float = DEFAULT_OFF_LINE_T,
    edge_limit: int = DEFAULT_EDGE_LIMIT,
    full_scan: bool = False,
) -> Dict[str, object]:
    samples = tuple(sorted(set(float(value) for value in theta_t)))
    references = tuple(sorted(set(float(value) for value in reference_ordinates)))
    _validate_limits(
        max_n=int(max_n),
        theta_t=samples,
        basis_dim=int(weil_basis_dim),
        scale=float(weil_scale),
        psd_relative_tolerance=float(psd_relative_tolerance),
        off_line_sigma=float(off_line_sigma),
        off_line_t=float(off_line_t),
        edge_limit=int(edge_limit),
        full_scan=bool(full_scan),
    )
    critical_line_zero_pairs(references)

    foundation = quadratic_form_probe(
        db_path=Path(db_path),
        max_n=int(max_n),
        edge_limit=int(edge_limit),
        full_scan=bool(full_scan),
    )
    graph_audit = foundation["graph_audit"]
    graph_rows = graph_audit["scalar_node_coverage"]["rows"]  # type: ignore[index]
    theta = _theta_layer(
        max_n=int(max_n),
        theta_t=samples,
        graph_rows=graph_rows,
    )

    critical_points = critical_line_zero_pairs((3.0, 5.0))
    off_line_points = off_line_zero_quartet(
        sigma=float(off_line_sigma),
        t=float(off_line_t),
    )
    critical_report = _matrix_report(
        critical_points,
        label="synthetic_critical_line_fixed_point_control",
        basis_dim=int(weil_basis_dim),
        scale=float(weil_scale),
        psd_relative_tolerance=float(psd_relative_tolerance),
        point_status="synthetic_not_zeta_zeros",
    )
    off_line_report = _matrix_report(
        off_line_points,
        label="synthetic_off_line_involution_control",
        basis_dim=int(weil_basis_dim),
        scale=float(weil_scale),
        psd_relative_tolerance=float(psd_relative_tolerance),
        point_status="synthetic_not_zeta_zeros",
    )
    pairing_fixture = _involution_pairing_fixture()
    if references:
        reference_report: Dict[str, object] = _matrix_report(
            critical_line_zero_pairs(references),
            label="caller_supplied_critical_line_reference_ordinates",
            basis_dim=int(weil_basis_dim),
            scale=float(weil_scale),
            psd_relative_tolerance=float(psd_relative_tolerance),
            point_status=(
                "caller_supplied_ordinates_not_independently_verified_as_zeta_zeros"
            ),
        )
        reference_report["interpretation"] = (
            "PSD is structurally forced by placing all supplied points on Re(s)=1/2; "
            "this does not verify the ordinates or test for omitted off-line zeros"
        )
    else:
        reference_report = {
            "status": "not_requested",
            "points": [],
            "is_evidence_for_rh": False,
        }

    transform_rows = theta["d4_poisson_transform_calibration"]  # type: ignore[assignment]
    return {
        "report_type": "theta_prefix_and_weil_zero_side_calibration",
        "config": {
            "max_n": int(max_n),
            "theta_t": list(samples),
            "weil_basis_dim": int(weil_basis_dim),
            "weil_scale": float(weil_scale),
            "psd_relative_tolerance": float(psd_relative_tolerance),
            "reference_ordinates": list(references),
            "off_line_sigma": float(off_line_sigma),
            "off_line_t": float(off_line_t),
            "edge_limit": int(edge_limit),
            "graph_stage_cutoff": int(max_n),
            "graph_stage_cutoff_rule": (
                "the quadratic-form foundation defaults its graph audit to max_n"
            ),
            "full_scan": bool(full_scan),
        },
        "claim_boundary": _claim_boundary(),
        "corpus": foundation["corpus"],
        "transform_bridge": _transform_bridge(),
        "theta_prefix_layer": theta,
        "weil_zero_side_calibration": {
            "criterion_orientation": {
                "weil_quadratic_sum": (
                    "Q(g)=sum_rho G(rho)*conj(G(1-conj(rho)))"
                ),
                "critical_line_reduction": (
                    "Q(g)=sum_rho abs(G(rho))^2 when every rho is fixed by "
                    "rho -> 1-conj(rho)"
                ),
                "arithmetic_explicit_formula_side_evaluated": False,
                "criterion_reference": (
                    "https://www.claymath.org/library/monographs/MPPc.pdf"
                ),
            },
            "synthetic_critical_line_control": critical_report,
            "synthetic_off_line_control": off_line_report,
            "exact_involution_pairing_fixture": pairing_fixture,
            "caller_supplied_reference": reference_report,
        },
        "graph_source_audit": {
            "foundation_summary": foundation["summary"],
            "scalar_and_named_witness_audit": graph_audit,
            "theta_or_weil_edge_type_exists": False,
            "interpretation": (
                "graph nodes and arithmetic edges support the finite scalar sources; "
                "exponential weights, theta summation, Mellin transforms, and Weil "
                "matrices remain external"
            ),
        },
        "missing_proof_obligations": _missing_obligations(),
        "summary": {
            "exact_theta_coefficient_prefix": True,
            "theta_sample_count": len(samples),
            "d4_transform_samples_within_analytic_tail_formula_value_binary64": sum(
                bool(row["residual_within_analytic_tail_only"])
                for row in transform_rows
            ),
            "d4_transform_samples_within_tail_formula_plus_roundoff_guard": sum(
                bool(row["residual_within_tail_plus_roundoff_guard"])
                for row in transform_rows
            ),
            "d4_transform_sample_count": len(transform_rows),
            "synthetic_critical_line_control_passes_finite_psd": critical_report[
                "eigendecomposition"
            ]["passes_finite_psd_test"],
            "synthetic_off_line_control_has_negative_direction": not off_line_report[
                "eigendecomposition"
            ]["passes_finite_psd_test"],
            "off_line_diagonal_only_placebo_would_pass": off_line_report[
                "diagonal_only_placebo"
            ]["would_pass_nonnegative_diagonal_test"],
            "off_line_same_point_gram_placebo_would_pass": off_line_report[
                "same_point_gram_placebo"
            ]["passes_finite_psd_test"],
            "exact_involution_pairing_fixture_passes": pairing_fixture[
                "control_passes"
            ],
            "caller_reference_status": reference_report.get(
                "point_status",
                reference_report.get("status"),
            ),
            "explicit_formula_arithmetic_side_evaluated": False,
            "test_space_density_proved": False,
            "riemann_hypothesis_proved": False,
        },
    }


def finite_float(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("must be finite")
    return value


def positive_float(raw: str) -> float:
    value = finite_float(raw)
    if value <= 0.0:
        raise argparse.ArgumentTypeError("must be > 0")
    return value


def parse_positive_float_csv(raw: str) -> List[float]:
    values: List[float] = []
    for part in str(raw).split(","):
        text = part.strip()
        if not text:
            continue
        value = positive_float(text)
        values.append(value)
    if not values:
        raise argparse.ArgumentTypeError("at least one positive value is required")
    return sorted(set(values))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build exact class-separated theta prefixes over a strict MoO graph "
            "and calibrate a finite zero-side Weil matrix with cross-term controls."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--max-n", type=positive_int, default=DEFAULT_MAX_N)
    parser.add_argument(
        "--theta-t",
        type=parse_positive_float_csv,
        default=list(DEFAULT_THETA_T),
        help="Comma-separated positive theta parameters.",
    )
    parser.add_argument(
        "--weil-basis-dim",
        type=positive_int,
        default=DEFAULT_WEIL_BASIS_DIM,
    )
    parser.add_argument("--weil-scale", type=positive_float, default=DEFAULT_WEIL_SCALE)
    parser.add_argument(
        "--psd-relative-tolerance",
        type=positive_float,
        default=DEFAULT_PSD_RELATIVE_TOLERANCE,
    )
    parser.add_argument(
        "--reference-ordinates",
        type=parse_positive_float_csv,
        help=(
            "Optional caller-supplied positive ordinates, placed on Re(s)=1/2. "
            "The probe does not verify that they are zeta zeros."
        ),
    )
    parser.add_argument(
        "--off-line-sigma",
        type=finite_float,
        default=DEFAULT_OFF_LINE_SIGMA,
    )
    parser.add_argument("--off-line-t", type=positive_float, default=DEFAULT_OFF_LINE_T)
    parser.add_argument("--edge-limit", type=positive_int, default=DEFAULT_EDGE_LIMIT)
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
    payload = theta_weil_probe(
        db_path=Path(args.db),
        max_n=int(args.max_n),
        theta_t=args.theta_t,
        weil_basis_dim=int(args.weil_basis_dim),
        weil_scale=float(args.weil_scale),
        psd_relative_tolerance=float(args.psd_relative_tolerance),
        reference_ordinates=args.reference_ordinates or (),
        off_line_sigma=float(args.off_line_sigma),
        off_line_t=float(args.off_line_t),
        edge_limit=int(args.edge_limit),
        full_scan=bool(args.full_scan),
    )
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_theta_weil_probe.v1",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
