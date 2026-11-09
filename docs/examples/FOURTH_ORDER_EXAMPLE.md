# Square-Branch Comparisons And A Proposed Irrational Limit

> Status: illustrative reading of existing research.
> Evidence layer: `external_probe`. Claim status: `lead` for the projected
> form; the finite witness checks remain observations.

The [branch-rhythm study](../../research/dynamics/BRANCH_RHYTHM_20261002.analysis.md)
asks how constructions agree, miss and approach agreement under continuation.
Here the comparison is a square against twice another square. Exact nonzero
agreement is impossible for rational roots, including fractional ones. Yet
selecting integer-root cases that differ by exactly one exposes a recurrence
whose relative discrepancy becomes arbitrarily small.

This is a way to understand a proposed irrational form through relations among
constructions. The selection needs no supplied decimal value of the limit.
The [shell/ratio example](BRANCH_INSPECTION.md) shows what an exact agreement
can enable; this example studies a controlled approach without agreement.

## What The Construction Shows

Three examples have complete integer witness bundles in the retained graph:

| Integer roots `(n,m)` | Square `n*n` | Doubled square `m*m + m*m` | Ratio `n/m` | Complete comparison available |
| --- | ---: | ---: | --- | --- |
| `(1,1)` | 1 | 2 | `1` | `U2` |
| `(3,2)` | 9 | 8 | `3/2` | `U9` |
| `(7,5)` | 49 | 50 | `7/5` | `U50` |

The square falls below, then above, then below the doubled square. The raw
miss stays exactly one. Relative to `m*m`, however, its magnitude is `1`,
`1/4`, then `1/25`. This normalization is essential: the integer difference
itself is not shrinking.

The witnesses obey the same operand rule as the [runtime walkthrough](WORKED_INSPECTION.md).
For `(3,2)`:

```text
U2:  2 * 2 -> 4
U3:  3 * 3 -> 9
U4:  4 + 4 -> 8
U9:  9 - 8 -> 1
```

`4` must be confirmed before it can supply the doubling. Both `9` and `8`
must be confirmed before the subtraction is available. The ratio `3/2`
already appears at `U3`, and the normalization `1/4` at `U4`; neither arrival
means the complete comparison has been witnessed yet.

These are inspected relations within the full operation field. The selector
does not replace that field with a special recurrence. Fractions are not
squared or reused as runtime operands. Integer certificates support the
comparison; signed normalized expressions below are analysis of those records.
The positive magnitude `1/25` and the integer defect `49 - 50 -> -1`, for
example, have separate witnesses.

## What Supports Looking Beyond These Cases

The original study checked the recurrence

```text
(n,m) -> (n + 2m, n + m)
```

from `(1,1)`. If `Q(n,m) = n*n - 2*m*m`, direct expansion gives

```text
Q(n + 2m, n + m) = -Q(n,m).
```

Thus the discrepancy alternates between `-1` and `+1`. The positive integer
`m` grows without bound under the recurrence. As an algebraic inspection of
the ratios, this says

```text
(n/m)^2 - 2 = +1/m^2 or -1/m^2.
```

The relative discrepancy therefore becomes arbitrarily small if the admitted
construction is continued. This is an exact conditional argument, stronger
than extrapolating from three examples. The study also gives a descent proof
that this recurrence exhausts the positive integer unit-discrepancy solutions.
It is a classical relation explicitly chosen for inspection; the evidence
does not establish that Modulus of One uniquely selects or privileges it.

No rational ratio can make the discrepancy zero. In lowest terms, an equality
`n*n = 2*m*m` would force both `n` and `m` to be even, contradicting lowest
terms. The recurrence supplies increasingly close relations while retaining
that distinction between finite agreement and proposed completion.

## Where The Fourth-Order Step Occurs

The fourth-order proposal is a **common limiting form** organizing these
rational comparisons. In conventional mathematics that positive form is named
`sqrt(2)`. It is algebraic irrational, not transcendental.

The finite constructions, their recorded differences, and the conditional
recurrence identity are available before granting that completed form. If
ordinary real completion is admitted, the positive ratios converge to the
unique positive solution of `x*x = 2`: their squared discrepancies tend to
zero. That is a theorem within those additional assumptions. It does not
insert a completed limit into the finite Modulus of One graph or establish it from the
immediate `1` alone.

In Modulus of One, the proposed form therefore remains an object of fourth-order
inspection. It names what the relationships suggest beyond any finite stage,
while the witnesses retain what has actually been constructed. It supplies
neither a new operand nor permission to reuse speculative fractions. Likewise,
the shrinking rational discrepancies do not establish a nonzero infinitesimal.

This makes the epistemic step visible without claiming a new discovery of
`sqrt(2)` or a validated Modulus of One-specific projection. The example illustrates the
meaning of fourth-order inquiry; it does not satisfy every stronger research
claim that such an inquiry could make.

The [circle-area comparison](../../research/geometry/AREA_INSPECTION_BRANCH_20261001.analysis.md)
offers a more elaborate continuation toward `pi`, with certified shrinking
bounds. It also requires an explicit Euclidean region and area measure, and
most of its larger graph certificates remain predictions. The older
[constant-selected chains](../../research/strict_stage/CONVERGENCE_STRUCTURE_NOTE.md)
have a purged source ledger and outstanding matched controls. The square
comparison's small integer certificates make it a useful algebraic companion;
the [pi account](PI_FOURTH_ORDER_EXAMPLE.md) develops the more elaborate
geometric interpretation with its assumptions and evidence limits explicit.

## Evidence And Projection Record

The [editorial evidence extract](evidence/fourth_order_square_example_20261107.json)
records the source identities and 28 distinct witnesses used here. The displayed
`n/m` division edges were checked directly in SQLite as a supplementary
readback; they were not all requested in the original report.

The [projection protocol](../protocols/order4-projection.md) requires the
following distinctions. This is a retrospective illustration of existing work,
not a new preregistered projection experiment.

| Field | This example |
| --- | --- |
| Name and status | Square-comparison limiting form; `external_probe / lead`. |
| Source family | Unit-discrepancy pairs in the existing branch-rhythm report, with exact integer operation witnesses in its named U160 corpus. |
| Selection rule | Positive integer `n,m` with `abs(n*n - 2*m*m) = 1`; original exhaustive scan used `m <= 512`. The coefficient 2 and relation were explicitly chosen. |
| Projection rule | Inspect `n/m` through its relative square discrepancy; interpret the unbounded continuation using an explicitly admitted completion. |
| Primary metric | Existing study checked exact unit discrepancy, recurrence coverage, and graph-stage predictions. There is no new preregistered projection score. |
| Graph evidence | First three complete comparison bundles observed at `U2`, `U9`, `U50`; node and edge IDs retained in the extract. |
| Stability checks | Original rational rescalings preserve relative discrepancy while retaining distinct raw witnesses and costs. |
| Controls | Rational-square coefficient comparisons and neighboring pairs; some neighbors return to the same primitive family after reduction. These do not establish special predictive power for the projected name. |
| Holdout | Original `m=33..512` continuation followed the fixed design; it is a deterministic continuation check. No independent projection-specific holdout was tested. |
| Prediction | The stated recurrence alternates the unit discrepancy and reduces its relative magnitude. Ordinary algebra explains this; no extra graph timing law follows. |
| Kill rule | Missing or ineligible witnesses invalidate a claimed recorded comparison. A stronger Modulus of One-specific projection claim needs independent controls it has not yet passed. |
| Allowed use | Explain how finite witnessed relations motivate a fourth-order proposed form. |
| Disallowed use | Claim a completed strict node, native irrational operand, infinitesimal, transcendental construction, or demonstrated advantage over matched projection controls. |

The re-audit on 7 November 2026 reproduced the original report byte-for-byte.
Its independent verifier checked 1,013 arithmetic requests and reread all 648
recorded edges; all six focused tests passed. The source corpus remained
unchanged. Only the first three full discrepancy bundles are present in that
U160 corpus. Later full comparison stages, beginning at `U289`, are predictions
under extended bounds, even where some earlier root transitions are recorded.

## Inspect A Fresh Small Field

The historical input is a local ignored database. A fresh checkout can build
all the finite witnesses in the table without it. From the repository root,
choose a new path:

```sh
python3 -m moo.strict_stage_moo \
  --db out/scratch/fourth_order_example_v1.sqlite \
  --max-stage 50 --max-abs-p 2500 --max-abs-q 50 \
  --max-abs-value 2500 --quiet

python3 -m moo.graph_query \
  --db out/scratch/fourth_order_example_v1.sqlite \
  --node 7/5 --limit 8 --pretty
```

These bounds retain every result of the four operations on `1..50`. This
fresh demonstration was checked against all 10,000 arithmetic witnesses,
plus the seed, and the 28 selected witnesses. Its node and edge IDs belong to
that newly generated corpus; historical IDs must be read against their own
source. The [original analysis](../../research/dynamics/BRANCH_RHYTHM_20261002.analysis.md#reproduction-and-retained-artifacts)
provides the full-study reproduction and verification commands.
