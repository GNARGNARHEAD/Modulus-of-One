# Euler Reciprocal Mass And Circle Lens

> Status: strict research-branch governance.
>
> Euler is useful to Modulus of One because `pi` appears in his work through exact
> arithmetic shadows: reciprocal-square mass, finite products, zeros, and prime
> factorization. This note does not claim that Modulus of One constructs `pi` or defines
> the Euclidean circle. Any later `pi` or circle-like Order-4 language must
> follow [order4-projection.md](../../docs/protocols/order4-projection.md).

## Claim Boundary

Allowed now:

```text
Modulus of One has unit-quadratic-shell probes over strict graph corpora.
Modulus of One can inspect rational quadratic-shell candidates through graph evidence.
Modulus of One can later inspect Euler-style reciprocal-square and product structures.
Modulus of One may later propose pi-shadow or circle-like Order-4 shadows only
after exact source families, projection rules, controls, and held-out tests.
```

Not allowed yet:

```text
Modulus of One defines the circle.
Modulus of One constructs pi.
Modulus of One has sine, angle, circumference, or area as internal objects.
Order-4 anchors can be used as operands or treated as completed Euclidean
objects.
```

The first internal object is not a circle. It is a rational quadratic shell.

## Quadratic Shell First

Define a Modulus of One point as an ordered pair of constructed rational nodes:

```text
(x, y)
```

Define the exact rational form:

```text
Q(x, y) = x*x + y*y
```

For a constructed rational `r`, define:

```text
Shell(r) = {(x, y): Q(x, y) = r*r}
```

This imports no angle, circumference, area, or real completion. It is an
algebraic predicate over rational nodes, and each participating node must be
read through the strict graph corpus.

The correct early claim is:

```text
Modulus of One has rational points satisfying a quadratic invariant.
```

not:

```text
Modulus of One has defined the circle.
```

## Unit-Shell Parametrization

The classical rational parametrization:

```text
x = (1 - t*t) / (1 + t*t)
y = (2*t) / (1 + t*t)
```

is allowed as an analysis-layer generator of exact rational candidates. It is
not, by itself, an internal derivation of the circle.

The strict graph question is:

```text
For a constructed rational t, are the corresponding x and y nodes present in
the strict corpus, and what are their construction witnesses?
```

The first implementation is read-only:

```sh
python3 -m moo.circle_probe --db out/experiments/strict_stage_graph_smoke.sqlite --unit-circle --node 3/4 --pretty
python3 -m moo.circle_probe --db out/experiments/strict_stage_graph_smoke.sqlite --unit-circle --pretty
```

Report language must say `unit_quadratic_shell` or `quadratic_shell`.
`circle-compatible rational probe` belongs only in external interpretation
notes until orbit/refinement criteria exist.

## Q-Preserving Transformations Later

Only after the shell report exists should Modulus of One inspect transformations.

A candidate transformation is admissible only if it is exact-rational and
preserves `Q`:

```text
Q(T(x, y)) = Q(x, y)
```

The first family to inspect is:

```text
[[a, -b],
 [b,  a]]

where a*a + b*b = 1
```

These should be called `Q-preserving transformations`, not rotations, until Modulus of One
has earned angle/orbit language through exact graph behavior.

## Euler Lenses

Euler is best folded in through exact finite rational structures before any
appeal to completed geometry.

The first read-only implementation is:

```sh
python3 -m moo.series_probe \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --geometric-ratio 1/2 \
  --geometric-terms 5 \
  --zeta-max-n 5 \
  --euler-max-prime 7 \
  --euler-local-geometric-terms 4 \
  --pretty
```

The geometric calibration uses:

```text
G_K(r) = sum over k = 0..K-1 of r^k
```

so `--geometric-terms 5` means exponents `0..4`.

It computes only exact finite rational families. Across its family rows, it
distinguishes:

```text
rational value-node presence
direct integer-quotient landing
intended term/sum/product recurrence edge
strict operand-policy blocker
```

The report never infers a recurrence edge from value co-presence and never
inserts analysis-layer edges into the corpus. Local Euler geometric expansions
are summarized by their exact finite endpoint and residual rather than by a
second nested term-by-term recurrence report. This v2 report is an
observation-layer primary-family pass; matched controls and held-out comparisons
remain outstanding.

### Basel Mass Lens

Track exact rational partial sums:

```text
S_N = 1 + 1/4 + 1/9 + ... + 1/N^2
```

Modulus of One-native observables:

```text
nodes for 1/n^2
partial-sum nodes S_N
first stages
confirmation status
witness diversity
denominator growth
convergence-chain graph structure
```

Allowed claim:

```text
Modulus of One can inspect exact finite reciprocal-square term and partial-sum nodes when
they are present in a strict corpus.
```

Disallowed claim:

```text
Modulus of One constructs pi from zeta(2).
```

### Euler Product Lens

Track finite prime products:

```text
P_N = product over p <= N of 1 / (1 - 1/p^2)
```

The series probe also records the exact finite local geometric truncation:

```text
1 + p^-2 + p^-4 + ... + p^(-2(K-1))
```

beside its exact residual to the closed factor `1 / (1 - p^-2)`. The exact
rational factor and finite truncation are both reported objects. Only reading
the factor as the completed infinite geometric-series limit is external.

Modulus of One-native observable:

```text
Does prime-indexed reciprocal-square construction differ from matched composite
controls in cost, witnesses, neighborhoods, or return behavior?
```

### Critical-Strip Zeta Lens

The quarter-turn phase supplies a precise external name for the imaginary unit:

```text
1/4 mod 1 -> exp(2*pi*i/4) = i
```

This does not make `1/4` a runtime complex operand. Under the phase map,
addition of phases corresponds to multiplication in `U(1)`, so the external
shadow of `i*i = -1` is:

```text
1/4 + 1/4 = 1/2 mod 1
```

Core rational multiplication still sends `1/4 * 1/4` to `1/16`. The two
operations must not be aliased.

There is now a second exact external calibration that does not depend on
complex exponentiation. On ordered integer pairs define

```text
J(x,y) = (-y,x)
(x,y)*(u,v) = (x*u-y*v, x*v+y*u).
```

Then `J^2=-I`, `J` preserves `x^2+y^2`, and pair multiplication obeys

```text
Norm(left*right) = Norm(left)*Norm(right).
```

This makes the imaginary unit precise as a quarter-turn operator before it is
treated as a scalar. The `D=-4` control and the stronger `D=-20` form-class
comparison are implemented by `moo/quadratic_form_probe.py` and governed by
[QUADRATIC_FORMS_CLASS_CHANNEL_LENS_NOTE.md](../number_theory/QUADRATIC_FORMS_CLASS_CHANNEL_LENS_NOTE.md). They remain
external pair/form structure; the runtime still has no complex operand or
quadratic-form class node.

The next finite analytic calibration is implemented by
`moo/theta_weil_probe.py` and governed by
[THETA_WEIL_CONSTRUCTIVE_OBLIGATIONS_NOTE.md](../number_theory/THETA_WEIL_CONSTRUCTIVE_OBLIGATIONS_NOTE.md). It preserves
the `D=-20` class channels and the Weil pairing `rho -> 1-conj(rho)`, then uses
a complete synthetic off-line quartet to show that same-point Gram and
diagonal-only projections erase the displacement. It does not evaluate the
arithmetic explicit formula or turn the synthetic points into zeta data.

For a critical-line input:

```text
s = 1/2 + i*t
n^(-s) = n^(-1/2) * exp(-i*t*log(n))
```

the unit phase is only one part of each term. The radial weight, logarithm,
generally irrational phase, complex addition, and analytic continuation remain
external. In particular, neither the ordinary Dirichlet series nor the Euler
product is used as a convergent construction in the critical strip.

The first read-only implementation is:

```sh
python3 -m moo.zeta_critical_probe \
  --db out/experiments/strict_stage_graph_smoke.sqlite \
  --sigma 0.5 \
  --t 14.134725141734693 \
  --hasse-terms 64 \
  --control-delta 0.01 \
  --near-zero-tolerance 1e-10 \
  --stability-tolerance 1e-12 \
  --target-kind user_supplied_reference_zero \
  --target-label first_nontrivial_zero_coordinate \
  --pretty
```

It uses a finite Hasse form of the Euler-transformed eta representation:

```text
zeta(s) ~= [sum over k=0..K-1 of
              2^(-k-1) * sum over j=0..k of
              (-1)^j * C(k,j) * (j+1)^(-s)]
            / (1 - 2^(1-s))
```

The finite triangular sum is regrouped by source integer. Its coefficients are
computed and stored exactly outside the graph as rational weights; only the
complex powers and accumulation use Python binary64 complex arithmetic. The
graph report audits:

```text
quarter-turn source and blocked phase-addition edges
positive integer source nodes
direct rational reciprocal precursor edges
a named sample of interior Pascal coefficient recurrence edges
two consecutive cutoff changes under an independent stability threshold
cancellation conditioning and a non-rigorous binary64 roundoff proxy
same-algorithm conjugate consistency and a horizontal/vertical local cross
s=2, s=-2, s=1, and removable eta-bridge guards
```

The Pascal scaffold is not a specific signal by itself: ordinary eligible
positive-integer addition explains its witnessed edges. Likewise, a rational
phase approximation selected from an external complex term is not a
graph-native phase selection; its node-presence summary is visualization only.
The default Pascal audit reaches only a named sample of the rows required by a
64-row Hasse evaluation and reports that coverage gap explicitly.

The `user_supplied_reference_zero` mode requires `0 < sigma < 1` and a label,
but the label and coordinate remain caller assertions. The probe does not look
them up or independently recognize a known zero. Its residual tolerance and
cutoff-stability tolerance are separate, and a positive separation reading also
requires the empirical term preflight, roundoff proxy, and calibration suite to
pass.

Allowed claim:

```text
The external finite approximation shows controlled weighted cancellation over
graph-audited integer and rational sources.
```

Disallowed claims:

```text
Modulus of One contains zeta(s) as a runtime object.
The graph constructs the reported complex residual or node 0.
A residual below a configured tolerance certifies an exact zero.
A critical-line calibration proves the Riemann hypothesis.
A nearest rational phase node witnesses the external complex phase.
```

Certification would require rigorous interval bounds and a zero-counting method
such as an argument-principle or Hardy-Z/Turing-style calculation. Those are not
implemented. Euler's `e^(ix)` remains delayed as runtime semantics below; this
probe uses complex exponentiation only as an explicit external analysis layer.

#### Cancellation-arrival follow-up

The next read-only question is not whether the terminal residual is small, but
how the fixed finite cancellation is revealed as graph evidence arrives. The
follow-up tool is:

```sh
python3 -m moo.zeta_arrival_probe \
  --db out/experiments/circle_as_one_u80.sqlite \
  --sigma 0.5 \
  --t 14.134725141734693 \
  --hasse-terms 64 \
  --stage-horizon 64 \
  --control-delta 0.01 \
  --height-control-ts 10,11,12,13,15,16,17,18,19,20 \
  --envelope-guard 1e-12 \
  --stability-tolerance 1e-12 \
  --near-zero-tolerance 1e-10 \
  --permutation-samples 4096 \
  --target-kind user_supplied_reference_zero \
  --target-label first_nontrivial_zero_coordinate \
  --full-scan \
  --pretty
```

Saved paired evidence and interpretation:

```text
../../out/experiments/euler/zeta_arrival_first_zero_u80_v1.json
../../out/experiments/euler/zeta_arrival_first_zero_u300_broad_v1.json
../../out/experiments/euler/zeta_cancellation_arrival_v1.analysis.md
```

For fixed terminal `K`, define the externally evaluated source term

```text
c_n(s) = A_(K,n) * n^(-s)
```

and reveal it at graph stage `u` only when the named mask admits source `n`.
The primary aligned mask requires both:

```text
integer n is confirmed by the positive spine at or before u
direct retained edge 1 / n -> 1/n exists at or before u
```

The coefficients `A_(K,n)` still use all terminal Hasse rows `0..K-1` at every
stage. Therefore this is a fixed-`K` source reveal, not a stage-`u` Hasse
approximation and not a runtime calculation.

The report first validates contiguous strict stages and complete candidate-event
counts through the requested horizon. A direct `1/n` edge is reciprocal
construction evidence for this external gate; except for `n=1`, the result
node `1/n` is not operand-ready and is never used as a runtime operand here.

For `n=1..64` in the saved strict corpora, confirmation and the first direct
reciprocal edge both occur at stage `n`. The aligned path is consequently the
ordinary source prefix `1,2,...,64`. That equality is an important negative
result: the graph supplies the positive-spine schedule, but no additional
topology orders these analytic terms.

At the caller-supplied reference coordinate, the aligned normalized radius
peaks at stage 2. After that peak, 56 binary64-resolved changes are all inward;
the longest inward streak is 56 and radial efficiency is effectively 1. The
four local controls have longest inward streaks of only 7 to 9. Sustained local
separation begins at stage 37 and exceeds factors of 10, 100, and 1000 at stages
40, 44, and 46.

Endpoint-preserving perturbations shuffle whole `c_n` values only inside
adjacent source blocks. None of 4096 block-size-2 or block-size-4 permutations
matches the aligned inward streak, inward fraction, or efficiency. The reported
add-one tail fraction is `1/4097`, explicitly an exploratory rank rather than a
formal p-value. Prefixes and endpoints use real/imaginary `math.fsum`; all null
endpoints match the canonical binary64 endpoint exactly in the saved runs. The
blocks and thresholds are fixed in probe v1 after exploratory calibration, not
preregistered, and the coordinate and metrics are not a blind discovery protocol.

The tempting alternative is bare node presence. In a broad corpus, composite
integer results appear speculatively through balanced addition and
multiplication; all sources through 64 are visible by stage 31. That mask moves
local-control separation much earlier, but it is aperture-sensitive and admits
unconfirmed nodes. It is an inspection contrast only. Any claimed computational
acceleration confined to this mask is rejected as speculative-operand leakage.

The finite cancellation envelope compares the current prefix magnitude with
the total L1 magnitude still available in unrevealed terms. Exiting the envelope
means the remaining finite terms cannot reach zero. Staying inside is merely a
necessary condition. Likewise, tail-to-terminal capture is almost identical at
the reference and local controls; it is attributed to the Hasse amplitude
envelope, not zero-specific choreography.

The surviving interpretation is deliberately narrow:

```text
The natural positive-spine source order gives unusually monotone external
finite cancellation at this caller-supplied reference coordinate.
```

It is not yet a graph-specific zeta result, because that operational order is
exactly ordinary integer order. It does not construct, discover, or certify a
zero.

#### Centered reciprocal-shell follow-up

The centered normalization suggested by the unit-shell work is now audited by
`moo/zeta_centered_inversion_probe.py` and governed in detail by
[CENTERED_RECIPROCAL_SHELL_LENS_NOTE.md](CENTERED_RECIPROCAL_SHELL_LENS_NOTE.md). With

```text
u = 2*s - 1
J(u) = -1/u
w = (s - 1)/s
```

the exact external action is `w -> -1/w`. It pairs the rational shell
parameters by `t -> 1/t`, preserves the four Gaussian units in the normalized
external `w` plane as a set, and
gives a chosen real homogeneous lift with `S^2=-I`. Required distinctions are:

```text
the u-unit circle is not the w-unit critical line
U(Q) is not the rational-phase root-of-unity set
J is a D4 reflection on {1,i,-1,-i}, not the C4 quarter-turn
an order-four matrix representative is lift data, not projective runtime order
```

The U80 and U300 first-zero reports are:

```text
../../out/experiments/euler/zeta_centered_inversion_first_zero_u80_v1.json
../../out/experiments/euler/zeta_centered_inversion_first_zero_u300_broad_v1.json
```

Both show all eight bounded forward `1/n` witnesses, only the trivial `n=1`
reverse witness, and paired shell-component visibility only at `n=1`. Thus the
reciprocal substrate is present but the centered interaction remains an
external candidate lens.

The proposed zeta-zero-symmetry subclaim is closed, not pending. The supplied
first-zero coordinate has finite `K=64` residual about `2.16e-15`, while its centered
image at height `1/(4*t)` has stable magnitude about `1.4594994686`. More
decisively, any fixed positive radius sends an unbounded sequence of zeros
toward the regular nonzero point `s=1/2`, so global zero-set invariance would
contradict isolatedness of analytic zeros. The exact geometry survives this
kill test; the proposed zeta-zero symmetry does not. Precomposing to study
`zeta(I_R(s))` instead permits accumulated transformed zeros because the center
becomes an essential singularity, but that is a new representation rather than
a symmetry of zeta.

### Zero/Product Lens

Euler's sine-product insight is useful only as a later structural analogy.

Allowed early object:

```text
exact finite product families and return-to-zero corridors
```

Disallowed early object:

```text
sine as a Modulus of One-native function
```

### Delayed Objects

Delay these until strict shell/orbit/return/refinement structures exist:

```text
pi
circumference
area
angle
sine
Euler's e^(ix)
polygon perimeter limits
```

## Controls

Any circle or `pi` lead must beat controls before promotion:

```text
denominator-matched rational controls
construction-cost matched node controls
parametric placebo curves
graph-shuffle nulls
operation-label shuffle nulls
nearby corpus-bound sensitivity checks
held-out strict corpora
```

Failure criteria:

```text
matched placebo curves score similarly
the effect disappears under small bound changes
only one hand-picked node supports it
the metric was chosen after seeing the result
raw approximation to pi is no better than continued-fraction baselines
graph shuffles preserve the signal
```

## Original Circle-Probe Milestone

Implement:

```text
moo/circle_probe.py
```

as a read-only SQLite report over strict graph corpora.

It should initially report:

```text
unit-shell candidate from t
x and y exact rationals
x*x + y*y = 1 exact check
t/x/y node presence
first stages and confirmation stages
incoming witness counts
operation histograms
baseline features
sign-symmetry coverage
claim_status: observation
```

No new runtime semantics, no schema changes, and no `pi` probe in the first
milestone.
