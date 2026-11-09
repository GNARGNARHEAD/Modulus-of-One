# Motif And Hinge Reproduction

> Program status: dormant exploratory-closure lead with retained historical
> witnesses and no strict-stage reproduction.

## Exact Question

Do bounded closure-era operation motifs or rational hinges, especially the
reported `-4/3` hinge, survive when the question is rebuilt over the aligned
strict graph with speculative operands disabled and matched controls fixed?

## Relation To The Core

The existing result comes from exploratory closure runs that reused
speculative values as operands. It remains useful hypothesis material, but it
is not current strict-stage Modulus of One evidence.

## Status By Scope

| Scope | Evidence layer | Claim status | Tool status | Result status | Result scope |
| --- | --- | --- | --- | --- | --- |
| Bounded closure motif and `-4/3` hinge | `exploratory` | `lead` | `historical` | `completed_version` | Named round-5/round-6 closure reports only; no strict reproduction |

## Conceptual Dependencies And Reading Order

1. [Exact hinge lead and kill rule](../../archive/exploratory_closure/EXPLORATORY_LEADS.md)
2. [First motif graph study](../../archive/exploratory_closure/MOTIF_GRAPH_NOTE.md)
3. [Bounded persistence study](../../archive/exploratory_closure/MOTIF_PERSISTENCE_NOTE.md)
4. [Motif-mass interpretation](../../archive/exploratory_closure/MOTIF_MASS_NOTE.md)

## Tools And Historical Dependencies

- [`moo/legacy/motif_graph_study.py`](../../moo/legacy/motif_graph_study.py) reads a saved closure
  report and summarizes first-witness motifs.
- [`moo/legacy/motif_persistence_study.py`](../../moo/legacy/motif_persistence_study.py) and
  [`moo/legacy/motif_grid_summary.py`](../../moo/legacy/motif_grid_summary.py) compare bounded closure
  replays.
- [`moo/legacy/motif_mass_study.py`](../../moo/legacy/motif_mass_study.py) joins historical motif and
  binding summaries.

These scripts remain historical instruments because their operand model is not
the aligned strict-stage default. They currently have no focused test files.

## Retained Evidence And Availability

The source closure reports
[`research/experiments/native_r5_full.json`](../experiments/native_r5_full.json)
and
[`research/experiments/native_r6_full.json`](../experiments/native_r6_full.json)
are present. The retained motif witnesses include
[`motif_r5.json`](../experiments/motif_r5.json),
[`motif_persistence_r5.json`](../experiments/motif_persistence_r5.json),
[`motif_persistence_r6.json`](../experiments/motif_persistence_r6.json),
and
[`motif_grid_r5_summary.json`](../experiments/motif_grid_r5_summary.json).

The `out/experiments/motif_mass_r6.json` output named by the historical
motif-mass note is absent. The note therefore survives as an interpretation,
not as a currently re-auditable machine result at that named path.

## Retained Finding And Strict Gate

The permitted historical statement is that `-4/3` acted as an exploratory
hinge under the named closure mode and bounds. The lead is promoted only if a
strict graph observable survives denominator-matched controls, nearby bound
changes, and exact edge inspection without speculative operands.

The lead is killed if the hinge or motif concentration disappears when
speculative operands are disallowed. Broad motif membership, value frequency,
or a high exploratory hub count is not enough.

## Allowed And Forbidden Language

Allowed: bounded exploratory hinge; historical motif lead; strict reproduction
required.

Forbidden: `-4/3` is a strict organizing center; motif closure proves a native
Modulus of One branch; historical scripts implement the aligned operand rule.

## Next Admissible Work

Specify one strict edge-level motif observable and matched denominator controls
before running a preserved SQLite corpus. Stop if the candidate cannot be
expressed through exact strict edges or if the hinge disappears under the
no-speculative-operands rule.
