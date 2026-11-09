# Zeta Cancellation Arrival: U80 Narrow / U300 Broad

## Outcome

At the caller-supplied coordinate

```text
s = 0.5 + 14.134725141734693 i
```

the admissible strict-stage reveal is unusually orderly, but it is not
graph-specific. In both saved corpora, source confirmation and the first direct
`1/n` witness occur at stage `n`. The operational trajectory is therefore the
ordinary finite source prefix `1,2,...,64`, and the two reports reproduce it
exactly.

The graph-specific contrast points the other way. The U300 aperture makes all
64 integer sources speculatively visible by stage 31, but that graph-shaped
presence order is much less radially orderly and is ordinary under its own
block-permutation null. Because those nodes are not yet confirmed operands, the
presence path is inspection evidence only.

The surviving claim is narrow:

> The natural positive-spine source order gives unusually monotone external
> finite cancellation at this caller-supplied reference coordinate.

This is not a graph construction, discovery, or certification of a zeta zero,
and it is not evidence for the Riemann hypothesis.

## Saved evidence

- `zeta_arrival_first_zero_u80_v1.json`
- `zeta_arrival_first_zero_u300_broad_v1.json`

Both reports use a fixed `K=64` Hasse/eta source basis, stage horizon 64,
binary64 complex evaluation, four local controls, ten height controls, and
4,096 deterministic permutations for each adjacent block size 2 and 4.

The coordinate is caller supplied and is not independently verified by this
probe. The configured-v1 thresholds and null design were fixed after
exploratory calibration; they were not preregistered.

## Corpus and schedule audit

The probe validates every strict stage through U64 before interpretation:

- stages are contiguous;
- candidate events equal `8*u-4`;
- retained events, new edges, and recorded non-seed edges agree;
- cumulative node and edge totals reproduce the stage table;
- the corpus generator is `strict_stage_moo_graph`.

| U64 evidence | U80 narrow aperture | U300 broad aperture |
|---|---:|---:|
| nodes | 2,270 | 3,795 |
| edges including the seed | 6,224 | 16,385 |
| sources present before confirmation | 3 | 63 |
| maximum speculative lead | 2 stages | 56 stages |
| all 64 source nodes visible | U64 | U31 |
| source readiness schedule | `n` | `n` |
| direct `1/n` witness schedule | `n` | `n` |
| operational completion | U64 | U64 |

The aligned schedule equality is complete rather than a `None == None`
censoring artifact: all 64 readiness/direct-witness pairs are observed and
equal. For `n>1`, the reciprocal result node `1/n` remains non-operand-ready;
the edge is evidence for the external reveal gate, not permission to operate on
that reciprocal in the graph runtime.

The first-witness topology does differ. In the narrow corpus, sources 2, 3, and
4 have earlier independent constructions, while sources 5 through 64 first
record a self-return such as `n * 1 -> n` at confirmation. In the broad corpus,
sources 2 through 64 have first witnesses that do not use the result as an
operand. That structural difference changes speculative visibility, but not the
admissible operational order.

Reciprocal reinforcement follows the divisor ladder `n,2n,...` through U64 in
both reports. It annotates the source and never multiplies the corresponding
analytic contribution.

## Operational cancellation trajectory

The U80 and U300 operational trajectory rows are value-for-value identical.

| measure | result |
|---|---:|
| finite residual `abs(zeta_K(s))` | `2.1570095574950392e-15` |
| radial normalization scale | `4.179028106390261` |
| peak stage | 2 |
| peak normalized radius | `0.16920364333163784` |
| resolved post-peak changes | 56 |
| resolved inward / outward | 56 / 0 |
| longest resolved inward streak | 56 |
| post-peak radial efficiency | `0.9999999999999997` |
| persistent radius below `1e-2` | U25 |
| persistent radius below `1e-3` | U37 |
| persistent radius below `1e-4` | U41 |
| persistently below every local control | U37 |
| local-control separation at least 10x / 100x / 1000x | U40 / U44 / U46 |

The two final cutoff changes are `3.3822620033034757e-13` and
`2.3149187697142205e-14`, both within the configured empirical stability check.
The operational terminal sum reconstructs the finite Hasse endpoint exactly in
binary64 under the normalized guard.

All four local controls are visibly less orderly:

| local control | longest streak | inward fraction | radial efficiency | irreversible envelope exit |
|---|---:|---:|---:|---:|
| lower sigma | 8 | `0.6250` | `0.7883` | U38 |
| upper sigma | 9 | `0.5893` | `0.7866` | U38 |
| lower t | 8 | `0.5714` | `0.7975` | U39 |
| upper t | 7 | `0.6250` | `0.7876` | U38 |

The target stays inside the remaining-L1 cancellation envelope at every stage.
That condition is necessary, not sufficient. Tail-to-endpoint capture differs
from the local controls by at most one stage and is therefore attributed to the
fixed Hasse amplitude envelope, not to zero-specific choreography.

## Endpoint-preserving nulls

Every prefix and endpoint is accumulated with separate real/imaginary
`math.fsum`. Across every saved permutation, the terminal binary64 endpoint is
exactly the canonical endpoint.

For the admissible natural order:

| null | natural streak | null maximum | null samples at least as extreme | add-one tail |
|---|---:|---:|---:|---:|
| adjacent blocks of 2 | 56 | 35 | 0 / 4,096 | `1/4097` |
| adjacent blocks of 4 | 56 | 24 | 0 / 4,096 | `1/4097` |

No permutation matches the natural inward fraction or radial efficiency either.
The add-one fraction is an exploratory deterministic rank, not a formal p-value.

The broad speculative-presence order provides the important negative control:

- completion at U31;
- longest inward streak 11;
- 18 inward and 4 outward resolved changes;
- inward fraction `0.8181818181818182`;
- radial efficiency `0.7577775441318392`;
- block-size-2 null maximum streak 17;
- 900 of 4,096 null samples at least as extreme;
- add-one upper-tail fraction `901/4097 = 0.21991701244813278`.

So the aperture-rich graph order does reveal the endpoint earlier, but it does
not reveal it more monotonically. Its apparent earlier control separation is
also inadmissible because it depends on unconfirmed source nodes.

The narrow speculative-presence contrast is nearly the natural order: only
sources 2, 3, and 4 arrive early. Its streak is 55 and it remains extreme under
the same null. This is consistent with a small perturbation of the ordinary
prefix, not with a new topology-driven ordering principle.

## Interpretation boundary

What the experiment supports:

- a reproducible fixed-finite cancellation trajectory conditioned on graph
  arrival evidence;
- an unusually monotone natural source order at the supplied coordinate;
- a clear separation between admissible readiness and speculative visibility;
- a negative graph-specific result: added construction topology does not supply
  the monotone order.

What it does not support:

- treating `source_node_present` as operand availability;
- calling `P_u` a stage-`u` zeta approximation;
- calling the natural `n` prefix graph-unique;
- multiplying a term by its reciprocal witness count;
- zero discovery, zero certification, or an RH claim.

## Reproduction

```sh
python3 moo_zeta_arrival_probe.py \
  --db out/experiments/circle_as_one_u80.sqlite \
  --sigma 0.5 --t 14.134725141734693 \
  --hasse-terms 64 --stage-horizon 64 \
  --control-delta 0.01 \
  --height-control-ts 10,11,12,13,15,16,17,18,19,20 \
  --envelope-guard 1e-12 --stability-tolerance 1e-12 \
  --near-zero-tolerance 1e-10 --permutation-samples 4096 \
  --target-kind user_supplied_reference_zero \
  --target-label first_nontrivial_zero_coordinate --full-scan \
  --write out/experiments/euler/zeta_arrival_first_zero_u80_v1.json --pretty

python3 moo_zeta_arrival_probe.py \
  --db out/experiments/pascal_edge_probe_u300.sqlite \
  --sigma 0.5 --t 14.134725141734693 \
  --hasse-terms 64 --stage-horizon 64 \
  --control-delta 0.01 \
  --height-control-ts 10,11,12,13,15,16,17,18,19,20 \
  --envelope-guard 1e-12 --stability-tolerance 1e-12 \
  --near-zero-tolerance 1e-10 --permutation-samples 4096 \
  --target-kind user_supplied_reference_zero \
  --target-label first_nontrivial_zero_coordinate --full-scan \
  --write out/experiments/euler/zeta_arrival_first_zero_u300_broad_v1.json --pretty
```
