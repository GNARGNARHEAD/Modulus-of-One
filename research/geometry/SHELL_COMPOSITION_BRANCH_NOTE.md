# Witnessed shell composition / candidate circle branch

Date: 2026-09-20

evidence_layer: external_probe
claim_status: candidate

The definition below is a proposed research schema. Its algebraic lemmas are
classical exact mathematics. Actual instances require graph witnesses and are
reported separately in the [composition audit](SHELL_COMPOSITION_20260920.analysis.md).
This note changes no runtime operand, confirmation, or certainty rule.

## Proposed definition

> The shell-composition branch is the repeated witnessed agreement of two
> self-products with a third self-product, together with witnessed compositions
> preserving that agreement. Normalization observes unit-shell positions while
> the underlying construction histories remain distinct.

The short label **candidate circle branch** refers to this relation and its
specified projection. A complete Euclidean circle additionally requires a
metric and completion. Neither a formula nor a finite witness bundle alone
establishes that completed object.

This extends the existing [shell relation](SHELL_SQUARE_RATIO_BRANCH_NOTE.md).
It adds ordered composition and explicitly retains orientation; it does not
replace the older sorted-leg search or its results.

## Witness object and membership

Fix a field F and checkpoint U. A source state is an ordered, signed integer
triple A=(a,b,r), r>0, with a named witness bundle:

    a*a -> a2
    b*b -> b2
    r*r -> r2
    a2+b2 -> r2

The two references to r2 must identify the same node. Record every named edge
occurrence, its input/output nodes, stage, and operand confirmation status.
The triple's numerical equality alone does not supply this bundle.

For B=(c,d,s), the composition requests are:

    a*c -> ac          b*d -> bd
    a*d -> ad          b*c -> bc
    ac-bd -> u         ad+bc -> v
    r*s -> w

The same intermediate node must connect each product to its later use. Reuse
is legal only once the selected field permits it; an early product output does
not automatically become an operand. The resulting ordered triple is (u,v,w).

There are distinct evidence predicates:

1. `composition`: the seven construction roles are retained.
2. `source_composition`: both direct source-shell bundles and the composition
   are retained.
3. `full_closure`: source_composition and the direct target-shell bundle are
   retained.

The norm identity below makes level 2 an external algebraic certificate of the
target's shell equality. It is not a retained level-3 direct proof. A repeated
branch claim must specify which predicate repeats; a single full_closure case
does not demonstrate general graph closure. Repeated roles may share an edge;
they are not independent occurrences.

In the current field, integer zero and negative results can be recorded but
cannot be operands. Thus some signed target states are visible without their
direct square witnesses, and identity/inverse operations can be blocked.
Those are field limitations, not failures of the external algebra.

## Exact composition and its quotient

For integer shell triples define the external operation

    (a,b,r) o (c,d,s) = (ac-bd, ad+bc, rs).

Expanding both squares proves

    (ac-bd)^2 + (ad+bc)^2
      = (a^2+b^2)(c^2+d^2)
      = (rs)^2.

This works for every signed choice with r,s positive. It requires no
trigonometry, irrational constant, or completed real object.

Observe a triple by P(a,b,r)=(a/r,b/r). Identify triples only at this observation
level when they differ by a common positive rational scale. The observations
are precisely

    G_Q = {(x,y) in Q^2 : x^2+y^2=1},
    (x,y)*(u,v) = (xu-yv, xv+yu).

Their identity is (1,0), and the inverse of (x,y) is (x,-y). Associativity
follows, for example, by representing (x,y) with the rational matrix

    [[x,-y], [y,x]]

and multiplying matrices. This matrix preserves the sum of two squares of
any rational vector, hence preserves squared differences as well. Interpreting
those differences as Euclidean distances is an explicit geometric choice.
G_Q is the observation space of the external all-triple family, not the image
of every finite field or a claim that all its coordinates are runtime nodes.

For a raw triple, composing with (a,-b,r) gives (r^2,0,r^2), a scaled identity.
The witness histories have not cancelled or become identical. Commutative and
associative value equalities likewise need not identify construction histories.
The group belongs to the normalized observation, not automatically to the
space of witnesses.

## Coverage without an infinite-valued parameter

For finite integers (m,n) other than (0,0), set

    T(m,n) = (m^2-n^2, 2mn, m^2+n^2).

The square identity proves every T is a shell triple. A common nonzero rational
rescaling of (m,n) leaves its normalized observation unchanged. This is the
meaning of a projective parameter pair [m:n]. For m nonzero, t=n/m gives

    U(t) = ((1-t^2)/(1+t^2), 2t/(1+t^2)).

Conversely, for (x,y) in G_Q other than (-1,0), put t=y/(1+x). Substitution
recovers both coordinates. Write this rational t as n/m to obtain an integer
parameter pair. The remaining point is P(T(0,1))=(-1,0).

Thus the family covers all rational unit-shell positions. No literal infinity
or division by zero is required. The projective composition is total:

    [m:n] * [p:q] = [mp-nq : mq+np].

Its output pair is nonzero because

    (mp-nq)^2 + (mq+np)^2 = (m^2+n^2)(p^2+q^2) > 0.

In the finite chart this gives (t+u)/(1-tu), but the homogeneous formula also
handles its missing denominator case. This is projective chart closure, not
metric completion. All-parameter coverage is an external theorem; a finite
corpus still witnesses only a bounded subset of its instances.

One parameter is not one generating state. Iterating a rational-coordinate
state can introduce no new denominator primes under this composition. Powers
of (3/5,4/5), for example, cannot reach (5/13,12/13), although they remain on
the shell. Mere composition closure also admits the four axis points alone.

## Information that normalization must preserve separately

Sorting legs or taking absolute values discards information required by the
composition. Let A=(3,4,5) and B=(4,3,5). Their sorted triangle shapes agree,
but

    A o A = (-7,24,25),
    A o B = (0,25,25).

Even after forgetting signs, these outputs have different shapes. Composition
therefore does not descend through that shape equivalence. Keep ordered signs
for the action; use a sorted shape only as an additional observation.

Likewise, (4,3,5) composed with itself and (8,6,10) composed with itself give
the same normalized position, but different raw triples, edges, and readiness
requirements. Scale equivalence does not erase provenance.

## What would distinguish circles

Two components, a fixed positive-definite quadratic form, and coverage matter.
A difference of squares instead permits hyperbolic structure. Even among
positive forms there is a family of equally exact alternatives:

    Q_k(a,b) = a^2 + k*b^2,
    (a,b,r) o_k (c,d,s) = (ac-k*bd, ad+bc, rs),

for fixed positive rational k. The same expansion preserves Q_k. A claim that
Modulus of One privileges k=1 needs an argument or comparison beyond having found a
composition identity. Over the usual coordinate metric, other k give ellipses;
relative to Q_k they are unit circles. Choosing a metric is substantive.

With the usual Euclidean distance, G_Q is dense in the real unit circle but
is not itself a continuous loop. Its metric completion is the real circle.
A constructive formulation uses Cauchy names with explicit error control.
Admitting this operation is separate from recording finite rational witnesses.

An ordinary circle in a larger ambient Euclidean space still lies in an affine
two-plane. Admitting all directions at fixed distance yields a sphere instead.
Neither arbitrary dimension nor a general norm-preserving action specifies a
circle on its own.

## Rational phase is a different structure

Every element of Q/Z has finite additive order. In G_Q only the four axis
positions have finite multiplicative order. A finite-order x+i*y lies in Q(i)
and is an algebraic integer; it therefore lies in Z[i]. Unit norm leaves only
1,i,-1,-i. This is classical algebra, also recorded in the
[reciprocal-shell note](../euler/CENTERED_RECIPROCAL_SHELL_LENS_NOTE.md) and
[Yekutieli, section 3](https://arxiv.org/html/2101.12166v2#S3).

In fact every group homomorphism f:Q/Z -> G_Q is trivial. Its image consists
of those four finite-order states. For any r choose s with 4s=r; then
f(r)=f(s)^4=1. Hence no nontrivial rational-to-rational bridge preserves both
operations. Enlarging the coordinate field or admitting completion is needed
for the usual correspondence. The four common landmarks do not extend to a
homomorphism defined on all rational phases with values in G_Q.

This mismatch is not by itself evidence for transcendence. Rational phases
give roots of unity and algebraic coordinates; a third turn already requires
(-1/2,sqrt(3)/2). Do not equate circularity with finite return of every step.

## Measure and pi are additional constructions

On a finite parameter chart, a direct calculation for the composition map
F_a(t)=(a+t)/(1-at) gives

    dF_a/(1+F_a^2) = dt/(1+t^2).

This invariant differential is determined only up to scale. Once Euclidean
arc length is admitted, differentiating U gives |U'(t)|=2/(1+t^2). Four copies
of the first quadrant then have total length

    C = 8 * integral from 0 to 1 of dt/(1+t^2).

Classically C=2*pi. This derives the circumference from the shell plus the
chosen length/completion rules; a separate Q/Z construction is not necessary.
It is not a finite rational runtime construction of pi. The existing
[area bridge](CIRCLE_SQUARE_AREA_BRIDGE_20260911.analysis.md) makes a related
passage through explicit rational bounds.

Uniform measure does not supply an absolute length scale. On the completed
compact circle, invariant regular measure is unique up to scale. On the
countably infinite rational group itself, a countably additive invariant
probability measure on all subsets is impossible: all singletons would have
the same mass, giving either zero total mass or infinite mass. Do not silently
import the completed-circle probability measure as a counting measure on
rational states.

## Circular potential belongs to observation

Fix both an admissible class of source constructions and an observation map.
Evidence E selects the sources consistent with E. Adding evidence can shrink
that set, but need not shrink it strictly or identify one source. A circle
collapsed to a point by the map is an exact example of information loss.

Compatibility with a circular source is not proof of circular origin. Finite
points can also be compatible with noncircular sources. Changing projection,
metric, or hidden dimension for each observation removes the constraint. This
observation question is distinct from the definition of branch membership.

## Branch card

```text
branch_name: witnessed shell-composition / candidate circle branch
moo_relation: repeated square/addition agreement and its preserved composition
operator_fan_root: mixed self-product, addition, subtraction, product, ratio
active_field: named positive-spine corpus and checkpoint; signed action external
eligible_sources: ordered integer triples, positive radius, named shell witnesses
witness_event: the source, composition, and target roles defined above
shadow_values: raw triples and separately normalized ordered rational pairs
membership_reading: full_closure for a directly witnessed closure instance;
  report source_composition and composition as explicitly weaker predicates
non_membership_reading: separate disagreement, missing retention, future operands,
  and structurally prohibited operands; absence is scoped to the named field
linearity_reading: the same finite relation schema recurs, not one trajectory
relation_distance: common dependence on self-relation/addition/composition roles;
  no numerical relation-distance invariant is established
stage_distance: earliest joint availability of the required retained events
witness_depth: two source-shell bundles, seven composition roles, target bundle;
  duplicates remain shared roles rather than independent witnesses
interaction_reading: structural dependency plus shared intermediate/result nodes
machine_fields: nodes, ordered requests, occurrence IDs/stages, confirmation,
  agreement, missing roles, predicted/observed readiness, checkpoint, input hashes
known_classical_shadow: rational unit circle and its rotation-composition group
allowed_claim_language: named witnessed composition/closure at a stated checkpoint
disallowed_claim_language: completed native circle, unique geometry, or pi from
  the finite motif; external identities relabelled as retained operations
weakening_or_kill_rule: missing witnesses weaken membership; ordinary readiness
  explaining timing kills a residual-timing claim; comparison-free closure does
  not establish that Modulus of One privileges this relation
```

## Open obligations

The audit establishes only its reported finite instances. General witness
coverage, a signed field's confirmation rule, and a reason to select the
two-square relation remain separate questions. Completion and measure require
explicit additional constructions. Any claim of privileged organization needs
new controls fixed before measurement; the current calibration is not that
experiment.
