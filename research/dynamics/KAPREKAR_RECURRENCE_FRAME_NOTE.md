# Kaprekar Recurrence Frame Note

> Status: external-probe research note.
>
> Evidence layer: `external_probe`. Claim status: `observation` with a
> representation-sensitive recurrence lead.
>
> Kaprekar's routine is useful to Modulus of One as a test of value identity,
> representation identity, recurrence-frame state, and graph-witnessed
> interaction. This note does not make digit sorting a Modulus of One runtime operation,
> does not make `6174` a privileged Modulus of One node, and does not claim that Modulus of One has an
> attractor.

## Finding

The useful connection is not:

```text
Modulus of One contains 6174.
```

The useful connection is:

```text
Kaprekar's routine defines a representation-sensitive recurrence frame whose
state cannot be identified with a rational value alone.
```

Current strict-stage Modulus of One can construct the integer `6174` through ordinary
arithmetic edges. It does not currently record the base, digit width, digit
ordering, or transformation edge that gives `6174` its Kaprekar meaning.

Therefore:

```text
6174 as a value node:
  ordinary Modulus of One arithmetic structure

6174 as a Kaprekar fixed point:
  external recurrence-frame structure
```

These readings can eventually interact, but they must not be collapsed.

## Classical Frame

For base `B` and fixed width `w`, a Kaprekar state is a width-`w` digit string.
Leading zeroes remain part of the representation. One step:

```text
1. sort the digits into descending order
2. sort the same digits into ascending order
3. subtract the ascending value from the descending value
4. write the result again at width w
```

For decimal width four, write the map as `K_10,4`. Every nonconstant four-digit
string reaches `6174`, and:

```text
K_10,4(6174) = 7641 - 1467 = 6174
```

Thus `6174` is a fixed point of this named external map.

It is not thereby a fixed point of Modulus of One.

## Difference-Coordinate Reduction

Let the four digits after descending sorting be:

```text
a >= b >= c >= d
```

Then:

```text
descending = 1000a + 100b + 10c + d
ascending  = 1000d + 100c + 10b + a

K_10,4(n) = 999(a-d) + 90(b-c)
```

The step depends only on two digit gaps:

```text
outer gap = a-d
inner gap = b-c
```

For `6174`, the descending digits are `7,6,4,1`, so:

```text
outer gap = 7-1 = 6
inner gap = 6-4 = 2

999*6 + 90*2 = 6174
```

This reduction gives the main structural finding. A large set of digit states
is quotiented immediately to a much smaller gap-coordinate state. The number
`6174` is the decimal four-digit state whose new output recreates its own digit
gaps.

It also follows that every nonzero decimal Kaprekar output is divisible by `9`,
because both `999` and `90` are divisible by `9`. This divisibility is part of
the classical transformation, not evidence that the `6174` node is intrinsically
special in Modulus of One.

## Why Value Identity Is Insufficient

The current Modulus of One runtime uses one canonical node per reduced rational value.
Kaprekar state is not a function of rational value without a base and width.

For example, the same integer `123` gives:

```text
decimal width 3:
  321 - 123 = 198

decimal width 4:
  3210 - 0123 = 3087
```

A reusable Kaprekar state therefore needs at least:

```text
(value, base, width)
```

or, more directly:

```text
(base, width, digit tuple)
```

The value node may remain the arithmetic landing site. The recurrence state
must live in a context-preserving analysis overlay unless a future core design
explicitly promotes representation state into runtime semantics.

## Bounded Modulus of One Diagnostic

On 2026-07-14, a temporary strict-stage corpus was built with:

```text
max_stage:      98
max_abs_p:      7000
max_abs_q:      200
max_abs_value:  7000
operand policy: confirmed positive-spine integers only
```

Querying node `6174` returned:

```text
first_stage:       98
confirmed_stage:   6174
status:            speculative_until_confirmed
incoming edges:
  98 * 63 -> 6174
  63 * 98 -> 6174
```

This is the ordinary product-branch landing:

```text
6174 = 63*98 = 2*3^2*7^3
```

It shows that a field retaining `6174` can see the value well before the
positive spine confirms it. It does not show a Kaprekar edge, digit recurrence,
or fixed-point interaction.

The diagnostic corpus was temporary and was not retained as a frozen research
artifact. This observation is reproducible from the current generator, but it
is not a preregistered dynamics result.

Reproduction commands for a deliberately retained local corpus would be:

```text
python3 -m moo.strict_stage_moo --db out/experiments/kaprekar_u98.sqlite --max-stage 98 --max-abs-p 7000 --max-abs-q 200 --max-abs-value 7000 --quiet --pretty
python3 -m moo.graph_query --db out/experiments/kaprekar_u98.sqlite --node 6174 --pretty
```

Do not run the first command over an existing path; the corpus builder refuses
to overwrite an existing database.

## Correct Modulus of One Classification

Kaprekar's routine should currently be classified as:

```text
recurrence frame:
  yes, as an external representation-sensitive iteration rule

Modulus of One branch:
  no, not from value presence or ordinary arithmetic edges alone

external probe:
  yes

runtime semantics:
  no

fixed point:
  yes, of K_10,4

Modulus of One attractor:
  no
```

The distinction is important. Kaprekar's map supplies its own finite state
space, evolution map, and trajectories. Dynamics language can therefore be
used for that named external frame. It must not be transferred to Modulus of One as a
whole.

## Candidate Analysis Overlay

An aligned future probe should preserve the external state and return to exact
Modulus of One graph context. A minimum event record would include:

```text
frame_id
base
width
source_digit_state
descending_digit_state
ascending_digit_state
descending_value
ascending_value
result_value
next_digit_state
source_value_node
result_value_node
available_moo_edges
missing_moo_witnesses
confirmation_status
interpretation_limits
```

The overlay should not add a unary `kaprekar` operator to core Modulus of One by default.
It should expose the underlying representation and subtraction construction so
the graph interaction remains inspectable.

## What Would Count As Interaction

Weak evidence:

```text
6174 is present.
6174 has many incoming edges.
6174 is divisible by 9.
6174 appears before positive-spine confirmation.
```

Stronger evidence:

```text
the digit-state transition is recorded with base and width
the descending and ascending constructions are explicit
the subtraction landing returns to an exact Modulus of One node
the same witness policy is applied to every state in the frame
gap-coordinate quotient classes are preserved as inspectable groups
results survive base, width, corpus-bound, and matched-node controls
```

A genuinely useful result would show that Modulus of One construction neighborhoods add a
reproducible distinction or prediction beyond the already-known
digit-difference dynamics.

## Lens Card

```text
name:
  Kaprekar representation-sensitive recurrence frame

evidence_layer:
  external_probe

claim_status:
  observation

provocative_hypothesis:
  Modulus of One construction neighborhoods may distinguish recurrence-frame states,
  basin positions, or terminal classes beyond value identity alone.

false_positive_guarded_against:
  Mistaking ordinary presence, divisibility by 9, product factorization, high
  derivation mass, or the classical digit-gap quotient for Modulus of One-native evidence.

graph_native_observable:
  Exact value nodes, available arithmetic edges, confirmation status,
  construction neighborhoods, and explicit gaps between the external
  transition witness and the retained strict graph.

query_or_report:
  No aligned Kaprekar probe exists yet. The bounded node diagnostic uses
  moo/strict_stage_moo.py and moo_graph_query.py.

metric:
  Transition witness completeness, relation distance, confirmation distance,
  basin depth, gap-coordinate class, neighborhood similarity, and residual
  signal after matched controls.

null_model_or_control:
  The exact classical digit-gap map; matched multiples of 9; matched composite
  nodes; alternate bases and widths; transition-label shuffles; and graph
  neighborhoods matched by stage, value height, and operation mix.

promotion_criteria:
  A saved, reproducible overlay returns every candidate to exact nodes and
  edges, survives base/width and graph controls, and predicts held-out terminal
  or basin behavior beyond the classical gap-coordinate model.

kill_criteria:
  The probe only reproduces the known Kaprekar map; all signal is explained by
  digit gaps, divisibility, factorization, or corpus bounds; or no exact graph
  context distinguishes the candidate from matched nodes.

allowed_claim_language:
  "6174 is a fixed point of the decimal four-digit Kaprekar frame. In a strict
  U98 corpus retaining the value, Modulus of One records 6174 as a speculative
  product-branch landing through 63*98."

disallowed_claim_language:
  "6174 is a Modulus of One attractor."
  "Modulus of One explains Kaprekar's constant."
  "The presence of 6174 proves a native interaction."
```

## Research Questions

1. Can a representation-state overlay preserve fixed width and leading zeroes
   without changing core value-node identity?
2. Which Modulus of One branch relations, if any, persist across Kaprekar frames with
   different bases and widths?
3. Does Modulus of One relation distance distinguish basin depth after controlling for the
   exact digit-gap quotient?
4. Can strict graph neighborhoods predict fixed points or terminal cycles on
   held-out bases better than classical difference coordinates already do?
5. Does the external transition expose a useful difference between arithmetic
   construction identity and representation identity, even if it yields no new
   number-theoretic result?

## Current Conclusion

Kaprekar's routine is a strong case study for a future recurrence-frame layer
because it makes the state-identity problem unavoidable. The present Modulus of One graph
constructs `6174` but does not construct its Kaprekar role.

The research value is therefore methodological:

```text
test whether Modulus of One can inspect a representation-sensitive recurrence without
confusing the external frame, the arithmetic value, and the graph witnesses
that connect them
```

Until an aligned overlay and controlled report exist, no stronger interaction
claim is earned.

## References

- Daniel Hanover, "The Base Dependent Behavior of Kaprekar's Routine: A
  Theoretical and Computational Study Revealing New Regularities", 2017:
  <https://arxiv.org/abs/1710.06308>
- Evan Chen, Ken Ono, Richard E. Schwartz, and Dinesh S. Thakur, "Four-digit
  Kaprekar dynamics in odd bases", 2026:
  <https://arxiv.org/abs/2606.20439>
- [RECURRENCE_FRAMES_NOTE.md](RECURRENCE_FRAMES_NOTE.md)
- [research-programs.md](../../docs/protocols/research-programs.md)
- [branch-evidence.md](../../docs/protocols/branch-evidence.md)
- [STAGE_DYNAMICS_LENS_NOTE.md](STAGE_DYNAMICS_LENS_NOTE.md)
- [DYNAMICS_TEST_PROTOCOL.md](DYNAMICS_TEST_PROTOCOL.md)
