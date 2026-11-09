# Circle As One And Phase

> Program status: exact external quotient and operator facts; active metric
> observation; completed transport design with insufficient aperture.

## Exact Question

What structure is retained or lost when rational graph nodes are projected into
`Q/Z` phase classes, and do exact metric or operator relations over that
quotient return non-generic information to the source graph?

## Relation To The Core

`Q/Z`, its map to `U(1)`, shortest-arc phase distance, and phase operators are
external exact mathematics over graph-recorded rational sources. They do not
make a Euclidean circle, complex phase, or metric into Modulus of One runtime semantics.

## Status By Scope

| Scope | Evidence layer | Claim status | Tool status | Result status | Result scope |
| --- | --- | --- | --- | --- | --- |
| Rational phase quotient and operator descent | `external_probe` | `observation` | `maintained` | `completed_version` | Exact external algebra over audited rational sources |
| Phase-metric collapse | `external_probe` | `observation` | `maintained` | `completed_version` | U40 v1; no promoted special-fibre effect |
| Registered phase-transport runs | `external_probe` | `observation` | `maintained` | `stopped_design` | U40/U80 designs stopped at the mutable-fraction aperture gate |

## Conceptual Dependencies And Reading Order

1. [Quotient, return, and lost lift](../CIRCLE_AS_ONE_QUOTIENT_NOTE.md)
2. [Metric collapse and graph-retained difference](../PHASE_METRIC_COLLAPSE_NOTE.md)
3. [Operator descent and provenance transport](../PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md)

## Tools And Software Dependencies

- [`moo/circle_as_one_probe.py`](../../../moo/circle_as_one_probe.py) performs
  the read-only quotient and return audit.
- [`moo/phase.py`](../../../moo/phase.py) owns shared exact phase operations.
- [`moo/phase_metric_probe.py`](../../../moo/phase_metric_probe.py) imports
  `moo_phase` and graph evidence helpers.
- [`moo/phase_transport_probe.py`](../../../moo/phase_transport_probe.py)
  imports `moo_phase` but does not import the metric probe.

The metric and transport studies are conceptual continuations and sibling
consumers of shared phase code, not a call chain.

Focused contracts are
[`tests/test_moo_circle_as_one_probe.py`](../../../tests/test_moo_circle_as_one_probe.py),
[`tests/test_moo_phase_operator.py`](../../../tests/test_moo_phase_operator.py),
[`tests/test_moo_phase_metric_probe.py`](../../../tests/test_moo_phase_metric_probe.py), and
[`tests/test_moo_phase_transport_probe.py`](../../../tests/test_moo_phase_transport_probe.py).

## Retained Evidence

- Quotient reports include
  `research/experiments/circle_as_one_u40_wide_d12_v3.json` and
  `research/experiments/circle_as_one_u80_d20_v3.json`.
- The metric report is
  `research/experiments/phase_metric_collapse_u40_wide_d12_v1.json`.
- Frozen transport preregistrations, reports, and analyses are enumerated by
  the [quarantined transport evidence index](../../experiments/geometry/quarantined_phase_transport/README.md).
- The underlying U40 and U80 corpora are listed in the
  [corpus inventory](../../experiments/CORPUS_INVENTORY.md).

## Current Disposition

- The rational phase quotient and its distinction from integer modulus one are
  exact.
- Different rational sources can collapse to zero phase distance while
  retaining different graph neighborhoods.
- Triangle-inequality behavior is an external metric fact, not an explanation
  of `Ref(1)` or a runtime circle.
- Addition/subtraction descend exactly; integer multiplication acts on phase;
  division is a torsion-preimage relation rather than a single-valued descended
  operator.
- Both registered transport runs failed the required mutable-fraction aperture
  gate. The current design ended without a transport-effect retain or kill
  verdict.

## Allowed And Forbidden Language

Allowed: exact quotient, exact external metric, graph-retained difference,
operator-descent boundary, insufficient-aperture stopped design.

Forbidden: Modulus of One constructs a circle; quotient collapse proves source identity;
the metric is runtime geometry; the transport effect exists despite the failed
registered aperture gate.

## Next Admissible Work

Do not rerun the exhausted transport design under altered thresholds. Any new
transport question requires a new design, new identifier, independent aperture
justification, and controls that are fixed before measurement.
