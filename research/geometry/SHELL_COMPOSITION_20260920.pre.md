# Witnessed shell composition: frozen audit design

Date: 2026-09-20

evidence_layer: external_probe (algebra and candidate selection); strict
(read-only retained-event audit)
claim_status: candidate (branch schema); observation (bounded audit)

This design is fixed before inspecting the new composition predicate in the
saved corpora. The examples were selected from the preceding mathematical
discussion, not discovered blindly. This is a new audit, not a continuation of
the stopped phase-transport experiment.

## Question

For ordered signed triples A=(a,b,r), B=(c,d,s), inspect the construction

    A o B = (ac-bd, ad+bc, rs).

Keep three evidence levels distinct: source shell witnesses, the seven
composition operations, and a direct shell witness for the output. Ordinary
algebra proves norm preservation. The audit asks which defining operations
are actually retained, when their joint witnesses become available, and which
parts are prohibited by the positive-spine field.

## Fixed cases

| Case | Left | Right | Output | Purpose |
| --- | --- | --- | --- | --- |
| positive_double | (4,3,5) | (4,3,5) | (7,24,25) | Positive composition and later direct output proof |
| positive_mixed | (4,3,5) | (12,5,13) | (33,56,65) | A second positive composition with a later source proof |
| signed_output | (3,4,5) | (3,4,5) | (-7,24,25) | Negative output is allowed; negative reuse is not |
| axis_output | (3,4,5) | (4,3,5) | (0,25,25) | Cancellation reaches an axis; zero reuse is not allowed |
| inverse_input | (3,4,5) | (3,-4,5) | (25,0,25) | Inverse law is external when signed operands are required |
| identity_input | (1,0,1) | (4,3,5) | (4,3,5) | Identity action requires zero operands in this literal schema |
| scaled_double | (8,6,10) | (8,6,10) | (28,96,100) | Same normalized output, distinct construction and timing |
| non_shell_control | (4,3,6) | (4,3,5) | (7,24,30) | Operations may exist while the source/target shell agreement fails |

Do not sort coordinates, replace negatives by their absolute values, reduce
raw output triples, or simplify operations involving zero. Such changes would
be different witnesses. Record normalization separately as a pair of division
requests, retaining both its external value and its actual witness status.

## Witness predicates

A direct shell requests a*a, b*b, r*r, and a*a+b*b. All four events must be
retained with confirmed operands at their saved stages, and the addition and
radius-square must land on the same node.

Composition requests ac, bd, ad, bc, ac-bd, ad+bc, and rs, with exact ordered
inputs and shared intermediate nodes. A composition event alone does not
certify its sources as shells.

`source_composition` requires both source shell motifs and the composition
motif. `full_closure` additionally requires the direct target shell motif.
The classical norm identity can interpret `source_composition` as an external
certificate for the target, but is not a replacement for its direct graph
witness. Normalization is a separate observation and is not part of these
closure predicates.

Deduplicate repeated literal edge requests only for storage; keep all their
roles in each motif. A shared edge is not two independent occurrences. Retain
every matching occurrence, not just the earliest event.

## Predictions and controls

For each literal arithmetic request with positive integer operands, the
ordinary readiness prediction is their maximum. For a joint motif, take the
maximum over all requested operands. A zero or negative operand gives a
structural blocker, not a large or infinite predicted stage. Arithmetic
agreement must hold independently of edge presence.

Under sufficiently wide retention:

| Case | Composition | Source + composition | Direct target shell |
| --- | ---: | ---: | ---: |
| positive_double | U16 | U16 | U576 |
| positive_mixed | U48 | U144 | U3136 |
| signed_output | U16 | U16 | Blocked by negative operand |
| axis_output | U16 | U16 | Blocked by zero operand |
| inverse_input | Blocked | Blocked | Blocked |
| identity_input | Blocked | Blocked | U16 |
| scaled_double | U64 | U64 | U9216 |
| non_shell_control | U16 | Rejected: source disagreement | Rejected: target disagreement |

The non-shell control's direct target requests all become eligible by U576,
but their outputs disagree. Missing edges alone must not be the reason for its
rejection. Scaled and unscaled copies are a deterministic comparison, not
independent samples. The signed, zero, and narrow-retention cases are controls
for overstating closure from value presence.

## Corpus scope

- Primary: preserved `out/experiments/pascal_edge_probe_u300.sqlite`.
- Later-stage validation:
  `out/experiments/gauss/strict_stage_u850_holdout_v1.sqlite`.
- Retention control: preserved `out/experiments/circle_as_one_u80.sqlite`.

These are existing, previously studied nested apertures, not independent or
previously untouched samples. Their bytes and hashes must match the
[corpus inventory](../../out/experiments/CORPUS_INVENTORY.md). Open read-only;
record alignment, configuration, and before/after hashes. Do not regenerate
or alter the inputs.

## Outputs and validation

Record raw and normalized triples, every requested operation, all matching
edge IDs/stages, exact node records and checkpoint status, agreement failures,
operand blockers, predicted/observed readiness, and graph inspection commands.
Bind the report to this design and the tool/helper source hashes. Report
complete, partial, and absent motifs even when the expected algebra is true.

Before the corpus run, verify independent arithmetic cases and adversarial
fixture failures: missing edge despite node presence, a nearby nonhit with all
events present, signed/zero inputs, future confirmation, and checkpoint
filtering. Enumerate a small rational shell independently to check parameter
coverage, including the missing affine-chart endpoint.

## Interpretation and stopping rule

This audit can establish a repeated witnessed composition motif and expose
its field boundary. It cannot establish that MoO uniquely selects circularity,
a completed circle, a new timing law, or pi. If ordinary operand readiness
explains all timings, report that result and stop this audit. Do not enlarge
the scan to hunt a residual. A general claim that this branch is privileged
would require a separately designed comparison with other repeated relations.
