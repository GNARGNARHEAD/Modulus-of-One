# Stage Dynamics And Recurrence Frames

> Program status: design-stage Modulus of One research with external recurrence-frame and
> witness-audited branch-rhythm calibrations.

## Exact Question

Does the strict construction graph exhibit persistent, threshold-sensitive, or
divergent stage behavior that survives explicit corpus and parameter controls?
Separately, how should representation-sensitive recurrences be compared with
Modulus of One without becoming runtime operations?

## Relation To The Core

Stage and confirmation are native to the current strict corpus. Chaos,
attractor, bifurcation, and digit-recurrence language are external framings
unless graph evidence earns a precise Modulus of One-native statement.

## Status By Scope

| Scope | Evidence layer | Claim status | Tool status | Result status | Result scope |
| --- | --- | --- | --- | --- | --- |
| Strict stage and confirmation behavior | `strict` | `observation` | `maintained` | `active` | Implemented substrate facts, not a chaos result |
| Proposed persistence and threshold suite | `strict` | `lead` | none | `active` | Design only; the unified probe is absent |
| Kaprekar recurrence-frame comparison | `external_probe` | `observation` | none | `completed_version` | Representation-sensitive external calibration |
| Branch-rhythm comparison | `external_probe` | `observation` | `maintained` | `completed_version` | Bounded probe with named clocks, rational-square matches and classical Pell recurrence, audited against U160 |

## Conceptual Dependencies And Reading Order

1. [Stage-dynamics lens](STAGE_DYNAMICS_LENS_NOTE.md)
2. [Preregistration and report protocol](DYNAMICS_TEST_PROTOCOL.md)
3. [Recurrence-frame versus branch distinction](RECURRENCE_FRAMES_NOTE.md)
4. [Kaprekar external calibration](KAPREKAR_RECURRENCE_FRAME_NOTE.md)
5. [Branch rhythm: clocks and witnessed comparisons](BRANCH_RHYTHM_20261002.analysis.md)

## Tool Status

`moo_dynamics_probe.py` is named in the protocol as a future interface target.
It does not currently exist and must not be presented as runnable.

Existing strict corpus builders and graph queries can support bounded
calibrations, but they do not implement the proposed stage-persistence,
threshold-sweep, edge-symbol recurrence, or neighborhood-divergence suite as a
unified instrument.

No focused unified-dynamics test exists because that instrument is absent. The
Kaprekar comparison is a note-level calibration and has no program-specific
test file.

The separate [branch-rhythm probe](branch_rhythm_probe.py) is implemented with
[six focused tests](../../tests/test_branch_rhythm_probe.py) and an
[independent verifier](verify_branch_rhythm.py). It compares named event
predicates and clocks; it does not implement the proposed unified instrument.

## Retained Findings

- Stage-dynamics vocabulary is safer than importing chaos terminology.
- A Kaprekar state depends on digit representation and recurrence-frame state,
  not value identity alone.
- `6174` is not a privileged Modulus of One node and the Kaprekar routine is not a Modulus of One
  attractor.
- Recurrence frames and branches are distinct: a frame governs how state and
  memory unfold; a branch is a repeated witnessed relation inside a selected
  field.
- A classical square/doubled-square comparison has a period-two signed
  discrepancy in recurrence steps and unbounded gaps between its specified
  graph certificate checkpoints. The U160 audit records the first three full
  discrepancy certificates and six root transitions; larger checkpoints are
  predictions. No pi-specific rhythm is established.

The [fourth-order illustration](../../docs/examples/FOURTH_ORDER_EXAMPLE.md) uses this
existing square comparison to explain the step from finite witnesses to a
proposed limiting form. Its supplementary ratio-edge readback is preserved in
an [editorial extract](../../docs/examples/evidence/fourth_order_square_example_20261107.json).
This is an illustrative external-probe lead, not a new projection experiment
or a stronger program result.

## Open Obligations

- Implement the probe only after each metric, control, checkpoint, and failure
  criterion is frozen.
- Preserve preregistration, report, interpretation, and decision as separate
  artifacts.
- Establish whether any signal survives value bounds, stage bounds, matched
  controls, and graph-local inspection.
- Keep the planned command labeled as planned until the file and tests exist.

## Allowed And Forbidden Language

Allowed: deterministic stage dynamics, persistence, threshold shift,
representation-sensitive external recurrence.

Forbidden: Modulus of One is chaotic; Modulus of One has an attractor or bifurcation; a planned probe
has produced evidence.

## Next Admissible Work

Implement the smallest preregistered stage-persistence test from the existing
protocol, or narrow the protocol if its required fields cannot be supported.
Stop or redesign when the same effect fails registered parameter and corpus
controls.
