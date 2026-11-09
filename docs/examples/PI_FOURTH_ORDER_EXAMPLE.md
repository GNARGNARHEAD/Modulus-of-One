# Circle Squaring, Area Inspection And A Proposed Pi Boundary

> Status: conditional illustration from existing research.
> Evidence layer: `external_probe`. Claim status: `lead` for the projected
> form; the recorded arithmetic and finite geometric checks remain observations.

The [area-inspection research](../../research/geometry/AREA_INSPECTION_BRANCH_20261001.analysis.md)
asks which rational-square constructions can be certified below or above an
area. Progressively tighter comparisons expose a persistent separation within
the branch. Under the geometric interpretation used here, its proposed common
boundary is conventionally named `pi`.

We explicitly admit a Euclidean unit disk, containment and additive area as
an inspection framework. The disk is a chosen geometric target; its numerical
area is not supplied. This continues the inspection of
[rational shell relationships](BRANCH_INSPECTION.md) by adding those geometric
commitments. Modulus of One has not derived them from the immediate `1`.

## The Equal-Area Question

Squaring the circle was a motivating question for the original inquiry,
within the broader problem of finding areas under curves. For a disk of
positive radius `R` and a square of positive side `s`, the equal-area question becomes, after
normalizing lengths by `R`,

```text
h*h = A,     h = s/R,
```

where `A` is the unit-disk area. The construction task is to obtain evidence
about the area and compare square constructions with it. Writing the equation
alone supplies neither that evidence nor a method of finding its side.

The [equal-area study](../../research/geometry/CIRCLE_SQUARE_AREA_BRIDGE_20260911.analysis.md)
uses rational polygons to enclose the area, then tests rational square sides
against those bounds. It records a path of certified comparisons. This is
the sense in which the work investigates circle squaring: the equal-area
question guides inspection and refinement. It does not claim an exact finite
solution to the classical compass-and-straightedge problem.

## Inspecting The Square Branch

A rational square has a construction to inspect. For a positive rational
root `p/q`, with positive integers `p,q`, self-products `p*p -> P` and
`q*q -> Q`, together with quotient witnesses, support the square value `P/Q`.
This includes fractional squares while obeying the current positive-integer
operand rule.

Let valid rational bounds satisfy `L_N <= A <= U_N`, where `A` is the chosen
area. They let us classify a square value `v`:

- `v < L_N` certifies it below the area.
- `v > U_N` certifies it above the area.
- A value remaining between the bounds is unresolved until further evidence
  settles it; equality needs its own certificate.

At the refinement with `14/5 <= A <= 10/3`, for example,
`(3/2)^2 = 9/4 < 14/5`, while `2^2 = 4 > 10/3`. Exact integer cross-products
certify those comparisons. Refinement allows closer square values to be
classified without treating an approximation to `pi` as the target value.

The original study compared 648 distinct rational-square values using exact
polygons, outward-rounded polygons and grid covers. Its argument establishes
that any valid shrinking-bound methods eventually classify every value
unequal to `A` on the same side. Their witnesses and refinement costs can
still differ. The proposed boundary thus organizes a family of comparisons.

For the unit disk, the boundary in **square values** is classically `pi`; in
square **roots** it is `sqrt(pi)`. These are different quantities. The finite
checks, conditional continuation and fourth-order interpretation are set out
below. Refinement index `N` is separate from the graph stage `U_n`.

## Following The Square-Side Brackets

The earlier study maintains lower and upper rational side bounds and tests
their mediant. If the candidate's square is below the area lower bound, the
lower side advances. If it is above the area upper bound, the upper side
retreats. If neither comparison is settled, refine the area bounds first.

The recorded path includes:

| Candidate square side | Certified comparison with the disk |
| --- | --- |
| `7/4` | Square area too small |
| `16/9` | Square area too large |
| `23/13` | Square area too small |
| `39/22` | Square area too large |

These decisions use exact rational comparisons with geometric enclosures;
no numerical value of `pi` or `sqrt(pi)` selects the side. Under the ordinary
geometric interpretation the proposed equal-area side is `sqrt(pi)`, and
every rational side remains distinct from it. Finer brackets give more
information without declaring an unresolved finite comparison to be equality.

The area-4 square control returns side `2` exactly. Equality is therefore a
possible outcome when an appropriate finite certificate exists.

## Finite Constructions We Can Inspect

Begin with the four axis points on the unit circle. Their inner diamond has
area 2; the square formed by their tangent lines has area 4. Add the rational
point `(3/5,4/5)` in the first quadrant and repeat the quarter construction
around the disk. The inner and outer polygon areas become `14/5` and `10/3`.
The disk lies between them under the admitted geometry.

Let `A` name the area being inspected:

| Refinement `N` | Exact rational bounds on `A` | Arithmetic certificate in the retained U160 graph |
| --- | --- | --- |
| 1 | `2 <= A <= 4` | All 14 requested edges recorded; specified bundle complete at `U4`. |
| 2 | `14/5 <= A <= 10/3` | All 61 requested edges recorded; specified bundle complete at `U64`. |
| 4 | `6486/2125 <= A <= 2209/693` | 124 of 149 requested edges recorded; full bundle at `U6486` is a prediction. |

`N` counts subdivisions of each quarter's rational parameter interval. It is
not the graph stage `U_n`. The table distinguishes exact rational calculation
from a complete recorded witness bundle.

The `N2` lower-area contributions are `8/5` and `6/5`. Their sum is encoded
through integer operations, including `8 + 6 -> 14` at `U8` and
`14 / 5 -> 14/5` at `U14`. The upper bound has a direct quotient witness
`10 / 3 -> 10/3` at `U10`. These early value arrivals do not complete the
whole geometric inspection's arithmetic certificate. That specified bundle
also checks the raw endpoint shells and their normalization, reaching `U64`.

All runtime operands are confirmed positive integers. Fractional coordinates,
areas, and formulas are inspected through integer encodings; the corpus has
no edge adding `8/5` to `6/5` as speculative operands. Zero-coordinate cases
are simplified externally and recorded explicitly by the inspection code.

The earlier [hand-built calibration](../../research/geometry/square_area_inspection.py)
reaches the same bounds with a different bundle at `U40`. Neither checkpoint
is claimed to minimize every possible certificate. Geometry, containment, and
the area rule remain interpretive assumptions; the graph checks arithmetic.

## Why The Boundary Is More Than A Decimal Guess

The existing refinement uses exact rational points

```text
P(t) = ((1 - t*t)/(1 + t*t), 2*t/(1 + t*t))
t = k/N,  k = 0,...,N.
```

Joining neighboring points supplies an inner polygon; neighboring tangent
lines supply an outer one. For adjacent parameters `a=k/N`, `b=(k+1)/N`, put

```text
w = (b-a)/(1+a*b) = N/(N*N + k*(k+1)).
```

The contributions across the four quadrants are `4w/(1+w*w)` below and `4w`
above. Their difference is `4w^3/(1+w*w)`. Since `0 < w <= 1/N`, summing the
`N` pieces gives

```text
0 <= upper(N) - lower(N) <= 4/N^2.
```

Thus the admitted disk area lies between rational bounds whose separation
becomes arbitrarily small. The ordinary geometric and completion assumptions
support the common limit. The proof supplies the continuation argument; a
finite collection of increasingly accurate decimals would not do so alone.

The [earlier large finite calculation](../../research/geometry/CIRCLE_SQUARE_AREA_BRIDGE_20260911.analysis.md)
also gives these exact outward rational bounds:

```text
3.141592653251708049438716 <= A <= 3.14159265375883583300936
```

This uses `N=65536` and rounds each contribution outward to denominator
`10^24`. The extra rounding width is at most `2*N/10^24`. These are finite
external arithmetic results, not complete recorded graph certificates at
that scale. The unrounded family above supplies the convergence proof;
a fixed rounding denominator is not asserted to converge as `N` grows forever.

## The Connection To Areas Under Curves

The independent grid method in the
[area-inspection study](../../research/geometry/AREA_INSPECTION_BRANCH_20261001.analysis.md#the-refinement-proofs)
is already an area-under-a-curve construction. In the first quadrant, the
upper circular arc bounds the region above the horizontal axis. Divide its
width into `N` rational columns. Integer squared-distance comparisons select
cell heights whose rectangles lie inside the region, and heights whose
rectangles cover it. Summing their rational areas gives lower and upper
bounds; multiplying by four covers the disk.

The method selects integer heights using `floor(sqrt(N*N-i*i))`. This is an
external search for an integer satisfying squared-distance inequalities,
not a new irrational runtime operand. The exact full-disk area gap is

```text
upper(N) - lower(N) = 4*(2*N-1)/(N*N).
```

That gap tends to zero under continuation. The grid and polygon methods
therefore give different finite constructions for inspecting the same area.
Their costs and witnesses differ, while their valid shrinking enclosures
eventually settle the same unequal square-area comparisons.

The broader area-under-curves inquiry asks how to obtain such certified
enclosures for other curves and establish that their gaps shrink. A general
method would need to specify its class of curves, region, and refinement
assumptions. The documented circle construction supplies a concrete case
and an inspection strategy to develop further.

## The Fourth-Order Interpretation

The proposed common area boundary is a hypothetical fourth-order form within
Modulus of One. In conventional Euclidean mathematics, unit-disk area is `pi`, a
transcendental number. Its classical identification and transcendence are
knowledge brought to the interpretation; the finite bounds do not prove
transcendence.

The graph retains the exact rational witnesses supporting the comparisons.
Naming their proposed area boundary `pi` adds no runtime node, and no later
positive-spine stage confirms it. The conditional convergence theorem
remains a theorem under its assumptions; those assumptions do not inherit
the immediate certainty of `1`.

The proposed form can organize further inspection while leaving the witness
families intact. Finite comparisons continue to establish which constructions
are definitely below or above; interpreting their common boundary does not
replace those comparisons with an assumed irrational operand.

### Where Tau Fits

With the convention `tau = 2*pi`, doubling the rational bounds gives

```text
4 <= 2A <= 8
28/5 <= 2A <= 20/3.
```

This can be encoded by doubling integer numerators and then taking quotients.
For example, `2 * 14 -> 28` and `28 / 5 -> 28/5` use confirmed integers;
no operation on a completed `pi` is needed. The supplemental witness check
records these finite encodings.

`Pi` is the direct name for the quantity this experiment measures. `Tau`
is an equally transcendental rescaling of its proposed boundary. These bounds
do not independently construct circumference, angle, or a full-turn metric.

## What The Controls Establish

The original study compared exact polygons, outward-rounded polygons, and
square-grid covers, and checked equivalent rational representations. Its
diamond and square controls give areas 2 and 4, showing that the inspection
can resolve rational cases. The common-boundary argument is conditional on
valid shrinking bounds; agreement between finitely many methods alone is not
its proof.

Area alone also cannot identify the circle. The area-preserving transformation
`(x,y) -> (2x,y/2)` sends the disk to an ellipse and preserves the scalar
polygon-area bounds. The disk therefore has to remain an explicit geometric
choice. No Modulus of One-specific preference for circles or predictive advantage of
the proposed `pi` form has been established.

## Projection And Evidence Record

This is a retrospective illustration, not a new preregistered experiment.
The [projection protocol](../protocols/order4-projection.md) applies as follows:

| Field | This example |
| --- | --- |
| Name and status | Unit-disk area boundary; `external_probe / lead` as a fourth-order illustration. |
| Source family | Rational shell coordinates and integer-encoded polygon/area comparisons in the existing fixed area-inspection study. |
| Selection rule | The Euclidean disk and rational subdivision `t=k/N` are explicitly selected; no numerical `pi` or trigonometric evaluation is supplied. |
| Projection rule | Interpret the common boundary of valid shrinking area enclosures using the stated geometry and completion. |
| Primary metric | Original width-versus-certificate-stage comparison and exact consistency checks; no new projection score. |
| Graph evidence | Complete `N1` and `N2` bundles; larger requested stages distinguished from recorded edges. |
| Stability and controls | Rescaling, independent shoelace/tangent checks, grid covers, diamond/square controls, and persistent classifications. The ellipse limits the geometric interpretation. |
| Holdout | Original `N16,32,64` and larger candidate denominators were deterministic continuation checks. No independent Modulus of One-specific projection holdout was tested. |
| Prediction | Unrounded width at most `4/N^2`; every unequal rational-square comparison eventually resolves under the admitted geometry. |
| Kill rule | Failed containment, conflicting definite comparisons, incorrect arithmetic, or an ineligible claimed witness invalidates the affected claim. A native-selection claim needs further controls. |
| Allowed use | Illustrate a hypothetical transcendental boundary supported by explicit finite constructions and conditional arguments. |
| Disallowed use | Derive Euclidean geometry or transcendence from `1`, promote `pi`/`tau` to an operand, or treat predicted certificates as stored evidence. |

The [editorial extract](evidence/pi_fourth_order_example_20261107.json)
preserves source identities, both complete bundles, and supplementary tau
encodings: 67 distinct historical witnesses. On 7 November 2026 the full area
report reproduced byte-for-byte; its independent verifier checked 10,468
arithmetic requests, reread 1,790 stored edges, and checked 98 intervals and
63,504 candidate comparisons. All 15 focused tests passed. Historical inputs
and reports remain unchanged.

A fresh small field suffices for the two complete polygon certificates and
the displayed tau encodings. From the repository root, choose a new path:

```sh
python3 -m moo.strict_stage_moo \
  --db out/scratch/pi_example_v1.sqlite \
  --max-stage 64 --max-abs-p 4096 --max-abs-q 64 \
  --max-abs-value 4096 --quiet

python3 -m moo.graph_query \
  --db out/scratch/pi_example_v1.sqlite \
  --node 14/5 --limit 8 --pretty
```

This fresh-field demonstration was checked against all 16,384 arithmetic
witnesses and the 67 selected witnesses. Historical edge IDs belong to their
named source; they are not transferred to a new corpus. Full-study reproduction
commands remain in the [original analysis](../../research/geometry/AREA_INSPECTION_BRANCH_20261001.analysis.md).
The [square-comparison example](FOURTH_ORDER_EXAMPLE.md) provides a simpler
algebraic illustration of the same epistemic distinction.
