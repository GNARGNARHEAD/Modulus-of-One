# A ratio branch for rational shell / square searches

Date: 2026-09-11

Evidence layers: external exact parametrization; retained strict graph motifs.
Claim status: bounded observation and an operational candidate selector.

For the provisional shell relation, there is an exact one-parameter search
family after normalization. It can generate points between known hits. The
same parameter occurs as two agreeing division witnesses in the preserved Modulus of One
graphs. Its algebra is classical; this experiment establishes its retained
construction context and measures an earlier certificate under the current
positive-spine rule.

The starting hit is x*x + y*y = r*r, with positive integers x <= y. This is
the shell proxy agreed for the investigation. No circle-area relation has
been introduced or tested.

## The repeated relationship

Set u = r-x and v = r+x. Then the shell identity is equivalent to

```text
u*v = y*y

u/y = y/v = t
```

The graph motif has several independent witnesses:

```text
x*x, y*y, r*r       three retained self-product edges
r-x -> u           a subtraction edge
r+x -> v           an addition edge
u*v -> y*y         a second construction of the y-square node
u/y -> t           one construction of the ratio node
y/v -> t           another construction of the same ratio node
```

The factor motif and quotient motif are reported separately. They need not
have the same retained status in an arbitrary bounded or damaged corpus.
Neither is silently substituted for the direct x*x + y*y -> r*r edge.

The parameter node itself can appear much earlier by another route. For
example, 3/5 is already an output at U5; the (8,15,17) factor/quotient motif
completes at U25. The branch evidence is the specified construction context,
not merely finding the value 3/5 in the graph.

This is a repeated witnessed relation in the named strict fields. Its graph
specificity is limited: sufficiently wide exhaustive arithmetic generation
predicts the motif. It is not a new law beyond that arithmetic.

## Why one parameter suffices

Write X=x/r and Y=y/r. These are scale-free coordinates. From t=y/(r+x),
or equivalently t=(r-x)/y, we obtain

```text
X = (1-t*t)/(1+t*t)
Y = 2*t/(1+t*t)
```

Conversely, these expressions satisfy X*X + Y*Y = 1 exactly. For a rational
shell, t is rational; for rational t, X and Y are rational. Therefore the
parameter covers all positive rational normalized shell points, up to the
chosen leg orientation. Using 0 < t < 1 covers the first quadrant with
orientation; sorting the legs identifies exchanged copies. In the sorted
x <= y convention, the canonical parameters satisfy sqrt(2)-1 <= t < 1,
with no rational equality at the lower endpoint.

For t=p/q in lowest terms, a primitive integer representative is obtained
from (q*q-p*p, 2*p*q, q*q+p*p) by dividing out its common divisor and sorting
the legs. This is an external selector. It does not operate on the graph's
speculative fraction node.

Scale remains a separate parameter for unnormalized triples. All positive
rational shells can be cleared to integer triples and reduced to primitive
representatives, but the corresponding fractional self-product operations
are not permitted in the current strict runtime. The general rational
statement is external algebra; the machine audit below is integer-scoped.

This rational parametrization and the difference-of-squares proof are
classical. See Keith Conrad, [Pythagorean Triples, sections 2 and 3](https://kconrad.math.uconn.edu/blurbs/ugradnumthy/pythagtriple.pdf).

## Filling a gap exactly

Two known positions are t=1/2 for (3,4,5), and t=2/3 for (5,12,13). Their
mediant is (1+2)/(2+3)=3/5. It lies strictly between them and gives (8,15,17).

Continuing the two gaps gives:

| Parameter | Primitive shell | Factor/ratio motif first complete | Direct square/addition first complete |
| --- | --- | ---: | ---: |
| 1/2 | 3,4,5 | U8, observed | U16, observed |
| 4/7 | 33,56,65 | U98, observed | U3136, predicted, outside saved apertures |
| 3/5 | 8,15,17 | U25, observed | U225, observed |
| 5/8 | 39,80,89 | U128, observed | U6400, predicted, outside saved apertures |
| 2/3 | 5,12,13 | U18, observed | U144, observed |

Every finite positive rational parameter in this interval supplies an exact
rational shell. Interpolating t is therefore justified by the inverse map.
Linear interpolation of the normalized coordinates X,Y would generally
leave the shell. Midpoints in parameter space and stage order also differ:
a point between two ratios can require a larger radius and later witnesses.

Repeated subdivision creates more candidates in a chosen interval. It is a
local search strategy, not a claim that this one subdivision scheme visits
every rational parameter. Exhaustive rational enumeration or the complete
primitive tree supplies a coverage guarantee.

## Graph audit

The [frozen design](SHELL_SQUARE_BRANCH_SEARCH_20260911.pre.md) was written
before scanning this predicate against the four saved corpora. The
[read-only tool](../../moo/shell_branch_search.py) records exact node records,
edge IDs, stages, status at the observed stage, missing-edge reasons, controls,
and source hashes in the [full machine report](results/2026-09-11-shell-square-branch-v1.json).
The [compact report](results/2026-09-11-shell-square-branch-summary-v1.json)
contains the summary and selected complete witness records.

The fixed envelope r <= 500 contains 386 positive integer triples with sorted
legs and 80 primitive shapes. A blind pair sweep, square-factor enumeration,
Euclid generation, and a primitive Berggren tree agreed exactly within the
envelope. Primitive parameters also passed exact inverse-map checks.

| Preserved corpus | Direct shell motifs | Factor motifs | Quotient motifs | Primitive shapes with factor motifs |
| --- | ---: | ---: | ---: | ---: |
| Wide U300 | 6 | 138 | 138 | 37 |
| Wide U850 | 12 | 386 | 386 | 80 |
| Wide U1000 | 13 | 386 | 386 | 80 |
| Narrow U80, retention control | 0 | 0 | 0 | 0 |

The U850 aperture adds 248 factor/quotient cases, including 43 new primitive
shapes, beyond the U300 completion window. U1000 adds one direct motif and
no new factor cases within this radius cap. All factor motifs in the envelope
complete by U833.

These apertures are nested and were used by earlier research; they are not
independent random samples. The present predicates and timing predictions
were fixed before this scan. Complete, partial, and absent rows are retained.

An additional scan begins at saved self-product outputs and searches their
incoming edges for unequal product operands. After the parity and radius
filters, it recovers exactly the same complete factor candidates: 138 at
U300 and 386 at U850/U1000. It receives no shell-triple list in its query.
Thus the candidate region can be found from construction collisions, not
only by looking up externally supplied triples.

For each hit with r+1 <= 500, the neighboring nonhit (x,y,r+1) was also
audited: 383 controls per corpus, zero false positives for the joint direct,
factor, or quotient predicates. These are deterministic algebra controls,
not a statistical significance test or evidence for an unexplained effect.

## Why the earlier certificate helps

In the selected strict positive-spine frame, an ordered pair of confirmed
positive integers first participates when the larger operand is reached.
With sufficient retention, the direct motif therefore completes at U_(y*y).
The factor and quotient motifs complete at U_(r+x).

For (8,15,17), the squared-value sum waits for operand 225 to be confirmed.
The factor route uses 9*25 -> 225, whose operands are ready at U25. Both
routes are real graph constructions, but they have different readiness costs.

All measured completion stages in the wide corpora matched these fixed
operand-size predictions: zero mismatches. The result is a useful earlier
certificate, fully explained by known arithmetic and the positive-spine
rule. There is no residual timing law established by this experiment.

The narrow U80 control fails the naive stage-only prediction because output
retention excludes the necessary self-product edges. It has one
square-node-complete case but no complete direct motif. This confirms why
the older value-presence reports could not resolve the witness question.

## Search reduction and rejected narrower guesses

The blind scan tested 124,750 leg pairs. The Euclid selector inspected 231
parameter pairs and generated exactly 386 scaled results from 80 primitive
shapes. These are loop/candidate counts for the implementations in this
experiment, not a wall-clock speedup claim. The square-factor implementation
uses trial division and is an independent coverage check, not a faster
algorithm as written.

The primitive family has a known three-child recursive organization. The
implemented Berggren tree reproduced all 80 primitive shapes; repeatedly
following only its A child produced 15. A single selected recursion chain
therefore does not cover this family. The matrices are external candidate
generation, not individually audited Modulus of One construction paths. See
[Janickova and Csokasi, Metric properties in Berggren tree of primitive Pythagorean triples](https://arxiv.org/abs/2304.05230).

A prime-only radius branch is also too narrow. For example (7,24,25) is
primitive, has a composite radius, and has factor/quotient witnesses at U32
and a direct witness at U576. At U850, 36 of the 80 primitive shapes have
composite radii. This does not test or reject more general prime-factor
organization of the family.

No common logarithmic-spiral rule was established or needed. The exact
selector found here is the rational parameter line and its recursive
enumeration, with scale handled separately.

## Concrete witness example and reproduction

In the preserved U850 corpus, the (8,15,17) case has:

```text
8*8 -> 64        edge 228, U8
15*15 -> 225     edge 844, U15
17*17 -> 289     edge 1092, U17
17-8 -> 9        edge 1055, U17
17+8 -> 25       edge 1054, U17
9*25 -> 225      edge 2440, U25
9/15 -> 3/5      edge 881, U15
15/25 -> 3/5     edge 2465, U25
```

Each operand is confirmed at the saved edge stage. The shared outputs can
remain speculative; they are compared as nodes, never promoted by the probe.
The schema may store a future integer confirmation stage even when the
corpus has not reached it. The tool explicitly compares that stage with the
observed aperture instead of treating a non-null field as confirmation.

Inspect the squared-result neighborhood:

```powershell
python -m moo.graph_query --db out/experiments/gauss/strict_stage_u850_holdout_v1.sqlite --node 225 --neighborhood --pretty
```

Rerun to a new output filename:

```powershell
python -B -m moo.shell_branch_search --max-radius 500 --write research/geometry/results/2026-09-11-shell-square-branch-rerun.json
python -B -m unittest test_moo_shell_branch_search -v
```

The audit completed in about 48 seconds on this host, including four
read-only corpus scans and before/after input hashing. All four input hashes
matched the preserved corpus inventory and remained unchanged. Eight focused
stdlib tests passed, including absent witnesses, speculative outputs, wrong
confirmation, nearby nonhits, independent enumeration, and exact gap
predictions. The in-memory --limit 3 demo also passed its acceptance checks.
An independent readback checked 14,532 distinct retained edge records across
the four snapshots against their SQLite operands, results, confirmation
stages, and arithmetic. Tool, helper, and frozen-design hashes matched.

The retained outcome is an exact search family and graph-backed early
certificate for the chosen rational-shell proxy. Defining an independent
circle-area signature remains a separate question.

The [subsequent equal-area test](CIRCLE_SQUARE_AREA_BRIDGE_20260911.analysis.md)
constructs external polygon/grid area bounds and finds a certified
approximation path, with no exact finite rational equal-area hits. It does
not upgrade this shell family to a squaring-the-circle branch.
