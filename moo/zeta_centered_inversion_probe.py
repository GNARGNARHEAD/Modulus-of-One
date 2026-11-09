from __future__ import annotations

import argparse
import json
import math
from contextlib import closing
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from moo.circle_probe import unit_shell_point
from moo.research_utils import (
    connect_readonly,
    emit_json,
    positive_int,
    report_metadata,
    require_strict_alignment,
)
from moo.zeta_critical_probe import (
    HARD_MAX_HASSE_TERMS,
    CriticalGraphInspector,
    _compact_edge,
    _complex_calibration,
    _edge_summary,
    _ladder_report,
    _node_summary,
    approximation_payload,
    complex_input_payload,
    complex_payload,
    finite_float,
    fraction_payload,
    hasse_zeta,
    parse_ladder,
    positive_float,
    recommended_hasse_terms,
)


CENTER = Fraction(1, 2)
RADIUS = Fraction(1, 2)
DEFAULT_T = 14.134725141734693
DEFAULT_STABILITY_TOLERANCE = 1e-12
MAX_ABS_T = 100.0
MAX_SHELL_INTEGER = 64


def centered_u(s: complex) -> complex:
    """Return u=(s-1/2)/(1/2)=2s-1 for the fixed v1 normalization."""

    return 2.0 * complex(s) - 1.0


def centered_inversion_u(u: complex) -> complex:
    value = complex(u)
    if value == 0.0:
        raise ValueError("centered inversion is undefined at u=0")
    return -1.0 / value


def centered_inversion_s(s: complex) -> complex:
    """Return I(s)=(s-1)/(2s-1), conjugate to u -> -1/u."""

    value = complex(s)
    denominator = 2.0 * value - 1.0
    if denominator == 0.0:
        raise ValueError("centered inversion is undefined at s=1/2")
    return (value - 1.0) / denominator


def ratio_w(s: complex) -> complex:
    """Return the endpoint ratio w=(s-1)/s."""

    value = complex(s)
    if value == 0.0:
        raise ValueError("the ratio coordinate is undefined at s=0")
    return (value - 1.0) / value


def phase_inversion(phase: Fraction) -> Fraction:
    """Return the Q/Z phase action r -> 1/2-r (mod 1)."""

    raw = Fraction(1, 2) - Fraction(phase)
    return Fraction(raw.numerator % raw.denominator, raw.denominator)


def _default_ladder(terms: int) -> List[int]:
    count = int(terms)
    return sorted(
        {
            max(1, count // 2),
            max(1, count - 16),
            max(1, count - 8),
            max(1, count - 4),
            count,
        }
    )


def _evaluation(
    s: complex,
    *,
    hasse_terms: int,
    ladder_terms: Sequence[int],
    near_zero_tolerance: float,
    stability_tolerance: float,
) -> Dict[str, object]:
    approximation = hasse_zeta(s, int(hasse_terms))
    payload = approximation_payload(approximation)
    ladder = _ladder_report(s, ladder_terms)
    residual = abs(approximation.zeta) if approximation.zeta is not None else None
    changes = [
        float(row["change_from_previous_zeta"])
        for row in ladder["rows"]  # type: ignore[index]
        if row["change_from_previous_zeta"] is not None
    ]
    terminal_changes = changes[-2:]
    stability_threshold = float(stability_tolerance) * (
        1.0 + (float(residual) if residual is not None else 0.0)
    )
    stable = len(terminal_changes) == 2 and all(
        change <= stability_threshold for change in terminal_changes
    )
    below = residual is not None and residual <= float(near_zero_tolerance)
    recommended_terms = recommended_hasse_terms(s.imag)
    preflight_ok = int(hasse_terms) >= int(recommended_terms)
    roundoff_proxy = payload["binary64_roundoff_proxy"]
    roundoff_below_tolerance = bool(
        roundoff_proxy is not None
        and float(roundoff_proxy) <= float(near_zero_tolerance)
    )
    zeta_payload = payload["zeta"]
    if isinstance(zeta_payload, dict):
        zeta_payload["phase_reliability"] = (
            "undefined_below_configured_zero_tolerance"
            if below
            else "ordinary_binary64_phase"
        )
        if below:
            zeta_payload["phase_turns"] = None
    payload.update(
        {
            "cutoff_stability": ladder,
            "numeric_preflight": {
                "empirical_recommended_hasse_terms": int(recommended_terms),
                "configured_hasse_terms": int(hasse_terms),
                "configured_meets_empirical_recommendation": bool(preflight_ok),
                "status": "heuristic_from_binary64_calibration_not_an_error_bound",
            },
            "diagnostic": {
                "absolute_residual": float(residual) if residual is not None else None,
                "near_zero_tolerance": float(near_zero_tolerance),
                "below_near_zero_tolerance": bool(below),
                "stability_tolerance": float(stability_tolerance),
                "stability_absolute_threshold": stability_threshold,
                "two_terminal_cutoff_changes": terminal_changes,
                "two_terminal_changes_below_threshold": bool(stable),
                "roundoff_proxy_below_residual_tolerance": (
                    roundoff_below_tolerance
                ),
                "certified_zero": False,
                "certification_status": "not_attempted_no_interval_error_bound",
            },
        }
    )
    return payload


def _exact_geometry(source: complex) -> Dict[str, object]:
    image = centered_inversion_s(source)
    u = centered_u(source)
    image_u = centered_u(image)
    w = ratio_w(source)
    image_w = ratio_w(image)
    involution_error = abs(centered_inversion_s(image) - source)
    u_conjugacy_error = abs(image_u - centered_inversion_u(u))
    w_action_error = abs(image_w + 1.0 / w)
    modulus_error = abs(abs(image_u) - 1.0 / abs(u))
    height_product_error = abs(source.imag * image.imag - 0.25)
    fixed_plus = 0.5 + 0.5j
    fixed_minus = 0.5 - 0.5j
    fixed_error = max(
        abs(centered_inversion_s(fixed_plus) - fixed_plus),
        abs(centered_inversion_s(fixed_minus) - fixed_minus),
    )
    tolerance = 1e-12
    errors = {
        "s_involution_error": float(involution_error),
        "u_conjugacy_error": float(u_conjugacy_error),
        "w_action_error": float(w_action_error),
        "modulus_reciprocity_error": float(modulus_error),
        "critical_line_height_product_error": float(height_product_error),
        "fixed_point_error": float(fixed_error),
    }
    return {
        "normalization": {
            "center": fraction_payload(CENTER),
            "radius": fraction_payload(RADIUS),
            "u_formula": "u=(s-1/2)/(1/2)=2s-1",
            "w_formula": "w=(s-1)/s",
            "inversion_u": "J(u)=-1/u",
            "inversion_s": "I(s)=(s-1)/(2s-1)",
        },
        "exact_identities": {
            "modulus": "abs(J(u))=1/abs(u)",
            "pointwise_fixed_units": "u=+i and u=-i",
            "s_fixed_points": "s=1/2+i/2 and s=1/2-i/2",
            "critical_line_action": (
                "the finite punctured line s=1/2+it, t!=0, maps to itself by "
                "t->1/(4t); s=1/2 exchanges with projective infinity"
            ),
            "ratio_action": "w(I(s))=-1/w(s)",
            "functional_reflection_ratio_action": "w(1-s)=1/w(s)",
            "endpoint_exchange": "0<->1 and 1/2<->infinity",
        },
        "matrix_lift": {
            "u_matrix": [[0, -1], [1, 0]],
            "s_matrix": [[1, -1], [2, -1]],
            "u_matrix_square": [[-1, 0], [0, -1]],
            "s_matrix_square": [[-1, 0], [0, -1]],
            "u_matrix_fourth_power": [[1, 0], [0, 1]],
            "projective_order": 2,
            "linear_lift_order": 4,
            "representative_status": (
                "order four belongs to the chosen real determinant-one representative; "
                "ordinary matrix order is not invariant under arbitrary complex scalar rescaling"
            ),
            "reading": (
                "The order-four homogeneous lift projects to an involution because "
                "a matrix and its negative define the same Mobius map."
            ),
        },
        "coordinate_loci": {
            "cayley_relation": "w=(u-1)/(u+1) and u=(1+w)/(1-w)",
            "u_unit_shell_in_s_plane": "abs(s-1/2)=1/2",
            "u_unit_shell_in_w_plane": "Re(w)=0, including the projective infinity endpoint",
            "w_unit_shell_in_s_plane": (
                "Re(s)=1/2 in the extended plane; the finite Mobius action is "
                "defined on the punctured line s!=1/2"
            ),
            "w_unit_shell_in_u_plane": "Re(u)=0, including the projective infinity endpoint",
            "intersection_in_s_plane": "s=1/2+i/2 and s=1/2-i/2",
            "warning": (
                "The centered circle and critical line are different invariant loci; "
                "modulus-one is coordinate-dependent, not Mobius-invariant language."
            ),
        },
        "source": {
            "s": complex_input_payload(source),
            "u": complex_payload(u),
            "w": complex_payload(w),
        },
        "image": {
            "s": complex_input_payload(image),
            "u": complex_payload(image_u),
            "w": complex_payload(image_w),
        },
        "binary64_identity_errors": errors,
        "binary64_identity_tolerance": tolerance,
        "classification": (
            "exact_centered_geometry_verified"
            if all(value <= tolerance for value in errors.values())
            else "binary64_identity_check_failed"
        ),
    }


def _domain_separation() -> Dict[str, object]:
    c4 = [
        (Fraction(0, 1), "1"),
        (Fraction(1, 4), "i"),
        (Fraction(1, 2), "-1"),
        (Fraction(3, 4), "-i"),
    ]
    phase_rows = [
        {
            "phase": fraction_payload(phase),
            "unit_label": label,
            "image_phase": fraction_payload(phase_inversion(phase)),
        }
        for phase, label in c4
    ]
    example_t = Fraction(1, 2)
    example_point = unit_shell_point(example_t)
    example_image = unit_shell_point(1 / example_t)
    return {
        "q_mod_z_phase_model": {
            "projection": "r -> exp(2*pi*i*r)",
            "coordinate_status": (
                "the four units are landmarks in the normalized external w/U(1) "
                "plane; the raw s-plane map does not preserve the raw set {1,i,-1,-i}"
            ),
            "centered_inversion_action": "r -> 1/2-r mod 1",
            "c4_action": phase_rows,
            "action_cycle_type": "(1 -1)(i)(-i)",
            "quarter_turn_cycle_type": "(1 i -1 -i)",
            "group_homomorphism": False,
            "order_change_example": "phase 1/3 has order 3 and maps to phase 1/6 of order 6",
            "warning": (
                "Centered inversion preserves the C4 set but is not the existing "
                "quarter-turn C4 action."
            ),
        },
        "rational_coordinate_shell": {
            "parameterization": (
                "U(t)=((1-t^2)/(1+t^2)) + i*(2t/(1+t^2))"
            ),
            "action": "-1/U(t)=U(1/t)",
            "projective_endpoints_and_fixed_parameters": {
                "endpoint_pair": "t=0 <-> infinity projects to 1 <-> -1",
                "fixed_plus": "t=1 projects to i",
                "fixed_minus": "t=-1 projects to -i",
            },
            "example": {
                "t": fraction_payload(example_t),
                "U_t": [
                    fraction_payload(example_point[0]),
                    fraction_payload(example_point[1]),
                ],
                "reciprocal_t": fraction_payload(1 / example_t),
                "U_reciprocal_t": [
                    fraction_payload(example_image[0]),
                    fraction_payload(example_image[1]),
                ],
                "root_of_unity": False,
                "reason": (
                    "3/5+4i/5 is not an algebraic integer, hence cannot be a root of unity."
                ),
            },
        },
        "set_relation": {
            "rational_phase_roots_of_unity": "exp(2*pi*i*(Q/Z))",
            "rational_coordinate_points": "U(Q union {infinity})",
            "both_dense_on_unit_circle": True,
            "sets_equal": False,
            "exact_intersection": ["1", "i", "-1", "-i"],
            "reading": (
                "The inversion preserves both rational skeletons separately; "
                "generic rational-coordinate shell points are not roots of unity."
            ),
        },
    }


def _shell_graph_audit(
    inspector: CriticalGraphInspector,
    *,
    shell_max_integer: int,
) -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    direct_edges: List[Dict[str, object]] = []
    reverse_edges: List[Dict[str, object]] = []
    opposition_edges: List[Dict[str, object]] = []
    parameter_nodes: List[Dict[str, object]] = []
    component_nodes: List[Dict[str, object]] = []
    for integer in range(1, int(shell_max_integer) + 1):
        t = Fraction(integer, 1)
        reciprocal_t = Fraction(1, integer)
        x, y = unit_shell_point(t)
        reciprocal_x, reciprocal_y = unit_shell_point(reciprocal_t)
        direct = _compact_edge(
            inspector.edge(
                left=1,
                op="/",
                right=integer,
                result=reciprocal_t,
                allow_commuted=False,
                claim_id="direct_unit_fraction",
                relation=f"1 / {integer} -> 1/{integer}",
            )
        )
        reverse = _compact_edge(
            inspector.edge(
                left=1,
                op="/",
                right=reciprocal_t,
                result=integer,
                allow_commuted=False,
                claim_id="reverse_reciprocal_parameter",
                relation=f"1 / (1/{integer}) -> {integer}",
            )
        )
        opposition = _compact_edge(
            inspector.edge(
                left=reciprocal_x,
                op="*",
                right=-1,
                result=x,
                allow_commuted=True,
                claim_id="shell_real_component_opposition",
                relation=(
                    f"-1 * {fraction_payload(reciprocal_x)['frac']} "
                    f"-> {fraction_payload(x)['frac']}"
                ),
            )
        )
        parameter_pair = [inspector.node(t), inspector.node(reciprocal_t)]
        components = [
            inspector.node(x),
            inspector.node(y),
            inspector.node(reciprocal_x),
            inspector.node(reciprocal_y),
        ]
        parameter_nodes.extend(parameter_pair)
        component_nodes.extend(components)
        direct_edges.append(direct)
        reverse_edges.append(reverse)
        opposition_edges.append(opposition)
        rows.append(
            {
                "n": integer,
                "t": fraction_payload(t),
                "reciprocal_t": fraction_payload(reciprocal_t),
                "U_n": {
                    "real": fraction_payload(x),
                    "imag": fraction_payload(y),
                },
                "U_reciprocal_n": {
                    "real": fraction_payload(reciprocal_x),
                    "imag": fraction_payload(reciprocal_y),
                },
                "exact_shell_identity": bool(
                    reciprocal_x == -x and reciprocal_y == y
                ),
                "parameter_pair_present": all(
                    bool(node["present"]) for node in parameter_pair
                ),
                "both_shell_points_component_nodes_present": all(
                    bool(node["present"]) for node in components
                ),
                "direct_parameter_witness_and_both_shell_points_present": bool(
                    direct["present"]
                    and all(bool(node["present"]) for node in components)
                ),
                "parameter_nodes": parameter_pair,
                "shell_component_nodes": components,
                "direct_unit_fraction_edge": direct,
                "reverse_parameter_edge": reverse,
                "real_component_opposition_edge": opposition,
                "runtime_complex_pair_or_mobius_edge": False,
            }
        )

    direct_summary = _edge_summary(direct_edges)
    reverse_summary = _edge_summary(reverse_edges)
    opposition_summary = _edge_summary(opposition_edges)
    aligned_rows = [
        row
        for row in rows
        if bool(row["direct_parameter_witness_and_both_shell_points_present"])
    ]
    return {
        "range": {"n_min": 1, "n_max": int(shell_max_integer)},
        "rows": rows,
        "summary": {
            "all_external_shell_identities_exact": all(
                bool(row["exact_shell_identity"]) for row in rows
            ),
            "parameter_nodes": _node_summary(parameter_nodes),
            "shell_component_nodes": _node_summary(component_nodes),
            "direct_unit_fraction_edges": direct_summary,
            "reverse_parameter_edges": reverse_summary,
            "real_component_opposition_edges": opposition_summary,
            "direct_witness_and_both_shell_points_present_count": len(aligned_rows),
            "direct_witness_and_both_shell_points_present_n": [
                int(row["n"]) for row in aligned_rows
            ],
            "co_presence_is_transformation_witness": False,
            "runtime_pair_projection_edges": 0,
            "runtime_mobius_transformation_edges": 0,
            "graph_evidence_depends_on_zeta_target": False,
        },
        "interaction_classification": (
            "external_projection_only_insufficient_repeated_graph_witnesses"
        ),
        "reading": (
            "The current strict positive-spine corpus can witness the rational "
            "precursor 1/n. Under its aligned operand policy, the reciprocal landing "
            "and shell components are inspected rather than reused as operands, and "
            "this runtime has no complex-pair or Mobius edge type."
        ),
    }


def _meta_value(conn: object, key: str) -> Optional[str]:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()  # type: ignore[attr-defined]
    return str(row["value"]) if row is not None else None


def _corpus_payload(conn: object, alignment: Dict[str, object]) -> Dict[str, object]:
    latest = conn.execute(  # type: ignore[attr-defined]
        "SELECT * FROM stages ORDER BY stage DESC LIMIT 1"
    ).fetchone()
    config_raw = _meta_value(conn, "config_json")
    try:
        config: object = json.loads(config_raw) if config_raw is not None else None
    except json.JSONDecodeError:
        config = config_raw
    return {
        "schema_version": _meta_value(conn, "schema_version"),
        "config": config,
        "latest_stage": dict(latest) if latest is not None else None,
        "nodes": int(conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()["n"]),  # type: ignore[attr-defined]
        "edges": int(conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()["n"]),  # type: ignore[attr-defined]
        "alignment": alignment,
        "access_mode": "sqlite_read_only",
    }


def _analytic_obstruction(center_evaluation: Dict[str, object]) -> Dict[str, object]:
    center_residual = center_evaluation["diagnostic"]["absolute_residual"]  # type: ignore[index]
    return {
        "classification": "global_fixed_radius_zero_set_symmetry_analytically_obstructed",
        "fixed_radius": fraction_payload(RADIUS),
        "critical_line_height_action": "t -> 1/(4t)",
        "argument": [
            "The nontrivial zeta zeros include an unbounded sequence of critical-line heights.",
            "A fixed-radius centered inversion would send those heights to a sequence tending to 0.",
            "The inversion is injective, so invariance would give distinct transformed zeros accumulating at s=1/2.",
            "Zeta is analytic and nonzero at s=1/2, so the identity theorem forbids that accumulation.",
        ],
        "center_nonzero_analytic_reason": (
            "eta(1/2) is a positive alternating-series sum and "
            "zeta(1/2)=eta(1/2)/(1-sqrt(2)) is therefore nonzero"
        ),
        "center_binary64_residual_control": center_residual,
        "scope": (
            "This rules out global invariance of the zeta zero set under any one "
            "fixed positive centered radius; it does not challenge the exact coordinate geometry."
        ),
        "transformed_function_caveat": {
            "function": "s -> zeta(I_R(s))",
            "center_status": (
                "s=1/2 becomes an essential singularity because I_R has a pole "
                "there and zeta has an essential singularity at infinity"
            ),
            "zero_accumulation_status": (
                "zeros of the transformed function may accumulate at that singularity"
            ),
            "interpretation": (
                "this is a new representation of zeta after precomposition, not a "
                "symmetry or permutation of the original zeta zero set"
            ),
        },
    }


def _claim_boundary() -> Dict[str, object]:
    return {
        "evidence_layer": "exact_external_geometry_plus_read_only_strict_graph_audit",
        "allowed_claim_language": [
            "The centered Mobius identities and rational shell identities hold exactly externally.",
            "The strict graph may witness rational precursor edges and component nodes.",
            "A finite Hasse calculation can reject preservation of the supplied near-zero at its centered-inversion image.",
            "A fixed-radius global zeta-zero symmetry is analytically obstructed by zero accumulation at the center.",
        ],
        "disallowed_claim_language": [
            "Do not claim that the current strict positive-spine runtime contains complex numbers, U(1), Mobius maps, or zeta.",
            "Do not identify the centered involution with the quarter-turn C4 action; only the four-point set is shared.",
            "Do not identify all rational-coordinate shell points with roots of unity.",
            "Do not treat the exact reformulation abs(w(rho))=1 as evidence for RH; it is equivalent to Re(rho)=1/2.",
            "Do not promote a formal interaction branch without repeated graph-native construction edges and a predictive test.",
        ],
    }


def zeta_centered_inversion_probe(
    *,
    db_path: Path,
    t: float = DEFAULT_T,
    hasse_terms: int = 64,
    ladder_terms: Optional[Sequence[int]] = None,
    near_zero_tolerance: float = 1e-10,
    stability_tolerance: float = DEFAULT_STABILITY_TOLERANCE,
    shell_max_integer: int = 12,
    edge_limit: int = 4,
    target_label: Optional[str] = "first_nontrivial_zero_reference",
) -> Dict[str, object]:
    numeric = [t, near_zero_tolerance, stability_tolerance]
    if not all(math.isfinite(float(value)) for value in numeric):
        raise ValueError("all numeric inputs must be finite")
    if float(t) == 0.0:
        raise ValueError("t must be nonzero because I is singular at s=1/2")
    if abs(float(t)) > MAX_ABS_T:
        raise ValueError(f"abs(t)>{MAX_ABS_T:g} exceeds the calibrated domain")
    if int(hasse_terms) < 1 or int(hasse_terms) > HARD_MAX_HASSE_TERMS:
        raise ValueError(f"hasse_terms must be in 1..{HARD_MAX_HASSE_TERMS}")
    if float(near_zero_tolerance) <= 0.0:
        raise ValueError("near_zero_tolerance must be > 0")
    if float(stability_tolerance) <= 0.0:
        raise ValueError("stability_tolerance must be > 0")
    if int(shell_max_integer) < 1 or int(shell_max_integer) > MAX_SHELL_INTEGER:
        raise ValueError(f"shell_max_integer must be in 1..{MAX_SHELL_INTEGER}")
    if int(edge_limit) < 2:
        raise ValueError("edge_limit must be >= 2")
    checkpoints = (
        sorted(set(int(value) for value in ladder_terms))
        if ladder_terms is not None
        else _default_ladder(int(hasse_terms))
    )
    if not checkpoints or any(value < 1 for value in checkpoints):
        raise ValueError("ladder_terms must contain positive integers")
    if max(checkpoints) > int(hasse_terms):
        raise ValueError("ladder_terms must not exceed hasse_terms")
    if int(hasse_terms) not in checkpoints:
        checkpoints.append(int(hasse_terms))
        checkpoints.sort()

    source = complex(0.5, float(t))
    reflection = 1.0 - source
    image = centered_inversion_s(source)
    points = {
        "source": source,
        "functional_reflection": reflection,
        "centered_inversion_image": image,
        "center_control": 0.5 + 0.0j,
        "fixed_point_plus": 0.5 + 0.5j,
        "fixed_point_minus": 0.5 - 0.5j,
    }
    evaluations = {
        name: _evaluation(
            point,
            hasse_terms=int(hasse_terms),
            ladder_terms=checkpoints,
            near_zero_tolerance=float(near_zero_tolerance),
            stability_tolerance=float(stability_tolerance),
        )
        for name, point in points.items()
    }
    source_zeta = hasse_zeta(source, int(hasse_terms)).zeta
    reflection_zeta = hasse_zeta(reflection, int(hasse_terms)).zeta
    conjugation_error = (
        abs(reflection_zeta - source_zeta.conjugate())
        if source_zeta is not None and reflection_zeta is not None
        else None
    )

    with closing(connect_readonly(Path(db_path))) as conn:
        alignment = require_strict_alignment(conn)
        corpus = _corpus_payload(conn, alignment)
        latest = corpus["latest_stage"]
        corpus_stage = int(latest["stage"]) if isinstance(latest, dict) else None
        inspector = CriticalGraphInspector(
            conn,
            corpus_stage=corpus_stage,
            edge_limit=int(edge_limit),
        )
        complex_calibration = _complex_calibration(inspector)
        graph_audit = _shell_graph_audit(
            inspector,
            shell_max_integer=int(shell_max_integer),
        )

    source_diagnostic = evaluations["source"]["diagnostic"]
    reflection_diagnostic = evaluations["functional_reflection"]["diagnostic"]
    image_diagnostic = evaluations["centered_inversion_image"]["diagnostic"]
    source_near = bool(source_diagnostic["below_near_zero_tolerance"])
    source_preflight = bool(
        evaluations["source"]["numeric_preflight"][
            "configured_meets_empirical_recommendation"
        ]
    )
    source_roundoff_resolved = bool(
        source_diagnostic["roundoff_proxy_below_residual_tolerance"]
    )
    source_stable = bool(
        source_diagnostic["two_terminal_changes_below_threshold"]
    )
    reflection_near = bool(
        reflection_diagnostic["below_near_zero_tolerance"]
    )
    reflection_stable = bool(
        reflection_diagnostic["two_terminal_changes_below_threshold"]
    )
    image_near = bool(image_diagnostic["below_near_zero_tolerance"])
    image_preflight = bool(
        evaluations["centered_inversion_image"]["numeric_preflight"][
            "configured_meets_empirical_recommendation"
        ]
    )
    image_stable = bool(
        image_diagnostic["two_terminal_changes_below_threshold"]
    )
    conjugation_tolerance = float(stability_tolerance) * (
        1.0 + (float(abs(source_zeta)) if source_zeta is not None else 0.0)
    )
    reflection_control_passes = bool(
        conjugation_error is not None
        and conjugation_error <= conjugation_tolerance
        and reflection_near == source_near
        and reflection_stable == source_stable
    )
    if source_near and not source_preflight:
        point_classification = (
            "source_small_residual_below_empirical_term_recommendation"
        )
    elif source_near and not source_roundoff_resolved:
        point_classification = "source_small_residual_not_below_roundoff_proxy"
    elif (
        source_near
        and source_stable
        and reflection_control_passes
        and not image_near
        and image_stable
        and image_preflight
    ):
        point_classification = (
            "supplied_near_zero_not_preserved_by_centered_inversion"
        )
    elif source_near and source_stable and not reflection_control_passes:
        point_classification = "functional_reflection_positive_control_failed"
    elif source_near and source_stable and not image_near and not image_stable:
        point_classification = (
            "centered_inversion_image_not_stable_at_configured_cutoffs"
        )
    elif source_near and source_stable and not image_near and not image_preflight:
        point_classification = (
            "centered_inversion_image_below_empirical_term_recommendation"
        )
    elif source_near and not source_stable:
        point_classification = (
            "supplied_small_residual_not_preserved_but_cutoff_stability_incomplete"
        )
    elif source_near and image_near:
        point_classification = "both_points_below_tolerance_not_a_symmetry_proof"
    else:
        point_classification = "source_not_resolved_as_near_zero_at_configured_cutoff"
    point_symmetry_supported: Optional[bool] = None
    if point_classification == (
        "supplied_near_zero_not_preserved_by_centered_inversion"
    ):
        point_symmetry_supported = False

    geometry = _exact_geometry(source)
    obstruction = _analytic_obstruction(evaluations["center_control"])
    return {
        "report_type": "zeta_centered_inversion_external_probe",
        "config": {
            "center": "1/2",
            "radius": "1/2",
            "t": float(t),
            "target_label": target_label,
            "hasse_terms": int(hasse_terms),
            "ladder_terms": checkpoints,
            "near_zero_tolerance": float(near_zero_tolerance),
            "stability_tolerance": float(stability_tolerance),
            "shell_max_integer": int(shell_max_integer),
            "edge_limit": int(edge_limit),
            "read_only": True,
        },
        "claim_boundary": _claim_boundary(),
        "corpus": corpus,
        "exact_centered_geometry": geometry,
        "unit_shell_domain_separation": _domain_separation(),
        "complex_calibration": complex_calibration,
        "graph_shell_audit": graph_audit,
        "zeta_evaluations": {
            "method": (
                "finite external binary64 Hasse/eta approximation; cutoff "
                "comparisons are empirical and are not rigorous error bounds"
            ),
            "target_label": target_label,
            "points": evaluations,
            "functional_reflection_conjugation_error": (
                float(conjugation_error) if conjugation_error is not None else None
            ),
            "functional_reflection_on_critical_line_control": {
                "meaning": (
                    "at sigma=1/2, s->1-s equals complex conjugation; this is a "
                    "conjugation control, not an independent evaluation of the full functional equation"
                ),
                "conjugation_tolerance": conjugation_tolerance,
                "source_and_reflection_near_zero_status_match": (
                    reflection_near == source_near
                ),
                "source_and_reflection_cutoff_stability_status_match": (
                    reflection_stable == source_stable
                ),
                "passes": reflection_control_passes,
            },
            "centered_inversion_image_cutoff_stable": image_stable,
            "pointwise_classification": point_classification,
            "zeta_inversion_symmetry_supported_at_supplied_point": (
                point_symmetry_supported
            ),
        },
        "analytic_obstruction": obstruction,
        "summary": {
            "exact_geometry": geometry["classification"],
            "graph_interaction": graph_audit["interaction_classification"],
            "supplied_point": point_classification,
            "global_zeta_zero_set": obstruction["classification"],
            "formal_branch_status": (
                "candidate_centered_reciprocal_shell_lens_not_promoted"
            ),
            "rh_status": (
                "abs(w(rho))=1 is an exact restatement of critical-line "
                "membership, not new evidence for the Riemann hypothesis"
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the fixed R=1/2 centered inversion as exact external geometry, "
            "strict-graph rational evidence, and a proposed zeta-zero-symmetry control."
        )
    )
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--t", type=finite_float, default=DEFAULT_T)
    parser.add_argument("--hasse-terms", type=positive_int, default=64)
    parser.add_argument("--ladder-terms", type=parse_ladder)
    parser.add_argument(
        "--near-zero-tolerance", type=positive_float, default=1e-10
    )
    parser.add_argument(
        "--stability-tolerance",
        type=positive_float,
        default=DEFAULT_STABILITY_TOLERANCE,
    )
    parser.add_argument("--shell-max-integer", type=positive_int, default=12)
    parser.add_argument("--edge-limit", type=positive_int, default=4)
    parser.add_argument(
        "--target-label", default="first_nontrivial_zero_reference"
    )
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--write",
        type=Path,
        help="Also write the JSON report. Existing files are never overwritten.",
    )
    parser.add_argument("--experiment-id")
    parser.add_argument("--with-checksums", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    payload = zeta_centered_inversion_probe(
        db_path=Path(args.db),
        t=float(args.t),
        hasse_terms=int(args.hasse_terms),
        ladder_terms=args.ladder_terms,
        near_zero_tolerance=float(args.near_zero_tolerance),
        stability_tolerance=float(args.stability_tolerance),
        shell_max_integer=int(args.shell_max_integer),
        edge_limit=int(args.edge_limit),
        target_label=str(args.target_label) if args.target_label else None,
    )
    if args.experiment_id:
        payload["experiment_id"] = str(args.experiment_id)
    payload["report_metadata"] = report_metadata(
        tool_path=Path(__file__),
        db_path=Path(args.db),
        argv=argv,
        schema_version="moo_zeta_centered_inversion_probe.v1",
        include_checksums=bool(args.write or args.with_checksums),
    )
    emit_json(payload, pretty=bool(args.pretty), write=args.write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
