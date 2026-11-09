# Geometry Experiments

This directory is for durable geometry-adjacent research records, including
their machine-readable reports.

Current scope:

```text
rational quadratic shells
unit-shell parametrization reports
Pythagorean shell scans
circle-without-pi guardrail tests
circle-square branch alignment tests
prime/Euclid shell-alignment audits
primitive Euclid branch sweeps
branch-lineage audits for square/shell interaction interpretation
quarantined q-conditioned phase-transport preregistrations
```

The artifacts here do not claim that Modulus of One defines the Euclidean circle or
constructs `pi`. Prime and Euclid-parameter fields are scrutiny fields after
rational shells are cleared to primitive integer triples; branch-sweep reports
also preserve partial and absent target branches as data. These artifacts do
not by themselves claim that primes explain Modulus of One geometry. They preserve strict
graph reports and paired analysis notes for rational shell structure.

Read geometry artifacts through Modulus of One witness language:

```text
value appears
value appears through the counting spine
value appears through the inspected branch
projected form organizes later witnessed emergence
```

Branch-lineage rule:

```text
branch = same relation repeated along the unfolding of Modulus of One
```

Primitive Euclid sweeps and circle-square reports are report machinery until
translated through branch lineage. A retained edge row is a witness field, not
the definition of the branch.

Tool terms such as `provenance`, `retention`, and `aperture` are bookkeeping
for order, witness, emergence, relation, and field of observation.

Each experiment run may produce:

```text
<experiment_id>.pre.md
<experiment_id>.json
<experiment_id>.analysis.md
```

All three files are part of the repository review surface. Scored and frozen
`*.json` reports are retained because their expanded node, edge, lineage,
control, and absent-branch rows are the machine evidence behind the analyses.
Negative or quarantined status does not make that evidence disposable.

Several historical geometry reports cannot be regenerated exactly from the
current workspace: their recorded strict-stage corpora are absent and their
recorded tool hashes differ from current source files. Those JSON reports are
therefore the surviving exact machine witnesses, not replaceable build output.
Any available source `*.sqlite` corpora remain ignored immutable inputs and are
inventoried in [CORPUS_INVENTORY.md](../CORPUS_INVENTORY.md).

Small `*.analysis_manifest.json`, `*.provenance.json`, and `*.summary.json`
sidecars remain part of the record when they bind a frozen run to its sources.
Analyses must name and, for frozen results, checksum the report they interpret.

Reports should use the invariant vocabulary in
[graph-invariants.md](../../../docs/protocols/graph-invariants.md), the realignment vocabulary in
[research-programs.md](../../../docs/protocols/research-programs.md), and the claim boundary in
[CLAIMS.md](../../../docs/CLAIMS.md).

## Quarantined Phase Transport

`quarantined_phase_transport/` contains the boundary README and frozen
preregistrations for the external q-conditioned, residue-blind transport test.
The exact operator classification and completed interpretation are indexed in
[PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md](../../geometry/PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md); the
implementation and focused contracts are `../../../moo_phase.py`,
`../../../moo_phase_transport_probe.py`, `../../../test_moo_phase_operator.py`,
and `../../../test_moo_phase_transport_probe.py`.

Its indexed artifacts are:

- [README.md](quarantined_phase_transport/README.md): quarantine and runtime boundary.
- [phase_provenance_transport_u40_q24_l8_v1.pre.md](quarantined_phase_transport/phase_provenance_transport_u40_q24_l8_v1.pre.md):
  frozen U40 primary preregistration.
- [phase_provenance_transport_u40_q24_l8_v1.analysis.md](quarantined_phase_transport/phase_provenance_transport_u40_q24_l8_v1.analysis.md):
  checksum-bound U40 interpretation. Its named `.json` report is retained as
  the corresponding machine evidence.
- [phase_provenance_transport_u80_q24_l8_v1_followup.pre.md](quarantined_phase_transport/phase_provenance_transport_u80_q24_l8_v1_followup.pre.md):
  separately frozen U80 aperture-resolution follow-up and stop rule.
- [phase_provenance_transport_u80_q24_l8_v1_followup.analysis.md](quarantined_phase_transport/phase_provenance_transport_u80_q24_l8_v1_followup.analysis.md):
  checksum-bound U80 interpretation. Its named `.json` report is retained as
  the corresponding machine evidence.

Both registered apertures stopped before retain/kill:

```text
U40:
  insufficient_aperture
  failed strict stratified-null mutable fraction and holdout-path count

U80 follow-up:
  insufficient_aperture
  failed strict stratified-null mutable fraction
```

The U80 stop rule closes the current design. These artifacts support no
transport claim, no promotion of rational phase operations into aligned Modulus of One,
and no runtime change.

The checksum-bound U40 aperture can be reproduced from the repository root:

```text
python3 -m moo.phase_transport_probe --db out/experiments/circle_as_one_u40_wide.sqlite --pretty
```

The frozen U80 follow-up can be emitted without changing the registered
parameters:

```text
python3 -m moo.phase_transport_probe --db out/experiments/circle_as_one_u80.sqlite --checkpoint-stage 80 --experiment-id phase_provenance_transport_u80_q24_l8_v1_followup --pretty
```

The retained reports are immutable. Use `--write` only with a new path and
experiment identifier for a genuinely new run; existing files are never
overwritten. The ability to rerun the current tool does not make a frozen
report disposable.
