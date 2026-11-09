# Gauss Quadratic Forms Through Modulus One: Analysis

> Experiment ID: `gauss_quadratic_forms_d20_u300_v1`
>
> Artifact: `gauss_quadratic_forms_d20_u300_v1.json`
>
> Artifact SHA-256:
> `8089755E39D20BDE3AEF409F8EBC6EED8624A2142E52DE3BEC8CFA0C85BFE296`

## Outcome

The run passed every fixed integrity check and produced a clean negative result
for bare modulus-one structure.

Gauss determinant `d_G=-5`—modern discriminant `Delta=-20`—has two positive
properly primitive classes, exact nontrivial composition, and hundreds of
distinct bounded representation witnesses. After evaluation and reduction
modulo one, all of them occupy the sole residue zero. The class transition is
recoverable only from retained provenance.

```text
552 raw D=-20 witnesses
-> 276 proper-automorphism orbits
-> 113 represented integers
-> 1 residue.
```

The disciplined verdict is therefore:

```text
Gauss composition survives over modulus one as decorated fibre data.
It does not survive as nontrivial arithmetic inside Z/1Z.
```

## Corpus And Stage Integrity

The report read
`out/experiments/pascal_edge_probe_u300.sqlite` with corpus alignment status
`pass`, but censored all graph evidence to stage 200. All 200 requested positive
integer nodes were present by that cutoff. No later `U=300` node or edge was
needed.

The report hashes agree with the design freeze:

```text
corpus SHA-256  3d23228ea2a1926918d49bbdc89d9f7bf85ecfe4729ec96c7bd6e9f97e54b097
tool SHA-256    75f80ed39d14c962535d1a83a93b313236bd2e7153ed4a1c4581367d73f7c306
```

## Complete Representation Shadows

All 1,184 signed witnesses across the one-class and two-class families have a
complete exact arithmetic DAG and coordinate-side scalar-relation ledger in the
`U=200` prefix. The report retains 4,540 relation-role occurrences over 378
distinct ordered relation IDs, 295 commutative-normalized keys, and 514 unique
directed graph edge IDs. The latest required relation occurs at stage 196.

| form | represented integers | raw witnesses | proper orbits | arithmetic occurrences | coordinate occurrences | distinct relation union | latest stage | missing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `x^2+y^2` | 79 | 632 | 158 | 1,784 | 0 | 158 | 196 | 0 |
| `A=x^2+5y^2` | 57 | 280 | 140 | 1,012 | 0 | 80 | 180 | 0 |
| `B=2x^2+2xy+3y^2` | 56 | 272 | 136 | 1,508 | 236 | 258 | 181 | 0 |

For `B`, the positive arithmetic DAG uses
`x^2+(x+y)^2+2y^2`. Its 236 coordinate-rewrite roles include 16 instances of
`|x|-|y| -> 0` for `x=-y`, across eight distinct magnitudes. Those edges retain
relational-zero evidence, but zero is never used as an operand. The complete
coordinate partition is 82 same-sign additions, 138 positive subtractions, 16
cancellations to zero, and 36 zero-coordinate aliases needing no edge. The
eight zero-result edges all have confirmed operands; zero is speculative at
each edge and remains non-operational.

This is attachment calibration, not selection. The strict positive spine is
saturated with the relevant exact in-range operations on confirmed operands.
The graph does not independently choose these three forms.

## Exact Composition Ledger

All 961 normalized composition events satisfy their polynomial identity and
land in the correct target proper-automorphism orbit:

| class transition | normalized events |
|---|---:|
| `A*A -> A` | 271 |
| `A*B -> B` | 466 |
| `B*B -> A` | 224 |

The unnormalized accounting contains 7,612 ordered signed-witness events:

```text
A*A -> A    2,128
A*B -> B    1,864
B*A -> B    1,864
B*B -> A    1,756
```

The normalized ledger uses 345 distinct commutative scalar multiplication
relations backed by 678 directed graph edge occurrences. Every relation is
usable by stage 200: it is present and its operands are confirmed at the edge.
Identity failures, target-fibre failures, and unusable scalar relations are all
zero.

## The Smallest Inspectable Transition

The central witness is

```text
B(1,0)=2
B(0,1)=3
B*B -> A
A(1,1)=6
2*3=6.
```

The strict corpus contains two directed occurrences of `2*3 -> 6`, both at
stage 3. Operands 2 and 3 are confirmed at those edges; result 6 is speculative
at the edge and becomes a positive-spine ground value later. The report does not
operate on 6 before promotion.

Modulo one, this entire scalar transition is only

```text
0*0=0.
```

The labels `B`, `B`, and `A`, the source coordinates, and the bilinear map
remain inspectable solely because the report carries them as decorations.

## Controls

- **Constant bucket:** passed. Replacing every represented integer by one
  arbitrary token gives the same bare topology as reduction modulo one.
- **One class versus two classes:** passed. `Delta=-4` and `Delta=-20` have
  identical bare quotient topology despite different decorated class data.
- **Stage prefix:** passed. The effective cutoff is exactly 200.
- **Automorphism normalization:** passed. Every raw representation fibre is
  partitioned exactly, and normalized coefficients equal orbit counts.
- **Composition closure:** passed. Every output orbit is in the configured
  target-form fibre.
- **Saturation:** behaved as expected. Complete graph-edge coverage is treated
  as calibration and earns no form-selectivity claim.
- **Character-phase separation:** passed by construction. The auxiliary
  `1/2 in Q/Z` sign-character label is never used as an integer residue modulo
  one.
- **Erasure boundary:** the graph database is read-only and contains no form or
  class fields. Removing the external labels therefore leaves its node and edge
  evidence unchanged.
- **Operator signature:** explicit. The bare quotient reports the total ring
  operations `+`, `-`, and `*`; division is excluded because `0/0` is undefined
  and does not descend to a total operation on `Z/1Z`.

## What Matured

The useful object is not a “quadratic form over modulus one.” It is a decorated
fibre of the evaluation map above a singleton quotient. Gauss's work supplies a
principled provenance algebra for that fibre:

```text
proper equivalence
-> reduced class
-> exact bilinear composition
-> class-character channel.
```

Modulus one then supplies an unusually severe erasure test. It shows exactly
which parts are intrinsic to the scalar quotient—none beyond the singleton—and
which parts require a retained lift.

This also clarifies the character transform. The nontrivial `C2` character is
genuine class information, but its phase label `1/2 in Q/Z` belongs to the
auxiliary character representation. It cannot be smuggled into `Z/1Z` to make
the quotient look two-pointed.

## Limits And Next Experiment

The run is finite and external. It does not install quadratic forms or class
groups as runtime objects, prove an Euler product, evaluate an Epstein zeta
function, or support an RH claim.

The best next control is modern discriminant `-23`. Its two inverse
nonprincipal proper classes represent the same scalar set. That case would
force an even sharper distinction: a scalar-only graph cannot tell the inverse
classes apart, so any claimed difference must be carried by orientation or
composition provenance and must disappear when those decorations are stripped.

## Verification Record

```text
quadratic-form focused tests: 15/15 passed
Python compilation over repository scripts: passed
in-memory/SQLite core alignment through U=6: passed
full unittest discovery: 100 passed, 2 unrelated errors
```

The two full-suite errors are outside this work: `test_moo_circle_square_probe`
imports a missing `circle_square_alignment_summary`, and
`test_primitive_euclid_branch_sweep` expects a missing summary key
`branch_count`. The quadratic-form tests and artifact checks are clean.
