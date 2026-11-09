# Modulus of One

**Modulus of One began with a failed attempt to count to two.**

That attempt grew out of an earlier inquiry into squaring the circle and,
more broadly, finding areas under curves. Asking what justifies a construction
led back to the apparently simple act of counting.

The philosophical starting thought is *cogito ergo unum* — “I think, therefore
one.” Here, `1` names an immediate certainty. Using it again requires
remembering an earlier occurrence,
identifying it, and admitting recurrence. Descartes' demon expresses the
problem: memory cannot simply inherit the certainty of the immediate `1`.
The arithmetic of `1 + 1 = 2` works once those commitments are admitted; it
does not establish their certainty.

Modulus of One continues by investigating what unfolds under admitted
construction rules. Its central method is **branch inspection**: follow repeated relationships,
examine where they agree or differ, and use what they reveal to guide further
construction and interpretation. Irrational, transcendental and infinitesimal
forms can be proposed through that inspection without being attained as
completed objects.

## From One To A Field Of Relations

With **each iteration of `1`, all four fundamental operations apply across
every available ordered pair, including self-pairs**. The first *operator fan*
already gives:

```text
1 + 1 -> 2    expansion
1 - 1 -> 0    cancellation
1 * 1 -> 1    preservation through self-product
1 / 1 -> 1    preservation through self-ratio
```

Counting is one branch within this continuing field of relations. Modulus of One
organizes their dependence on the starting certainty into four epistemic orders:

| Order | What supports it |
| --- | --- |
| **First** | The immediate certainty: “I think, therefore one.” |
| **Second** | Admitted memory and recurrence of `1`; counted multiples depend on this commitment. |
| **Third** | Relations among those iterations, including fractions and multiplicative constructions. |
| **Fourth** | Hypothetical points or forms proposed through inspection of the earlier orders. |

Exact arithmetic preserves those dependencies. A whole number can appear
through a third-order relation and later gain second-order support through
counting; its earlier witnesses remain. Infinitesimals and transcendentals
share fourth-order epistemic standing, while remaining mathematically different.
A conditional proof can support an interpretation without granting its
assumptions first-order certainty.

The current executable model follows the **positive counting spine**. At
stage `U_n`, confirmed multiples `1..n` may be operands; other outputs are
recorded for inspection and can be reused only if counting later confirms
them. The full signed operator-fan field is broader. Equal rational results
share a node, with distinct local operation witnesses retained around it.

## What A Branch Lets Us Inspect

A branch is a repeated witnessed relation within the unfolding field.
Self-addition gives `n -> n+n`; self-multiplication gives `n -> n*n`.
Inspection selects such relationships from the full field and asks what
happens when they interact.

Consider three self-products and an addition:

```text
3 * 3 -> 9
4 * 4 -> 16
5 * 5 -> 25
9 + 16 -> 25
```

The addition and the third square agree at one value node. Repeating this
pattern identifies a **shell relation**: two squares add to a third.
Inspecting the surrounding products and ratios gives another way to recognize
and extend it:

```text
5 - 3 -> 2       5 + 3 -> 8
2 * 8 -> 16
2 / 4 -> 1/2     4 / 8 -> 1/2
```

The two ratios agree because the product `2*8` is the square `4*4`.
In general, a shell `x*x + y*y = r*r` gives
`(r-x)/y = y/(r+x)`. That repeated ratio supplies a parameter for finding
further shells. Between the parameters `1/2` for `(3,4,5)` and `2/3` for
`(5,12,13)`, the ratio `3/5` generates `(8,15,17)` exactly.

**Inspection has turned an agreement between branches into a way to make
further constructions.** The algebra is classical; its use here is to extract
a relation, establish why it continues, and return its instances to witnessed
construction. The [worked branch inspection](docs/examples/BRANCH_INSPECTION.md)
shows that argument, the graph witnesses, and the geometric interpretation.

## Growth, Refinement And Proposed Limits

The square relation also connects these inspected root/result values:

```text
2   -> 4   -> 16   -> 256   -> ...
1/2 -> 1/4 -> 1/16 -> 1/256 -> ...
```

The first grows without bound under continuation; the second remains positive
at every finite step and becomes arbitrarily small. The fractional relations
use integer-encoded certificates: the current runtime never squares a
speculative fraction as an operand. These comparisons provide a concrete
setting for investigating unbounded continuation and infinitesimal proposals.
The finite relations are established; an infinitesimal interpretation remains
an open fourth-order question.

A different comparison leads toward an irrational form. Compare a square with
twice another square, selecting cases whose difference is exactly one:

| Roots `(n,m)` | Square comparison | Relative difference |
| --- | --- | --- |
| `(1,1)` | `1 - 2 = -1` | `-1` |
| `(3,2)` | `9 - 8 = 1` | `1/4` |
| `(7,5)` | `49 - 50 = -1` | `-1/25` |

The recurrence `(n,m) -> (n+2m,n+m)` reverses the sign of that difference
and increases the scale. The raw gap stays one; relative to `m*m`, it shrinks.
No nonzero rational roots give exact agreement. Under ordinary real
completion, the ratios `n/m` approach the positive form conventionally named
`sqrt(2)`. The [square-comparison study](docs/examples/FOURTH_ORDER_EXAMPLE.md)
explains the conditional argument and its finite witnesses.

Here the proposed form organizes an enduring relationship between
constructions. No numerical value of `sqrt(2)` was needed to select them,
and naming the form supplies no new runtime operand.

## Squaring The Circle And Inspecting Area

The circle investigation returns to the original area question. Given a disk,
which square constructions have less area, which have more, and what would
justify an equal-area interpretation? Explicitly admit a Euclidean unit disk
and an area rule. Rational polygons give inner and outer area bounds: first
`2` and `4`, then `14/5` and `10/3`. Refinement makes their separation
arbitrarily small.

Now inspect rational-square constructions against those bounds. A square
below a lower bound is definitely below the area; one above an upper bound
is definitely above it. Further refinement settles more comparisons. The
research compared polygon and grid methods, preserving their different
witnesses while proving that valid shrinking bounds eventually classify every
square value unequal to the area on the same side.

This also guides the construction of closer square-side brackets. The
existing study certifies side `7/4` as too small, `16/9` as too large, then
`23/13` as too small and `39/22` as too large. An unresolved comparison calls
for finer area bounds. The investigation advances through certified relations
between constructions.

This defines a separation within the ordered square-branch values. Under the
stated geometric interpretation, its proposed common boundary is `pi`; the
corresponding boundary in square **roots** is `sqrt(pi)`. Modulus of One can
investigate that boundary through finite comparisons while retaining it as a hypothetical
fourth-order form. The [pi account](docs/examples/PI_FOURTH_ORDER_EXAMPLE.md)
shows the constructions and assumptions. Classical identification and
transcendence belong to the interpretation; the finite bounds alone do not
prove them.

The grid inspection makes the connection to **area under a curve** explicit:
columns of rational cells lie below the first-quadrant arc or cover the region
under it. Their finite area sums bound the quarter-disk area; refinement
shrinks the gap. The broader question is how to find and justify such enclosing
constructions for other curves. The worked circle case illustrates that
inquiry, while an exact finite circle-squaring construction has not been
obtained.

## Using An Insight To Construct Something Better

The spiral research gives another use for branch inspection. In an explicit
geometric interpretation of ordered pairs, repeated multiplication of a
chosen seed traces a logarithmic spiral. Squaring and normalizing that seed
gives a rational unit direction whose powers supply further directions. The
subsequent unit-distance investigation combines families from two seeds,
builds points by adding selected directions, and counts pairs of points exactly
one unit apart.

Adding or removing one selected direction from a sum already gives such a
pair. Inspection revealed something more: a signed combination of several
directions also gives a unit displacement. That displacement belongs to the
multiplication family, but lies beyond the depth from which the directions
were selected. Its exact relation explained eight extra unit pairs and showed
why different selections would meet at the same point in a later extension. Following the relation
guided a changed selection:
**1,020 points with 5,188 unit pairs**, improving the original example's
**1,024 points with 5,128 pairs**.

The [research trail](research/geometry/erdos_unit_distance/RELATION_GEOMETRY_NOTE.md)
records the exact comparisons. This is a finite improvement within a classical
geometric interpretation. A related argument bounds how quickly the unit-pair
count can grow as the original fixed-seed family expands. Inspection can
suggest a productive change and establish limits on what continuing a route
can achieve.

## Explore The Work

Modulus of One remains an open philosophical and mathematical inquiry. Branches make
its construction field investigable; their interactions support arguments,
counterexamples, new constructions and proposed forms. The witnesses keep
those interpretations answerable to the relationships that motivated them.

- [Worked branch inspection](docs/examples/BRANCH_INSPECTION.md): from a
  square/sum agreement to a ratio and further shell constructions.
- [Philosophical notes](docs/PHILOSOPHY.md): certainty, recurrence, branch
  inspection and the warrant for interpretation.
- [Supporting research](research/README.md): investigations, evidence,
  negative findings and open questions.
- [Documentation guide](docs/README.md): definitions, software and history.

For a small executable introduction to the operand and witness rules, the
[runtime walkthrough following `16`](docs/examples/WORKED_INSPECTION.md) runs
with `python3 tools/moo_walkthrough.py`, using only the Python standard library.

By **GNARGNARHEAD**. [Citation metadata](CITATION.cff).

Code is licensed under [MIT](LICENSE-MIT); writing, figures, and research
reports under [CC BY 4.0](LICENSE-CC-BY-4.0). See the
[license scope](LICENSE.md) for details.

This public snapshot has fresh history and privacy-redacted research copies.
See [snapshot provenance](docs/PUBLIC_RELEASE.md) for the scope and evidence identities.
