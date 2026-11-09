# Phase Provenance Transport U40 Q24 L8 V1 Preregistration

> Status: frozen before the first scored report.
>
> evidence_layer: quarantined counterfactual over read-only strict graph
>
> claim_status: make-or-break exploratory test

> experiment_id: phase_provenance_transport_u40_q24_l8_v1

> Semantic amendment before the saved primary report: implementation review
> corrected "phase-blind" to "residue-blind conditional on q" and rejected
> same-stage SQLite insertion order as time. No statistic, threshold, corpus,
> path length, cap, seed, null, or decision rule changed.

## Question

Does the q-conditioned, residue-blind order of nearby division occurrences in the strict graph
produce more proper-prefix returns to identity than ordinary cyclic-group
transport with the same denominator, path length, and exact step multiset?

This does not ask whether rational nodes operate in aligned MoO. They do not.
It asks whether strict graph provenance orders externally attached phase labels
in a way not already explained by their ordinary composition in `C_q`.

## Frozen Source And Aperture

```text
corpus:
  out/experiments/circle_as_one_u40_wide.sqlite

checkpoint:
  U40

eligible occurrences:
  recorded division edges through U40
  strict alignment must pass
  exact result-phase denominator q in [3, 24]

path length:
  8 occurrence nodes

caps:
  at most 512 eligible occurrences per q
  at most 32 outgoing neighbors per occurrence
  at most 64 accepted paths per q

null samples:
  4096

stage-bin width for the stratified shuffle:
  1 (exact source stage)

deterministic seed:
  1729
```

The caps remain active in every mode. Truncation and excluded counts must be
reported.

## Q-Conditioned, Residue-Blind Provenance Walks

Two eligible division occurrences are adjacent when their exact source edges
share a confirmed input node. Orientation requires a strictly increasing source
stage. Same-stage SQLite insertion order is not treated as time and creates no
oriented transition. Seed selection, degree truncation, and the holdout split
use deterministic hashes of canonical source-edge content and the frozen seed,
not database insertion ids. The exact denominator `q` defines each conditional
stratum; phase residue, endpoint state, and return count are forbidden from all
selection and tie-breaking within that stratum.

Accepted paths must:

```text
contain eight distinct edge occurrences
contain eight distinct result nodes
carry an exact shared-input witness for every transition
be occurrence-disjoint from every other accepted path for the same q
```

The accepted path is a provenance walk, not a runtime construction path.

## External Transport And Primary Statistic

For residues `s_1,...,s_8` in `C_q`, accumulate externally:

```text
X_0 = 0
X_t = X_(t-1) + s_t mod q
```

The path score is the number of proper-prefix returns:

```text
R(P) = count of t in [1, 7] with X_t = 0
```

The endpoint is excluded because the total sum is unchanged by permuting the
steps. Normalize by seven, average within each `q`, and then average equally
across eligible `q` values so large fibres do not dominate.

## Frozen Controls

### Exact-step permutation

Keep every accepted provenance path and its exact residue multiset fixed.
Independently permute step order within each path for every null replicate.
This is the primary ordinary-`C_q` baseline. It preserves `q`, path length,
repeated-step pattern, graph selection, and endpoint.

### Stage/exposure/hub-stratified label shuffle

Keep the provenance paths fixed and shuffle phase residues among eligible
occurrences only within strata defined by:

```text
q
exact source stage (stage-bin width 1)
floor(log2(max(1, checkpoint incoming-witness count)))
floor(log2(max(1, shared-input hub degree)))
```

This guards against generator order, stage, witness exposure, and input-hub
structure. A holdout occurrence position is mutable only when its stratum has
at least two occurrences carrying at least two distinct residues.

## Holdout

Accepted paths are assigned by a stable SHA-256 hash of the seed, `q`, and the
complete canonical source-edge sequence. Even hash parity is discovery; odd
parity is holdout. The decision statistic uses holdout paths only. Discovery
output may diagnose the aperture but may not change thresholds or selection
rules. Corpus edge ids remain in the report as evidence but do not control the
selection or split.

## Decision Rule

Return `insufficient_aperture` unless the holdout contains:

```text
at least 32 occurrence-disjoint paths
at least 4 distinct q values
at least 16 mutable label-shuffle positions
at least 25 percent mutable label-shuffle positions
```

Retain a provenance-conditioned transport candidate only when all are true:

```text
observed holdout statistic exceeds the exact-step null mean
observed holdout statistic is above its exact-step 99th percentile
observed holdout statistic exceeds the stratified-shuffle null mean
observed holdout statistic is above its stratified-shuffle 99th percentile
```

Otherwise the frozen decision is `kill_current_hypothesis`.

Interpretation of failure:

```text
beats neither control:
  no provenance-order signal in this aperture

beats an iid diagnostic but not exact-step permutation:
  ordinary step-composition arithmetic

beats exact-step permutation but not the stratified shuffle:
  stage, exposure, or input-hub ordering
```

## Claim Boundary

Allowed:

```text
the external accumulator over these q-conditioned, residue-blind provenance walks did or did
not exceed the two frozen cyclic controls
```

Disallowed:

```text
rational phases operate in aligned MoO
the provenance walk is a runtime path or orbit
Q/Z is a ring under rational multiplication or division
a return excess proves circle geometry
failure of this aperture disproves every possible phase lens
```
