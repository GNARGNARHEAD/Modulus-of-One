# Earlier Closure And Ledger Tools

These instruments support the [historical research](../../archive/README.md):
bounded set closure, speculative-operand scans, motif studies, node-summary
ledgers and their plotting/inspection tools. They remain runnable as modules,
for example `python3 -m moo.legacy.order_transition_study --help`.

They do not all implement the same model. Closure studies can reuse speculative
values; the transitional stage-indexed ledger instead records summaries under
its stated stage rule. Neither is the current graph-first SQLite substrate.
Read each study's original evidence layer and source requirements before use.
The waterfall and attractor visualizers call the current runtime demo with
its default confirmed-operand restriction; their historical status concerns
the plotting and interpretation workflow, not speculative-operand closure.
Optional plotting dependencies and missing historical inputs are described in
the [development guide](../../docs/software/DEVELOPMENT.md) and
[corpus inventory](../../research/experiments/CORPUS_INVENTORY.md).

Preservation does not promote a result or retire a broader research question.
The [motif/hinge program](../../research/motif_hinge/README.md) specifies the
strict-graph reproduction gate for its historical leads.
