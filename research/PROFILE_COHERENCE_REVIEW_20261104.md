# Node-Profile Coherence Review

Date: 2026-11-04

evidence_layer: external_probe
claim_status: observation

This review checks the connection between mathematical association, named
construction certificate, saved graph evidence, and the wording presented to
an inspector. It follows the [coverage map](PROFILE_COVERAGE.md) and the
[canonical claim boundary](../docs/CLAIMS.md). No test-suite result was used as
evidence. Source reading, explicit algebra, counterexamples, and independent
read-only SQL supplied the checks. This is not a reproof of every research
program or evidence that the chosen geometric families are intrinsic branches.

## Corrections Identified

### A constructed endpoint did not bind an advertised square root

The imported generic paired and left expansions construct `81` through the
inputs `7` and `2`, but their original target-construction schemas contain no
operation involving `9`. The profile adapter nevertheless used them as complete
certificates of the association connecting root `9` to square result `81`.

Classically, both expansions equal `(7+2)²=9²`. The missing part was a retained
binding of the advertised root to those inputs. This was visible by reading the
requests, even though every stored edge and numerical equality was correct.
The existing rational-square adapter already requests `p/q -> root`; the shell
expansions already retain `16+9 -> 25`. The generic adapter needed the same
construction standard.

The [corrected adapter](../moo/association_families.py) obtains `7+2 -> 9` from
the existing factored route and adds it as `binding:root_sum` when absent. It
records the source route and whether the adapter added the binding. That premise
is included in witness support and overlap but remains outside the imported AC
construction expression. The frozen
[target-construction definitions](strict_stage/route_identity/pascal_shell_calibration.py)
and their historical report remain unchanged.

The added request completes at U7, so the paired and left completion maxima
remain U53 and U77. The [binding control](geometry/results/2026-11-04-node-profiles-review/root_binding_control.json)
removes only that edge in a temporary source copy: the endpoint expansion can
remain supported while the root/result certificate becomes incomplete. The
[schema review](geometry/results/2026-11-04-node-profiles-review/binding_schema_review.json)
records the adapter-level binding check. Target equality alone is insufficient
as a general rule for importing construction-backed participant relationships.

This was a question about the imported recipe's claim, not a missing square
relationship in the node profile. The literal `9*9 -> 81` already supports that
relationship at U9. An incomplete alternative recipe neither removes this
support nor delays it. The profile needs one supported relationship record;
checking every recipe separately is optional deeper inspection. The
[profile note](../docs/software/NODE_PROFILES.md) now leads with those simple definitions,
and the default text view shows one line per relationship. Recipe details remain
available through `profile --details` and the certificate queries.

### Whole-source facts were mixed with checkpoint observations

In a U16 profile built from the saved U576 corpus, node `289` correctly had
`present:false`, yet its unqualified payload also exposed `first_stage:17`,
`first_edge_id:1092`, and `confirmed_stage:289`. The latter is a positive-spine
threshold, not an observed confirmation at U16. The source facts were useful,
but their scope was unclear inside a checkpoint-specific profile.

The [profile reader](../moo/node_profiles.py) now keeps the original record
under `saved_source_node`. Public arrival, identity, and confirmation fields
describe the selected checkpoint; unavailable observations are null.
`confirmation_threshold` is separately named as a schedule. The view conversion
also applies when reading old v1/v2 files, without migrating those snapshots.

The [graph-query attachment](../moo/graph_query.py) also needed two explicit
scopes. Its native neighborhoods cover the entire saved corpus, while the
attached association index may select an earlier checkpoint. `query_scope`
now names both views and their common source hash. It does not silently filter
the native graph query or call an incomplete saved frontier complete.
The [checkpoint records](geometry/results/2026-11-04-node-profiles-review/checkpoint_views.json)
retain the concrete before/after interpretation.

## What Broad Membership Can And Cannot Tell Us

Direct SQL over the v2 index found 809 indexed values, of which 780 participate
in square associations: approximately **96.4%**. There are 400 square-root roles;
with witnessed-only selection, 708 values participate in squares and 360 are
roots. These are catalogue counts, not statistics over the entire source graph.
The review corrections preserve the association and participant selection.

This breadth follows from the definition: every selected rational root is a
source of its own square association. In unrestricted positive rational shell
geometry, every positive rational `r` can be a radius through
`(3r/5,4r/5,r)`. Increasing bounds therefore does not make those broad tags
intrinsically discriminating. The useful question specifies a role, restricted
family, certificate, normalization, or clock.

The current witnessed intersection `3,4,5,7,24,25` is consequently a result of
the declared finite selection. It is not an unexpected correlation or evidence
that these values are special. Likewise, only roots `9` and `25` receive the
seven fixed imported routes. Their richer profiles reflect that encoding choice.
Certificate counts cannot rank intrinsic richness or independent support.

A `partial` status is weak by design. For example, every selected unit-shell
literal certificate includes `1*1=1`, so that shared request can make it partial
while all fractional-coordinate operations remain unavailable. Partial status
is not a progress percentage or a geometric-affinity measure.

## The Timing Examples Have Direct Explanations

For a positive integer shell `(x,y,r)`, the nine-request normalized-square
certificate includes divisions by `r²`. Since `x,y<r`, every other requested
operand is at most `r²`. In a complete positive-spine field with adequate
retention, its specified completion is therefore **U(r²)**. Scaling the source
by a positive integer `k` scales this threshold by `k²`. U25 versus U100 for
`(3,4,5)` and `(6,8,10)` is explained before measurement.

Similarly, the four-request rational-square encoding for positive reduced
`p/q` completes at `max(p²,q²)` under those assumptions. The retained requests
give `P=p²`, `Q=q²`, `x=p/q`, and `v=P/Q`; external algebra then establishes
`v=x²`. No fractional-input multiplication edge has been created.

The spiral identity is equally explicit:

```text
(4x-3y)² + (3x+4y)² = 25(x²+y²) = (5r)².
```

Its third local transition uses `28-72=-44`, `21+96=117`, and `25*5=125`,
with maximum requested operand 96. A negative output is permitted; reusing
`-44` as a later operand is blocked. This explains the U96 third step and
incomplete fourth lineage without a geometric exception.

These distinctions are useful construction information, not newly discovered
rhythms. The [area inspection](geometry/AREA_INSPECTION_BRANCH_20261001.analysis.md)
and [certificate note](strict_stage/PASCAL_SHELL_CERTIFICATE_NOTE.md) correctly
separate bundle availability from causal execution time and global optimality.

## One Supported Consequence Is Not Yet A Registered Shell Certificate

The [composition note](geometry/SHELL_COMPOSITION_BRANCH_NOTE.md) proves that
source-shell support plus retained scalar composition is an external algebraic
certificate of the target norm, even before a direct target-shell proof exists.
The profiles currently register that support under the spiral association.

Thus `-44` is a witnessed coordinate of spiral step 3 at U96, while the direct
shell association `(-44,117,125)` remains incomplete. This is a finite-criteria
coverage choice, not a failed norm identity. A later named composition-norm
certificate could connect the two associations. For now,
`find shell spiral --witnessed-only` means support through registered criteria;
it does not enumerate every supported mathematical consequence.

## Independent Evidence And Its Limit

The [independent SQL auditor](geometry/audit_node_profile_snapshot.py) uses
standard-library SQLite, exact fractions, hashing and JSON. It does not call
the profile selectors, `GraphEvidence`, profile support functions, or tests for
its truth lookup. The [v2 audit](geometry/results/2026-11-04-node-profiles-review/v2_independent_audit.json)
checked all 435 associations and 832 certificates, 1,241 distinct directed
requests, and the stored references, eligibility and completion summaries.
It found no mismatch in those recorded arithmetic/evidence fields.

That did **not** establish the missing root binding: a correct list of arithmetic
requests can still fail to support the relationship advertised above it. The
mathematical implication and scope arguments in this note are therefore separate
from the data audit. The [manual readback](geometry/results/2026-11-04-node-profiles-review/math_readback.json)
also checks independently specified example requests.

The [v3 audit](geometry/results/2026-11-04-node-profiles-review/v3_independent_audit.json)
and [current profile report](geometry/results/2026-11-04-node-profiles-v3/report.json)
record the reviewed implementation. Original corpora and prior reports remain
unchanged. Future extensions should improve a concrete comparison of roles,
routes, shared occurrences, or readiness; additional geometric names alone do
not establish explanatory or predictive value.

## Usefulness Inspection

The profiles are useful as an index from a constrained question to its supporting
constructions. Broad family overlap is weak; roles, the selected construction,
and the reason support is missing carry the information. This worked inspection
found no unexplained geometric law, but it exposed an alternative construction
that a sequential-only reading would miss.

The [profile report](geometry/results/2026-11-04-profile-inspection-v1/report.json)
uses three fresh indexes over the same unchanged U576 source, with square height
25, shell radius bound 25, and four selected power states. Only the seed changes.
The [independent SQL record](geometry/results/2026-11-04-profile-inspection-v1/independent_sql.json)
derives the arithmetic and looks up edges without importing profile or evidence
helpers. A [cross-readback](geometry/results/2026-11-04-profile-inspection-v1/cross_readback.json)
compares the two records. No test-suite result supplies the mathematical evidence.

### Orientation Separates Shape From Reusable Construction

Let `A_n` be powers of `(4,3,5)`, `B_n` powers of `(3,4,5)`, and `C_n` powers
of `(8,6,10)` under the existing ordered composition.

| Seed | Sequentially supported states and completion stages | First incomplete sequential step at U576 |
| --- | --- | --- |
| A: `(4,3,5)` | `(4,3,5)` U16; `(7,24,25)` U16; `(-44,117,125)` U96 | Step 4 would reuse `-44` |
| B: `(3,4,5)` | `(3,4,5)` U16; `(-7,24,25)` U16 | Step 3 would reuse `-7` |
| C: `(8,6,10)` | `(8,6,10)` U64; `(28,96,100)` U64 | Step 3 needs the positive operand `768`, beyond the saved checkpoint |

These stages describe the seed shell and linked scalar-transition bundles.
The seed and second state can both be supported at U16: iteration order is not
chronological graph execution. Scalar inputs may exist through other routes
before the preceding selected transition completes.

The shape comparison has an exact explanation. For external complex notation
`z=4+3i`, the swapped seed is `w=3+4i=i*conjugate(z)`, so
`w^n=i^n*conjugate(z^n)`. A and B therefore have the same radius and the same
unordered absolute coordinate pair at every n, including mathematically defined
states beyond the witnessed prefix. Their signed coordinate roles differ, which
changes when the selected recurrence would reuse a forbidden operand.

Scaling is equally explicit: `C_n=2^n A_n`, so their ordered unit-normalized
positions agree. C's third state is `(-352,936,1000)`. Its only missing local
request at U576 is `168+768 -> 936`; completion at U768 is an operand-readiness
prediction under the same adequate retention, not a recorded observation.
This is a checkpoint limitation, distinct from B's negative-input limitation.

### A Blocked Sequential Step Has Another Witnessed Construction

The most useful follow-up was to ask which earlier power states compose to the
same target. The inspection used the existing composition probe for every
ordered split `i+j=n`, for `2 <= n <= 4`, across the three seeds. It did not add
a special certificate to one node.

For A, the fourth state can be built from its second state twice:

```text
(7,24,25) o (7,24,25)
  = (49-576, 168+168, 625)
  = (-527,336,625).
```

All seven scalar requests are retained by U576. The three source self-products
are already among those seven requests; the retained sum `49+576 -> 625`
completes the direct source-shell bundle. Thus the existing `source_composition`
criterion is complete. The critical subtraction is edge `1324999` at U576;
the source-shell sum is edge `1324998` at U576, in the named U576 source.
The separately witnessed A2 lineage identifies the source as `z^2`, and the
external identity `(z^2)^2=z^4` identifies the target as A4. The
`source_composition` criterion itself uses the direct source-shell bundle.

The sequential A3-composed-with-A1 certificate remains incomplete, and the
direct target-shell certificate still requires the forbidden operand `-527`.
Those are different claims. The current profile's sequential status must not
be read as absence of every construction of that fourth-power state. This
concrete distinction is a reason to inspect a tag's witness references.

The source criterion also matters before a block: A3's linked lineage completes
at U96, while requiring the direct source shell `(7,24,25)` makes
`source_composition` wait until U576. There is no timing contradiction; the
two requests ask for different premises.

### Useful Queries And Misleading Readings

- `square:result spiral:radius` locates `25` and exposes a shared construction:
  `5*5 -> 25`, edge `84` at U5, supports the square and is reused in the spiral
  bundle, which completes at U16. The two tags are not independent evidence.
  Square radii at even iterations already follow from the chosen radius `5^n`.
- `shell:radius spiral:radius --by-stage 400` joins `25` across `(15,20,25)`
  and `(7,24,25)`. This is scalar reuse, not a matching configuration. The
  matching ordered target shell becomes directly supported at U576.
- `square:result square:root` gives connections such as `2 -> 4 -> 16 -> 256`.
  Its apparent end is a root-selection limit: the source also retains
  `256*256 -> 65536` at U256. The query does not discover a natural endpoint.
- The same query links `1/2 -> 1/4 -> 1/16 -> 1/256` through integer-ratio
  certificates at U4, U16 and U256. This is an encoded relationship chain;
  no fractional value has become a reusable operand.

Fixed raw selection bounds must also be kept in view when comparing scales.
The unfiltered square-radius query includes A4's `625`, but omits C4's `10000`
because the root `100` exceeds the selected square height 25. This says nothing
about a difference in their square-radius law. In the narrow U80 retention
control, even the literal seed-shell bundles are absent despite the coordinate
nodes being present. Missing support can therefore reflect selection, frontier,
retention, or a specific operand/route restriction.

### What Changed And How To Reproduce

The only new selector setting is `--spiral-seed X Y R`; it uses the existing
ordered composition definition and records the seed in the index. Default
association specifications were compared before and after and are identical.
Structured role-search output now states that sharing a scalar does not identify
a shared configuration or dependency. No new family definitions or per-node
exceptions were introduced. Alternative split constructions remain inspectable
in this report rather than silently replacing the selected sequential criterion.

The existing independent snapshot auditor checked each new index; the separate
SQL derivation agreed on all ten sequential states through the first incomplete
steps and all eighteen ordered composition splits. Source corpora and old
indexes retained their hashes. These checks corroborate the records; the
identities and interpretation above supply the mathematical argument.

Run from the repository root, choosing unused output paths:

```sh
python3 -B research/geometry/node_profile_inspection.py \
  --db out/scratch/shell_composition_20260920_current_v1/wide_u576.sqlite \
  --index-dir out/scratch/node_profile_inspection_recheck \
  --write /tmp/moo-profile-inspection-recheck.json

python3 -B research/geometry/inspect_profile_controls_sql.py \
  --write /tmp/moo-profile-controls-recheck.json
```
