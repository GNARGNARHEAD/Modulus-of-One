# August 2026 External Probe Results And Provenance

> Status: superseded as lifecycle authority; retained as a results and
> provenance record.
>
> An earlier consolidation used these versioned results to retire whole tool
> families and research lenses. That lifecycle decision is withdrawn. The
> source, tests, and primary notes have been restored and remain governed by
> their own claim boundaries. This file preserves the useful methods,
> measurements, hashes, negative results, and failure boundaries. Local raw
> JSON reports under `out/experiments/` are retained as durable machine
> evidence. Large SQLite inputs remain local-only and are checksum-bound in
> `out/experiments/CORPUS_INVENTORY.md`.

## How To Read These Results

MoO's primary object is a witnessed construction graph. An external calculation
does not become a runtime or graph-native result merely because it is exact.
It can still remain a maintained calibration, falsification instrument, or
source of explicit next obligations when its evidence layer and claim limits
remain clear.

The studies below were internally careful, but their strongest outcomes were
calibrations, analytic rejections, or demonstrations of information that an
external projection can erase. Those outcomes constrain specific claims and
versioned experiments; they do not by themselves retire the associated tools
or every broader lens. Code size is not a scientific lifecycle criterion.

## Exact Phase Metric Scout

The U40 scout pulled the shortest-arc metric on `R/Z` back to rational
sources:

```text
phase(x) = x mod 1 in [0,1)
d_phase(x,y) = min over n in Z of abs(x-y-n)
```

It correctly established that distinct rational nodes have zero phase distance
exactly when their difference is an integer. The exact metric, triangle slack,
sampled-path contraction, and retained-lift helpers remain in `moo_phase.py`.
Their core axioms and path cases remain tested in `test_moo_phase_operator.py`.

The bounded graph comparison did not earn a phase-fibre effect. Across 54
successfully matched observations:

```text
median same-phase neighborhood distance:      0.6499344864
median matched different-phase distance:      0.6582890002
median per-pair same-minus-control difference: 0.0089505924
```

These medians are alike at the resolution of this observation. The U40 result
does not promote a special phase-fibre effect. The exact metric, probe, tests,
and research note remain maintained for calibrated graph-divergence and
retained-lift questions.

Local report identity:

```text
phase_metric_collapse_u40_wide_d12_v1.json
sha256 8862b924a1454612348d4bc311a7ff1d67cd35782f2ea04770b39bcfcaa67637
```

## External Critical-Line Calibration

The critical probe evaluated a finite 64-row Hasse/eta approximation
at the caller-supplied coordinate

```text
s = 0.5 + 14.134725141734693*i.
```

It produced a binary64 residual of
`2.1570095574950392e-15`, passed its finite-cutoff and local-control checks,
and deliberately left `target_certified_zero=false`. The numerical result was
identical across the two corpora. Differences in source and Pascal-edge
coverage followed their stage/value bounds and were not zeta-specific graph
evidence.

The coordinate was not discovered or independently certified by the probe.
Complex powers, analytic continuation, and accumulation were external to MoO.
This therefore remains a numerical calibration, not a runtime construction or
zero result.

Recorded tool identity for this summarized run:

```text
moo_zeta_critical_probe.py
sha256 95c0010bcc4e48339ba83526ee2487259af990067f849cf6c67db0d9d3a961db
```

## Fixed-Basis Cancellation Arrival

The arrival follow-up held one external 64-source Hasse basis fixed and revealed
terms according to graph timestamps. Its admissible gate required both source
confirmation and a direct `1/n` witness.

For every `n=1..64`, both events occurred at stage `n`. The admissible trajectory
was therefore exactly the ordinary integer prefix:

```text
1,2,3,...,64.
```

That natural order had a 56-step resolved inward streak at the supplied
coordinate and ranked above all 4,096 adjacent-block perturbations in the
configured exploratory null. But this was not a graph-specific ordering: it
was ordinary positive-spine order. In the broad U300 corpus, speculative node
presence exposed all sources by U31, yet that graph-shaped contrast had streak
11 and an add-one upper-tail rank

```text
901/4097 = 0.21991701244813278.
```

The richer graph-presence order was ordinary under its own null and inadmissible
as operand scheduling. The earned result was a negative graph-specific control.

Recorded tool identity for this summarized run:

```text
moo_zeta_arrival_probe.py
sha256 5146f6807d2871f0acb71626bb322926f971a163f2bc478462f68d5bf72869d9
```

## Centered Reciprocal Inversion

The exact centered map at radius `1/2` was

```text
I(s) = 1/2 - 1/(4*(s-1/2)).
```

Its rational shell identities were correct external geometry. The proposed
global zeta-zero symmetry was not merely unsupported; it was analytically
impossible. Nontrivial zeta zeros have unbounded ordinates. If `I` preserved
them, a sequence with `abs(Im(rho_n)) -> infinity` would yield distinct zeros

```text
I(rho_n) -> 1/2.
```

Zeta is analytic and not identically zero near `1/2`, so its zeros are isolated
there. Such an accumulation contradicts the identity theorem.

The finite control agreed with that exact obstruction. At the supplied
coordinate the Hasse residual was about `2.16e-15`; at its centered image the
stable magnitude was about `1.4594994686`. The U80 and U300 graph audits also
found all eight forward `1/n` witnesses but only the trivial `n=1` reverse
witness. Co-presence did not provide a graph-native transformation.

Precomposing zeta with `I` would define a different function with a singular
center. It would not make `I` a symmetry of zeta's original zero set.

Recorded tool identity for this summarized run:

```text
moo_zeta_centered_inversion_probe.py
sha256 4613471d324f8cdaab4c12c750cc9403442a57286cc76398c3a68310050c82c5
```

## Theta And Weil Cross-Term Calibration

This calibration's exact controls remain useful. They are external assembly
fixtures rather than MoO graph results, and they expose the obligations that a
future theorem-bearing analytic layer must satisfy.

The `D=-20` character-to-class inversion requires cross terms. Two exact cases
made the loss explicit:

```text
n=2: (a_plus,a_minus) = (1,-1)
     a_A^2 = (1+1-2)/4 = 0
     diagonal-only value = 1/2

n=6: (a_plus,a_minus) = (2,2)
     a_B^2 = (4+4-8)/4 = 0
     diagonal-only value = 2
```

Likewise, with

```text
U = 2^(-1/2) * [[1,1],[1,-1]]
H_character = diag(1,4)
H_class = U^T H_character U = 1/2 * [[5,-3],[-3,5]],
```

deleting the off-diagonal entries destroys the character directions even
though the remaining matrix looks harmless.

For the Weil involution `iota(rho)=1-conj(rho)`, the synthetic complete quartet

```text
0.7 +/- 3i, 0.3 +/- 3i
```

gave a full finite matrix with two clear negative binary64 eigenvalues,
approximately `-2.5762970828` and `-1.5351906746`. The same-point Gram surrogate
and diagonal-only surrogate both passed. The algebraic core of the control was

```text
true involutive matrix = 2 * [[0,1],[1,0]]  eigenvalues -2,2
same-point surrogate   = 2 * [[1,0],[0,1]]  eigenvalues  2,2.
```

This proves that the shortcut can erase off-line displacement in the synthetic
fixture. It says nothing about actual zeta zeros.

The missing obligations were decisive:

- no independently computed arithmetic explicit-formula matrix;
- no complete zero sum or rigorous tail replacement;
- no theorem-sufficient dense test family;
- no all-dimensions limiting argument;
- no certified numerical error ledger;
- no graph-native test-function selection rule.

The strict graph contributed audited scalar sources only. It did not contain
theta weights, Mellin transforms, zero points, or Weil edges.

Recorded tool identity for this summarized run:

```text
moo_theta_weil_probe.py
sha256 dc5777d14d7059e73848940c743d3c1abc5a4eb66cbc0869e8f3dbdfd6934861
```

## Restored And Maintained Source Surface

The following files were previously removed by an overbroad consolidation.
They have been restored and remain part of the repository's reproducible
research surface, subject to the claim boundaries in their primary notes:

```text
moo_phase_metric_probe.py
test_moo_phase_metric_probe.py
research/geometry/PHASE_METRIC_COLLAPSE_NOTE.md

moo_zeta_critical_probe.py
test_moo_zeta_critical_probe.py
moo_zeta_arrival_probe.py
test_moo_zeta_arrival_probe.py
moo_zeta_centered_inversion_probe.py
test_moo_zeta_centered_inversion_probe.py
research/euler/CENTERED_RECIPROCAL_SHELL_LENS_NOTE.md

moo_theta_weil_probe.py
test_moo_theta_weil_probe.py
research/number_theory/THETA_WEIL_CONSTRUCTIVE_OBLIGATIONS_NOTE.md
```

The separate zeta analysis notes are also present as the primary
human-readable interpretations of their saved runs. The exact phase operator,
finite-series probe, circle-as-one quotient, congruence control, maintained
quadratic-form infrastructure, and phase-transport machinery remain in the
tree. The U850 quadratic-form v1 evidence package remains frozen, while the
quadratic tools and downstream theta/Weil calibration remain maintained.

`Qwen3-8-27B-Analysis-full-conversation.md` has likewise been restored as
historical source context. The distilled projection-degeneracy note remains
the falsifiable research protocol; the conversation itself is context, not
evidence.

## Continuation Rule

The restored tools may reproduce their exact bounded studies for regression,
provenance, or calibration. Repeating the same input does not promote a claim.
A new claim needs an explicit observable and, where inferential weight is
sought, a new versioned design showing how it distinguishes graph construction
from ordinary source order, corpus aperture, or externally supplied analytic
structure. Existing analytic rejections and frozen stop rules remain binding
within their stated scope.
