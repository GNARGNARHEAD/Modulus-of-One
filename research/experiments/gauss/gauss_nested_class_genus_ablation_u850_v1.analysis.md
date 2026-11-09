# Gauss Nested Class/Genus Ablation: Analysis

> Experiment ID: `gauss_nested_class_genus_ablation_u850_v1`
>
> Result: exact external calibration passes; no graph-conditioned effect is
> promoted; the bare modulus-one quotient is an exact maximal-erasure control.
>
> Runtime effect: none. This is a read-only research lens over frozen
> strict-stage corpora.

## Verdict

The experiment did what a strong control should do: it separated three
different claims that would otherwise be easy to blur together.

```text
Gauss form witness and proper class
    -> represented integer
    -> MoO construction neighborhood of that integer
    -> residue modulo m
    -> the sole residue modulo 1
```

The first object is rich. The final object is not. Between them, the tests show
exactly where the distinctions disappear:

1. Exact form coefficients, coordinates, and bilinear composition retain the
   full externally supplied Gauss structure.
2. Ordinary scalar arithmetic and congruences recover genus perfectly in the
   `Delta=-56` control.
3. The frozen MoO graph features add no promoted held-out information beyond
   that scalar baseline, either for genus or for the harder within-genus class
   contrast.
4. Opposite non-ambiguous forms have identical scalar value and graph-feature
   signatures, imposing an exact `1/2` ceiling on oriented recovery.
5. Reduction modulo one maps every endpoint to zero and leaves exactly zero
   class/genus information.

So the result is not "modulus one secretly contains the class group." It is a
cleaner and more useful statement:

```text
The class transition can survive as decorated provenance over the singleton
fibre, but it does not survive in the bare quotient itself.
```

This is the same boundary the preregistration was designed to expose. It is a
nested class/genus ablation, not a strict factorial experiment: proper class
belongs to genus, so the two variables cannot be independently crossed.

## Why Gauss Forms Are A Severe Test

Binary quadratic forms make information loss exact rather than metaphorical.
A form

```text
Q(x,y) = a*x^2 + b*x*y + c*y^2
```

has a proper class, a genus, representation coordinates, and a composition
law. Evaluating it retains only the integer `n=Q(x,y)`. Different rich objects
can therefore cast the same scalar shadow.

The three frozen families were chosen to separate distinct failure modes:

| modern discriminant | class group | genera | role |
|---:|---|---|---|
| `-20` | `C2` | `{A}`, `{B}` | class equals genus; easy calibration |
| `-23` | `C3` | `{A,P,M}` | one genus; `P` and `M=P^-1` are scalar-identical |
| `-56` | `C4` | `{A,C}`, `{P,M}` | genus and proper class separate |

For `Delta=-56`, the forms are

```text
A = [1,  0, 14]   principal
P = [3,  2,  5]   generator
C = [2,  0,  7]   order two
M = [3, -2,  5]   inverse of P
```

This supplies both a coarse target, `{A,C}` versus `{P,M}`, and a genuinely
nested target, `A` versus `C` inside the same genus. Gauss's theory predicts
that local congruence characters should see the former much more readily than
the latter. The experiment reproduces precisely that hierarchy.

## Frozen Design And Integrity

The analysis was frozen before the confirmatory corpus was created. Development
used values `1..200` from the existing U300 corpus; prediction used either
`201..400` or the full `201..800` confirmatory range. Each graph feature for
integer `n` was measured at the inclusive horizon `n+50`.

The U850 corpus contains:

```text
619,996 nodes
2,890,001 directed edge occurrences
```

All of the following integrity checks passed:

- the preregistration, source files, Python version, argument vector, corpus
  generator, database, summary, and manifests matched their frozen hashes;
- the strict positive-spine operand-alignment audit passed;
- development and holdout database hashes were unchanged after analysis;
- all 200 overlapping prefix feature vectors agreed exactly between the U300
  and U850 corpora;
- no form ID, class, genus, coefficient, coordinate, orbit ID, or form-selected
  edge entered the graph models.

The full machine-readable result is
`gauss_nested_class_genus_ablation_u850_v1.json`. Its SHA-256 is
`ff6fc920cfeb48101938018bff7f948c4e68377c96eaa8f4c1af4f32d3f966b2`.

## Primary Held-Out Results

The score is macro balanced accuracy. "Graph lift" means

```text
balanced_accuracy(scalar + graph) - balanced_accuracy(scalar only).
```

The scalar model deliberately contains a very strong arithmetic baseline:
exact prime exponents through 800, divisor statistics, `gcd(n,|Delta|)`, and
one-hot residues for every divisor of `|Delta|`. The graph block contains only
label-free node evidence: confirmation lag, degrees, operation histograms, and
distinct operands/results.

Because the complete prime-exponent vector identifies each tested integer,
"incremental graph value" here is relative to the frozen nearest-centroid
geometry. Even a positive lift would not mean that the graph contained
information unavailable from integer identity to an unrestricted method.

### T1: `Delta=-56` genus

| checkpoint | scalar | graph only | scalar + graph | graph lift | matched-null p |
|---|---:|---:|---:|---:|---:|
| `201..400` | `1.0000` | `0.5000` | `1.0000` | `0.0000` | `0.8967` |
| `201..800` | `1.0000` | `0.5000` | `1.0000` | `0.0000` | `0.4040` |

The scalar baseline already recovers genus perfectly. The graph cannot improve
on it and supplies exactly zero incremental lift. This is a positive
calibration for classical genus theory and a null graph-increment result.
Because the scalar score is already at the ceiling, this task cannot determine
whether graph features redundantly reflect genus; it only establishes that they
add no score beyond the scalar model.

### T2: `Delta=-56`, `A` versus `C` within one genus

| checkpoint | scalar | graph only | scalar + graph | graph lift | matched-null p |
|---|---:|---:|---:|---:|---:|
| `201..400` | `0.2250` | `0.5000` | `0.3750` | `0.1500` | `0.6987` |
| `201..800` | `0.4500` | `0.5000` | `0.4643` | `0.0143` | `0.7809` |

The intermediate `+0.15` is the most instructive number in the report. In
isolation it looks promising. Under the preregistered matched permutation,
however, the null median was itself `+0.15` and the null mean was about
`+0.166`. At the larger mandatory checkpoint, the lift shrank to `+0.0143`.
The final null median was also `+0.0143`.

In other words, the apparent early gain behaved exactly like an ordinary
small-sample fluctuation. The control prevented a transient score from being
renamed a structural discovery.

The final combined model predicted none of the 15 `A` cases correctly and 13
of the 14 `C` cases correctly. Its small balanced-accuracy improvement is
therefore not credible recovery of both classes; it is close to collapsing to
`C`. The development set has only 14 exclusive `A`/`C` samples and the final
holdout 29. The `201..400` checkpoint has nine cases and is contained inside
`201..800`, so the two checkpoints are a sequential stability check, not two
independent replications.

The final raw p-values were `0.4040` and `0.7809`; both Holm-adjusted values
were `0.8079`. Neither task met the frozen minimum lift of `0.05`, the adjusted
`p<=0.01` threshold, or the required positive replication pattern. No
graph-conditioned effect was promoted.

The matched null had ample mobility rather than being frozen by its strata.
At the final checkpoint, every holdout row was in a nonsingleton stratum. The
expected cross-label, graph-changing transfer fractions were about `0.500` for
genus and `0.468` for the within-genus contrast.

The matched permutation is a frozen, coarse exposure-matched sensitivity
procedure. Since every graph feature is a deterministic function of `n`, its
strata do not establish literal conditional exchangeability. Its p-values
govern this registered analysis; they are not universal conditional-
independence tests.

## Secondary Controls

### `Delta=-20`: the easy case

Here class and genus coincide. On `201..800`, the scalar model scored `1.0`,
the topology-only model `0.5`, and the combined model `1.0`. The graph lift was
zero. This confirms that the pipeline can recover the classical local split
when it is present, without attributing the recovery to graph topology.

### `Delta=-23`: one genus, class modulo inversion

The secondary `A` versus `{P,M}` score on `201..800` was:

```text
scalar              0.4967
graph only           0.5000
scalar + graph       0.5000
graph lift          +0.0033
```

This is descriptive and effectively at chance. It agrees with the exact local
control: all three forms have the same residue distribution modulo 23.

### Exact inverse-pair ceiling

The inverse forms are not merely difficult to distinguish. They are exactly
indistinguishable from the frozen scalar-node observables:

| family | inverse pair | common scalar values through 800 | duplicated audit rows | exact ceiling |
|---|---|---:|---:|---:|
| `-23` | `P` versus `M` | `267` | `534` | `1/2` |
| `-56` | `P` versus `M` | `205` | `410` | `1/2` |

The same integer selects the same graph node and therefore the same graph
features. Any deterministic scalar-plus-node method claiming better than
one-half oriented recovery on these paired rows would be carrying leaked form
information.

## The Quotient Ladder

The preregistered "ladder" asks not just whether information disappears at
modulus one, but how it changes across a controlled modulus panel. It is a
divisibility poset rather than one literal nested chain: for example, moduli 4
and 7 are incomparable. The `m=809` endpoint is injective only on the frozen
range `1..800`; it is not a general refinement of the discriminant divisors.

### `Delta=-56`

| modulus | genus MI, bits | genus BA | class MI given genus, bits | `A`/`C` BA |
|---:|---:|---:|---:|---:|
| `1` | `0.000000` | `0.5000` | `0.000000` | `0.5000` |
| `2` | `0.000000` | `0.5000` | `0.000000` | `0.5000` |
| `4` | `0.000000` | `0.5000` | `0.009554` | `0.5524` |
| `7` | `0.999878` | `1.0000` | `0.000597` | `0.4548` |
| `8` | `0.999878` | `1.0000` | `0.009554` | `0.5524` |
| `14` | `0.999878` | `1.0000` | `0.000597` | `0.4548` |
| `28` | `0.999878` | `1.0000` | `0.029625` | `0.4143` |
| `56` | `0.999878` | `1.0000` | `0.029625` | `0.4143` |

Modulo 56, the coprime genus supports are exactly disjoint:

```text
principal genus: {1, 9, 15, 23, 25, 39}
other genus:     {3, 5, 13, 19, 27, 45}
```

Within either genus, the paired forms have the same local distributions modulo
7, 8, and 56. Thus congruence sees genus almost perfectly and proper class
poorly. This is the classical class/genus hierarchy made empirical on the
frozen sample.

For `Delta=-20`, moduli 4, 5, 10, and 20 recover the class/genus split
perfectly, while moduli 1 and 2 are at chance. For `Delta=-23`, modulus 23
provides only about `0.0303` conditional bits and `0.5104` balanced accuracy
for the one-genus class contrast.

The injective endpoint `m=809` retains the integer identity on `1..800`, so its
mutual information is high. It has no predictive score: no holdout residue was
seen in training. It also cannot restore inverse orientation, because the two
inverse forms can still produce the same integer. Retaining the endpoint is
not the same as retaining its antecedent.

### The exact modulus-one endpoint

At `m=1`:

```text
carrier cardinality                         1
sole residue                                0
deduplicated bare quotient nodes            1
deduplicated unlabelled edge relations      1
genus mutual information                    0
conditional class mutual information        0
constant-bucket balanced accuracy          1/2
```

No form orientation, proper class, genus, character phase, or composition
provenance is retained by the quotient. Any such information can exist only as
an annotation on the preimage fibre. Modulus one is therefore not a small
window onto this structure; it is the exact endpoint at which the scalar
quotient has forgotten all of it.

## Composition And The Saturation Trap

The external mathematics passed every exact check:

- independently derived reduced-form class tables matched `C2`, `C3`, and
  `C4`;
- every symbolic bilinear identity held;
- every bounded composition output landed in its required target fibre;
- `4,873`, `9,277`, and `6,381` normalized composition events were verified
  for discriminants `-20`, `-23`, and `-56` respectively.

Their scalar multiplication shadows were also completely present in the MoO
graph:

| discriminant | distinct scalar products | directed edge IDs | usable by U850 |
|---:|---:|---:|---:|
| `-20` | `1,398` | `2,774` | all |
| `-23` | `885` | `1,754` | all |
| `-56` | `1,566` | `3,107` | all |

That completeness is a saturation control, not class evidence. A strict corpus
that records all in-range products of confirmed positive operands should
contain these scalar multiplications regardless of which external quadratic
form led us to inspect them. The edge `u*v -> uv` does not record the form
classes of representations of `u`, `v`, or `uv`, nor the bilinear coordinate
map that composes them.

No graph-native composition classifier was implemented, and the report says
so explicitly. The 1,000-run operation-histogram shuffle is only a destructive
descriptive ablation; it cannot turn saturated edge coverage into composition
evidence.

## What The Control Bought Us

The "factorial control" is best understood here as a controlled ladder of
ablations. Its practical value was high even though the result was null:

1. **It localized the signal.** Genus information lives in ordinary
   discriminant-sensitive arithmetic, not in the singleton quotient.
2. **It exposed leakage.** Coefficients trivially identify the externally
   assigned class, while inverse-pair duplication proves that scalar-node
   orientation recovery is impossible.
3. **It rejected a seductive fluctuation.** The early `+0.15` graph lift was
   ordinary under the matched null and nearly vanished on the larger holdout.
4. **It separated availability from selectivity.** Every composition shadow
   was present, but universal presence cannot identify which edges are Gauss
   composition witnesses.
5. **It made modulus one falsifiable.** The bare quotient must be identical to
   a constant bucket. Any nonzero information there is an error, not a
   discovery.

The control therefore strengthens MoO by narrowing the meaningful claim. MoO's
distinctive object is not the residue `0` and not the scalar value alone. It is
the witnessed emergence retained before projection. But that provenance has
to be natively recorded or independently predicted; it cannot be reconstructed
by naming a saturated scalar edge after an external theory.

## Claim Boundary

Earned, within the frozen primitive single-target samples, feature family,
classifier, cutoffs, and bound through 800:

```text
The bounded form fibres and composition calibrations are exact.
Classical scalar congruence information recovers the tested genus split.
The frozen graph block adds no promoted held-out class/genus information.
Inverse orientation is exactly non-identifiable from a scalar node.
The bare Z/1Z endpoint is exact maximal erasure.
Decorated preimage provenance may retain what the quotient forgets.
```

Not earned:

```text
The MoO runtime contains quadratic forms or class groups as native objects.
Modulus one itself contains hidden class or genus structure.
A scalar multiplication edge is a Gauss composition witness.
The null graph result proves that no richer graph-native encoding can exist.
Any finite class/genus result implies a theta, zeta, or zero-set theorem.
```

## Best Next Experiment

The next useful experiment is not another classifier over the same integer
node summaries. It is a witness-level composition test. It would first define
a graph-native relation object without form labels, then ask whether its
neighborhood predicts a held-out composition channel better than scalar
product and exposure controls. Until MoO records a native distinction that can
separate two representations of the same integer, inverse-class orientation
should remain a deliberately impossible target.

The present experiment has done the prior job: it established the honest null
floor and showed which distinctions a future witness-level representation
would actually have to preserve.
