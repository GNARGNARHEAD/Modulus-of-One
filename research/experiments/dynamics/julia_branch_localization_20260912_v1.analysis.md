# Julia sets as MoO inspection lenses: finite localization v1

Status: exploratory external calibration with exact strict-graph witnesses.
No new MoO branch, completed Julia set, Mandelbrot set, or chaotic effect is
claimed. The result is a concrete design for a witness-preserving inspector.

## Question

Can the quadratic Julia/Mandelbrot family help locate and distinguish repeated
relations in the broader MoO field? Which distinctions would an inspector need
to preserve rather than flatten into a fractal picture?

The governing distinction is between a repeated witnessed relation, the rule
that reuses state, and a projection of that state. These can meet without
becoming the same object. Julia and Mandelbrot are external views over a
declared recurrence family; their names do not establish MoO branches.

## Corpus and frozen test

The [preregistration](julia_branch_localization_20260912_v1.pre.md) specifies
the cases before this measurement. The earlier q=7, seed=1 example from the
conversation was already known and is explicitly excluded from novelty claims.

The experiment used three immutable corpora:

| Corpus | Complete stage | Value bound | Queried relations | Retained relations |
| --- | ---: | ---: | ---: | ---: |
| pascal_edge_probe_u300.sqlite | 300 | 1e9 | 148 | 123 |
| circle_as_one_u40_wide.sqlite | 40 | 40 | 148 | 104 |
| circle_as_one_u80.sqlite | 80 | 4 | 148 | 86 |

Every database was opened with `mode=ro&immutable=1`. SHA-256 hashes before
and after inspection agree. No corpus or core runtime file was changed.
Actual configs, schema metadata, exact commands, and source hashes are in the
[machine report](julia_branch_localization_20260912_v1.json). A
[compact report](julia_branch_localization_20260912_v1.summary.json) retains
the selected trajectories and witness registry and is bound to the full report
by SHA-256.

The [analysis source](julia_branch_localization_20260912_v1.analysis.py) is
stdlib-only apart from the existing shared graph-evidence interface. It is a
retained experiment source, not a runtime extension. All external calculations
are explicitly separate from database witness queries.

## Metrics and validation

The primary descriptive metric is the consecutive prefix of a declared
recurrence whose primitive operations have exact retained witnesses at a
checkpoint. For a phase return, all integer operations and division-output
witnesses through the repeated phase are required.

Checkpoints are U2,U4,U8,U16,U40,U80,U256,U300, clipped to each corpus's
complete frontier. Corpus-wide node payloads are not interpreted as checkpoint
confirmation. Presence is checked against each actual edge stage.

Known-answer checks passed for 32 doubling profiles, exact quadratic cycles,
certified escape, finite unresolved status, and arithmetic and positive-spine
operand confirmation of every returned edge. This was not a full repository
test run. No statistical significance or predictive superiority was tested.

## Finding 1: a clear branch distinction survives the projection

Start with confirmed integer 2, retaining a common divisor 7.

| Reading | Integer self-addition | Integer self-multiplication |
| --- | --- | --- |
| Source lineage | 2,4,8,16 | 2,4,16 |
| Division outputs | 2/7,4/7,8/7,16/7 | 2/7,4/7,16/7 |
| Phase readout modulo 1 | 2/7,4/7,1/7,2/7 | 2/7,4/7,2/7 |
| External return period | 3 | 2 |
| All displayed witnesses available | U16 in U300 and U40 | U16 in U300 and U40 |

The two first operations land on 4 at U2 through different witnesses. The
lineages subsequently separate and meet again at 16, with different operation
words and recurrence lengths. This is a finite witnessed distinction, not a
conclusion drawn from a value list.

Selected U300 witnesses:

| Relation | Edge ID | Stage |
| --- | ---: | ---: |
| 2+2 -> 4 | 10 | 2 |
| 2*2 -> 4 | 12 | 2 |
| 4+4 -> 8 | 50 | 4 |
| 8+8 -> 16 | 226 | 8 |
| 4*4 -> 16 | 52 | 4 |
| 2/7 -> 2/7 | 181 | 7 |
| 4/7 -> 4/7 | 189 | 7 |
| 8/7 -> 8/7 | 225 | 8 |
| 16/7 -> 16/7 | 929 | 16 |

In the division rows, the left expression denotes the operation on integer
numerator and denominator, and the right expression denotes its rational
result node. Fractions are recorded outputs throughout; no rational output is
reused as a strict operand. Source lineages select compatible primitive edges
across stages; they are not logs of repeated runtime replay.

The exact external circle projection is P(t)=exp(2*pi*i*t). It obeys
P(2t)=P(t)^2. Consequently the self-addition column corresponds to the
quadratic map z -> z^2 on its Julia circle. The self-multiplication column
instead induces residue squaring n -> n*n modulo the retained denominator.
It must not be called the same Julia dynamics merely because it contains
squaring. The unit-circle and doubling relationship is standard mathematics;
see [Milnor's notes, pages 3 and 12](https://www.math.stonybrook.edu/~jack/DYNOTES/dn4a.pdf).

This corrects a potentially loose reading of the earlier discussion: the
native witnesses verified for the circle-doubling connection belong to integer
self-addition. Complex self-multiplication is the external projected reading.

## Finding 2: a witnessed return and a critical escape can coexist

For f(x)=x*x-6, starting at 3 gives a fixed point:

```text
3*3 -> 9        U3, edge 28
9-6 -> 3        U9, edge 279
```

Both witnesses are retained in U300 and U40, with confirmed positive operands.
The negative parameter itself has the witness 3-9 -> -6 at U9, edge 303 in
U300. The chosen recurrence normal form uses subtraction of confirmed 6; it
does not reuse the speculative node -6 as an additive operand.

The external critical trajectory for the same parameter is 0,-6,30,...,
which is certified to escape. Therefore c=-6 lies outside the Mandelbrot set
even though f has a bounded orbit at 3. Its derivative at that fixed point is
6, so the point is repelling, not attracting. Standard complex dynamics places
repelling periodic points in the Julia set. These are external mathematical
interpretations of the finite witness certificate, not a claim that MoO has
constructed that Julia set. The definitions and critical-orbit criterion are
given in [Belk's notes](https://e.math.cornell.edu/people/belk/dynamicalsystems/NotesJuliaMandelbrot.pdf),
and the repelling-periodic-point characterization in
[Milnor's notes](https://www.math.stonybrook.edu/~jack/DYNOTES/dn4a.pdf).

The parameters c=m-m*m for m=1..6 were explicit forced-fixed-point controls.
Their return certificates are all present in U300 and U40; for m>=3 their
critical trajectories escape. Their existence follows from the selected
parameters and must not be presented as a discovered MoO pattern.

For c=-2, the smaller certificate 2*2 -> 4, 4-2 -> 2 is complete at U4
(U300 edges 12 and 43). This provides another directly inspected point of
contact with classical Julia dynamics.

The inspection consequence is precise: a parameter label is insufficient.
Preserve the map, starting state, parameter witness, and operation normal form.
A return is also insufficient to infer attraction.

## Finding 3: different Julia shapes can share a projected recurrence

There is a second exact bridge, established algebraically rather than inferred
from these database measurements. Let H(z)=z+1/z for z != 0. Then

```text
H(z*z) = H(z)*H(z) - 2.
```

On the unit circle H(z)=2*cos(theta), so H maps that circle onto [-2,2],
identifying z and 1/z. The c=0 Julia circle and c=-2 Julia interval are thus
related by an explicit fold intertwining the two maps. This is a
semiconjugacy, not a one-to-one identification of their states. The two Julia
sets are standard examples in [Levenberg's notes, page 32](https://www.math.stonybrook.edu/~ebedford/PapersForM543/LevenbergNotes.pdf).

A visually different shape need not indicate an independent construction
lineage. An inspector should expose what its projection identifies, including
the orientation and inverse choices lost in this fold. General Julia sets are
not asserted to be such simple folds.

## Finding 4: field limits can hide one branch while leaving its values

U80 is deeper than U40 but has a tighter absolute-value bound. In U80, nodes
9 and 16 are present, but 3*3 -> 9 and 4*4 -> 16 were excluded at their
candidate stages by retention. In U40 those edges are retained.

Likewise, 16/7 is visible in U80 while the declared numerator lineages do not
have complete witness support. Both q=7 phase-return certificates fail the
complete-witness check in that corpus. Plotting only their rational endpoints
would conceal this loss of branch evidence.

For x -> x*x+1 from seed 1, the external values begin 1,2,5,26,677. U300
supports the first three transitions. It records 26*26 -> 676 at U26, but
676+1 -> 677 requires operand confirmation at U676. In U40 and U80 even the
676 self-product output is filtered. These are different blockers.

For x -> x*x-1 from seed 1, the first transition to 0 is witnessed, but the
next square uses an operand outside the positive-spine rule. For squaring from
1/2, the first transition is already outside that operand rule, even where
both input and output values are recorded.

All missing queried relations were explained by stage, retention, or operand
policy. No unexplained eligible edge absence was found in these selected cases.

## Failed and negative findings

- All 32 sampled doubling return profiles match the denominator baseline.
  For reduced denominator 2^s*m, the transient is s and the eventual period is
  the multiplicative order of 2 modulo odd m (period 1 for m=1). These returns
  provide exact calibration, not evidence of an additional MoO effect.
- Rational squaring is not a well-defined operation on general phase classes:
  1/3 and 4/3 have the same phase, but their squares have phases 1/9 and 7/9.
  Their proposed square edges also fail the strict operand rule. Numerator
  squaring at a retained common denominator is a different finite construction.
- None of the critical orbits is represented as a native complex runtime
  orbit. Their exact rational-component calculations are external controls.
- The c=1/4 critical orbit produced no cycle or escape in eight steps. Its
  finite detector therefore reports unresolved. A separate proof that
  [0,1/2] maps into [1/4,1/2] certifies boundedness. Finite non-escape alone
  would not have done so.
- A finite collection of rational phases cannot establish the completed Julia
  boundary. Rational doubling samples also have finite eventual periods, so
  their behavior cannot be generalized to all real phases without argument.
- Forced periodic points and familiar phase cycles do not establish new
  branch families, importance rankings, or predictive organization.

## Decision: a finite witness inspector is justified

The useful location is the interaction of witnessed self-addition,
self-multiplication, subtraction, recurrence scheduling, and declared
projections. A minimal inspector should preserve:

1. The exact repeated relation and fixed parameter, with its construction.
2. Starting state and the distinction between recurrence step and MoO stage.
3. Primitive construction edges, intermediate nodes, and confirmation status.
4. The explicit projection, retained divisor/lift, and what it forgets.
5. Separate outcomes for exact return, projected return, certified escape,
   finite unresolved behavior, and incomplete graph witness support.

A Julia view can compare seeds under one fixed map. A Mandelbrot view can
compare the critical orbit across parameters. Neither view should use a
visual arm, period, or color region as the definition of a MoO branch.

## Next question

The next admissible experiment would test whether a predeclared Julia-derived
partition organizes independently selected graph neighborhoods better than
denominator, construction-cost, stage, and operator controls. That experiment
has not been designed or run here. The present result supports a careful
inspection instrument and a specific set of mathematical connections.
