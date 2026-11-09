# Experiment Evidence

> Status: retained mixed-layer research record.

This tree stores machine reports, preregistrations, interpretation notes,
analysis programs, tables, and figures produced by Modulus of One research. These files
remain visible to ordinary source control even when an experiment was
exploratory, negative, rejected, frozen, or stopped for insufficient aperture.

Retention is not promotion. Interpret every artifact through its own
`evidence_layer`, `claim_status`, preregistration, analysis note, and current
research lens. Historical closure-mode reports do not become aligned strict
graph evidence merely because their bytes are preserved.

## Immutability Rule

- Never regenerate or edit a scored/frozen report in place.
- A changed tool, dependency, corpus, configuration, seed, or protocol receives
  a new experiment identifier.
- Keep negative and null results; they are part of the control record.
- Do not infer reproducibility from the continued existence of a generator.
- Preserve exact hashes and source/database identities whenever they are known.

## Large Corpora

SQLite source corpora are excluded from ordinary source control. The five
historical inputs, totalling more than 742 MiB, are absent at their named paths
in this checkout. Their recorded sizes, hashes, and configurations remain in
[the corpus inventory](CORPUS_INVENTORY.md), alongside the separately named
calibration inputs that survive locally. Reports and hashes alone do not
make an input available.

Preserve surviving inputs unchanged. A new generation run needs its own path
and identity; it cannot replace a missing historical source merely by using
the same configuration. The [worked inspection](../../docs/examples/WORKED_INSPECTION.md)
provides a small example that can be generated from a fresh checkout.

## Evidence Families

- `dynamics/`: retained preregistrations, analyses, and machine reports for
  stage-sensitive research.
- `euler/`: finite series and zeta calibration, arrival, and centered-inversion
  evidence.
- `gauss/`: congruence, quadratic-form, nested class/genus, provenance, and
  frozen holdout records.
- `geometry/`: rational shell, Euclid, phase, and stopped-design transport
  evidence.
- `216/`: historical 216/golden-rotation/power-lattice reports and notes.
- Root-level reports: mixed current and historical outputs whose status is
  defined by their corresponding research or archive documentation.
- Root-level `lattice_*_analysis.py` programs: retained historical analysis
  sources for the adjacent tables and figures.

## Original Paths And Sources

This collection moved from `out/experiments/` on 2026-11-07. Frozen reports,
preregistrations, analyses, figures and dated analysis programs retain their
original bytes, including embedded paths and source hashes. Read those paths
in their recorded revision; they are not fresh commands or claims of current
input availability. The [layout record](../../archive/reorganizations/20261107/README.md)
and its path map locate the retained files. Ignored databases were not moved.

New reports belong to a new experiment; run tools into a fresh ignored output
path first, review the record, then retain it beside its program or in this
collection. An old report remains an old report even when its tool is maintained.
