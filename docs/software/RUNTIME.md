# Runtime And Construction Identity

This reference describes the expression-oriented in-memory runtime in
[`moo/constructionist_math.py`](../../moo/constructionist_math.py). The
[graph-corpus contract](GRAPH_CORPUS.md) owns the SQLite full-field generator,
its stage schedule, retention and completeness rules. The
[epistemic-order note](../foundations/EPISTEMIC_ORDER.md) owns their philosophical
interpretation.

## Two Ways To Inspect Construction

The in-memory `Graph` records selected arithmetic constructions and explicit
frontier advances. Evaluating an expression does not enumerate the full
four-operation field or confirm an arithmetic result. Use
`advance_frontier_max_to(n)` to admit counted recurrence through `n`, then
`eval_moo(expression, graph=graph)` to inspect selected constructions.

The SQLite generator, `python3 -m moo.strict_stage_moo`, enumerates all four
operations over the available ordered pairs, subject to declared output
retention. The [walkthrough](../examples/WORKED_INSPECTION.md) checks that full
field through `U16`. These interfaces serve different inspection tasks under
the same confirmed-positive-operand restriction.

## Nodes, Values And Promotion

`Ref(1)` is seeded when a graph is initialized. The in-memory indices are:

| Index | Meaning |
| --- | --- |
| `nodes_by_int` | One grounded reference per confirmed integer. |
| `nodes_by_value` | One node per reduced rational value `(p, q)`. |
| `nodes_by_uid` | Nodes indexed by local identity. |
| `value_classes` | The value projection; currently one rational value node per class. |

An arithmetic result can precede confirmation. Positive-spine promotion changes
the status of the existing integer value node; it does not erase its edges or
create a second copy of its value. Zero, negative values and noninteger
rationals remain relational outputs in the aligned runtime. The signed-frontier
helper is explicitly unimplemented.

| Runtime annotation | Interpretation |
| --- | --- |
| `status == "G"` | A confirmed reference, including the primitive `1`. |
| `status == "S"` | An unconfirmed value or injected claim. Historical exploratory mode also has an undefined division node. |
| `metadata["tier"]` / `epistemic_order` | `1` for the primitive anchor, `2` for confirmed positive integers above `1`, `3` for the other runtime nodes. These labels do not certify each incoming witness. |
| `constructible_from_one` | True for grounded anchors and for a speculative node supported by a derivation whose inputs are constructible; false for an isolated injected claim with no supporting construction. |

The helper `speculate_ref(n)` can insert a speculative integer claim without
deriving it. Its presence in a graph is not evidence of a witnessed arrival.
This explicit injection facility is used in demonstrations and tests; it is
not a second primitive or automatic confirmation.

## Operations And Historical Mode

Aligned arithmetic permits only confirmed positive-spine operands. Exact
integer and reduced rational outputs join their canonical value nodes. An
output is grounded only if the positive spine has already confirmed it.
Zero cannot be a denominator in aligned mode because it is not an eligible
operand.

`allow_speculative_operands=True` (CLI `--allow-speculative-operands`) enables
historical exploratory behavior. It permits operations that aligned mode
rejects, including speculative reuse; division by zero then records a shared
undefined node, not a rational value. Use that mode only with its evidence
layer stated. The [legacy tools](../../moo/legacy/README.md) preserve older
closure and ledger workflows for comparison.

## What Local Witnesses Preserve

Edges retain the operation, ordered inputs, result and metadata. Equal-valued
constructions can have distinct edges while sharing their result node.
The evidence unit is the node with its incoming witnesses and surrounding
graph, rather than its numeric label alone.

This representation does **not** choose a particular ancestral supplying
witness each time that value is used. For example, both `1*1` and `1/1` return
the same node. A later addition of those references cannot distinguish which
earlier witness supplied its left or right role. The
[identical-export counterexample](../../archive/reviews/ASTRA_CRITIQUE_20261106.md#local-provenance-does-not-select-a-supplying-witness)
demonstrates this limit. Witness-specific proof composition needs an explicit
certificate or additional representation; a bare local edge cannot supply it.

## Inspection Interfaces And Open Work

- `to_json()` and `to_jsonable()` export graph state.
- `to_dot()` and `to_dot_view()` expose structural/value views.
- `resolve_events()` and `to_resolve_dot()` expose promotion diagnostics.
- `stats()` and field-map helpers summarize the graph.
- `python3 -m moo.graph_query` inspects SQLite nodes, incoming witnesses and
  neighborhoods; [node profiles](NODE_PROFILES.md) add bounded associations
  and named certificates without changing operand eligibility.

These are implemented operational rules, not a completed axiomatization of
Modulus of One. Open work includes a formal identity calculus, independence and collapse
criteria, rewiring invariants, consistency/completeness obligations, and
witness-specific path composition. The [otherness inquiry](../foundations/OTHERNESS.md)
owns the foundational distinction questions; the
[circle/phase program](../../research/geometry/circle_as_one/README.md) owns
questions about quotient fibres, return and loop interpretation. The
[archived design](../../archive/reorganizations/20261107/VISION.md) preserves
the earlier roadmap without serving as a second current specification.
