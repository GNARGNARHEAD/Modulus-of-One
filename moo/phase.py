from __future__ import annotations

from fractions import Fraction
from typing import Dict, Sequence, Tuple, Union

from moo.graph_corpus import format_key, normalize_key


Key = Tuple[int, int]
Value = Union[Fraction, int]
DEFAULT_PHASE_FAMILY_MATERIALIZATION_LIMIT = 512


def _fraction(value: Value) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    raise TypeError("phase values must be int or Fraction")


def _integer_scalar(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("phase scalars must be integers")
    return int(value)


def _materialization_limit(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("materialization_limit must be an integer")
    limit = int(value)
    if limit < 0:
        raise ValueError("materialization_limit must be >= 0")
    return limit


def fraction_key(value: Value) -> Key:
    fraction = _fraction(value)
    return normalize_key(int(fraction.numerator), int(fraction.denominator))


def fraction_payload(value: Value) -> Dict[str, object]:
    key = fraction_key(value)
    return {
        "frac": format_key(key),
        "p": int(key[0]),
        "q": int(key[1]),
    }


def phase_fraction(value: Value) -> Fraction:
    """Return the canonical representative in Q intersect [0, 1)."""

    fraction = _fraction(value)
    denominator = int(fraction.denominator)
    return Fraction(int(fraction.numerator) % denominator, denominator)


def phase_key(value: Value) -> Key:
    """Return the normalized key of the canonical Q/Z phase representative."""

    return fraction_key(phase_fraction(value))


def additive_return_order(value: Value) -> int:
    """Return the additive order of a rational phase in Q/Z."""

    phase = phase_fraction(value)
    return 1 if phase == 0 else int(phase.denominator)


def phase_payload(value: Value) -> Dict[str, object]:
    phase = phase_fraction(value)
    payload = fraction_payload(phase)
    payload.update(
        {
            "is_identity": phase == 0,
            "u1_point": (
                "1"
                if phase == 0
                else f"exp(2*pi*i*{format_key(phase_key(phase))})"
            ),
            "additive_return_order": additive_return_order(phase),
        }
    )
    return payload


def circular_length(value: Value) -> Fraction:
    """Exact shortest distance in turns from a rational phase to identity."""

    phase = phase_fraction(value)
    return min(phase, Fraction(1, 1) - phase)


def circular_distance(left: Value, right: Value) -> Fraction:
    """Shortest-arc R/Z distance in turns, restricted to Q/Z and pulled back to Q."""

    return circular_length(_fraction(left) - _fraction(right))


def phase_add(left: Value, right: Value) -> Fraction:
    """Add two rational phases in the quotient group Q/Z."""

    return phase_fraction(_fraction(left) + _fraction(right))


def phase_subtract(left: Value, right: Value) -> Fraction:
    """Subtract two rational phases in the quotient group Q/Z."""

    return phase_fraction(_fraction(left) - _fraction(right))


def phase_scale(scalar: int, value: Value) -> Fraction:
    """Apply the retained-integer action mu_n([x]) = [n*x] on Q/Z."""

    n = _integer_scalar(scalar)
    return phase_fraction(n * _fraction(value))


def phase_scale_kernel(
    scalar: int,
    *,
    materialization_limit: int = DEFAULT_PHASE_FAMILY_MATERIALIZATION_LIMIT,
) -> Dict[str, object]:
    """Describe ker(mu_n), materializing its finite members within the cap."""

    n = _integer_scalar(scalar)
    limit = _materialization_limit(materialization_limit)
    if n == 0:
        return {
            "scalar": 0,
            "kind": "all_phases",
            "finite": False,
            "cardinality": None,
            "materialization_limit": limit,
            "materialized": False,
            "kernel_points": None,
            "interpretation": "ker(mu_0) is all of Q/Z",
        }

    cardinality = abs(n)
    materialized = cardinality <= limit
    points = (
        [phase_payload(Fraction(index, cardinality)) for index in range(cardinality)]
        if materialized
        else None
    )
    return {
        "scalar": n,
        "kind": "finite",
        "finite": True,
        "cardinality": cardinality,
        "materialization_limit": limit,
        "materialized": materialized,
        "kernel_points": points,
        "points_omitted_reason": (
            None
            if materialized
            else f"kernel cardinality exceeds materialization_limit={limit}"
        ),
        "interpretation": "ker(mu_n) = {k/abs(n) mod 1 : 0 <= k < abs(n)}",
    }


def phase_scale_preimages(
    scalar: int,
    target: Value,
    *,
    materialization_limit: int = DEFAULT_PHASE_FAMILY_MATERIALIZATION_LIMIT,
) -> Dict[str, object]:
    """Describe all y in Q/Z satisfying mu_n(y) = target."""

    n = _integer_scalar(scalar)
    limit = _materialization_limit(materialization_limit)
    target_phase = phase_fraction(target)
    base = {
        "scalar": n,
        "target_phase": phase_payload(target_phase),
        "materialization_limit": limit,
    }
    if n == 0:
        if target_phase == 0:
            return {
                **base,
                "kind": "all_phases",
                "finite": False,
                "cardinality": None,
                "materialized": False,
                "preimages": None,
                "interpretation": "mu_0(y) = 0 for every phase y",
            }
        return {
            **base,
            "kind": "empty",
            "finite": True,
            "cardinality": 0,
            "materialized": True,
            "preimages": [],
            "interpretation": "mu_0 has no nonidentity value in its image",
        }

    cardinality = abs(n)
    materialized = cardinality <= limit
    preimages = None
    if materialized:
        preimages = []
        seen = set()
        for branch_index in range(cardinality):
            root = phase_fraction(Fraction(target_phase + branch_index, n))
            if root in seen:
                raise AssertionError("integer phase scaling produced duplicate roots")
            seen.add(root)
            if phase_scale(n, root) != target_phase:
                raise AssertionError("integer phase scaling produced an invalid root")
            preimages.append(
                {
                    "branch_index": branch_index,
                    "phase": phase_payload(root),
                }
            )
    return {
        **base,
        "kind": "finite",
        "finite": True,
        "cardinality": cardinality,
        "materialized": materialized,
        "preimages": preimages,
        "preimages_omitted_reason": (
            None
            if materialized
            else f"preimage cardinality exceeds materialization_limit={limit}"
        ),
        "single_valued": cardinality == 1,
        "interpretation": (
            "The fibre is one coset of ker(mu_n); division by n is a relation, "
            "not a single-valued quotient operation, unless abs(n) = 1."
        ),
    }


def integer_division_branch(
    source: Value,
    divisor: int,
    result: Value,
    *,
    materialization_limit: int = DEFAULT_PHASE_FAMILY_MATERIALIZATION_LIMIT,
) -> Dict[str, object]:
    """Validate source/divisor=result, then identify its Q/Z preimage branch."""

    n = _integer_scalar(divisor)
    if n == 0:
        raise ZeroDivisionError("integer phase division branch requires nonzero divisor")
    source_fraction = _fraction(source)
    result_fraction = _fraction(result)
    expected_result = source_fraction / n
    if result_fraction != expected_result:
        raise ValueError(
            "source arithmetic must satisfy result == source / divisor before "
            "phase-branch classification"
        )

    source_phase = phase_fraction(source_fraction)
    source_lift = source_fraction - source_phase
    if source_lift.denominator != 1:
        raise AssertionError("source minus canonical phase must be an integer lift")
    cardinality = abs(n)
    branch_index = int(source_lift) % cardinality
    selected_phase = phase_fraction(Fraction(source_phase + branch_index, n))
    result_phase = phase_fraction(result_fraction)
    if selected_phase != result_phase:
        raise AssertionError("retained source lift selected the wrong division branch")
    if phase_scale(n, result_phase) != source_phase:
        raise AssertionError("division result is not a torsion preimage of source phase")

    return {
        "source_relation_valid": True,
        "source": fraction_payload(source_fraction),
        "divisor": n,
        "result": fraction_payload(result_fraction),
        "source_phase": phase_payload(source_phase),
        "result_phase": phase_payload(result_phase),
        "source_integer_lift": int(source_lift),
        "preimage_count": cardinality,
        "selected_branch_index": branch_index,
        "single_valued_from_phase": cardinality == 1,
        "selection_uses_retained_source_lift": cardinality > 1,
        "phase_relation_holds": True,
        "preimage_family": phase_scale_preimages(
            n,
            source_phase,
            materialization_limit=materialization_limit,
        ),
        "claim_boundary": (
            "The retained source lift selects one torsion preimage. The quotient "
            "phase alone does not select a branch when abs(divisor) > 1."
        ),
    }


def classify_phase_operation(op: str) -> Dict[str, object]:
    """Return the static Q/Z descent class of one MoO arithmetic symbol."""

    if not isinstance(op, str):
        raise TypeError("operation must be one of '+', '-', '*', '/'")
    classifications: Dict[str, Dict[str, object]] = {
        "+": {
            "operation": "+",
            "descent_kind": "binary_additive_operation",
            "well_defined_on_quotient_classes": True,
            "single_valued": True,
            "law": "[a] + [b] = [a+b]",
        },
        "-": {
            "operation": "-",
            "descent_kind": "binary_additive_operation",
            "well_defined_on_quotient_classes": True,
            "single_valued": True,
            "law": "[a] - [b] = [a-b]",
        },
        "*": {
            "operation": "*",
            "descent_kind": "no_binary_quotient_descent",
            "well_defined_on_quotient_classes": False,
            "single_valued": False,
            "conditional_relation": (
                "A retained integer operand n defines the external scalar action mu_n; "
                "the quotient class [n] does not retain that scalar."
            ),
            "counterexample": "0 ~ 1, but 0*(1/2) ~ 0 and 1*(1/2) ~ 1/2",
        },
        "/": {
            "operation": "/",
            "descent_kind": "no_binary_quotient_descent",
            "well_defined_on_quotient_classes": False,
            "single_valued": False,
            "conditional_relation": (
                "Division by a retained nonzero integer n selects one preimage under "
                "mu_n; the phase input alone does not select it for abs(n) > 1."
            ),
            "counterexample": "0 ~ 1, but 0/2 ~ 0 and 1/2 ~ 1/2",
        },
    }
    if op not in classifications:
        raise ValueError("operation must be one of '+', '-', '*', '/'")
    return dict(classifications[op])


def triangle_slack(start: Value, via: Value, end: Value) -> Fraction:
    """Return the exact nonnegative triangle slack for one routed comparison."""

    first = circular_distance(start, via)
    second = circular_distance(via, end)
    direct = circular_distance(start, end)
    slack = first + second - direct
    if slack < 0:
        raise AssertionError("circular phase distance violated triangle inequality")
    return slack


def triangle_route_payload(start: Value, via: Value, end: Value) -> Dict[str, object]:
    first = circular_distance(start, via)
    second = circular_distance(via, end)
    direct = circular_distance(start, end)
    slack = triangle_slack(start, via, end)
    return {
        "start": fraction_payload(_fraction(start)),
        "via": fraction_payload(_fraction(via)),
        "end": fraction_payload(_fraction(end)),
        "first_leg": fraction_payload(first),
        "second_leg": fraction_payload(second),
        "direct_distance": fraction_payload(direct),
        "triangle_slack": fraction_payload(slack),
        "status": "tight" if slack == 0 else "strict",
    }


def sampled_path_payload(
    values: Sequence[Value],
    *,
    include_points: bool = True,
) -> Dict[str, object]:
    """Compare a sampled lift path with its endpoint-sampled Q/Z projection."""

    if not values:
        raise ValueError("sampled path must contain at least one point")
    points = [_fraction(value) for value in values]
    lift_steps = [abs(right - left) for left, right in zip(points, points[1:])]
    phase_steps = [
        circular_distance(left, right) for left, right in zip(points, points[1:])
    ]
    lift_path_length = sum(lift_steps, Fraction(0, 1))
    phase_path_length = sum(phase_steps, Fraction(0, 1))
    lift_endpoint_distance = abs(points[-1] - points[0])
    phase_endpoint_distance = circular_distance(points[0], points[-1])
    step_contraction = lift_path_length - phase_path_length
    endpoint_contraction = lift_endpoint_distance - phase_endpoint_distance
    phase_detour = phase_path_length - phase_endpoint_distance
    if step_contraction < 0 or endpoint_contraction < 0 or phase_detour < 0:
        raise AssertionError("sampled phase path contraction invariant failed")
    phase_return = phase_endpoint_distance == 0
    return {
        "sample_count": len(points),
        "points": [fraction_payload(point) for point in points]
        if include_points
        else None,
        "projected_phase_points": [
            fraction_payload(phase_fraction(point)) for point in points
        ]
        if include_points
        else None,
        "points_omitted": not include_points,
        "lift_path_length": fraction_payload(lift_path_length),
        "sampled_phase_path_length": fraction_payload(phase_path_length),
        "lift_endpoint_distance": fraction_payload(lift_endpoint_distance),
        "phase_endpoint_distance": fraction_payload(phase_endpoint_distance),
        "sampled_step_contraction": fraction_payload(step_contraction),
        "endpoint_contraction": fraction_payload(endpoint_contraction),
        "phase_detour": fraction_payload(phase_detour),
        "phase_return": phase_return,
        "sampled_net_integer_lift": (
            int(points[-1] - points[0])
            if phase_return and (points[-1] - points[0]).denominator == 1
            else None
        ),
        "sampling_limit": (
            "Endpoint sampling can alias a continuous full turn to zero length; "
            "path length is preserved only to the resolution of the retained steps."
        ),
    }
