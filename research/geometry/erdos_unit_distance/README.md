# Erdos Unit-Distance Exponent

> Status: external mathematical investigation; certificate analysis and a bounded
> fixed-seed, split-prime, and variable-denominator branch gates completed.
> No claim of a new record exponent or a solution for the optimal exponent.

## Question And Relation To Core

**Exact question:** Which changes to an infinite-family construction can improve
its guaranteed planar unit-distance exponent? The completed gates examine both
Sawin's original equation (11), the repeated product/subset-sum construction
from two rational unit directions, a three-field example of prime splitting,
and variable-denominator comparisons with a uniform bound for full boxes.

**Relation to core:** This is classical mathematics prompted by the conversation
about projection and infinity. The fixed-seed gate includes a small positive-spine
Modulus of One graph witnessing the scalar shell and ratio ingredients. The split-prime
example likewise retains a scalar graph and a separate external field graph.
Their geometry is an external lens; speculative ratios are not used as core operands. There
is no corpus dependency or claim of a Modulus of One-specific mathematical result.

| Scope | evidence_layer | claim_status | tool_status | result_status |
| --- | --- | --- | --- | --- |
| Published finite-parameter reproductions | external_probe | observation | maintained | completed_version |
| Uniform ceiling for the original equation (11) | external_probe | candidate | maintained | completed_version |
| Fixed-seed branch counts, relation, and limiting exponent 1 | external_probe with scalar graph witnesses | candidate | maintained | completed_version |
| One-prime field growth, exact box counts, and comparison thresholds | external_probe with scalar graph witnesses | candidate | maintained | completed_version |
| Variable denominators, finite class separation, and a fixed-field full-box bound | external_probe with scalar graph witnesses | candidate | maintained | completed_version |
| Relation-guided finite improvement and exact direction continuation | external_pair_geometry | observation with exact arguments | maintained | completed_version |
| Sphere-overlap derivation and structural continuation | external_probe | lead | maintained | active |

The ceiling is supported by an explicit inequality argument and directed
interval computations. It remains a locally checked mathematical result,
without independent review or a proof-assistant formalization.

## Reading Order And Dependencies

1. [Investigation and full bound argument](SAWIN_FORMULA_BOUND_NOTE.md).
2. [Version 1 evidence](results/2026-09-10-sawin-formula-investigation-v1.json).
3. [External certificate tool](../../../moo/erdos_unit_distance_certificate.py).
4. [Focused tests](../../../tests/test_erdos_unit_distance_certificate.py).
5. [Fixed-seed branch gate and infinite argument](FIXED_SEED_BRANCH_GATE_NOTE.md).
6. [Branch gate evidence](results/2026-09-10-fixed-seed-branch-v1.json),
   [probe](../../../moo/unit_direction_branch_probe.py), and
   [checks](../../../tests/test_moo_unit_direction_branch_probe.py).
7. [Split-prime growth and exact point-assembly comparison](SPLIT_PRIME_BRANCH_GROWTH_NOTE.md).
8. [Split-prime evidence](results/2026-09-10-split-prime-branch-v1.json),
    [probe](../../../moo/split_prime_branch_probe.py), and
    [checks](../../../tests/test_moo_split_prime_branch_probe.py).
9. [Independent split-prime verifier](../../../moo/verify_split_prime_branch_report.py)
   and [critique evidence](results/2026-09-10-split-prime-critique-v1.json).
10. [Variable denominators and the limit of full boxes](VARIABLE_DENOMINATOR_BRANCH_NOTE.md).
11. [Variable-denominator evidence](results/2026-09-11-variable-denominator-v1.json),
    [probe](../../../moo/variable_denominator_probe.py), and
    [checks](../../../tests/test_moo_variable_denominator_probe.py).
12. [Shared 241 nodes, norm projections, and modular continuation](SHARED_241_NODE_NOTE.md),
    [exact evidence](results/2026-09-11-shared-241-nodes-v1.json), and
    [bounded verifier](../../../moo/verify_241_branch_joins.py).
13. [Geometric inspection of the eight extra links](GEOMETRIC_PROJECTION_NOTE.md):
    exact translated copies, an affine cube projection, and a four-copy prediction check.
14. [Relation-guided finite improvement and exact direction continuation](RELATION_GEOMETRY_NOTE.md),
    [complete graph evidence](results/2026-09-11-relation-geometry-v1.json),
    [bounded probe](../../../moo/relation_geometry_probe.py), and
    [checks](../../../tests/test_moo_relation_geometry_probe.py).

Conceptual dependencies: finite certificates, prime splitting, the
Golod-Shafarevich criterion, logarithmic growth rates, and ball overlap.
The source theorem is [Sawin's paper](https://arxiv.org/html/2605.20579v1).

Software dependencies: Python standard library only. The search uses binary
floating point to propose parameters; exact integer checks and directed Decimal
intervals independently evaluate those parameters. The upper-bound calculation
uses exact multiplicity comparisons and directed intervals throughout.

## Retained Results And Limits

- Reproduced the original exponent 1.0141144286784982...
- Reoptimized a published 74-prime T and reproduced 1.0318830655396396...
- Derived and checked that **no admissible finite parameter choice in the
  unmodified equation (11) can reach exponent 1.03503**.
- This last statement bounds a formula, not the maximum unit-distance count.
  It does not bound extensions of the proof that change that formula.
- The earlier spiral pitch supplies no demonstrated prediction of the optimal
  unit-distance exponent.
- The fixed-seed branch family has eight extra unit pairs at 1,024 points and
  an exact later endpoint collision, but its limiting exponent is exactly 1.
  Its complete available unit-direction count is only quadratic in depth,
  whereas its distinct point count grows at least exponentially in depth.
- A bounded change of ten selected directions gives 1,020 points and 5,188
  unit pairs, improving the original example's 1,024 points and 5,128 pairs.
  Complete exact pair checks and an independent reconstruction agree. One
  short relation continues along an explicit rational direction sequence
  tending to i; the longer collision relation does not persist at every step.
  This supplies a finite improvement and a direction limit, without a new
  asymptotic exponent or an optimality claim.
- Prime 241 supplies 12, 72, and 1,944 unit directions at the same denominator
  in three explicit cyclotomic fields. Full-basis boxes turn this into exact
  equal-point comparisons, with the largest field leading for every T>=259
  under the declared N=T^8 comparison. This is a family-specific threshold.
- Each fixed field/denominator still has limiting exponent 1. Keeping 241
   completely split bounds the degree of a cyclotomic continuation by 64;
   an infinite continuation needs a different field-family argument.
- The split-prime findings survived a second-agent critique and a locally rerun
  reconstruction in a different arithmetic basis. Denominator 241 holds within
  the declared prime-pair exponent budget; squaring a generator can require
  241^2. A suitable infinite family can use a fixed larger prime power, but
  sufficient direction counts and their geometric use remain separate obligations.
- Fixing the denominator was an experimental control. The next investigation
  may vary it together with the field and prime choices. The split-prime note
  now gives the corresponding gain-versus-denominator tradeoff from the
  published geometry bound; fixed denominator is not a requirement of the problem.
- In K_24, denominator 73*97 supplies 157,464 directions and about 7,751 unit
  neighbors per point at N=8192^8, versus about 1,970 for denominator 73^2.
  Exact cap crossings separate the mixed-prime boxes from every point set
  with a single-prime or prime-square common difference denominator in K_24.
- For any fixed CM field and integral basis, all full rectangular coefficient
  boxes satisfy E<=C_epsilon*N^(1+epsilon), uniformly over arbitrary denominators.
  More generally, any fixed-field sequence attaining a fixed positive exponent
  gain requires its least common difference denominator to grow faster than
  every fixed power of N. This is necessary, and does not exclude arbitrary
  configurations with larger denominators.

The JSON report preserves both complete lower-bound parameter lists, their
prime witnesses, interval evaluations, and every case in the upper-bound
argument. It is a completed version; use a new filename for a new run. No
pre-existing frozen corpus or scored report is an input.

## Tools, Checks, And Reproduction

With a Python executable available:

~~~text
python -m unittest test_erdos_unit_distance_certificate -v
python -m moo.erdos_unit_distance_certificate --precision 70 --target-delta 0.03503
python -m unittest test_moo_unit_direction_branch_probe -v
python -m moo.unit_direction_branch_probe
python -m unittest test_moo_split_prime_branch_probe -v
python -m moo.split_prime_branch_probe
python -B -m moo.verify_split_prime_branch_report
python -B -m unittest test_moo_variable_denominator_probe -v
python -B -m moo.variable_denominator_probe
python -B -m unittest test_moo_relation_geometry_probe test_moo_unit_direction_branch_probe -v
python -B -m moo.relation_geometry_probe
~~~

To save another report, add an output path with a new versioned filename.
The tool refuses to replace an existing output file.

Eight focused tests cover published values, interval refinement, an independent
rational-series check of logarithms, invalid arithmetic data, split-prime
budget accounting, exhaustive small knapsack comparisons, and the infinite-tail
closure. The detailed note records the runtime used on this machine.

Eight additional branch-gate tests check independent exact geometry, duplicate
construction paths, the retained relation, scalar graph eligibility, and bounded
resource limits. Its largest enumerated stage contains 1,024 distinct points;
the infinite conclusion comes from the argument, not extrapolation of the data.

Nine split-prime tests check independent field arithmetic, construction and
factor witnesses, exact finite geometry, box counts, and the comparison tail.
All 25 tests across the three tools passed together. The huge full-basis point
sets are counted symbolically, not enumerated.

Seven variable-denominator tests check new prime factors in an independent
radical basis, every computed direction norm, construction graphs, exact
overlap compression and cap thresholds, all Gaussian denominators through
500, and the distinction between denominator growth and actual edge density.
All 32 tests across the four tools passed, together with the core demo at limit 3.

## Claim Language And Next Work

Allowed: "The original equation (11) has a checked formula-level ceiling below
the threshold 1.03503 for every finite admissible parameter choice."

Forbidden: "The Erdos unit-distance exponent is at most 1.03503", "the true
exponent converges to 1.03503", or "Modulus of One has independently produced a record."

Open obligations: independently review the bound argument; audit the complete
arithmetic and geometric refinements behind stronger reported exponents;
preserve subexponential losses when changing a window-counting lemma.

**Next admissible experiment:** reproduce a complete modified certificate
formula, checking its new lemmas before comparing exponents. The ball-overlap
step has been worked through analytically in the note. The covolume, class-group,
and field-tower changes remain separate obligations.

For a new branch construction, first derive how the available unit-direction
count grows relative to its distinct point count. The fixed-seed gate identifies
a necessary growth condition before further point enumeration is justified.
The split-prime example now supplies a complete small model of that growth and
an exact point-window counting control. Its successor must justify its infinite
sequence and retain class-group, denominator, and pair-loss costs; growing
denominators are allowed, and a field tower is one possible route.

The variable-denominator gate now rules out a sustained exponent gain from
full boxes in a fixed field for every denominator choice. A fixed-field
successor must change the assembly enough to permit superpolynomial least
difference denominators relative to point count, and demonstrate repeated
unit neighborhoods. Changing fields is another possible route; the constants
in the fixed-field proof are not uniform over arbitrary field families.

**Stop rule:** do not continue blind parameter searches in equation (11) with
the expectation of reaching 1.03503 or the stronger reported values. Do not
promote a modified numerical formula before its changed hypotheses are checked.
Do not expand the tested fixed-seed family to chase a positive power gain: its
infinite exponent is already pinned to 1. A successor must change the growth
mechanism, then account for both point count and realized unit pairs.
Do not extend the 241 example indefinitely by adjoining only roots of unity:
complete splitting requires the root order to divide 240.
