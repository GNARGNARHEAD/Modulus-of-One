# Square-branch area inspection: frozen comparison

Date: 2026-10-01

evidence_layer: external_probe
claim_status: candidate

This design follows GNARGNARHEAD's clarification that the square branch includes
rational squares and that the inspection route, rather than a selected output,
is the question. It tests a possible definition boundary on that branch. It
does not change runtime operands, confirmation, geometry, or completion rules.

## Question and assumptions

Can independently specified finite area inspections consistently classify
rational-square constructions relative to a common area boundary, while their
different arithmetic costs and witnesses remain visible?

Use ordinary Euclidean coordinates, containment and additive area as explicit
external assumptions. The disk is x*x+y*y<=1, the diamond is |x|+|y|<=1, and the
square is [-1,1]^2. These geometric selectors are not derived from MoO. No pi,
sqrt(pi), trigonometric evaluation, or known approximation coefficients enter
selection or calculation.

## Methods fixed before measurement

1. Rational polygons. Use t=k/N, k=0..N and the rational unit-shell map
   ((1-t*t)/(1+t*t),2*t/(1+t*t)). Sum inscribed and tangent-polygon areas
   exactly. For adjacent a,b let w=(b-a)/(1+a*b); the four-quadrant
   contributions are 4*w/(1+w*w) and 4*w.
2. Rounded rational polygons. Compute those same contributions but round the
   lower down and upper up to denominator D=N^3. Record integer inequality
   certificates for rounding; floor/ceiling are selectors, not runtime
   primitives. This is a fixed third encoding, not an adaptive improvement
   selected after seeing the comparison.
3. Square grid. Count N by N first-quadrant cells certainly inside the shape
   or intersecting it according to their far/near corner tests; reflect to
   four quadrants. Circle row counts may use integer square root as an
   external selector only with squared-distance inequality certificates.
   Include touching cells in the upper cover, matching the earlier probe.

The polygon controls are exact boundary polygons for the diamond and square.
The grid controls use their respective corner predicates on the same grid.
They test whether the method automatically forces the circle's area.

N=1,2,4,8 are calibration levels. N=16,32,64 are reserved continuation levels.
This is a deterministic out-of-range check, not statistical independence.
At every level compare raw coordinate representations i/N and 2i/(2N).
For polygons this scales both raw parameter integers, preserving t. Do not
erase the additional source witnesses when fractions reduce to the same node.

## Arithmetic cost and graph boundary

Compile specified rational operations into positive-integer multiplication,
addition, subtraction and division, with final rational outputs inspected
rather than reused. Exact gcd reduction is selected externally and certified
by integer quotient/product relations. Use least common denominators in
addition and record the integer operations establishing them. Zero-coordinate
specializations are explicit external simplifications, never zero operand
edges. All nontrivial runtime operands are confirmed positive integers.

Cost is the largest operand in this named certificate: the earliest possible
positive-spine stage for that certificate under sufficient retention. Also
record unique arithmetic edges and the earliest quotient stage implied by the
reduced final rational bounds. This is not a minimum-cost theorem, time or
memory benchmark, or complete cost model for the external selectors.

Read the previous calibration's current U160 corpus without modification.
Audit every requested edge whose operands fit U160 and whose result fits its
retention bounds. Preserve edge IDs, nodes and confirmation status. Larger
requests remain exact admissibility certificates with predicted stages, not
claims of recorded edges in an unbuilt universe. Save source and corpus hashes.

Primary comparison: certified interval width against the certificate's stage
cost. Construct a nondominated width/stage table over the fixed tested levels.
Do not select pairs using proximity to an externally supplied pi.

## Branch comparisons and predictions

Enumerate reduced positive roots p/q<=2, q<=16, and compare their square values
against each interval. Mark below only when (p/q)^2<L, above only when
(p/q)^2>U, and exact only when L=U=(p/q)^2. Otherwise mark unresolved. Repeat
for the new q=17..32 roots as an out-of-range candidate check. These fractions
are the inspected objects; integer encodings do not exclude them from scope.

Persist at least one actual comparison certificate for each nonempty category
at each level, using cross-products and their difference. Keep their costs
separate from the area-bound cost. Preserve all candidate classifications.

Predictions to check:

- Equivalent representations produce identical intervals and classifications.
- Two valid methods never issue opposite definite classifications.
- A definite below/above comparison never reverses under refinement.
- Exact polygon width is <=4/N^2; rounded width is <=6/N^2.
- The inclusive circle-grid cover has width exactly 4(2N-1)/N^2.
- Grid controls contain their known exact areas 2 and 4; exact polygons
  return those areas. The square control recognizes the branch value 4.
- All auditable graph edges obey the existing positive-spine rule.

These are classical arithmetic/geometric predictions. Passing them establishes
the specified inspection's consistency, not an unexplained MoO law.

## Candidate definition and failure rules

Investigate an area-comparison boundary as two witness-indexed families:
square constructions eventually certified below the target by a finite lower
area bound, and those eventually certified above it by a finite upper bound.
An unresolved finite square is not an equality witness. Method independence
must follow from valid bounds and shrinking widths, not numerical agreement
at the finitely tested levels alone.

Any contradictory classification, failed containment/independent area check,
inadmissible claimed runtime edge or failed representation invariance rejects
the affected implementation or claim. A cost advantage that depends on the
selected encoding is explicitly limited to that encoding. A generic cut also
existing for controls cannot establish that MoO intrinsically privileges the
circle. No circle-specific native branch or completed irrational is promoted
by this experiment.

Save the implementation, exact certificate/report, focused independent checks,
analysis including negative findings, and a width-versus-stage figure.
