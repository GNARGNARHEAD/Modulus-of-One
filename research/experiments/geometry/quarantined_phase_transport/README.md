# Quarantined Phase-Transport Experiments

> Status: counterfactual experiment area, not aligned runtime output.

Reports here start from read-only, positive-spine strict graph occurrences, but
their phase accumulation is external:

```text
strict division occurrences
-> q-conditioned, residue-blind provenance walks
-> external addition of Q/Z step labels
```

Rational result nodes are not used as operands in the source corpus. A
provenance walk is not a construction path, and a cumulative phase state is
not a Modulus of One runtime node unless an exact source edge independently records it.

Each experiment must preserve occurrence ids, input-node witnesses, stages,
result nodes, checkpoint scope, strict-alignment status, source/tool checksums,
conditional cyclic-group controls, and an explicit kill decision.

No result from this directory may be presented as runtime circle motion or as
evidence for changing the speculative-operand rule.

## Frozen Runs

```text
phase_provenance_transport_u40_q24_l8_v1:
  primary
  result = insufficient_aperture
  failed = holdout path count and mutable-position fraction

phase_provenance_transport_u80_q24_l8_v1_followup:
  separately preregistered aperture-resolution follow-up
  result = insufficient_aperture
  failed = mutable-position fraction
```

U80 resolved simple path scarcity but did not reach the unchanged `1/4`
mutable-position gate for the exact `(q, stage, exposure, hub)` shuffle. Its
preregistered stop rule therefore ends the current design. Do not tune stage
bins, path length, thresholds, seed, or corpus in response to these reports.

Each local run set has a `.pre.md`, checksum-bound `.json`, and paired
`.analysis.md`. The repository retains all three: the preregistration freezes
the design, the JSON preserves the exact machine evidence, and the analysis
states the interpretation boundary. A failed aperture gate is a scientific
result and does not make its scored payload disposable. The mathematical and
graph interpretation is in
[[PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md](../../../geometry/PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md)](../../../geometry/PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md).

To inspect either frozen configuration without writing a bulk report, run from
the repository root:

```text
python3 -m moo.phase_transport_probe --db out/experiments/circle_as_one_u40_wide.sqlite --pretty

python3 -m moo.phase_transport_probe --db out/experiments/circle_as_one_u80.sqlite --checkpoint-stage 80 --experiment-id phase_provenance_transport_u80_q24_l8_v1_followup --pretty
```
