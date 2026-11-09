# Node Association Profiles

Date: 2026-11-04

evidence_layer: external_probe
claim_status: observation

Graph support is audited through checkpoint-scoped strict witnesses.

Node profiles show the relationships a value participates in, its role in each,
and the earliest recorded support among the selected constructions. Each
relationship is stored once and shared by its participants' profiles.

The starting definitions are small:

- A square relationship connects `a` and `b` through `a*a = b`.
- A shell relationship connects `(x,y,r)` through `x*x + y*y = r*r`.
- The selected spiral starts at an integer shell `(a,b,s)`, `s>0`, and repeats
  `(x,y,r) -> (a*x-b*y, b*x+a*y, s*r)`. The default seed is `(4,3,5)`.

These arithmetic definitions identify the relationships to inspect. Recorded
operations establish their construction support; integer encodings remain
distinguished from literal fractional operations. Shapes and family membership
remain external interpretations, within [docs/CLAIMS.md](../CLAIMS.md).

One complete supporting construction is enough. For example, `9*9 -> 81`
supports the square relationship between `9` and `81`; another recipe reaching
`81` does not have to establish that relationship again for the profile to keep
it. Alternative recipes are evidence to inspect, not additional definitions or
tags. Their individual completion times do not reset the relationship's first
support. The default view shows each relationship once; recipe comparison is
optional detail.

The implementation is [moo/node_profiles.py](../../moo/node_profiles.py), with exact
[family selectors](../../moo/association_families.py), the shared
[evidence reader](../../moo/graph_evidence.py), and
[certificate comparison](../../moo/profile_certificates.py). The
[research coverage map](../../research/PROFILE_COVERAGE.md) distinguishes what is
integrated from broader research that remains mapped for later inspection.
The [coherence review](../../research/PROFILE_COHERENCE_REVIEW_20261104.md) records
the direct mathematical/SQL review, two corrections, and remaining limits.
Its [worked inspection](../../research/PROFILE_COHERENCE_REVIEW_20261104.md#usefulness-inspection)
compares orientation, scale, and alternative compositions to assess what the
profiles actually help reveal.

## Bounded Selection

| Family | Default selection | Participant roles |
| --- | --- | --- |
| Square | Distinct nonnegative rational roots `p/q`, `0 <= p <= 25`, `1 <= q <= 25` | Root and square result |
| Shell | Ordered positive integer triples `x*x+y*y=r*r`, `r <= 25`; their unit-radius normalizations; selected spiral triples and their normalizations | Coordinates, radius, and their three squares |
| Spiral | Steps 1 through 5 of one selected pair product; default `(4+3i)^n`, radius `5^n` | Current and preceding coordinates and radius |

The defaults select 400 square associations, 30 shells and 5 spiral steps.
Shell leg orientations and raw scales stay distinct. Identical normalized
ordered triples share an association with separate source certificates. Signed
and out-of-radius shells enter only through the selected spiral. This is neither
exhaustive rational-shell coverage nor automatic spiral discovery.

## Membership And Named Certificates

Mathematical membership is exact and separate from graph support. A certificate
is `witnessed` only when all its requests and named certificate dependencies are
supported at the checkpoint; `partial` means some support, and `unwitnessed`
means none. An association is `witnessed` when at least one named certificate is
complete. Alternative certificates never fill each other's missing requests.
Inspect the certificate criterion before interpreting that aggregate status.

- `literal` retains the original self-product or direct shell square-sum test.
- `integer_ratio` encodes a positive noninteger rational square through four
  integer requests: `p*p`, `q*q`, `p/q`, and `p²/q²`. It does not supply a literal
  `(p/q)*(p/q)` edge.
- `normalize:a,b,c` retains the full nine-request normalized-shell encoding:
  three self-products, the square sum, two coordinate ratios, and three ratios
  for the squared coordinates and normalized sum. Each selected positive
  integer source scale has its own certificate.
- Seven fixed `route:*` certificates for `square:25` and `square:9` reuse the
  existing [Pascal-shell/generic definitions](../../research/strict_stage/route_identity/pascal_shell_calibration.py).
  They attach only when those associations are selected. All construction
  requests and premise steps are retained. The adapter also requires the root
  sum from the matching factored route; the two generic expansions add
  `7+2 -> 9` as an explicit association-binding premise. Optional associative/commutative (AC)
  expression metadata covers construction steps only; premises remain audited.
- Spiral support retains its seed and preceding-step lineage. A later direct
  target-shell proof is a separate certificate question.

`first_supported_stage` is the completion of that named certificate, or the
earliest complete selected certificate for an association. It is not a minimum
over every possible proof. The reader checks eligibility and retention, and
filters stored edge references and node visibility by the selected checkpoint.
`GraphEvidence` stored-edge presence alone is not an earlier-checkpoint witness.

No match means no match in this bounded selection and filter, not mathematical
nonmembership. `find square` includes both roots and squared results: `3` and
`9` share `3*3=9`. It does not test only whether a value is a perfect square.
Profiles name participant roles; `compare` reports common families, roles and
instances. These intersections are not statistical correlation measures.

## Inspect A Tag With A Constraint

Use a tag to select relationships, then constrain the role or stage to ask a
specific question. `find` accepts `family:role` selectors and requires every
selector to match the same value. It returns the matching relationship references
so the selection can be traced back to its construction evidence.

For example, using the index path below:

```sh
# Where can a square result serve as the root of another square?
python3 -B -m moo.node_profiles find --index "$profile_index" \
  square:result square:root --witnessed-only

# Which square results are spiral radii by U16?
python3 -B -m moo.node_profiles find --index "$profile_index" \
  square:result spiral:radius --by-stage 16
```

The first selection provides connections to follow, including `2 -> 4 -> 16 ->
256` in the saved U576 index. The second returns `25`, with square support at U5
and spiral-radius support at U16; changing the cutoff to U15 returns no match.
That comparison exposes the timing of two relationships involving the same
node. It does not establish a statistical correlation or an unexplained law.

Square roles are `root` and `result`. Shell roles are `x`, `y`, `radius`,
`x_square`, `y_square`, and `radius_square`. Spiral roles are `x`, `y`, `radius`,
`previous_x`, `previous_y`, and `previous_radius`. Omitting a role includes all
roles in that family. `--by-stage` requires witnessed support for every selector
and cannot exceed the saved checkpoint. `--json` includes all matching records.
These constraints reuse existing relationships; their combinations are queries,
not additional tag definitions. A selection boundary is not a branch endpoint.

Shared scalar values need not belong to the same configuration. At U400,
`shell:radius spiral:radius` matches `25` through shell `(15,20,25)` and spiral
state `(7,24,25)`. The latter's direct shell certificate completes at U576.
Inspect the returned association references before comparing their stages.
Likewise, root/result intersections can link integer-encoded rational squares;
that does not make fractional values reusable operands in the source graph.

## Use

### A Fresh Small Example

A fresh checkout does not include the local U576 database used by the larger
example below. To inspect profiles without that source, generate a new U80
field and index it:

```sh
python3 -m moo.strict_stage_moo \
  --db out/scratch/node_profiles_small_v1/field.sqlite \
  --max-stage 80 --max-abs-p 6400 --max-abs-q 80 --max-abs-value 6400 --quiet
python3 -m moo.node_profiles build \
  --db out/scratch/node_profiles_small_v1/field.sqlite \
  --index out/scratch/node_profiles_small_v1/associations.sqlite
python3 -m moo.node_profiles profile \
  --index out/scratch/node_profiles_small_v1/associations.sqlite 3 9 25 9/25
```

These bounds retain the full four-operation field on `1..80`. Relationships
that require later stages will appear incomplete or unsupported at this
checkpoint. This is a new example, not a reproduction of a saved U576 report.
Choose a new scratch suffix if either output already exists.

### The Larger Local Calibration

Run from the repository root. This build reads the existing U576 calibration
and refuses to overwrite an index. Choose a new output path for another build.
For the saved reviewed v3 run, set `profile_index` instead to
`out/scratch/node_profiles_20261104_reviewed/associations.sqlite` and skip build.

```sh
profile_index=out/scratch/node_profiles_demo_v3/associations.sqlite
python3 -B -m moo.node_profiles build \
  --db out/scratch/shell_composition_20260920_current_v1/wide_u576.sqlite \
  --index "$profile_index"

python3 -B -m moo.node_profiles profile --index "$profile_index" 3 9 25 625 9/25 -44
python3 -B -m moo.node_profiles profile --index "$profile_index" --json --details 9/25
python3 -B -m moo.node_profiles compare --index "$profile_index" --witnessed-only 3 9
python3 -B -m moo.node_profiles find --index "$profile_index" --witnessed-only square shell spiral
python3 -B -m moo.node_profiles association --index "$profile_index" 'shell:3/5,4/5,1'
python3 -B -m moo.node_profiles certificate --index "$profile_index" 'square:3/5#integer_ratio'
python3 -B -m moo.node_profiles compare-certificates --index "$profile_index" \
  'square:3/5#integer_ratio' 'shell:3/5,4/5,1#normalize:3,4,5'
python3 -B -m moo.node_profiles compare-certificates --index "$profile_index" \
  'shell:3/5,4/5,1#normalize:3,4,5' 'shell:3/5,4/5,1#normalize:6,8,10'
python3 -B -m moo.node_profiles compare-certificates --index "$profile_index" \
  'square:25#route:shell_expanded_paired' 'square:25#route:shell_expanded_left'

python3 -B -m moo.graph_query \
  --db out/scratch/shell_composition_20260920_current_v1/wide_u576.sqlite \
  --node 25 --associations "$profile_index" --pretty
```

Profiles show one line per relationship by default. `profile --details` adds
the supporting and incomplete construction certificates; `--json --details`
includes exact request records and edge references.
`--family square|shell|spiral` filters a profile.
Build options `--square-height`, `--max-radius`, `--spiral-steps` and `--stage`
fix selection and checkpoint. `--spiral-seed X Y R` changes the ordered seed
within the same composition family; it must satisfy `X*X+Y*Y=R*R` with `R>0`.
The chosen seed is recorded in the index scope. Signed or zero coordinates do
not gain operand eligibility. Existing indexes keep their saved selection.
The graph inspector also accepts `--associations`
with `--compare`, and verifies the source hash.
Its `query_scope` labels the full saved-corpus neighborhood separately from
the association checkpoint; attaching a profile does not filter the native
graph query to that stage.

`compare-certificates` expands named dependencies and compares directed requests
and retained edge occurrences separately, preserving repeated role links.
Matching supplied AC metadata does not merge certificates or premises. Empty
overlap does not establish independence, and shared edges are not independent
confirmations. Occurrence coverage is explicit; truncated references cannot
establish equal edge sets. The comparison performs no graph-wide proof search.

## Snapshots And Observations

Each index stores its source hash, rule-source hashes, bounds and checkpoint.
Standalone queries read that snapshot without silently refreshing it. Existing
corpora remain unchanged. Sources with a nonempty SQLite write-ahead log are
rejected because the main-file hash would omit updates; use a closed,
checkpointed artifact. The inspector never checkpoints the source itself.
Public node fields describe the selected checkpoint. `saved_source_node`
retains the original whole-source record; `confirmation_threshold` states the
positive-spine schedule, while public `confirmed_stage` is null until that
threshold is reached. This view correction also applies when reading older
indexes, without modifying their stored rows.

The [v1 report](../../research/geometry/results/2026-11-04-node-profiles-v1/report.json)
is retained as the initial single-criterion snapshot; older indexes remain readable.
The [v2 report](../../research/geometry/results/2026-11-04-node-profiles-v2/report.json)
records the initial named-certificate extension. Its two generic expansions
omit the root-binding sum, so it remains a historical record of the pre-review
criterion. The [v3 report](../../research/geometry/results/2026-11-04-node-profiles-v3/report.json)
contains the corrected bindings and explicit node scopes. After building a
current default U576 index, the [calibration script](../../research/geometry/node_profile_calibration.py)
checks source/rule hashes, named stages and selected materialized edge records
by direct SQL readback. It writes a new report and refuses overwrite:

```sh
python3 -B research/geometry/node_profile_calibration.py \
  --db out/scratch/shell_composition_20260920_current_v1/wide_u576.sqlite \
  --index "$profile_index" --write /tmp/moo-node-profiles-v3-recheck.json
```

The existing U576 calibration supplies these useful distinctions:

| Association or node | Named support and interpretation |
| --- | --- |
| `square:3/5` | Literal fractional self-product blocked; `integer_ratio` complete at U25. Thus `9/25` has a witnessed encoding without becoming an eligible operand. |
| `shell:3/5,4/5,1` | Normalization from `(3,4,5)` completes at U25; from `(6,8,10)` at U100. Equal normalized values retain different source routes. |
| `square:25`, target `625` | Literal and fixed factored route at U25; paired expansion U337; left expansion U544; composed norm U576. Same target and some equal AC expressions do not imply equal availability. |
| `25` | Square result of `5` at U5, spiral step-2 radius at U16, and radius of `(7,24,25)` with direct shell proof at U576. |
| `-44` | Spiral step-3 coordinate with linked support at U96; direct shell proof and its reuse as a step-4 operand remain blocked. |

The `3/5` square encoding shares all four directed requests and observed edges
with the normalization from `(3,4,5)`. This identifies their common construction
evidence; the two association labels do not constitute independent support.

These expose alternative certificates and their boundaries. They establish no
new geometric or timing law. Broad family participation is weakly selective:
780 of the 809 indexed values participate in the square family, including
sources. The normalized-shell completion at U25 versus U100 follows from the
required divisor `r²`; it is not an additional timing effect. Roles, certificate
criteria and restricted families carry the useful comparison information.
Focused contracts are
[family-selector tests](../../tests/test_moo_association_families.py),
[profile tests](../../tests/test_moo_node_profiles.py), and
[certificate-comparison tests](../../tests/test_moo_profile_certificates.py).
