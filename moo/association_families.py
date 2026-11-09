"""Exact, bounded association selectors for a derived MoO inspection index.

These specifications request arithmetic witnesses; they do not assert that a
corpus contains those witnesses or permits their operands.  The selected square,
shell, and fixed-seed spiral families are explicit inspection lenses, not a
discovery or classification of every branch of MoO.
"""

from __future__ import annotations

from fractions import Fraction
import json
from math import isqrt
from typing import Any


SQUARE_SOURCES = ["docs/protocols/branch-evidence.md"]
SHELL_SOURCES = [
    "research/geometry/SHELL_COMPOSITION_BRANCH_NOTE.md",
    "research/geometry/SHELL_SQUARE_RATIO_BRANCH_NOTE.md",
]
ENCODING_SOURCES = [
    "research/geometry/square_area_inspection.py",
    "research/geometry/AREA_INSPECTION_BRANCH_20261001.analysis.md",
]
ROUTE_SOURCES = [
    "research/strict_stage/PASCAL_SHELL_CERTIFICATE_NOTE.md",
    "research/strict_stage/route_identity/pascal_shell_calibration.py",
    'moo/route_identity_probe.py',
]


def _participant(role: str, value: int | Fraction) -> dict[str, str]:
    return {"role": role, "value": str(Fraction(value))}


def _request(
    role: str, left: int | Fraction, op: str, right: int | Fraction
) -> dict[str, str]:
    left, right = Fraction(left), Fraction(right)
    if op == "*":
        result = left * right
    elif op == "+":
        result = left + right
    elif op == "-":
        result = left - right
    elif op == "/":
        result = left / right
    else:
        raise ValueError(f"Unsupported association operation: {op}")
    return {
        "role": role,
        "left": str(left),
        "op": op,
        "right": str(right),
        "result": str(result),
    }


def _certificate(
    identifier: str,
    label: str,
    criterion: str,
    requests: list[dict[str, str]],
    sources: list[str],
    *,
    parameters: dict[str, Any] | None = None,
    dependencies: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "label": label,
        "criterion": criterion,
        "parameters": parameters if parameters is not None else {},
        "sources": list(sources),
        "requests": requests,
        "dependencies": dependencies if dependencies is not None else [],
    }


def _shell_id(x: Fraction, y: Fraction, r: Fraction) -> str:
    return f"shell:{x},{y},{r}"


def _shell_spec(x: Fraction, y: Fraction, r: Fraction) -> dict[str, Any]:
    return {
        "id": _shell_id(x, y, r),
        "family": "shell",
        "label": f"Shell ({x}, {y}, {r})",
        "parameters": {"x": str(x), "y": str(y), "r": str(r)},
        "participants": [
            _participant("x", x),
            _participant("y", y),
            _participant("r", r),
            _participant("x_square", x * x),
            _participant("y_square", y * y),
            _participant("r_square", r * r),
        ],
        "sources": list(SHELL_SOURCES),
        "relations": [],
        "certificates": [
            _certificate(
                "literal", "Literal self-products and sum",
                "three_literal_self_products_and_direct_sum",
                [
                    _request("x_square", x, "*", x),
                    _request("y_square", y, "*", y),
                    _request("r_square", r, "*", r),
                    _request("shell_sum", x * x, "+", y * y),
                ],
                SHELL_SOURCES,
            )
        ],
    }


def _normalization_certificate(x: int, y: int, r: int) -> dict[str, Any]:
    """The existing nine-request positive-integer square-relation encoding."""
    return _certificate(
        f"normalize:{x},{y},{r}",
        f"Integer encoding from ({x}, {y}, {r})",
        "integer_encoded_normalized_shell",
        [
            _request("p_square", x, "*", x),
            _request("q_square", y, "*", y),
            _request("r_square", r, "*", r),
            _request("sum", x * x, "+", y * y),
            _request("x", x, "/", r),
            _request("y", y, "/", r),
            _request("x_square_encoding", x * x, "/", r * r),
            _request("y_square_encoding", y * y, "/", r * r),
            _request("sum_encoding", x * x + y * y, "/", r * r),
        ],
        ENCODING_SOURCES,
        parameters={
            "raw_source": {"x": str(x), "y": str(y), "r": str(r)},
            "source_association": f"shell:{x},{y},{r}",
            "interpretation": "Integer-encoded identity; no fractional-input self-product or sum.",
        },
    )


def _attach_fixed_square_routes(specs: list[dict[str, Any]]) -> None:
    """Adapt the existing fixed route calibration without expanding selection."""
    selected = {spec["id"]: spec for spec in specs if spec["id"] in {"square:9", "square:25"}}
    if not selected:
        return
    from moo.route_identity_probe import canonical_route_expression
    from research.strict_stage.route_identity.pascal_shell_calibration import certificates

    targets = {Fraction(81): "square:9", Fraction(625): "square:25"}
    routes = certificates()
    root_bindings = {}
    for route in routes:
        association = selected.get(targets.get(Fraction(*route.target)))
        if association is None or not route.route_id.endswith("_factored"):
            continue
        root = Fraction(association["parameters"]["root"])
        candidates = [step for step in route.steps if step.op == "+" and Fraction(*step.result) == root]
        if len(candidates) != 1:
            raise ValueError(f"Expected one root-binding sum in {route.route_id}")
        root_bindings[(route.external_family, route.target)] = (route.route_id, candidates[0])
    for route in routes:
        association = selected.get(targets.get(Fraction(*route.target)))
        if association is None:
            continue
        requests = []
        for prefix, steps in (("step", route.steps), ("premise", route.premise_steps)):
            for step in steps:
                request = _request(
                    f"{prefix}:{step.step_id}", Fraction(*step.left), step.op,
                    Fraction(*step.right),
                )
                if Fraction(request["result"]) != Fraction(*step.result):
                    raise ValueError(f"Incorrect fixed route step: {route.route_id}/{step.step_id}")
                requests.append(request)
        binding_route, binding_step = root_bindings[(route.external_family, route.target)]
        binding = _request("binding:root_sum", Fraction(*binding_step.left), binding_step.op,
                           Fraction(*binding_step.right))
        # Reaching the squared endpoint alone does not bind this route to the
        # association's root. Retain the named sum even for expanded recipes.
        binding_role = next((request["role"] for request in requests
                             if all(request[key] == binding[key]
                                    for key in ("left", "op", "right", "result"))), None)
        added_binding = binding_role is None
        if added_binding:
            requests.append(binding)
            binding_role = binding["role"]
        association["certificates"].append(_certificate(
            f"route:{route.route_id}", route.description,
            "fixed_square_route_certificate", requests, ROUTE_SOURCES,
            parameters={
                "route_id": route.route_id,
                "external_family": route.external_family,
                "description": route.description,
                "target": str(Fraction(*route.target)),
                "dependency_tags": list(route.dependency_tags),
                "ac_expression": json.loads(json.dumps(canonical_route_expression(route))),
                "expression_scope": "construction steps only; original and association-binding premises separately retained",
                "association_binding": {
                    "root": association["parameters"]["root"],
                    "source_route_id": binding_route, "request_role": binding_role,
                    "added_by_adapter": added_binding,
                },
                "interpretation_limit": route.interpretation_limit,
            },
        ))
        association["sources"] = list(dict.fromkeys([*association["sources"], *ROUTE_SOURCES]))


def generate_associations(
    *, square_height: int = 25, max_radius: int = 25, spiral_steps: int = 5,
    spiral_seed: tuple[int, int, int] = (4, 3, 5),
) -> list[dict[str, Any]]:
    """Return deterministic, JSON-compatible exact association specifications.

    ``square_height`` selects distinct nonnegative roots p/q with
    0 <= p <= square_height and 1 <= q <= square_height.  ``max_radius``
    selects all ordered positive integer shell triples within that radius;
    both leg orientations and all integer scales in the bound are included.
    Each raw shell also supplies its rational unit-radius triple, deduplicated
    by exact ordered coordinates rather than by an unoriented triangle shape.
    Positive noninteger square roots also carry an integer-ratio certificate;
    unit shells retain a full nine-request encoding per positive integer source.
    These are alternatives to literal witnesses, not replacements for them.
    The fixed Pascal/shell route certificates are attached only when their
    existing square roots 9 or 25 are selected by the square-height bound.

    ``spiral_steps`` selects iterations 1 through that bound of the external
    pair product with the selected integer shell seed, default (4, 3, 5).
    The seed preserves signed coordinate order and must satisfy x*x+y*y=r*r
    with r > 0. Zero and negative operands remain subject to the source field.
    Every selected
    spiral triple and its unit-radius projection is included as a shell even
    when signed or beyond ``max_radius``.  Iteration 1 obtains its source
    evidence from the seed shell.  Later iterations depend on that source and
    the preceding spiral, but never require the direct target-shell witness.

    Limits must be nonnegative integers; zero disables the corresponding
    bounded selector.  A disabled shell selector does not suppress the shell
    instances explicitly required by a nonempty spiral selection.  No field,
    confirmation, or operand-reuse semantics are supplied by these selectors.
    """
    for name, limit in (
        ("square_height", square_height),
        ("max_radius", max_radius),
        ("spiral_steps", spiral_steps),
    ):
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError(f"{name} must be a nonnegative integer")
        if limit < 0:
            raise ValueError(f"{name} must be a nonnegative integer")
    if len(spiral_seed) != 3 or any(isinstance(v, bool) or not isinstance(v, int)
                                    for v in spiral_seed):
        raise TypeError("spiral_seed must contain three integers")
    seed_x, seed_y, seed_r = spiral_seed
    if seed_r <= 0 or seed_x * seed_x + seed_y * seed_y != seed_r * seed_r:
        raise ValueError("spiral_seed must satisfy x*x+y*y=r*r with r > 0")

    specs: list[dict[str, Any]] = []
    roots = {
        Fraction(p, q)
        for q in range(1, square_height + 1)
        for p in range(square_height + 1)
    }
    for root in sorted(roots):
        certificates = [_certificate(
            "literal", "Literal self-product", "literal_self_product",
            [_request("self_product", root, "*", root)], SQUARE_SOURCES,
        )]
        sources = list(SQUARE_SOURCES)
        if root > 0 and root.denominator != 1:
            p, q = root.numerator, root.denominator
            certificates.append(_certificate(
                "integer_ratio", "Integer encoding of the rational square",
                "integer_encoded_rational_square",
                [
                    _request("p_square", p, "*", p),
                    _request("q_square", q, "*", q),
                    _request("root", p, "/", q),
                    _request("square", p * p, "/", q * q),
                ],
                ENCODING_SOURCES,
                parameters={"numerator": str(p), "denominator": str(q),
                            "representation": "reduced_positive_integer_ratio"},
            ))
            sources.extend(ENCODING_SOURCES)
        specs.append(
            {
                "id": f"square:{root}",
                "family": "square",
                "label": f"Self-product of {root}",
                "parameters": {"root": str(root), "square": str(root * root)},
                "participants": [
                    _participant("root", root),
                    _participant("square", root * root),
                ],
                "sources": sources,
                "relations": [],
                "certificates": certificates,
            }
        )
    _attach_fixed_square_routes(specs)

    shells: dict[tuple[Fraction, Fraction, Fraction], dict[str, Any]] = {}
    included_sources: set[tuple[Fraction, Fraction, Fraction]] = set()

    def include_shell(x: int, y: int, r: int) -> None:
        raw = Fraction(x), Fraction(y), Fraction(r)
        if raw in included_sources:
            return
        included_sources.add(raw)
        unit = Fraction(x, r), Fraction(y, r), Fraction(1)
        for triple in (raw, unit):
            if triple not in shells:
                shells[triple] = _shell_spec(*triple)
        relation_parameters = {
            "source_radius": str(r),
            "raw_source": {"x": str(x), "y": str(y), "r": str(r)},
            "projection": "(x/r,y/r,1)",
        }
        shells[raw]["relations"].append({
            "kind": "normalizes_to", "target": _shell_id(*unit),
            "parameters": dict(relation_parameters),
        })
        shells[unit]["relations"].append({
            "kind": "normalized_from", "target": _shell_id(*raw),
            "parameters": dict(relation_parameters),
        })
        if min(x, y, r) > 0:
            shells[unit]["certificates"].append(_normalization_certificate(x, y, r))
            shells[unit]["sources"] = list(dict.fromkeys([
                *shells[unit]["sources"], *ENCODING_SOURCES,
            ]))

    for r in range(1, max_radius + 1):
        for x in range(1, r):
            y_squared = r * r - x * x
            y = isqrt(y_squared)
            if y > 0 and y * y == y_squared:
                include_shell(x, y, r)

    spirals: list[dict[str, Any]] = []
    x, y, r = spiral_seed
    seed_key = f"{seed_x},{seed_y},{seed_r}"
    seed_shell = f"shell:{seed_key}"
    for iteration in range(1, spiral_steps + 1):
        requests: list[dict[str, str]] = []
        previous_participants: list[dict[str, str]] = []
        dependencies = [f"{seed_shell}#literal"]
        if iteration > 1:
            previous_x, previous_y, previous_r = x, y, r
            ac, bd = previous_x * seed_x, previous_y * seed_y
            ad, bc = previous_x * seed_y, previous_y * seed_x
            x, y, r = ac - bd, ad + bc, previous_r * seed_r
            requests = [
                _request("ac", previous_x, "*", seed_x),
                _request("bd", previous_y, "*", seed_y),
                _request("ad", previous_x, "*", seed_y),
                _request("bc", previous_y, "*", seed_x),
                _request("x", ac, "-", bd),
                _request("y", ad, "+", bc),
                _request("r", previous_r, "*", seed_r),
            ]
            previous_participants = [
                _participant("previous_x", previous_x),
                _participant("previous_y", previous_y),
                _participant("previous_r", previous_r),
            ]
            dependencies.append(f"spiral:{seed_key}:{iteration - 1}#scalar_lineage")
        include_shell(x, y, r)
        spirals.append(
            {
                "id": f"spiral:{seed_key}:{iteration}",
                "family": "spiral",
                "label": f"Seed ({seed_x}, {seed_y}, {seed_r}), iteration {iteration}",
                "parameters": {
                    "seed": list(spiral_seed),
                    "iteration": iteration,
                    "x": str(x),
                    "y": str(y),
                    "r": str(r),
                },
                "participants": [
                    _participant("x", x),
                    _participant("y", y),
                    _participant("r", r),
                    *previous_participants,
                ],
                "sources": [SHELL_SOURCES[0]],
                "relations": [],
                "certificates": [_certificate(
                    "scalar_lineage", "Seed shell and linked scalar transitions",
                    "seed_shell_and_linked_scalar_transitions", requests,
                    [SHELL_SOURCES[0]], dependencies=dependencies,
                )],
            }
        )

    for triple in sorted(shells, key=lambda item: (item[2], item[0], item[1])):
        specs.append(shells[triple])
    specs.extend(spirals)
    return specs
