# Shell composition: witnessed construction and later output proof

Date: 2026-09-20

evidence_layer: strict (new current-generator fields); external_probe (algebra)
claim_status: observation
result_status: completed_version

## Outcome

The [candidate definition](SHELL_COMPOSITION_BRANCH_NOTE.md) is now precise
enough to distinguish a retained composition from a retained direct proof of
its output shell. In the new wide field,

    (4,3,5) o (4,3,5) = (7,24,25)

has its two source-shell bundles and composition by U16. Its direct target
shell bundle first completes at U576. The target square-sum must wait for 576
to become an eligible operand. This is an exactly explained readiness gap,
not an unexplained timing effect.

At U576, five of the eight fixed cases have source_composition witnesses, and
one has full_closure. There is a repeated source/composition motif, but only
one fully witnessed closure instance in this small selection. No general
closure or privileged-circle claim follows.

The signed and axis cases construct their negative/zero outputs but cannot
reuse them in the literal target-shell or normalization operations. Inverse
and identity actions remain blocked in the literal signed/zero-input schema.
These results expose the current field boundary without changing its rules.

## Historical inputs were unavailable

The [original frozen design](SHELL_COMPOSITION_20260920.pre.md) named three
historical SQLite inputs. Those files are absent from this checkout; a search
including ignored files found no SQLite corpus before this work generated its
new fields. Historical JSON reports and provenance sidecars are present, but
were not substituted for direct database measurements of the new predicate.

The original run stopped at its first file-open and produced no measurements
or report. The [input-availability amendment](SHELL_COMPOSITION_20260920.amendment.md)
was then written before generating the new inputs. It preserves every fixed
case, prediction, and witness predicate and assigns the separate experiment
ID `shell_composition_20260920_current_v1`.

This is a current-generator calibration, not reproduction of the historical
U300/U850/U80 blobs or an independent holdout validation. No historical corpus
path was populated or overwritten. The core runtime and generator are unchanged.

## Retained artifacts and new inputs

- [Manifest](results/2026-09-20-shell-composition-current-manifest-v1.json):
  generator hashes, settings, generation summaries, input paths/hashes, and
  checkpoint roles.
- [Exact report](results/2026-09-20-shell-composition-current-v1.json):
  requested operations, all matching occurrence records, node records and
  checkpoint status, motif membership, blockers, and predictions.
- [Read-only probe](../../moo_shell_composition_probe.py).
- [Focused tests](../../test_moo_shell_composition_probe.py).

The two new inputs live under
`out/scratch/shell_composition_20260920_current_v1/`:

| Input | Nodes | Edges | Bytes | Scope |
| --- | ---: | ---: | ---: | --- |
| wide_u576.sqlite | 286,590 | 1,327,105 | 140,918,784 | Wide retention, inspected at U16/U144/U300/U576 |
| narrow_u80.sqlite | 3,522 | 9,559 | 1,052,672 | Current narrow-retention control |

Wide settings are max_abs_p=10^9, max_abs_q=576, max_abs_value=10^9.
Narrow settings are max_abs_p=200, max_abs_q=200, max_abs_value=4.
Both retain confirmed edges and use no edge/time cutoff. Both pass strict
alignment with zero speculative-input and non-core-operand edges. All
before/after read-only input hashes match.

These are disposable current-generator calibration inputs. The manifest
preserves enough information to rebuild an equivalent field under a new
input identity; byte-identical regeneration is not claimed. The exact report
retains the selected witness records if the scratch inputs are later removed.

## Fixed-case results at U576

| Case | Literal composition | Sources + composition | Direct target shell | Full closure |
| --- | --- | --- | --- | --- |
| positive_double | U16 | U16 | U576 | U576 |
| positive_mixed | U48 | U144 | Beyond aperture: U3136 predicted | Incomplete |
| signed_output | U16 | U16 | Negative operand blocked | Incomplete |
| axis_output | U16 | U16 | Zero operand blocked | Incomplete |
| inverse_input | Signed operands blocked | Blocked | Zero operand blocked | Incomplete |
| identity_input | Zero operands blocked | Blocked | U16 | Incomplete |
| scaled_double | U64 | U64 | Beyond aperture: U9216 predicted | Incomplete |
| non_shell_control | U16 | Source equality false | Target equality false | Rejected |

U3136 and U9216 are arithmetic predictions, not observations. At U576 the
non-shell control has every requested edge, including both direct shell
bundles and the composition; it is rejected because the indicated nodes do
not agree. Its left discrepancy is -11 and its target discrepancy is -275.
This rules out an accidental predicate that accepts operation presence alone.

The identity case has a valid direct target (4,3,5) even though its source and
composition are blocked. Target membership alone therefore cannot establish
the particular composition history either.

## Concrete edge evidence

For positive_double, these records belong to the new wide input:

| Request | Edge ID | Stage |
| --- | ---: | ---: |
| 4*4 -> 16 | 52 | U4 |
| 3*3 -> 9 | 28 | U3 |
| 4*3 -> 12 | 48 | U4 |
| 3*4 -> 12 | 64 | U4 |
| 16-9 -> 7 | 935 | U16 |
| 12+12 -> 24 | 530 | U12 |
| 5*5 -> 25 | 84 | U5 |
| 16+9 -> 25 | 934 | U16 |
| 7*7 -> 49 | 172 | U7 |
| 24*24 -> 576 | 2,212 | U24 |
| 25*25 -> 625 | 2,404 | U25 |
| 49+576 -> 625 | 1,324,998 | U576 |

The value 16 is produced at U4 but cannot be reused until U16. Similarly,
576 is produced at U24 but cannot enter the last addition until U576. The
result 625 can remain speculative when the two target routes agree; comparing
outputs is not reuse as an operand.

The two ordered products 4*3 and 3*4 share value 12 but retain different edge
IDs. The matching composition uses those named roles, not a substituted
commutative lookup.

For the orientation controls, `9-16 -> -7` is edge 999 at U16 and
`12-12 -> 0` is edge 531 at U12. These are real retained outputs. No
`(-7)*(-7)` or `0*0` operation is licensed in this field.

The scaled and unscaled compositions both normalize to (7/25,24/25).
For example, `7/25 -> 7/25` is division edge 2,433 at U25, while
`28/100 -> 7/25` is division edge 39,717 at U100. The same observation retains
different division witnesses and different source-composition readiness
(U16 versus U64).

## Checkpoints, retention, and baseline

| Checkpoint | Complete compositions | Complete source_composition | Complete full_closure |
| --- | ---: | ---: | ---: |
| Wide U16 | 4 | 3 | 0 |
| Wide U144 | 6 | 5 | 0 |
| Wide U300 | 6 | 5 | 0 |
| Wide U576 | 6 | 5 | 1 |
| Narrow U80 | 0 | 0 | 0 |

The composition-only counts include the non-shell control. No such count is
a count of circles. Likewise, normalization may be available for a non-shell
triple; division by its radius does not prove unit norm.

Across all four wide checkpoints and all seven reported motif predicates,
the registered operand-readiness baseline has zero mismatches, including its
agreement and prohibited-operand conditions. This is a deterministic check
over selected overlapping cases, not a significance estimate.

The narrow U80 field instead lacks required retained edges even where the
component values exist. It has no complete direct source-shell bundle for
these cases and no complete composition. Four target normalizations are
nevertheless complete. Its wide-retention prediction mismatches are expected
control outcomes and must not be interpreted as anomalous timing.

Summary `partial` means an incomplete motif with some retained requested
events; consult agreement and missing_roles to distinguish incomplete edge
coverage from a fully populated but false equality.

## Verification and reproduction

Nine focused stdlib tests pass. They include deleted witnesses with surviving
values/alternate routes, a nonhit with every operation present, signed/zero
blockers, future edges and confirmation, duplicate retained occurrences,
shared roles, narrow retention, and invalid saved confirmation metadata.

An independent coordinate enumeration through integer radius 25 yields 36
distinct rational shell positions. All recover through the parameter inverse,
including (-1,0). The finite homogeneous composition check compares 9,216
parameter-pair products exactly. These are implementation checks; the general
proofs are in the candidate definition.

An independent raw-SQL readback checked 214 checkpoint references representing
73 distinct input/edge records, their exact arithmetic, node identities,
confirmation stages, and checkpoint eligibility. Tool/helper, design,
amendment, and manifest hashes match the report. The report SHA-256 is
`6398fb7ac10871f32417a76a69000fe7474b0afdfd25eb58fd76f895240eb350`.

Run the tests:

```sh
python3 -B -m unittest test_moo_shell_composition_probe -v
```

With the new scratch inputs still present, rerun to a fresh report filename:

```sh
python3 -B moo_shell_composition_probe.py \
  --current-fixtures-manifest research/geometry/results/2026-09-20-shell-composition-current-manifest-v1.json \
  --write out/scratch/shell-composition-rerun.json
```

Inspect a target neighborhood:

```sh
python3 -B moo_graph_query.py \
  --db out/scratch/shell_composition_20260920_current_v1/wide_u576.sqlite \
  --node 625 --neighborhood --pretty
```

Without the explicit current-fixture manifest, the tool targets the original
historical paths and refuses to substitute another input. If scratch inputs
are removed, use the manifest's generator settings with `strict_stage_moo.py`
under new filenames and record a new manifest/input identity. Do not overwrite
the existing report, manifest, or any historical corpus path.

## Disposition

The fixed calibration is complete. The formalized schema and exact witnesses
are useful; a new timing law is not supported. General graph closure and a
reason for MoO to privilege the two-square composition remain open. Extending
signed operand rules, admitting completion, and introducing measure remain
separate decisions. No larger residual search is warranted by this result.
