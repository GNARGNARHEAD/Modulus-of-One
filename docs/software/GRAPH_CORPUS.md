# Graph-First Positive-Spine Corpus

> Status: canonical graph-storage, stage and retention contract.

The SQLite corpus stores confirmed iterations, retained relational outputs and
their ordered construction events. Use the [runtime reference](RUNTIME.md)
for selected in-memory expressions, and the
[corpus inventory](../../research/experiments/CORPUS_INVENTORY.md) for source
identities and availability. Saved reports do not imply their inputs survive.

## The Construction Rule

The epistemic reading comes first: recurrence of `1` is second order because
it depends on memory; relations between its multiples are third order. This
corpus implements the counted-recurrence projection of that account. Its
positive-integer operand rule expresses which constructions have second-order
support in this field. It is not a claim that exact fractional arithmetic is
numerically uncertain. See [Epistemic Order](../foundations/EPISTEMIC_ORDER.md).

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

The [worked inspection](../examples/WORKED_INSPECTION.md) generates a small complete
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

The `edges` table is the important shift. It means Modulus of One can ask graph questions
directly:

```text
which constructions produce 34/21?
which nodes share construction inputs?
which paths collapse onto the same value?
what is the local graph neighborhood of a probe-selected node?
which structures are dense by edge count rather than just value proximity?
```

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
retention rule. `moo/graph_corpus.py` owns the frontier and retention helpers;
both `moo/strict_stage_moo.py` and `moo/graph_evidence.py` consume those same rules.
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
python3 -m moo.strict_stage_moo \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --max-stage 80 \
  --max-abs-p 200 \
  --max-abs-q 200 \
  --max-abs-value 4 \
  --summary out/scratch/strict_stage_graph_smoke_v1_summary.json \
  --quiet --pretty
```

The [archived corpus note](../../archive/reorganizations/20261107/GRAPH_CORPUS_NOTE.md)
retains the April U80/U120 measurements and their original source paths.
Those historical inputs are absent. A fresh run is a new corpus with its own
hash and summary, not a replacement for either original input.

## Graph Query Example

Command:

```sh
python3 -m moo.graph_query \
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

The lack of outgoing edges is correct under aligned Modulus of One. `34/21` is a real
speculative rational node; it is recorded in Modulus of One, but speculative nodes are
inspected rather than operated on.

## Current Query Tools

The graph corpus can now be read through Modulus of One-facing queries:

```sh
python3 -m moo.graph_query \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --summary --pretty

python3 -m moo.graph_query \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --node 34/21 --neighborhood --limit 8 --pretty

python3 -m moo.graph_query \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --compare 34/21 55/34 --limit 8 --pretty

python3 -m moo.graph_query \
  --db out/scratch/strict_stage_graph_smoke_v1.sqlite \
  --confirmations --limit 20 --pretty
```

These are read-only instruments over the stored graph. They do not change the
Modulus of One run. Their job is to expose:

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
moo/graph_corpus.py
moo/strict_stage_moo.py
moo/graph_query.py
```

and should treat node-only ledgers as transitional artifacts.
