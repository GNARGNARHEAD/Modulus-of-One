# Graph-First Positive-Spine Corpus

> Status: canonical graph-storage contract with historical April 2026 run
> measurements.
>
> The two SQLite files named below were treated as current when this note was
> written, but neither is present in the current workspace:
>
> Recorded expanded corpus:
> `out/experiments/strict_stage_graph_u120_20260430.sqlite`
>
> Recorded smoke corpus:
> `out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite`
>
> Use the [corpus inventory](out/experiments/CORPUS_INVENTORY.md) for the exact
> retained inputs that survive now. The recorded paths above are provenance,
> not writable command targets.

## Why This Exists

MoO is fundamentally a construction graph, not a list of values.

The graph is the primary method of inspection. A value is only a coordinate in
the graph; the evidence is how that value is produced, how often paths collapse
onto it, which confirmed inputs surround it, and how it relates to nearby nodes.

The core object is:

```text
confirmed iterations
speculative nodes
construction events
many paths collapsing onto the same value
shared construction inputs and graph neighborhoods
```

The previous node-summary positive-spine ledger preserved node summaries and
first construction records. That was useful, but not graph-native. The JSONL
artifact has been purged so it is no longer treated as an active research
substrate.

The graph-first corpus fixes that for the current positive-spine strict corpus.
It is not the complete signed operator-fan MoO field.

Any non-graph report should be treated as a scout or summary. It can point at a
node, but it does not replace graph inspection.

## The Construction Rule

The epistemic reading comes first: recurrence of `1` is second order because
it depends on memory; relations between its multiples are third order. This
corpus implements the counted-recurrence projection of that account. Its
positive-integer operand rule expresses which constructions have second-order
support in this field. It is not a claim that exact fractional arithmetic is
numerically uncertain. See [Epistemic Order](EPISTEMIC_ORDER_NOTE.md).

At a complete stage `U_n`, let the confirmed multiples be

```text
C_n = {1, 2, ..., n}.
```

Apply each of `+`, `-`, `*`, and `/` to **every ordered pair** `(a,b)` in
`C_n × C_n`, including equal operands. The field already contains all four
operations on `(1,1)` at `U1`. Division has a positive denominator in this
implementation. Results are represented by reduced rational values, with one
node per value and distinct operation occurrences retained as edges.

The generator records each ordered operation at its first available stage:

```text
s = max(a,b)
edge = (s, operation, a, b, result).
```

At stage `n`, it therefore only needs to add pairs with `max(a,b)=n`. Earlier
edges remain in the same graph. This is incremental storage of the full
operation field, not a choice to stop applying some operations or to inspect
only the counting branch. With no output filtering, `U_n` has `4*n*n`
arithmetic edges plus the seed edge.

For a bounded saved corpus, retain an edge when its result passes the declared
retention rule **at stage `s`**. A rejected result is not silently reconsidered
at a later stage. The confirmed multiples are present even when bounds omit
some of their arithmetic witnesses. Thus the value nodes at `U_n` consist of
the confirmed multiples together with retained outputs; they are not just the
list `1..n`.

Presence and confirmation are different facts. `2*3 -> 6` appears at `U3`;
`6` gains second-order confirmation when counted recurrence reaches `U6`.
Even `5+1 -> 6` is available at `U5`. The existence of that arithmetic edge
does not advance the recurrence or its confirmation stage. The schedule and
the recorded relational witnesses must both remain visible.

For any positive integer `k`, the database's `confirmed_stage=k` field records
this schedule even if the saved corpus stops before `Uk`. A checkpoint view
must first verify that the checkpoint has reached `k`; a future threshold is
not an observed confirmation. Fractions, zero, and negatives have no such
positive-spine confirmation threshold.

The [worked inspection](docs/WORKED_INSPECTION.md) generates a small complete
field and a separate bounded control, then checks these distinctions directly.

## Canonical Tables

The SQLite corpus stores:

```text
nodes
  node_id
  p
  q
  label
  kind
  first_stage
  confirmed_stage
  first_edge_id

edges
  edge_id
  stage
  op
  left_node_id
  right_node_id
  result_node_id

stages
  stage
  candidate_events
  retained_events
  new_nodes
  new_edges
  total_nodes
  total_edges
  elapsed_seconds
```

The `edges` table is the important shift. It means MoO can ask graph questions
directly:

```text
which constructions produce 34/21?
which nodes share construction inputs?
which paths collapse onto the same value?
what is the local graph neighborhood of a probe-selected node?
which structures are dense by edge count rather than just value proximity?
```

## Positive-Spine Strict Rule

The current graph corpus follows the positive-spine strict rule:

```text
operands = confirmed positive-spine iterations only
outputs = retained speculative nodes
speculative outputs are inspected, not operated on
promotion by the positive spine permits later operation
```

At stage `U_n`, new edge occurrences are generated for ordered operand pairs
where at least one operand is the newly confirmed positive-spine value `n`. This
stores each confirmed-operand construction at its first possible stage.

This is a useful strict corpus, but it is scoped:

```text
positive spine:
  expansion branch / counted recurrence projection

not implemented here:
  full signed operator-fan field
```

See `FUNDAMENTAL_OPERATOR_FAN_NOTE.md`.

## Complete-Frontier And Retention Contract

A row in `stages` is not automatically a completed strict frontier. At stage
`u`, the generator visits the ordered pairs whose maximum operand is `u`:

```text
2*u - 1 ordered operand pairs
4 arithmetic operations per pair
8*u - 4 candidate events
```

A run stopped mid-frontier by `--max-edges` can record a partial last row. The
current time-limit check occurs between stages, but readers do not assume that
every producer will always stop only at that boundary. Read-only evidence
therefore uses the last contiguous stage whose
`candidate_events` equals the shared complete-frontier count. It reports the
recorded maximum separately and never treats a partial frontier as an eligible
absence aperture.

Result retention is also part of edge eligibility. A candidate result is
recorded only when it passes the configured numerator, denominator, and
absolute-value bounds, except for the explicitly configured confirmed-edge
retention rule. `moo_graph_corpus.py` owns the frontier and retention helpers;
both `strict_stage_moo.py` and `moo_graph_evidence.py` consume those same rules.
If `config_json` is missing, invalid, or names an unsupported generator, the
evidence layer reports retention eligibility as unavailable rather than
guessing that an absent result should have been stored.

Consequently:

```text
missing beyond the last complete frontier
  != eligible edge absence

missing because the result is outside retention bounds
  != eligible edge absence

exact edge count
  is independent of the display-reference limit
```

This contract matters whenever a probe compares present and absent named
relations. It prevents corpus truncation or configured filtering from being
reported as graph behavior.

## Disposable Smoke Reproduction

Choose an unused scratch suffix. The builder refuses to overwrite an existing
corpus. A current reproduction command is:

```sh
python3 strict_stage_moo.py \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --max-stage 80 \
  --max-abs-p 200 \
  --max-abs-q 200 \
  --max-abs-value 4 \
  --summary out/scratch/strict_stage_graph_smoke_v1_summary.json \
  --quiet --pretty
```

Recorded U80 result:

```text
final stage: U80
nodes:       3,522
edges:       9,559
alignment:   pass
```

Expanded U120 result:

```text
final stage: U120
nodes:       7,798
edges:       20,989
alignment:   pass
```

Node kinds:

```text
certainty:              1
positive integers:     79
rationals:          3,437
relational integers:   5
```

Edge operations:

```text
seed:    1
+:       6
-:   3,550
*:     160
/:   5,842
```

## Graph Query Example

Command:

```sh
python3 moo_graph_query.py \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --node 34/21 \
  --limit 8 \
  --pretty
```

Result:

```text
34/21 exists as a rational node.
first stage: U34
incoming edges:
  U34: 34 / 21 -> 34/21
  U68: 68 / 42 -> 34/21
outgoing edges:
  none
```

The lack of outgoing edges is correct under aligned MoO. `34/21` is a real
speculative rational node; it is recorded in MoO, but speculative nodes are
inspected rather than operated on.

## Current Query Tools

The graph corpus can now be read through MoO-facing queries:

```sh
python3 moo_graph_query.py \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --summary --pretty

python3 moo_graph_query.py \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --node 34/21 --neighborhood --limit 8 --pretty

python3 moo_graph_query.py \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --compare 34/21 55/34 --limit 8 --pretty

python3 moo_graph_query.py \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --confirmations --limit 20 --pretty
```

These are read-only instruments over the stored graph. They do not change the
MoO run. Their job is to expose:

```text
how a speculative node was produced
which confirmed inputs sit around it
which other nodes share those inputs
which positive-spine values were first seen speculatively before the positive
spine confirmed them
```

`--confirmations` reports only confirmations reached by the last complete
saved stage and names that `confirmation_checkpoint`. Future thresholds remain
visible in ordinary node records. If stage completeness cannot be established,
the confirmation list is empty and its checkpoint is null; this does not
establish that no confirmation occurred.

## Relationship To Older Artifacts

The old node-summary positive-spine run remains useful only as historical
context; its JSONL ledger has been purged and should not be treated as active
storage.

The older exploratory closure corpus remains useful for motif hypotheses, but
it reuses speculative nodes as operands and is not the positive-spine strict
corpus.

Going forward, serious positive-spine graph work should use:

```text
moo_graph_corpus.py
strict_stage_moo.py
moo_graph_query.py
```

and should treat node-only ledgers as transitional artifacts.
