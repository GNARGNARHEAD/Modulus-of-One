# One Prime, More Branches, And The Cost Of Using Them

Date: 2026-09-10.

The bounded example has a positive result: enlarging the arithmetic can
increase the number of unit directions supplied by **one fixed prime**, with
the same denominator. For prime 241, the three fields below have exactly
12, 72, and 1,944 available oriented unit directions.

The assembly of points matters just as much. A grid made only from the chosen
generators uses 2, 4, and 8 of those directions. A grid using a full arithmetic
basis can use all of them. An exact counting formula compares these larger
point sets without enumerating their points. In the equal-point comparison
defined below, the middle field takes the lead at T=18; the largest takes
the lead at T=259 and stays ahead for every larger integer T.

These thresholds are specific to the declared bases, denominator, and point
families. They are not universal optimal spacings, exponent estimates, or a
record for the Erdos problem. The calculations and proof arguments are locally
checked. The three fields are finite examples, not an asserted infinite tower.

## Rule, Scope, And The Arithmetic Levels

Let zeta_m=exp(2*pi*i/m), and use

\[
K_4=\mathbb Q(i)\subset K_8=\mathbb Q(i,\sqrt2)
\subset K_{24}=\mathbb Q(i,\sqrt2,\sqrt3).
\]

Equivalently K_m=Q(zeta_m), for m=4,8,24. Write d=[K_m:Q] and f=d/2.
The integer ring is O_m=Z[zeta_m], with basis 1,zeta_m,...,zeta_m^(d-1).
The relevant minimal polynomials are

\[
\Phi_4(X)=X^2+1,\quad\Phi_8(X)=X^4+1,\quad
\Phi_{24}(X)=X^8-X^4+1.
\]

These power-basis and degree facts are standard; see Theorem 6.4 in
[Milne's Algebraic Number Theory](https://www.jmilne.org/math/CourseNotes/ANT.pdf).
All points are viewed in one fixed complex embedding, hence in the plane.
Higher field degree here counts independent rational coordinates. It does not
mean the geometric point set is in a higher-dimensional Euclidean space.

The probe uses exact integer coefficient vectors in these bases. The common
coordinate denominator is p=241, and the available unit set is

\[
U_m=\{z\in p^{-1}O_m:z\overline z=1\}.
\]

The field embedding is injective. Thus this algebraic norm identity is exactly
the planar unit-length condition; it also implies unit length in every
conjugate embedding, because the cyclotomic automorphisms commute with
complex conjugation.

### Branch card

```text
branch_name: conjugate-factor ratio and multiplication, followed by additive assembly
moo_relation: scalar product/addition agreement is witnessed; field arithmetic is external
operator_fan_root: product, ratio, and addition
active_field: scalar positive spine to 256; external K_4, K_8, K_24
eligible_sources: confirmed scalar operands in core; declared cyclotomic elements externally
witness_event: prime-factor root, conjugate ratio, multiplication edge, unit-difference edge
shadow_values: coefficient vectors for unit directions and planar point positions
membership_reading: retain the construction and norm witness for each direction
non_membership_reading: absence from one additive span does not mean absence from U_m
linearity_reading: the same conjugate-ratio and multiplication relations repeat
relation_distance: external factor/exponent steps; no invented core Modulus of One distance
stage_distance: arithmetic level m is separate from positive-spine iteration
witness_depth: factor, ratio, product, and additive-use witnesses are distinct
interaction_reading: a direction is used when two retained endpoints differ by it
machine_fields: modular roots, factors, exponents, graph edges, coefficient spans, exact pair counts
known_classical_shadow: split primes in cyclotomic fields and finite lattice-box overlaps
allowed_claim_language: exact counts and crossover within the specified point families
disallowed_claim_language: infinite field tower proved here; global optimal exponent or spacing
weakening_or_kill_rule: no graph growth based only on available directions or finite log slopes
```

## How 241 Supplies More Independent Factor Branches

The three selected algebraic integers are

\[
\alpha_4=15-4i,\qquad
\alpha_8=4-\zeta_8^2-2\zeta_8^3,\qquad
\alpha_{24}=2+\zeta_{24}.
\]

Each has field norm 241. In particular,

\[
15^2+4^2=241,\qquad \Phi_{24}(-2)=2^8-2^4+1=241.
\]

These choices form an actual refinement. Taking the relative norm of
alpha_24 down to K_8 gives alpha_8; taking the relative norm of alpha_8 down
to K_4 gives alpha_4. These are checked as polynomial identities, not inferred
from numerical magnitudes.

The prime 241 splits into d different prime ideals in each K_m. The conjugates
of alpha_m generate them. To witness their distinctness, the report gives
every root of Phi_m modulo 241 and the unique root at which each conjugate
vanishes. A convenient primitive root for zeta_m is

\[
r_m=(-2)^{24/m}\pmod{241}.
\]

The conjugate generators have norm 241 and their product is exactly 241.
Consequently they supply f distinct pairs (P_j, conjugate(P_j)).
For one representative alpha_j from each pair define

\[
q_j=\alpha_j/\overline{\alpha_j}.
\]

Each q_j has unit length in every embedding. Its prime valuations are +1 at
P_j, -1 at conjugate(P_j), and zero at the other primes above 241. Therefore
the q_j are multiplicatively independent: a product equal to 1 must have
zero exponent at every pair.

For representatives t=(1) at m=4, t=(1,3) at m=8, and t=(1,5,7,11) at m=24,
the retained parent/child identities are

\[
q_{4,1}=q_{8,1}/q_{8,3},\qquad
q_{8,1}=q_{24,1}/q_{24,7},\qquad
q_{8,3}=q_{24,11}/q_{24,5}.
\]

The old branch is thus expressed through new factor branches after extending
the field. This example involves one ordinary rational prime throughout.

## Why The Denominator Does Not Multiply With The Branch Count

For each pair choose an exponent a_j in {-1,0,1}. The products

\[
w=\zeta_m^t\prod_{j=1}^{f}q_j^{a_j}
\]

all have denominator dividing **241**, even when several q_j are multiplied.
Each conjugate prime factor appears in a denominator at most once, and their
full product already divides 241.

An explicit integer numerator makes the cancellation reviewable:

\[
p w=\zeta_m^t\prod_j F_j(a_j),\qquad
F_j(1)=\alpha_j^2,\quad F_j(0)=\alpha_j\overline\alpha_j,
\quad F_j(-1)=\overline\alpha_j^2.
\]

The program constructs this numerator directly. It checks its product with
its conjugate is p^2. This shared denominator is the feature that independent
powers of two fixed Gaussian seeds did not provide as their depths increased.

Here a common denominator D means that D*w is an algebraic integer in the
specified field. This is a statement about integral-basis coefficients;
the real and imaginary coordinates need not be rational numbers.

The exponent restriction is essential. The additive module p^(-1)O_m is not
closed under arbitrary multiplication. Already in the first field,

\[
q_{4,1}=\frac{209-120i}{241},\qquad
q_{4,1}^2=\frac{29281-50160i}{58081}.
\]

Since gcd(29281,50160,58081)=1 and 58081=241^2, the square cannot be written
with denominator 241 in Z[i]. Combining different prime-pair branches within
the declared exponent budget preserves 241; repeating one branch beyond that
budget can require higher powers. The retained multiplication graph only
includes moves that stay inside the exponent budget.

There are m distinct root-of-unity phases in these even-order cyclotomic
fields; see Theorem 4.1 in
[Conrad's Cyclotomic Extensions](https://kconrad.math.uconn.edu/blurbs/galoistheory/cyclotomic.pdf).
The exponent vector is recoverable from prime valuations, and the remaining
phase is unique. Therefore all m*3^f constructed directions are distinct.

They are also the **complete** unit set in p^(-1)O_m. If z belongs to that set,
its prime valuations outside 241 are zero, while each conjugate pair above
241 has valuations (a_j,-a_j), with a_j in {-1,0,1}. Dividing by the
corresponding product of q_j leaves an algebraic unit with all conjugates on
the unit circle. Such a unit is a root of unity; the kernel argument on pages
6-7 of [Conrad's unit theorem notes](https://kconrad.math.uconn.edu/blurbs/gradnumthy/unittheorem.pdf)
supplies this standard fact. Hence the constructed list exhausts U_m.

| Field | Rational basis dimension d | Independent prime pairs f | Prime-exponent choices | Root phases | Complete oriented unit directions M |
| --- | ---: | ---: | ---: | ---: | ---: |
| K_4 | 2 | 1 | 3 | 4 | 12 |
| K_8 | 4 | 2 | 9 | 8 | 72 |
| K_24 | 8 | 4 | 81 | 24 | 1,944 |

The table separates the gain from independent prime choices from the gain
from additional root-of-unity phases. Opposite directions are counted
separately; unordered point pairs will be counted once.

For these particular fields, the same valuation proof gives
|{z in p^(-k)O_m: z*conjugate(z)=1}|=m*(2k+1)^f for every integer k>=0.
Only k=1 was enumerated in this run.

## A Simple Generator Grid Fails To Use Most Directions

First try points whose generator coefficients independently range from
0 through s-1:

\[
P^{\rm gen}_{m,s}=\left\{\sum_{j=1}^{f}c_jq_j:
0\leq c_j<s,\ c_j\in\mathbb Z\right\}.
\]

The q_j are rationally independent. This is checked by exact matrix rank;
it also follows by taking a coefficient with minimal p-adic valuation and
examining the unique pole of its q_j. Thus N=s^f, with no duplicate positions.

The complete U_m list can be intersected with the integer span of the q_j by
exact linear algebra. At all three levels, the only unit steps in that span
are +q_j and -q_j. The check covers every member of U_m, so enlarging s cannot
activate a missed direction. Consequently

\[
E=f(s-1)s^{f-1}\quad\hbox{for every integer }s\geq1.
\]

| Field | Available directions | Directions used by generator grid | Points at s=5 | Unit pairs at s=5 |
| --- | ---: | ---: | ---: | ---: |
| K_4 | 12 | 2 | 5 | 4 |
| K_8 | 72 | 4 | 25 | 40 |
| K_24 | 1,944 | 8 | 625 | 2,000 |

At K_8 the rational span contains eight unit directions, but only four have
integer generator coefficients. At K_24 even the rational span contains only
eight. These are different obstructions, both recorded in the report.

The retained side-3 graphs have 3, 9, and 81 distinct points. Their addition
edges are all their unit edges, checked by an independent exhaustive pair
comparison. This diagnoses the assembly rule, not a shortage in U_m.

## Full-Basis Boxes: Count Without Enumerating Points

Now allow coefficients along the entire integral basis:

\[
P_{m,s}=\left\{\frac1p\sum_{j=0}^{d-1}c_j\zeta_m^j:
0\leq c_j<s,\ c_j\in\mathbb Z\right\}.
\]

Distinct coefficient vectors give distinct complex points, so N=s^d exactly.
If a unit direction has numerator vector v=(v_0,...,v_(d-1)), the number of
ordered endpoint pairs with that displacement is

\[
\prod_{j=0}^{d-1}(s-|v_j|)_+,\qquad x_+=\max(x,0).
\]

This counts the intersection of an integer coefficient box with its translate
by v. Every unit displacement between two points belongs to the complete U_m
list. Therefore the following is an exact all-pairs formula:

\[
\boxed{N=s^d,\qquad
2E=\sum_{v\in pU_m}\prod_{j=0}^{d-1}(s-|v_j|)_+.}
\]

Only 12, 72, or 1,944 displacement vectors must be processed, regardless of
how many points the formula describes. The largest numerator coefficients are
241, 241, and 255 respectively. A direction becomes usable when every
coordinate shift fits, but its frequency of use can still be low near the
boundary.

### An exact comparison at equal point counts

For an integer T>=1 set the three coefficient side lengths to T^4, T^2, and T.
Then all three constructions have exactly N=T^8 distinct points. Compare
their average number of unit neighbors, 2E/N:

| T | K_4 | K_8 | K_24 |
| ---: | ---: | ---: | ---: |
| 18 | 11.9658 | 14.1593 | 0 |
| 128 | 12.0000 | 70.3398 | 0.00874 |
| 258 | 12.0000 | 71.5891 | 70.9696 |
| 259 | 12.0000 | 71.5923 | 72.5627 |
| 512 | 12.0000 | 71.8955 | 507.5892 |

Displayed averages are rounded. The saved counts and comparison signs use
exact integers. For example at T=259, every point set has

\[
N=20,248,745,068,443,234,721,
\]

and the K_8 and K_24 unit-pair counts are respectively

\[
724,826,742,921,056,397,376,
\qquad734,651,529,941,326,792,096.
\]

These huge point sets were specified and counted algebraically, not generated
or sampled. Their large sizes are an effect of the declared comparison rule;
there is no claim of a computationally materialized configuration.

All integer T from 1 through 512 were checked. The winners are:

- T=1,2,3: all three have zero unit pairs.
- 4<=T<=17: K_4 wins.
- 18<=T<=258: K_8 wins.
- T>=259: K_24 wins.

The last interval is proved beyond the finite scan. For each fixed field,
2E/N is a sum of products of factors (1-|v_j|/s)_+, and is nondecreasing in s.
It never exceeds M. Already at T=18, the K_8 average exceeds 12, the absolute
direction cap of K_4. At T=259, the K_24 average exceeds 72, the cap of both
smaller levels. Therefore those dominance claims persist for every larger T.

At T=258 all 1,944 K_24 directions occur somewhere, yet their average use is
still below the K_8 average. The crossover measures repeated endpoint use,
not merely whether a direction appears. It is a concrete prediction for these
families; changing the basis or point-window rule can change the threshold.

## What Happens At Infinity

For any one of the three fixed fields, U_m is finite. The overlap formula gives

\[
\lim_{s\to\infty}\frac{2E}{N}=M,
\qquad \lim_{s\to\infty}\frac{\log E}{\log N}=1.
\]

Thus the positive comparison above concerns which construction has more unit
pairs at the same point count. It does not produce a fixed power improvement
for arbitrarily large point sets from one fixed field and denominator.

There is also an exact obstruction to extending this *cyclotomic* example
forever while keeping 241 completely split. Complete unramified splitting in
Q(zeta_m) requires 241=1 modulo m, since reduction must supply a primitive
m-th root in F_241. Hence m divides 240. The largest compatible field degree
is phi(240)=64. The compatible conductors and their degrees are saved in the
report. This stops an infinite continuation made only by adjoining more roots
of unity with the same splitting prime; it does not stop other field towers.

The successful published construction uses growing field degree with bounded
root discriminant and controlled prime splitting. Its two main counting steps
are described in [the companion paper, Lemmas 2.1 and 2.2](https://arxiv.org/html/2605.20695v1).
Our finite example makes the independent factor choices and shared denominator
explicit. Its principal prime generators suffice for the complete count, but
individual principal generators are not necessary for a controlled-denominator
collection. Nonprincipal prime ideals do not themselves force new rational
primes into the denominator.

More precisely, Lemma 2.2 gives the following conditional statement. For a
CM field of degree 2f, one completely split unramified rational prime p,
and a fixed positive integer budget k, it supplies at least

\[
\frac{(k+1)^f}{h(K)}
\]

unit directions in p^(-2k)O_K, using ratios of ideal products in the same ideal
class. The rational denominator D=p^(2k) depends on k, not f. In a suitable
infinite family, k can be chosen once. The class number h(K) reduces the
guaranteed direction count; it does not introduce a degree-dependent power
of p in this bound. This does not establish that denominator p alone,
or specifically D=241, supplies enough directions indefinitely.

For a proposed infinite family, define the retained fraction

\[
\rho=\frac{2E}{NM}.
\]

Then the identity

\[
\frac{\log E}{\log N}
=1+\frac{\log M+\log\rho-\log2}{\log N}
\]

states the next gate precisely. Direction growth must overcome the loss from
directions that do not connect retained points, relative to point growth.
Three finite field levels do not establish that balance along an infinite
sequence.

### Allowing The Denominator To Grow

Clarification, 2026-09-11: fixing D=241 isolated the effect of changing fields
in this experiment. The unit-distance problem imposes no fixed-denominator
condition. Neither this finite result nor the earlier fixed-seed obstruction
proves that every successful construction must keep D fixed or use growing
field degree. The proposed fixed-denominator continuation is one research
option, not a necessary next step.

The geometry bound itself permits varying D. In Lemma 2.1 of the companion
paper, take the Minkowski lattice D^(-1)O_K, degree 2f, window radius R=2,
delta=D^(-1), u=M^(1/f), and v=rd(K)/2, where rd denotes root discriminant.
Then the lemma supplies a point set with

\[
N\leq B^f,\qquad 2E\geq(BG)^f,\qquad
B=36D^2,\quad G=\frac{\pi M^{1/f}}{36v}.
\]

For G>1 this certifies

\[
E\geq\frac12 N^{1+\varepsilon},\qquad
\varepsilon=\frac{\log G}{\log(36D^2)}.
\]

This is a direct rearrangement of the cited lemma, not an optimal-exponent
formula. Along a proposed sequence, a sufficient condition is that these
epsilon values stay above one fixed positive number and the produced point
counts tend to infinity. D may grow: the gain log(G) must compensate for
log(36D^2) in this particular bound. A vanishing certificate does not prove
the underlying point sets cannot do better.

**Revised next obligation:** allow field degree, denominator, and prime-factor
choices to vary, and account jointly for available directions and their use
by actual point sets. Compare explicit constructions through their N and E
bounds. A denominator restriction needs an experimental or mathematical
justification specific to the construction. The existing box formula remains
an exact finite control, and the degree-64 ceiling still applies to the
specific cyclotomic continuation with 241 completely split.

The [2026-09-11 variable-denominator continuation](VARIABLE_DENOMINATOR_BRANCH_NOTE.md)
now carries out that comparison. It finds explicit improvements using 73 and
97, and proves a full-box upper bound covering every denominator in a fixed
CM field. That later result also derives a necessary denominator-growth
condition for more selective fixed-field point sets.

## Modulus of One Evidence, Tools, And Validation

The core calibration preserves incoming edges witnessing
15*15 + 4*4 = 241 and 2^8 - 2^4 + 1 = 241. Squares beyond the current frontier
are initially speculative, and the positive spine explicitly reaches them
before they become operands. The export has 256 grounded nodes and 262
arithmetic edges. No speculative operand mode was enabled.

Cyclotomic roots and field elements are declared external objects. Their
coefficient vectors, prime-factor witnesses, conjugate-ratio refinements,
and product edges are preserved in an external construction graph. This does
not add them as grounded nodes in the rational Modulus of One runtime. The scalar graph's
standard export shape is unchanged.

- [Probe](../../../moo/split_prime_branch_probe.py).
- [Independent checks](../../../tests/test_moo_split_prime_branch_probe.py).
- [Completed version 1 evidence](results/2026-09-10-split-prime-branch-v1.json).
- [Previous fixed-seed gate](FIXED_SEED_BRANCH_GATE_NOTE.md).

The report contains the complete direction lists, their construction edges,
all factor and refinement witnesses, small point graphs, all 512 exact
equal-point comparisons, and the finite cyclotomic growth ceiling. Large
point and pair counts are decimal strings so JSON readers cannot silently
round them to binary floating point. Approximate display averages are separate
from the exact rational numerators and denominators.

```text
python -m unittest test_moo_split_prime_branch_probe -v
python -m moo.split_prime_branch_probe
python -m moo.split_prime_branch_probe --output path/to/a-new-version.json
```

Nine new tests cover independent polynomial arithmetic, modular splitting,
unit norms, recovery of branch choices from poles, construction edges and
refinement identities, complete span intersections, exhaustive small geometry,
box overlaps, crossover and tail bounds, scalar eligibility, and input limits.
The combined run with the two previous unit-distance tools passed all 25 tests.
The core demo at limit 3 also completed successfully, and all 46 local Markdown
links in the touched research notes and indexes resolved.

The runtime was Python 3.12.14 at
`C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
The probe is standard-library-only and refuses to overwrite an existing report.

## Adversarial Review And Independent Recalculation

A second-agent critique on 2026-09-10 found no error in the stated finite
result. The primary agent checked the arguments and required runnable evidence
before accepting the computational findings. The reviewer's initial script
verified direction nodes but did not cover every construction edge implied by
its description. Those additional checks were implemented and run locally.

The retained [independent verifier](../../../moo/verify_split_prime_branch_report.py)
imports neither the probe nor its tests. It calculates in the radical basis
1,sqrt(2),sqrt(3),sqrt(6),i,i*sqrt(2),i*sqrt(3),i*sqrt(6). It obtains each q_j by
solving the division equation against its conjugate factor, then independently
converts the resulting directions into the declared integral bases.

The [completed critique evidence](results/2026-09-10-split-prime-critique-v1.json)
records successful checks of all 2,028 directions, all 7,316 multiplication
edges, the three parent/child ratio identities, distinct modular prime-factor
witnesses, rational and integer spans, and exhaustive unit-pair comparisons
for the small point graphs. All 512 exact equal-point count rows agree.
It also records the denominator counterexample above, the crossover thresholds,
and the cyclotomic degree ceiling. Both input and verifier SHA-256 hashes are
saved for reproducibility; the original version 1 report was unchanged.

```text
python -B -m moo.verify_split_prime_branch_report
```

The completeness proof still uses the stated algebraic number theory, and
permanent dominance still uses the monotonicity argument. The review supports
these finite results and their declared limits; it supplies no infinite tower
or new exponent certificate. The existing nine focused tests also passed again.
