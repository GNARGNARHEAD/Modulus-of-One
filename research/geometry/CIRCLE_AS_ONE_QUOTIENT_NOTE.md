# Circle As One: Quotient, Return, And Lost Lift

> Status: active speculative research note with a read-only strict-graph probe.
>
> evidence_layer: external exact quotient over positive-spine strict graph
>
> claim_status: exploratory observation, not runtime geometry
>
> Primary artifacts:
> `../../moo_circle_as_one_probe.py`,
> `../../moo_congruence_quotient_probe.py`,
> `../../out/experiments/circle_as_one_u40_wide_d12_v3.json`, and
> `../../out/experiments/circle_as_one_u80_d20_v3.json`, with the integer
> negative control in
> `../../out/experiments/circle_as_one_u40_integer_congruence_v1.json`.

## Foundational Correction

The useful proposal is not:

```text
the circle is literally the number 1
```

It is:

```text
1 is the full-turn return and identity point;
the circle is the quotient structure produced by identifying x with x+1.
```

The standard model is:

```text
R -> R/Z ~= U(1)
x -> exp(2*pi*i*x)
```

The number `1` has two different roles:

```text
on the covering line:
  1 is one unit of displacement

on the quotient circle:
  1 is one full turn and therefore the identity point again
```

This makes the model directly relevant to the failed proof of `2`. On the
line, `1`, `2`, and `3` are different lifts. After quotienting by integer
translation, all three land at the same observed circle point. The endpoint
does not retain how many full turns occurred.

The circle does not defeat the memory problem. It gives the memory problem an
exact mathematical form.

## Three Different "Modulus One" Constructions

These must not be conflated.

### Integer Congruence

```text
Z/1Z
```

has one residue class. Every integer maps to `0`. It is a legitimate trivial
quotient ring, but it is not a circle. Its bare quotient graph is one point with
one unlabeled loop regardless of the source arithmetic.

### Rational Or Real Phase

```text
Q/Z
R/Z
```

identify values whose difference is an integer. They have infinitely many
phase classes. `R/Z` is the circle group; `Q/Z` is its rational finite-return
subgroup.

### Indiscriminate Value Collapse

Mapping every graph value, including arbitrary rationals, into one bucket is
neither Gaussian integer congruence nor the phase circle. It is merely a generic
one-class abstraction.

The circle-as-one proposal uses the second construction. The first is a useful
negative control.

There is also an operator boundary. The additive structure descends to the
phase quotient:

```text
addition in Q/Z:
  becomes multiplication of phases in U(1)

subtraction in Q/Z:
  becomes multiplication by an inverse in U(1)
```

Ordinary rational multiplication and division do not descend in general. For
example:

```text
1/2 ~ 3/2 mod Z

(1/2)*(1/2) = 1/4
(3/2)*(1/2) = 3/4

1/4 is not equivalent to 3/4 mod Z
```

So the original four-operator fan cannot simply be copied onto the circle. The
quotient preserves the additive/subtractive part and changes its geometric
reading; it obfuscates the general multiplicative/divisive part. That loss is a
feature to inspect, not a defect to hide.

## The Information Collapse

Let:

```text
pi(x) = x mod 1
```

Then:

```text
kernel(pi) = Z
fibre over pi(x) = x + Z
```

The quotient retains:

```text
rational phase
relative position within one turn
finite additive return order for rational phases
```

It discards:

```text
integer lift
absolute winding count
which copy of the unit interval contained the source
```

This is not dimensional collapse in the narrow topological sense: `R` and
`R/Z` are both one-dimensional. It is nevertheless a clean information
collapse with explicit fibres. It can therefore act as the first rigorous
model for the broader dimensional-collapse programme.

Under Cartesian doubt, the observed return to the identity point does not prove
the lift. Recovering a winding count requires a continuously preserved path or
memory of the lift, which is precisely what the demon may attack.

## Rational Phase Before Completed Circle

The current Modulus of One graph contains exact rational values, so the first admissible
domain is:

```text
Q/Z
```

not the completed real circle.

For a reduced rational phase:

```text
p/q mod 1
```

the additive return order is exactly `q`:

```text
q * (p/q) = 0 mod 1
```

Under the exponential map, this is a root of unity:

```text
p/q -> exp(2*pi*i*p/q)
```

The order-`q` phases form a finite cyclic return structure. The number of
phases of exact order `q` is Euler's totient:

```text
phi(q)
```

This yields a disciplined ladder:

```text
1:
  identity / full-turn return

C_q:
  finite q-step return cycle / regular q-gon phase set

Q/Z:
  all rational finite-return phases / all roots of unity

R/Z ~= U(1):
  completed circle
```

The roots of unity are dense in the circle, but they are not the completed
circle themselves. Completion remains an Order-4 question.

## The Geometric-Series Closure

Let `z` be a non-identity root of unity of exact order `q`. Then:

```text
z^q = 1
```

and the finite geometric series closes exactly:

```text
1 + z + z^2 + ... + z^(q-1)
  = (1 - z^q) / (1 - z)
  = 0
```

This gives the polygon/circle framing a precise cancellation law:

```text
complete nontrivial orbit:
  returns to 1 multiplicatively and cancels to 0 additively

identity phase alone:
  does not cancel; q repetitions sum to q
```

That asymmetry may be useful for Modulus of One:

```text
identity accumulation versus complete-orbit cancellation
```

But the identity is currently external cyclotomic algebra. The graph probe may
report that a rational phase node exists and that its denominator predicts a
return order. It must not report the complex sum as a graph-witnessed Modulus of One
construction.

## Gauss As Framing

Gauss enters naturally through cyclotomy rather than through a generic appeal
to genius or number mysticism.

Three progressively stronger external lenses are relevant:

```text
roots of unity:
  equal division of the circle into finite cyclic phase sets

Gaussian periods:
  partition selected roots by multiplicative residue classes and sum each class

quadratic Gauss sums:
  weight/project phases by the square map and measure the surviving signal
```

For an odd prime `p`, the classical quadratic Gauss sum is:

```text
G(p) = sum from n=0 to p-1 of exp(2*pi*i*n*n/p)
```

and satisfies:

```text
G(p)^2 = (-1)^((p-1)/2) * p
```

The full unweighted phase cycle cancels. The square-selected/weighted phase
family leaves a highly constrained residual. That makes Gauss sums a plausible
later probe of the question:

```text
Which branch selections survive a projection that erases the unselected orbit?
```

Gauss's work on cyclotomy and regular polygons also gives the finite-return
structures geometric meaning. The later Gauss-Wantzel classification of
straightedge-and-compass constructible regular polygons is relevant framing for
which finite phase decompositions admit a particular construction grammar. It
does not show that the current Modulus of One graph has that grammar.

## Translation Into The Modulus of One Graph

The external quotient map sends every rational graph node `p/q` to its exact
residue phase:

```text
p/q -> (p mod q)/q
```

Nodes differing by an integer land in the same quotient fibre:

```text
p/q
(p+q)/q
(p+2q)/q
...
```

The quotient identifies them. The Modulus of One graph need not.

The graph may retain:

```text
different first stages
different confirmation status
different incoming construction counts
different operation signatures
different local neighborhoods
different witnessed +1 translations
```

This creates a direct test of the dimensional-collapse insight:

```text
quotient phase:
  what the shadow retains

integer lift:
  what the quotient erases

graph witness structure:
  possible surviving evidence about the erased lift
```

This is only an analogy until a representation map between geometric source
points and graph constructions is explicitly defined. Phase-fibre multiplicity
must not be identified with construction-witness multiplicity by wording alone.

## Read-Only Probe

The probe is:

```text
moo/circle_as_one_probe.py
```

It:

```text
maps each retained rational node to an exact Q/Z phase
groups observed integer lifts into quotient fibres
reports denominator / additive return order
checks the expected phi(q) count of primitive order-q phases
records first-stage and incoming-edge variation within each fibre
asks whether x + 1 -> x+1 is actually present as a graph edge
reports the finite geometric closure as external algebra only
```

It does not use floating-point complex numbers. Phase, lift, order, and cycle
are represented exactly by integers and reduced rational residues.

Example:

```sh
python3 -m moo.circle_as_one_probe \
  --db out/experiments/circle_as_one_u40_wide.sqlite \
  --max-denominator 12 \
  --max-phase-classes 24 \
  --sample-lifts 8 \
  --translation-pair-limit 8 \
  --pretty
```

## First Results

### U40 Wide-Aperture Control

Corpus:

```text
max_stage:      40
max_abs_value:  40
phase cutoff:   denominator <= 12
```

Report:

```text
research/experiments/circle_as_one_u40_wide_d12_v3.json
```

Summary:

```text
scanned graph nodes:                    340
observed Q/Z phase classes:              46
expected reduced phases through q=12:    46
phase-class coverage:                  1.00
phase classes with multiple lifts:       46
observed identity lifts:                  80
complete return orders:                 1..12
```

The return-order histogram is exactly the totient pattern:

```text
order q:  1  2  3  4  5  6  7  8  9 10 11 12
count:    1  1  2  2  4  2  6  4  6  4 10  4
          = phi(q)
```

This is expected quotient arithmetic, not a new Modulus of One discovery. Its value is
that the selected corpus exposes the complete rational phase skeleton through
the stated denominator cutoff.

Selected fibres:

| phase | order | observed lifts | first-stage spread | incoming-edge range | reported `+1` witnesses |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `0` / identity `1` | 1 | 80 | 39 | 1-81 | 8/8 |
| `1/2` | 2 | 20 | 37 | 1-20 | 0/8 |
| `1/3` | 3 | 14 | 37 | 1-13 | 0/8 |
| `1/4` | 4 | 10 | 33 | 1-10 | 0/8 |

The integer return fibre has witnessed `+1` translations because positive-spine
integers are operands. The sampled rational translations are absent with the
explicit blocker:

```text
operand_not_positive_spine
```

So the current graph contains rational phase points but does not internally
walk their predicted finite cycles.

The same quotient phase also collapses nodes with materially different graph
histories. For phase `1/2`, the observed lifts have a first-stage spread of 37
and incoming-edge counts ranging from 1 to 20. The quotient erases the integer
lift; the graph retains evidence that the lifts did not emerge identically.

### Integer Modulus-One Negative Control

Report:

```text
research/experiments/circle_as_one_u40_integer_congruence_v1.json
```

At U40:

```text
integer source nodes:                       80
integer quotient classes modulo 1:           1
integer-result edge occurrences:          2697
edge occurrences retained with decoration: 2697
non-seed operation-decorated signatures:     4
unlabeled non-seed quotient topologies:       1
```

The first operator fan makes the distinction visible:

```text
source results:       2, 0, 1, 1
projected residues:   0, 0, 0, 0
retained operations:  +, -, *, /
```

The bare integer quotient erases the asymmetry completely. Edge occurrence,
operation, stage, and status decoration preserve it. This is a direct example
of Modulus of One's graph carrying information that a value quotient destroys.

It also confirms why `Z/1Z` cannot itself be the proposed circle: it contains
only the negative-control one-bucket topology. The circle begins only when the
rational/real phase domain is admitted as an external observation space.

### U80 Narrow-Aperture Check

Report:

```text
research/experiments/circle_as_one_u80_d20_v3.json
```

Summary:

```text
scanned graph nodes:                    593
observed Q/Z phase classes:             128
expected reduced phases through q=20:   128
phase-class coverage:                  1.00
phase classes with multiple lifts:      128
observed identity lifts:                  85
complete return orders:                 1..20
```

The narrow `max_abs_value = 4` aperture retains all confirmed positive integers
but does not retain most `n + 1 -> n+1` speculative successor edges before
confirmation. Only the first three of the first eight reported positive
identity translations are present. The U40 wide-aperture control restores all
eight. This is a field-of-observation effect, not evidence that the later
integer return structure disappears.

## What The First Probe Establishes

The probe supports these narrow statements:

```text
1. The strict rational graph admits an exact external Q/Z quotient.

2. The tested corpora contain every reduced rational phase through the named
   denominator cutoffs.

3. Integer translation is collapsed by the quotient while graph stage and
   witness information remain lift-sensitive.

4. The integer spine can cast witnessed loops at the identity point under the
   quotient.

5. Rational finite-return cycles are not graph-operational under the current
   positive-spine operand rule.

6. Integer congruence modulo 1 and rational phase modulo 1 are different
   quotients: the former is a one-class negative control, while the latter
   carries the finite-return phase skeleton.
```

It does not establish:

```text
the circle as a runtime object
a topological path or homotopy type in the graph
a completed U(1)
a graph-native complex phase sum
a graph-native Gauss sum
certainty of winding count
```

## Next Falsifiable Studies

The U40 metric scout completed its first bounded matched-control run without
promoting a special within-fibre graph effect. That versioned negative result
does not retire the metric instrument: `../../moo_phase_metric_probe.py`, its
tests, and [PHASE_METRIC_COLLAPSE_NOTE.md](PHASE_METRIC_COLLAPSE_NOTE.md) remain maintained alongside the
exact shortest-arc metric, triangle slack, and retained-lift path helpers in
`../../moo_phase.py`. The measured U40 result and source identity are also
preserved in
[AUGUST_2026_EXTERNAL_PROBE_DISPOSITIONS.md](../../archive/completed_external_calibrations/AUGUST_2026_EXTERNAL_PROBE_DISPOSITIONS.md).

Another genuinely distinct geometry lead is
[PROJECTION_DEGENERACY_LEAD.md](PROJECTION_DEGENERACY_LEAD.md): it asks whether witness multiplicity and
collision order can distinguish projected source families after angle,
orientation, scale, and clock are quotiented away.

### Fibre Retention

Compare nodes `x+n` inside a phase fibre against matched controls:

```text
within-fibre neighborhood similarity
within-fibre operation-signature similarity
first-stage spacing
witness-count scaling
translation-edge coverage
```

Question:

```text
Does graph provenance systematically retain the integer lift that Q/Z erases?
```

### Graph-Selected Cyclotomy

For a fixed modulus `q`, select residue phases using an actual graph branch:

```text
square-branch witnesses
product-branch landings
prime-branch non-landings
matched value-only and random residue controls
```

Then compare their exact symbolic or high-precision phase sums. A signal is
interesting only if graph-based selection differs from the equivalent ordinary
residue-class selection and survives controls.

### Gauss-Sum Calibration

The first Gauss calibration should use the square branch at odd primes:

```text
n -> n*n
n*n mod p -> rational phase in Q/Z
```

The classical quadratic Gauss sum is the calibration target, not the claimed
discovery. The Modulus of One question is whether retained square-branch witnesses and
their controls organize the same phase family in a graph-distinctive way.

### Refinement Across Return Orders

When `d` divides `q`, compare the order-`d` phase structure with its placement
inside the order-`q` phase structure. This gives a first exact test of
cross-scale consistency before any higher-dimensional interpretation.

## Kill Rules

Downgrade the circle-as-one route if:

```text
phase grouping adds no graph information beyond ordinary denominator classes

within-fibre graph differences are fully explained by stage, magnitude, or
denominator controls

apparent Gauss/cyclotomic signals are produced entirely by externally supplied
residue arithmetic rather than graph-native branch selection

no return path is graph-witnessed and all circle language remains imported

completion language predicts no held-out rational phase or graph structure
```

## Allowed And Disallowed Language

Allowed:

```text
circle-as-one quotient model
1 as full-turn return / U(1) identity
exact rational phase fibre
integer lift lost under Q/Z projection
finite rational return order
external cyclotomic or Gauss framing
graph-retained evidence across collapsed lifts
```

Disallowed:

```text
Modulus of One has constructed the circle
the number 1 is literally the circle
Q/Z is already the completed circle
phase-fibre multiplicity is graph-witness multiplicity
the rational cycle is graph-witnessed despite the operand rule
return to 1 proves the winding history with certainty
Gauss's theorems follow from Modulus of One
```

## Short Version

```text
On the line, +1 changes the lift.
On R/Z, +1 makes one full turn and returns to the identity point 1.

The quotient forgets the integer lift.
The graph may retain its construction history.

That makes circle-as-one a precise first model of information collapse:
not a proof of the circle, but a falsifiable bridge between Modulus of One provenance,
rational return cycles, geometric-series cancellation, and Gauss's cyclotomy.
```
