# Runtime Walkthrough: Following 16

This is an implementation companion to the [main account](../../README.md).
For the mathematical use of branch inspection, begin with the
[worked shell/ratio investigation](BRANCH_INSPECTION.md). This smaller tutorial
explains confirmation, shared values and retained witnesses: `4` appears
before it may be used, `16` then appears through `4 * 4`, further relations
reach that same value, and counted recurrence eventually confirms it.

From the repository root, run:

```sh
python3 tools/moo_walkthrough.py
```

The walkthrough uses the Python standard library. It builds temporary
SQLite databases, checks the construction, prints the checkpoints below, and
removes its temporary files. It needs no saved research corpus.

## The Field Being Inspected

This example uses the current **positive-spine** model. At `U_n`, the counted
multiples `1..n` are available as operands. All four fundamental operations
apply to every ordered pair, including self-pairs. Relational results remain
visible even when they are not yet eligible as operands.

At `U1`, this gives the first operator fan:

```text
1 + 1 -> 2
1 - 1 -> 0
1 * 1 -> 1
1 / 1 -> 1
```

The generator records each operation once, when both operands first become
available, and retains it at later stages. For operands `a` and `b`, that
first stage is `max(a,b)`. Thus `U_n` contains `4*n*n` arithmetic edges plus
its seed edge. Each iteration extends the same full operation field; the
checkpoints below select observations within it.

The generated field reaches `U16`, with numerator and absolute-value bounds
of 256 and denominator bound 16. These retain every result of the four
operations on `1..16`: a product is at most 256, a sum at most 32, a
subtraction has magnitude at most 15, and a reduced ratio's numerator and
denominator are at most 16. The script independently checks the Cartesian
product and all exact results at **every stage from `U1` through `U16`**.
The full signed Modulus of One field remains broader than this positive-spine model.

## From The First Fan To 16

The first fan constructs `2` at `U1`. Counted recurrence confirms it at `U2`,
where both `2 + 2` and `2 * 2` reach `4`. These are distinct witnesses at one
value node. `4` is recorded but cannot yet be used as an operand.

At `U4`, recurrence confirms `4` and makes `4 * 4 -> 16` available. This is
the first appearance of `16`, and the only arithmetic witness reaching it
by that stage. The claim can also be checked directly: earlier operands are
at most 3, so products are at most 9; at `U4`, addition reaches at most 8,
while subtraction and division cannot reach 16. The only product of operands
in `1..4` equal to 16 is `4 * 4`.

At `U8`, the incoming arithmetic witnesses for `16` are exactly:

| Witness | First available stage |
| --- | --- |
| `4 * 4 -> 16` | `U4` |
| `8 + 8 -> 16` | `U8` |
| `2 * 8 -> 16` | `U8` |
| `8 * 2 -> 16` | `U8` |

Both operand orders are kept. All four witnesses reach the same canonical
value node; the earlier square witness remains. The observation that `U4`
has only a square witness is still correct. A wider claim that `16` can
*only* arise through squaring has been refuted by the additive witness.

At `U16`, counted recurrence confirms `16`, allowing it to become an operand.
That supplies second-order support without changing the value or erasing
its earlier relational witnesses. It does not confer the immediate certainty
of `1`.

The report's `four` and `sixteen` records capture these checkpoints with
stage-filtered edge queries, node IDs, and confirmation status. A stored
`confirmed_stage=16` is a threshold; the checkpoint must have reached sixteen
before the value is confirmed there. Other report checks, `shared_half` and
`six`, provide supplementary checks of shared identity and confirmation.

These runtime distinctions support the branch investigations; they are not
their whole purpose. The [shell/ratio example](BRANCH_INSPECTION.md) uses an
agreement to generate further constructions, and the
[pi example](PI_FOURTH_ORDER_EXAMPLE.md) proposes a convergence form through
inspection under added geometric assumptions. Such a proposal has no counted
confirmation stage like `U16` for the integer `16`.

## A Control On What Was Saved

A separate control corpus reaches `U8` but retains results only up to
numerator and absolute value 8, with denominator bound 8 and the usual
confirmed-edge exception. It omits `4 * 4 -> 16`: the operands are available,
but the result lies outside the retention bounds when the pair first appears.

An absent stored edge therefore needs an explanation before it can support
a mathematical claim. Here the explanation is the declared output bound.
The control changes storage bounds, not the operation rule. The main field's
bounds retain the entire finite operation field used in this construction.

## Keep And Inspect The Evidence

Choose a new output directory to preserve both databases and the report:

```sh
python3 tools/moo_walkthrough.py --output-dir out/scratch/walkthrough_v1
```

The script refuses an existing directory. `report.json` includes source and
database hashes, operation counts, node identities, exact edge references,
checkpoint observations, and the control's retention assessment. The databases
also retain their generation configurations. The witnesses are local operation
records; the corpus does not choose an ancestral proof for each operand use.

For a detailed query of the `16` node in this newly generated field:

```sh
python3 -m moo.graph_query \
  --db out/scratch/walkthrough_v1/field.sqlite \
  --node 16 --limit 32 --pretty
```

This query inspects the completed `U16` field. Use the report's checkpoints
for the earlier `U4` and `U8` observations.

This is a fresh demonstration using the current generator. Historical research
reports refer to their own source identities and edge IDs. See the
[corpus contract](../software/GRAPH_CORPUS.md),
[source inventory](../../research/experiments/CORPUS_INVENTORY.md), and
[development guide](../software/DEVELOPMENT.md) for larger runs and checks.
