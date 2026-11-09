# A Finite Improvement From The Seven-Step Relation

Date: 2026-09-11.

Changing the selected directions improves the original small example:
**1,020 distinct points give 5,188 unit pairs**, compared with 1,024 points
and 5,128 pairs before. Every unordered pair was checked using exact squared
distance. An independent agent reconstructed the directions and repeated the
counts without importing the project probes.

This is a strict improvement over that particular example. The bounded
search establishes neither optimality nor a new asymptotic exponent. It also
exposes a short relation with an exact continuation of directions toward i.
The continuation does not preserve all the relations responsible for the
finite improvement.

## Construction And Controls

Use u=(3+4i)/5, v=(5+12i)/13, and delta=u^3*v^2. The seven directions

\[
S=(1,u^2,uv,v^2,u^3,u^2v,uv^2)
\]

satisfy

\[
-1-u^2+uv-v^2-u^3+u^2v-uv^2=\delta.
\]

A point is a sum of a subset of the selected directions. Distinct subsets
can represent the same geometric point, and different construction edges
can represent the same geometric unit pair. Both identifications are retained
explicitly in the report.

| Selected directions | Distinct points N | Unit pairs E | Distinct coordinate-flip pairs | Extra pairs |
| --- | ---: | ---: | ---: | ---: |
| Original triangular ten | 1,024 | 5,128 | 5,120 | 8 |
| Seven S | 128 | 449 | 448 | 1 |
| S and u | 256 | 1,026 | 1,024 | 2 |
| S and delta | 255 | 1,024 | 1,024 | 0 |
| S, delta, u | 510 | 2,303 | 2,303 | 0 |
| S, delta, u, v | 1,020 | 5,124 | 5,116 | 8 |
| S, delta, i*u*v^2 | 510 | 2,319 | 2,303 | 16 |
| S, delta, i*u*v^2, -i*u^2*v | **1,020** | **5,188** | **5,116** | **72** |

The original triangular ten are u^a*v^b for a,b>=0 and a+b<=3.
The new selection replaces its three directions u, v, v^3 with delta and
two quarter-turn directions. Both use ten binary choices, hence 1,024 raw paths.

All these comparisons use integer coordinates divided by D=274625. The
winning generators, in the order used by the stored graph, are:

~~~text
0  1              ( 274625,       0)
1  u^2            ( -76895,  263640)
2  u*v            (-139425,  236600)
3  v^2            (-193375,  195000)
4  u^3            (-257049,   96668)
5  u^2*v          (-272935,   30420)
6  u*v^2          (-272025,  -37700)
7  delta          ( 112359, -250588)
8  i*u*v^2        (  37700, -272025)
9  -i*u^2*v       (  30420,  272935)
~~~

Closing the initial relation by adding delta identifies one opposite pair
of the eight-cube's vertices. All 1,024 cube edges survive, giving 255 points
and 1,024 pairs. Compared with adding u, however, this saves one point and
loses two pairs: the correct comparison is (255,1024) against (256,1026).
The two earlier extra pairs become coordinate-flip pairs after identification;
counting them again would be an error.

## Where The Improvement Comes From

The final graph has four merged points, each with two subset occurrences.
Their mask pairs are (36,219), (292,475), (548,731), and (804,987).
They are four translated copies of the same zero relation. Four pairs of
coordinate-flip occurrences also merge, leaving 5,116 distinct such edges.

There are then 72 further geometric edges in three directions. With each
edge oriented to have positive real displacement, their exact witnesses are:

| Signed sum giving a unit displacement | Displacement | Translated edges |
| --- | --- | ---: |
| 1+v^2-u^3-delta+i*u*v^2 | -i*u^2 | 32 |
| -u*v-u^2*v+u*v^2-i*u*v^2-i*u^2*v | -u^2*v^2 | 32 |
| -1-u^2-v^2-u^3-delta-i*u*v^2-i*u^2*v | -u^2*v^2 | 8 |
| 1+u^2-u*v-v^2+u^3+u^2*v+delta-i*u*v^2-i*u^2*v | v | 2 |

The middle two families share exactly two geometric edges. Their signed
witnesses differ by the existing zero relation, so they must not be treated
as independent relations. The total is therefore

\[
32+(32+8-2)+2=72,
\qquad 5116+72=5188.
\]

The five-term witnesses each leave five binary choices free, producing
32 translations. The seven-term witness leaves three free choices, producing
eight translations; the nine-term witness leaves one, producing two. These
counts were checked after identifying equal endpoints, as well as directly
against the full unit-edge graph. Both endpoint masks are inspected at a
merged point, rather than choosing a single representative prematurely.

Adding the first quarter-turn direction gives 16 extra links. A generic copy
of that 510-point arrangement would have 1,020 points and
2*2319+510=5,148 pairs. The selected second quarter-turn instead supplies
40 additional pairs, reaching 5,188. This isolates a gain beyond copying
the first small benefit.

## A Copying Baseline With An Exact Limitation

For any finite nonempty point set P, choose a unit vector w such that P and
P+w are disjoint and their only cross-pairs at unit distance are matching
points. Then

\[
N'=2N,\qquad E'=2E+N.
\]

Such choices exist: overlap excludes finitely many point differences. For
each nonzero difference a, an unwanted cross-pair requires
|w|=1 and 2*w dot a=-|a|^2, so excludes at most two more directions. There
are infinitely many rational unit directions, so rational configurations
can use fresh rational choices at every finite step.

After r such steps,

\[
N_r=2^rN_0,\qquad E_r=2^rE_0+r2^{r-1}N_0.
\]

Consequently C(P)=2E/N-log2(N) is invariant under this copying operation,
and log(E_r)/log(N_r) tends to one. A special direction can depart from this
baseline by producing overlaps or additional cross-edges.

C is 0.015625 for the original arrangement and about 0.178195582749 for
the new one. It is a useful exploratory comparison against copying. It
does not measure future extension possibilities, coordinate costs, or
proximity to a global optimum. A fixed improvement in C, followed only
by generic copying, still has limiting exponent one.

## An Exact Direction Branch

Dividing the second short witness by u*v gives

\[
uv-(1+i)u+(1-i)v-1=0.
\]

Thus v=T(u), where

\[
T(z)=\frac{1+(1+i)z}{z+1-i}.
\]

For |z|=1, the numerator equals z times the conjugate of the denominator.
The denominator cannot vanish on the unit circle, so T maps unit directions
to unit directions and preserves rational complex coordinates.

Starting at 1 gives an explicit sequence:

\[
z_n=T^n(1)=\frac{n+1+ni}{n+1-ni}
=\frac{2n+1+2n(n+1)i}{2n^2+2n+1}.
\]

In particular z_1=u and z_2=v. To prove the formula, represent T by
M=I+A, where A has rows (i,1) and (1,-i). Direct multiplication gives
A^2=0, so M^n=I+n*A. This establishes the sequence for every nonnegative
integer n. The probe separately checks the first 13 iterates using rational
arithmetic.

There is a knowable direction limit:

\[
z_n\longrightarrow i,\qquad
|z_n-i|^2=\frac{2}{2n^2+2n+1}.
\]

These are points on the unit circle approaching a quarter-turn. The limit
belongs to this specified direction recurrence. It supplies no count of
points or pairs in a growing arrangement.

The distinction is testable: the original eight-term zero relation holds
for z_1,z_2, but fails for z_0,z_1 and for z_2,z_3. Its residual at z_0,z_1
is (-24-32i)/25. One short relation therefore continues, while the entire
winning graph has not been shown to continue. The polynomial denominator
2n^2+2n+1 is not necessarily prime; it is already 25 at n=3.

## Scope Of The Search And Evidence

The search started from S and delta and tried all 98 unoriented unit
directions in the D lattice. Negating a newly added generator translates
the whole subset-sum set, so one sign per direction suffices for these counts.
Repeated existing directions were included as controls. Candidates were
ranked by approximate C, then exact average degree and a coordinate tie-break.

Two candidates tied for the best first extension, both at (510,2319).
Both branches were followed through another 98 candidates, for 294 evaluated
extensions in total. This was a bounded greedy comparison, not an exhaustive
search of all pairs of directions. At most ten generators and 1,024 paths
were enumerated. The main improvement uses exact integer counts and does
not depend on a close floating-point comparison.

The D lattice has exactly 196 oriented unit directions, so every finite
configuration in it satisfies E<=98*N. Keeping D was a control for this
local experiment; changing denominators remains allowed. The direction
sequence above already leaves this fixed lattice. The earlier fixed-seed
family's exponent-one proof also continues to apply to that family.

This is an external pair-geometry lens. The report retains subset additions,
all point occurrences, every unit edge, relation witnesses, and their overlaps.
No scalar speculative node is used or promoted by this experiment. The
mathematical conclusions do not depend on being specific to Modulus of One.

The [probe](../../../moo/relation_geometry_probe.py) writes a new report with
exclusive creation. The [frozen evidence](results/2026-09-11-relation-geometry-v1.json)
contains all candidate summaries and eight complete selected graphs, with
source hashes. Its SHA256 is
5e17ee45e0afac0c11932af8f56a1606023d4c4fd178bd4c951476e7d2ff146b
(4,644,257 bytes). Existing frozen results were not replaced.

For every selected graph, an independent enumeration inside the tool checks
all unordered pairs using integer squared distance, without using the unit
shell. The winning graph requires 519,690 such pair tests. A separate agent
also reconstructed the rational directions and reproduced the two main
counts and extra-edge breakdown without importing any project probe.

Four new [tests](../../../tests/test_moo_relation_geometry_probe.py) and the eight
existing direction-probe tests passed together. They include rejection of
a deliberately removed edge, to check the independent audit catches a
corrupted graph. Reproduce with:

~~~text
python -B -m unittest test_moo_relation_geometry_probe test_moo_unit_direction_branch_probe -v
python -B -m moo.relation_geometry_probe
~~~

Use --output with a new versioned filename to retain another report.

The useful next obligation is to show how compatible short relations grow
along a construction and how many distinct edges survive their overlaps.
The explicit direction limit provides orientation; sustained edge growth
needs its own argument before larger enumeration is justified.
