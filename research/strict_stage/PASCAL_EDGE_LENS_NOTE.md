# Pascal Edge Lens Note

> Status: controlled null result plus route-identity calibration.
>
> This note replaces the weaker "Pascal edges appear in Modulus of One" reading with an
> edge-specific, control-aware lens. The local recurrence result is mostly a
> null result; the surviving lead is route identity, path multiplicity, and
> controlled exponent-lift route collision. See [ROUTE_IDENTITY_LENS_NOTE.md](ROUTE_IDENTITY_LENS_NOTE.md)
> for the explicit commutative and associative quotients.

## Frame

Pascal's triangle is useful here only when treated as a rooted graded
construction graph, not as a value array.

The external mathematical frame is:

```text
Pascal graph / Pascal-Bratteli diagram:
  vertices: (n,k)
  cover edges: (n,k) -> (n+1,k) and (n,k) -> (n+1,k+1)
  projected value: number of root-to-(n,k) paths = C(n,k)
```

So the coefficient is not the primary object. The primary object is the edge
system whose path count projects to the coefficient.

This matters because Modulus of One's strict positive-spine corpus already records
eligible arithmetic closure. A local edge witness:

```text
C(n-1,k-1) + C(n-1,k) -> C(n,k)
```

is exact graph evidence, but it is not specific evidence for Pascal unless it
survives controls against other additive triangles.

## Reports

Corpora:

```text
out/experiments/pascal_edge_probe_u300.sqlite
out/experiments/pascal_cubic_scale_u1000.sqlite
```

Probe and reports:

```text
moo/pascal_edge_probe.py
research/experiments/pascal_edge_probe_u300_v2.report.json
research/experiments/pascal_coefficient_u1000_v2.report.json
research/experiments/pascal_subset_u1000_v2.report.json
research/experiments/pascal_cubic_u1000_v2.report.json
research/experiments/pascal_cubic_u1000_v3.report.json
research/experiments/pascal_controls_u300_v1.report.json
research/experiments/pascal_controls_u1000_v1.report.json
research/experiments/pascal_controls_u300_v2.report.json
research/experiments/pascal_controls_u1000_v2.report.json
research/experiments/216/route_identity_216_u1000_v2.report.json
```

The probe now has a `controls` mode for additive null triangles and prime
subset-lattice aperture thresholds.

The `v3` cubic report supersedes `v2` for route-alias and retention-aware
fields. The `v2` control reports supersede their `v1` counterparts by naming
prime-lattice results as stage-threshold eligibility rather than complete
visibility. The older paths remain listed only as historical artifacts.

## What Dies

The claim:

```text
Pascal's triangle overlaps Modulus of One because Pascal recurrence additions are present.
```

does not survive controls.

At U1000, the coefficient recurrence report through row 30 found:

```text
interior positions:        435
eligible by stage:         162
eligible complete:         162
unexpected eligible miss:  0
```

That is mechanically correct, but the controls show it is non-specific.

For rows 0..15 at U1000:

```text
Pascal additive triangle:
  total interior recurrence cases: 105
  eligible by stage:                92
  eligible complete:                92

20 random positive additive triangles:
  all eligible recurrence edges complete: true
```

The U300 control gives the same reading:

```text
Pascal additive triangle:
  total interior recurrence cases: 105
  eligible by stage:                77
  eligible complete:                77

20 random positive additive triangles:
  all eligible recurrence edges complete: true
```

Therefore local recurrence edges are useful only as a witness layer. They are
not an explanatory signal by themselves.

The same caution applies to:

```text
value presence
row-like lists
diagonal finite differences
raw derivation counts
generic + edge completion
```

Every positive integer appears as `C(n,1) = n`, so value overlap is nearly
vacuous.

## What Survives

### 1. Aperture Laws

Pascal recurrence misses are aperture-conditioned. At U1000, the first row-14
miss is:

```text
715 + 1287 -> 2002
candidate stage: 1287
corpus stage:    1000
```

This is not a structural miss. It says the relevant operand is not yet allowed
under strict-stage positive-spine operation.

That means the coefficient recurrence is still a useful aperture probe, but not
a Pascal-specific discovery.

### 2. Boolean Lattice Cover Structure

The subset-lattice lens is stronger than coefficient adjacency because it tests
rank counts, cover edges, and commuting diamonds.

For atom set `{2,3,5,7,11}` at U1000:

```text
subset nodes present: 32/32
cover relations:      80
complete covers:      79
diamonds:             80
complete diamonds:    76
```

The first missing cover is:

```text
1155 * 2 -> 2310
candidate stage: 1155
corpus stage:    1000
```

But controls show that binomial rank counts are still generic for independent
atom lattices.

At U300, among 4-prime atom sets with primes up to 31:

```text
stage-eligible thresholds:  7/330
first stage-eligible:       {2,3,5,7}, threshold 105
first stage-ineligible:     {2,3,5,23}, threshold 345
```

At U1000:

```text
stage-eligible 4-prime thresholds: 38/330
stage-eligible 5-prime thresholds:  0/462
first 5-prime threshold:            {2,3,5,7,11}, threshold 1155
```

These threshold controls evaluate stage aperture only. They do not call a
lattice completely visible without separately checking corpus retention and
the exact cover-edge witnesses.

So the Boolean lattice lens survives as ranked construction geometry and
aperture measurement. It does not by itself identify a unique Pascal branch.

### 3. Route Collision

The strongest surviving object is not ordinary Pascal adjacency. It is route
identity: non-equivalent construction certificates landing on the same node.
"Independent" is too strong unless the route cut, quotient, and dependency
rules are named.

The right-triangle cubic branch gives the clean example:

```text
(a,b,c,s,r) = k(3,4,5,6,1)
a^2 + b^2 = c^2
a^3 + b^3 + c^3 = s^3
Delta_3 = s^3 - (a^3+b^3+c^3) = s^2(5r-c)
```

Zero defect occurs exactly on the `3-4-5` similarity class among positive right
triangles.

At U1000, scale `k = 1` is fully visible:

```text
9 + 16 -> 25          stage 16
6 * 36 -> 216         stage 36
36 * 6 -> 216         stage 36
27 + 64 -> 91         stage 64
91 + 125 -> 216       stage 125
216 / 216 -> 1        stage 216
```

At scale `k = 2`, the side-cube sum is visible through:

```text
216 + 512 -> 728      stage 512
728 + 1000 -> 1728    stage 1000
```

but the ratio:

```text
1728 / 864 -> 2
```

is not yet visible, because it needs stage 1728.

The first route-identity control changes the earlier reading. These two named
geometric routes:

```text
cube surface route: 6 * s^2 -> 216
cube volume route:  s^2 * s -> 216
```

both substitute to the same multiplication orbit at `s=6`:

```text
6 * 36 -> 216       edges 4924, 5068
36 * 6 -> 216       the same two edges after commutative aggregation
AC expression:      *(6,6,6)
```

They are two external interpretations of one arithmetic certificate, not two
Modulus of One routes.

The surviving collision is narrower:

```text
cube route:         (6 * 6) * 6 -> 216
side-cube route:    3^3 + 4^3 + 5^3 -> 216
```

These are different associative/commutative expression certificates at the
declared leaf cut. The side-cube certificate is fully visible at stage `125`;
the cube certificate is visible at stage `36`. They remain theorem-linked and
share the positive-spine root, so the correct status is structural convergence
at a declared cut, not proven semantic or statistical independence.

The Pascal connection is not that `3,4,5,6` resemble row entries. Exponent
lifts are governed by binomial and multinomial grammar, but a value-side
`(3+3)^3` expansion certificate is algebraically dependent on the direct cube.
It is a useful route-quotient calibration, not evidence for a distinctive
Pascal sub-branch.

That makes the next target:

```text
frozen exponent-expansion certificate
  versus graph-distinct construction certificate
  with exact same result node
  plus AC quotient, dependency flags, and defect controls
```

## Assessment Rule

A Pascal/MoO claim should now pass this checklist:

```text
1. exact nodes:
   every operand/result exists as a strict node, with confirmed stage reported

2. exact edges:
   expected op, exact left/right/result node ids, directed edge count, edge stage

3. aperture:
   candidate stage is named; misses beyond the corpus stage are not failures

4. controls:
   additive recurrence is compared against non-Pascal additive triangles
   rank counts are compared against other binomial/Boolean posets

5. route identity:
   certificates remain different after commutative and associative quotients
   semantic labels alone do not establish another route
   shared steps, leaf cuts, and declared algebraic dependencies are reported

6. defect:
   if equality is special, report the defect on nearby controls, not only the hit
```

## Next Tests

1. Apply the completed route-identity machinery to Pascal coefficients:

```text
C(n,k) versus random integers matched by value range and first-stage window
features: incoming op signature, exact + parents, multiplication parents,
          shared operand neighborhoods, confirmation lag
```

2. Add a Pascal-Bratteli projection report:

```text
for each (n,k):
  theoretical path count C(n,k)
  local Modulus of One recurrence edge status
  residue/carry class
  parent confirmation status
  control cohort
```

3. Generalize the calibrated cubic value-side certificate to frozen
   multinomial lift probes:

```text
(x+y)^3, (x+y+z)^3, and higher exponent expansion routes
compare expansion-route nodes against geometry-route nodes
record route collisions and defects
```

4. Add ranked-poset controls:

```text
prime atom lattices
composite coprime atom lattices
random additive triangles
shuffled Pascal adjacency
other binomial posets
```

5. Keep the right-triangle cubic branch separate from Pascal. The current
value-side binomial certificate demonstrates a dependent rewrite; it does not
make the cubic closure Pascal-specific. Promotion would require frozen
expansion schemas and controls against generic polynomial identities.

## References

- Pascal graph / Pascal adic construction: `https://petersen.web.unc.edu/wp-content/uploads/sites/17054/2018/04/part1.pdf`
- Graph-based construction interpretation of binomial coefficients:
  `https://cs.uwaterloo.ca/journals/JIS/VOL26/Talman/talman2.pdf`
- Pascal triangle as branching graph / central measures:
  `https://lpetrov.cc/art2022/`
- Lucas theorem and mod-prime digit structure:
  `https://ericrowland.github.io/papers/Lucas%27_theorem_modulo_p%5E2.pdf`
- Kummer carry interpretation:
  `https://en.wikipedia.org/wiki/Kummer%27s_theorem`
