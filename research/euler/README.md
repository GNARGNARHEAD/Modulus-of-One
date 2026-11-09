# Euler Reciprocal Structures And Zeta Calibrations

> Program status: mixed external program with exact finite structure,
> controlled numerical calibrations, a narrow arrival observation, and a
> rejected centered zero-symmetry claim.

## Exact Question

What can exact finite reciprocal sums, Euler products, Hasse-form zeta
calibrations, graph-stage source arrival, and centered reciprocal-shell
geometry contribute after their rational sources are audited against the Modulus of One
graph?

## Relation To The Core

Every analytic or complex operation remains external. The strict graph supplies
audited rational and integer sources, stages, confirmations, and retained
construction witnesses. It does not contain `zeta(s)`, complex arithmetic, or a
certified zero as runtime objects.

## Status By Scope

| Scope | Evidence layer | Claim status | Tool status | Result status | Result scope |
| --- | --- | --- | --- | --- | --- |
| Finite reciprocal, Euler-product, and critical-strip calibrations | `external_probe` | `observation` | `maintained` | `completed_version` | Exact finite objects and numerical controls; no zero certificate |
| Saved graph-arrival ordering | `external_probe` | `observation` | `maintained` | `completed_version` | Negative graph-specific result under ordinary `1..64` source order |
| Centered reciprocal-shell geometry | `external_probe` | `candidate` | `maintained` | `completed_version` | Exact external geometry with interpretation still bounded |
| Centered inversion of the zeta zero set | `external_probe` | `rejected` | `maintained` | `completed_version` | Rejected symmetry subclaim |

## Conceptual Dependencies And Reading Order

1. [Reciprocal-mass, Euler-product, critical, and arrival ledger](EULER_RECIPROCAL_MASS_AND_CIRCLE_LENS_NOTE.md)
2. [Centered reciprocal-shell follow-up](CENTERED_RECIPROCAL_SHELL_LENS_NOTE.md)
3. [Quadratic-form bridge](../number_theory/quadratic_forms/README.md)

## Tools And Software Dependencies

- `moo/series_probe.py` evaluates exact finite rational series and products.
- `moo/zeta_critical_probe.py` provides the finite external critical-strip
  calibration.
- `moo/zeta_arrival_probe.py` imports the critical probe and reveals a fixed
  external basis under graph-stage masks.
- `moo/zeta_centered_inversion_probe.py` imports the critical probe and the
  circle probe; it does not import the arrival, phase, quadratic-form, or
  theta/Weil probes.

Focused contracts are
[`tests/test_moo_series_probe.py`](../../tests/test_moo_series_probe.py),
[`tests/test_moo_zeta_critical_probe.py`](../../tests/test_moo_zeta_critical_probe.py),
[`tests/test_moo_zeta_arrival_probe.py`](../../tests/test_moo_zeta_arrival_probe.py), and
[`tests/test_moo_zeta_centered_inversion_probe.py`](../../tests/test_moo_zeta_centered_inversion_probe.py).

The reading order is therefore conceptual, not a claim that every tool calls
the preceding one.

## Frozen Evidence

The [Euler file-level evidence index](../../docs/evidence/euler.md)
enumerates the retained reports and analyses and records that no separate
preregistration files survive there. Their SQLite inputs are separately
registered in the
[corpus inventory](../experiments/CORPUS_INVENTORY.md).

## Current Disposition

- Exact finite reciprocal-square sums, local geometric truncations, and finite
  Euler products are valid external objects over graph-audited sources.
- The critical-strip probe is a controlled finite calibration at a
  caller-supplied coordinate, not a zero recognizer or certificate.
- In the saved arrival runs, source availability through `1..64` reduced to
  ordinary positive-spine order. The unusual monotone finite cancellation is
  retained, but it is not graph-specific zeta evidence.
- Centered reciprocal-shell geometry is exact as an external construction.
- The proposed centered inversion symmetry of the zeta zero set is rejected.

## Open Obligations

- Rigorous zero certification would require interval control and a valid
  zero-counting method not implemented here.
- A graph-specific arrival claim requires an admissible ordering that is not
  merely ordinary integer order or speculative-node leakage.
- Any continuation through theta/Weil must satisfy the explicit obligations in
  the quadratic-form program.

## Allowed And Forbidden Language

Allowed: exact finite structures; controlled external cancellation over
graph-audited sources; rejected centered zero-symmetry subclaim.

Forbidden: Modulus of One constructs `pi`; Modulus of One contains or discovers zeta zeros; a small
binary64 residual certifies a zero; the centered inversion preserves the zeta
zero set.

## Next Admissible Work

Do not repeat the rejected symmetry or relabel ordinary source order as a graph
effect. Continue only with a preregistered source-ordering hypothesis that is
defined by retained graph structure and beats matched controls, or with the
explicitly bounded analytic obligations already recorded.
