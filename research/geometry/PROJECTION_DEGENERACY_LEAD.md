# Projection Degeneracy And Minimal Representation Lead

> Status: speculative-only geometry lead.
>
> This note preserves the project-relevant idea from a broader conversation
> archive. It is not evidence that Modulus of One currently reconstructs geometry, and it
> does not add geometric objects or projection operators to the runtime.

## Question

When a higher-dimensional object is observed through a lower-dimensional
projection, many different sources can produce the same visible points. What
survives if the external coordinate frame, viewing angle, orientation, and
clock are not trusted?

The candidate answer is not the projected coordinates alone. It is the exact
pattern by which distinct source witnesses become indistinguishable:

```text
source relations
-> projected values
-> collision multiplicities and event order
-> equivalence class of possible sources
```

This matches Modulus of One's existing epistemic discipline: a resulting value is not the
whole object. Distinct witnessed constructions that meet at that value remain
distinct evidence.

## Exact Calibration

For a rectangle with half-widths `a,b`, an orthogonal projection of its four
vertices onto a line has coordinates

```text
+/- a*cos(theta) +/- b*sin(theta).
```

Generically these are four positions. A three-position collapse occurs when

```text
a*cos(theta) = b*sin(theta),
```

so, when the ordinary coordinate description is admitted,

```text
tan(theta) = a/b.
```

For a square, `a=b`, and the familiar diagonal collapse occurs at 45 degrees
modulo its symmetries. The angle is only an external calibration. The proposed
invariant observation is the event structure:

```text
four distinct positions
-> one pair approaches
-> one multiplicity-two collision
-> the pair separates
```

An arbitrary monotone reparameterization of the clock changes speeds but not
the collision, its multiplicity, or the order of collision events. Those are
the first candidate projection invariants.

## What Must Be Retained

A probe should keep at least:

- the number of distinct projected positions;
- the source-witness multiplicity at each position;
- which source witnesses collide;
- the ordering and partial ordering of collision events;
- exact ratios among simultaneous separations, when defined;
- repetitions induced by source symmetries;
- the assumptions placed on the source family.

It should discard or explicitly treat as external:

- absolute angle;
- orientation and handedness;
- absolute clock time and rotation speed;
- a name such as triangle, square, or circle before it is distinguished from
  competing source families.

## First Falsifiable Experiment

Use exact rational or symbolic source coordinates for a small frozen family:

```text
line segment
several triangle classes
square
non-square rectangles
selected irregular quadrilaterals
finite rational samples from a circle shell
```

Generate their one-dimensional projection event ledgers, then quotient away
absolute angle, orientation, scale, and monotone time reparameterization. Ask
which source families remain distinguishable using only collision provenance
and exact relational invariants.

The experiment should report equivalence classes, not force a classifier to
name every source. An indistinguishable pair is a valid result: it identifies
a real information boundary.

Required controls include:

- relabeling source vertices;
- scale and translation changes;
- reflection and orientation reversal;
- monotone but highly nonuniform time changes;
- irregular shapes matched to a regular shape's selected collisions;
- removing multiplicity or provenance to measure exactly what those fields
  contribute.

## Relation To The Current Graph

The strict Modulus of One graph already records multiple construction occurrences that
can land on one rational value. That is an analogy and possible data model, not
yet a geometric projection theorem. A future graph-native connection needs an
explicit map from construction witnesses to a frozen projection ledger and a
held-out prediction that is not explained by value, stage, or exposure alone.

## Claim Boundary

Allowed:

```text
Collision multiplicity and event order can retain information erased by a
lower-dimensional value projection.

This exact source family has this projection-equivalence class under the named
quotient of observational freedoms.
```

Not allowed:

```text
Three points mean triangle.
Four points mean square.
Modulus of One currently reconstructs hidden dimensions.
A projection analogy is evidence for a runtime geometric object.
```

## Promotion And Stop Rules

Promote this from a speculative note only if an exact, deterministic probe
separates at least one held-out source family after all declared observational
freedoms are quotiented out and after matched irregular controls.

Stop or narrow the lead if the proposed fingerprint is fully reproduced by
simple multiplicity counts, depends on the discarded angle/clock, or cannot
distinguish regular sources from matched irregular controls.
