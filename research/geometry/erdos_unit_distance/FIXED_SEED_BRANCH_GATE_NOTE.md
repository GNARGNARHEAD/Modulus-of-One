# Fixed-Seed Unit Directions: A Bounded Branch Gate

Date: 2026-09-10.

The two rational directions proposed in the conversation do produce an exact
interaction: their first 1,024 subset-sum points have eight additional unit
pairs, all explained by one relation. That relation also supplies an explicit
later collision between two different subset constructions.

However, the infinite family specified below has limiting unit-distance
exponent **exactly 1**. Its available unit directions grow too slowly relative
to its number of points. This closes the proposed fixed-seed scaling experiment;
larger enumerations cannot turn this family into a positive power improvement.

These are external mathematical results with a small, actual Modulus of One scalar
witness graph. The arguments and exact computations have been checked locally.
There is no claim of mathematical novelty, a record exponent, or a bound on all
planar point configurations.

## The Rule And The Gate

Use complex notation for ordinary ordered pairs, and set

\[
u=\frac{3+4i}{5},\qquad v=\frac{5+12i}{13},\qquad |u|=|v|=1.
\]

Starting with the direction 1, repeat multiplication by either u or v. At
external generation depth k retain

\[
V_k=\{u^a v^b:a,b\geq0,\ a+b\leq k\}.
\]

Then take all binary subset sums, identifying equal positions:

\[
P_k=\left\{\sum_{w\in V_k}\epsilon_w w:\epsilon_w\in\{0,1\}\right\}.
\]

Let N_k be the number of **distinct points** and E_k the number of **unordered
distinct point pairs at distance 1**. Separate construction occurrences,
coordinate-flip edges, and all geometric unit edges. A repeated route to the
same point is not an additional point; repeated witnesses for one pair are not
additional pairs.

The gate is to enumerate only k=0,1,2,3, then establish what indefinite
repetition permits analytically. The control is the single-seed power ray
1,u,...,u^(m-1), checked for m=1,...,10. Neither calculation exceeds 1,024 raw
subset paths in one stage.

This rule is a proposed external lens. It was selected from the shell, ratio,
product, and addition discussion; no graph search independently selected it.

## Branch Card And Actual Modulus of One Evidence

```text
branch_name: shell-ratio witnesses with repeated product/addition in an external lens
moo_relation: self-multiplication, shared square/sum output, and ratio output
operator_fan_root: mixed product, addition, and ratio
active_field: positive-spine scalar calibration to 169; external rational pair plane
eligible_sources: confirmed scalar operands in core; declared u and v in the lens
witness_event: recorded square/sum/division edges; external direction and addition edges
shadow_values: rational unit directions and their subset-sum positions
membership_reading: the corresponding construction edge must be retained
non_membership_reading: no witness here does not imply absence from the full Modulus of One field
linearity_reading: multiply by the same selected seeds; repeat binary addition
relation_distance: a+b is external word length, not Modulus of One relation-distance
stage_distance: core frontier 13 then 169; k is a separate external cutoff
witness_depth: read through retained input/output edges and source eligibility
interaction_reading: additional unit edges or shared endpoints with exact witnesses
machine_fields: direction edges, subset masks, canonical point IDs, pair witnesses, statuses
known_classical_shadow: Gaussian rational directions and binary subset sums
allowed_claim_language: exact relation and limiting exponent for the specified family
disallowed_claim_language: core complex branch, grounded rational geometry, global exponent bound
weakening_or_kill_rule: a limiting exponent of 1 stops fixed-seed scaling for a power gain
```

The calibration uses the existing strict `Graph` runtime, with speculative
operands disabled. It first advances the positive spine to 13 and records
3*3, 4*4, 5*5, 12*12, and 13*13. Outputs beyond the frontier remain speculative
until the positive spine reaches them. After advancing to 169, it records

\[
9+16=25=5\cdot5,\qquad25+144=169=13\cdot13.
\]

Each equality is witnessed by incoming edges to a common canonical output,
rather than merely by a numerical lookup. Finally it records 3/5, 4/5, 5/13,
and 12/13 as four speculative ratio outputs. They are never used as core
operands.

The saved graph has **173 nodes and 179 arithmetic edges**: 169 grounded
positive integers and four speculative ratios. Its unchanged `to_jsonable()`
export is embedded in the report. Complex multiplication, pair addition,
negative coordinates, zero as the geometric origin, and Euclidean distance
belong to the external lens; they do not promote these scalar nodes or extend
the runtime's confirmation rule. The circle here is the norm-one circle,
not the phase quotient from the separate circle-as-one program.

## Exact Finite Result

| Depth k | Selected directions | Raw subset paths | Distinct points N | Unit pairs E | Extra pairs beyond coordinate flips |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1 | 2 | 2 | 1 | 0 |
| 1 | 3 | 8 | 8 | 12 | 0 |
| 2 | 6 | 64 | 64 | 192 | 0 |
| 3 | 10 | 1,024 | 1,024 | 5,128 | 8 |

There are no duplicate subset positions in these four stages. At k=3, the
ordinary coordinate flips supply 5,120 distinct pairs. The additional eight
pairs use an eleventh unoriented direction. The exact count includes every
unit displacement in the common denominator lattice, including directions
outside V_3. An independent exhaustive comparison of all 523,776 point pairs
agrees with the shell-based count.

### The retained interaction

Set

\[
A=1+u^2+v^2+u^3+uv^2,\qquad B=uv+u^2v.
\]

The additional unit displacement is

\[
B-A=u^3v^2=\frac{8643-19276i}{21125},\qquad |B-A|=1.
\]

Both endpoints already belong to P_3, although the multiplicative direction
u^3 v^2 first belongs to V_5. The other three available terms u, v, and v^3 can
be added to both endpoints in any subset, giving the eight translated pairs.
Their subset masks and exact coordinates are retained individually.

This yields a concrete later consequence:

\[
uv+u^2v=1+u^2+v^2+u^3+uv^2+u^3v^2.
\]

Two different binary subsets therefore reach the same endpoint in P_5. We
verified this exact equality directly, without enumerating P_5. It is the first
stage containing all terms of this particular witness; we have not claimed it
is the earliest collision of any kind. The relation was extracted after the
P_3 enumeration, and the P_5 check is its follow-up consequence, not a separate
blind prediction.

The branch framing earns something concrete here: it identifies a multiplicative
direction already realized by an additive difference, then identifies the
endpoint constructions that will merge when that direction is admitted. The
underlying arithmetic is classical, and the effect alone does not establish an
asymptotic gain.

## Single-Seed Control: An Exact Formula For Every Length

Define

\[
Q_m=\left\{\sum_{j=0}^{m-1}\epsilon_j u^j:\epsilon_j\in\{0,1\}\right\}.
\]

We can determine both counts for all m:

\[
|Q_m|=2^m,\qquad E(Q_m)=m2^{m-1}
       =\tfrac12|Q_m|\log_2|Q_m|.
\]

First, u is not an algebraic integer. Its monic minimal polynomial over the
rationals is X^2-(6/5)X+1, which does not have integer coefficients. A collision
between two binary sums would give a nonzero polynomial vanishing at u, with
coefficients in {-1,0,1}. After changing its sign if necessary it is monic,
contradicting non-integrality. Thus all 2^m sums are distinct.

Next consider a nonzero difference A(u), where A has coefficients in
{-1,0,1}. Remove its lowest power, writing A(X)=X^ell B(X), with B's constant
and leading coefficients both equal to +1 or -1. Let r be the degree of B.
Since |u|=1, a unit difference would require |B(u)|=1.

If r>0, the expression

\[
H(X)=X^r\bigl(B(X)B(X^{-1})-1\bigr)
\]

is an integer polynomial of degree 2r with leading coefficient +1 or -1.
Because the coefficients are real and the conjugate of u is u^(-1), the
unit-length assumption gives H(u)=0. Changing sign again gives a monic integer
polynomial, a contradiction. Hence r=0, and the difference consists of exactly
one term +u^j or -u^j.

Consequently the only unit edges change one binary choice. There are m*2^(m-1)
such unordered pairs. The ten exact finite checks agree with this argument;
at m=10 the control has 1,024 points and exactly 5,120 unit pairs. Its limiting
logarithmic exponent is 1 despite its unbounded logarithmic factor.

### Where the earlier logarithmic spiral fits

The earlier visualization explicitly generated z_k=(1+2i)^k. With unwrapped
angle theta_k=k*atan(2) and radius r_k=5^(k/2), every plotted integer iterate
satisfies

\[
\log r_k=\frac{\log 5}{2\arctan 2}\,\theta_k.
\]

Thus the exact points do lie on one logarithmic spiral; the rendered curve is
a continuous interpolation. This is a precise repeated-multiplication branch
in the external pair lens. Its connection to prime/square arithmetic comes
from 1^2+2^2=5. The plot contains powers of that chosen seed; it is not a plot
of independently collected members of the full prime and square branches.

There is a direct bridge to the unit directions in this experiment. Squaring
and normalizing the spiral seed gives

\[
\frac{z_{2k}}{5^k}=\left(\frac{-3+4i}{5}\right)^k.
\]

These are rational unit directions. The single-seed proof above only uses
unit modulus and failure to be an algebraic integer, so it applies equally to
w=(-3+4i)/5: its monic minimal polynomial is X^2+(6/5)X+1. Binary subset sums
of these directions therefore also have exactly N=2^m and E=m*2^(m-1).
This is an analytic extension of the control argument; the recorded finite
control uses u=(3+4i)/5.

The spiral observation consequently survives intact and leads to a predictive
counting law for this explicit use of its directions. Its pitch controls
radial growth per turn; an extremal exponent additionally depends on how
direction branches combine into distinct points and realized unit pairs.
Normalizing individual spiral points changes their mutual distances: the
subset-sum construction is a new geometric point set, not a distance-preserving
view of the original spiral.

With several prime seeds, each fixed multiplication ray has its own spiral
law. In unwrapped angle/log-radius coordinates, products of two seeds have
the form

\[
(\theta,\log r)
=a(\arg q_1,\log|q_1|)+b(\arg q_2,\log|q_2|).
\]

This is generally a two-parameter pattern, rather than one line. A common
spiral for the wider structure would need an additional relation. The
additive interaction retained above is a concrete place where different
multiplication lineages meet; the infinite bound accounts for it as well.

## Two Seeds: The Infinite Bound

Write alpha=2+i and beta=3+2i. Their norms are the distinct primes 5 and 13, and

\[
u=\frac{\alpha}{\overline\alpha},\qquad
v=\frac{\beta}{\overline\beta}.
\]

Unique factorization in the Gaussian integers shows that different exponent
pairs (a,b) give different directions: the valuations at alpha and beta recover
a and b. Thus V_k has (k+1)(k+2)/2 members. Gaussian unique factorization and
the four units are standard facts; see
[Keith Conrad's notes on the Gaussian integers](https://kconrad.math.uconn.edu/blurbs/ugradnumthy/Zinotes.pdf).

### 1. Points grow at least exponentially in k

The set P_k contains Q_(k+1), using only 1,u,...,u^k. The control argument gives

\[
N_k\geq2^{k+1}.
\]

This remains true even when other subset sums collide. We do not assume
2^|V_k| distinct points at untested depths.

### 2. All possible unit directions grow only quadratically in k

Every point has both coordinates in (1/D)Z for D=5^k*13^k=65^k. Therefore
any unit displacement has the form (x+iy)/D, with integers x,y satisfying

\[
x^2+y^2=D^2.
\]

Factorization gives all such numerators as

\[
i^t\alpha^j\overline\alpha^{2k-j}
     \beta^\ell\overline\beta^{2k-\ell},
\quad t\in\{0,1,2,3\},\quad j,\ell\in\{0,\ldots,2k\}.
\]

There are exactly 4(2k+1)^2 oriented directions. This is a bound from the
entire ambient lattice, so incidental edges such as the eight just found are
already included. A point can have at most one neighbor in each direction.
Counting both endpoints of each edge yields

\[
E_k\leq2N_k(2k+1)^2\leq8N_k(\log_2 N_k)^2.
\]

### 3. The exponent is pinned to 1

The coordinate-flip graph on all subset masks is connected. Identifying masks
with equal positions preserves connectedness, and a flip never becomes a loop
because its displacement has length 1. Hence E_k>=N_k-1. Combining the bounds,

\[
N_k-1\leq E_k\leq8N_k(\log_2 N_k)^2,
\qquad
\boxed{\lim_{k\to\infty}\frac{\log E_k}{\log N_k}=1}.
\]

This is an ordinary limit for the specified family, not an asserted limit for
the global extremal function u(n). For any fixed delta>0, this family has
E_k/N_k^(1+delta) tending to zero. Growing its depth cannot eventually produce
a persistent positive power gain.

## What This Says About Further Compute

The local relation survives the test, while the proposed fixed-seed route to a
larger exponent fails the gate. Preserve the relation and stop enumerating
larger P_k solely to seek an exponent above 1. No larger Modulus of One corpus is required
to settle that decision.

A useful orientation for a successor is the number M of *available* oriented
unit directions relative to the distinct point count N. Since E<=NM/2, a
target E>=c*N^(1+delta) needs at least M>=2c*N^delta. This is necessary, not
sufficient: enough of those directions must actually connect retained points.

In this family, log(M)/log(N) tends to zero, so no efficiency of endpoint reuse
can rescue a positive delta. A new rule must change that growth relationship,
for example by introducing new arithmetic seeds instead of only powering
these two. Adding seeds is not itself a guarantee: their cost in point count
and the density of realized pairs must be bounded as well. This result does
not exclude all rational-coordinate constructions or all Modulus of One-guided lenses.

The separately studied published construction uses number fields of growing
degree, making a fixed pair of Gaussian seeds a limited model of its arithmetic
growth. The growing-degree mechanism is explained in the
[authors' companion paper](https://arxiv.org/html/2605.20695v1).
The existing certificate/refinement investigation remains a different possible
continuation; this gate does not alter its conclusions.

## Artifacts And Reproduction

- [Exact probe](../../../moo/unit_direction_branch_probe.py).
- [Focused independent checks](../../../tests/test_moo_unit_direction_branch_probe.py).
- [Completed version 1 report](results/2026-09-10-fixed-seed-branch-v1.json).
- [Program card and the separate certificate investigation](README.md).

The JSON preserves every direction construction edge in the bounded two-seed
stages. For P_3 it also preserves 1,024 canonical points with subset masks,
1,023 subset-addition edge occurrences, and all 5,128 geometric unit edges
with coordinate-flip witness counts. The addition occurrences construct the
points; the full geometric edge list also includes flips across every subset
context and the eight extra pairs. The embedded Modulus of One graph preserves its normal
export shape and its actual epistemic statuses.

```text
python -m unittest test_moo_unit_direction_branch_probe -v
python -m moo.unit_direction_branch_probe
python -m moo.unit_direction_branch_probe --output path/to/a-new-version.json
```

All eight focused tests passed. They check shell completeness against a
separate integer-square search, all point pairs independently, reconstruction
from retained graph edges, duplicate-path controls, all ten single-seed counts,
the later collision with independent rational arithmetic, scalar witness
eligibility, and bounded-input rejection. All geometry uses exact integers or
fractions. The reported finite log(E)/log(N) field is only a floating-point
display value; it is not used in a proof or count.

The combined run with the existing certificate tests passed all 16 tests.
The core demo at limit 3 also completed, and all 42 local Markdown links in
the touched research notes and indexes resolved.

The executable used here was
`C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`
(Python 3.12.14). The tool refuses to overwrite an existing output file.
