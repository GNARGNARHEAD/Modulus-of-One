# Equal-area circle / square bridge: a limit path, no finite rational hits

Date: 2026-09-11

Evidence layers: external exact Euclidean area bounds; read-only strict graph
precursor audit. Claim status: certified external bounds with an explicit
runtime boundary.

This pass did not find an exact equal-area hit branch among rational lengths.
It produced a certified approximation path and identified why the earlier
shell branch does not supply such hits. For a nonzero rational radius and a
rational square side, equal Euclidean area is impossible. This is an
arithmetic obstruction, not just a limited search depth.

The computation obtained its area bounds without a supplied value of pi,
sqrt(pi), any trigonometric function, or known continued-fraction coefficients.
It uses a declared external Euclidean disk and area rule. It does not claim
that MoO has internally defined that disk, area, or a completed irrational.

## What this pass tested

The earlier experiment used x*x+y*y=r*r as a provisional shell hit. That is
an identity between squared lengths. Its parameter t describes a boundary
point after radius normalization. It does not specify the area of a circle.

Here the circle is explicitly the boundary of the external unit disk
D={(X,Y): X*X+Y*Y <= 1}. A positive square side h has area h*h. The target is

```text
h*h = Area(D).
```

For an arbitrary radius R and side s, h=s/R. Scaling removes the overall
size. In conventional notation Area(D)=pi and h=sqrt(pi), but neither target
number is an input to the algorithm.

The geometry, filled polygons, area measure, and completion are external
assumptions. A finite or countable set of graph coordinates alone is not the
filled disk. The experiment makes this distinction explicit instead of
renaming the shell predicate as a circle-area construction.

## Independent construction of the area bounds

Use the rational boundary parameter from the earlier work:

```text
P(t) = ((1-t*t)/(1+t*t), 2*t/(1+t*t)),  t=k/N, k=0..N.
```

Reflect the quarter boundary through all four quadrants. Joining consecutive
vertices makes an inscribed polygon. Intersecting consecutive tangent lines
makes a circumscribed polygon. Both have exactly rational coordinates and
rational areas. The first lies inside the disk; the second contains it.

For consecutive parameters a,b, put w=(b-a)/(1+a*b). Direct cross-product
and tangent-intersection algebra gives the whole-disk contributions

```text
lower contribution = 4*w/(1+w*w)
upper contribution = 4*w.
```

With a=k/N and b=(k+1)/N, w=N/(N*N+k*(k+1)). The total unrounded gap obeys

```text
upper - lower
  = sum 4*w*w*w/(1+w*w)
  <= 4/(N*N).
```

Thus the exact unrounded polygons squeeze one limiting area. This derives a
circle-area quantity from a geometric refinement family rather than from
decimal proximity to a supplied constant. It remains classical external
geometry, not a new MoO theorem.

For the finite computation, each lower term was rounded down and each upper
term up to denominator 10^24. All selection decisions use integers and exact
rationals. The certified additional gap is at most 2*N/10^24. The finite run
reaches N65536; a fixed rounding denominator is not being claimed to implement
the completed limit as N tends to infinity. The unrounded family supplies
the mathematical convergence statement.

Two independent checks were used:

- Explicit vertices, tangent intersections, and the shoelace area formula
  reproduce the optimized bounds for small N, including non-power-of-two N.
- Separate rational grid cells were counted as wholly inside or covering the
  disk, using only integer squared distances and integer square roots. At
  grid sizes 32,128,512,2048,8192, every resulting interval contains the finest
  polygon interval.

The grid bounds are much wider; they verify an independent geometric
construction, not the full last-digit precision of the polygon calculation.

## What happened to the apparent hits

Enumerate reduced ratios h=p/q with 1 <= h <= 2 and q <= 1000. A candidate
survives a level only if h*h remains inside that level's exact area interval.
Survival means unresolved compatibility, never equality.

| N per quadrant | Total polygon sides | Compatible rational ratios |
| ---: | ---: | ---: |
| 32 | 128 | 187 |
| 64 | 256 | 46 |
| 128 | 512 | 11 |
| 256 | 1024 | 3 |
| 512 | 2048 | 0 |
| 65536 | 262144 | 0 |

The final three coarse candidates were

```text
1441/813
1737/980
296/167.
```

At N512, the first two are proved too small and the third too large. This
rules out every reduced rational ratio in the stated denominator envelope,
not just those three: the earlier filters were exhaustive and nested.
It does not rule out closer approximations with larger denominators.

At N65536, the certified unit-disk area bounds are

```text
3.141592653251708049438716
  <= Area(D) <=
3.14159265375883583300936.
```

They imply the certified square-side bounds

```text
1.772453850810 <= h <= 1.772453850954.
```

The width of the side interval is 1.44e-10. These decimal endpoints are exact
rational outward bounds, not a floating-point residual interpreted as proof.

## The branch that remains

One can maintain a lower and upper rational side bound and test their
mediant. If its square is below the area lower bound, move the lower side up.
If it is above the area upper bound, move the upper side down. Otherwise,
refine the polygons before deciding. This gives a certified Stern-Brocot
bracket path.

For example, the resolved comparisons include

```text
7/4:   too small
16/9:  too large
23/13: too small
39/22: too large.
```

The path does not call any of these an exact circle-square hit. At the final
precision it resolves the path until the imposed denominator-sum cap 10000,
leaving neighboring rational bounds 8545/4821 and 17386/9809. No previously
certified decision reverses under refinement.

The areas 2 and 4 serve as controls. The diamond of area 2 gives a different
root-bracketing path. The square of area 4 correctly returns the exact rational
side 2. The algorithm can recognize exact equality when the target area and
rational side permit it; it does not reject equality by construction.

This is a general rational bracketing procedure driven by geometric area
bounds. Its stable prefix is explained by those bounds. No new simple
recurrence, prime-only rule, or logarithmic spiral was established.

## Why there cannot be finite exact rational hits

The finite rational MoO operations preserve rationality. If R and s are
nonzero rational lengths and their Euclidean areas agree, then

```text
pi = s*s/(R*R),
```

which would make pi rational. Its irrationality rules this out. The stronger
classical transcendence result also rules out the usual finite
compass-and-straightedge construction. See
[Milla, The Transcendence of pi and the Squaring of the Circle](https://arxiv.org/abs/2003.14035).

There is consequently no exceptional nonzero rational radius that escapes
the obstruction. In the real (R,s) plane the equal-area relation is a ray of
irrational slope. Among rational pairs it has no nonzero point. The
approximation path approaches that relation without supplying exact rational
intersections with it.

This theorem is separate from the constant-free numerical experiment. The
experiment excludes the finite q<=1000 envelope by exact bounds; the theorem
excludes all finite rational ratios for this Euclidean equal-area definition.

## Return to the strict graph

The preserved wide U300 and U1000 corpora were opened read-only and passed
strict alignment. The audit examined 57 parameter/vertex cases: every
interior k/N for N=2,4,8,16,32. Repeated coordinates at different N are
separate witness cases, not counted as independent shapes.

| Corpus | Complete vertex witness cases | Length-ratio landings, of 46 | Square-area quotient landings, of 46 | Intended fractional area operations, of 4 |
| --- | ---: | ---: | ---: | ---: |
| U300 | 17 | 16 | 7 | 0 |
| U1000 | 26 | 18 | 8 | 0 |

The 46 side ratios are the union of endpoints and queried ratios across the
finite bracket runs. Some exceed the corpus operand range. Missing entries
are preserved, not removed to improve the success rate.

All vertex completion stages match their raw integer operand-size prediction
N*N+k*k. This is evidence for the recorded construction path and for its
ordinary positive-spine readiness cost, not a graph-specific geometric law.

The area recurrence exposes a distinct boundary. For the N2 inscribed
polygon, one external area decomposition is

```text
8/5 + 6/5 -> 14/5.
```

The result 14/5 exists in both corpora by the integer quotient 14/5. The
intended addition edge does not: its rational inputs cannot be operands under
the strict positive-spine policy. Similarly, the outer area decomposition
2+4/3 -> 10/3 has a result value but no intended fractional addition edge.

This audit does not prove that every finite area calculation is inaccessible
to integer encodings. Clearing denominators can encode finite rational
arithmetic using integer constructions followed by division, at additional
stage cost. Such a complete area-recurrence encoding was not built or audited
here. It would still produce rational approximations, not an exact rational
equal-area hit.

What would be needed for a stronger internal claim is explicit geometry/area
semantics, witnessed finite accumulation through an admissible encoding, and
a separately justified limit representation. Adding a limit representation
would change what counts as a constructed object; this pass made no runtime
changes or speculative-operand exception.

## Artifacts and validation

- [Frozen design](CIRCLE_SQUARE_AREA_BRIDGE_20260911.pre.md).
- [Full report](results/2026-09-11-circle-square-area-v1.json): every surviving
  finite-envelope candidate, all interval and bracket records, and compact
  exact graph node/edge tables with input and source hashes.
- [Compact summary](results/2026-09-11-circle-square-area-summary-v1.json).
- [Probe](../../moo_circle_square_area_probe.py).
- [Nine focused stdlib tests](../../test_moo_circle_square_area_probe.py).

Run from the repository root, choosing a new output path:

```powershell
python -B moo_circle_square_area_probe.py --max-n 65536 --max-denominator 1000 --write research/geometry/results/circle-square-area-rerun.json
python -B -m unittest test_moo_circle_square_area_probe -v
```

The full run took about 14 seconds on this host. All nine tests passed. Both
corpus hashes matched the preserved inventory and remained unchanged. No
runtime source or saved corpus was modified.

A separate verification pass, without importing the probe helpers, enumerated
all 304193 reduced ratios in 1 <= h <= 2 with denominator at most 1000 and
reproduced all 17 levels of candidate lists. It also checked each bracket
comparison and outward side bound, reread 630 saved node records and 526
present edge records from the original databases, and verified 536 missing
edge queries. Source and design hashes matched. These checks are recorded in
the compact summary under `independent_validation`.

The retained conclusion is narrower than a squaring-the-circle discovery:
the shell parameter can support an external area refinement, which supports
a certified approximation path. Exact equal-area hits are absent from the
current rational-length domain.
