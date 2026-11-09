# Pascal / shell certificate calibration: fixed design

Date: 2026-09-22. Written before the new graph-witness lookups.

evidence_layer: external_probe
claim_status: candidate

This is a small exact calibration prompted by GNARGNARHEAD's pasted conversation
about the unit shell and Pascal's triangle. It tests certificate distinctions,
not Pascal specificity, privileged geometry, or a new timing law. The earlier
shell-composition report already supplied the direct-shell U576 example; that
case is a reused calibration, not a holdout.

## Inputs and rule

Use only the two current-generator inputs checksum-bound by
[the shell-composition manifest](../../geometry/results/2026-09-20-shell-composition-current-manifest-v1.json).
Verify hashes, open read-only, and check strict alignment. Do not generate or
modify a corpus. Report the wide field at its complete U576 checkpoint and
the narrow-retention control at U80. These are calibration fields, not
independent samples.

## Frozen certificates and predictions

At the declared square-coordinate cut X=16, Y=9, compare:

| Certificate | Expression | Predicted wide completion |
| --- | --- | ---: |
| factored | (X+Y)(X+Y) | U25 |
| expanded_left | ((XX+XY)+XY)+YY | U544 |
| expanded_paired | (XX+YY)+(XY+XY) | U337 |
| composed_norm | (16-9)^2+(12+12)^2, with 12=4*3 | U576 |

For these four certificates also retain the source-shell premises 4*4=16,
3*3=9, 5*5=25, and 16+9=25, and expand square-coordinate leaves back to 4,3
in the construction expressions. Repeated use of an intermediate shares its
node and witness; it does not create another recorded event.

Generic binary-power control: X=7, Y=2, no shell premise. Apply the first three
schemas. Predictions: factored U9, expanded_left U77, expanded_paired U53.
All three target 81. This control tests whether the timing distinction needs
a shell; it is not a magnitude-matched statistical control.

The two expanded routes in each family must have equal associative/commutative
(AC) expression fingerprints, different intermediate witnesses, and different
completion stages. The factored and expanded expressions must remain distinct
under AC, with their distributive/binomial dependency explicitly declared.
No semantic or statistical independence is predicted.

Record the literal 625/625 -> 1 request: U625 is predicted, hence it must be
unavailable in U576. Record (4/5)*(4/5) -> 16/25: fractional operands are
structurally prohibited, regardless of their value presence.

## Measurement, controls, and stop rule

Primary quantities: exact directed edge references, operand confirmation,
earliest complete certificate stage, and AC fingerprint equality. Baseline:
maximum positive-integer operand over all required requests, conditional on
retention. Keep target-node first arrival separate from certificate completion.

Use the narrow field as a retention control; none of the seven certificates
is predicted to be complete there. Compare the two expanded arrangements as
the AC control, and X=7,Y=2 as the generic polynomial control. Validate each
reported edge reference independently with raw SQL and exact arithmetic.

Also check the external algebra exactly on a small fixed grid of rational
parameters (0, 1/2, 3/4, -2/3) and exponents 0..8: binomial parity expansion
versus pair multiplication, norm preservation, and the positive partition.
These checks supplement the general proofs; they are not graph measurements.

If a prediction fails, report the failure and inspect its cause. Do not expand
the search or optimize the examples. Stop after these cases. No held-out
predictive claim or runtime/foundation change is proposed.
