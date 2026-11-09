# Worked Branch Inspection: From An Agreement To Further Constructions

The [main account](../../README.md) introduces branches as repeated witnessed
relations in the field generated from admitted recurrence of `1`. This example
follows an investigation: an agreement between squares and addition exposes a
ratio; that ratio gives a way to find further agreements.

It draws on the existing [shell/ratio study](../../research/geometry/SHELL_SQUARE_RATIO_BRANCH_NOTE.md).
The algebra is classical, the graph witnesses are finite, and the geometric
reading is explicit. The point is to show what inspecting branches enables.

## Begin With A Shared Result

The square branch relates a source to its self-product. Consider these
constructions within the full four-operation field:

```text
3 * 3 -> 9
4 * 4 -> 16
5 * 5 -> 25
9 + 16 -> 25
```

Two squares combine through addition to agree with a third square. The
repeated pattern is the shell relation `x*x + y*y = r*r`. Its witnesses
identify which self-products and addition agree at a common value node.

At positive-spine stage `U16`, all four displayed edges are available in an
unfiltered field. The products appear earlier, but `9` and `16` must be
confirmed before they can supply the addition. Confirmation permits a use;
the agreement between the witnessed relations is what we investigate.

## Inspect The Surrounding Relations

The same sources also give:

```text
5 - 3 -> 2       5 + 3 -> 8
2 * 8 -> 16     4 * 4 -> 16
2 / 4 -> 1/2    4 / 8 -> 1/2
```

An unequal product meets the square at `16`. Two divisions meet at `1/2`.
These are related observations. With `u = r-x` and `v = r+x`, ordinary
algebra gives

```text
x*x + y*y = r*r
        implies u*v = y*y
        implies u/y = y/v = t.
```

Conversely, the factor agreement restores the shell equality. For positive
sources, the ratio agreement and factor agreement are equivalent as algebraic
statements. Their particular graph edges remain different witnesses: one
missing edge is not supplied merely by knowing the equivalent identity.

The numerical value `1/2` appeared through `1/2` at `U2`. This inspection
learns something additional about it: a particular pair of division witnesses
expresses the relationship between a square and its surrounding factors.
That pattern is complete at `U8`; the direct square/addition agreement above
waits until `U16`. These are checkpoints for named sets of witnesses, not
minimum costs over every possible argument.

## Use The Ratio To Fill A Gap

Normalize a shell by its radius: `X=x/r`, `Y=y/r`. Solving the ratio relation
gives the external parametrization

```text
X = (1-t*t)/(1+t*t)
Y = 2*t/(1+t*t).
```

Substitution proves `X*X + Y*Y = 1`. For a rational parameter `t=p/q` with
positive integers `0 < p < q`, the integer triple

```text
(q*q - p*p, 2*p*q, q*q + p*p)
```

therefore satisfies the shell relation. Remove a common integer factor to
obtain its primitive representative. The parameter is used to select integer
construction requests; it is not promoted to a runtime operand.

Two known cases have parameters `1/2` and `2/3`. Adding their numerators and
denominators gives the mediant `3/5`, strictly between them:

| Parameter | Integer triple from the formula | Primitive shell |
| --- | --- | --- |
| `1/2` | `(3,4,5)` | `(3,4,5)` |
| `3/5` | `(16,30,34)` | `(8,15,17)` |
| `2/3` | `(5,12,13)` | `(5,12,13)` |

The intervening shell has its own factor and ratio witnesses:

```text
17 - 8 -> 9       17 + 8 -> 25
9 * 25 -> 225    15 * 15 -> 225
9 / 15 -> 3/5    15 / 25 -> 3/5
```

Those relations are all witnessed by `U25` in a sufficiently wide field.
The direct sum `64 + 225 -> 289` requires `U225`. The candidate-generation
formula and these witness checkpoints are separate: the checkpoint says
which requested edges coexist, not which ancestral proof supplied every
operand use.

**The useful inference is a constructive selector.** A ratio extracted from
an interaction between branches now supplies further cases, with an exact
reason why they satisfy the relation. Subdivision can continue in parameter
space. Simply averaging the normalized coordinates of two shell points would
generally leave the shell; knowing the parameter changes how we search.

## What The Geometric Reading Adds

With the ordinary Euclidean metric, `(X,Y)` is a rational unit-circle position.
The shell relation and its parameter precede that interpretation. Ordered
shell composition adds another question: which compositions preserve the
agreement, and which distinctions survive normalization? The
[composition study](../../research/geometry/SHELL_COMPOSITION_BRANCH_NOTE.md)
retains signs, order and witnesses while developing those arguments.

Admitting a disk and an area rule then permits comparisons between rational
square constructions and shrinking area bounds. The
[pi example](PI_FOURTH_ORDER_EXAMPLE.md) follows that passage to a proposed
boundary. The [square-comparison example](FOURTH_ORDER_EXAMPLE.md) illustrates
a simpler irrational boundary through repeated near-agreement.

Branch inspection also feeds further construction. The related
[spiral and unit-direction investigation](../../research/geometry/erdos_unit_distance/FIXED_SEED_BRANCH_GATE_NOTE.md#where-the-earlier-logarithmic-spiral-fits)
examines repeated pair products and their normalized directions. An
[additive/multiplicative interaction](../../research/geometry/erdos_unit_distance/RELATION_GEOMETRY_NOTE.md)
then guides a finite improvement in the number of unit-distance pairs. This
research adds its geometric framework explicitly; its proposed forms never
become confirmed scalar Modulus of One operands.

## Inspect A Fresh Field

The following commands need only Python's standard library. From the
repository root, choose an unused database path:

```sh
python3 -m moo.strict_stage_moo \
  --db out/scratch/branch_inspection_v1.sqlite \
  --max-stage 32 --max-abs-p 1024 --max-abs-q 32 \
  --max-abs-value 1024 --quiet

python3 -m moo.graph_query \
  --db out/scratch/branch_inspection_v1.sqlite \
  --node 225 --limit 32 --pretty

python3 -m moo.graph_query \
  --db out/scratch/branch_inspection_v1.sqlite \
  --node 3/5 --limit 32 --pretty
```

Every four-operation result from operands `1..32` fits those bounds. Inspect
`225` for both `15*15` and `9*25`; inspect `3/5` for `9/15` and `15/25`
among its scaled division witnesses. The field also contains the earlier
`(3,4,5)` example. It is too small for the direct `64+225` addition, whose
absence has a known operand-readiness explanation.

This generates a fresh field and fresh edge IDs. The original study's
[report](../../research/geometry/results/2026-09-11-shell-square-branch-v1.json)
retains its own observations, controls and source identities; its historical
inputs are accounted for in the
[corpus inventory](../../research/experiments/CORPUS_INVENTORY.md).
The [runtime walkthrough](WORKED_INSPECTION.md) explains confirmation and
retention in more detail.
