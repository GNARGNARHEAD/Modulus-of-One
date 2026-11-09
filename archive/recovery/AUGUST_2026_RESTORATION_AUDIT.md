# August 2026 Restoration Audit

> Status: completed source-and-evidence recovery audit.
>
> Date: 2026-08-28.

## Why This Record Exists

An overbroad consolidation removed sixteen research artifacts and replaced six
detailed navigation/research documents with much shorter versions. The
scientific mistake was to treat bounded negative or insufficient-aperture
results as authority to retire whole tools and connected research lenses.

That decision is withdrawn. The deleted surface was recovered from an exact
Codex session record before any further cleanup. In total, the restored deleted
surface contains 698,935 bytes: five probes, five test modules, three primary
research notes, two saved analyses, and one historical source conversation.
The session record contains exactly twenty-two consolidation deletion
directives: these sixteen artifacts plus the six detailed documents listed
below. Every target is present again.

The short explanatory rewrite was not discarded. It now lives separately as
`../../LAYMAN_OVERVIEW.md`, while the detailed documents again provide the
primary research map.

## Recovery Source

The local rescue snapshot is:

```text
out/recovery/pre_restoration_2026-08-28/
```

It contains:

- a stable 7,794,007-byte copy of the source session record;
- exact deleted-file payloads extracted from the complete patch event;
- the six pre-consolidation detailed documents;
- the shorter post-consolidation document versions;
- pre-restoration bytecode and saved-report safety copies.

Stable session snapshot identity:

```text
file: rollout-2026-08-10T09-25-53-019fea22-6fc6-7113-b4fb-b4f13e1da882.jsonl
sha256: 684cc79fd2f2f335b066f2efd79e681a35cadd811d33442700b76bc728c9e920
```

This rescue directory is intentionally local and ignored; it is a fallback,
not a durable backup. The recovered source, tests, notes, analyses, and
historical conversation are restored to the ordinary repository surface.

## Exact Deleted-File Restoration

Each file below was first restored byte-for-byte. Fifteen remain byte-identical
to the extracted payload. The critical-probe test was then changed deliberately
to record a complete strict-stage fixture under the corrected shared evidence
contract; its original extracted bytes remain in the rescue snapshot.

| Restored path | Bytes | Extracted SHA-256 |
| --- | ---: | --- |
| `moo_phase_metric_probe.py` | 79,639 | `bde3682d79ecbf93d5ae71ef79db1ad9ceee6217e7a9274bc8d301e37f125d01` |
| `moo_theta_weil_probe.py` | 58,923 | `dc5777d14d7059e73848940c743d3c1abc5a4eb66cbc0869e8f3dbdfd6934861` |
| `moo_zeta_arrival_probe.py` | 83,940 | `5146f6807d2871f0acb71626bb322926f971a163f2bc478462f68d5bf72869d9` |
| `moo_zeta_centered_inversion_probe.py` | 34,679 | `4613471d324f8cdaab4c12c750cc9403442a57286cc76398c3a68310050c82c5` |
| `moo_zeta_critical_probe.py` | 59,150 | `95c0010bcc4e48339ba83526ee2487259af990067f849cf6c67db0d9d3a961db` |
| `test_moo_phase_metric_probe.py` | 19,461 | `0b92260fdac2c91b52230448c38de4f55ab5ae1974e443320ac3c37426a5ca78` |
| `test_moo_theta_weil_probe.py` | 11,785 | `267074f4873e512b134bd5885a08b1380d2d5059f4aa56669a2b611d53c12038` |
| `test_moo_zeta_arrival_probe.py` | 12,149 | `5e75012090e231b76c95ae5ac0924b08d3bdc2b1fe118cfa4f927fdfc95bc6f7` |
| `test_moo_zeta_centered_inversion_probe.py` | 8,607 | `b496922c0af5adeeed1e4d6eef661883c0ea4dfd91ffa90deb28d8b6d9ad12b4` |
| `test_moo_zeta_critical_probe.py` | 14,710 | `e9d4e95c4aa3c582ab96e2cc2b32ff216261e43b14627ee5ccc84b51508f5ffb` |
| `research/euler/CENTERED_RECIPROCAL_SHELL_LENS_NOTE.md` | 15,508 | `9e421e6db09322edcf8bc2d765ae5b417afd314643fabce0db43829b89098bdc` |
| `research/geometry/PHASE_METRIC_COLLAPSE_NOTE.md` | 16,339 | `9f86b1396e5e0b5c9ea0a7731f4c6b512c9f4750a1b7fefacede9401e2847ae0` |
| `research/number_theory/THETA_WEIL_CONSTRUCTIVE_OBLIGATIONS_NOTE.md` | 14,132 | `c22b24b9c609b12caa5055514f06062d60eb5ade6e14a191d0c69b3588f82a50` |
| `out/experiments/euler/zeta_cancellation_arrival_v1.analysis.md` | 8,432 | `c9defc02186b77b80234dbf112c0fb66ef32b232a65df9b17d5f9e2dae9cc71a` |
| `out/experiments/euler/zeta_critical_first_zero_v1.analysis.md` | 4,655 | `5f59a9490e6a2d6fb2c2ce7762f2270c36cde67596229b7b35108d0ad2d684c0` |
| `Qwen3-8-27B-Analysis-full-conversation.md` | 256,826 | `c22b0d26c2f0a5afb1833e39b2f7c5c702327ac2d4d321ec0fd51a3949801027` |

The repaired critical test now has SHA-256
`54cd8049719a280851cc083227f1ee147058fd38daa15b080abcdd0e198c722b`.
Its only recovery-follow-up change is fixture completeness: it records stages
1 through 16 with `strict_stage_expected_candidate_events(stage)` so a missing
late source is tested against a genuinely complete frontier rather than an
internally contradictory stage record.

## Detailed-Document Restoration

These pre-consolidation documents were preserved and reinstated as the base
before making narrow lifecycle and artifact-policy corrections:

| Snapshot path | Bytes | Pre-consolidation SHA-256 |
| --- | ---: | --- |
| `README.md` | 36,726 | `ba2c324f740aec6e3438629d57188c2564de30f27df3087da9bf2bcd10ff57b2` |
| `DOCS_INDEX.md` | 23,696 | `faef5c00d2df3692c4247fa40e657467439bb73360c261f6ad3cebac8931d413` |
| `RESEARCH_LENSES.md` | 36,820 | `f38c4f1e0242f7bdcebe81d84ff5d501509adaa68cdfb3178b41c33f93c43b79` |
| `research/README.md` | 3,857 | `c829c635954b43b2212107cbe1dd06d01a96a6c50a9284203cdb972d74d58c90` |
| `research/euler/EULER_RECIPROCAL_MASS_AND_CIRCLE_LENS_NOTE.md` | 18,807 | `d0aa2415df82facc60a0824722c3f25dd2511d5915c56c8c7acc6617e680d93a` |
| `out/experiments/euler/README.md` | 2,838 | `962863dc4cbf722d851c4011047678465673df46ee4dd7cef1e73abfb564f633` |

The current versions differ where they now link the layperson overview,
distinguish maintained tools from versioned outcomes, and retain machine
evidence. The preserved originals remain locally available for comparison.

## Scientific Status After Review

- The quadratic source and test stack was intact, but its theta/Weil analytic
  continuation had been severed. That continuation is restored. The U850 v1
  ablation remains frozen and negative for its tested feature/model; the wider
  quadratic infrastructure remains maintained.
- The theta/Weil probe is an active external finite calibration with six open
  obligations. It is not an arithmetic explicit-formula calculation or RH
  evidence.
- The critical first-zero v1 probe is a completed numerical calibration, not a
  zero certificate.
- The arrival v1 probe preserves a reproducible finite cancellation trajectory
  but its graph-specific interpretation was not promoted.
- The centered reciprocal-shell lens remains a candidate. Only the proposed
  fixed-radius global zeta-zero symmetry is rejected.
- The phase metric remains a maintained exact instrument. Its U40 v1 graph
  comparison did not promote a special fibre effect.
- The exact U40/U80 phase-transport design is exhausted by its registered
  insufficient-aperture rule. That is not a retain or kill decision for every
  future transport design.

## Verification Gate

The post-recovery workspace passed:

```text
python -m unittest discover -v
201 tests passed

python -m compileall -q .
passed

python moo_core_alignment_check.py --max-stage 6 --pretty
passed: 28 nodes, 90 edges, no mismatches
```

Focused live checks also established that the restored saved phase, critical,
arrival, and centered reports are valid JSON, bind to the current restored tool
and source-corpus hashes, and reproduce their selected scientific summaries.
The U300/N200 theta/Weil replay reproduces the recorded tail-only versus
tail-plus-roundoff calibration split and the synthetic off-line control.

## Known Integration Follow-Ups

These issues were found during the restored-code review but are intentionally
not mixed into the recovery change:

1. `report_metadata` binds the direct tool and database but not transitive
   helpers such as `moo_graph_evidence.py`. The saved v1 critical and centered
   summaries remain stable, but their current full payloads contain legitimate
   new completeness/aperture fields without a changed direct-tool hash. A v2
   provenance schema should hash the dependency bundle and report schema.
2. `moo_zeta_critical_probe._compact_edge` should preserve eligibility,
   complete-stage, and truncation fields from the shared evidence layer. Its
   bounded display-reference count should not be named as though it were an
   exact distinct-edge count.
3. `moo_zeta_arrival_probe._validate_stage_prefix` duplicates strict-generator
   frontier and retention rules. It should consume the shared completeness
   contract so generator and probe semantics cannot drift.
4. The phase-metric report's `complete_scan` field means every recorded
   additive edge was scanned; it does not independently certify that the
   checkpoint is a complete strict frontier. The field should be renamed or
   paired with the shared complete-stage audit.
5. Theta/Weil needs a new machine-readable v2 report, transitive provenance,
   stronger Jacobi residual/orthogonality checks, and additional tail-envelope
   contracts before any promotion. Its current synthetic fixtures remain
   calibration baselines.

Do not overwrite the seven saved v1 reports while addressing these items.
Schema or dependency changes require new experiment identifiers.

All 74 JSON records in `out/experiments/` are now retained by the ignore
policy, along with the experiment Markdown, Python analysis sources, tables,
and figures. Retention preserves bytes without promoting historical or
exploratory evidence. The five large SQLite inputs remain local-only and are
checksum-bound in `../../out/experiments/CORPUS_INVENTORY.md`; they must not be
deleted or overwritten before durable blob storage exists.

A final ignore-policy comparison found no hidden repository file outside the
explicit local recovery snapshot, Python bytecode/cache directories, repository
metadata, and the five inventoried SQLite blobs.

No Git command was used during this recovery or audit.
