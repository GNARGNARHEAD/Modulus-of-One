# Spectral And Null-Like Scouting

> Program status: concept-stage external analysis program; no implemented
> spectral scout or measured program claim.

## Exact Question

Can edge-derived signals help locate graph regions or construction paths whose
structure is hard to see in ordinary value summaries, including paths that
collapse under a chosen projection while remaining nontrivial in the source
graph?

## Relation To The Core

Fourier, graph-spectral, diffusion, Hodge, and null-geodesic ideas are external
framing. They may propose an inspection signal, but every candidate must return
to exact nodes, edge occurrences, witnesses, neighborhoods, and controls.

## Status By Scope

| Scope | Evidence layer | Claim status | Tool status | Result status | Result scope |
| --- | --- | --- | --- | --- | --- |
| Edge-derived spectral scout | `external_probe` | `lead` | none | `active` | Design only; no implemented scout or measurement |
| Null-like projection-collapse analogy | `external_probe` | `lead` | none | `active` | Conceptual inspection heuristic only |

## Conceptual Dependencies And Reading Order

1. [Spectral scout concept](SPECTRAL_SCOUT_NOTE.md)
2. [Null-geodesic lens](NULL_GEODESIC_LENS_NOTE.md)
3. [Fourier analysis lens](FOURIER_ANALYSIS_LENS_NOTE.md)
4. [Spectral/null related works](SPECTRAL_NULL_RELATED_WORKS_NOTE.md)

The related-works note unifies the two question families, but it remains a
literature and design map rather than evidence.

## Tool Status

No `moo_spectral_*` implementation currently exists. Historical visualization
or motif scripts must not be relabeled as the proposed spectral scout.

There is therefore no focused spectral test file.

A minimal future tool would need to state:

- the exact graph corpus and edge field it reads;
- the external projection or signal it computes;
- the nodes or paths it returns for inspection;
- matched nulls or shuffles;
- what it refuses to conclude from the score alone.

## Current Disposition

- Spectral scouting is a candidate way to prioritize graph inspection.
- A null-like path means nontrivial source structure can collapse under a
  declared projection; it does not import spacetime physics into Modulus of One.
- No current measurement establishes a spectral signature, null corridor,
  harmonic branch, or graph geometry.

## Allowed And Forbidden Language

Allowed: proposed edge-derived scout; projection-collapse analogy; candidate
localized graph inspection.

Forbidden: Modulus of One has a spectrum with demonstrated meaning; Modulus of One contains null
geodesics; literature similarity is project evidence.

## Next Admissible Work

Implement only the smallest report-only scout with one fixed edge signal, one
localization rule, and matched graph shuffles. Stop if the score cannot return a
small exact graph context or performs no better than simple degree/value
baselines.
