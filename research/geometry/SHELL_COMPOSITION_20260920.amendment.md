# Shell composition: input-availability amendment

Date: 2026-09-20. Written before generating or inspecting the new fields.

The [original design](SHELL_COMPOSITION_20260920.pre.md) cannot run in this
checkout: none of the inventoried SQLite inputs exists here. A repository-wide
search including ignored files found no SQLite corpus. The saved historical
JSON reports and provenance sidecars do survive. The attempted original run
stopped at the first file-open and produced no report or graph measurements.

Keep that design unchanged. Do not rebuild files at any historical path or
claim that a current-generator field reproduces their bytes.

## Separate current-generator calibration

Experiment ID: `shell_composition_20260920_current_v1`.

Keep all eight cases, literal witness predicates, controls, predictions, and
stop rules from the original design. Change only the source fields:

- Generate a new wide field through U576, the preregistered first readiness
  stage for the direct target proof in `positive_double`.
- Inspect it at U16, U144, U300, and U576. These are checkpoints of one new
  field, not independent samples or a historical holdout.
- Generate a separate U80 field with `max_abs_p=200`, `max_abs_q=200`,
  `max_abs_value=4`, and confirmed edges retained, as a current retention
  control. It is not the original U80 blob.
- Wide settings: `max_abs_p=1000000000`, `max_abs_q=576`,
  `max_abs_value=1000000000`, confirmed edges retained; no edge/time limit.

Store new inputs under `out/scratch/shell_composition_20260920_current_v1/`.
Bind paths, configurations, source hashes, generation summaries, input hashes,
and checkpoint roles in a retained manifest under `research/geometry/results/`.
These current-generator calibration files are reproducible disposable inputs;
the new report retains the selected exact graph records. They do not replace
the absent historical immutable inputs or alter their inventory hashes.

The probe must require an explicit manifest for this mode, verify its source
and input hashes, and open the resulting inputs read-only. It must not fall
back automatically from missing historical inputs to new ones. Bind both this
amendment and the original design into the new report.

## Claim boundary

The measured outcome can establish which fixed motifs are retained in these
new, named positive-spine fields. It cannot establish historical reproduction,
independent validation, privileged circular structure, or a residual timing
law. Report the original frozen-input audit as unavailable, regardless of the
current calibration outcome. Stop after checking the registered predictions.
