# Strict-Stage Core Corpus

> Program status: active graph substrate with transitional studies retained at
> their actual evidence strength.

## Exact Question

What construction, confirmation, witness, operation, neighborhood, and
aperture structure appears in the selected positive-spine strict field when
speculative outputs are recorded but never reused as operands before
confirmation?

## Relation To The Core

This is the current implemented strict evidence layer. It is narrower than the
full signed operator-fan concept and does not promote a value merely because an
arithmetic edge reaches it.

## Status By Scope

| Scope | Evidence layer | Claim status | Tool status | Result status | Result scope |
| --- | --- | --- | --- | --- | --- |
| Positive-spine operand and graph-integrity rules | `strict` | `strict_result` | `maintained` | `active` | Current in-memory and SQLite implementations |
| Rational baseline and operation ecology | `strict` | `observation` | `maintained` | `active` | Current bounded graph measurements |
| Temporal confirmation interpretation | `strict` | `lead` | `maintained` | `active` | Promotion behavior observed; broader interpretation open |
| Historical strict node-summary studies | `strict` | `observation` | `historical` | `completed_version` | Aligned operand semantics, but non-graph-native and missing named source/report files |
| Closure aperture and witness-threshold studies | `exploratory` | `lead` | `historical` | `completed_version` | Native closure ledgers with availability limits listed below |

## Conceptual Dependencies And Reading Order

1. [Current graph-corpus contract](../../../docs/software/GRAPH_CORPUS.md)
2. [Runtime and construction identity](../../../docs/software/RUNTIME.md)
3. [Graph invariants](../../../docs/protocols/graph-invariants.md)

For the transition from earlier ledgers, consult the
[stage-indexed universe](../STAGE_INDEXED_UNIVERSE_NOTE.md),
[first R100 study](../STAGE_INDEXED_R100_NOTE.md),
[old-ledger convergence](../CONVERGENCE_STRUCTURE_NOTE.md),
[construction aperture](../CONSTRUCTION_APERTURE_NOTE.md), and
[witness threshold](../WITNESS_THRESHOLD_NOTE.md). Their availability and
claim limits are accounted for below; they are not prerequisites for using
the current corpus.

## Tools And Software Dependencies

- [`moo/constructionist_math.py`](../../../moo/constructionist_math.py) is the in-memory
  graph runtime and demo/export surface.
- [`moo/strict_stage_moo.py`](../../../moo/strict_stage_moo.py) and
  [`moo/graph_corpus.py`](../../../moo/graph_corpus.py) build the SQLite path.
- [`moo/graph_query.py`](../../../moo/graph_query.py) inspects exact graph
  neighborhoods and confirmations.
- [`moo/core_alignment_check.py`](../../../moo/core_alignment_check.py)
  compares small runs across the in-memory and SQLite paths.
- [`moo/research_report.py`](../../../moo/research_report.py),
  [`moo/rational_baselines.py`](../../../moo/rational_baselines.py), and shared graph
  invariants support the registered rational-baseline, temporal-confirmation,
  and operation-ecology lenses.

Focused supporting contracts are
[`tests/test_rational_baselines.py`](../../../tests/test_rational_baselines.py),
[`tests/test_moo_graph_invariants.py`](../../../tests/test_moo_graph_invariants.py),
[`tests/test_moo_graph_evidence.py`](../../../tests/test_moo_graph_evidence.py), and
[`tests/test_moo_graph_query.py`](../../../tests/test_moo_graph_query.py). The
query tests exercise inspection and confirmation. The corpus builder and
alignment CLI do not currently have dedicated test files; other tests build
bounded corpora, and the walkthrough independently checks the full field.

## Current Corpus Evidence

Historical SQLite identities, sizes, hashes and regeneration limits are recorded
in the [corpus inventory](../../experiments/CORPUS_INVENTORY.md). Its
2026-11-04 check records all five historical inputs as absent and distinguishes
the surviving, separately named U576/U80/U160 calibration sources. The corpus
contract points to that inventory; older named paths do not establish that
their inputs survive.

[Node association profiles](../../../docs/software/NODE_PROFILES.md) use this substrate
read-only, with source hashes, checkpoint filtering and named certificates.
They add inspection metadata without changing graph or operand semantics.

## Transitional Evidence Accounting

| Note | Source status | Derived-report status | Permitted reading |
| --- | --- | --- | --- |
| `STAGE_INDEXED_R100_NOTE.md` | Named R100 source JSON absent | Named summary absent | Preserved first study; not currently re-auditable from its named files |
| `CONVERGENCE_STRUCTURE_NOTE.md` | Source ledger explicitly purged | Named derived report absent | Historical non-graph-native chain context |
| `CONSTRUCTION_APERTURE_NOTE.md` | `native_r5_full.json` and `native_r6_full.json` present | Named aperture summaries absent | Transitional first-witness observation; not globally minimal or graph-native |
| `WITNESS_THRESHOLD_NOTE.md` | `native_r5_v3.json` and `native_r5_full.json` present | Named threshold summary absent | Completed local ledger audit; not a current strict graph result |

These notes stay visible here because missing or transitional evidence is a
status to record, not a reason to erase the question.

## Registered Lens Ownership

This card owns the transition entries for:

- Rational Baseline Lens
- Temporal Confirmation Lens
- Operation Ecology Lens
- Aperture Lens

The first three have maintained graph-oriented infrastructure. Aperture still
needs a graph-native ancestry formulation before its older ledger result can be
promoted.

## Allowed And Forbidden Language

Allowed: current positive-spine operand rule; graph-recorded speculative output;
bounded strict observation; explicitly transitional ledger result.

Forbidden: the current field is the full signed Modulus of One; missing derived reports are
present; first-witness aperture is globally minimal; a node summary replaces
edge-level evidence.

## Next Admissible Work

Reproduce one transitional question through a separately named SQLite graph
before adding another summary metric. Stop any proposed metric that cannot identify the exact edges and
completeness frontier supporting it.
