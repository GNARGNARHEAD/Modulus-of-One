# Fermat Little Return-Corridor Probe

> Status: speculative analysis probe.
>
> This is not a new Modulus of One operation and not a proof attempt. It is a graph
> inspection probe for return structure around prime moduli.
>
> Artifact state: the April 2026 smoke corpus named below is absent and no saved
> probe report survives. The command is retained as historical design
> provenance, not as a current runnable path. Use the
> [corpus inventory](../experiments/CORPUS_INVENTORY.md) for retained inputs.

## Framing

Fermat's Little Theorem says that, for prime `m`, the value:

```text
a^m - a
```

is divisible by `m`.

Modulus of One should not add modular arithmetic or exponentiation as primitives. This
probe computes the target corridor externally, then asks what the existing Modulus of One
graph actually contains:

```text
a -> a^m -> a^m - a -> (a^m - a) / m
```

The Modulus of One evidence is the graph:

```text
node + construction edges + local graph neighborhood + confirmation status
```

not the bare theorem.

The target values are analysis-layer selections, not new Modulus of One constructions.
If the required nodes or edges are absent from the graph, the probe reports
that absence rather than manufacturing the corridor inside Modulus of One.

## Certainty Anchor Rule

Base `1` is included by default.

In ordinary theorem-probing it is easy to treat `a = 1` as a trivial case. In
Modulus of One that is the wrong default. Self-reference through `1` is exactly the kind
of correlation that matters, because `1` is the only certainty and the anchor
from which later structure becomes interpretable.

The probe may still be run with `--min-base 2` for a comparison pass, but that
is a filtered view, not the default Modulus of One view.

## Historical Probe Command

Do not recreate or overwrite the recorded path merely to make this command
work. A new run needs a compatible surviving read-only corpus or a fresh
scratch corpus and a new result identity.

```sh
python3 -m moo.fermat_little_probe \
  --db out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite \
  --max-modulus 12 \
  --max-base 8 \
  --top-k 5 \
  --pretty
```

## Interpretation Discipline

The probe reports:

```text
prime_summary
composite_summary
prime_return_failures
composite_integral_returns
graph_rich_returns
```

The clean arithmetic contrast is whether the return is integral. The stricter
Modulus of One signal is whether the return corridor is present in the graph as edges, not
only as values.

The recorded small-corpus design targeted low-stage corridors, especially
around `1` and `2`. Larger modulus/base corridors require a newly declared
corpus whose bounds retain the relevant power, subtraction, and division
nodes.

## What Would Be Interesting

Potentially useful future observations:

```text
prime moduli produce return corridors that stay structurally coherent
composite moduli show broken or partial return corridors
self-reference through 1 repeatedly appears as the organizing anchor
graph-rich returns share neighborhoods or confirmation profiles
```

That would not prove Fermat's Little Theorem. It would give Modulus of One a clean
prime/composite probe for return structure around the certainty anchor.
