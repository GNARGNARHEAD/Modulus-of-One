# Exact Finite Series Probe: U300 / U1000 Observation

> Status: observation-layer report over two saved strict positive-spine graph
> corpora. This is not a convergence result and does not construct an infinite
> geometric series, zeta(2), or pi.

## Reports

```text
out/experiments/euler/series_zeta_probe_u300_v2.json
out/experiments/euler/series_zeta_probe_u1000_v2.json
```

Both reports use:

```text
geometric ratio: 1/2
geometric terms: 8, exponents 0..7
zeta(2) cutoff: N = 6
Euler prime cutoff: p <= 7
local geometric diagnostic: 4 terms per Euler factor
```

The source corpora both pass the strict alignment audit with zero speculative
input edges and zero non-core operand edges.

## Main Result

| Evidence family | U300 | U1000 |
|---|---:|---:|
| Geometric partial endpoints present | 8/8 | 8/8 |
| Geometric term recurrence steps present | 0/7 | 0/7 |
| Geometric accumulation steps present | 0/7 | 0/7 |
| Zeta partial endpoints present | 4/6 | 4/6 |
| Reciprocal-square term edges present | 6/6 | 6/6 |
| Zeta accumulation steps present | 0/5 | 0/5 |
| Closed Euler-product endpoints present | 3/4 | 3/4 |
| Direct Euler-factor quotient edges present | 4/4 | 4/4 |
| Euler product steps present | 0/4 | 0/4 |
| Four-term local geometric endpoints present | 1/4 | 2/4 |

All five zeta accumulation steps and all four Euler product steps are ineligible
under the strict operand aperture because at least one operand is a speculative
rational. Missing later endpoints are additional corpus censoring, not the
primary recurrence blocker.

The strict graph does contain the exact finite ingredients:

```text
n * n -> n^2
1 / n^2 -> 1/n^2
p^2 / (p^2 - 1) -> closed Euler factor
```

It does not contain the rational accumulation/product lineages:

```text
S_(N-1) + 1/N^2 -> S_N
P_(j-1) * factor_p -> P_j
```

## Corpus Aperture

The zeta endpoints through `205/144` are present. `5269/3600` and
`5369/3600` are absent in both corpora because their reduced denominators exceed
the saved denominator bounds and their canonical quotient stages exceed the
saved stage bounds.

The Euler product through prime `5`, `25/16`, is present. The product through
prime `7`, `1225/768`, is absent in both corpora. The local four-term geometric
endpoint for `p=3`, `820/729`, is absent at U300 but present at U1000; this is the
only main coverage change between the two reports.

## Cross-Family Collision

The nontrivial shared endpoint is:

```text
3/2
```

It is both the second `r=1/2` geometric partial sum and the closed Euler product
through prime `3`. In the graph it first appears as `3 / 2`, has only scaled
division witnesses, and has no outgoing operand edges. This is a value collision,
not shared series/product construction lineage.

For the configured finite cutoffs:

```text
1225/768 - 5369/3600 = 5971/57600
```

This exact gap compares two different finite truncations only.

## Positive Control

On the same U300 corpus, the eight-term integer-ratio calibration `r=2` reports:

```text
partial endpoints present: 8/8
term recurrence steps present: 7/7
accumulation steps present: 7/7
```

The probe therefore detects recorded recurrence lineage when the operands are
eligible; the zero counts for the convergent rational families are not a
boolean-reporting artifact.

## Interpretation And Next Controls

The current result supports the measurement distinction:

```text
value-node presence != named series recurrence
```

It does not yet test denominator/height-matched controls, reverse accumulation,
count-matched composite products, graph shuffles, or a preregistered held-out
corpus. Those controls are required before promoting the Euler reciprocal-mass
lens beyond observation.
