# Arithmetic Calibrations At 216

> Program status: completed external arithmetic calibration.

## Question And Scope

Which apparent relationships at `216` are exact identities, dependent
projections, or effects already explained by the strict graph generator?
These are selected calibration examples. They do not establish privileged
status for `216` or change Modulus of One's runtime or philosophical foundations.

## Results

| Scope | Evidence layer | Claim status | Tool status | Result status |
| --- | --- | --- | --- | --- |
| Power identities and golden-rotation dependencies | `external_probe` | `observation` | `maintained` | `completed_version` |
| Raw route mass as evidence of special graph status | `external_probe` | `rejected` | `maintained` | `completed_version` |
| Declared route-certificate distinctions | `strict` | `observation` | `maintained` | `completed_version` |

The retained arithmetic includes:

- `216 = 6^3 = 2^3 * 3^3`.
- `3^2 + 4^2 = 5^2` and `3^3 + 4^3 + 5^3 = 6^3`.
- With `phi = (1 + sqrt(5))/2`, `144*phi = 233 - phi^-12`.
  The half-turn approximations at 72 and 216 follow from this same identity;
  they are dependent observations.
- The proposed return at 231 fails the direct rotation check.
- Aggregate incoming-route counts at 216 match the strict-generator formulas.
- Geometric labels can describe the same algebraic route. Distinct declared
  certificates can also share dependencies.

The [route-identity note](../strict_stage/ROUTE_IDENTITY_LENS_NOTE.md) retains
the exact right-triangle cubic-defect proof and the graph-route comparisons.
Its [program card](../strict_stage/route_identity/README.md) owns those results,
their tests, and the open question of semantic independence beyond the
specified certificate system.

## Tools And Evidence

| Calibration | Tool | Saved report |
| --- | --- | --- |
| Golden rotation | [analyze_golden_rotation_216.py](../../tools/analyze_golden_rotation_216.py) | [JSON](../experiments/216/golden_rotation_216_v1.json), [analysis](../experiments/216/golden_rotation_216_v1.md) |
| Power identities | [explore_216_power_lattice.py](../../tools/explore_216_power_lattice.py) | [JSON](../experiments/216/power_lattice_216_v1.json), [analysis](../experiments/216/power_lattice_216_v1.md) |
| Route identity | [moo/route_identity_probe.py](../../moo/route_identity_probe.py) | [U1000 report](../experiments/216/route_identity_216_u1000_v2.report.json) |

These tools are separate calibrations. The two standalone arithmetic scripts
have no dedicated test files; the route probe has
[focused tests](../../tests/test_moo_route_identity_probe.py).

The historical U1000 report used
`out/experiments/pascal_cubic_scale_u1000.sqlite`, whose recorded checksum is in
the [corpus inventory](../experiments/CORPUS_INVENTORY.md). That input
is absent from this checkout. The saved report remains available, but its
original database measurements cannot currently be rerun here.

One explanatory sentence in that report was generalized during the 2026-10-21
cleanup. Its `editorial_revision` records the original file hash and the exact
field changed. Numerical evidence and original run provenance are unchanged.

## Interpretation And Further Work

These results support exact identities, dependency checks, and quotient-specific
route comparisons. Raw multiplicity and repeated labels alone do not support
special status for a number.

This calibration has no pending source-dependent branch. Any further graph
claim belongs to the route-identity program and needs a stated route quotient,
comparison cases, and controls. A distinction that disappears under its
required quotient must be weakened or rejected.
