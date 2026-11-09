# Archive

> Status: historical and mixed-status evidence map.

The archive preserves older exploratory closure notes, transitional ledgers,
working logs, and misalignment audits. These files are not deleted because they
contain useful leads and project history, but they are not current strict-stage
Modulus of One evidence unless a result is reproduced through a strict graph query.

Recovery provenance for the August 2026 restoration is recorded in
[AUGUST_2026_RESTORATION_AUDIT.md](recovery/AUGUST_2026_RESTORATION_AUDIT.md).

## Areas

- `exploratory_closure/`: bounded closure-era studies that reused speculative
  values as operands. Read as hypothesis generation, not aligned Modulus of One
  computation. The current disposition and strict-reproduction gate for the
  motif/hinge subset are owned by
  [[README.md](../research/motif_hinge/README.md)](../research/motif_hinge/README.md).
- `transitional_strict_ledgers/`: strict-stage summaries that predate the
  graph-first SQLite corpus path.
- `misalignment/`: audits of old language and interpretation drift.
- `working_logs/`: pause-point notes and operational planning records.
- `source_conversations/`: original conversation transcripts preserved locally
  byte-for-byte and omitted from the public snapshot. Their
  exploratory claims and unresolved tool citations are
  historical context; current claims belong in the maintained research notes.
  The Qwen-titled transcript was moved here on 2026-11-06. The former root
  pointer was consolidated into this availability notice on 2026-11-07. Its 256,826 bytes retain the restoration
  audit's SHA-256 `c22b0d26c2f0a5afb1833e39b2f7c5c702327ac2d4d321ec0fd51a3949801027`.
- `completed_external_calibrations/`: compact results and provenance records
  for careful external probes. A versioned run may finish with a calibration,
  rejection, or negative graph-specific result without retiring its maintained
  instrument or every broader question it can test. The primary research notes
  govern current lifecycle; these archive records preserve methods,
  measurements, hashes, and claim boundaries.
- `recovery/`: checksum-bound records of restoration sources, restored
  surfaces, and post-recovery verification.
- `superseded_maps/`: checksum-verified snapshots of detailed navigation files
  preserved before their active front doors were shortened.

- [reviews/](reviews/REVIEW_20261106.md): the November review, its separate
  [point-by-point critique](reviews/ASTRA_CRITIQUE_20261106.md), and
  [verified fixes](reviews/FIVE_FIXES_20261106.md).
- [reorganizations/20261107/](reorganizations/20261107/README.md): preserved
  correction/design snapshots, their current owners, and the path migration
  map. They are historical records, not competing current specifications.

## Rule

When recovering a lead from the archive, preserve its original evidence layer
and write the new result through the current protocol:

```text
archived lead
-> strict graph query or preregistered probe
-> saved report
-> analysis note
-> candidate / rejected / stricter result
```
