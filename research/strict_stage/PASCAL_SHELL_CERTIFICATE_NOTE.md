# Pascal, shell powers, and construction identity

Date: 2026-09-22.

evidence_layer: external_probe
claim_status: candidate

Exact algebra below is proved separately from the bounded strict-graph
observations. This note distills GNARGNARHEAD's pasted conversation beginning
"What can you tell me about A squared plus B squared equals 1?" It proposes
an analysis-layer certificate schema, with no change to runtime operands,
confirmation, or certainty.

The useful addition is a precise connection between **ordered expansion
choices, their quotients, and witnessed certificate availability**. Pascal's
coefficients alone do not establish special circle structure. In particular,
an associative/commutative expression class can contain certificates with
different completion stages.

## What was already established

The [shell-composition definition](../geometry/SHELL_COMPOSITION_BRANCH_NOTE.md)
already gives rational norm-one composition, its integer witness bundles,
parameter coverage, and the separation from rational phase. Its
[calibration](../geometry/SHELL_COMPOSITION_20260920.analysis.md) distinguishes
source-plus-composition witnesses from a direct output-shell proof.

The [Pascal lens](PASCAL_EDGE_LENS_NOTE.md) already rejects ordinary additive
recurrence as a Pascal-specific signal. The
[route-identity lens](ROUTE_IDENTITY_LENS_NOTE.md) distinguishes directed
events, commutative witnesses, AC expressions, and semantic labels.

The conversation joins these programs; it does not supersede those results.

## 1. Pascal coefficients count fibres of a declared expansion

Let W_n={0,1}^n be the finite set of ordered choices in expanding n copies
of (u+v). Define k(w) as the number of ones in w. The commutative monomial
associated with w is

    m(w) = u^(n-k(w)) v^k(w).

For independent formal symbols u,v, two words give the same monomial exactly
when they have the same k. There are therefore n+1 monomial classes and

    |{w : k(w)=k}| = C(n,k).

Proof: choosing such a word is choosing its k one-positions among n positions.
Equivalently, these are permutation orbits with binomial orbit sizes.

This is the precise meaning available for "Pascal is route multiplicity":
it counts **formal expansion choices before the commutative quotient**.
After that quotient there is one monomial template for each k, carrying the
coefficient C(n,k). Numerical substitution can cause further identifications.
It does not follow that Modulus of One stores C(n,k) distinct edges or independent
construction certificates. Repeated use of a value can reuse the same witness.

This combinatorics applies to every binary polynomial power, including ones
with no norm constraint. A shell-specific claim cannot use it as its signal.

## 2. Two evaluations of the same choice set

Let A,B be rational and A^2+B^2=1. Complex notation here abbreviates the
external rational-pair algebra; i is not a new runtime operand.

### Signed composition

Evaluate the word w as

    alpha(w) = A^(n-k(w)) (i B)^k(w).

Then sum_w alpha(w)=(A+iB)^n=P_n+i Q_n, where

    P_n = sum_j (-1)^j C(n,2j) A^(n-2j) B^(2j),
    Q_n = sum_j (-1)^j C(n,2j+1) A^(n-2j-1) B^(2j+1).

Each sum runs only over indices whose exponents are nonnegative. The four
residues of k modulo 4 determine the coordinate and sign. An equivalent
recursive construction is

    (P_0,Q_0) = (1,0),
    (P_(n+1),Q_(n+1)) = (A P_n-B Q_n, B P_n+A Q_n).

Expanding the two squares gives

    P_(n+1)^2+Q_(n+1)^2
      = (A^2+B^2)(P_n^2+Q_n^2).

Induction proves P_n^2+Q_n^2=1. This is an exact classical identity, valid
without angles or completed real coordinates.

The power map preserves the rational shell but need not map onto it. For
example, a rational square root of (0,1) would require A^2=B^2=1/2, which
is impossible over the rationals. The conversation's "onto itself" language
is valid for positive powers on the real circle, not generally its rational
subset.

### Positive weights

Instead evaluate each word by its squared modulus:

    mu_n(w) = |alpha(w)|^2 = A^(2(n-k(w))) B^(2k(w)).

These weights are nonnegative and sum to 1. Grouping by k gives

    p_(n,k) = C(n,k) A^(2(n-k)) B^(2k),
    sum_k p_(n,k) = 1.

They also satisfy the finite refinement identity

    mu_(n+1)(w0)+mu_(n+1)(w1) = mu_n(w).

Thus the conversation yields a compatible family of finite rational
partitions of 1, or probability distributions on the declared word sets.
Interpreting these as probabilities of Modulus of One graph histories requires an
additional sampling model; no such frequencies have been measured here.

The distinction matters: squaring after summing signed terms is different
from summing their squares. At A=4/5, B=3/5, n=2,

    squared second coordinate of (A+iB)^2 = 576/625,
    binomial weight p_(2,1)                = 288/625.

Both full constructions have total norm/mass 1, but their intermediate
quantities differ. In particular, the coefficient 2 in the imaginary
coordinate is squared to 4; it is not a count of four stored graph routes.

Any nonnegative rational X,Y with X+Y=1 supports the same partition grammar.
It need not lift to rational A,B with X=A^2,Y=B^2: X=Y=1/2 is a counterexample.
This supplies a direct generic-partition control.

## 3. What the squared-coordinate projection forgets

Define q(A,B)=B^2; the other square is then 1-q. This forgets coordinate
signs. General shell composition does not descend through q. Indeed, put

    z=(4/5,3/5),    z_inverse=(4/5,-3/5).

Both have q=9/25, but

    q(z*z)         = 576/625,
    q(z*z_inverse) = 0.

Identical projected inputs thus permit different projected products.

Self-powering is a narrower exception. Two unit-shell pairs with the same q
differ by overall sign and/or conjugation. Powers preserve these equivalences,
so q(z^n) does depend only on q(z). For n=2 the induced polynomial is

    q(z^2) = 4 q(z)(1-q(z)).

This is not the binomial middle weight 2q(1-q). It is also not a binary group
law on squared coordinates. These distinctions prevent conflating shell
composition, finite probability weights, and the information retained by q.

The rational-phase versus rational-coordinate distinction supplies no new
result here: the shell-composition note already proves that their common
finite-order positions are precisely the four axes, and that every group
homomorphism Q/Z -> G_Q is trivial.

## 4. Proposed Modulus of One object: a witnessed shell-power certificate

Fix a corpus F, checkpoint U, positive integer source triple (a,b,r), exponent
n>=1, and an explicit finite operation schema sigma. Record

    K = (F,U,a,b,r,n,sigma,leaf_cut,role_map,dependencies).

The role_map associates every requested arithmetic operation with its exact
retained node and directed edge references, stage, and confirmation status.
Repeated roles may share one event. Definitions use only finite witnesses;
they do not require a completed circle.

Require the source-shell bundle

    a*a -> a2,  b*b -> b2,  r*r -> r2,  a2+b2 -> r2.

Possible schemas then compare:

- iterated ordered pair composition and its direct output-shell proof;
- a factored power (a2+b2)^n;
- an expanded numerator sum_k C(n,k) a^(2(n-k)) b^(2k);
- the radius power r^(2n), with the shared-result comparison explicit.

All exponents and coefficients must be lowered to declared operations or
named confirmed leaves. They are not extra primitive operations. Distinct AC
expressions remain declared binomial/norm-dependent rewrites, not independent
evidence for the shell. Ordinary closure of a formula is not retained closure
of these witness bundles.

Clearing denominators is necessary for this current field. The literal
fractions A=a/r and B=b/r can exist as outputs but cannot be operands under
the positive-spine rule. Integer numerator certificates can instead be checked,
with normalization stated separately as an external observation or as explicit
final division witnesses. These are different routes, not interchangeable
descriptions of a witnessed rational computation.

Returning a numerator D=r^(2n) to 1 by D/D requires stage D for that final
edge. It does not change the certainty of the source or of the certificate.
The primitive value 1 has not acquired increasing intrinsic complexity:
only the selected certificate schemas have grown.
Different upstream certificates then share the same terminal D/D witness;
their distinctions must be inspected before that last quotient.

## 5. Completion stage is not an AC invariant

For a declared certificate C, let tau_F(C) be the earliest checkpoint at which
all required directed requests are retained with eligible operands. Missing
requests give no finite observed completion. This measures availability of a
finite witness bundle, not execution time or an automatically causal path.

In a complete wide positive-spine field, conditional on retaining every
requested result, an operation with positive integer inputs x,y first occurs
at max(x,y). Consequently the predicted certificate threshold is the maximum
operand across all its requests, including premises. A produced output needs
confirmation only when it subsequently appears as an operand.

Take a=4,b=3,r=5, so X=a^2=16 and Y=b^2=9. All four certificates below target
625, with the source-shell premises included:

| Certificate | Intermediate additions or products | Observed completion |
| --- | --- | ---: |
| Factored | 16+9=25; 25*25=625 | U25 |
| Expanded, left-associated | 256+144=400; 400+144=544; 544+81=625 | U544 |
| Expanded, paired | 256+81=337; 144+144=288; 337+288=625 | U337 |
| Composed-shell norm | 16-9=7; 12+12=24; 49+576=625 | U576 |

The two expanded certificates have the same AC expression at the cut {4,3}:

    a*a*a*a + a*a*b*b + a*a*b*b + b*b*b*b.

They have different intermediate witnesses and different completion stages.
Therefore tau_F does not descend to a single value on AC classes. This is a
counterexample with exact retained witnesses, not a conjecture. U337 is the
threshold for the named paired certificate; no optimality claim is made.

An AC quotient is still useful for expression identity. For timing questions,
retain its members' witnesses and stages. For a declared finite comparison
family S, one possible summary is

    T_(F,S)([C]_AC) = {tau_F(C') : C' in S and C' ~_AC C},

with incomplete members recorded separately. Here the expanded class has
observed stage set {337,544}. Replacing both certificates with a bare canonical
expression would erase precisely this distinction.

The generic control X=7,Y=2 targets 81 and has thresholds U9 (factored),
U77 (left-associated), and U53 (paired). Its two expansions also agree under
AC. The phenomenon therefore does not need the shell relation. Every measured
wide-field threshold agrees with ordinary operand readiness; no residual
timing law or privileged Pascal organization is supported.

## Evidence, verification, and scope

The [fixed design](route_identity/PASCAL_SHELL_20260922.pre.md) was saved before
these new lookups. The
[report](route_identity/results/2026-09-22-pascal-shell-calibration-v1.json)
contains both input hashes, source hashes, exact requests, nodes, directed
edge references, AC comparisons, boundary blockers, and prediction checks.

Both inputs are the existing current-generator shell-calibration fields,
opened read-only with hashes unchanged. All seven wide-field predictions
match. None of the seven certificates is complete in the narrow U80 retention
control. Raw SQL readback independently verifies 30 distinct directed records
in the wide field and 2 in the narrow field. Thirty-six exact rational
parameter/exponent checks verify the algebra against repeated pair
multiplication and positive partitions; the general proofs above carry the
unbounded statements.

The literal rational square is blocked by `operand_not_positive_spine`.
625/625 -> 1 is beyond the U576 field: U625 remains a prediction, not an
observed return witness. The U576 composed-shell case was already known and
is not an independent holdout. No large corpus was created or modified.

Reproduce to a fresh output path:

```sh
python3 -B research/strict_stage/route_identity/pascal_shell_calibration.py \
  --write out/scratch/pascal-shell-calibration-rerun.json
```

If the disposable inputs are absent, the script stops. Their reconstruction
settings and identity limits are in the earlier shell-composition manifest;
the saved report still preserves the selected records.

The retained formalization is a **finite certificate system connecting binary
choice, norm-preserving composition, and quotients of construction identity**.
It supports keeping AC identity and stage-sensitive provenance together.
It does not yet justify a new foundational rule, a distinguished Pascal
branch, or a native probability interpretation.
