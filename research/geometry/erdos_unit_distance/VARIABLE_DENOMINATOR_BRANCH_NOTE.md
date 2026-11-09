# Variable Denominators: More Directions And A Limit Of Full Boxes

Date: 2026-09-11.

Allowing different denominators produces a substantial finite improvement.
In K_24, denominator 73*97=7,081 supplies 157,464 complete oriented unit
directions. Denominator 73^2=5,329 supplies 15,000. At the same point count
in the full-basis construction, the mixed-prime case has about 7,751 unit
neighbors per point, compared with about 1,970 for the square.

The analysis also removes a possible ambiguity in the earlier stopping rule:
for any fixed CM field and fixed integral basis, **all full rectangular
coefficient boxes have E<=C_epsilon*N^(1+epsilon), uniformly over every
integer denominator**. The denominator is free in this statement. The proof
identifies a limitation of this point-assembly rule, not a prohibition on
arbitrary point sets in the field.

These are locally checked consequences and examples from classical arithmetic
and geometry. No new optimal exponent or improvement to a published exponent
certificate is claimed.

## Scope And Construction Graph

Use the same fields, bases, and embedding as the
[three-field note](SPLIT_PRIME_BRANCH_GROWTH_NOTE.md):
K_m=Q(zeta_m), m=4,8,24, with O_m=Z[zeta_m], degree d and f=d/2.
For a positive rational integer D define

\[
U_m(D)=\{z\in D^{-1}O_m:z\overline z=1\},\qquad M=|U_m(D)|.
\]

D is a common bound on denominators; some individual directions require only
a proper divisor of D. Opposite oriented directions are distinct, while
unordered point pairs are counted once.

```text
branch_name: independent conjugate-prime ratios with variable exponent budgets
evidence_layer: external cyclotomic construction with a separate scalar Modulus of One graph
variable_parameters: ordinary primes, denominator exponents, and point-window size
fixed_controls: each declared field and its integral basis within a comparison
construction_edges: prime factor, conjugate ratio, exponent increment, root phase
point_use_witness: exact box overlap for each unit displacement
graph_storage: explicit factor graphs and phase cycle; symbolic Cartesian product
scope_limit: no core promotion of external field elements; no global exponent claim
```

The twelve cases cover denominator 241 and 241^2 in all three fields,
5*13 in K_4, 17*41 in K_8, and 73,97,73^2,73*97 in K_24.
They are declared comparisons, not an exhaustive optimization over primes.

## New Prime Factors And Their Independent Checks

In K_24, put z=zeta_24 and choose

\[
\alpha=1+z+2z^3,\qquad \beta=1+z+z^2+z^4.
\]

Their field norms are 73 and 97. There are short witnesses using radicals:

\[
\alpha\overline\alpha
=6+\tfrac52\sqrt2+2\sqrt3+\tfrac12\sqrt6.
\]

Taking the sign change of sqrt(3) gives 35+24*sqrt(2), then

\[
35^2-2\cdot24^2=73.
\]

Similarly,

\[
\beta\overline\beta=5+2\sqrt2+2\sqrt3+\sqrt6,
\]

whose next relative norm is 15+8*sqrt(2), and

\[
15^2-2\cdot8^2=97.
\]

Both rational primes are 1 modulo 24. The report supplies all eight modular
roots, every conjugate seed, its norm, and its unique zero among those roots.
For automorphisms 1,5,7,11,13,17,19,23, the zero lists are respectively

```text
73: 52, 30, 17,  7, 21, 43, 56, 66
97: 54,  4, 24, 88, 43, 93, 73,  9
```

Each norm-prime element generates a principal prime ideal. The distinct
conjugates give four independent conjugate pairs above each ordinary prime;
different ordinary primes have disjoint valuation support. These facts are
verified for the selected seeds, rather than inferred from splitting alone.

The smaller-field witnesses are 2+i and 3+2i in K_4, with norms 5 and 13;
and 1+2*zeta_8 and 1+zeta_8+zeta_8^2+2*zeta_8^3 in K_8, with norms 17 and 41.

## Complete Direction Counts With Variable Exponents

For the explicitly verified principal split primes, let D=product_p p^(k_p).
For each of the f conjugate pairs above p, write q_(p,j)=alpha_(p,j)/bar(alpha_(p,j)).
Every direction has a unique representation

\[
z=\zeta_m^t\prod_{p,j}q_{p,j}^{a_{p,j}},
\qquad -k_p\leq a_{p,j}\leq k_p,
\]

with t in 0,...,m-1. To see integrality, construct the numerator directly:

\[
Dz=\zeta_m^t\prod_{p,j}
\alpha_{p,j}^{k_p+a_{p,j}}
\overline\alpha_{p,j}^{k_p-a_{p,j}}.
\]

Valuations recover the exponents. Any direction in D^(-1)O_m with the same
valuation pattern differs by an integral unit whose conjugates have modulus
one, hence a root of unity. The completeness proof from the earlier note
therefore gives

\[
\boxed{M_m(D)=m\prod_{p\mid D}(2k_p+1)^f.}
\]

| Field | Denominator | Complete oriented unit directions |
| --- | ---: | ---: |
| K_4 | 241^2 = 58,081 | 20 |
| K_4 | 5*13 = 65 | 36 |
| K_8 | 241^2 = 58,081 | 200 |
| K_8 | 17*41 = 697 | 648 |
| K_24 | 73 | 1,944 |
| K_24 | 73^2 = 5,329 | 15,000 |
| K_24 | 241^2 = 58,081 | 15,000 |
| K_24 | 73*97 = 7,081 | 157,464 |

Of the last 157,464 directions, exactly 153,600 have least denominator 7,081;
1,920 have least denominator 73, another 1,920 have least denominator 97,
and 24 are roots of unity. Thus the growth is not duplicate representations
with inflated denominators. The report includes these denominator counts for
every case, checked against the coefficient gcds.

The branch count explains the difference: using two new prime-pair groups at
depth one contributes 3^(2f), whereas depth two for one prime contributes 5^f.
This is a direction-count comparison; the sizes of the primes and the ability
to use those directions in a point set still matter.

## Exact Point Use At Equal N

Use full-basis boxes

\[
P_{D,s}=\left\{D^{-1}\sum_{j=0}^{d-1}c_j\zeta_m^j:
0\leq c_j<s,\ c_j\in\mathbb Z\right\}.
\]

Their N=s^d points are distinct. If v is the integral numerator of an
available unit displacement, the exact count is

\[
2E=\sum_{v\in D U_m(D)}\prod_j(s-|v_j|)_+.
\]

The probe groups displacements with the same sorted absolute coefficient
profile. This preserves the product exactly; tests independently sum over
every ungrouped displacement to check the compression.

For the cross-field table in the report, the coefficient side is T^(8/d),
so every case at the same T has N=T^8 points. Within K_24, take T=s=8,192:

| Denominator | Directions M | Average unit neighbors 2E/N | Retention 2E/(NM) |
| --- | ---: | ---: | ---: |
| 73 | 1,944 | 1,901.12185 | 0.97794 |
| 97 | 1,944 | 1,886.20367 | 0.97027 |
| 241 | 1,944 | 1,803.23042 | 0.92759 |
| 73^2 | 15,000 | 1,970.39007 | 0.13136 |
| 241^2 | 15,000 | 0 | 0 |
| 73*97 | 157,464 | 7,751.43471 | 0.04923 |

These are exact integer counts presented with rounded averages. The common
N=8,192^8 and each E are stored as decimal strings. No huge point sets were
enumerated. All 157,464 mixed-prime directions occur somewhere at this size;
low retention means low average use per point, not absence of those directions.

## An Upper Bound Covering Every Denominator In A Fixed CM Field

Now drop the selected-prime and principality assumptions. Let K be any fixed
CM field of degree 2f, with w roots of unity, and D any positive integer.
Write tau(n) for the number of positive divisors of n. Then

\[
\boxed{|U_K(D)|\leq w\,\tau(D^2)^f.}
\]

Here is the complete valuation argument. For p^a exactly dividing D,
integrality of Dz gives v_P(z)>=-a*e_P. The identity z*bar(z)=1 gives
v_P(z)+v_bar(P)(z)=0. A self-conjugate prime therefore has valuation zero.
A distinct conjugate pair with ramification index e_P has at most 2a*e_P+1
possible valuations. Outside D all valuations vanish.

If r_P is the residue degree, the field degree identity gives

\[
2\sum_{\{P,\overline P\},\,P\ne\overline P}e_P r_P\leq2f,
\quad\hbox{hence}\quad \sum_{\rm pairs}e_P\leq f.
\]

Since 2a*e+1<=(2a+1)^e, there are at most (2a+1)^f patterns above p.
Two realized elements with the same valuations have an integral-unit quotient
with all conjugates on the unit circle. That quotient is a root of unity, so
each pattern contributes at most w elements. Multiplying over p proves the
bound. Nonprincipal ideals can only remove patterns from this upper count.
The standard CM unit fact is explained by the kernel argument in
[Conrad's unit theorem notes, pages 6-7](https://kconrad.math.uconn.edu/blurbs/gradnumthy/unittheorem.pdf).

For completeness, the divisor estimate needed below is elementary. Fix eta>0.
For primes p>=2^(1/eta), b+1<=2^b<=p^(eta*b). For each of the finitely many
smaller primes, sup_(b>=0) (b+1)/p^(eta*b) is finite. Multiplying these bounds
over the prime factorization of n gives tau(n)<=C_eta*n^eta. Consequently
tau(D^2)=D^(o(1)), uniformly over all positive integers D as D grows.

### A Finite Separation From Every Single-Prime-Square Denominator

The new upper bound strengthens the finite comparison. For every rational
prime p in K_24, regardless of splitting or principality,

\[
M_{K_{24}}(p)\leq24\cdot3^4=1,944,\qquad
M_{K_{24}}(p^2)\leq24\cdot5^4=15,000.
\]

These are caps on average unit degree for **any** point selection whose
pairwise differences lie in p^(-1)O_24 or p^(-2)O_24, respectively.
They are not restricted to our box rule, and p may vary with N.

For D=7,081, the exact box averages cross these caps as follows:

| Cap | Last side below the cap | Average there | First side above the cap | Average there |
| ---: | ---: | ---: | ---: | ---: |
| 1,944 | 6,453 | 1,943.04651 | 6,454 | 1,945.26914 |
| 15,000 | 9,805 | 14,996.17366 | 9,806 | 15,000.86037 |

The report preserves exact integer inequalities at all four boundaries.
For fixed D the normalized overlap sum is nondecreasing in s. Therefore, for
every s>=9,806, the mixed-prime box has more unit pairs than every equal-N
configuration in K_24 whose common difference denominator divides the square
of any one rational prime. The analogous prime-denominator statement holds
from s=6,454.

These are first crossings of the uniform caps. They need not be the earliest
sizes at which the class comparisons hold. They do not cover larger prime
powers, other mixed denominators, growing fields, or arbitrary planar sets.

## Why Full Boxes Still Cannot Improve The Asymptotic Exponent

Allow arbitrary rectangular side lengths s_j>=1 and arbitrary D, while
keeping the field and integral basis fixed. For the cyclotomic power bases,
an existing unit edge requires

\[
D=\left|\sum_j a_j\zeta_m^j\right|
\leq\sum_j(s_j-1)\leq\prod_j s_j-1=N-1.
\]

The last inequality follows by expanding product_j(1+(s_j-1)). For another
fixed integral basis, multiply the right-hand bound by the fixed maximum B
of the complex magnitudes of its basis elements. If D>B(N-1), the box has
no unit edge at all.

Otherwise the direction bound gives

\[
E\leq\frac{N}{2}|U_K(D)|\leq\frac{wN}{2}\tau(D^2)^f.
\]

Apply the elementary divisor estimate with eta=epsilon/(2f), using
D<=B*N. For every epsilon>0 there is a constant C depending only on the
fixed field, basis, and epsilon such that

\[
\boxed{E\leq C N^{1+\varepsilon}}
\]

for every integer D and every rectangle. In particular, this family cannot
achieve E>=c*N^(1+delta) for fixed c,delta>0 along N tending to infinity:
choose epsilon=delta/2 to get a contradiction. This is an upper bound;
it does not assert a limiting exponent of exactly one for empty or sparse
edge sets. A finite choice among our three fields also obeys the bound by
taking the largest of their constants.

## A Necessary Growth Condition For More Selective Point Sets

There is a useful consequence that does not require boxes. For any finite
point set P with differences in fixed K, define the least difference denominator

\[
D(P)=\min\{D\in\mathbb Z_{>0}:D(P-P)\subseteq O_K\}.
\]

This is translation invariant. It equals the least common denominator of
P-x_0 for any one chosen point x_0. The same available-direction bound applies
to every point selection:

\[
E(P)\leq\tfrac12 N\,M_K(D(P)).
\]

If D(P)<=N^C for a fixed C, then E<=C_epsilon*N^(1+epsilon) for every epsilon>0.
Consequently a sequence in fixed K with E>=c*N^(1+delta), fixed c,delta>0,
must satisfy

\[
\boxed{\frac{\log D(P)}{\log N}\longrightarrow\infty.}
\]

Indeed, if D<=N^C on an infinite subsequence, use M_K(D)<=A_theta*D^theta
with theta=delta/(2C) to contradict that lower bound. The conclusion applies
along the sequence on which the assumed lower bound holds.

This is a necessary condition, not an impossibility theorem. For even t,

\[
q_t=\frac{t^2-1+2ti}{t^2+1}
\]

has unit length and least denominator t^2+1. The two points {0,q_t} already
have unbounded denominator. More strongly, choosing t=2^N and points
{0,q_t,2q_t,...,(N-1)q_t} gives a denominator growing faster than every fixed
power of N but only N-1 unit pairs. Large denominators alone do not supply
the required endpoint reuse.

## What This Changes About The Next Step

The finite comparisons favor introducing new independent prime factors over
the particular repeated-prime choices tested. They do not establish a general
prime-selection optimizer. The denominator may vary throughout future work.

The full-box upper bound now supplies a reason to stop optimizing these boxes
solely for a sustained exponent gain in a fixed field. A successor must change
that point assembly enough to escape its denominator-versus-N bound, or use
arithmetic fields for which the fixed-field argument is no longer uniform.
For a fixed-field successor, track the least difference denominator and N
before doing a large geometric search; polynomial denominator growth is a
proved obstruction to the requested exponent gain.

Any sparse construction must also supply actual repeated neighborhoods. Merely
placing one point in every available unit direction around a center gives at
most two additional neighbors on the unit circle per outer point, hence at
most 2*(N-1) unit pairs. In K_24 our direction set is closed under rotations
by 60 degrees, so adding the center to all 157,464 directions yields exactly
157,465 points and 314,928 unit pairs. This follows from elementary circle
geometry, not an exhaustive pair search. It is another simple assembly control,
not a proposed exponent improvement.

## Evidence, Review, And Reproduction

- [Probe](../../../moo/variable_denominator_probe.py).
- [Seven focused tests](../../../tests/test_moo_variable_denominator_probe.py).
- [Completed version 1 evidence](results/2026-09-11-variable-denominator-v1.json).

The report has twelve exact cases and 132 equal-point comparison rows. Its
factor graphs, conjugate-prime witnesses, and phase cycles are explicit. The
Cartesian-product direction graph is specified by its node and edge rules,
not serialized in full. All 194,284 direction occurrences across the cases
were enumerated for exact counts and hashing, and their unit norms were checked
using independent polynomial long division. The largest case has 157,464
directions, grouped into 19,286 exact overlap profiles. Its symbolic product
graph has 997,272 edges.

The critique agent independently verified the new radical norm identities,
the valuation bound, the arbitrary-denominator box argument, the necessary
denominator-growth condition, and the scope of the denominator-class caps.
It did not independently rerun the large box counts. The primary agent checked
those against ungrouped displacement sums and verified the strict integer
inequalities at the four cap boundaries. The focused tests also enumerate
Gaussian unit directions for all 1<=D<=500 and check a small point set by
exhaustive pair comparison.

The scalar Modulus of One graph reaches 241 on the positive spine. It records products
65,697,5329,7081,58081 from confirmed operands. The last four outputs remain
speculative and are never used as operands. The external field calculations
do not promote those nodes or alter the core export shape.

```text
python -B -m unittest test_moo_variable_denominator_probe -v
python -B -m moo.variable_denominator_probe
python -B -m moo.variable_denominator_probe --output path/to/a-new-version.json
```

The standard-library-only probe refuses to overwrite a report. The completed
JSON is 1,864,899 bytes. The seven new tests passed in 14.279 seconds on the
bundled Python 3.12.14 runtime. All 25 earlier unit-distance tests passed again,
for 32 passing tests across the four tools. The core demo at limit 3 passed;
59 local links resolved. Separate checks verified all twelve least-denominator
histograms, the 132 exact averages, and the 48 unit pairs in a 25-point
roots-plus-center control. Earlier completed reports were preserved.

Version 1 report SHA-256:
`0db03fbcb6b39a988d7ef817fd5414fce31ff8cf6527fed0dd6390ee30802088`.
