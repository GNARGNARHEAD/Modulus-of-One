# Repository Layout And Document Consolidation

On 2026-11-07, the flat repository was organized around the philosophy,
worked constructions and supporting research. The baseline was commit
`921669be473b7f2776344e1f61e3d26d68a2946a` in the original working repository.
The root went from 136 files to eight; its 70 Python modules and 38 tests
moved into dedicated directories. The two domain test modules joined the
same test discovery root.

## Current Homes

| Material | Location and purpose |
| --- | --- |
| Public introduction, credit, licenses and contribution instructions | Repository root. |
| Philosophy, foundations, claims, examples, protocols and software references | [docs/](../../../docs/README.md), with one named owner for each kind of definition. |
| Runtime and reusable instruments | [moo/](../../../moo/README.md), invoked as Python modules. Earlier closure and ledger tools are explicitly identified under `moo/legacy/`. |
| Automated checks | [tests/](../../../tests/README.md), including the geometry and dynamics checks. |
| Small reader-facing executable | `tools/moo_walkthrough.py`. |
| Program questions, domain scripts and evidence | [research/](../../../research/README.md); saved experiments formerly under `out/experiments/` are now in [research/experiments/](../../../research/experiments/README.md). |
| Dated reviews, earlier interpretations and recovery provenance | [archive/](../../README.md). |
| Local outputs and preserved large inputs | Ignored `out/` and the paths in the corpus inventory; databases were not moved. |

## Consolidated Documents

- The current [epistemic-order note](../../../docs/foundations/EPISTEMIC_ORDER.md)
  includes the operator-fan note's unique distinctions: cancellation versus
  unmarked absence, self-ratio versus parts, the continuing full fan, and the
  conceptual signed field versus implemented positive-spine rule.
- The [claim ledger](../../../docs/CLAIMS.md) owns current claim limits and
  evidence layers. Alignment and realignment documents here preserve their
  correction history rather than acting as competing current specifications.
- The [research protocol](../../../docs/protocols/research-programs.md)
  combines program lifecycle with the former analysis-tool protocol and
  machine-term translation. The [lens reference](../../../docs/research/LENSES.md)
  retains all 17 detailed design contracts; assigning a program owner did not
  erase their controls or stopping criteria.
- The [runtime reference](../../../docs/software/RUNTIME.md) owns current
  representation and interface details from `VISION.md`. Its potential-infinity
  distinction is retained in the [philosophical notes](../../../docs/PHILOSOPHY.md).
  Open questions are routed to their foundation or research owner.
- The [documentation guide](../../../docs/README.md) and research program
  cards replace the old central file index. That index was not exhaustive;
  its original contents are preserved here without retaining its authority.
- The current [corpus contract](../../../docs/software/GRAPH_CORPUS.md)
  no longer opens with missing historical inputs or repeats its operand rule.
  The complete original corpus note here preserves its dated measurements.
- The former root conversation pointer is consolidated into the
  [archive availability notice](../../README.md). The raw transcript remains
  unchanged locally and excluded from the public file snapshot.

The [section transfer record](DOCUMENT_TRANSFERS.json) accounts for the
foundation, claim and protocol consolidation. The
[path map](PATH_MAP.json) locates moved and merged files and records original
hashes. It is a migration record, not another current reading index.

## Evidence And Original Path Context

Frozen reports, preregistrations, analyses, figures, editorial evidence extracts,
dated analysis programs and historical snapshots retain their original bytes.
Their embedded paths, commands, source hashes and links describe the original
run or revision. Read them in that context; use the path map to find relocated
files. Current navigation and runnable examples use the new layout.

Moving a source module and changing its imports changes its hash. It does not
certify that source as the one used by a historical experiment. Frozen source
guards retain their expected identities and reject changed sources. Exact
historical reproduction still requires the original code, environment and
inputs; the public snapshot does not bundle every historical source revision.

The [corpus inventory](../../../research/experiments/CORPUS_INVENTORY.md)
continues to distinguish five missing historical databases from surviving
local calibrations. Some protected calibrations live under `out/scratch/`;
that directory is not a blanket deletion target.

Two stale statements in the active span/triad/square note were corrected using
the already adopted rules: the `2*2 -> 4` witness occurs at `U2`, before the
complete additive triad at `U3`; and a witness returning to value `1` does not
inherit immediate certainty. No operand or confirmation rule changed.
