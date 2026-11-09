# Running And Checking Modulus of One

Run commands from the repository root. Python tools are modules in `moo/`;
use `python3 -m moo.<module>` rather than executing a file inside that package.
The [source guide](../../moo/README.md) maps the main entry points. The runtime, SQLite graph tools, node
profiles, walkthrough, and automated tests use the Python standard library.
The November 2026 review checked them with Python **3.14.4** in a fresh virtual
environment without installed packages. That is a tested environment, not a
claim that every Python version has been checked.

```sh
python3 tools/moo_walkthrough.py
```

The [runtime walkthrough](../examples/WORKED_INSPECTION.md) explains those
confirmation and witness checks and how to keep the evidence. For a fresh
field showing a mathematical use of branch inspection, follow the
[shell/ratio investigation](../examples/BRANCH_INSPECTION.md#inspect-a-fresh-field).
The original expression-oriented runtime is also available:

```sh
python3 -m moo.constructionist_math --confirm-through 2 '1/(1+1)'
```

That command prints the exact result `S(1/2)` together with extensive
construction, acceptance, JSON, and graph details. `S` records its speculative
status under the model's operand rule.

`--confirm-through 2` explicitly advances counted recurrence before evaluating
the expression. Expression evaluation itself never confirms an arithmetic
result. Without that option a new graph has only `1` confirmed: `1+1` returns
speculative `2`, and reusing it in `1/(1+1)` is rejected. In Python, use
`graph.advance_frontier_max_to(n)` before `eval_moo(expression, graph=graph)`.
The expression tool records selected constructions; use the walkthrough or
stage-corpus generator to inspect the full four-operation field.

## Tests

The [five-fix record](../../archive/reviews/FIVE_FIXES_20261106.md) describes the confirmation and
branch-report contracts added after the point-by-point critique. Branch reports
now identify their revised output as `branch_lineage.v4`.

All tests, including the geometry and dynamics checks, now have one discovery root:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

An isolated environment can be created with `python3 -m venv --without-pip`
and an unused directory as its final argument. Use that environment's Python
for the commands above. No package installation is required for these checks.

Some historical plotting scripts use `matplotlib` or Pillow. These are
optional analysis dependencies, needed only for those scripts; they are not
required to read the philosophy, construct a graph, or run the test suite.

## Fresh Demonstration Versus Historical Reproduction

Source code and saved reports are in the repository. Large SQLite inputs are
ignored by Git. A fresh clone can generate new examples, but it does not
contain every historical input needed to rerun the research reports.

Use the [corpus inventory](../../research/experiments/CORPUS_INVENTORY.md) to distinguish
known source identities, missing historical inputs, and surviving local
calibrations. Generate new corpora at new paths. The generator refuses to
overwrite an existing database.

Some experiments deliberately require an exact historical environment. The
nested quadratic-form analysis, for example, requires Python 3.12.13 and
hash-matched analysis sources. Running the general test suite on 3.14.4 does
not satisfy that reproduction contract. Its audit tests exercise acceptance
and rejection of runtime versions without weakening the production guard.

Frozen reports, preregistrations, source manifests, and surviving input
databases retain their identities. Changed code or configuration produces a
new experiment, with its own outputs. The
[experiment guide](../../research/experiments/README.md) explains this evidence rule.

## Local Outputs And Preserved Sources

Write new runs under a new path in ignored `out/`. Saved, reviewed experiment
records live in `research/experiments/` or the owning program's `results/` tree.
Do not write over those records. A changed source, configuration or protocol
requires a new experiment identity and its own provenance.

**Do not treat all of `out/scratch/` as disposable.** The separately named
U576/U80 shell-composition calibration databases survive there and are listed
in the corpus inventory. Preserve those inputs and the U160 area-inspection
source at their recorded paths; relocating tracked reports does not relocate
or recreate a database. Remove only outputs you have identified as disposable.

Frozen reports and dated analysis programs keep the paths and source hashes
from their original runs. To reproduce those runs, recover the identified
source revision and environment as well as the inputs; current imports are
not hash-identical historical sources. The
[layout record](../../archive/reorganizations/20261107/README.md) explains how to
locate moved files. Frozen source guards still reject a mismatch.
