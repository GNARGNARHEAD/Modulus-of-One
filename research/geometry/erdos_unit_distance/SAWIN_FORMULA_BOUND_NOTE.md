# A Finite Test Of An Infinite-Family Exponent

Date: 2026-09-10.

This investigation reproduced two existing lower-bound certificates and
derived a uniform upper relaxation for the original certificate formula.
The checked result is:

> Every admissible parameter choice in Sawin's unmodified equation (11)
> produces an exponent strictly less than 1.03503.

This is a restriction on that formula. It is **not** an upper bound on the
Erdos unit-distance problem, an exact optimum for this method, or a claim of
novelty in the mathematical literature. The proof argument and numerical
enclosures below have been checked locally, without independent review.

## Source And Reproduction

[Sawin's Lemma 12 and equation (11)](https://arxiv.org/html/2605.20579v1)
turn admissible finite prime data into a guarantee for arbitrarily large planar
point sets. Write the exponent as 1 + delta, with delta = N / D.

Let T be the selected odd primes, S the selected rational primes, k(p) positive
integers, and R > 1. Define

\[
L=\log\left(4\prod_{q\in T}q\right),\qquad
C(L)=\frac12\log(2\pi/e)-\frac L8-\frac12\log(L/2).
\]

The formula is

\[
N=C(L)+\log(1-1/R)+
  \sum_{p\in S}\frac{\log(k(p)+1)}{4e(p)},
\]

\[
D=\log\left(2R\prod_{p\in S}p^{k(p)/(2e(p))}+1\right),
\]

where e(p)=2 for p=2 or p in T, and e(p)=1 otherwise.

The required budget is

\[
|T|+|S|+|\{p\in S:p\text{ splits in }\mathbb Q(\sqrt{\prod T})\}|+1
\leq (|T|-1)^2/4.
\]

The tool also checks primality, the parity condition on T, and a local
inertness or congruence witness for every prime in S.

| Reproduction | T size | S size | Split count | Evaluated exponent |
| --- | ---: | ---: | ---: | --- |
| Sawin's displayed data | 13 | 22 | 0 | 1.014114428678498238894... |
| Reoptimized published T | 74 | 1092 | 165 | 1.031883065539639663060... |

The second T is the first 74 odd primes, removing 347, 353, 379 and adding
503, 601, 631, as specified in
[spiderduckpig's original MathOverflow answer](https://mathoverflow.net/questions/511514/what-is-the-unit-distance-exponent).
S and the multiplicities were recomputed locally, rather than copied.
Its budget use is 1257 out of 1257.

The [saved report](results/2026-09-10-sawin-formula-investigation-v1.json)
contains all integer data and 70-significant-digit interval endpoints. These
reproductions are validations of existing mathematics, not new records.

## Derivation Of The Uniform Upper Relaxation

The following is the argument developed in this investigation. It applies to
all finite T satisfying the original theorem, not just the two examples.

### 1. Test a proposed exponent

Fix a positive rational target eta. A certificate reaching exponent 1 + eta
would require N - eta D >= 0.

Omit the positive correction inside the logarithm by defining

\[
D_0=\log(2R)+\sum_{p\in S}\frac{k(p)\log p}{2e(p)}<D.
\]

Therefore

\[
N-\eta D\leq C(L)+B_\eta(R)+
 \sum_{p\in S}
 \frac{\log(k(p)+1)-2\eta k(p)\log p}{4e(p)},
\]

where

\[
B_\eta(R)=\log(1-1/R)-\eta\log(2R).
\]

This inequality has the useful direction: making its right side negative
excludes the proposed exponent in the original formula.

### 2. Eliminate the radius analytically

Differentiation gives

\[
B_\eta'(R)=\frac{1-\eta(R-1)}{R(R-1)}.
\]

Its unique maximum on R > 1 is at

\[
R_\eta=1+1/\eta.
\]

This eliminates an unbounded continuous search. It optimizes the residual
N - eta D0, not the exact quotient N / D.

### 3. Give every prime its most favorable contribution

Define

\[
g_\eta(p)=\frac14\max_{k\in\mathbb Z_{\geq0}}
 \bigl(\log(k+1)-2\eta k\log p\bigr).
\]

Each summand in step 1 is at most g_eta(p). For a negative summand, the
zero choice is an upper bound. For a positive summand, replacing e(p) by 1
can only increase it. Inertness restrictions can also be discarded when
forming an upper bound.

The maximizing integer can be obtained from adjacent differences:

\[
k=\left\lfloor\frac1{p^{2\eta}-1}\right\rfloor,
\]

allowing a tie with the adjacent integer. The implementation uses exact
integer powers to verify the maximizing choice.

There is an exact finite prime cutoff:

\[
g_\eta(p)>0\quad\Longleftrightarrow\quad
p<2^{1/(2\eta)}.
\]

Indeed, k=1 gives positive profit below this cutoff. At or above it,
k+1 <= 2^k <= p^(2 eta k) for every integer k >= 1.

### 4. Bound every choice of T by its size

Put t=|T|. The budget implies

\[
|S|\leq K(t):=
\left\lfloor\frac{(t-1)^2}{4}-t-1\right\rfloor.
\]

Every valid case has t >= 7. Let p_i be the increasing rational primes
starting with 2, and q_i the increasing odd primes starting with 3.

For fixed k the prime profit decreases with p, so its maximum g_eta(p)
also decreases with p. Consequently

\[
\sum_{p\in S}g_\eta(p)
\leq \sum_{i=1}^{K(t)}g_\eta(p_i).
\]

Meanwhile

\[
L\geq L_t:=\log4+\sum_{i=1}^t\log q_i.
\]

C(L) is strictly decreasing for L > 0. Replacing L by L_t enlarges the
bound. This even ignores whether the smallest t odd primes satisfy the
parity condition, so it cannot exclude a valid T by accident.

For the numerical upper bound, replace pi by the strictly larger 22/7:

\[
C_+(L)=\frac12\log(44/7)-\frac12-\frac L8-\frac12\log(L/2).
\]

The classical inequality pi < 22/7 can, for example, be witnessed by the
positive integral

\[
22/7-\pi=\int_0^1\frac{x^4(1-x)^4}{1+x^2}\,dx>0.
\]

We have now obtained

\[
N-\eta D\leq
U_t(\eta):=
C_+(L_t)+B_\eta(R_\eta)+
\sum_{i=1}^{K(t)}g_\eta(p_i).
\]

All potentially incompatible favorable choices are being granted together:
smallest possible discriminant, no ramification discount, no split-prime
penalty, and no local admissibility obstruction. That makes U an upper bound,
not a proposed realizable field construction.

### 5. Close the infinite tail

Let m be the number of positive-profit primes. Once K(t) >= m, the prime
sum has saturated. As t increases further, L_t increases and C_+(L_t)
strictly decreases. Thus U_t decreases throughout the remaining infinite tail.

It suffices to check the finite list ending at the first t with K(t) >= m.
There is no empirical extrapolation in this step.

## Checked Threshold: 1.03503

Choose

\[
\eta=3503/100000=0.03503.
\]

The exact prime-cutoff comparison is p^3503 < 2^50000. It gives:

| Quantity | Value |
| --- | --- |
| Largest integer below the cutoff | 19803 |
| Last profitable prime | 19801 |
| Number of profitable primes m | 2241 |
| Largest optimal multiplicity | 20 |
| Finite t cases | 7 through 98 |
| K(97), K(98) | 2206, 2253 |
| Largest upper-bound residual occurs at | t=45, K(t)=438 |

Directed interval evaluation gives the conservative statement

\[
\max_{7\leq t\leq98} U_t(\eta)<-0.00492623<0.
\]

The tail argument covers every t > 98. Hence N - eta D < 0 for every
admissible parameter choice, proving the stated restriction on equation (11).

The deliberately relaxed upper envelope is not the attainable optimum of
the formula. Its largest case t=45 is not evidence that a real optimal
construction has 45 primes.

## Numerical Trust Boundary And Tests

The search for S uses a fractional objective and a weight-1/weight-2 knapsack
calculation. Floating-point comparisons in that search make proposals only;
no global optimality claim is made for the returned lower certificate.

The formula evaluations and upper certificate use outward-rounded Decimal
intervals. Natural logarithm and exponential rely on their documented correct
rounding, with neighboring representable numbers used as enclosure endpoints.
See the [Python Decimal documentation](https://docs.python.org/3/library/decimal.html).

For the lower-bound reproductions, pi is enclosed using Machin's identity
and exact rational alternating-series remainders. The +1 in equation (11)'s
denominator is retained. The upper proof instead uses pi < 22/7.

Integer primality, Legendre-symbol witnesses, cutoff inequalities, and
adjacent-multiplicity comparisons are exact. The complete calculation remains
an ordinary mathematical argument plus a small numerical certificate, not a
proof-assistant formalization.

Eight focused tests passed. They include a rational atanh-series check
independent of Decimal.ln, exhaustive small knapsack comparisons, rejection of
invalid certificates, interval refinement, and infinite-tail accounting.
A lower target eta=0.035 remains permitted by the relaxation, checking that
the program does not simply reject every target.

On this machine the runtime used was:

~~~text
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
~~~

Reproduce without writing a report:

~~~text
python -m unittest test_erdos_unit_distance_certificate -v
python -m moo.erdos_unit_distance_certificate --precision 70 --target-delta 0.03503
~~~

## Structural Continuation: Count Overlap Directly

The useful consequence of the ceiling is that larger prime searches in
equation (11) cannot reach the reported values around 1.0358. The
[MathOverflow refinements](https://mathoverflow.net/questions/511514/what-is-the-unit-distance-exponent)
change arithmetic and geometric estimates. The thread also corrects some
earlier claims above 1.036; those should not be imported from an older summary
as established bounds. The complete modified certificate has not been audited
here.

One geometric component can be understood directly. The following derivation
checks the ball-overlap idea already described by Naslund in that discussion.

Let Lambda be a full lattice in R^m, and let V contain M lattice vectors
of norm one, each mapping injectively and additively to a planar unit vector.
For a translated ball W_w=B_R(w), average over w in a fundamental domain.
If N_w counts lattice points and E_w counts directed pairs whose differences
are in V, then

\[
\mathbb E N_w=\frac{\operatorname{vol}(B_R)}{\operatorname{covol}\Lambda},
\qquad
\mathbb E E_w=
M\frac{\operatorname{vol}(B_R\cap(B_R-v))}
       {\operatorname{covol}\Lambda}.
\]

Rotational symmetry makes the second overlap independent of the chosen
unit vector v. Some nonempty window therefore has E_w/N_w >= M Theta_m(R),
where Theta is the normalized intersection volume. For unordered pairs,
divide by two. This constant does not alter an exponent.

For a=1/(2R), R>1/2, slicing the two caps gives

\[
\Theta_m(R)=
\frac{2\,\operatorname{vol}(B_{m-1}(1))}
     {\operatorname{vol}(B_m(1))}
\int_a^1(1-s^2)^{(m-1)/2}\,ds.
\]

The volume prefactor has logarithm o(m). Bound the integral above by its
maximum integrand times the interval length, and below by the integral
over [a,a+epsilon]. Taking logarithms, dividing by m, and then letting
epsilon decrease to zero yields

\[
\lim_{m\to\infty}\frac{\log\Theta_m(R)}m
=\frac12\log\left(1-\frac1{4R^2}\right).
\]

Thus the surviving-pair rate has a definite infinite-dimensional limit.
It is a count-relevant limit, not a fitted spiral pitch.

The switch to normalized Euclidean norm is compatible with the minimum-length
argument: if a_v are the conjugate coordinate magnitudes, then
sqrt(mean(a_v^2)) >= (product(a_v))^(1/d). For the selected norm-one
elements every a_v equals one. This preserves both the arithmetic
minimum-length lower bound and the selected vectors' unit lengths.

If the denominator is temporarily relaxed to log(2AR), the new
radius-dependent residual is

\[
\frac12\log(1-1/(4R^2))-\eta\log(2R),
\]

whose maximum is at

\[
R=\frac12\sqrt{1+1/\eta}.
\]

This is an exact radius-selection rule for that specified residual. It
does not determine the optimal unit-distance exponent. Subexponential overlap
factors must be retained, or absorbed with exponent slack, when converting
the limit into a theorem.

The next substantive work is to audit and combine a complete set of modified
lemmas, especially the class-number, covolume, and field-tower steps. A smaller
or more attractive numerical expression alone is not a verified improvement.
