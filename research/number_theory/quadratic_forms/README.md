# Quadratic Forms And Theta/Weil

> Program status: maintained exact external infrastructure, one frozen
> graph-conditioned null result, and active analytic proof obligations.

## Exact Question

What form-class and character information is lost when quadratic-form
representations collapse to scalar values, can any retained class/genus channel
be detected in strict graph construction features, and what exact obligations
are required before theta/Weil language can support a stronger analytic bridge?

## Relation To The Core

Quadratic forms, class groups, theta specialization, and Weil pairings are
external structures. The strict graph contributes audited scalar sources and
construction features; it does not acquire form-class or complex-zero nodes.

## Status By Scope

| Scope | Evidence layer | Claim status | Tool status | Result status | Result scope |
| --- | --- | --- | --- | --- | --- |
| Exact quadratic-form and class-channel machinery | `external_probe` | `observation` | `maintained` | `active` | Reusable exact calibration infrastructure |
| Nested graph-conditioned class/genus effect | `external_probe` | `observation` | `maintained` | `frozen_version` | U850 v1 null under the registered design |
| Theta/Weil analytic bridge | `external_probe` | `lead` | `maintained` | `active` | Finite cross-term calibration; analytic obligations remain open |

## Conceptual Dependencies And Reading Order

1. [Quadratic forms and class-character channels](../QUADRATIC_FORMS_CLASS_CHANNEL_LENS_NOTE.md)
2. [Theta prefixes and Weil cross-term obligations](../THETA_WEIL_CONSTRUCTIVE_OBLIGATIONS_NOTE.md)

## Tools And Software Dependencies

- [`moo/quadratic_form_probe.py`](../../../moo/quadratic_form_probe.py) owns the
  exact base enumeration and composition machinery.
- [`moo/quadratic_form_nested_math.py`](../../../moo/quadratic_form_nested_math.py),
  [`moo/quadratic_form_nested_probe.py`](../../../moo/quadratic_form_nested_probe.py),
  and [`moo/quadratic_form_recovery.py`](../../../moo/quadratic_form_recovery.py)
  implement the nested class/genus ablation and recovery checks.
- [`moo/theta_weil_probe.py`](../../../moo/theta_weil_probe.py) genuinely
  imports the base quadratic-form probe.

The focused contracts are
[`tests/test_moo_quadratic_form_probe.py`](../../../tests/test_moo_quadratic_form_probe.py),
[`tests/test_moo_quadratic_form_nested_math.py`](../../../tests/test_moo_quadratic_form_nested_math.py),
[`tests/test_moo_quadratic_form_nested_probe.py`](../../../tests/test_moo_quadratic_form_nested_probe.py),
[`tests/test_moo_quadratic_form_recovery.py`](../../../tests/test_moo_quadratic_form_recovery.py),
and [`tests/test_moo_theta_weil_probe.py`](../../../tests/test_moo_theta_weil_probe.py).

## Frozen Evidence

The [Gauss file-level evidence index](../../experiments/gauss/README.md)
enumerates the U300 development and U850 holdout preregistrations, reports,
analyses, and sidecars. The U850 SQLite holdout is checksum-registered in the
[corpus inventory](../../experiments/CORPUS_INVENTORY.md), but was absent
at its named path in the 2026-11-04 availability check. The retained reports
remain evidence under that historical source identity; they are not a fresh
audit against a current corpus.

## Current Disposition

- Exact representation fibres, automorphisms, class composition, character
  channels, and modulus-one erasure are retained.
- The nested `Delta=-20,-23,-56` U850 v1 ablation found no promoted
  graph-conditioned class/genus effect under its registered design.
- That null result does not retire the reusable exact tools or broader program.
- Theta prefixes and the finite Weil matrix preserve cross terms that
  diagonal-only or same-point placebos erase.
- The current work does not evaluate the arithmetic explicit formula and is not
  evidence for the Riemann hypothesis.

## Open Obligations

The detailed theta/Weil note lists the unmet analytic requirements, including
valid test-function space, transform normalization, truncation/tail control,
arithmetic explicit-formula terms, zero data or certified substitutes, and
rigorous interpretation of positivity or failure.

## Allowed And Forbidden Language

Allowed: exact external form/class calibration; frozen graph-conditioned null;
cross-term-preserving finite analytic control.

Forbidden: the null proves no quadratic interaction can exist; the synthetic
quartet is zeta data; the current matrix supplies RH evidence.

## Next Admissible Work

Continue only by satisfying a named missing analytic obligation or by
preregistering a genuinely new graph-conditioned design with an independent
corpus. Do not tune a replacement against the frozen U850 holdout.
