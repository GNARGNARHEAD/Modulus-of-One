# Point-by-Point Critique — 6 November 2026

**Resolution:** all five findings below were subsequently corrected and
verified. See [the fix record](FIVE_FIXES_20261106.md) for current behavior,
regressions, and independent review. The examples below preserve the failures
observed before those fixes; source line numbers refer to that reviewed state.

GNARGNARHEAD requested an independent Astra review at extra-high reasoning, with
each assertion checked against the work. The reviewer used `gpt-6-astra` with
`xhigh` reasoning, examined fourteen claims in order, and reported them
incrementally. The primary reviewer checked the owning sources and independently
reproduced every defect accepted below. This is a review of the current working
tree, including the uncommitted editorial cleanup.

**Five reproducible defects were found in three software paths.** They concern
premature confirmation, a missed product witness, and arithmetic classification
being presented as witnessed branch membership. These are failures to implement
or report MoO's stated distinctions. This review found no demonstrated
contradiction in the central philosophical account under its stated assumptions.
That is a bounded review conclusion, not a proof of the philosophy or a novelty
assessment.

## The Fourteen Points, In Order

| # | Claim examined | Adjudicated result |
| --- | --- | --- |
| 1 | Immediate `1` is the starting certainty. | Supported as an explicitly adopted philosophical boundary. Neither the notes nor the code derive arithmetic cardinality from that naming. |
| 2 | Memory, recurrence, relations, and projected convergence motivate the orders. | The dependency argument is present. A criticism that this classification is not uniquely forced does not establish a flaw: the text makes no uniqueness claim and does not define order as instruction depth. |
| 3 | The first fan contains all four operations on `1`. | Supported by the exact arithmetic and generator. The notes explicitly admit operations and reuse rather than claiming to derive them from immediate certainty. |
| 4 | The full-operation rule continues with each iteration. | Supported over the current confirmed-positive operand field. The broader signed field still lacks a complete implemented confirmation schedule; this was already acknowledged. |
| 5 | Incremental first-availability storage retains the operation field. | Supported. Each ordered pair belongs to exactly one frontier `max(a,b)`, giving `4*N*N` arithmetic edges at unfiltered `U_N`. This stores first availability, not repeated temporal executions of the same pair. |
| 6 | Producing a value differs from confirming it. | The generator and walkthrough preserve this distinction. The query tool's `--confirmations` report violates it: finding F2. |
| 7 | Equal rational values share a node while local witnesses remain distinct. | Supported by canonicalization, the schema, and independent readback of the two `1/2` witnesses. |
| 8 | The graph preserves construction dependencies. | Supported for local value-node incidence and attached witnesses. It does not bind each operand role to a particular supplying witness; see the representational limit below. This stronger guarantee is not established as an intended requirement. |
| 9 | Aligned computation does not reuse unconfirmed relational results. | The positive-spine generator follows the rule. The public expression evaluator bypasses it by promoting integer results immediately: finding F1. |
| 10 | Later evidence can change an interpretation without erasing a witness. | Supported. At `U4`, only `4*4` reaches `16`; at `U8`, `8+8` is also present. The earlier bounded observation remains true. |
| 11 | Absence claims depend on complete frontiers and retention bounds. | Supported in the shared `GraphEvidence` contract and walkthrough control. This does not establish that every older analyzer uses that contract correctly. |
| 12 | Branch reports distinguish witnessed relations from ordinary value labels. | The governing notes require this distinction. The prime-lineage report violates it in three reproduced ways: findings F3–F5. |
| 13 | Finite rational evidence does not itself construct a completed non-rational limit. | The stated boundary and projection protocol preserve this distinction. A useful exact baseline for rational arrival and witness count is derived below. |
| 14 | Passing checks establish the behavior being presented. | The walkthrough establishes its finite examples. The existing tests and alignment checker do not cover all public-runtime or branch-report claims; their passes coexist with F1–F5. |

## Accepted Findings

### F1 — The Expression Evaluator Confirms Arithmetic Results Immediately

**Priority: high.** In [constructionist_math.py](../constructionist_math.py),
`eval_moo` routes every positive integer arithmetic result through
`promote_expression_integer` and `promote_core_iteration` (lines 1657–1678).
The latter changes status without verifying that counted recurrence reached
the integer. Its own contract says arithmetic alone does not confirm a result
(lines 612–627); [VISION.md](../VISION.md), section 5.2, says the same.

Independent reproduction in default aligned mode:

```python
from constructionist_math import eval_moo

g, result = eval_moo("((1+1)*(1+1))+1")
print(sorted(g.nodes_by_int))  # [1, 2, 4, 5]
print(result.status)          # G
```

The multiplication produces `4`, immediately promotes it, and reuses it to
produce `5`. There is no confirmed `3`. The result is reported as Order 2.
In contrast, a `Graph` whose frontier is explicitly advanced to `2` leaves
the result of `2*2` speculative. No documented exemption for expression mode
was found; `allow_speculative_operands` is false in this reproduction.

Correction criterion: expression evaluation must preserve the distinction
between arithmetic production and independently established recurrence.
Returning an unconfirmed result, rejecting its reuse, or explicitly advancing
the recurrence are different interface choices; silently promoting it does
not satisfy the stated rule.

### F2 — The Confirmation Query Reports Future Events As Completed

**Priority: medium.** In [moo_graph_query.py](../moo_graph_query.py),
`later_confirmed_nodes` (lines 301–319) checks only that a scheduled
`confirmed_stage` exists and follows first appearance. It never checks whether
the saved construction reached that threshold. The command's help promises
values that the spine has already confirmed, and its output key is
`later_confirmed`.

On a complete, freshly generated `U3` with bounds 100, it returns
`2, 3, 4, 5, 6, 9`. Only `2` and `3` have reached their confirmation stages.
It reports `speculative_for_stages=6` for `9`, although the construction stops
at three. That is a scheduled interval, not an elapsed observation.

Correction criterion: distinguish an observed confirmation from a future
threshold, using actual completed stage coverage. This is already required by
[the corpus contract](../GRAPH_CORPUS_NOTE.md), lines 95–99.

### F3 — The Prime Analyzer Also Treats A Schedule As A Spine Witness

**Priority: medium.** In [branch_lineage.py](../branch_lineage.py),
`prime_lineage_entry` (line 334) sets `counting_spine_witnessed` from a
non-null confirmation threshold alone.

On a complete fresh `U4` with bounds 1000, it reports both `5` and `12` as
`witnessed_through_counting_spine`. Their thresholds are `5` and `12`;
neither has been reached. Their relational appearances are real, but they
have not acquired the claimed second-order support in this saved field.

Correction criterion: gate the spine-witness reading on the reached stage,
separately from value presence and scheduled confirmation.

### F4 — One Missing Factor Pair Is Mistaken For An Absent Product Branch

**Priority: high.** `_factor_pair` in
[branch_lineage.py](../branch_lineage.py), lines 317–323, returns the first
nontrivial factor pair. `prime_lineage_entry` checks only that pair's edge,
then uses its absence to report that the product landing is unwitnessed
(lines 335–357).

At complete `U4`, the first pair for `12` is `2*6`; operand `6` is still
unconfirmed. The analyzer therefore reports
`product_landing_permitted_but_not_witnessed_in_field`. Direct SQL readback
finds both `4*3 -> 12` and `3*4 -> 12`, at stage 4, in the same database
(edge IDs 48 and 64 in this fresh run).

This is a false absence claim contradicted by stored evidence. One failed
route cannot establish that a whole relation family is unwitnessed.

Correction criterion: inspect all relevant retained nontrivial product
witnesses, or all eligible factor pairs, before reporting branch absence.
Keep the status of a selected factorization separate from the whole branch.

### F5 — An Absent Prime Is Reported As A Native Branch Member

**Priority: medium.** In the same `U4`, `11` has no value node. Nevertheless,
`prime_lineage_entry` labels it `prime_branch_member` and
`irreducibility_condition` because the arithmetic factor search found no
factor. The report has no `classification_basis` distinguishing that arithmetic
classification from a MoO witness.

The [branch card](../BRANCH_FORMALIZATION_NOTE.md), lines 334–352, requires a
counting-spine witness and explicitly rejects silently treating ordinary
primality as a MoO witness. Lines 185–208 require the classification basis to
distinguish graph evidence, generator inference, and arithmetic shortcuts.

Ordinary primality of `11` is not in dispute. The flaw is the report's claim
about membership in the witnessed construction under its own definition.

Correction criterion: retain useful arithmetic labels, but label their basis
and do not promote them to witnessed branch membership without the required
construction evidence.

## Limits That Were Not Accepted As Bugs

### Local Provenance Does Not Select A Supplying Witness

This pair of histories produces identical complete runtime exports:

```python
from constructionist_math import Graph

def history(reverse):
    g = Graph()
    one = g.get_or_create_ref(1)
    product = g.mul(one, one)
    ratio = g.div(one, one)
    g.add(ratio, product) if reverse else g.add(product, ratio)
    return g.to_jsonable()

assert history(False) == history(True)
```

Both earlier witnesses are retained, but `product` and `ratio` reference the
same value node. The later edge cannot say which prior witness supplied its
left or right role. This was independently reproduced.

The existing model deliberately uses shared value references with attached
local evidence. It is therefore not a demonstrated violation of its stated
identity rule. It is a real limit on stronger language about preserving every
derivation dependency. Witness-specific proof composition would require an
additional representation or certificate layer. Similarly, a node-level
Order-1 label on the shared value `1` is not a witness-level certification of
every construction returning to it.

### A Motivated Classification Need Not Be Uniquely Forced

The reviewer initially raised the fact that dependence on memory alone does
not uniquely select every order assignment. The primary reviewer rejected
this as a demonstrated flaw. MoO explicitly distinguishes recurrence support
from relations dependent on those multiples; the text does not claim that
this is the only logically possible classification. The reviewer agreed to
retain it as an open formalization question, rather than an absent rationale
or a release obligation.

### The Signed Field Remains An Acknowledged Development Task

The complete signed field requires a precise confirmation schedule, operand
eligibility, and treatment of zero denominators. The current positive-spine
corpus avoids zero denominators and does not implement the whole field.
This limitation was already stated and was not discovered by the critique.

## A Derived Constraint For Projection Research

For a positive reduced noninteger rational `p/q` in an unfiltered
positive-spine `U_N`, all incoming arithmetic witnesses are

```text
(k*p) / (k*q) -> p/q, with k >= 1 and k*max(p,q) <= N.
```

Addition, subtraction, and multiplication of integer operands cannot produce
a noninteger rational. Reduced fraction equality forces every division pair
to have the form above. Consequently, once the value appears:

```text
first appearance = max(p,q)
incoming witness count at U_N = floor(N / max(p,q))
outgoing arithmetic witnesses = 0
```

Both reviewers independently checked all 143 noninteger rational nodes in a
fresh unfiltered `U16`; there were no mismatches. These formulas describe the
current positive-operand model, not an arbitrary signed or closure model.

Raw arrival stage and repeated division count therefore have an exact
arithmetic baseline. Their agreement with a proposed constant is not an
independent convergence argument. Further structure, explicit projection
rules, and suitable controls are needed, as the existing
[projection protocol](../ORDER4_PROJECTION_PROTOCOL.md) already requires.
This does not establish that every possible projection lacks useful structure.

## Verification Scope And Reproduction

The primary reviewer generated fresh complete `U3`, `U4`, and `U16` databases
in a new temporary directory. No historical corpus was modified. For F2,
use `U3` and bounds 100. For F3–F5, use `U4` and bounds 1000. Both use the
current strict generator, no edge/time limit, and confirmed-edge retention.

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import closing
from strict_stage_moo import build_strict_stage_graph
from moo_research_utils import connect_readonly
from moo_graph_query import later_confirmed_nodes
from branch_lineage import branch_lineage_report

with TemporaryDirectory() as scratch:
    for stage, bound in ((3, 100), (4, 1000)):
        path = Path(scratch) / f"u{stage}.sqlite"
        build_strict_stage_graph(
            db_path=path, max_stage=stage, max_abs_p=bound,
            max_abs_q=bound, max_abs_value=bound,
            max_edges=None, time_limit_seconds=None, commit_every=stage,
            retain_confirmed_edges=True, verbose=False,
        )
        with closing(connect_readonly(path)) as conn:
            if stage == 3:
                print(later_confirmed_nodes(conn, limit=20))
            else:
                report = branch_lineage_report(conn, branch="prime", limit=12)
                print([e for e in report["entries"] if e["value"] in (5, 11, 12)])
```

The primary reviewer also reran 30 existing branch, graph-evidence, invariant,
and route-identity tests. All passed despite these counterexamples. The earlier
308-test pass remains accurate; its coverage did not establish these missing
contracts. Astra separately checked the nine tests in the edited orchestration
test class and found no weakening of the production interpreter guard.

[moo_core_alignment_check.py](../moo_core_alignment_check.py), lines 59–86,
constructs its memory graph using the generator's arithmetic/frontier helpers
and private insertion methods. It does not exercise `eval_moo` or public
arithmetic promotion. Its pass therefore cannot exclude F1. The walkthrough's
separate Cartesian-product and Fraction checks remain useful and passed.

At the end of the initial critique, runtime behavior and the theory were
unchanged and F1–F5 were open. Their subsequent fixes and focused regressions
are recorded in [the resolution](FIVE_FIXES_20261106.md).
This review does not audit every historical
research result or imply that unaffected frozen results are invalid.
