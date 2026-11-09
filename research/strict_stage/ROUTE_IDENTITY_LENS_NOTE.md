# Route Identity Lens Note

> Status: controlled external calibration.
>
> evidence_layer: strict graph plus declared external route certificates
>
> claim_status: route quotient validated; semantic independence unresolved

## Result

The 216 and Pascal calibration examines which construction distinctions
survive explicit route quotients and generator controls. Its graph-native
result is a route-identity discipline:

```text
edge occurrence
-> directed algebraic witness
-> commutative edge orbit
-> associative/commutative expression certificate
-> external semantic label
```

Each arrow is an explicit quotient. A label such as `cube_surface` or
`cube_volume` cannot manufacture a new graph route after the arithmetic
certificate has collapsed.

The calibration also produces an important null result. At strict stage U1000,
all aggregate incoming-route mass for node `216` is predicted exactly by the
generator. The value is therefore useful because named certificates collide
there, not because its raw derivation count is anomalous.

## Reproducible Evidence

Corpus:

```text
out/experiments/pascal_cubic_scale_u1000.sqlite
complete stage: 1000
nodes:          856601
edges:          4000001
strict alignment: pass
```

Probe and reports:

```text
moo/route_identity_probe.py
research/experiments/216/route_identity_216_u1000_v2.report.json

moo/pascal_edge_probe.py
research/experiments/pascal_cubic_u1000_v3.report.json
```

Route report command:

```text
python3 -m moo.route_identity_probe \
  --db out/experiments/pascal_cubic_scale_u1000.sqlite \
  --target 216 \
  --control 215 --control 217 --control 231 \
  --case cubic-216 \
  --milestone 18 --milestone 36 --milestone 125 --milestone 216 \
  --control-radius 16 \
  --witness-limit 24 --edge-ref-limit 4 \
  --pretty --include-checksums \
  --write research/experiments/216/route_identity_216_u1000_v2.report.json
```

Neighborhood return:

```text
python3 -m moo.graph_query \
  --db out/experiments/pascal_cubic_scale_u1000.sqlite \
  --node 216 --neighborhood --pretty
```

## Identity Ladder

### 1. Edge Occurrence

An occurrence preserves `edge_id`, stage, operation, input order, and result.
This is the most detailed stored event identity.

### 2. Directed Witness

Repeated occurrences of the same:

```text
(op, left value, right value, result value)
```

count once. Direction still matters.

### 3. Commutative Witness

Inputs are sorted for `+` and `*`. They are not sorted for `-` or `/`.

Therefore:

```text
6 * 36 -> 216
36 * 6 -> 216
```

are one commutative witness backed by two directed edge occurrences:

```text
edge 4924 at stage 36
edge 5068 at stage 36
```

### 4. Associative/Commutative Expression

Declared construction trees flatten and sort same-operation `+` and `*`
components while preserving operand multiplicity. For example, every
parenthesization and permutation of:

```text
27 + 64 + 125
```

has one AC expression family. The different stored histories may still be
counted as a symmetry/path orbit, but not as independent route families.

The probe deliberately does not quotient through distributivity,
factorization, exponent expansion, geometry, or all field identities. A full
ring/field quotient would collapse every expression to its value and erase the
construction object being studied.

### 5. Semantic Family

Labels such as:

```text
cube volume
cube surface
prime factorization
right-triangle side cubes
binomial expansion
```

are analysis-layer annotations. They can declare dependencies and suggest
controls. They do not alter graph identity.

## The One-Step Multiplicity Null

For a complete wide strict positive-integer corpus through stage `U`, and
`1 <= n <= U`, the incoming directed event count is forced by the generator:

```text
addition:       n - 1
subtraction:    U - n
multiplication: tau(n)
division:       floor(U/n)

D_U(n) = U - 1 + tau(n) + floor(U/n)
```

After the commutative quotient:

```text
addition:       floor(n/2)
subtraction:    U - n
multiplication: ceil(tau(n)/2)
division:       floor(U/n)

Q_U(n) = floor(n/2) + (U-n) + ceil(tau(n)/2) + floor(U/n)
```

For `U=1000`, `n=216`, and `tau(216)=16`:

```text
directed events:
  215 + 784 + 16 + 4 = 1019

commutative-normalized witnesses:
  108 + 784 + 8 + 4 = 904
```

The report observes exactly `1019` and `904`. There is no residual. Aggregate
one-step collision mass is therefore generator mechanics, not salience.

Local controls agree with that reading:

```text
value  directed  normalized  normalized multiplication witnesses
215        1007         898       2
216        1019         904       8
217        1007         897       2
231        1011         892       4
```

Within the symmetric `200..232` window, `216` ranks first of 33 only on
unordered multiplication witnesses. That is ordinary divisor richness. It
ranks seventh on normalized total witness mass and seventh on first arrival.

## Declared 216 Certificates

The built-in calibration validates every internal edge, names its aperture,
and compares multiple quotient fingerprints.

```text
certificate                         complete stage  AC expression
prime_cube_product                              27  *(2,2,2,3,3,3)
cube_volume_6                                  36  *(6,6,6)
cube_surface_6                                 36  *(6,6,6)
binomial_3_plus_3_cube_expansion              108  dependent expansion tree
right_triangle_side_cubes                     125  +(*(3,3,3),*(4,4,4),*(5,5,5))
```

All five certificates are visible in the U1000 corpus.

The target node itself appears earlier, at stage `18`, through the factor pair
`12 * 18`. It is confirmed by the positive spine at stage `216`. Thus:

```text
value arrival != route arrival != confirmation
```

### Surface Versus Volume

At side `6`:

```text
cube surface: 6 * (6 * 6)
cube volume:  (6 * 6) * 6
```

Both normalize to:

```text
*(6,6,6)
```

They are distinct external geometric roles projected onto one arithmetic
certificate. They are not two Modulus of One routes.

The corrected Pascal cubic report exposes the same issue for the scale-1
labels `area_half` and `semiperimeter`: both reduce to the single directed
witness `12 / 2 -> 6` (`edge_id 493`). Typed geometric roles may differ, but
the current scalar graph certificate does not.

The equality of surface and volume is also scale-specific:

```text
surface = 216 r^2
volume  = 216 r^3
volume / surface = r
```

They coincide only at `r=1`. This coincidence must not be conflated with the
right-triangle cubic closure, which holds for every positive scale.

### Factorization And Binomial Rewrites

`2^3 * 3^3` is graph-distinct from the `6^3` leaf cut, but both carry the
declared dependency `six_cube_identity`. It is a factorization rewrite, not an
independent discovery.

The value side of the `(3+3)^3` binomial expansion is also graph-distinct but
declared algebraically dependent on the same cube identity. Equal expansion
terms collapse to shared scalar nodes, so the graph does not retain every
coefficient role. This is a useful Pascal/exponent-lift calibration, not a
distinctive Pascal branch.

### Side-Cube Closure

The exact side-cube certificate includes:

```text
3 * 3 -> 9
9 * 3 -> 27
4 * 4 -> 16
16 * 4 -> 64
5 * 5 -> 25
25 * 5 -> 125
9 + 16 -> 25        premise edges 934, 998; stage 16
27 + 64 -> 91       edges 15982, 16238; stage 64
91 + 125 -> 216     edges 61866, 62366; stage 125
```

The square-sum relation is recorded as a required `premise` edge. It does not
change the AC fingerprint of the cubic construction, but the external
right-triangle label is unsupported unless this premise is also visible.

This certificate and `6^3` are different AC construction schemas at the
declared leaf cut. That makes their convergence the strongest route-collision
object in the probe. It is still theorem-linked and shares the universal
positive-spine root `1`, so the report calls it `distinct_at_cut_only`, not
globally independent evidence.

## Exact 3-4-5 Closure Theorem

Let `a,b` be the legs, `c` the hypotenuse, `s` the semiperimeter, and `r` the
inradius of a positive Euclidean right triangle. Then:

```text
c = s - r
a + b = s + r
ab = 2rs
```

Therefore:

```text
a^3+b^3+c^3
  = (s+r)^3 - 6rs(s+r) + (s-r)^3
  = 2s^3 - 6rs^2

Delta_3
  = s^3 - (a^3+b^3+c^3)
  = s^2(6r-s)
  = s^2(5r-c)
```

Since `s>0`:

```text
Delta_3 = 0
iff c = 5r
iff s = 6r, a+b = 7r, ab = 12r^2
iff {a,b} = {3r,4r}
```

Thus zero cubic defect holds exactly on the `3-4-5` similarity class, for all
positive real scales. The bounded scan is only a computational witness to this
theorem; it is not the proof.

The right-triangle domain is essential. The non-right triangle `(29,29,42)`
has `c=5r` but cubic defect `2134`, so neither the formula nor the conclusion
extends unchanged outside the stated domain.

## External-Probe Disposition

The arithmetic calibrations have the following results:

```text
Pascal local recurrence:       generic witness; killed as distinctive signal
72/144/216 golden rotation:    dependent on the 144 Fibonacci near-return
231 phi-return association:    rejected
3-4-5 cubic closure:           exact structural theorem
216 aggregate route mass:      exact generator null
216 named route collision:     qualified; side cubes vs 6^3 survives the route quotient
```

This is the useful result of the exercise: most tempting patterns weaken,
collapse, or fail under explicit controls, while one exact structural
convergence survives in a narrower form.

## Kill Rules And Next Tests

Kill or downgrade a route claim when:

```text
commutative reversal explains the apparent multiplicity
associative regrouping explains the apparent multiplicity
the aggregate count matches the strict-generator closed form
two names resolve to the same edge references
a required internal edge is missing inside a complete eligible aperture
a declared dependency explains the second certificate
the result depends on post-hoc target selection
```

Next useful tests are:

1. Freeze route schemas before scanning targets, then test held-out collisions.
2. Compare other right triangles, cubes, exponents, and polynomial lifts.
3. Match controls by value, first stage, divisor profile, operation exposure,
   route cut, and aperture.
4. Count commuting-path orbit size separately from AC family identity.
5. Add confirmation gates to certificates when an intermediate is produced
   speculatively before later operand use.
6. Keep explicit failures, including `231`, in the result ledger.

The graph remains primary. The external system supplies candidate structure;
exact nodes, edges, quotient rules, aperture, dependencies, and controls decide
what survives.
