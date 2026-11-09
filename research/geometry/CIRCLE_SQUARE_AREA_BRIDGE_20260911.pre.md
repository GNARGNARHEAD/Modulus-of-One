# Circle / square area bridge: frozen design

Date: 2026-09-11

Question: does an independently specified equal-area circle/square condition
yield an exact-hit branch or a useful rigorously bounded candidate branch?

## Definitions fixed for this pass

- The circle is the boundary of the external Euclidean unit disk
  D={(x,y): x*x+y*y <= 1}. This geometry is explicitly admitted as an analysis
  lens; it is not claimed to have emerged as runtime semantics.
- Area is ordinary planar area, bounded by inscribed and circumscribed
  polygons and independently by inside/covering rational grid cells.
- A normalized square of rational side h=p/q has area h*h.
- An exact hit means h*h equals the disk area. Membership in a finite area
  interval is only unresolved compatibility, never an exact hit.
- No numerical pi, square root of pi, trigonometric functions, or known
  continued-fraction coefficients enter candidate generation or selection.

## Exact polygon family

Use rational boundary vertices P(t)=((1-t*t)/(1+t*t),2*t/(1+t*t)), with
t=k/N, k=0..N, reflected through four quadrants. The lower area is the
inscribed polygon area from cross products. The upper area is the polygon
formed by tangent intersections. Neither polygon is called a circle.

For consecutive parameters a,b, put w=(b-a)/(1+a*b). Contributions to the
whole-disk bounds are lower=4*w/(1+w*w), upper=4*w. For the uniform rational
grid, w=N/(N*N+k*(k+1)). The raw gap is at most 4/(N*N). Round every lower
term down and every upper term up on denominator 10^24. The resulting exact
rational gap is at most 4/(N*N)+2*N/10^24.

Scan N=1,2,...,65536 by powers of two. Levels through N256 form the initial
precision aperture; N512..65536 are refinements, explicitly not independent
random data. Intersect successive outward intervals to preserve nesting.

## Independent geometry check

For M=32,128,512,2048,8192, count unit-disk grid cells of side 1/M that lie
entirely inside, and cells that cover the disk. Use integer squared distances
and integer square roots only. The resulting area intervals must overlap the
polygon intervals; the finest polygon interval must lie inside each grid
interval. This is a different geometric construction of the area bounds.

Independently compute small N polygon areas from explicit rational vertices,
tangent-line intersections, and the shoelace formula to verify the simplified
contribution formulas. Do not use the contribution formulas as their own test.

## Candidate branch and controls

- Enumerate all reduced rational side ratios 1 <= h <= 2 with q <= 1000.
  Record how many remain compatible with each area interval and their exact
  values. This is a finite denominator envelope, not the entire rational line.
- Build a Stern-Brocot/mediant bracket path by exact square-versus-area-bound
  comparisons. Stop at an unresolved comparison or denominator-sum > 10000.
  Do not label the path an exact rational solution or a new recurrence law.
- Control areas: the diamond |x|+|y| <= 1 has area 2, and the square
  [-1,1]^2 has area 4. The square control must recognize an exact rational
  side 2. The diamond must follow its different square-root bracket.
- Record if coarse polygon bounds retain candidates which later refinements
  exclude. Such loss is evidence against treating finite-resolution hits as
  exact intersections.
- Explain the rational-closure obstruction to any finite exact rational
  equal-area hit, using the classical irrationality of the unit-disk area.
  This theorem is separate from the pi-free numerical construction.

## Return to graph evidence

Open preserved wide U300 and U1000 corpora read-only. Audit:

- The integer arithmetic and coordinate-quotient witnesses for all interior
  polygon vertices at N=2,4,8,16,32.
- Exact node and edge records for side ratios on the resolved bracket path,
  their numerator/denominator self-products, and the quotient of those squares
  when operand-ready. Keep absent and future-stage cases.
- Intended area addition/multiplication for the N2 polygon, distinguishing
  rational value landing from the forbidden use of speculative fractions as
  operands. A direct integer quotient is not the intended area recurrence.
- Strict alignment and before/after input hashes.

The primary comparison is exact-area compatibility versus precision and graph
witness eligibility versus operand size. Any effect fully explained by the
external geometry and positive-spine schedule is not a new MoO-specific law.

## Rejection and interpretation limits

Reject a claimed exact hit if it is only bracket-compatible. Reject a
graph-native area construction if the required fractional-operand recurrence
is absent. Reject a native circle discovery if the external Euclidean norm,
area rule, or completion step is being treated as internally established.

Useful outcomes include a certified approximation branch, a precise proof
that exact finite hits are absent under current rules, and an explicit map
of which construction/completion steps the current runtime lacks.
