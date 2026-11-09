# Gauss, Congruence, and the Modulus-One Boundary

> Status: active external framing lens plus a strict-corpus observation.
>
> Claim labels: `evidence_layer: external_probe_over_strict_corpus`,
> `claim_status: observation`.
>
> This note does not add congruence, modular arithmetic, Gaussian integers,
> roots of unity, or quadratic forms to the Modulus of One runtime. Gauss supplies the
> question and the boundary tests. The Modulus of One evidence remains the source graph's
> nodes, edge occurrences, stages, and confirmation states.

## Verdict

Gauss does not reveal hidden arithmetic *inside* modulus one. He reveals why
modulus one is useful precisely because it has no integer resolving power.

For integers,

```text
a congruent to b (mod 1) for every a and b.
```

The quotient has one residue class. Its bare graph is one vertex with total
loops. That collapse is forced, not discovered.

This makes it a severe negative control for Modulus of One:

```text
construct first, then project modulo 1
-> integer values become indistinguishable
-> retained edge ids, operations, stages, witnesses, and confirmation histories remain
-> everything still visible is information beyond integer residue value
```

The U300 strict-corpus report passes that test. It collapses 24,394
integer-valued nodes to one occupied residue while retaining all 271,768
integer-result edge occurrences, including the seed. The quotient topology is
trivial; the decorated fiber is not.

The strongest conclusion is therefore restrained:

> Modulus one is a maximally coarse integer observer. It does not explain Modulus of One,
> but it cleanly audits whether Modulus of One really preserves witnessed emergence when
> value distinctions are erased.

## Source Method

The primary reference is Gauss's 1801 *Disquisitiones Arithmeticae*. Article
numbers below were checked against the [ETH e-rara first-edition
scan](https://www.e-rara.ch/zut/content/structure/1254642) and the [Library of
Congress copy](https://www.loc.gov/item/36021572/). The [Clarke English
translation reissued by Springer](https://link.springer.com/book/10.1007/978-1-4939-7560-0)
is the translation reference. Open article-indexed transcriptions of [Section
I](https://en.wikisource.org/wiki/Translation:Disquisitiones_Arithmeticae/First_Section),
[Section II](https://www.spectralquantity.com/Disquisitiones-Arithmeticae/sectio-2),
and [Section IV](https://www.spectralquantity.com/Disquisitiones-Arithmeticae/sectio-4)
were used for navigation and then checked against the scans.

Gauss rarely says "modulus one" explicitly. This note therefore distinguishes:

```text
explicit Gauss statement
direct specialization of Gauss's definition
modern convention
Modulus of One interpretation
```

That distinction matters most around primitive roots, the zero ring, Jacobi
symbols, and Gaussian integer quotients, where modern conventions should not be
retroactively attributed to Gauss.

## First Guardrail: Five Different Uses of One

The phrase "modulus of one" is overloaded. These objects must remain separate.

| Name | Domain and relation | Size at one | Role here |
|---|---|---:|---|
| Modulus of One certainty | `Ref(1)` and its witnessed recurrence | one primitive certainty | core epistemic framing |
| integer congruence modulo 1 | `a ~ b` when `1` divides `a-b` | one class | Gauss-derived negative control |
| rational phase modulo 1 | `x ~ y` when `x-y` is an integer | infinitely many classes | additive external lens, not the integer quotient |
| complex absolute modulus 1 | `abs(z)=1`, the unit circle | infinitely many points | phase/geometry lens |
| residue 1 modulo `q` | the class `[1]_q` | depends on `q` | ordinary residue, not modulus equal to 1 |

There is a second distinction in Gauss's later complex arithmetic:

| Phrase | Meaning |
|---|---|
| Gaussian integers of norm 1 | the four units `+1`, `-1`, `+i`, `-i` |
| congruence modulo a Gaussian unit | one residue class |

Four norm-one elements are not four residues modulo one. The fourfold structure
belongs to the ambient arithmetic; quotienting by any unit erases it.

## What Follows from the *Disquisitiones*

### Articles 1-4: the one-class boundary

Article 1 defines two integers as congruent when their difference is divisible
by the modulus. Gauss explicitly limits the terminology to integers rather
than fractions. Nothing in that definition excludes modulus 1. Since 1 divides
every integer difference, every pair of integers is congruent modulo 1.

Articles 2-4 then specialize without strain:

- every integer is a residue of every other integer modulo 1;
- a block of one consecutive integer is a complete residue system;
- the least nonnegative residue system is `{0}`;
- there is no second residue class with which to contrast it.

In modern notation, `Z/1Z` is a singleton. Calling it the zero ring assumes the
convention that a ring may have `0=1`; the [Stacks Project states that
convention explicitly](https://stacks.math.columbia.edu/tag/00AQ). This note
does not need that convention. The one-class conclusion follows directly from
Gauss's divisibility definition.

### Articles 5-11: valid arithmetic with zero discrimination

Gauss proves that congruences are compatible with addition, subtraction,
multiplication, powers, and integer-polynomial substitution. At modulus 1,
these laws remain valid but say only that the result lies in the sole class.

This has a useful negative formulation:

```text
F(x) congruent to 0 (mod 1)
```

holds for every integer-polynomial value `F(x)`. A modulus-one congruence can
never obstruct an integer equation. If a probe reports a nontrivial solvability
distinction at modulus 1, the distinction came from retained source data or
from a domain mistake, not from the residue quotient.

### Articles 22-36: cancellation and CRT become boundary identities

Gauss's cancellation and linear-congruence results count roots as residue
classes, not as raw integer witnesses. At modulus 1, every integer witness lies
in the same root class. "One root" therefore does not mean "one construction."

Likewise, a modulus-one coordinate is neutral in a simultaneous-congruence
system:

```text
lcm(1, m) = m
```

Adding `x congruent to 0 (mod 1)` contributes no information. The U300 report
checks this for every requested comparison modulus: adding the mod-1 coordinate
does not change the observed class count for moduli 2, 3, 4, 5, 6, 8, or 12.

### Articles 38-39: Gauss repairs the unit boundary

This is the most revealing explicit boundary passage.

Article 38 initially counts positive integers relatively prime to `A` and
strictly smaller than `A`. At `A=1`, that gives an empty count. In Article 39,
Gauss changes the endpoint to numbers *not greater than* `A`, observes that the
change affects only `A=1`, and thereby sets `phi(1)=1`. He then states the
divisor-sum identity

```text
sum(phi(d) for d dividing A) = A.
```

The important lesson is not that every degenerate case should be renamed one.
It is that a boundary convention must be justified by the structural law it
preserves. Here the altered endpoint makes the global divisor decomposition
uniform, including its unit case.

For Modulus of One this suggests an audit question:

> When a generic count becomes empty at `1`, is zero the intended structure,
> or is there an identity-like witness whose count must be one for a stated
> composition law to remain valid?

That question is diagnostic, not permission to normalize results ad hoc.

### Articles 45-92: where substitution of 1 stops

Gauss's order and primitive-root theories do not arise by blindly putting
`p=1` into prime-modulus formulas.

- Article 45 requires a positive exponent smaller than a prime modulus. No
  positive exponent is smaller than 1.
- The primitive-root development uses order `p-1` and indices modulo `p-1`.
  Substitution of 1 would produce an order-zero/index-mod-zero expression,
  outside the theory Gauss states.
- The later composite-modulus articles still do not literally include 1,
  because 1 is neither prime nor composite.

Under some modern conventions the unit group of the singleton ring is a
trivial cyclic group. Calling its element a "primitive root modulo 1" is still
a modern convention, not a result to attribute to Gauss.

### Articles 94 onward: quadratic residue boundary, not reciprocity

Gauss begins the quadratic-residue definition with an arbitrary modulus. By
direct specialization, the sole class modulo 1 has a square representative:
`0*0` lies in it. Thus every integer belongs to a square-represented class and
there is no quadratic nonresidue obstruction modulo 1.

The richer results that follow impose stronger hypotheses:

- the equal residue/nonresidue split uses odd prime moduli;
- Euler's criterion uses an odd prime modulus;
- quadratic reciprocity compares prime moduli.

None is a theorem "at prime 1," because 1 is not prime. Likewise, a Legendre
symbol with denominator 1 is not defined by the odd-prime definition. The
modern Jacobi convention with denominator 1 is an empty-product convention;
see [DLMF 27.9](https://dlmf.nist.gov/27.9). It is not Gauss's reciprocity law
evaluated at 1.

## The Rational-Domain Trap

Modulus of One's graph contains reduced rationals, but Gauss's Article 1 congruence does
not apply to fractions.

There is a legitimate rational relation often also called "modulo 1":

```text
x ~ y when x-y is an integer.
```

This is the additive quotient `Q/Z`. It is not a one-class quotient:

```text
1/2 ~ 3/2
1/2 is not equivalent to 0.
```

It also does not support general multiplication of equivalence classes. For
example,

```text
1/2 ~ 3/2,
but multiplying both by 1/2 gives 1/4 and 3/4,
whose difference is 1/2 rather than an integer.
```

Therefore the probe makes three policies explicit:

```text
integer_congruence_mod_1:
  integer nodes only; one class; integer +,-,* compatibility

fractional_phase_mod_1:
  rational nodes; many additive classes; no general multiplication quotient

total_value_collapse:
  one bucket for all graph values; generic graph abstraction, not Gauss congruence
```

Of the corpus's 360,001 edges through U300, 88,233 division results are
non-integer rationals. They remain in the source graph and are reported as
excluded from the integer projection. Silently collapsing them to the same
class would turn an integer theorem into a different graph-forgetting rule.

The separate [CIRCLE_AS_ONE_QUOTIENT_NOTE.md](../geometry/CIRCLE_AS_ONE_QUOTIENT_NOTE.md) and
`moo/circle_as_one_probe.py` study the legitimate exact `Q/Z` phase quotient.
That work is complementary: `Z/1Z` is its one-bucket negative control, not its
circle model.

## A Wider Gauss Lens

Congruence is the direct lens. Other parts of Gauss's work add useful scrutiny
only when their domains and limits are respected.

### Binary quadratic forms: value is not representation

In *Disquisitiones* Articles 153-259, Gauss distinguishes:

```text
form
represented value
integer representation witness (x,y)
transformation/equivalence
reduced representative
composition witness
principal class
```

This is close to Modulus of One's distinction between a value node and its construction
edges. Equal represented values do not erase their representations. Reduction
selects useful representatives while preserving class relations; composition
contains bilinear witness data not recoverable from the product value alone.

The analogy has a limit. Modulus of One's current edge graph is not Gauss's form class
group, and its value-node canonicalization is not reduction of quadratic forms.
The legitimate use is a scrutiny question: when normalizing an object, which
transformation and representation witnesses must remain visible?

The active follow-through is
[QUADRATIC_FORMS_CLASS_CHANNEL_LENS_NOTE.md](QUADRATIC_FORMS_CLASS_CHANNEL_LENS_NOTE.md) with the read-only
`moo/quadratic_form_probe.py`. It makes this distinction executable for the
`D=-4` and `D=-20` controls: complete representation fibres and exact bilinear
composition remain external annotations, while named scalar nodes and edges
are audited separately. In particular, it exhibits how the scalar product
`2*3=6` loses a `nonprincipal*nonprincipal->principal` form-class transition.

### Gaussian integers: a strong deferred control

In *Theoria residuorum biquadraticorum, commentatio secunda*, Articles 30-31
extend arithmetic to `a+bi`, identify the four units, conjugation, and norm
`a*a+b*b`, and establish norm multiplicativity. Articles 38-42 give the lattice
picture of multiples of a Gaussian modulus and count exactly `N(m)` residue
classes modulo `m`. See the [ETH primary
scan](https://doi.org/10.3931/e-rara-61067) and the [article-indexed
translation](https://en.wikisource.org/wiki/Translation:Theoria_residuorum_biquadraticum).

A Gaussian modulus of norm 1 is a unit, so its congruence quotient has exactly
one class. This produces a sharp future control:

```text
ambient norm-one locus: four units and their associate symmetries
quotient by any norm-one unit: one class
```

The current rational runtime cannot construct `i` from `1` using rational
`+,-,*,/`. Implementing this now would silently add a new number domain.
Accordingly Gaussian integers remain deferred as runtime semantics. An exact
external pair/operator calibration is now available: `J(x,y)=(-y,x)`,
`J^2=-I`, and Gaussian pair multiplication with its polynomial norm identity.
That analysis layer does not make `i` a runtime operand.

### Cyclotomy: many antecedents of one, but not at n=1

The final section of *Disquisitiones* studies roots of `x^n=1`, their periods,
and division of the circle. Distinct roots sharing the `n`th-power target 1 are
a useful analogy for "many structured antecedents, one projected result."

At `n=1`, however, there is only the identity root and no nontrivial period
structure. Cyclotomy does not supply hidden richness to modulus one. It would
also require algebraic extensions absent from the current runtime. For a modern
historical audit of the last section, see Anderson, Chahal, and Top, ["The last
chapter of the Disquisitiones of
Gauss"](https://arxiv.org/abs/2110.01355).

### Screened out for now

- Gauss's intrinsic curvature suggests asking which observations survive a
  change of representation, but an isometric bending is not a many-to-one
  quotient. It is only a methodological analogy.
- Gauss's least-squares work requires an independently specified error model.
  Congruence modulo one is exact equivalence, not noisy measurement.

These themes add prestige more readily than precision here, so they should not
drive a current Modulus of One probe.

## The Graph Experiment

### Tool and artifact

The read-only tool is `moo/congruence_quotient_probe.py`. The saved primary
report is:

```text
research/experiments/gauss/gauss_congruence_quotient_u300_v1.json
```

It was generated with:

```text
python3 -m moo.congruence_quotient_probe \
  --db out/experiments/pascal_edge_probe_u300.sqlite \
  --moduli 1,2,3,4,5,6,8,12 \
  --checkpoints 1,2,3,5,10,20,40,80,160,300 \
  --sample-limit 4 --include-checksums \
  --write research/experiments/gauss/gauss_congruence_quotient_u300_v1.json --pretty
```

The report contains the corpus and tool SHA-256 checksums. It refuses to modify
the corpus and refuses to overwrite an existing report.

### Corpus certificate

The source corpus is the alignment-pass U300 positive-spine strict graph:

| Field | Value |
|---|---:|
| stages | 300 |
| all source nodes | 78,889 |
| all source edges | 360,001 |
| `+` / `-` / `*` / `/` occurrences | 90,000 each |
| speculative operand edges | 0 |
| non-core operand edges | 0 |

The integer projection has a separate completeness check. At cutoff `U`, the
broad all-integer domain expects `U^2` occurrences for each of `+`, `-`, and
`*`, and `sum(floor(U/k), k=1..U)` exact-integer division occurrences. The
confirmed-positive domain expects `U(U-1)/2` each for `+` and `-`, and the same
divisor summatory count for `*` and `/`. Every U300 check passed.

### Two source domains

`all_integer_shadow` is primary because it honors Gauss's integer domain. It
keeps zero, negatives, positive results not yet confirmed by U300, and every
integer-result witness.

`confirmed_positive_spine` is the stricter Modulus of One control. It keeps nodes 1 through
300 and edge occurrences whose results lie in that confirmed set. It loses
zero, negatives, and future-positive speculative results, so it must not be
mistaken for all of `Z`.

| U300 domain | nodes | non-seed edges | `+` | `-` | `*` | exact `/` |
|---|---:|---:|---:|---:|---:|---:|
| all integer shadow | 24,394 | 271,767 | 90,000 | 90,000 | 90,000 | 1,767 |
| confirmed positive spine | 300 | 93,234 | 44,850 | 44,850 | 1,767 | 1,767 |

Each domain also includes the single seed occurrence in its total edge count.

### Decorated quotient, not a deduplicated graph

For modulus `m`, the probe maps integer labels to least nonnegative residues:

```text
n -> n mod m.
```

It does not merge source edge records. A projected edge retains:

```text
edge_id
stage
operation
ordered left/right/result node ids and values
left/right/result residues
result status at the edge event
result status at the selected checkpoint
```

For exact integer division `a/b=c`, the probe checks `b*c congruent to a`; it
does not treat `/` as generally defined on residue classes. This distinction is
essential when the divisor is not invertible modulo `m`.

## Results

### Result 1: maximal node collapse, exact edge conservation

At modulus 1 in the all-integer domain:

| Measure | U300 result |
|---|---:|
| source integer nodes | 24,394 |
| occupied residue nodes | 1 |
| source nodes collapsed beyond representative | 24,393 |
| integer-result edge occurrences, including seed | 271,768 |
| edge occurrences retained | 271,768 |
| non-seed operation-decorated signatures | 4 |
| unlabeled non-seed quotient topologies | 1 |
| algebra-check failures | 0 |

This is the central control. If operation labels and occurrence identity are
removed, every non-seed edge is the same total loop. The quotient itself has no
topological specificity. The 271,768 surviving records belong to the source
fiber, not to arithmetic internal to the singleton quotient.

### Result 2: the first operator fan survives only as decoration

The source fan is:

| edge | source | result status at U1 | mod-1 result |
|---:|---|---|---:|
| 2 | `1+1 -> 2` | speculative positive | 0 |
| 3 | `1-1 -> 0` | relational nonpositive | 0 |
| 4 | `1*1 -> 1` | certainty | 0 |
| 5 | `1/1 -> 1` | certainty | 0 |

The residue projection cannot distinguish expansion, cancellation, or
preservation. The retained graph can, because it keeps the four operation
labels, four edge ids, three source values, and different epistemic outcomes.

This does **not** mean the quotient proves those distinctions. It means
construction followed by forgetting retains a fiber that computation entirely
inside the forgotten one-element world could never reconstruct.

### Result 3: one residue fiber contains incompatible epistemic statuses

The U300 all-integer fiber contains:

| status at U300 | nodes |
|---|---:|
| certainty | 1 |
| confirmed positive spine | 299 |
| relational nonpositive | 300 |
| speculative positive after U300 | 23,794 |

All share residue 0 modulo 1. Therefore integer residue equality cannot be used
as an epistemic equivalence. In particular, `0 congruent to 1 (mod 1)` does not
say `0` and `Ref(1)` have the same status, origin, or role in the source graph.

### Result 4: the collapse exposes an operator/time asymmetry

The all-integer source occurrences have these result states at their event:

| op | certainty | confirmed then | speculative positive then | nonpositive relation |
|---|---:|---:|---:|---:|
| `+` | 0 | 0 | 90,000 | 0 |
| `-` | 299 | 44,551 | 0 | 45,150 |
| `*` | 1 | 598 | 89,401 | 0 |
| exact `/` | 300 | 1,467 | 0 | 0 |

In the confirmed-positive control, addition contributes 44,850 results that
were speculative at their construction event and confirmed later. Subtraction
and exact division point only to values already confirmed at the event.
Multiplication mixes 599 already-confirmed/certainty results with 1,168 later
confirmations.

This asymmetry comes from the source generation and confirmation rule, not from
modulus one. Modulus one is useful here because it removes value separation
without removing the timeline, making that fact difficult to confuse with a
residue pattern.

### Result 5: modulus one is the root partition, not a deep branch

For every tested pair `m1 | m2`, the observed residue partition modulo `m2`
refined the partition modulo `m1`; all 16 refinement checks passed. Modulus 1
is the coarsest member because it divides every tested modulus.

At U300, the number of occupied residues was exactly the modulus for 1, 2, 3,
4, 5, 6, 8, and 12. The non-seed operation-decorated signature count rose as:

```text
m=1:   4
m=2:  16
m=3:  36
m=4:  64
m=5: 100
m=6: 144
m=8: 256
m=12: 576
```

The `4*m^2` pattern is forced here by four integer arithmetic relations whose
result residue is determined by the ordered input residues. It is a classical
control, not evidence of a new Modulus of One law.

### Result 6: the control remains stable across stage growth

| checkpoint | all integer nodes | all integer edges incl. seed | confirmed nodes | confirmed edges incl. seed |
|---:|---:|---:|---:|---:|
| 1 | 3 | 5 | 1 | 3 |
| 10 | 56 | 328 | 10 | 145 |
| 40 | 567 | 4,959 | 40 | 1,877 |
| 80 | 2,034 | 19,569 | 80 | 7,057 |
| 160 | 7,363 | 77,643 | 160 | 27,125 |
| 300 | 24,394 | 271,768 | 300 | 93,235 |

At every checkpoint the mod-1 quotient has one occupied residue. Growth occurs
entirely in its source fiber. This is the expected behavior of a stable
maximally coarse observer.

## What Is Forced, Observed, and Inferred

| Statement | Status |
|---|---|
| every integer is congruent modulo 1 | direct specialization of Gauss Art. 1 |
| the least residue system is `{0}` | direct specialization of Arts. 3-4 |
| `phi(1)=1` under the endpoint repair | explicit in Gauss Art. 39 |
| modulus 1 adds no CRT information | direct arithmetic consequence |
| the sole class has a square representative | direct specialization of Arts. 94-95 |
| 24,394 U300 integer nodes collapse to one class | corpus-conditioned observation |
| 271,768 integer-result occurrences survive as records | corpus-conditioned observation |
| addition is forward-looking in this corpus | observation about this strict confirmation rule |
| Modulus of One has information beyond value | supported insofar as the named retained edge fields are considered part of Modulus of One's object |
| modulus one validates Modulus of One | rejected |
| the singleton quotient contains hidden rich topology | rejected |
| all rational Modulus of One nodes are Gaussian-congruent mod 1 | category/domain error |

## Lens Card

```text
name:
  Gauss congruence / modulus-one negative control

evidence_layer:
  external_probe_over_strict_corpus

claim_status:
  observation

provocative_hypothesis:
  If witnessed emergence is genuinely primary, a projection that erases every
  integer value distinction should still preserve auditable construction,
  operation, stage, and confirmation information.

false_positive_guarded_against:
  Mistaking forced universal looping, maximal collision, or a one-node quotient
  for discovered Modulus of One structure; conflating Z/1Z, Q/Z, U(1), and Ref(1).

graph_native_observable:
  integer source-node fibers; exact edge occurrences; operation signatures;
  first/confirmed stages; result status at event and checkpoint; first fan.

query_or_report:
  python3 -m moo.congruence_quotient_probe --db <corpus.sqlite> --moduli 1,2,3,4,5,6,8,12 --pretty

metric:
  occupied residues; node collision count; conserved edge occurrences;
  operation-decorated signatures; status-by-operation counts; completeness;
  refinement and CRT-neutrality checks.

null_model_or_control:
  the bare one-bucket quotient; m>1 residue ladders; confirmed-positive induced
  domain; stage checkpoints; future injective modulus and balanced coloring.

promotion_criteria:
  This lens remains an external observation. A stronger Modulus of One claim would require
  a preregistered retained-fiber statistic that predicts held-out graph
  structure beyond stage, operation, size, and random-color controls.

kill_criteria:
  Edge ids or status histories are silently deduplicated; rational results are
  folded into Gaussian integer congruence; the observed signal reduces to the
  forced one-node/one-loop topology; completeness fails without being reported.

allowed_claim_language:
  "Modulo one erases all integer value distinctions in the named source domain,
  while the decorated projection retains these exact source witnesses."

disallowed_claim_language:
  "Gauss proves Modulus of One," "modulus one proves 0 and 1 are the same in Modulus of One," or
  "rich structure lives inside Z/1Z."
```

## Mature Reading for Modulus of One

The Gauss perspective changes the question from:

```text
What mysterious structure is modulus one hiding?
```

to:

```text
What information does the coarsest legitimate integer projection destroy?
What information did Modulus of One preserve before that destruction?
Which boundary conventions at one are forced by a global identity?
```

Three consequences follow.

First, `Ref(1)` and the residue class modulo 1 must not be identified. `Ref(1)`
is an epistemic/source-graph anchor. The mod-1 class is an observer output that
also contains 0, 2, every negative integer, and every future positive integer.

Second, order of operations matters:

```text
build the witnessed graph -> quotient values
```

retains a decorated fiber, whereas

```text
start inside the singleton quotient -> operate
```

can produce only the singleton and cannot recover the fan. The richness is in
the lift and its provenance, not in the quotient.

Third, Gauss's `phi(1)=1` repair offers a disciplined model for unit boundaries:
state the identity to be preserved, state the convention, and verify that only
the intended boundary changes. It does not license numerological assignments
or a generic preference for one.

## Next Tests

The current result is mature enough to define the next controls without
pretending they are already done:

1. Reproduce the registered metrics on the existing broad U1000 corpus as a
   holdout, without changing thresholds after inspection.
2. Add an injective-modulus control larger than the observed integer range, so
   the no-collapse endpoint is measured beside the one-class endpoint.
3. Compare congruence classes for `m>=2` against balanced random colorings with
   the same fiber sizes; this separates arithmetic compatibility from generic
   compression.
4. Shuffle operation labels while preserving stage and endpoints to test which
   temporal asymmetries require the true operator ecology.
5. Add collision-pair and bucket-multiplicity distributions without emitting a
   value-only ranking.
6. Keep Gaussian integers deferred as runtime objects. Use the exact external
   pair/operator and norm-one calibration in the quadratic-form probe until the
   project explicitly introduces an algebraic-extension layer capable of
   representing `i`.

The current stopping point is intentional: modulus one has earned a role as a
boundary observer and negative control. It has not earned a role as an internal
arithmetic engine, an explanation of Modulus of One, or a source of new number theory.
