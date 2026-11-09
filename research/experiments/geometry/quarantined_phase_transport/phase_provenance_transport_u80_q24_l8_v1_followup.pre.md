# Phase Provenance Transport U80 Q24 L8 V1 Follow-up Preregistration

> Status: frozen before any U80 transport-path extraction or scored report.
>
> evidence_layer: quarantined counterfactual over read-only strict graph
>
> claim_status: aperture-resolution follow-up
>
> experiment_id: phase_provenance_transport_u80_q24_l8_v1_followup

## Why This Follow-up Exists

The frozen U40 primary passed its identity and operator audits but returned
`insufficient_aperture`: 28 holdout paths rather than 32, and 3/28 mutable
holdout positions rather than 1/4. That result is not a retain or kill.

This one follow-up distinguishes two possibilities without relaxing the test:

```text
U80 reaches the original aperture:
  apply the unchanged frozen retain/kill rule

U80 remains insufficient:
  stop this line; the present strict-path/null design is not estimable from
  the available circle-as-one corpora
```

Before freezing this file, only the U80 corpus identity, schema, configuration,
stage count, node count, edge count, and SHA-256 were inspected. No U80
transport paths, residues, return statistic, null sample, or aperture result
was computed.

## Frozen Source And Identity

```text
corpus:
  out/experiments/circle_as_one_u80.sqlite

corpus SHA-256:
  796e043087eee8908c840d21f1c14235310c0093e816927bbab8374fbd0d4780

schema version:
  1

config:
  generator = strict_stage_moo_graph
  max_stage = 80
  max_abs_p = 200
  max_abs_q = 200
  max_abs_value = 4.0
  retain_confirmed_edges = true

checkpoint:
  U80
```

The smaller value bound is a property of the pre-existing corpus, not a tuned
probe parameter. This follow-up may resolve aperture for that corpus; it is not
pooled with U40 and does not replace the U40 result.

## Frozen Probe Configuration

Everything below is unchanged from the U40 primary:

```text
eligible exact result denominators:
  q in [3, 24]

path length:
  8 occurrence nodes

caps:
  512 eligible occurrences per q
  32 outgoing neighbors per occurrence
  64 accepted paths per q

null samples:
  4096

stage-bin width:
  1 (exact source stage)

seed:
  1729
```

Selection remains q-conditioned and residue-blind. Two division occurrences
are adjacent only when their exact source edges share a confirmed input node,
and an arc requires a strictly increasing source stage. Canonical source-edge
content, not SQLite insertion ids, controls caps, neighbor ordering, path
selection, and the discovery/holdout split. Paths must contain eight distinct
edge occurrences and eight distinct results, with an exact shared-input
witness for each transition, and are occurrence-disjoint within q.

## Frozen Statistic And Controls

For residues `s_1,...,s_8` in ordinary additive `C_q`, accumulate externally:

```text
X_0 = 0
X_t = X_(t-1) + s_t mod q
```

The path score counts proper-prefix returns at `t` in `[1,7]`. Scores are
normalized by seven, averaged within q, then equally across holdout q values.

The controls remain:

1. exact-step permutation within each fixed path;
2. label shuffling within exact `(q, source stage, exposure bin, hub bin)`
   strata.

Both use 4096 deterministic draws and exact `Fraction` comparisons.

## Unchanged Aperture And Decision Rule

Return `insufficient_aperture` unless the holdout contains all of:

```text
at least 32 occurrence-disjoint paths
at least 4 distinct q values
at least 16 mutable label-shuffle positions
at least 25 percent mutable label-shuffle positions
```

With sufficient aperture, retain only if the observed statistic exceeds both
the mean and the 99th percentile of both frozen controls. Otherwise kill the
current provenance-conditioned hypothesis in this U80 aperture.

No secondary path length, coarser stage bin, lower mutability threshold,
alternate seed, pooled U40/U80 statistic, or further corpus is authorized by
this preregistration.

## Claim Boundary

The result concerns only an external `C_q` accumulator over q-conditioned,
residue-blind provenance walks. Rational result nodes remain non-operational;
the walks are not runtime paths; and neither a positive nor negative result is
evidence that `Q/Z` inherits rational multiplication or division.
