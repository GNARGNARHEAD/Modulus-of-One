# Centered Reciprocal-Shell Lens

> Status: candidate external interaction lens; not a formal Modulus of One branch.
>
> The centered reciprocal geometry is exact. Its contact with the strict graph
> is an aperture question, not a runtime complex operation. The stronger claim
> that the same inversion preserves zeta zeros is rejected, both by an analytic
> accumulation obstruction and by the finite numerical control described below.

## Verdict

The useful object is the centered involution

```text
u = 2*s - 1
J(u) = -1/u
```

or, equivalently,

```text
I(s) = (s - 1) / (2*s - 1).
```

It exactly connects four structures that Modulus of One can keep separate and compare:

```text
centered reciprocal pairing        u -> -1/u
rational unit-shell pairing        t -> 1/t
rational phase reflection          r -> 1/2 - r mod 1
homogeneous sign-losing lift        S^2 = -I, [S]^2 = [I]
```

This is an exact structural alignment: the geometry itself is classical, while
its fit with these Modulus of One branches is the project-specific observation. It is
enough to justify a candidate interaction lens. It is not enough to
declare a graph-native branch: the complex coordinates, shell map, phase map,
and Mobius action remain external, and value co-presence does not supply a
transformation edge.

## Exact Centered Geometry

Start with the general centered coordinate

```text
u = (s - 1/2) / R
J(u) = -1/u,                 R > 0.
```

Then

```text
|J(u)| = 1/|u|.
```

The radius-one shell is therefore the unique radius level sent to itself;
radii below and above one exchange. This does not mean that it is the only
invariant set of the Mobius map. It is the unique self-dual *modulus level* in
this chosen coordinate.

The pointwise fixed units solve

```text
u = -1/u
u^2 = -1
u = +i or -i.
```

For the foundational normalization `R = 1/2`, one has

```text
u = 2*s - 1
I(s) = 1/2 - 1/(4*(s - 1/2))
     = (s - 1)/(2*s - 1).
```

Thus

```text
I(0) = 1
I(1) = 0
I(1/2) = infinity
I(infinity) = 1/2.
```

The fixed points in the `s` plane are

```text
s = 1/2 + i/2
s = 1/2 - i/2.
```

On the finite punctured critical line, the map compresses and reciprocates
height:

```text
I(1/2 + i*t) = 1/2 + i/(4*t).
```

The sign of nonzero `t` is retained and the paired ordinates satisfy
`t*t' = 1/4`. The puncture matters: `s=1/2` itself is exchanged with projective
infinity.

## The `u` Shell Is Not The `w` Shell

Introduce the endpoint-ratio coordinate

```text
w = (s - 1)/s = (u - 1)/(u + 1).
```

It gives the exact critical-line test

```text
|w| = 1
iff |s - 1| = |s|
iff Re(s) = 1/2.
```

In this coordinate the two relevant involutions are

```text
centered inversion I:       w -> -1/w
functional reflection:      w ->  1/w.
```

The extra minus sign is an opposition or half-turn in the external phase
picture. The two modulus-one statements must nevertheless not be merged:

```text
|u| = 1  <->  |s - 1/2| = 1/2      centered circle through 0 and 1
|w| = 1  <->  Re(s) = 1/2          critical line in the extended plane
```

Under the Cayley coordinate change, the `u`-unit shell maps to the imaginary
axis in the `w` plane, not to the `w`-unit shell. Both loci are invariant under
`w -> -1/w`, and they meet at `w = +/- i`, corresponding to the two fixed
points. Consequently, a statement such as "modulus one is self-dual" is
coordinate-specific. It is not a Mobius-invariant identification of the
centered circle with the critical line.

For any supplied point `rho`, the condition

```text
|w(rho)| = 1
```

is exactly another way to say `Re(rho) = 1/2`. Applied to all nontrivial zeta
zeros, it restates the Riemann hypothesis; it does not add evidence for it.

## Rational Unit Shell And Rational Phase Circle

The existing exact rational shell parametrization is

```text
U(t) = (1 - t^2)/(1 + t^2) + i*(2*t)/(1 + t^2),
```

with `t` in the extended rational line. Direct rational algebra gives

```text
-1/U(t) = U(1/t).
```

The endpoint and fixed cases are

```text
t = 0       <-> infinity      U = 1 <-> -1
t = 1       fixed             U = i
t = -1      fixed             U = -i.
```

This exact identity makes `t -> 1/t` a natural reciprocal-shell interaction to
audit against strict graph evidence. It does not turn `U(t)` into a graph
complex node or make the external identity a recorded graph edge.

Two dense external subsets of the unit circle occur in this project:

```text
U(Q union {infinity})                 rational-coordinate shell points
exp(2*pi*i*(Q/Z))                     roots of unity / rational phases
```

They are not the same set. Their intersection is exactly

```text
{1, i, -1, -i}.
```

Indeed, a root of unity with rational real and imaginary coordinates belongs
to `Q(i)` and is an algebraic integer. It must therefore be a Gaussian integer;
unit modulus leaves only the four Gaussian units. For example,

```text
U(1/2) = 3/5 + (4/5)*i
```

is a rational-coordinate shell point but not a root of unity.

The inversion preserves both domains, but by different parameter rules:

```text
shell parameter:       t -> 1/t
rational phase:        r -> 1/2 - r mod 1.
```

This domain separation is a required control, not a technical footnote.

## Normalized `w`-Plane `C4` Set, `D4` Reflection, And The Lift

In the normalized external `w` / `U(1)` plane, multiplication by `i` on the
four Gaussian units is the `C4` rotation

```text
1 -> i -> -1 -> -i -> 1.
```

Centered inversion acts differently:

```text
J(1)  = -1
J(-1) =  1
J(i)  =  i
J(-i) = -i.
```

It preserves the same four-point set but acts as a `D4` reflection: it swaps
the horizontal pair and fixes the vertical pair. Calling this action the
existing `C4` cycle would erase its cycle type. This statement is about the
normalized unit plane: the raw `s`-plane map does not preserve the raw set
`{1,i,-1,-i}`.

A homogeneous representative of the Mobius map is

```text
S = [[0, -1],
     [1,  0]].
```

It satisfies

```text
S^2 = -I
S^4 = I.
```

On signed homogeneous vectors this gives a four-step return, while in
projective space `S` and `-S` induce the same transformation, so `[S]` has
order two. This is a clean model of sign information lost under projection.

There is an important representative guardrail. A projective matrix is defined
only up to nonzero scalar; over complex scalars, rescaling `S` can change the
ordinary matrix order. The order-four lift is therefore meaningful only after
the real determinant-one representative, signed homogeneous-vector state, or
equivalent lift data has been named. The visible Mobius involution alone does
not canonically manufacture a `C4` runtime object. Its signed-vector lift is
also not the same action as multiplication by `i` on the four Gaussian units.

## Graph Aperture

The current strict positive-spine corpus can answer a narrower set of questions
than the external geometry:

```text
Is rational t present, confirmed, and operand-ready?
Is 1/t present, and is there a direct reciprocal construction witness?
Are the rational component nodes x, y, -x needed by U(t) and U(1/t) present?
What stages, statuses, and incoming edge occurrences support those nodes?
Are the rational phase calibrators 0, 1/4, 1/2, and 3/4 graph-visible?
```

That current corpus and operand policy cannot answer these as runtime facts:

```text
Does the current strict runtime contain the complex point U(t)?
Does it apply J, a phase reflection, or a Mobius transformation?
Does graph co-presence of t and 1/t form a transformation edge?
Does the current strict runtime evaluate or accumulate zeta(s)?
```

The probe must report parameter-node and shell-component visibility separately.
It must distinguish bare node presence, dynamic confirmation, operand
readiness, and direct edge occurrence. A complete external identity paired with
incomplete graph aperture is not a failed identity; it is censored graph
evidence. Conversely, complete component co-presence is not a graph-native
Mobius witness.

Repeated paired visibility may justify a better controlled interaction study.
It does not earn formal branch status until a named graph predicate, controls,
holdout behavior, and a promotion or kill rule exist.

## Why This Cannot Be The Proposed Zeta Zero-Set Symmetry

There is a decisive analytic obstruction. Nontrivial zeta zeros have
unbounded ordinates. If centered inversion preserved every such zero, choose a
sequence

```text
rho_n = beta_n + i*t_n,     0 < beta_n < 1,     |t_n| -> infinity.
```

It would produce distinct zeros

```text
I(rho_n) = 1/2 - 1/(4*(rho_n - 1/2)) -> 1/2.
```

The zeta function is analytic in a neighborhood of `s = 1/2` and is not
identically zero. Its zeros are therefore isolated there. An infinite sequence
of distinct zeros accumulating at `1/2` would contradict the identity theorem.
Hence `I` cannot preserve the nontrivial zero set globally.

There is a useful but different construction. If one precomposes zeta and
studies

```text
F_R(s) = zeta(I_R(s)),
```

then `s=1/2` becomes an essential singularity: `I_R` has a pole there and zeta
has an essential singularity at infinity. Zeros of `F_R` may therefore
accumulate at `1/2`; accumulation at a singularity does not violate the
identity theorem. This is a new representation obtained by changing the
argument of zeta, not a symmetry or permutation of the original zeta zero set.

This is stronger than a numerical counterexample. The numerical probe remains
useful because it makes the failure concrete using the same finite Hasse
machinery and graph-audited sources as the existing critical-strip work. At the
caller-supplied first-zero coordinate

```text
s0 = 1/2 + 14.134725141734693*i,
```

the paired point is

```text
I(s0) = 1/2 + 0.0176869374885714*i.
```

The finite `K=64` Hasse calculation gives a near-zero residual at the supplied
coordinate but a stable magnitude near `1.4594994686` at its inversion image.
That calculation is an external binary64 calibration, not a zero certificate;
it agrees with the exact analytic reason the proposed zeta-zero symmetry must
fail.

Functional reflection is the appropriate nearby control. On the critical line
`1-s` is the complex conjugate of `s`, and in the ratio coordinate it acts as
`w -> 1/w`, without compressing unbounded zero heights into a finite
accumulation point.

## First Bounded Run

The implementation is read-only. Two saved reports apply the same fixed
`n=1..8` aperture to the U80 corpus and the broader U300 corpus:

```text
research/experiments/euler/zeta_centered_inversion_first_zero_u80_v1.json
research/experiments/euler/zeta_centered_inversion_first_zero_u300_broad_v1.json
```

The bounded graph result is identical in both corpora:

```text
direct 1/n witnesses:                         8 / 8
reverse 1/(1/n) -> n witnesses:               1 / 8
nonidentity reverse blockers:                 7 operand_not_positive_spine
direct witness plus both shell points visible: n = 1 only
real-component opposition edges:              0 / 8
C4 phase-addition edges:                       0 / 4
```

The lone reverse witness at `n=1` is the identity `1/1 -> 1`; it is not a
repeated nontrivial return. For `n=2..8`, the positive-coordinate shell point
is visible but the opposed negative real component needed for its partner is
absent. This is stable from U80 to U300 and is exactly the current aligned
operand aperture, not a failure of the external shell identity.

At the quoted first-zero coordinate, the U80 and U300 reports also agree:

```text
|zeta(s0)| finite K=64 diagnostic:            2.1570095574950392e-15
|zeta(1-s0)| conjugation control:              2.1570095574950392e-15
|zeta(I(s0))|:                                 1.459499468625638
|zeta(1/2)| center control:                    1.4603545088095873
|zeta(1/2 +/- i/2)| fixed-point controls:      1.0653492124937796
```

All listed evaluations pass the configured terminal cutoff-stability check.
The source is a caller-supplied coordinate and the finite residual is not a
zero certificate, but the stable order-one image is a decisive numerical
rejection at this point and agrees with the analytic global obstruction.

## Probe Contract

The read-only implementation is
`../../moo_zeta_centered_inversion_probe.py`. The fixed small run is:

```sh
python3 -m moo.zeta_centered_inversion_probe \
  --db out/experiments/circle_as_one_u80.sqlite \
  --t '14.134725141734693' \
  --hasse-terms 64 \
  --shell-max-integer 8 \
  --near-zero-tolerance 1e-10 \
  --stability-tolerance 1e-12 \
  --target-label first_nontrivial_zero_coordinate \
  --pretty
```

The report should keep five ledgers separate:

1. exact coordinate and matrix identities;
2. `C4` rotation versus `D4` reflection action tables;
3. rational-shell and rational-phase domain separation;
4. strict graph aperture for rational parameters, components, and witnesses;
5. external Hasse values at the target, functional reflection, inversion image,
   and fixed points.

Required controls are involution round-trip, modulus reciprocity, fixed-point
checks, exact shell pairing, phase-action checks, `U(1/2)` as a non-root-of-
unity witness, functional reflection, multiple Hasse cutoffs, and the analytic
accumulation obstruction.

The machine-readable first-zero classification is:

```text
exact_centered_geometry_verified
external_projection_only_insufficient_repeated_graph_witnesses
supplied_near_zero_not_preserved_by_centered_inversion
global_fixed_radius_zero_set_symmetry_analytically_obstructed
candidate_centered_reciprocal_shell_lens_not_promoted
```

It must not be reported as a discovered zeta-zero symmetry, an RH mechanism, a
runtime complex construction, or a formal Modulus of One branch.

## Lens Registration

```text
name:
  centered reciprocal-shell interaction lens
evidence_layer:
  exact_external_geometry_over_strict_graph
claim_status:
  candidate, with zeta-inversion subclaim rejected
provocative_hypothesis:
  The exact t <-> 1/t shell pairing may expose repeatable reciprocal/component
  aperture in strict graph corpora.
false_positive_guarded_against:
  Merging the u-shell with the w-shell; merging U(Q) with roots of unity;
  calling a D4 reflection the C4 rotation; inferring an edge from co-presence;
  or treating a coordinate identity as a zeta symmetry.
graph_native_observable:
  Parameter and component nodes, stages, confirmation/readiness status, direct
  reciprocal and construction edges, and retained edge occurrences.
query_or_report:
  moo/zeta_centered_inversion_probe.py and this note.
metric:
  Exact identity pass rate, paired node/component coverage, direct witness
  coverage, corpus censoring, Hasse residual and cutoff stability.
null_model_or_control:
  C4/D4 action distinction, u/w locus distinction, rational-phase/domain
  control, functional reflection, fixed points, multiple cutoffs, and the
  analytic accumulation obstruction.
promotion_criteria:
  A preregistered corpus sweep finds repeated, control-separated graph-visible
  reciprocal/component interaction with a named graph predicate and holdout.
kill_criteria:
  Co-presence is the only graph support; matched reciprocal controls behave the
  same; the effect is bound-sensitive; or any zero-set invariance is required.
allowed_claim_language:
  "This external centered involution pairs these exact rational shell
  parameters and exposes this bounded strict-graph aperture."
disallowed_claim_language:
  "Modulus of One contains this Mobius map," "the inversion is the C4 cycle," "zeta has
  this symmetry," "this supports RH," or "this is a formal branch."
```
