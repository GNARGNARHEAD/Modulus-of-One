# Phase Operator Descent And Provenance Transport

> Status: exact operator boundary plus completed, frozen U40/U80 transport
> design with an insufficient-aperture outcome.
>
> evidence_layer: exact external `Q/Z` algebra over a read-only strict graph.
>
> claim_status: operator facts established; both frozen transport runs were
> insufficient for their registered null, exhausting the current design
> without a retain or kill verdict for the transport effect.
>
> Primary artifacts:
> [`../../moo_phase.py`](../../moo/phase.py),
> [`../../test_moo_phase_operator.py`](../../tests/test_moo_phase_operator.py),
> [`../../moo_phase_transport_probe.py`](../../moo/phase_transport_probe.py),
> [`../../test_moo_phase_transport_probe.py`](../../tests/test_moo_phase_transport_probe.py), and
> the frozen
> [`phase_provenance_transport_u40_q24_l8_v1` preregistration](../experiments/geometry/quarantined_phase_transport/phase_provenance_transport_u40_q24_l8_v1.pre.md).

## Purpose

The phase projection

```text
pi: Q -> Q/Z
pi(x) = [x] = x mod Z
```

retains exact rational phase and forgets integer lift. That quotient has a
well-defined additive group structure, but it does not inherit the complete
four-operator rational arithmetic fan. The distinction is decisive:

```text
+ and -:
  descend as binary operations on quotient classes

integer scaling:
  survives when the integer scalar is retained outside the quotient

general * and /:
  do not descend as binary quotient operations

division by a retained integer:
  survives as a finite torsion-preimage relation, not generally as a function
```

The provenance-transport probe uses only this valid additive layer. It attaches
reduced division-result residues to paths selected from strict graph evidence,
then accumulates those labels externally in ordinary finite cyclic groups. It
does not make rational results into Modulus of One operands and does not call its
provenance walks runtime paths.

This note complements the broader
[[CIRCLE_AS_ONE_QUOTIENT_NOTE.md](CIRCLE_AS_ONE_QUOTIENT_NOTE.md)](CIRCLE_AS_ONE_QUOTIENT_NOTE.md) and the
maintained metric instrument in
[[PHASE_METRIC_COLLAPSE_NOTE.md](PHASE_METRIC_COLLAPSE_NOTE.md)](PHASE_METRIC_COLLAPSE_NOTE.md). The completed
U40 metric observation is also summarized in the
[`external-probe results record`](../../archive/completed_external_calibrations/AUGUST_2026_EXTERNAL_PROBE_DISPOSITIONS.md).
It narrows the operator boundary and records the transport experiment without
promoting it out of quarantine.

## Exact `Q/Z` Operator Descent

Two rationals represent the same phase when they differ by an integer:

```text
x ~ y  iff  x - y is in Z.
```

An operation descends only if changing representatives cannot change the
output class. The implemented classification is:

| Source operation | Global quotient status | Valid retained structure |
| --- | --- | --- |
| `a + b` | descends, single-valued | `[a] + [b] = [a+b]` |
| `a - b` | descends, single-valued | `[a] - [b] = [a-b]` |
| `a * b` | does not descend globally | retained-integer action `mu_n([x]) = [nx]` |
| `a / b` | does not descend globally | finite preimage relation for retained nonzero integer divisor |

The executable classification and exact operations are in
[`moo/phase.py`](../../moo/phase.py). Representative invariance,
counterexamples, kernels, preimages, and branch selection are covered in
[`tests/test_moo_phase_operator.py`](../../tests/test_moo_phase_operator.py).

### Addition and subtraction

For integers `m,n`:

```text
(a + m) + (b + n) = (a + b) + (m + n)
(a + m) - (b + n) = (a - b) + (m - n).
```

The differences from `a+b` and `a-b` are integers, so both output classes are
independent of representatives. Thus `Q/Z` is an additive abelian group, and
`phase_add` and `phase_subtract` are genuine quotient operations.

### Retained-integer scaling

For a retained integer `n`, define:

```text
mu_n([x]) = [n*x].
```

If `x` changes to `x+k`, the product changes by the integer `n*k`, so `mu_n`
is a well-defined group endomorphism. The word retained matters. All integers
have the same quotient class `[n]=[0]`; the phase class alone does not remember
which scalar acts. Therefore `mu_2` and `mu_3` are distinct external actions
even though `[2]=[3]=[0]` in `Q/Z`.

The exact kernel and fibre structure is:

```text
n = 0:
  ker(mu_0) = all of Q/Z
  the preimage of 0 is all phases
  the preimage of a nonidentity phase is empty

n != 0:
  ker(mu_n) = { k/|n| mod 1 : 0 <= k < |n| }
  every target phase has exactly |n| preimages
  every preimage fibre is one coset of ker(mu_n).
```

The implementation materializes these finite families only within an explicit
cap; omission above the cap changes report size, not the exact cardinality.

### Why multiplication does not descend globally

Binary multiplication cannot be defined from two quotient classes alone. For
example, `0 ~ 1`, but:

```text
0 * (1/2) = 0
1 * (1/2) = 1/2,
```

and `0` is not equivalent to `1/2` modulo integers. Multiplication by an
actually retained integer is valid through `mu_n`; multiplication by the
quotient class `[n]` is not the same construction. Consequently `Q/Z` is used
here as an additive group, not asserted to be a ring under ordinary rational
multiplication.

## Division Is A Torsion-Preimage Relation

General binary division has the same representative problem. Even the simple
equivalence `0 ~ 1` gives inequivalent results after division by `2`:

```text
0/2 = 0
1/2 = 1/2.
```

With a retained nonzero integer divisor `n`, however, division has a precise
relational form. A candidate result phase `y` must satisfy:

```text
mu_n(y) = [source].
```

There are exactly `|n|` such phases. Division is therefore a finite
torsion-preimage relation. It is single-valued from phase data only for
`|n|=1`. When `|n|>1`, the retained integer lift of the source selects one
branch.

The `integer_division_branch(source, divisor, result)` helper first verifies
the source arithmetic exactly:

```text
result == source / divisor.
```

Only then does it classify the phase relation. If
`source = source_phase + source_integer_lift`, its branch index is:

```text
source_integer_lift mod |divisor|.
```

This prevents a phase narrative from repairing or concealing an invalid
source edge.

### Full divisor branch versus reduced transport coordinate

For a strict integer division occurrence:

```text
a / b = p / q
g = gcd(a,b)
p = a/g
q = b/g,
```

there are two related but non-interchangeable descriptions:

```text
full retained-divisor relation:
  mu_b(y) = [a]
  fibre cardinality = b
  selected branch index = a mod b

reduced result phase used by transport:
  [p/q]
  exact reduced denominator = q
  C_q residue = p mod q.
```

Cancellation can make these sizes different. For example:

```text
6/15 = 2/5

full relation:
  15 preimages under mu_15, selected branch 6

reduced transport label:
  q = 5, residue = 2.
```

The full `b`-branch record says how the retained integer source and divisor
select the observed quotient phase. The reduced `(q,residue)` pair says where
that observed result sits in its exact finite cyclic return group. The
transport probe audits both, but it uses only the reduced coordinate as its
external step label. It never substitutes `q` for the full divisor, nor the
reduced residue for the full branch index.

## Provenance-Ordered `C_q` Prefix-Return Test

The transport experiment asks a deliberately narrower question:

> After conditioning on exact denominator `q`, does strict graph provenance
> order the externally attached residues so that proper-prefix returns occur
> more often than under ordinary cyclic controls?

It does not ask whether rational phases operate in aligned Modulus of One.

### Read-only source and operator audit

[`moo/phase_transport_probe.py`](../../moo/phase_transport_probe.py) opens the
SQLite corpus in read-only/query-only mode and scopes source evidence to a
strict checkpoint. It rejects speculative or non-positive-spine source
operands, dangling references, checkpoint-arrival inconsistencies, invalid
division arithmetic, noncanonical results, reduced-denominator/residue
mismatches, and full torsion-branch mismatches.

Eligible occurrence nodes are recorded division edges whose reduced result
phase has exact denominator `q` in the configured range, beginning at `q=3`.
The rational result is an inspected edge result, never a new operand.

### Q-conditioned, residue-blind graph paths

The exact denominator defines a conditioning stratum, so the selection is
properly described as **q-conditioned and residue-blind**, not phase-blind
across all denominators.

Within each `q`:

1. Occurrences are capped by deterministic hashes of canonical source-edge
   content. SQLite edge ids remain evidence identifiers but do not control
   selection.
2. Two occurrences are adjacent when their recorded division edges share an
   exact confirmed input node.
3. An oriented arc requires a strictly increasing source stage. Same-stage
   SQLite insertion order is not treated as time.
4. Outgoing degree and seed order are deterministically hash-capped without
   consulting residue, endpoint, or return count.
5. Accepted fixed-length paths have distinct edge occurrences, distinct result
   values, an exact shared-input witness for every transition, and are
   occurrence-disjoint within `q`.

These are composable paths in a graph of source-edge occurrences. They are not
recorded rational-operation chains and not runtime trajectories.

### External statistic

For a selected path with reduced residues `s_1,...,s_L` in `C_q`, the probe
computes outside Modulus of One:

```text
X_0 = 0
X_t = X_(t-1) + s_t mod q.
```

Its score is the number of proper-prefix returns:

```text
R(P) = count of t in [1,L-1] such that X_t = 0.
```

The endpoint is excluded because permuting an exact step multiset leaves its
total sum, and therefore its endpoint, unchanged. Scores are divided by
`L-1`, averaged within each `q`, then averaged equally across holdout `q`
values so a large denominator fibre cannot dominate merely by supplying more
paths.

### Split and controls

A stable SHA-256 hash of the seed, `q`, and complete canonical source-edge
sequence assigns each accepted path to discovery or holdout. Only holdout paths
enter the decision statistic.

The two frozen aggregate nulls are:

1. **Exact-step permutation.** Keep each path, `q`, length, endpoint, and exact
   residue multiset fixed; independently permute only step order. This is the
   direct ordinary-`C_q` composition control.
2. **Stage/exposure/hub-stratified label shuffle.** Keep paths fixed and shuffle
   residues only among eligible occurrences matching `q`, exact source stage,
   `floor(log2(max(1, checkpoint exposure)))`, and
   `floor(log2(max(1, shared-input hub degree)))`. This controls generator
   stage, result exposure, and shared-input concentration.

The decision aperture requires all of:

```text
at least 32 holdout paths
at least 4 distinct holdout q values
at least 16 mutable label-shuffle positions
at least 25 percent mutable holdout positions.
```

Given sufficient aperture, retention requires the observed statistic to exceed
both the mean and the 99th percentile of both nulls. Otherwise the frozen rule
kills the current provenance-conditioned hypothesis. Insufficient aperture is
reported separately.

## Frozen Primary And Quarantine Boundary

The primary configuration is frozen in the linked preregistration:

```text
experiment: phase_provenance_transport_u40_q24_l8_v1
corpus: out/experiments/circle_as_one_u40_wide.sqlite
checkpoint: U40
q: 3 through 24
path length: 8
occurrence cap: 512 per q
outgoing-degree cap: 32 per occurrence
path cap: 64 per q
null samples: 4096
stage-bin width: 1, exact source stage
seed: 1729.
```

Before the scored report, the preregistration received a semantic clarification:
selection is q-conditioned/residue-blind; only strict stage increase orients an
arc; and canonical source-edge content, not SQLite insertion ids, controls
hashes. No corpus, statistic, threshold, cap, seed, null, or decision rule was
changed.

The probe binds a decisive primary result to the expected experiment id,
corpus path and SHA-256, corpus schema/configuration, strict frontier-stage
contract, preregistration SHA-256, checkpoint, and frozen parameters. A run
that fails this identity preflight may still produce bounded diagnostics, but
it cannot emit the frozen make-or-break decision.

### Corrected frozen U40 result

The checksum-bound U40 run passed its frozen identity preflight and was
eligible to issue the preregistered primary decision. Its graph aperture was:

```text
eligible division occurrences:
  984

selected after caps:
  984

accepted paths:
  55

holdout paths:
  28

holdout q values:
  14

mutable holdout positions:
  24 / 224 = 3/28
```

The exact holdout statistic and controls were:

```text
observed:
  9/56

exact-step permutation:
  mean = 39545/344064
  99th percentile = 197/1176
  upper-tail p = 88/4097

stage/exposure/hub-stratified shuffle, after the canonical-pool fix:
  mean = 391903/2408448
  99th percentile = 75/392
  upper-tail p = 2352/4097
```

The observed value exceeds the exact-step mean but not its 99th percentile. It
exceeds neither the corrected stratified mean nor the corrected stratified
99th percentile. Those comparisons are descriptive here: the frozen decision
does not reach the retain/kill branch because the aperture gate fails first.

```text
failed aperture checks:
  holdout paths: 28 < 32
  mutable fraction: 3/28 < 1/4

frozen U40 decision:
  insufficient_aperture
```

This is neither retention nor a kill of the provenance-conditioned candidate.
It says that the frozen U40 strict-path sample cannot estimate the registered
decision at its required aperture.

### Separately preregistered U80 aperture-resolution follow-up

One follow-up was frozen specifically to test whether a larger strict
checkpoint resolves the U40 aperture failure. Its protocol is in
[`phase_provenance_transport_u80_q24_l8_v1_followup.pre.md`](../experiments/geometry/quarantined_phase_transport/phase_provenance_transport_u80_q24_l8_v1_followup.pre.md).
It keeps the U40 path definition, statistic, controls, thresholds, caps, null
count, stage-bin width, and seed unchanged; it does not pool U40 and U80.

The checksum-bound U80 run also passed its frozen identity preflight. Its graph
aperture was:

```text
eligible division occurrences:
  2219

selected after caps:
  2219

accepted paths:
  142

holdout paths:
  68

holdout q values:
  21

mutable holdout positions:
  104 / 544 = 13/68
```

The exact holdout statistic and controls were:

```text
observed:
  3215/24696

exact-step permutation:
  mean = 1423661/14450688
  99th percentile = 1651/12348
  upper-tail p = 71/4097

stage/exposure/hub-stratified shuffle:
  mean = 98291/802816
  99th percentile = 209/1372
  upper-tail p = 63/241
```

U80 clears the path-count, denominator-count, and absolute mutable-position
gates. It still fails the preregistered mutable-fraction gate:

```text
failed aperture check:
  mutable fraction: 13/68 < 1/4

frozen U80 decision:
  insufficient_aperture
```

The larger checkpoint therefore does not resolve estimability for the present
strict-path and exact-stratum design. As at U40, this is neither retain nor
kill.

### Registered stop rule

The U80 follow-up preregistered the terminal branch:

```text
U80 remains insufficient:
  stop this line; the current strict-path/null design is not estimable from
  the available circle-as-one corpora.
```

That branch has now fired. There will be no further current-design transport
runs: no alternate seed, secondary path length, coarser stage bin, lower
mutability threshold, pooled U40/U80 statistic, or additional corpus sweep.
Any future transport question must be a materially new design with a new
preregistration, not a continuation or tuning of this experiment.

## Claim Boundary

Allowed claims are limited to:

```text
addition and subtraction are exact binary operations on Q/Z;
retained integers act through exact endomorphisms mu_n;
division by a retained nonzero integer defines an exact finite preimage relation;
the strict graph supplied these named, checkpoint-scoped division occurrences
and shared-input witnesses;
the external holdout accumulator did or did not exceed the two frozen controls.
```

Disallowed claims include:

```text
Q/Z inherits ordinary rational multiplication or division as binary operations;
the reduced q/residue is the full retained-divisor branch;
speculative rational nodes operate in aligned Modulus of One;
a provenance walk is a runtime path or orbit;
a return excess proves circle geometry;
failure in this aperture disproves every phase or modulus-one lens.
```

The construction is intentionally asymmetric: graph evidence chooses and
witnesses the paths; exact quotient algebra supplies external labels and
controls; neither layer is allowed to impersonate the other.

## Verification

The focused contracts are:

```text
python3 -m unittest -v tests/test_moo_phase_operator.py
python3 -m unittest -v tests/test_moo_phase_transport_probe.py
```

The operator suite checks representative invariance, action laws, kernels,
preimage cosets, source-arithmetic validation, and retained-lift branch
selection. The transport suite checks exact null comparisons, controlled
retain/kill outcomes, aperture failure, checkpoint isolation, same-stage
reinsertion invariance, arithmetic and operand rejection, hard caps, read-only
behavior, and report metadata/write protection.
