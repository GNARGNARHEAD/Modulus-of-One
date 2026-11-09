# Quadratic Forms And Class-Character Channels

> Status: maintained exact external quadratic-form infrastructure with a
> completed and frozen U850 v1 class/genus ablation.
>
> Implemented by `moo/quadratic_form_probe.py` and the nested class/genus
> suite. The U850 v1 design, report, and provenance sidecars remain frozen;
> that versioned result does not freeze the reusable quadratic-form tools or
> broader research program. The later theta/Weil layer remains an active
> external analytic calibration with explicit missing proof obligations and is
> also summarized in
> [AUGUST_2026_EXTERNAL_PROBE_DISPOSITIONS.md](../../archive/completed_external_calibrations/AUGUST_2026_EXTERNAL_PROBE_DISPOSITIONS.md).
> None of these layers changes Modulus of One runtime semantics.

## Verdict

Quadratic forms give the current project a useful answer to the dimensional-
collapse question, but not a proof of the Riemann hypothesis.

The scalar projection

```text
(form class, x, y, construction law) -> represented integer n
```

forgets which form represented `n`, which integer pair witnessed it, and how
representations compose. That lost information is not decorative. At
discriminant `-20`, the principal-form coefficient sequence is not
multiplicative, while the two exact class-character channels are. The
character transform recovers a multiplicative distinction that the isolated
scalar rendering obscures.

This is the earned result:

```text
representation fibres -> form classes -> exact composition -> character channels
```

When this structure is scrutinized through the integer modulus-one quotient,
the conclusion is deliberately harsher: every represented value becomes zero.
Only a decorated preimage can remember the Gauss class transition. The bare
quotient cannot.

The analytic continuation and zero sets of the associated theta or Epstein
series remain outside the implemented probes. A companion probe now adds exact
formal theta prefixes, a calibrated classical `D=-4` transform with tail
envelopes, and synthetic zero-side Weil cross-term controls; it does not
evaluate an Epstein zero set or the arithmetic zeta explicit formula.

## What The Scalar Rendering Loses

Let

```text
Q(x,y) = a*x^2 + b*x*y + c*y^2.
```

A report containing only `n=Q(x,y)` has collapsed at least four distinctions:

| retained in the richer object | absent from the scalar `n` |
|---|---|
| the coefficients `(a,b,c)` | which quadratic form was used |
| the pair `(x,y)` | which representation witnessed `n` |
| the proper-equivalence class of `Q` | which class channel the witness occupies |
| the bilinear composition map | how two witnesses multiply before projection |

This is a concrete version of the line/triangle problem. A projected point can
be exact and still be informationally incomplete. The right question is not
whether the point is false, but which antecedent distinctions the projection
cannot recover.

Modulus of One's scalar graph retains a different rich object: construction edges for the
value. Those edges are important, but they are not silently equivalent to
quadratic-form witnesses or form-class composition.

## Exact Enumeration, Including Holes

For a positive-definite integral form, put

```text
D = b^2 - 4*a*c < 0
Delta = 4*a*c - b^2 > 0.
```

The exact identity

```text
4*a*Q(x,y) = (2*a*x + b*y)^2 + Delta*y^2
```

gives a complete finite search. If `0 < Q(x,y) <= N`, then

```text
|y| <= floor(sqrt(4*a*N/Delta))
|2*a*x+b*y| <= floor(sqrt(4*a*N-Delta*y^2)).
```

The probe uses these integer bounds and then checks `Q(x,y)` exactly. It does
not accept a caller-selected coordinate box. Therefore an empty witness list
through `N` is an observed hole in the complete bounded fibre, not a crop of an
unknown search region.

The implementation uses the modern discriminant convention `Delta=b^2-4ac`.
Gauss does not. In the *Disquisitiones* he writes

```text
(a,b,c)_G = a*x^2 + 2*b*x*y + c*y^2
d_G = b^2-a*c.
```

Thus a modern middle coefficient `B=2b` gives `Delta=4*d_G`. The two-form
experiment below is Gauss determinant `d_G=-5`, equivalently modern
discriminant `Delta=-20`. This translation is part of every machine-readable
form record; silently calling both numbers “the discriminant” would corrupt the
historical comparison.

The historical route is Articles 153–159 for notation, representation,
transformation, proper equivalence, and opposite forms; Articles 171–176 for
negative-determinant reduction and reduced-class enumeration; Articles
223–231 for classes, primitive conventions, and the principal class; Articles
234–244 for composition; and Article 249 for composition of classes. The
[1801 first edition](https://www.e-rara.ch/zut/content/structure/1254642) is the
primary witness. The searchable
[1807 French Section V](https://fr.wikisource.org/wiki/Recherches_arithm%C3%A9tiques/Section_cinqui%C3%A8me)
and [Article 249](https://fr.wikisource.org/wiki/Page%3AGauss_-_Recherches_arithm%C3%A9tiques%2C_traduction_Poullet-Delisle%2C_1807.djvu/295)
make the article map inspectable, while Timorin's
[Disquisitiones 235](https://arxiv.org/abs/1309.4879) gives a careful modern
reconstruction of the composition formalism and prints the `B*B -> A` example.

## The `D=-4` Control: Circle As The Operator `i`

The form

```text
G(x,y) = x^2+y^2
```

supports a precise pair-level version of the earlier circle-as-`i` idea. Define

```text
J(x,y) = (-y,x).
```

Then

```text
J^2(x,y) = (-x,-y)
J^4(x,y) = (x,y)
G(J(x,y)) = G(x,y).
```

Thus `i` can be read exactly as the quarter-turn operator `J` on ordered real
pairs. It need not first be installed as a mysterious scalar. The pair product

```text
(x,y)*(u,v) = (x*u-y*v, x*v+y*u)
```

has the exact norm identity

```text
G((x,y)*(u,v)) = G(x,y)*G(u,v),
```

because

```text
(xu-yv)^2+(xv+yu)^2 = (x^2+y^2)(u^2+v^2).
```

The unit shell `G=1` contains the four integer pairs `(1,0)`, `(0,1)`,
`(-1,0)`, and `(0,-1)`, and `J` cycles them. This is an exact external pair
algebra. The current rational runtime still does not contain Gaussian integers
or complex multiplication as native objects.

As a coefficient control, let `r_G(n)` count signed, ordered integer-pair
representations and set `g(n)=r_G(n)/4` for positive `n`. The probe finds no
coprime multiplicativity defect through its configured bound. Independently of
that finite check, Jacobi's divisor formula proves the global identity

```text
r_G(n) = 4*(number of divisors congruent to 1 mod 4
            - number of divisors congruent to 3 mod 4).
```

The counting convention and theorem are recorded in
[DLMF 27.13(iv)](https://dlmf.nist.gov/27.13).

## Gauss `d_G=-5` / Modern `Delta=-20`: Two Forms, One Scalar Product

Standard reduced-form enumeration at discriminant `-20` gives exactly

```text
A = (1,0,5)_G = [1,0,5]: A(x,y) = x^2+5*y^2
B = (2,1,3)_G = [2,2,3]: B(x,y) = 2*x^2+2*x*y+3*y^2
```

Here square brackets use modern coefficients and the subscript `G` marks
Gauss's half-middle convention. `A` is principal and `B` nonprincipal. Gauss's
Article 176 table makes `d_G=-5` the first clean case in his convention with
two positive properly primitive classes in the same order. This is a
convention-sensitive minimality claim: the smallest modern negative
discriminant with a nontrivial primitive class group is `-15`, not `-20`.

The enumeration is finite: modern reduction gives `3a^2 <= 20`, so `a` is `1` or
`2`; integrality, primitivity, and the standard boundary sign convention then
leave precisely those two forms. Calling them the two proper classes uses the
classical reduction theorem. With that theorem, the class group is `C2`.

The smallest decisive fibres are:

| `n` | witnesses for `A` | `r_A(n)` | witnesses for `B` | `r_B(n)` |
|---:|---|---:|---|---:|
| 1 | `(-1,0),(1,0)` | 2 | none | 0 |
| 2 | none | 0 | `(-1,0),(1,0)` | 2 |
| 3 | none | 0 | `(-1,1),(0,-1),(0,1),(1,-1)` | 4 |
| 6 | `(-1,-1),(-1,1),(1,-1),(1,1)` | 4 | none | 0 |

So the scalar identity `2*3=6` has a richer antecedent:

```text
B(1,0)=2
B(0,1)=3
A(1,1)=6.
```

The graph can retain an edge `2 * 3 -> 6`. That edge does not retain the
transition from the nonprincipal label to the principal label.

## Exact Composition Before Projection

The form labels are supported by bilinear identities, not assigned after
looking at the coefficient table.

For `A*A -> A`:

```text
A(x,y)A(u,v) = A(xu-5yv, xv+yu).
```

For `A*B -> B`:

```text
U = xu-yu-3yv
V = xv+2yu+yv
A(x,y)B(u,v) = B(U,V).
```

For `B*B -> A`:

```text
X = 2xu+xv+yu-2yv
Y = xv+yu+yv
B(x,y)B(u,v) = A(X,Y).
```

These follow directly by putting `r^2=-5` and writing

```text
A(x,y) = Norm(x+y*r)
B(x,y) = Norm(2*x+(1+r)*y)/2,
```

then multiplying the ring expressions and collecting the real and `r`
coefficients. The probe carries the coordinate maps, named samples, and
regression checks. The identities themselves are ordinary polynomial
identities; their validity does not depend on a finite scan.

## Scrutinizing The Forms Through Modulus One

The conservative modulus-one map is not a new form-composition law. It is the
ordinary integer quotient applied *after* evaluation:

```text
decorated witness (form, class, x, y, composition lineage)
    -> represented integer n=Q(x,y)
    -> rho_1(n)=0 in Z/1Z.
```

At `N=200`, the `d_G=-5` family has the exact finite collapse

```text
552 signed integer-pair witnesses
-> 276 proper-automorphism orbits
-> 113 represented integers
-> 1 residue.
```

The principal form contributes 280 raw witnesses, 140 proper orbits, and 57
represented integers. The nonprincipal form contributes 272 raw witnesses,
136 proper orbits, and 56 represented integers. Their represented-value sets
are disjoint through 200. None of those counts creates a second residue.

The smallest class transition makes the erasure visible:

```text
B(1,0)=2
B(0,1)=3
B*B -> A
A(1,1)=6
2*3=6

under rho_1: 0*0=0.
```

The bare quotient has one node. With operation labels retained it has the
forced self-loops `0+0=0`, `0-0=0`, and `0*0=0`; after operation labels are
erased it has one self-loop. It is identical to a constant-bucket control that
replaces every integer by one arbitrary token. The `C2` transition survives
only if form labels and the bilinear coordinate witness are deliberately kept
as decorations in the sole residue fibre.

Those are the total ring operations. Division is excluded: the only putative
denominator in `Z/1Z` is zero, so `0/0` is undefined and division does not
descend as a total quotient operation.

That gives both the candidate and its falsifier:

```text
candidate: Gauss composition is a nontrivial provenance channel inside the
           singleton fibre.

falsifier: strip form labels and bilinear witnesses; no class distinction may
           remain in either the scalar graph or the bare quotient.
```

An optional coefficientwise audit also sends `(a,b,c)`, `(x,y)`, `d_G`,
`Delta`, and `Q(x,y)` to zero. That is only an illustration of integer erasure;
the probe does not call it a developed theory of quadratic forms over the zero
ring.

Finally, the sign character's label `-1 <-> 1/2 in Q/Z` is a different map.
It is a rational phase representation of a character value, not reduction of
the represented integer modulo one. Conflating those constructions would
manufacture a two-phase result that `Z/1Z` does not possess.

## The Class-Character Transform

There are two proper units for `D=-20`, so for positive indices define

```text
a_A(n) = r_A(n)/2
a_B(n) = r_B(n)/2.
```

The `C2` character table is

| character | principal | nonprincipal |
|---|---:|---:|
| trivial | `+1` | `+1` |
| sign | `+1` | `-1` |

and the exact transform is

```text
a_plus(n)  = a_A(n)+a_B(n)
a_minus(n) = a_A(n)-a_B(n).
```

At `n=2,3,6`:

| `n` | `a_A` | `a_B` | `a_plus` | `a_minus` |
|---:|---:|---:|---:|---:|
| 2 | 0 | 1 | 1 | -1 |
| 3 | 0 | 2 | 2 | -2 |
| 6 | 2 | 0 | 2 | 2 |

The principal sequence therefore has the exact defect

```text
a_A(2)*a_A(3) = 0 != 2 = a_A(6).
```

Both character channels satisfy the corresponding relation:

```text
a_plus(2)*a_plus(3)   = 2 = a_plus(6)
a_minus(2)*a_minus(3) = 2 = a_minus(6).
```

The exact scan through `N=200` finds:

```text
g = r_(x^2+y^2)/4:       no coprime defect
a_A:                     first reported defect at 2*3=6
a_B:                     fails the unit condition because a_B(1)=0
a_A+a_B:                 no coprime defect
a_A-a_B:                 no coprime defect
a_A+2*a_B placebo:       coprime defects present
```

The placebo matters. Multiplicativity is not restored by an arbitrary mixture;
the class characters use the homomorphisms of the class group. The finite scan
is a regression result, not the proof. Kani defines the character-weighted
theta basis with the proper unit normalization and proves that its positive-
index coefficients are multiplicative; see the definition around equation
(6) and Theorem 12 in
[The Space of Binary Theta Series](https://mast.queensu.ca/~kani/papers/theta.pdf).

The signs also touch the circle-as-one phase model without conflating it with
the graph:

```text
+1 <-> Q/Z phase 0
-1 <-> Q/Z phase 1/2.
```

For larger class groups, character values can be higher roots of unity. The
`C2` Hadamard transform implemented here must not be generalized by pretending
all character tables contain only `+1` and `-1`.

## Theta And Epstein: The Earned Analytic Bridge

For a positive form `Q`, its theta series groups the lattice by representation
fibres:

```text
Theta_Q(t) = sum over (x,y) in Z^2 of exp(-pi*t*Q(x,y))
           = 1 + sum over n>=1 of r_Q(n)*exp(-pi*t*n).
```

Its Epstein Dirichlet series groups the same nonzero lattice by the same
fibres:

```text
E_Q(s) = sum over (x,y)!=(0,0) of Q(x,y)^(-s)
       = sum over n>=1 of r_Q(n)*n^(-s),    initially Re(s)>1.
```

So the implemented representation ledger is an exact finite coefficient
prefix for both objects. It is not yet an evaluation of either infinite
series. The theta/Mellin route to completed zeta functions is classical; see
[DLMF 20.10](https://dlmf.nist.gov/20.10). Any implementation of that route
must add tail bounds, transformation laws, and analytic-domain bookkeeping.

For `D=-20`, the individual form theta series mix the two character channels:

```text
Theta_A = character-channel mixture
Theta_B = character-channel mixture.
```

The `+` and `-` transforms diagonalize the class action and yield the
multiplicative coefficient channels. This is the substantive bridge from the
lost representation label to modern `L`-function structure.

## The Adversarial Result

This direction supplies a warning as strong as its positive result.

A positive-definite quadratic form has positive theta coefficients and an
Epstein zeta function with a Riemann-like functional equation. Those facts do
not force all nontrivial zeros onto the critical line. For class number at
least two, individual Epstein zeta functions mix inequivalent character
channels, and off-critical-line zeros are known; Lamzouri studies zeros with
`1/2 < Re(s) < 1` for precisely this setting in
[Zeros of the Epstein zeta function to the right of the critical line](https://arxiv.org/abs/1907.06387).

Therefore the following inference is invalid:

```text
positive theta kernel + self-dual functional equation -> RH.
```

The `D=-20` control shows why cancellation between hidden channels is a real
structural issue. Any prospective zeta proof must control the relevant channel
and its cross terms, not merely exhibit positivity before dimensional collapse.

## Graph Audit

Run:

```sh
python3 -m moo.quadratic_form_probe \
  --db out/experiments/pascal_edge_probe_u300.sqlite \
  --max-n 200 \
  --graph-stage-cutoff 200 \
  --composition-event-limit 10000 \
  --pretty
```

The report returns:

```text
complete signed, ordered representation fibres through max_n
proper-automorphism orbit partitions
standard reduced-form enumeration for D=-4 and D=-20
exact pair and bilinear composition calibrations
complete bounded orbit-normalized D=-20 composition events
principal/nonprincipal coefficient ledgers
C2 character and noncharacter-placebo channels
finite coprime multiplicativity audits
scalar node coverage for every n through max_n
complete positive-spine scalar shadows for every representation witness
stage-censored scalar-edge shadows for every composition relation
the explicit two-stage projection n -> 0 in Z/1Z
explicit analytic and claim boundaries
```

Every form witness is evaluated without operating on a speculative node. The
diagonal forms use squares, positive coefficient scaling, and positive partial
sums. For `B`, the exact rewrite

```text
B(x,y) = x^2 + (x+y)^2 + 2*y^2
```

does the same. Signed coordinates remain external annotations. The
`|x+y|` rewrite is audited separately with addition or directed subtraction.
When `x=-y`, the edge `|x|-|y| -> 0` is retained as relational-zero evidence,
but zero is never reused as an operand.

The saved `N=200`, `U=200`-prefix calibration yields:

| form | raw witnesses | proper orbits | relation-role occurrences | distinct ordered relations | latest evidence stage |
|---|---:|---:|---:|---:|---:|
| `x^2+y^2` | 632 | 158 | 1,784 | 158 | 196 |
| `A=x^2+5y^2` | 280 | 140 | 1,012 | 80 | 180 |
| `B=2x^2+2xy+3y^2` | 272 | 136 | 1,744 | 258 | 181 |

Across all three forms these are 378 distinct ordered relation IDs. They
collapse to 295 commutative-normalized keys and are backed by 514 unique
directed graph edge IDs. Within the two `d_G=-5` forms the corresponding counts
are 326, 269, and 462.

For `B`, the last column of structure splits into 1,508 arithmetic-DAG step
occurrences over 175 distinct ordered relations and 236 coordinate-rewrite
occurrences over 90 relations. The union has 258 relations because seven
relations play both kinds of role. The coordinate cases are 82 same-sign
additions, 138 positive subtractions, 16 cancellations to zero, and 36
zero-coordinate aliases needing no edge. The cancellation side ledger uses the
eight exact edges `k-k -> 0`, `1 <= k <= 8`; their operands are confirmed, zero
is speculative at the edge, and zero is never reused. All reported relations
are usable at or before the stage cutoff.

The composition ledger contains 961 proper-orbit-normalized events:

```text
A*A -> A    271
A*B -> B    466
B*B -> A    224
```

They use 345 distinct commutative scalar multiplication relations backed by 678
directed graph edge occurrences. Every bilinear output lands in the correct
target orbit fibre and every scalar relation is present with confirmed operands
in the `U=200` prefix. For accounting, the report also
records 7,612 ordered signed-witness events before automorphism and source-order
normalization.

The graph evidence is deliberately separate:

```text
strict graph: scalar nodes and recorded arithmetic edge occurrences
external probe: form, representation fibre, class label, pair algebra, transform
```

In particular, zero and negative representation coordinates may be present as
speculative graph nodes, but the strict positive-spine corpus does not operate
on them. Presence is not operand readiness, and neither is a form-evaluation
edge.

Complete edge coverage is a saturation control, not a discovery. The strict
positive spine supplies every retained in-range operation on confirmed positive
operands, so it would be surprising if these exact scalar shadows were absent.
The selective information remains external: which form, which class, which
coordinate witness, and which bilinear map gave the scalar operation.

## Confirmatory Nested Class/Genus Ablation

The preregistered U850 follow-up extends the two-class calibration to three
families:

```text
Delta=-20: Cl ~= C2, genera {A}, {B}
Delta=-23: Cl ~= C3, one genus {A,P,M}
Delta=-56: Cl ~= C4, genera {A,C}, {P,M}
```

It is a nested control rather than a strict factorial design: every proper
class belongs to one genus. The experiment removes information in stages:

```text
A0  exact decorated form witness and composition
A1  coefficients/coordinates retained as a leakage sentinel
A2  represented integer and a strong scalar-arithmetic baseline
A3  label-free Modulus of One node-neighborhood features
A4  quotient residue, ending at the bare singleton modulo one
```

The final `201..800` holdout gives the decisive comparison:

| target | scalar BA | graph-only BA | scalar + graph BA | graph lift | matched p |
|---|---:|---:|---:|---:|---:|
| `Delta=-56` genus | `1.0000` | `0.5000` | `1.0000` | `0.0000` | `0.4040` |
| `Delta=-56`, `A` versus `C` within one genus | `0.4500` | `0.5000` | `0.4643` | `0.0143` | `0.7809` |

Both Holm-adjusted p-values are `0.8079`; neither graph-conditioned effect is
promoted. The smaller `201..400` checkpoint produced an apparently attractive
`+0.15` within-genus graph lift, but the matched-null median was also `+0.15`
and the effect nearly vanished on the mandatory larger holdout. This is a
control success: it prevents a small-sample fluctuation from being re-described
as class structure.

The scope is deliberately bounded. The genus task is ceiling-limited because
the scalar score is already `1.0`, so it cannot rule out redundant genus
patterns in the graph. The within-genus final holdout contains only 29 exclusive
`A`/`C` samples, and the combined model predicts none of the 15 `A` cases. The
matched shuffle is a frozen coarse sensitivity null, not a theorem of literal
conditional exchangeability. Thus the result is failure to promote this
feature/model signal, not a proof that every possible graph-native encoding is
uninformative.

The quotient panel reproduces the classical hierarchy. For `Delta=-56`, moduli
7, 8, 14, 28, and 56 recover genus perfectly on the frozen coprime sample.
Within-genus class information remains weak and non-predictive. At modulus one,
genus mutual information and conditional class mutual information are exactly
zero in every family. The `m=809` endpoint is injective only on `1..800` and is
descriptive: development and holdout residues are disjoint.

The inverse-form control is exact rather than statistical. Reflection
`(x,y)->(x,-y)` gives `P` and `M` identical represented integers and therefore
identical scalar-node graph features. Through 800 this yields 267 conflicting
value signatures at `Delta=-23` and 205 at `Delta=-56`, with an exact
one-half ceiling for deterministic oriented recovery. Any better scalar-node
result would be leakage.

All externally specified composition identities and bounded target fibres pass
exactly. Their 1,398, 885, and 1,566 distinct scalar multiplication relations
for `Delta=-20`, `-23`, and `-56` are all present in the U850 graph. This is
scalar multiplication saturation, not graph-native composition recovery; no
graph-native composition classifier was performed.

The locked report and interpretation are:

```text
research/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.json
research/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.analysis.md
```

The earned conclusion is therefore narrower and stronger than the initial
suggestion: ordinary arithmetic sees genus, the tested scalar-node graph block
adds no promoted class/genus information, inverse orientation is unavailable
by construction, and the bare modulus-one quotient is exact maximal erasure.
Only an explicitly retained preimage witness can carry the forgotten Gauss
transition.

## Claim Boundary

Allowed:

```text
The bounded representation enumeration is complete and exact.
The displayed pair and bilinear composition formulas are exact identities.
The D=-20 principal ledger has an exact 2*3=6 multiplicativity defect.
The two character channels pass the exact finite test through the named bound.
The strict graph contains the reported scalar nodes and edge occurrences.

Every represented integer maps to the sole residue zero in Z/1Z; retained
class distinctions are fibre provenance, not quotient arithmetic.
```

Disallowed:

```text
Modulus of One currently contains quadratic forms, Gaussian integers, ideal classes,
theta functions, or Epstein zeta functions as runtime objects.

A finite multiplicativity scan proves an Euler product.

The form-class labels are encoded by the scalar node or multiplication edge.

Quadratic-form positivity or a functional equation proves RH.

This probe computes or certifies any zeta zero.

The nontrivial C2 character phase `1/2 in Q/Z` is integer reduction modulo one.

Complete in-range scalar-edge coverage selectively identifies Gauss forms.
```

## Theta/Weil Continuation And Open Obligations

A later finite theta/Weil calibration correctly showed that class-basis cross
terms and the dual-point involution cannot be deleted without losing
information. It did not compute an arithmetic explicit-formula matrix, a
complete zero sum, a theorem-sufficient dense test space, rigorous numerical
enclosures, or a graph-native selection rule. Its exact fixtures and missing
obligations remain maintained in `../../moo_theta_weil_probe.py`,
`../../test_moo_theta_weil_probe.py`, and
[THETA_WEIL_CONSTRUCTIVE_OBLIGATIONS_NOTE.md](THETA_WEIL_CONSTRUCTIVE_OBLIGATIONS_NOTE.md); the completed-calibrations
archive also preserves their measured results and source hashes. This is an
active calibration and an explicit roadmap, not an RH result or a completed
analytic proof.

The modern discriminant `-23` inverse-class control remains here because it is
part of the frozen U850 nested ablation: its two nonprincipal inverse proper
classes have exactly the same scalar value set, so a scalar-only graph view
cannot distinguish them. This study identifies information a future native
witness relation would have to preserve. It does not supply a theorem about
theta functions or zeta zeros.
