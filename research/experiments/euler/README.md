# Euler-Framed Experiment Records

This directory holds compact records from completed finite-series and external
zeta calibrations over strict Modulus of One graph corpora. They are observation and
control studies, not runtime constructions of infinite series, complex
arithmetic, `pi`, or zeta zeros.

## Retention Boundary

The repository retains the complete scored or frozen experiment record:

```text
README.md
*.pre.md
*.analysis.md
*.json
```

The JSON reports are retained research evidence, including negative and
externally calibrated results. They contain the machine-readable node, edge,
control, configuration, and checksum rows behind the paired interpretations;
the prose is not a substitute for those rows.

Source `*.sqlite` corpora remain ignored because they are large immutable
inputs, not because they are disposable. Their exact paths, sizes, hashes,
graph counts, and current reproducibility limits are recorded in
[CORPUS_INVENTORY.md](../CORPUS_INVENTORY.md). Preserve those blobs in durable content-addressed
storage before cleaning this workspace or moving to another machine.

The current analyses cover:

- exact finite geometric, reciprocal-square, and Euler-product endpoints;
- finite external critical-line numerical calibration at a caller-supplied
  coordinate;
- graph-reveal ordering of the same fixed external Hasse source basis.

Read each `*.analysis.md` before using a local report. The analyses state the
operand, aperture, numerical, and claim boundaries that the raw payload alone
does not communicate.

## Local Reproduction

The finite-series comparison can be emitted to stdout from the repository
root with:

```text
python3 -m moo.series_probe --db out/experiments/pascal_edge_probe_u300.sqlite --geometric-ratio 1/2 --geometric-terms 8 --zeta-max-n 6 --euler-max-prime 7 --euler-local-geometric-terms 4 --pretty --with-checksums
```

The two external zeta controls can likewise be reproduced locally:

```text
python3 -m moo.zeta_critical_probe --db out/experiments/circle_as_one_u80.sqlite --sigma 0.5 --t 14.134725141734693 --hasse-terms 64 --control-delta 0.01 --near-zero-tolerance 1e-10 --stability-tolerance 1e-12 --target-kind user_supplied_reference_zero --target-label first_nontrivial_zero_coordinate --pretty --with-checksums

python3 -m moo.zeta_arrival_probe --db out/experiments/circle_as_one_u80.sqlite --sigma 0.5 --t 14.134725141734693 --hasse-terms 64 --stage-horizon 64 --control-delta 0.01 --height-control-ts 10,11,12,13,15,16,17,18,19,20 --envelope-guard 1e-12 --stability-tolerance 1e-12 --near-zero-tolerance 1e-10 --permutation-samples 4096 --target-kind user_supplied_reference_zero --target-label first_nontrivial_zero_coordinate --full-scan --pretty --with-checksums
```

The retained JSON reports are immutable records. Use `--write` only with a new
path and experiment identifier when creating a genuinely new run; report
writers refuse to overwrite existing files. The paired U1000/U300,
U80/U40-wide, and U80/U300-broad comparisons use different source corpora; do
not pool them or describe an aperture change as a graph effect. A reproduction
command does not make a saved scored report disposable.
