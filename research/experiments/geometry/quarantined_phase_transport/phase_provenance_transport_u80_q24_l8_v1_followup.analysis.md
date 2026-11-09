# Phase Provenance Transport U80 Q24 L8 V1 Follow-up Analysis

> Result: `insufficient_aperture`.
>
> Consequence: the preregistered stop rule fires; no further current-design
> transport run or post-result tuning is authorized.

## Identity And Integrity

Every frozen U80 follow-up identity field passed, including the independently
recorded corpus and preregistration hashes, the strict frontier-stage audit,
checkpoint U80, unchanged caps/statistic/controls, 4096 null draws, exact-stage
binning, and seed 1729.

```text
source database SHA-256:
  796e043087eee8908c840d21f1c14235310c0093e816927bbab8374fbd0d4780

probe SHA-256:
  364167fe749f7695b02db7e2907b715cce202c2ae6f20f4ed5de6c7f5b89bb57

selection SHA-256:
  d00a685e91f6370e7d24398f1c74ecb5a042d66875c690949ee232a275953bae

saved report SHA-256:
  18fcd803fe59d97fa6a43fb7ffab85c6aa7dcaa1399cebd113e30f7988713444
```

The pre-existing U80 corpus has a narrower value bound than the U40 primary;
the follow-up was not pooled with U40. It was chosen and frozen only to ask
whether a longer strict-stage horizon resolves the original aperture failure.

## Graph Aperture

```text
eligible / selected division occurrences: 2219 / 2219
accepted paths:                          142
discovery / holdout paths:               74 / 68
holdout q values:                        21
mutable holdout positions:               104 / 544 = 13/68
```

U80 resolved the U40 path-count problem: 68 holdout paths exceed the required
32. It also passed the distinct-q and absolute mutable-position gates. The
fractional mutability gate still failed:

```text
13/68 < 1/4
```

Thus the strict exact-stage/exposure/hub null remains too immobile for the
preregistered inference even after the stage horizon doubled.

## Descriptive Statistic And Controls

These values remain descriptive because the aperture gate failed.

```text
observed holdout statistic: 3215/24696

exact-step permutation:
  mean:               1423661/14450688
  99th percentile:    1651/12348
  upper-tail +1 rank: 71/4097

exact-(q,stage,exposure,hub) label shuffle:
  mean:               98291/802816
  99th percentile:    209/1372
  upper-tail +1 rank: 63/241
```

The observed value exceeded both null means but neither 99th percentile. The
unchanged retention conjunction therefore would not have been met even if the
aperture had passed, but the official result remains `insufficient_aperture`,
not `kill_current_hypothesis`.

## What This Meaningfully Resolves

The follow-up separates mere U40 path scarcity from the deeper limitation.
More stages supplied ample paths and q coverage, yet the strict stratified null
still could not relabel at least one quarter of held-out positions. The current
path/null pairing is therefore not estimable from either available
circle-as-one corpus under its own guardrails.

Per the preregistration, stop here. Do not coarsen stage bins, shorten paths,
lower the mutability threshold, switch seeds, pool corpora, or try a third
corpus after seeing these outcomes. A future phase experiment would need a new
independent motivation—preferably a graph-native nonidentity transition or a
design whose null mobility can be established before return statistics are
inspected.
