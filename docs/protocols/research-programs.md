# Research And Analysis Protocol

> Status: active program-card, lifecycle and general analysis protocol.
>
> The graph is primary. Edges are the structure. Analysis tools choose where
> and how to inspect it; the [claim ledger](../CLAIMS.md) sets the limits of
> interpretation.

## Questions, Claims, Tools And Results

Keep these distinct:

```text
program identity: the stable question or family of questions
claim status:     how strongly one claim is supported
tool status:      whether an instrument is maintained or historical
result status:    what happened to one versioned experiment or design
```

A rejected subclaim does not delete its program. A frozen result does not
freeze every tool in the program. A speculative program does not become less
real because its current answer is uncertain.

## Canonical Status Values

Program prose may summarize mixed work, but each material claim or result
scope uses these tokens:

```text
evidence_layer: strict | exploratory | external_probe
claim_status: observation | lead | candidate | strict_result | rejected
tool_status: maintained | historical
result_status: active | completed_version | frozen_version | stopped_design
```

Give different scopes separate rows rather than joining statuses into a new
phrase. `none` can state that no implemented tool exists; it is not a
lifecycle status. Qualifications belong in `result_scope`, not the token.

## Required Program Card

Each active card accounts for these fields. Related fields can share a
section, but the information must remain identifiable and cannot be supplied
only by an unlinked note:

```text
exact_question
relation_to_core
evidence_layer
claim_status
tool_status
result_status
result_scope
conceptual_dependencies
software_dependencies
notes_in_reading_order
tools_and_tests
frozen_artifacts_and_corpus_availability
retained_negative_or_rejected_findings
open_proof_or_measurement_obligations
allowed_claim_language
forbidden_claim_language
next_admissible_experiment
stop_rule
```

Subject-area routers such as [README.md](../../research/geometry/README.md) are domain maps,
not program cards unless they explicitly identify themselves as a program.
They route to cards without repeating this schema.

Conceptual and software dependencies are separate: a later question can
continue an earlier idea without importing its program; tools can be siblings
over shared utilities rather than a pipeline.

The [detailed lens reference](../research/LENSES.md) remains authoritative for
hypotheses, false-positive guards, graph observables, queries, metrics,
controls, promotion criteria and kill criteria. This card schema routes
lifecycle and evidence; it does not replace those design fields. The detailed
reference cannot be retired until every still-live lens has transferred its
contract or records an explicit disposition.

## Evidence And Availability

A card routes; it does not replace evidence. Each material result points
directly, or through a linked file-level evidence index, to the exact detailed
note, tool, test, corpus, preregistration, saved report and analysis needed to
audit it. Record missing tests, inputs and derived reports explicitly; a move
to another directory does not resolve their absence.

Use the [corpus inventory](../../research/experiments/CORPUS_INVENTORY.md) for
source identities and known availability. The
[graph-corpus contract](../software/GRAPH_CORPUS.md) owns operand, retention
and completeness rules. The [graph-invariant protocol](graph-invariants.md)
owns measurement definitions. The [branch evidence protocol](branch-evidence.md)
and [Order-4 projection protocol](order4-projection.md) supply their specialized
requirements.

## Analysis Must Return To The Graph

```text
strict-stage Modulus of One graph
-> edge-derived analysis signal
-> candidate structure or region
-> exact nodes and edges
-> graph-context inspection
```

A candidate is a reason to inspect, not the conclusion. Each tool states the
corpus it reads, the edge records it uses, its projection or filter, the nodes
or neighborhoods returned for inspection, and what it refuses to conclude by
itself. Without that exact context, an output is not yet useful Modulus of One evidence.

Tools may filter neighborhoods, project edges into temporary signals, rank
places for inspection, compare confirmation across stages, seek structural
signatures, and use external concepts as labels after inspecting graph
structure. Counts, scores, spectra, constants, geometry/prime labels and
convergence language serve as scouting or interpretation aids.

Tools must not:

- treat speculative nodes as eligible operands of strict-stage Modulus of One;
- replace edge inspection with value lists or hide edges behind a summary;
- turn external labels into runtime semantics;
- use target constants as the first definition of Modulus of One importance;
- claim a score, spectrum or metric is Modulus of One structure by itself;
- discard self-reference to `1`.

Speculative nodes are inspected rather than reused as strict operands until
the field rule promotes them. External analysis does not change this runtime
rule.

## Reading The Evidence

Value matches, decimal proximity, high counts, visual patterns and external
labels are weak signals. Stronger evidence includes exact construction
edges, coherent neighborhoods, clear confirmation status, repeated behavior
across stages, traceable relation to `1`, and survival under changed
inspection projections. A weak signal can remain a useful scout while its
graph meaning is unresolved.

The Modulus of One strengthening ladder is:

```text
value appears
-> value appears with a witness
-> witness belongs to the relevant branch
-> branches interact through shared witnesses or timing
-> the branch interaction organizes further emergence
-> projected form predicts new witnessed structure
```

Ask of a report: What order supports this object? What branch relation is
being tested? Which witness produced it? Did it emerge through the branch
being studied, or is it visible through the counting spine? Is the desired
relation permitted but unwitnessed in this field? Is this an interaction or
an inferred projected form, and does it organize further emergence?

If these questions are unanswered, the report is bookkeeping rather than a
Modulus of One result. The relevant evidence protocol, not impressive structure or a
position in this ladder alone, governs promotion.

## Machine Terms And Modulus of One Reading

Machine fields can remain stable in code and JSON. Interpretation translates
them back to the construction being inspected:

| Machine or report term | Modulus of One reading |
| --- | --- |
| `core_confirmation_only` | Witnessed through the counting spine. |
| `self_product_edge` | Witnessed through the self-relation branch. |
| `valid but not retained` | Permitted but not witnessed in this field. |
| `provenance` | The retained witness record. |
| `retention` / `aperture` | The field of observation. |
| `controls` | Checks against ordinary explanations. |
| `holdout` | Held-out or future witnessed structure. |
| `projected constant` | Proposed projected form. |

The machine field is bookkeeping, not the concept. In particular, local
operation provenance does not automatically select a supplying ancestral
witness. The [runtime identity contract](../software/RUNTIME.md) states what
is represented; the [epistemic-order note](../foundations/EPISTEMIC_ORDER.md#construction-and-report-language)
interprets `grounded` and `speculative` labels.

## Standard Analysis Output

New analysis tools should prefer:

```text
tool_name
graph_corpus
projection_or_filter
candidate_id
why_flagged
nodes
edges
neighborhood_query
confirmation_status
interpretation_limits
```

`nodes`, `edges`, `neighborhood_query` and `interpretation_limits` keep the
tool accountable to the graph.

## Domain Interpretation Rules

| Kind of analysis | Boundary |
| --- | --- |
| Geometry | Circle, square, triangle and area language labels speculative subsets of emergent patterns unless the graph context earns the interpretation. |
| Prime and Fermat probes | Prime, Fermat, Goldbach, Sophie Germain, twin-prime and related concepts are inspected through nearby graph structure; a known-number-theory property test alone does not constitute Modulus of One research evidence. |
| Convergence | Record Modulus of One structure before comparing external constants. Proximity to `pi`, `e` or another constant requires shared construction context, edge structure or persistent graph behavior to acquire Modulus of One significance. |
| Spectral scouts | An edge-derived spectrum identifies where to look; meaning comes from the returned graph neighborhood. |
| Historical closure | Useful hypotheses may survive, but reuse of speculative outputs makes such studies historical exploratory artifacts, not aligned strict-stage computation. |

The [research map](../../research/README.md) routes to current program cards,
tools and detailed evidence rather than duplicating their inventories here.

## Seventeen-Lens Ownership Ledger

Every existing level-three lens entry in the
[detailed reference](../research/LENSES.md) remains accounted for below.
Ownership is not proof that its design contract has transferred into the
card. Keep this ledger until a separate reviewed change retires or replaces
the detailed reference with complete accounting.

| Existing lens | Current owner |
| --- | --- |
| Rational Baseline Lens | [Strict-stage core corpus](../../research/strict_stage/core_corpus/README.md) |
| Temporal Confirmation Lens | [Strict-stage core corpus](../../research/strict_stage/core_corpus/README.md) |
| Operation Ecology Lens | [Strict-stage core corpus](../../research/strict_stage/core_corpus/README.md) |
| Gauss Congruence / Modulus-One Control | [Number theory](../../research/number_theory/README.md) |
| Phase Metric Collapse / Triangle-Inequality Lens | [Circle as one](../../research/geometry/circle_as_one/README.md) |
| Quadratic Shell Lens | [Shell geometry](../../research/geometry/shell_geometry/README.md) |
| Quadratic-Form Class-Channel Lens | [Quadratic forms](../../research/number_theory/quadratic_forms/README.md) |
| Theta-Weil Cross-Term Calibration | [Quadratic forms](../../research/number_theory/quadratic_forms/README.md) |
| Euler Reciprocal Mass Lens | [Euler reciprocal and zeta work](../../research/euler/README.md) |
| Zeta Critical-Strip External Probe | [Euler reciprocal and zeta work](../../research/euler/README.md) |
| Zeta Cancellation-Arrival Probe | [Euler reciprocal and zeta work](../../research/euler/README.md) |
| Centered Reciprocal-Shell Interaction Lens | [Euler reciprocal and zeta work](../../research/euler/README.md) |
| Order-4 Projection Lens | [Order-4 projection protocol](order4-projection.md) |
| Stage Dynamics Lens | [Dynamics](../../research/dynamics/README.md) |
| Phase Operator-Descent / Provenance-Transport Lens | [Circle as one](../../research/geometry/circle_as_one/README.md) |
| Motif / Hinge Lens | [Motif and hinge reproduction](../../research/motif_hinge/README.md) |
| Aperture Lens | [Strict-stage core corpus](../../research/strict_stage/core_corpus/README.md) |

Count: `17 / 17` existing lens entries assigned. Their detailed criteria
remain in the reference unless explicitly transferred.

## Promotion And Retirement

A program enters the active map when its question, boundaries and stop rule
are explicit. A claim is promoted only through its relevant evidence protocol.
A program leaves the active map only when its card records why:

```text
question answered
question absorbed by a named successor
design exhausted under a named stop rule
question shown incoherent or inadmissible
```

Archiving a note does not substitute for that disposition. Keep the exact
versioned evidence, including negative or rejected findings, available through
the owning card and archive routes.
