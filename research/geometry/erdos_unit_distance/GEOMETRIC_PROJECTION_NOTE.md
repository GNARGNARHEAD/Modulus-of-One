# The Eight Extra Links Form An Exact Projection Pattern

Date: 2026-09-11.

This inspects the depth-3 two-seed example, not the later 241-denominator
comparisons. The eight extra links are eight translated copies of one
relation. Their placement is an exact affine image of the vertices of a
three-dimensional cube. They are not eight measurements at increasing sizes.

## Source And Exact Geometry

The existing [probe](../../../moo/unit_direction_branch_probe.py), invoked as
two_seed_stage(3, retain_graph=True), returns 1,024 distinct points and 5,128
unit pairs: 5,120 generator-step pairs and eight additional pairs. The
coordinates are integer pairs divided by D=274625. Every unit pair is verified
by its exact squared length; no floating-point distance threshold is used.

Write u=(3+4i)/5 and v=(5+12i)/13. The ten construction directions are
u^a*v^b with a,b>=0 and a+b<=3. A point is a binary subset sum of these ten
directions, so the entire point arrangement is the image of the vertices of
a 10-dimensional cube under a fixed linear map to the plane. This terminology
is standard; see Lecture 7 on zonotopes and cube projections in
[Postnikov's combinatorics and geometry course](https://math.mit.edu/~apost/courses/18.217_2024/).
The point set is discrete; its convex hull is the corresponding zonotope.

All eight extra links have displacement

\[
\delta=\frac{8643-19276i}{21125}=u^3v^2,
\qquad 8643^2+19276^2=21125^2.
\]

Their common construction witness is the already retained relation

\[
-1-u^2+uv-v^2-u^3+u^2v-uv^2=u^3v^2.
\]

The seven directions on the left belong to depth 3. The direct direction on
the right first belongs to the selected generator family at depth 5. This
was the source of the earlier exact later-collision witness; it is not a new
independent relation discovered by fitting a curve.

The remaining three binary choices are u, v, and v^3. For each
epsilon in {0,1}^3 the corresponding link is

\[
p(\epsilon)\longrightarrow p(\epsilon)+\delta,\qquad
p(\epsilon)=p_0+\epsilon_1u+\epsilon_2v+\epsilon_3v^3,
\]

with p_0=(-524719+517608i)/274625. All eight links are different in this
point set and have disjoint endpoints. The 16 endpoints induce exactly 32
unit pairs: the two three-cube graphs contribute 24, and the eight extra
links join them. This local patch is a unit-edge planar realization of the
four-dimensional cube graph; its combinatorial dimensions are not physical
Euclidean dimensions.

## A Four-Copy Fit Predicts The Other Four

Use the copies indexed 000, 100, 010, and 001 to determine an affine map:
p_0 is the 000 location, and each other location minus p_0 supplies one map
column. In integer coordinates those columns are

~~~text
u:   ( 164775,  219700)
v:   ( 105625,  253500)
v^3: (-254375, -103500)
~~~

For each of the other four bit triples, adding the indicated columns predicts
the recorded start point exactly. Adding the displacement of the 000 link
then predicts the end point exactly. Every coordinate residual is zero.
This is a consistency check with withheld copies inside a known construction;
it is not independent evidence for a newly discovered general law.

Removing each copy's translation makes all eight segments coincide. It does
not require rescaling or bending a segment. The visualization interpolates
between their original relative positions and this aligned comparison.

## What A Curve Or Distortion Would Mean

The eight start locations have a six-vertex convex hull, with two interior
points. The full 1,024-point arrangement has a 20-vertex convex hull. These
are images of cube vertices spread across a two-dimensional region, rather
than samples supplied in a natural order along a one-dimensional curve.

An exact rational row reduction of the eight rows
[x^2, x*y, y^2, x, y, 1] has rank six. Consequently no nonzero polynomial
of degree at most two vanishes at all eight start locations: they lie on no
single line, circle, ellipse, parabola, or hyperbola. This does not exclude
arbitrary higher-degree interpolating curves. A best orthogonal straight-line
fit has RMS perpendicular error about 0.27763 in unit-distance lengths.

The linear map is uniform in location, but does not preserve all distances
by one common scale factor. For example, the independent cube-axis steps
mapping to u and v each have unit length, while their difference maps to

\[
|u-v|=\frac{2}{\sqrt{65}}\approx0.24807.
\]

That direction-dependent compression is determined by the map's columns.
There is no varying perspective distortion to estimate in this example.

The exact affine rule predicts the positions of copies whenever the specified
translation choices are present. It does not predict how many distinct
copies survive all later point identifications, nor a limiting optimal
unit-distance exponent. All eight links here come from one fixed size.
The earlier fixed-seed family already has a proved limiting exponent one;
these geometric checks provide a control for inspecting richer constructions.

## Inspection Record

The checks in this inspection reconstructed the graph from the existing
probe, compared all eight signed-generator witnesses and displacements,
recovered the three free choices, checked all four withheld copies, counted
the 16-point induced graph, and computed exact convex hulls and conic rank.
No core graph, speculative status, existing frozen report, or point-assembly
rule was changed. The interactive drawing retains the integer generators
and separately verifies observed and predicted endpoints before plotting.
