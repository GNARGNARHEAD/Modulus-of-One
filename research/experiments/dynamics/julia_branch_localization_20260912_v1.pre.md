# Julia branch localization: finite calibration v1

Frozen before measurement on 2026-09-12 (local time).

## Question and status

Where can quadratic Julia dynamics be attached to exact MoO construction
witnesses, and which distinctions would a graph-based inspector need to retain?

Evidence layer: `external_probe`, with individually queried `strict` edges.
Claim status: exploratory calibration / observation. No promotion of a Julia
set, new branch, chaos claim, or graph-specific predictive effect is allowed.
The earlier conversation already inspected the q=7, seed=1 doubling example;
it is prior motivation, not a held-out discovery.

## Corpus paths and configurations

- `out/experiments/pascal_edge_probe_u300.sqlite`: primary U300, p/value bounds
  1e9, q bound 300, confirmed edges retained.
- `out/experiments/circle_as_one_u40_wide.sqlite`: U40, p/q bounds 200, value
  bound 40, confirmed edges retained.
- `out/experiments/circle_as_one_u80.sqlite`: U80, p/q bounds 200, value bound 4,
  confirmed edges retained.

The machine report must capture actual config/schema metadata, source and
corpus hashes, and before/after equality of corpus hashes. Open each input
read-only with SQLite `mode=ro&immutable=1`.

## Exact commands

From the repository root in PowerShell:

```powershell
& 'C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B out/experiments/dynamics/julia_branch_localization_20260912_v1.analysis.py --self-check
& 'C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B out/experiments/dynamics/julia_branch_localization_20260912_v1.analysis.py
```

The script refuses to overwrite an existing report. This source is an
experiment-local inspection instrument, not a new runtime module.

## Frozen cases

1. Numerator self-addition and self-multiplication, seed 2, four steps, fixed
   denominators 2 through 16 and 31. Retain every primitive integer witness and
   every division-output witness. Compare the exact phase maps separately.
2. Independent doubling-period baseline for seeds 1 and 2 at the same
   denominators: reduced denominator 2^s*m, transient s, period ord_m(2), with
   period 1 when m=1.
3. Scalar recurrence certificates: (seed,c)=(1,0),(2,-2),(1,-1),(1,1), and
   (1/2,0). Use four steps except the fractional case (three), stopping at an
   exact repeat. Normalize negative real offsets as subtraction of |c| and
   omit a zero offset. This normal form is an explicit witness choice.
4. Parameter-selected fixed-point controls m=1..6, c=m-m*m. Compare the
   witnessed return at m with the external critical orbit starting at zero.
   These parameters deliberately force fixed points; their existence is not
   a discovery or a measure of MoO-specific structure.
5. External critical orbits for c=0,-1,-2,-6,1,1/4,1/2,i, eight steps, exact
   rational component arithmetic. Detect exact cycles and escapes beyond
   max(2,|c|). Otherwise retain `unresolved_after_budget`. Record a separate
   invariant-interval boundedness argument for c=1/4.
6. Representative-change negative control: 1/3 and 4/3 have identical phase
   but different squared phase. Do not confuse rational squaring with complex
   squaring after phase projection.

## Metrics, checkpoints, and controls

Checkpoints: U2,U4,U8,U16,U40,U80,U256,U300, only within each corpus's last
complete frontier. Presence is scoped by actual edge stage; a corpus-wide node
or edge payload is not automatically a checkpoint observation.

Primary metric: consecutive declared recurrence steps with every required
primitive edge retained by a checkpoint. For phase returns, also require all
division-output witnesses through the first repeated projected phase.

Secondary metrics: exact residue preperiod/period, earliest witness stages,
field-rule blockers, retention blockers, and confirmation status.

Controls: analytical denominator baseline; alternate numerator operator;
changed representative; parameter-forced fixed points; narrow corpus bounds;
finite non-escape versus an independent boundedness certificate.

Multiple comparisons: descriptive exhaustive reporting of declared cases;
no significance testing, rankings, or post-selected promotion thresholds.
Validation corpora are aperture comparisons, not independent statistical
holdouts. Self-checks cover known exact cycles, escape, unresolved status,
phase periods, and arithmetic/operand status of returned graph witnesses.

## Decision rules and limits

Promotion rule: none in v1. A useful result is a precisely delimited inspection
lead with exact witnesses and clear external projection rules.

Kill/downgrade rule: no retained witness means no witnessed branch claim;
known generator/retention exclusions must not be called graph-specific
absence. A cycle in a quotient is not a runtime rational cycle. A repeated
edge certificate is not a log of infinitely many runtime events. Boundedness
is not attraction, and a finite unresolved trajectory is not membership in a
completed Julia or Mandelbrot set.

Allowed language: exact finite calibration; witnessed integer relation;
external phase return; partial recurrence certificate; prospective inspector.

Disallowed language: MoO constructs a Julia/Mandelbrot set; a new branch or
chaotic effect was discovered; speculative operands were promoted; these
target-selected examples predict previously unseen strict graph structure.
