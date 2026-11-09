# Rational Shell Geometry

> Program status: active external shell/square and construction-lineage
> scrutiny.

## Exact Question

When exact rational components satisfy shell and square relations, does their
strict graph timing or construction ancestry support a repeatable Modulus of One branch
reading beyond value co-presence and classical formula membership?

## Relation To The Core

The shell equation and Euclid parametrization are external exact filters.
Modulus of One-specific evidence begins only when their components, operations, stages,
witnesses, and lineages are returned to the strict graph.

## Status By Scope

| Scope | Evidence layer | Claim status | Tool status | Result status | Result scope |
| --- | --- | --- | --- | --- | --- |
| Exact shell and Euclid-family filters | `external_probe` | `observation` | `maintained` | `completed_version` | External exact report machinery |
| Bounded timing and lineage reports | `strict` | `observation` | `maintained` | `completed_version` | Named corpus-bound graph reports |
| General shell-branch law | `strict` | `lead` | `maintained` | `active` | No promoted law; ancestry and controls remain required |
| Ordered shell-composition schema | `external_probe` | `candidate` | `maintained` | `active` | Signed witnesses; group structure belongs to normalized observations |
| Fixed shell-composition calibration | `strict` | `observation` | `maintained` | `completed_version` | New current-generator U576 and U80 fields; historical SQLite inputs absent from this checkout |

## Conceptual Dependencies And Reading Order

1. [Geometry-wide probe boundary](../GEOMETRIC_PROBES_NOTE.md)
2. [Shell/square component report protocol](../CIRCLE_SQUARE_ALIGNMENT_PROTOCOL.md)
3. [Prime-Euclid normalization bridge](../PRIME_EUCLID_SHELL_ALIGNMENT_PROTOCOL.md)
4. [Primitive Euclid formula-family sweep](../PRIMITIVE_EUCLID_BRANCH_SWEEP_PROTOCOL.md)
5. [Shell / prime-branch interpretation](../SHELL_PRIME_BRANCH_INTERACTION_NOTE.md)
6. [Witnessed shell composition / candidate circle branch](../SHELL_COMPOSITION_BRANCH_NOTE.md)
7. [Composition calibration and input-availability boundary](../SHELL_COMPOSITION_20260920.analysis.md)

## Tools And Software Dependencies

- [`moo/circle_probe.py`](../../../moo/circle_probe.py) supplies exact rational
  unit-shell and Pythagorean filters.
- [`moo/circle_square_probe.py`](../../../moo/circle_square_probe.py) imports
  the circle and prime-shell feature machinery.
- [`moo/primitive_euclid_branch_sweep.py`](../../../moo/primitive_euclid_branch_sweep.py)
  imports circle-square reporting helpers and performs the formula-family
  follow-up.
- [`moo/prime_shell_features.py`](../../../moo/prime_shell_features.py) supplies shared
  normalization and factor fields.
- [`moo/branch_lineage.py`](../../../moo/branch_lineage.py) is the separate inspection
  tool required by the branch-lineage protocol; the sweep does not import it.
- [`moo/shell_composition_probe.py`](../../../moo/shell_composition_probe.py)
  separately audits ordered source, composition, and target witness bundles.
  It imports shared read-only graph utilities, not the sorted-leg selector.

This is a real implementation dependency chain, unlike several merely
conceptual reading sequences elsewhere in the repository.

Focused contracts are
[`tests/test_moo_circle_probe.py`](../../../tests/test_moo_circle_probe.py),
[`tests/test_moo_circle_square_probe.py`](../../../tests/test_moo_circle_square_probe.py),
[`tests/test_primitive_euclid_branch_sweep.py`](../../../tests/test_primitive_euclid_branch_sweep.py),
[`tests/test_prime_shell_features.py`](../../../tests/test_prime_shell_features.py), and
[`tests/test_branch_lineage.py`](../../../tests/test_branch_lineage.py).
The composition contract is
[`tests/test_moo_shell_composition_probe.py`](../../../tests/test_moo_shell_composition_probe.py).

## Retained Evidence

The [node-profile integration](../../../docs/software/NODE_PROFILES.md) exposes the
existing literal square/shell criteria, integer-encoded rational squares,
source-specific normalization certificates and fixed composition lineage in
one inspection path. Its [coverage map](../../PROFILE_COVERAGE.md) and
[U576 re-audit](../results/2026-11-04-node-profiles-v3/report.json) preserve the
distinction between mathematical membership and named graph support.

The [2026-09-11 ratio-branch search](../SHELL_SQUARE_RATIO_BRANCH_NOTE.md)
adds an exact rational parameter selector and a retained factor/quotient motif
audit over then-preserved U300/U850/U1000 corpora, with narrow U80 as a retention
control. It found earlier certificates explained completely by operand size;
it does not promote a new circle or unexplained branch-ordering law.

The [equal-area continuation](../CIRCLE_SQUARE_AREA_BRIDGE_20260911.analysis.md)
uses independently specified Euclidean area, exact polygon/grid bounds, and
a strict precursor audit. It distinguishes a certified approximation path
from exact hits, which are absent for nonzero rational circle/square lengths.

The [circle/square area account](../../../docs/examples/PI_FOURTH_ORDER_EXAMPLE.md)
explains the equal-area question, its connection to area under a curve, and
the conditional fourth-order interpretation for readers of the main account.
Its [editorial extract](../../../docs/examples/evidence/pi_fourth_order_example_20261107.json)
preserves the first two complete polygon certificates and supplementary tau
encodings. It adds no native-circle, completed-constant, or projection-advantage
claim to this program.

The [2026-10-01 inspection comparison](../AREA_INSPECTION_BRANCH_20261001.analysis.md)
adds integer certificates for rational-square area comparisons, compares exact
and rounded polygon bounds with grid covers, and proposes a witness-indexed
area-comparison boundary. Its method-independence proof assumes external area
and shrinking bounds. Only U160 witness records are observed; larger cost
checkpoints are predictions. Equal-area ellipses show why this boundary does
not define a circle-specific native branch.

The [2026-09-20 composition audit](../SHELL_COMPOSITION_20260920.analysis.md)
distinguishes witnessed component construction from a direct output-shell
proof, and keeps signed/zero operand blockers explicit. Its
[frozen design](../SHELL_COMPOSITION_20260920.pre.md) could not read the absent
historical SQLite files. An explicit
[input amendment](../SHELL_COMPOSITION_20260920.amendment.md) instead fixes new
current-generator calibration fields. Their
[manifest](../results/2026-09-20-shell-composition-current-manifest-v1.json) and
[report](../results/2026-09-20-shell-composition-current-v1.json) preserve that
distinction. These inputs do not replace the historical corpora.

The [geometry file-level evidence index](../../../docs/evidence/geometry.md)
enumerates the preregistrations, reports, analyses, and partial file families.
Several historical reports name source corpora that are no longer present and
record tool hashes that differ from the current sources. For those runs, the
retained JSON reports are the surviving exact machine witnesses and are not
currently reproducible from their original inputs. Any SQLite inputs that do
survive are governed by the
[corpus inventory](../../experiments/CORPUS_INVENTORY.md).

## Current Disposition

- Exact shell membership and rational normalization are established report
  fields.
- Component co-presence is report machinery, not a branch-lineage result.
- Prime factors and Euclid parameters are external descriptors until they
  survive timing, construction, and matched controls.
- Complete, partial, and absent formula-family rows are all first-class
  outcomes.
- No single bounded corpus establishes a general branch-ordering law.
- The composition group acts on normalized ordered values. Sorting legs loses
  information needed for composition; quotient equality does not merge witness
  histories. A completed circle and a metric remain additional constructions.

## Allowed And Forbidden Language

Allowed: exact rational shell candidate; component visibility; retained square
provenance; bounded formula-family coverage; candidate branch interaction.

Forbidden: Modulus of One defines the Euclidean circle; a Pythagorean identity is itself a
Modulus of One branch; primes explain shell structure without graph controls.

## Next Admissible Work

Continue only with preregistered ancestry or timing tests over preserved corpora
and matched absent/partial/complete controls. Stop or weaken the branch reading
if formula membership explains the signal without retained construction
lineage.

The fixed composition calibration is complete; do not enlarge it to seek a
timing residual after its operand-size predictions pass. A further claim that
Modulus of One privileges this relation needs a new design comparing alternative witnessed
relations, such as fixed weighted sums of two squares. A signed operand field
would require an explicit foundational/implementation decision, not a probe
shortcut.

## Historical Interpretation

The [2026 realignment example](../../../archive/reorganizations/20261107/MOO_REALIGNMENT_NOTE.md#geometry-reading)
preserves the earlier U80/U480 distinction between a value arriving and its
shell or branch witnesses being retained. It is a dated reading of those
corpora; current claims use this program and the [research protocol](../../../docs/protocols/research-programs.md).
