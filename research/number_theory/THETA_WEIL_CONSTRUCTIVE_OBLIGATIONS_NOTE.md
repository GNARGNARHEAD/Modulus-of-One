# Theta Prefixes And Weil Cross-Term Obligations

> Status: active external analytic calibration over graph-audited scalar
> sources.
>
> Implemented by `moo/theta_weil_probe.py`. This does not change Modulus of One runtime
> semantics and does not supply evidence for the Riemann hypothesis.

## Verdict

The quadratic-form direction now reaches a useful second construction layer:

```text
exact representation fibres
  -> exact formal theta prefixes
  -> class-character channels with their constant terms intact
  -> externally weighted finite theta values with analytic tail envelopes
  -> finite zero-side Weil matrices that retain the dual-point cross pairing
```

The strongest result is not positivity. It is a controlled demonstration of
which information a positivity calculation can erase.

For the Weil involution

```text
iota(rho) = 1-conj(rho),
```

critical-line points are fixed. Replacing `iota(rho)` by `rho` everywhere
therefore turns the target form into a same-point Gram matrix. That replacement
is harmless if the desired conclusion is already assumed and destructive if
an off-line pair exists. The probe includes an off-line quartet for which the
full matrix is indefinite while the same-point Gram surrogate and the
diagonal-only surrogate both pass.

That is the dimensional-collapse insight in an exact analytic setting:

```text
full object:       rho paired with 1-conj(rho)
collapsed object:  rho paired with itself
lost information:  displacement away from Re(s)=1/2
```

The probe is a research instrument for preserving that distinction. It is not
an RH test on the actual zeta function because it does not yet evaluate the
arithmetic explicit-formula side or the complete zero sum.

## Exact Formal Theta Prefixes

For a positive-definite form `Q`, let `r_Q(n)` count all signed, ordered
integer pairs with `Q(x,y)=n`. The raw finite prefix is

```text
K_Q,N(q) = 1 + sum_(1<=n<=N) r_Q(n)*q^n.
```

This is a formal polynomial. No exponential or floating-point value is needed
to define it.

If `w_Q` is the configured proper-automorphism normalization, the
unit-normalized class prefix is

```text
Ktilde_Q,N(q) = 1/w_Q + sum_(1<=n<=N) (r_Q(n)/w_Q)*q^n.
```

The constant must be divided too. Attaching constant `1` to an already
normalized positive-index ledger would mix two normalizations. The exact
constants carried by the report are:

| form class | `w_Q` | raw constant | unit-normalized constant |
|---|---:|---:|---:|
| `x^2+y^2`, `D=-4` | 4 | 1 | 1/4 |
| `x^2+5y^2`, `D=-20` | 2 | 1 | 1/2 |
| `2x^2+2xy+3y^2`, `D=-20` | 2 | 1 | 1/2 |

For the two `D=-20` classes, the character prefixes are

```text
K_plus  = Ktilde_A + Ktilde_B
K_minus = Ktilde_A - Ktilde_B.
```

Their constants are exactly `1` and `0`. Every positive-index character row
retains its two class components, so cancellation is inspectable rather than
replaced by a scalar total.

The report calls these exact external representation coefficients over
graph-audited scalar sources. It does not call them graph-derived. The strict
corpus has nodes and arithmetic construction edges for scalar values; it has
no form-evaluation, theta-weight, Mellin-transform, or Weil-functional edge.

## External Theta Specialization And Tail Bound

The analytic layer specializes

```text
q = exp(-pi*t),  t>0.
```

For the configured forms, the elementary inequality `2|xy|<=x^2+y^2`
supplies

```text
Q(x,y) >= mu*(x^2+y^2),  mu=1.
```

More generally, for `Q=ax^2+bxy+cy^2`, the implemented bound is

```text
mu = min(2a-|b|, 2c-|b|)/2,
```

when this number is positive.

Let

```text
T_Q,N(t) = sum_(Q(x,y)>N) exp(-pi*t*Q(x,y)).
```

For any `0<eta<1`, split the exponential, use `Q>N` in the first factor and
the radial lower bound in the second:

```text
T_Q,N(t)
 <= exp(-pi*t*(1-eta)*N)
    * sum_(x,y in Z) exp(-pi*eta*t*mu*(x^2+y^2))
 <= exp(-pi*t*(1-eta)*N)
    * (1 + 1/sqrt(eta*t*mu))^2.
```

The last step bounds each decreasing integer Gaussian sum by `1` plus its
real-line integral. This is an analytic upper-bound formula over exact reals.
The reported numerical value is still ordinary binary64, not a directed-
rounding interval.

## Calibrated `D=-4` Transform

For `G(x,y)=x^2+y^2`, Poisson/Jacobi transformation gives

```text
Theta_G(t) = t^(-1)*Theta_G(1/t).
```

This is a classical theorem, not something inferred from the plot or finite
samples. The probe evaluates both finite prefixes and combines the two
analytic truncation envelopes. The relevant one-dimensional Jacobi parameter
inversion is recorded in [DLMF 20.7(viii)](https://dlmf.nist.gov/20.7); the
two-dimensional identity is its product for the square lattice.

There are two distinct numerical questions:

```text
analytic truncation:  what was omitted beyond N?
binary64 roundoff:    what was changed while evaluating retained terms?
```

At `N=200` and `t=0.25,0.5,1,2,4`, three of five residuals are below the
displayed analytic tail estimate alone. The `t=0.5` and `t=2` residuals are
about one binary64 ulp while the analytic tails are far smaller. All five pass
after adding the explicitly labelled roundoff guard. That guard is a
conservative diagnostic formula, not an interval certificate.

Thus the earned statement is only:

```text
the finite values are consistent with the known transform at the reported
binary64 scale after separating truncation from a non-rigorous roundoff guard.
```

## Class Cross Terms Cannot Be Deleted

The inverse `C2` transform is

```text
a_A = (a_plus+a_minus)/2
a_B = (a_plus-a_minus)/2.
```

Squaring either expression requires a cross term. Two exact repository
fixtures make the loss visible.

At `n=2`:

```text
(a_plus,a_minus) = (1,-1)
a_A^2 = (1+1-2)/4 = 0.
```

A diagonal-only calculation gives `1/2`.

At `n=6`:

```text
(a_plus,a_minus) = (2,2)
a_B^2 = (4+4-8)/4 = 0.
```

A diagonal-only calculation gives `2`.

The probe also carries a basis-covariance control. With

```text
U = 2^(-1/2)*[[1,1],[1,-1]]
H_character = diag(1,4),
```

the class-basis matrix must be

```text
H_class = U^T*H_character*U = 1/2*[[5,-3],[-3,5]].
```

It has the same eigenvalues `1,4`. Deleting the off-diagonal entries changes
both character-direction values to `5/2`. This control is exact and does not
depend on an eigensolver.

The exponentially weighted coefficient kernels elsewhere in the report are
also labelled as placebos: they are Gram matrices by construction. Their
positive semidefiniteness checks coefficient assembly, but says nothing about
Weil positivity or zero locations.

## The Weil Involution

Let `G(s)` be the Mellin transform of an admissible test function satisfying

```text
G(0)=G(1)=0.
```

In the positive zero-side convention, the relevant correlation is

```text
Q(G) = sum_rho G(rho)*conj(G(1-conj(rho))).
```

The endpoint constraints remove the two pole terms in the corresponding
explicit formula. Bombieri's Clay exposition states the explicit formula and
Weil positivity criterion in this form; see
[The Riemann Hypothesis](https://www.claymath.org/library/monographs/MPPc.pdf),
sections 2-3 of the RH chapter.

Put

```text
iota(rho)=1-conj(rho).
```

If `Re(rho)=1/2`, then `iota(rho)=rho`, and the summand is `|G(rho)|^2`.
Off the line, `rho` and `iota(rho)` are different points. That difference is
exactly what the matrix must retain.

For a real coefficient basis `G_0,...,G_(d-1)`, the implemented matrix is

```text
H_ij = sum_rho conj(G_i(rho))*G_j(iota(rho)).
```

The finite point multiset must be closed under conjugation and the Weil
involution. The probe rejects incomplete orbits rather than manufacturing
Hermiticity by silently averaging unrelated points.

## Current Test Basis

The calibration basis is

```text
G_k(s) = s*(1-s)
         *((s-1/2)/sqrt(alpha))^k
         *exp((s-1/2)^2/(4*alpha)).
```

The factor `s*(1-s)` enforces `G_k(0)=G_k(1)=0`. In logarithmic coordinates,
the inverse Mellin functions are Gaussian-polynomial functions multiplied by
the standard half-density. They decay rapidly at both multiplicative ends.

This basis was chosen to test assembly and sensitivity, not because the
project has proved that its degree exhaustion is dense in the theorem's test
space. The report therefore calls every resulting matrix a finite zero-side
calibration.

## Adversarial Weil Controls

The default critical-line control uses the synthetic points

```text
1/2 +/- 3i,  1/2 +/- 5i.
```

Its matrix is a Gram matrix because every point is fixed by `iota`. Positive
semidefiniteness here is structurally forced and is not RH evidence.

The default off-line control uses the complete synthetic quartet

```text
0.7 +/- 3i,  0.3 +/- 3i.
```

At basis dimension `6` and `alpha=16`, the full matrix has two clear negative
eigenvalues in binary64:

```text
-2.5762970828, -1.5351906746.
```

The same-point matrix

```text
P_ij = sum_rho conj(G_i(rho))*G_j(rho)
```

passes the configured PSD tolerance, as it must: it is a Gram matrix for any
point set. Every diagonal entry of the full matrix is also nonnegative. Thus
both tempting shortcuts miss the injected off-line displacement.

An exact algebraic fixture removes dependence on this chosen basis. Assign
evaluation vector `(1,0)` to the two right-half points and `(0,1)` to their
left-half partners. Then

```text
true involutive matrix = 2*[[0,1],[1,0]]  eigenvalues -2,2
same-point surrogate   = 2*[[1,0],[0,1]]  eigenvalues  2,2.
```

This is an assembly fixture, not a claim that the synthetic points are zeta
zeros. An implementation that cannot distinguish these two matrices has
collapsed the very dimension the criterion is meant to inspect.

## What The Strict Graph Contributes

Run:

```sh
python3 -m moo.theta_weil_probe \
  --db out/experiments/pascal_edge_probe_u300.sqlite \
  --max-n 200 \
  --pretty
```

The `U300`, `N=200` run finds all `200` positive scalar source nodes and the
named `D=-20` scalar composition shadows. For each theta coefficient, the
report retains the exact representation witnesses and the scalar node audit.

The graph contribution stops there:

```text
graph-native:
  scalar node, status, arithmetic construction edges, graph neighborhood

external exact annotation:
  quadratic form, lattice witness, form class, formal theta coefficient

external analytic evaluation:
  exponential weight, theta tail, Mellin transform, zero-side Weil matrix
```

This separation is not a disclaimer pasted onto the end. It is part of the
data model: every formal coefficient says that it is not graph-derived, and
the report states that no theta or Weil edge type exists.

## Missing Proof Obligations

The constructive gap is now narrower and more explicit.

### 1. Arithmetic explicit-formula matrix

The next Weil matrix must be defined independently from the arithmetic side:

```text
pole contribution
prime-power contribution, including multiplicity log(p)
gamma constant
archimedean integral
```

Only after an entrywise identity has been checked should it be compared with a
zero-side matrix. A matrix assembled solely from supplied critical-line points
is PSD by construction and cannot discover an omitted off-line zero.

### 2. Complete sum or rigorous replacement

A finite zero list is not the full Weil sum. A future result needs certified
zero data plus a rigorous zero-tail bound, or must work entirely through the
arithmetic explicit formula.

### 3. Fixed test space and topology

One safe future choice is the constrained multiplicative test space

```text
g in C_c^infinity(0,infinity),  G(0)=G(1)=0,
```

with the usual transported test-function topology: common compact support and
uniform convergence of every derivative. A nested family must be proved dense
in that topology while preserving the two moment constraints. Plain `L2`
density is not automatically enough.

The current log-Gaussian polynomial family has no such density proof in the
report.

### 4. All dimensions, not one matrix

Positive semidefiniteness at one dimension, scale, or finite sample establishes
only positivity on that displayed span. An RH implication requires positivity
for every test in a theorem-sufficient dense class, plus continuity of the
functional used in the limiting passage.

### 5. Certified error ledger

Binary64 eigenvalues and heuristic roundoff guards are diagnostics. A negative
direction for the actual arithmetic matrix would require an enclosure. If
`H_tilde=H+E` and `||E||<=eta`, a negative eigenvalue is certified only when

```text
lambda_min(H_tilde) + eta < 0.
```

The witness vector, every entry interval, prime-power truncation, archimedean
quadrature error, Hermitian residual, and operator-norm error must remain in
the report. Small negative eigenvalues must never be clipped.

### 6. Graph-native selection rule

The present choices of `t`, basis degree, and scale are external. A genuinely
Modulus of One-specific contribution would need a rule selecting test functions from
construction neighborhoods or branch structure, followed by controls showing
that the selection predicts something not already forced by the external
analytic basis.

## Claim Boundary

Allowed:

```text
The theta coefficient prefixes through N are exact formal polynomials over
complete bounded representation fibres.

The D=-4 transform samples agree at the stated non-rigorous binary64 scale
after truncation and roundoff are reported separately.

The full finite involutive matrix detects the synthetic off-line quartet,
while same-point and diagonal-only placebos erase it.

The finite controls identify information that a dimensional collapse loses.
```

Disallowed:

```text
The strict graph computes theta functions, Mellin transforms, or zeta zeros.

Positive coefficient kernels establish Weil positivity.

PSD on supplied critical-line points is evidence for RH.

The synthetic quartet says anything about the actual zeros of zeta.

The current finite family supplies a constructive proof of RH.
```

The present result is therefore a sharper framework, not a theorem about the
zeta zeros: it makes the hidden involution, the cross terms, the finite/infinite
boundary, and the information lost by the wrong projection explicit enough to
test.
