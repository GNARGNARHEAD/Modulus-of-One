# Resolution Of The Five Critique Findings — 6 November 2026

The five defects in the [Astra critique](ASTRA_CRITIQUE_20261106.md) were
corrected one at a time, with each failure reproduced before its fix and
focused regressions run afterward. These changes enforce the existing
positive-spine rules. They do not replace the epistemic hierarchy or implement
the broader signed field.

## Changes

| Finding | Corrected behavior | Regression coverage |
| --- | --- | --- |
| F1: expression results were immediately confirmed | Evaluation leaves recurrence unchanged. Results remain speculative unless already confirmed. Public promotion cannot skip an iteration. | [Expression tests](../test_constructionist_math.py): first fan, integer and fractional outputs, rejected reuse, explicit later confirmation, witness preservation, exploratory mode, CLI. |
| F2: confirmation query included future stages | `--confirmations` includes only thresholds reached by the last complete saved stage and reports that checkpoint. | [Query tests](../test_moo_graph_query.py): complete U3/U6, partial frontier, missing stage evidence, preserved future schedule. |
| F3: branch reports treated thresholds as spine witnesses | Spine support and operand eligibility require actual completed-stage coverage. Linear branch witnesses use the same checkpoint. | [Branch tests](../test_branch_lineage.py): future integers, later confirmation, interrupted runs, stored edges beyond the complete checkpoint. |
| F4: one missing factor pair was treated as an absent product branch | The analyzer queries all retained nontrivial ordered product witnesses at the checkpoint and exposes their exact references/count. | Alternate routes for `12`, all seven routes for `36` by U18, and filtered products that must remain unwitnessed. |
| F5: ordinary primality was presented as witnessed membership | Arithmetic labels have an explicit basis. Native membership requires spine support and a complete, retention-eligible product field with no nontrivial product witness. | Absent `11`, unconfirmed `5`, confirmed `5`, bounded prime/composite examples, unknown retention, and future factor operands. |

Branch reports use schema **`branch_lineage.v4`**. The old sparse test fixture
was replaced by a real generated corpus so its stage-completeness claims are
supported by actual frontier telemetry.

## Expression Evaluation

A new graph has only `1` confirmed. Evaluating `1+1` records speculative `2`;
it does not advance recurrence. Evaluating `1/(1+1)` therefore requires an
explicit advance through two:

```sh
python3 constructionist_math.py --confirm-through 2 '1/(1+1)'
```

The result remains speculative `1/2`. In Python:

```python
from constructionist_math import Graph, eval_moo

graph = Graph()
graph.advance_frontier_max_to(2)
_, four = eval_moo('(1+1)*(1+1)', graph=graph)
assert four.status == 'S'
graph.advance_frontier_max_to(4)
assert four.status == 'G'
```

The same value node and its earlier multiplication witness survive the change
of support. The expression tool records selected operations. The stage-corpus
generator and walkthrough remain the tools for inspecting the full operation
field at each iteration.

## What Makes The Prime Report's Absence Check Eligible

For a nontrivial positive-integer product `a*b=n`, both `a` and `b` are less
than `n`. Confirmation through `n` therefore covers every possible factor
operand. The product event's first stage `max(a,b)` is also less than `n`, so
the result never receives the confirmed-result retention exemption at that
event. The same fixed output bounds apply to every possible nontrivial
product landing on `n`.

The analyzer uses the shared retention rule to test those bounds at `n-1`,
separately from checking the reached stage. Only then can absent product
witnesses support the report's irreducibility reading. Unknown or excluding
bounds block that reading. An ordinary prime/composite label remains available
as `arithmetic_shortcut`; it does not become a graph witness. Arithmetic
factorization also prevents a composite with unexpectedly missing edges from
being labelled a prime-branch member.

`GraphEvidence.retains_result` exposes the existing retention calculation;
it does not change the generator or assert that an edge exists. The report
distinguishes retained witnesses, relations permitted by confirmed operands,
and arithmetic classifications through `classification_basis`.

## Verification

In a fresh source-only copy and Python 3.14.4 virtual environment with no
installed packages:

- Root suite: **320 passed**.
- Geometry suite: **6 passed**.
- Dynamics suite: **6 passed**.
- Walkthrough, explicit-confirmation expression command, ordinary demo, and
  Fibonacci demo: passed.

Total: **332 tests**, including 24 added regressions. Each original failure
was observed before correction. The additional partial-frontier linear-branch
inconsistency was also reproduced and corrected during verification.

The Astra reviewer independently reran the 35 focused expression/query/branch/
evidence tests, then generated 64 corpora covering U1 through U8, four output
bounds, and complete versus edge-limited runs. Its independent checks covered
2,496 prime-report rows plus confirmation and square/even reports, with no
mismatches. The primary reviewer separately checked the owning code, the
retention argument, the original counterexamples, and the full test suite.

The original critique remains a record of the failures before correction.
Frozen research reports and source manifests were not rewritten. The source
corpora and generator are unchanged; newly produced analysis reports carry
the changed tool identities and, for branch reports, the new schema version.
These checks cover the five fixes and their boundary cases, not every open
research claim in the repository.
