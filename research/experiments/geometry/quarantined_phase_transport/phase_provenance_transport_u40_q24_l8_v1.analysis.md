# Phase Provenance Transport U40 Q24 L8 V1 Analysis

> Result: `insufficient_aperture`.
>
> Claim boundary: quarantined external `C_q` accumulation over read-only strict
> graph evidence; not a runtime path and not operation on speculative nodes.

## Identity And Integrity

The saved report authenticated every frozen identity field: experiment id,
database path and SHA-256, schema/config, strict frontier-stage contract,
preregistration path and SHA-256, checkpoint, caps, null count, stage bin, and
seed.

```text
source database SHA-256:
  12d358def1827b217a603a6da1aa793aa3525eb28b135fd3991af1bbcdc279ad

probe SHA-256:
  364167fe749f7695b02db7e2907b715cce202c2ae6f20f4ed5de6c7f5b89bb57

selection SHA-256:
  9ca573a2607ec73182b16c973f406b342f45932dea3962369bc53d903b6f1d97

saved report SHA-256:
  c5344e9669d3a6a6ea53b48578f99df61091dde09eedf55653652968db0ecee5
```

The source database was opened by SQLite URI `mode=ro` with
`PRAGMA query_only=ON`. All source-node, edge, exposure, and witness queries
were checkpoint-scoped through U40.

## Graph Aperture

```text
eligible / selected division occurrences: 984 / 984
accepted paths:                         55
discovery / holdout paths:              27 / 28
holdout q values:                       14
mutable holdout positions:              24 / 224 = 3/28
```

Two frozen gates failed:

```text
holdout paths:       28 < 32
mutable fraction:   3/28 < 1/4
```

The distinct-q and absolute mutable-position gates passed. Because every gate
was required, the report cannot emit either a retain or kill verdict.

## Descriptive Statistic And Controls

These values are preserved for diagnosis, not promoted into a decision after
the aperture failure.

```text
observed holdout statistic: 9/56

exact-step permutation:
  mean:               39545/344064
  99th percentile:    197/1176
  upper-tail +1 rank: 88/4097

exact-(q,stage,exposure,hub) label shuffle:
  mean:               391903/2408448
  99th percentile:    75/392
  upper-tail +1 rank: 2352/4097
```

The observed value exceeded the exact-step mean but not its 99th percentile;
it exceeded neither the stratified mean nor its 99th percentile. More
importantly, the stratified control could move only `3/28` of holdout
positions, so those comparisons are not treated as a make-or-break test.

## Interpretation

The corrected strict-stage orientation removed same-stage insertion order from
the path clock. Under that graph-respecting definition, U40 did not provide
enough holdout paths or enough label mobility for the frozen conditional null.
This is informative about the estimator, not evidence for or against phase
transport.

The only authorized follow-up is the separately preregistered U80
aperture-resolution run. No U40 threshold, stage bin, path length, seed, or cap
is changed after seeing this result.
