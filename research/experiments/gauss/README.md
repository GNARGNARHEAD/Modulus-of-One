# Gauss-Framed Reports

This directory holds Gauss-framed saved outputs for integer congruence and
quadratic-form scrutiny through modulus one.

## Retention Boundary

The committed experiment record keeps both the human interpretation and the
machine-readable evidence:

```text
README.md
*.pre.md
*.analysis.md
*.json
```

Scored and frozen JSON reports are retained, including negative results. The
preregistrations freeze the questions and controls; the analyses preserve the
verdicts; and the machine reports retain the exact fibres, witness rows,
predictions, null records, configurations, and source identities needed to
audit those verdicts.

Only `*.sqlite` corpora remain ignored. They are immutable research inputs, not
disposable generated files. Their exact paths, sizes, hashes, graph counts, and
current reproducibility limits are recorded in [CORPUS_INVENTORY.md](../CORPUS_INVENTORY.md). A
fresh checkout must restore and verify the relevant corpus before rerunning an
analysis.

The congruence calibration artifact is:

```text
gauss_congruence_quotient_u300_v1.json
```

It projects the integer shadow of
`out/experiments/pascal_edge_probe_u300.sqlite` through moduli
`1,2,3,4,5,6,8,12` at ten stage checkpoints. The report retains source edge
occurrences and epistemic status fields rather than replacing them with a
deduplicated residue graph.

Interpret it with:

```text
research/number_theory/GAUSS_CONGRUENCE_AND_MODULUS_ONE_LENS_NOTE.md
```

The modulus-one one-node/one-loop topology is a forced negative control. It is
not a structural discovery. Only exact source-fiber evidence can support a Modulus of One
observation.

The quadratic-form experiment is:

```text
gauss_quadratic_forms_d20_u300_v1.pre.md
gauss_quadratic_forms_d20_u300_v1.json
gauss_quadratic_forms_d20_u300_v1.analysis.md
```

It uses Gauss determinant `-5` (modern discriminant `-20`) at form bound
`N=200`, censors graph evidence to the `U=200` prefix of the saved `U=300`
corpus, audits every representation shadow and normalized composition event,
and then applies the exact projection `n -> 0 in Z/1Z`.

The result is a decorated-fibre finding, not a nontrivial quotient: 552 signed
two-class witnesses reduce to 276 proper-automorphism orbits, then 113
represented integers, then one residue. Read the paired analysis with
[QUADRATIC_FORMS_CLASS_CHANNEL_LENS_NOTE.md](../../number_theory/QUADRATIC_FORMS_CLASS_CHANNEL_LENS_NOTE.md).

The confirmatory nested class/genus experiment is:

```text
durable review record:
gauss_nested_class_genus_ablation_u850_v1.pre.md
gauss_nested_class_genus_ablation_u850_v1.analysis_manifest.json
strict_stage_u850_holdout_v1.provenance.json
strict_stage_u850_holdout_v1.summary.json
gauss_nested_class_genus_ablation_u850_v1.json
gauss_nested_class_genus_ablation_u850_v1.analysis.md

ignored immutable corpus input:
strict_stage_u850_holdout_v1.sqlite
```

It freezes exact `Delta=-20`, `-23`, and `-56` form families before creating a
U850 holdout corpus, independently derives their `C2`, `C3`, and `C4` class
tables, and separates:

```text
decorated form witness
-> scalar arithmetic
-> label-free Modulus of One node neighborhood
-> residue panel
-> singleton Z/1Z endpoint
```

On the final `201..800` holdout, ordinary scalar arithmetic recovers the
`Delta=-56` genus split perfectly (`BA=1.0`). Adding graph features gives zero
lift. For the harder `A` versus `C` contrast inside one genus, the graph lift is
`0.0143` with matched-permutation `p=0.7809`; it is not promoted. The two
primary Holm-adjusted p-values are both `0.8079`.

The exact negative controls also pass. Inverse forms have identical
scalar-node observables and an exact `1/2` oriented-recovery ceiling. Every
bounded scalar composition shadow is present in the strict graph, but this is
full multiplication saturation rather than selective Gauss evidence. At
modulus one, genus and conditional class information are exactly zero and the
bare quotient has one node and one unlabelled relation.

Read [gauss_nested_class_genus_ablation_u850_v1.analysis.md](gauss_nested_class_genus_ablation_u850_v1.analysis.md) for the
interpretation. The machine report is deliberately large because it retains
exact fibres, class tables, composition events, predictions, and null records;
those rows make it part of the durable review surface. Its negative promotion
decision does not reduce its archival value.

## Local Reproduction

The congruence and bounded `Delta=-20` reports can be emitted locally with:

```text
python3 -m moo.congruence_quotient_probe --db out/experiments/pascal_edge_probe_u300.sqlite --moduli 1,2,3,4,5,6,8,12 --pretty

python3 -m moo.quadratic_form_probe --db out/experiments/pascal_edge_probe_u300.sqlite --max-n 200 --graph-stage-cutoff 200 --composition-event-limit 10000 --pretty --with-checksums
```

The historical U850 corpus command is recorded verbatim in
`strict_stage_u850_holdout_v1.provenance.json`. It is shown here to document the
frozen run, not to authorize replacement of the existing database:

```text
python3 -m moo.strict_stage_moo --db out/experiments/gauss/strict_stage_u850_holdout_v1.sqlite --max-stage 850 --max-abs-p 1000000000 --max-abs-q 850 --max-abs-value 1000000000 --commit-every 25 --summary research/experiments/gauss/strict_stage_u850_holdout_v1.summary.json --quiet
```

With the exact frozen corpus restored and hash-verified, the confirmatory
analysis command is:

```text
python3 -m moo.quadratic_form_nested_probe --write research/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.json --pretty --quiet --with-checksums
```

These writers do not overwrite existing files. Do not replace the corpus,
report, or sidecars after a source or argument change; that would be a new
experiment, not a reproduction of this one. The retained report is not made
disposable by the availability of an analysis command.

## Historical Provenance After The Evidence Repair

The August 2026 shared frontier/retention repair intentionally changed the two
generator sources after this experiment was frozen. The untouched provenance
sidecar records:

```text
moo/graph_corpus.py
  frozen  5f863dc297b3b2136fa76835d13067ae41206a150885dd37ba2bb49da5532c1f
  current 87a7ef9b864100e44d0941903ef1b7d66ad2f13d05892c2ac1c00ca7e9619ece

moo/strict_stage_moo.py
  frozen  e91574e0df7c573ec6e36d56dfbe5c779da632108d631ec22b4d2196acfc099b
  current 362175c960bc4d5e2c909a7c97ffcf7e2065a1ec75cec9b6c2f2c18a2044d0c3
```

This is expected provenance drift, not a reason to rewrite the historical
record. The old database/report remain bound to the frozen hashes. Running the
repaired generator would create a new corpus and therefore requires a new
experiment id, preregistration, manifest, provenance file, report, and analysis.
