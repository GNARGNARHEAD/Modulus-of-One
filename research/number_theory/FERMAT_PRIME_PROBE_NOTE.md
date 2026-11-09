# Fermat Prime Non-Collapse Probe

> Status: speculative analysis probe.
>
> This is not a new Modulus of One operation and not a proof attempt. It is a graph-inspection
> probe for prime-exponent target structure.
>
> Artifact state: the April 2026 smoke corpus named below is absent and no saved
> probe report survives. The command is retained as historical design
> provenance, not as a current runnable path. Use the
> [corpus inventory](../experiments/CORPUS_INVENTORY.md) for retained inputs.

## Framing

For odd prime `p`, Fermat's Last Theorem says there are no positive whole-number
solutions to:

```text
a^p + b^p = c^p
```

Modulus of One should not treat exponentiation as a new primitive. In this probe,
`a^p`, `b^p`, and `c^p` are external repeated-multiplication targets. The
evidence must come from the graph:

```text
node + construction edges + local graph neighborhood
```

not from the bare equation.

The power targets are analysis-layer selections, not new Modulus of One construction
rules. If a target value or edge is not present in the saved graph corpus, the
probe treats that as absence in the current run rather than constructing it by
fiat.

## Modulus of One Question

The Modulus of One-readable question is:

```text
Do odd-prime power targets show a distinctive failure to collapse?
```

For `p = 2`, square/self-relation targets can collapse:

```text
3^2 + 4^2 = 5^2
```

For odd prime `p`, the Fermat-style target:

```text
left side:  a -> a^p, b -> b^p, a^p + b^p
right side: c -> c^p
```

does not collapse for positive whole-number values.

In Modulus of One, that makes the failure itself the object of inspection:

```text
which target nodes exist?
which construction edges produce them?
how close are near misses?
do prime exponents create recognizable non-overlap neighborhoods?
```

## Historical Probe Command

Do not recreate or overwrite the recorded path merely to make this command
work. A new run needs a compatible surviving read-only corpus or a fresh
scratch corpus and a new result identity.

```sh
python3 -m moo.fermat_prime_probe \
  --db out/experiments/strict_stage_graph_smoke_20260430_v2.sqlite \
  --primes 3,5,7 \
  --min-base 2 \
  --max-base 8 \
  --top-k 8 \
  --pretty
```

The recorded `U80` design had tight value bounds, so most higher power target
nodes were expected to be absent. A new calibration needs a declared corpus
with bounds chosen to retain the relevant power targets.

## Interpretation Discipline

The probe reports:

```text
collision_count
nearest_non_collapses
graph_rich_targets
```

`collision_count` should remain zero for odd prime exponents over positive
whole-number bases.

`nearest_non_collapses` are not evidence by themselves. They are only candidate
addresses for graph inspection.

`graph_rich_targets` are more Modulus of One-relevant because they ask which Fermat-style
targets are actually present as graph nodes with construction edges.
The stricter signal is `found_target_edges`, not just `found_target_nodes`: a
whole-number node may exist because the core loop reached it, even when the
specific power/sum target edge is absent under the current corpus bounds.

## What Would Be Interesting

Potentially useful future observations:

```text
odd-prime targets repeatedly approach collapse but miss by structured gaps
near misses share construction neighborhoods
prime exponents differ from composite exponents in graph-rich target structure
p = 2 collapse behavior separates sharply from odd-prime non-collapse behavior
```

That would not prove anything about Fermat's theorem. It would give Modulus of One a clean
prime-exponent probe for graph non-collapse.
