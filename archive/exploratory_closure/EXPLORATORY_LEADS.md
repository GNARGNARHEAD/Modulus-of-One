# Exploratory Lead Ledger

> Status: mixed-status exploratory lead ledger.
>
> This file preserves speculative and historical leads without upgrading them to
> strict-stage MoO claims. Each lead must name its source mode, bounds, graph or
> report query, promotion criteria, and kill criteria.

## Ledger Rules

Each lead should use this shape:

```text
lead:
evidence_layer: exploratory | external_probe | strict
claim_status: observation | lead | candidate | strict_result | rejected
source_mode:
source_artifacts:
bounds:
speculative_operands_used:
graph_native_observable:
current_claim:
strict_reproduction_query:
promotion_criteria:
kill_criteria:
allowed_claim_language:
disallowed_claim_language:
```

## Exploratory And Historical Leads

### Phase-Provenance Transport: Exhausted U40/U80 Design

```text
lead: qz_phase_provenance_transport
evidence_layer: external_probe
claim_status: observation
source_mode:
  read-only strict-stage graph occurrences plus external additive C_q labels
source_artifacts:
  ../../research/geometry/PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md
  ../../out/experiments/geometry/quarantined_phase_transport/
bounds:
  frozen U40 primary and separately preregistered U80 follow-up; q=3..24,
  length=8, 4096 null draws, exact-stage stratification, seed=1729
speculative_operands_used:
  no in the source graph; rational result phases are inspected only and the
  cumulative C_q states exist outside MoO
graph_native_observable:
  strict division edge occurrences, source stages, confirmed shared inputs,
  result nodes, exposure, and shared-input hub degree
current_claim:
  addition/subtraction descend exactly through Q/Z and retained-integer
  division has an exact torsion-preimage interpretation; both frozen transport
  runs were insufficient for the preregistered stratified-null aperture, so no
  provenance-order effect was retained or killed
strict_reproduction_query:
  python3 moo_phase_transport_probe.py --db <frozen-corpus.sqlite> \
    --max-q 24 --path-length 8 --null-samples 4096 \
    --stage-bin-width 1 --seed 1729 --checkpoint-stage <40-or-80> --pretty
promotion_criteria:
  A new independently frozen design first satisfies every unchanged aperture
  gate and then exceeds the mean and 99th percentile of both cyclic controls.
kill_criteria:
  The U80 stop rule already kills further tuning of this current path/null
  design; a future independently motivated design may pose a different test.
allowed_claim_language:
  "The exact operator boundary is established; the current transport design
  was not estimable under its strict null."
disallowed_claim_language:
  "MoO has phase motion," "speculative phases operate," or either a retain or
  kill verdict for the transport effect.
```

### Exploratory `-4/3` Hinge

```text
lead: exploratory_-4_over_3_hinge
evidence_layer: exploratory
claim_status: lead
source_mode:
  bounded exploratory closure, not aligned strict-stage MoO
source_artifacts:
  ../working_logs/NEXT_STEPS.md
  MOTIF_GRAPH_NOTE.md
  MOTIF_PERSISTENCE_NOTE.md
  MOTIF_MASS_NOTE.md
  CORRIDOR_ATLAS_NOTE.md
bounds:
  historical n=5/n=6 bounded replay reports; see each source artifact for exact
  q and value caps
speculative_operands_used:
  yes in exploratory closure reports
graph_native_observable:
  high report-level hub count, motif membership, coverage of inspected nodes
  such as 34/21 and 87/32 in the historical closure corpus
current_claim:
  -4/3 was an exploratory hinge under the named closure mode and bounds.
strict_reproduction_query:
  Use a strict graph corpus and inspect -4/3 with:
    python3 moo_research_report.py --db <corpus.sqlite> --node -4/3 --pretty
  Then compare corpus-wide rankings:
    python3 moo_research_report.py --db <corpus.sqlite> --corpus-baselines \
      --rank-by derivation_events --control denominator --pretty
promotion_criteria:
  A strict-stage graph observable shows repeated witness diversity or
  neighborhood structure for -4/3 after denominator/component controls.
kill_criteria:
  The hinge role disappears when speculative operands are disallowed, or it is
  ordinary among denominator-matched controls.
allowed_claim_language:
  "-4/3 is an exploratory hinge under closure mode."
disallowed_claim_language:
  "-4/3 is a strict MoO organizing center" until the strict reproduction query
  supports that claim.
```

### Probe-Selected Rational Dossiers

```text
lead: inspected_probe_rational_dossiers
evidence_layer: external_probe
claim_status: observation
source_mode:
  external constants selected historical rationals for inspection
source_artifacts:
  ../working_logs/NEXT_STEPS.md
  TRANSCENDENTAL_ATTRACTORS_NOTE.md
  ../../research/strict_stage/CONVERGENCE_STRUCTURE_NOTE.md
bounds:
  mixed historical reports; strict graph dossiers must name their own SQLite
  corpus config
speculative_operands_used:
  depends on source artifact; strict graph dossiers do not use speculative
  operands
graph_native_observable:
  strict node dossier fields: first_stage, confirmation status, incoming
  witnesses, shared-input neighborhood, rational baselines
current_claim:
  Probe-selected rationals are inspection targets, not MoO-native identities.
strict_reproduction_query:
  python3 moo_research_report.py --db <corpus.sqlite> --node 34/21 --pretty
  python3 moo_research_report.py --db <corpus.sqlite> --node 22/7 --pretty
  python3 moo_research_report.py --db <corpus.sqlite> --node 87/32 --pretty
promotion_criteria:
  A target has a corpus-wide rank or strict graph role that remains meaningful
  after rational baselines and controls.
kill_criteria:
  The dossier shows only ordinary denominator/tree visibility or the ranking
  flags many mundane controls equally.
allowed_claim_language:
  "34/21 is a probe-selected strict graph node with the following dossier."
disallowed_claim_language:
  "MoO constructs pi/e/sqrt2/phi" from a rational near miss.
```
