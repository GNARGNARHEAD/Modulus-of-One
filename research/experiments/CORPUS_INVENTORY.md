# Strict Corpus Inventory

> Historical inventory verified on 2026-08-28; current availability checked
> again on 2026-11-04 below.

## Current Availability: 2026-11-04

All five historical SQLite files listed in this inventory are now **absent at
their named paths in this checkout**. The historical byte sizes, hashes and
configuration records below remain provenance records, not present-availability
claims. Their retained JSON reports survive. No replacement has been generated
at a historical path, and a report's node/edge IDs cannot be imported as witnesses
in a different source corpus.

| Historical source under `out/experiments/` | Current local state |
| --- | --- |
| `pascal_edge_probe_u300.sqlite` | Absent |
| `pascal_cubic_scale_u1000.sqlite` | Absent |
| `circle_as_one_u40_wide.sqlite` | Absent |
| `circle_as_one_u80.sqlite` | Absent |
| `gauss/strict_stage_u850_holdout_v1.sqlite` | Absent |

The separately named current-generator calibration sources below are present.
Their live hashes match their retained calibration reports; they do not replace
the five historical inputs. The first two paths are relative to
`out/scratch/shell_composition_20260920_current_v1/`.

| Surviving source | SHA-256 |
| --- | --- |
| `wide_u576.sqlite` | `655e2ba49f53519e7cb3720ad8894579aaf113444afbe56b81a99ae7bbdae2b6` |
| `narrow_u80.sqlite` | `efccebea17d2ab95777b0e8480990d5b3f527eb94bcca68b13bd4ec438702df5` |
| `research/geometry/results/2026-10-01-square-area-inspection-v1/current_u160.sqlite` (repository-relative) | `8c31e7da4dc5d359df31b7fa18b195c14e6b190426c704a5c6d4f4bff7e11fb7` |

These are local ignored inputs, not a durable backup. The
[research-to-profile coverage map](../PROFILE_COVERAGE.md) records
which definitions can be re-audited and which results remain report-only.
Derived node-profile databases are indexes over a named source, not new source
corpora. The preservation contract continues to apply to every surviving input.

## Preservation Warning

These SQLite files are immutable research inputs. **Do not delete, overwrite,
vacuum, migrate, or regenerate them in place.** The repository intentionally
ignores `*.sqlite`, so an ordinary source commit does not preserve these blobs.
Before cleaning this workspace or moving to another machine, copy each corpus
to durable content-addressed storage and verify its byte size and SHA-256
against this inventory.

A replacement produced by different source code, arguments, SQLite behavior,
or environment is a new corpus and requires a new experiment identifier. It
must not silently take the path of an existing frozen input.

All five files below were present during the **2026-08-28** audit, opened successfully
through the read-only corpus interface, and passed the strict alignment audit
with zero speculative-input edges and zero non-core operand edges.

## `pascal_edge_probe_u300.sqlite`

```text
path: out/experiments/pascal_edge_probe_u300.sqlite
bytes: 37560320
sha256: 3d23228ea2a1926918d49bbdc89d9f7bf85ecfe4729ec96c7bd6e9f97e54b097
nodes: 78889
edges: 360001
```

Configuration: strict-stage positive spine through U300, with
`max_abs_p=1000000000`, `max_abs_q=300`, `max_abs_value=1000000000`, and
confirmed edges retained.

Durability: local-only ignored blob. Its hash is bound into the saved Euler and
Gauss reports that read it. No dedicated frozen generator-source manifest
accompanies this corpus, so exact byte-for-byte regeneration from the current
source tree has not been established. Preserve the existing blob.

## `pascal_cubic_scale_u1000.sqlite`

```text
path: out/experiments/pascal_cubic_scale_u1000.sqlite
bytes: 430129152
sha256: 1dcb1037ad05a2c91a9bfdbc848abc8b9a9ba626d032355264c0ac90c39dd472
nodes: 856601
edges: 4000001
```

Configuration: strict-stage positive spine through U1000, with
`max_abs_p=1000000000`, `max_abs_q=1000`, `max_abs_value=1000000000`, and
confirmed edges retained.

Durability: local-only ignored blob and the largest corpus in this inventory.
Its hash is bound into the saved U1000 finite-series report. No dedicated
frozen generator-source manifest accompanies it, so exact byte-for-byte
regeneration from the current source tree has not been established. Preserve
the existing blob.

## `circle_as_one_u40_wide.sqlite`

```text
path: out/experiments/circle_as_one_u40_wide.sqlite
bytes: 442368
sha256: 12d358def1827b217a603a6da1aa793aa3525eb28b135fd3991af1bbcdc279ad
nodes: 1019
edges: 4139
```

Configuration: strict-stage positive spine through U40, with `max_abs_p=200`,
`max_abs_q=200`, `max_abs_value=40`, and confirmed edges retained.

Durability: local-only ignored blob. Its hash is frozen in the U40 phase
transport analysis and in the Euler reports that read it. Those reports can be
re-evaluated while this exact corpus survives, but no dedicated frozen
generator-source manifest establishes exact corpus regeneration. Preserve the
existing blob.

## `circle_as_one_u80.sqlite`

```text
path: out/experiments/circle_as_one_u80.sqlite
bytes: 1052672
sha256: 796e043087eee8908c840d21f1c14235310c0093e816927bbab8374fbd0d4780
nodes: 3522
edges: 9559
```

Configuration: strict-stage positive spine through U80, with `max_abs_p=200`,
`max_abs_q=200`, `max_abs_value=4`, and confirmed edges retained.

Durability: local-only ignored blob. Its hash is frozen in the U80 phase
transport analysis and in multiple Euler reports. Those reports can be
re-evaluated while this exact corpus survives, but no dedicated frozen
generator-source manifest establishes exact corpus regeneration. Preserve the
existing blob.

## `strict_stage_u850_holdout_v1.sqlite`

```text
path: out/experiments/gauss/strict_stage_u850_holdout_v1.sqlite
bytes: 309338112
sha256: cf3d1dd7a67dbd6772647dac7c746e09267e6e4c3d888f53b05c6e4073565162
nodes: 619996
edges: 2890001
```

Configuration: strict-stage positive spine through U850, with
`max_abs_p=1000000000`, `max_abs_q=850`, `max_abs_value=1000000000`, and
confirmed edges retained. The recorded generation elapsed time is
`145.8106301999942` seconds.

Durability: local-only ignored frozen holdout. Its retained provenance and
summary sidecars bind this exact blob to the nested class/genus experiment.
Exact regeneration from current sources is not valid because both frozen
generator hashes differ from the current files:

```text
moo/graph_corpus.py
  frozen: 5f863dc297b3b2136fa76835d13067ae41206a150885dd37ba2bb49da5532c1f
  current: 87a7ef9b864100e44d0941903ef1b7d66ad2f13d05892c2ac1c00ca7e9619ece

moo/strict_stage_moo.py
  frozen: e91574e0df7c573ec6e36d56dfbe5c779da632108d631ec22b4d2196acfc099b
  current: 362175c960bc4d5e2c909a7c97ffcf7e2065a1ec75cec9b6c2f2c18a2044d0c3
```

The current generator may be used only for a newly identified corpus and
experiment. Preserve the existing U850 blob as the sole exact frozen holdout.

## Storage Contract

The five historical files totalled 778522624 bytes. No durable external retrieval location is
currently recorded here. Until one exists, local presence is not a backup.

A durable copy is acceptable only when it is immutable or content-addressed
and the retrieved bytes reproduce the SHA-256 above. Git LFS, an immutable
release asset, or another backed-up artifact store can satisfy that role. A
plain ignored copy elsewhere in this working tree cannot.
