# Phase Metric Collapse: Triangle Inequality And Graph-Retained Difference

> Status: active external metric lens with a read-only strict-graph probe.
>
> evidence_layer: exact external phase metric over strict graph
>
> claim_status: observation
>
> Primary artifacts:
> `../../moo_phase.py`,
> `../../moo_phase_metric_probe.py`,
> `../../test_moo_phase_metric_probe.py`, and
> `../../out/experiments/phase_metric_collapse_u40_wide_d12_v1.json`.

## Verdict

The triangle inequality does not explain `Ref(1)`, construct a circle inside
Modulus of One, or add a metric to the runtime. It does provide an exact external
instrument for asking what a modulus-one observer forgets.

For rational values, define:

```text
phase(x) = x mod 1 in [0, 1)

d_phase(x, y) = min over n in Z of abs(x - y - n)
```

This is the shortest-arc metric inherited from `R/Z`, restricted to `Q/Z`.
Its pullback to source rationals is a pseudometric:

```text
d_phase(x, y) = 0 exactly when x - y is an integer.
```

Therefore two distinct graph nodes may have zero phase distance while retaining
different arrival stages, confirmation states, incoming edges, operation
signatures, and shared-input neighborhoods. Those retained construction
differences, not the forced metric identity, are the object of inspection.

The first U40 report demonstrates that the instrument works, but it does not
yet show a special within-fibre graph effect. Bounded same-phase pairs and their
successfully matched different-phase controls have similar neighborhood-
distance medians. The result is therefore a calibrated observation and a
sharper next experiment, not a promotion of circle geometry into Modulus of One.

## Lens Card

```text
name:
  phase metric collapse / triangle-inequality lens

evidence_layer:
  exact external phase metric over strict graph

claim_status:
  observation

provocative_hypothesis:
  Distinct source nodes that become zero-distance observations modulo one may
  retain systematic graph-visible construction differences.

false_positive_guarded_against:
  Treating the guaranteed metric identity as discovered structure; calling
  bounded graph divergence a global maximum; confusing Z/1Z, Q/Z, complex
  unit modulus, and Ref(1); or calling an external return orbit a runtime path.

graph_native_observable:
  exact node ids and values; checkpoint status; first and confirmed stages;
  incoming edge references; operation counts; direct-input sets;
  shared-input-result neighborhoods; recorded +1 translation edges.

query_or_report:
  python3 -m moo.phase_metric_probe --db <corpus.sqlite> \
    --max-denominator 12 --max-phase-classes 16 \
    --pairs-per-phase 4 --pretty

metric:
  exact circular phase distance in turns; source absolute distance;
  routed triangle slack; direct-input Jaccard distance; shared-input-result-
  neighborhood Jaccard distance; operation-signature total variation.

null_model_or_control:
  integer Z/1Z one-class control; source absolute-distance triangle slack;
  deterministic different-phase controls matched on left anchor, reduced
  denominator, and integer lift; multiplication non-descent witness; fixed
  exact metric calibration cases.

promotion_criteria:
  A preregistered checkpoint/corpus sweep finds a repeatable paired difference
  between same-phase and exposure-matched different-phase graph structure,
  with explicit coverage and held-out or permutation controls.

kill_criteria:
  The effect remains comparable to matched controls, disappears under nearby
  corpus bounds, depends on identity-fibre domination, or requires treating
  speculative rational nodes as operands without an explicit runtime change.

allowed_claim_language:
  "These distinct source nodes have zero exact phase distance and retain these
  named graph differences at checkpoint U."

disallowed_claim_language:
  "Modulus of One has constructed the circle," "zero phase distance means equal source
  nodes," or "the triangle inequality was discovered by the corpus."
```

## Exact Mathematical Layer

### Phase length and distance

The exact length of a phase from the identity is:

```text
ell(x) = min(phase(x), 1 - phase(x)).
```

It lies in `[0, 1/2]`. The pair distance is:

```text
d_phase(x, y) = ell(x - y).
```

The implementation uses `fractions.Fraction`; no chord-length or trigonometric
float is introduced. It verifies symmetry, identity on quotient classes,
translation invariance, contraction against source absolute distance, and the
triangle inequality:

```text
d_phase(a, c) <= d_phase(a, b) + d_phase(b, c).
```

`Q/Z` itself is not called a geodesic space. It is a rational, totally
disconnected subgroup carrying the restriction of the ambient shortest-arc
metric from `R/Z`.

### Routed slack

For a routed comparison `start -> via -> end`, define:

```text
slack = d(start, via) + d(via, end) - d(start, end).
```

`slack = 0` means the sampled route is tight under the selected metric.
Positive slack means the endpoint comparison is shorter than the two sampled
legs. On the phase quotient this can arise from cancellation, wrap, or loss of
orientation. The scalar alone does not decide which.

### Sampled returns and lost lift

A retained sequence of phase samples can have positive accumulated phase length
and zero endpoint distance. This gives the lost-lift problem an exact metric
form. But endpoint sampling can also alias an entire continuous turn:

```text
samples [0, 1]:
  source lift step = 1
  phase endpoint step = 0
```

The probe therefore labels its finite return walks as external and sampled.
For a canonical representative `p/q` in `[0,1)`, repeated lifts `k*p/q` end at
integer `p`. That net lift is convention-dependent: `2/3` and `-1/3` name the
same phase but natural repeated lifts end at `+2` and `-1`. Only the phase
sequence, additive order `q`, and return to identity are quotient invariants.

At phase `1/2`, either shortest orientation has equal length. The probe marks
that antipodal ambiguity explicitly.

## What The Probe Reads

The tool opens one graph-first strict SQLite corpus read-only and requires the
positive-spine alignment check to pass. Every report has a checkpoint `U`.

Node scope:

```text
first_stage <= U
reduced denominator <= configured maximum
```

Incoming operation counts, edge references, direct inputs, and neighborhoods
are all filtered to `edge.stage <= U`. Eventual `confirmed_stage` remains
visible as a corpus field, but candidate status and ranking use confirmation
only when it has occurred by `U`.

This distinction prevents future confirmation from leaking into an earlier
checkpoint ranking.

## Zero-Distance Pair Search

An exhaustive same-phase pair search grows as:

```text
sum over fibres of choose(fibre_size, 2).
```

The identity fibre dominates that count. The probe therefore uses a named,
bounded candidate policy:

```text
all consecutive observed lifts
+ fixed landmarks:
    minimum / maximum lift
    earliest / latest first stage
    minimum / maximum incoming count
    one checkpoint-status representative
-> bounded metadata preselection
-> exact graph scoring
```

At least one adjacent-lift candidate is retained per reported fibre when one is
available. The report gives total possible pairs, adjacent pairs, candidate
pairs, exact-scored pairs, and one of:

```text
exhaustive
adjacent_plus_landmarks_complete
bounded_adjacent_plus_landmarks
```

No bounded winner is described as a global maximum.

## Graph Divergence Returned For Inspection

Each exact-scored pair returns:

```text
nodes:
  node ids, exact values, phases, integer lifts, kind, checkpoint status,
  first stage, eventual confirmed stage, incoming operation counts

edges:
  bounded incoming edge references for both nodes
  direct +1 translation witness when the lift gap is one

direct inputs:
  set sizes, intersection, union, exact Jaccard similarity/distance,
  sampled node ids

shared-input-result neighborhood:
  set sizes, intersection, union, exact Jaccard similarity/distance,
  sampled node ids

supporting differences:
  checkpoint-status mismatch
  checkpoint confirmation gap
  first-stage gap
  incoming-edge-count gap
  raw operation-count L1
  normalized operation-signature total variation
```

Ranking is lexicographic and explicitly not a composite metric. The primary
field is defined shared-input-result-neighborhood Jaccard distance, followed by
minimum neighborhood support and the named supporting fields.

## Matched Different-Phase Controls

For a same-phase pair `(left, right)`, the control keeps `left` fixed and seeks
a different-phase replacement for `right` with:

```text
same reduced denominator
same integer lift
nearest checkpoint status
nearest first stage
nearest incoming-edge exposure
```

Exact match quality and all residual gaps are reported. No caliper is silently
imposed in v1.

Denominators `1` and `2` have only one reduced phase in their exact-order
stratum. Their lack of a different-phase control is classified as
`structurally_not_applicable`, not a corpus failure. For larger denominators, a
missing checkpoint node is classified separately as `corpus_match_missing`.

Only the successfully paired population is used for the same-versus-control
median comparison.

## Additive Triangle Audit

For every recorded `+` and `-` occurrence through checkpoint `U`, the tool
compares two routed metrics:

```text
source real line:
  0 -> left -> result using abs(x-y)

phase quotient:
  0 -> left -> result using d_phase(x,y)
```

The operation relation is validated first. A malformed operation occurrence is
reported and excluded from operation-specific slack aggregates; any relation,
step, or triangle failure marks the additive audit `fail`.

Only `+` and `-` are admitted. Ordinary rational multiplication and division do
not descend to `Q/Z`; the report includes the exact negative control:

```text
1/2 ~ 3/2 mod Z

(1/2)*(1/2) = 1/4
(3/2)*(1/2) = 3/4

d_phase(1/4, 3/4) = 1/2.
```

## Current Runtime Aperture

The aligned strict corpus uses only confirmed positive-spine integers as
operands. Every such operand has identity phase. Rational phase nodes are
recorded as results but are not reused as operands.

Consequently:

```text
nonidentity additive operand edges = 0
```

in the current report. This blocks nontrivial graph-witnessed additive phase
steps. Even a future positive count would establish eligible additive edges,
not a chained orbit. A witnessed path requires explicit edge chaining, and a
binary construction history is more accurately a proof DAG than an ordinary
node walk.

The external finite return walks remain calibration objects only.

## U40 Wide Report

### Command

```text
python3 -m moo.phase_metric_probe \
  --db out/experiments/circle_as_one_u40_wide.sqlite \
  --max-denominator 12 \
  --max-phase-classes 16 \
  --pairs-per-phase 4 \
  --neighborhood-sample-limit 6 \
  --edge-ref-limit 4 \
  --slack-sample-limit 8 \
  --write research/experiments/phase_metric_collapse_u40_wide_d12_v1.json \
  --pretty
```

### Corpus and search aperture

| field | result |
|---|---:|
| checkpoint | `U40` |
| all source nodes | 1,019 |
| all source edge occurrences | 4,139 |
| strict alignment | pass |
| scanned nodes with denominator `<=12` | 340 |
| observed phase classes | 46 |
| multi-lift phase classes | 46 |
| reported phase classes | 16 |
| possible same-phase pairs in scanned scope | 4,020 |
| adjacent same-phase pairs | 294 |
| exact-scored zero-distance pairs | 64 |
| unique exact-scored/control nodes | 85 |
| matched different-phase controls | 54 |
| structurally inapplicable controls | 8 |
| corpus-missing controls | 2 |

The 64 scored pairs are about `1.59%` of all possible same-phase pairs in the
scanned scope. They are observation-ranked candidates, not an exhaustive
maximum search.

### Metric and graph result

The fixed reference calibration and all 2,448 routed inequalities over the 16
reported phases pass with zero violations. This certifies the exact
implementation, not a new theorem.

Four of the 64 zero-distance pairs cross checkpoint-status categories. All 64
have defined shared-input-result-neighborhood comparisons.

For the 54 successfully paired observations:

| descriptive statistic | median Jaccard distance |
|---|---:|
| same-phase zero-distance pair | `0.6499344864` |
| matched different-phase control | `0.6582890002` |
| per-pair same minus control | `0.0089505924` |

The bounded medians are close. This does not currently support a claim that
zero-distance phase fibres are uniquely coherent or uniquely divergent in the
graph. It does show that zero phase distance can coexist with substantial exact
construction-neighborhood difference.

The highest-ranked nonidentity observation in this bounded search is:

```text
phase:
  1/2

source nodes:
  1/2 and 39/2

phase distance:
  0

shared-input-result-neighborhood Jaccard distance:
  256/319 ~= 0.8025

minimum neighborhood support:
  202
```

It is a candidate for direct graph inspection, not a global extremum or an
independent significance result.

### Additive result

| operation | edges | source tight | source strict | phase tight | phase strict |
|---|---:|---:|---:|---:|---:|
| `+` | 780 | 780 | 0 | 780 | 0 |
| `-` | 1,600 | 0 | 1,600 | 1,600 | 0 |

Every subtraction occurrence loses positive real-line triangle slack after the
integer values are projected to the identity phase. The maximum source slack is
`80`; the maximum phase slack is `0`.

This is a forced consequence of the current operand aperture:

```text
all recorded additive operands are integers
-> every operand and result has phase zero
-> the phase triangle is tight and trivial
```

The useful observation is the contrast: source subtraction/cancellation is
visible on the line and erased by the modulus-one observer. It is not evidence
of hidden dynamics inside the singleton phase trace.

## Relation To The Null-Like Lens

The report supplies a concrete, nonphysical instance of the repository's
null-like framing:

```text
zero under one named observer
+ nontrivial retained graph context
```

For pairs, the named observer is phase distance. For construction paths, more
work is required: a zero-distance endpoint pair is not itself a path, and the
current strict graph does not supply nonidentity rational operand chains. See
[NULL_GEODESIC_LENS_NOTE.md](../spectral/NULL_GEODESIC_LENS_NOTE.md) for the broader framing boundary.

## Next Tests

The highest-value follow-up was not a larger replay of the same pair metric. It
was to identify which source operations actually descend through `Q/Z`, then
test the surviving additive structure against provenance-conditioned controls.
That work is now recorded in
[[PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md](PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md)](PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md).

The exact result is that addition and subtraction descend, retained integers
act by endomorphisms, general multiplication does not descend, and division by
a retained nonzero integer is a finite torsion-preimage relation rather than a
binary quotient operation. The quarantined transport test then used only
external additive `C_q` accumulation over graph-witnessed paths.

Its checksum-bound U40 primary and separately preregistered U80 follow-up both
returned `insufficient_aperture`. U80 supplied enough paths but still put only
`13/68` of holdout positions in mutable exact-stage/exposure/hub strata, below
the frozen `1/4` gate. This distinguishes the bottleneck from mere U40 path
scarcity and fires the preregistered stop rule.

Accordingly, do not run a U300 replay, coarsen stage bins, shorten paths, lower
the mutability threshold, or search alternate seeds under the current design.
A future test is worth opening only if it introduces either a genuinely
graph-native nonidentity transition or an independently frozen corpus/design
that can establish null estimability before inspecting the return outcome.

## Short Version

```text
Triangle inequality supplies the instrument, not the discovery.

Modulo one can make distinct source nodes zero-distance observations.
The strict graph can still distinguish their constructions.

At U40 those graph differences are real, but bounded matched controls are
similar. Nontrivial phase steps are blocked by the current operand rule.

The lens is now falsifiable, checkpoint-scoped, and graph-returning.
It is not runtime circle geometry.
```
