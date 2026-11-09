# Gauss Quadratic Forms Through Modulus One: Design Freeze

> Experiment ID: `gauss_quadratic_forms_d20_u300_v1`
>
> Design frozen: 2026-08-28
>
> Status: post-feasibility, pre-artifact protocol. Exact feasibility counts were
> used to size and debug the report, so this is not a blind statistical
> preregistration. The interpretations, controls, and failure rules below were
> fixed before writing the named JSON artifact.

## Fixed Inputs

```text
corpus: out/experiments/pascal_edge_probe_u300.sqlite
corpus SHA-256: 3D23228EA2A1926918D49BBDC89D9F7BF85ECFE4729EC96C7BD6E9F97E54B097
form bound: N=200
graph evidence cutoff: U=200
composition event emission limit: 10000
probe schema: moo_quadratic_form_probe.v2
design-freeze tool SHA-256: 9849517FA788E4D59315B4900EE5A9A87B2189FD031AEE37BDDCAB0E30D515BE
```

The primary historical family is Gauss determinant `d_G=-5`, equivalently
modern discriminant `Delta=-20`:

```text
A=(1,0,5)_G=[1,0,5]       principal
B=(2,1,3)_G=[2,2,3]       nonprincipal
```

The one-class control is `x^2+y^2`, Gauss determinant `-1`, modern
discriminant `-4`.

## Fixed Projection

```text
signed integer-pair witness
-> proper-automorphism orbit
-> represented positive integer n
-> rho_1(n)=0 in Z/1Z.
```

Only `n` is quotiented in the primary analysis. Form ID, class, coordinates,
orbit, bilinear composition, and strict-graph references are retained as fibre
provenance. They are not residue coordinates.

The auxiliary sign-character label `-1 <-> 1/2 in Q/Z` is explicitly outside
this projection.

## Fixed Questions And Expected Outcomes

1. **Bare quotient.** Every represented integer must occupy residue zero. Its
   one-node operator-labelled topology must match a constant-bucket control.
   Any second residue is an implementation failure.
2. **Decorated fibre.** The exact class law `A*A=A`, `A*B=B`, `B*B=A` and the
   witness `B(1,0)B(0,1)=2*3=6=A(1,1)` should remain inspectable only as
   provenance above the singleton residue.
3. **Erasure falsifier.** Removing form/class/bilinear decorations must leave
   the scalar graph evidence and bare quotient unchanged. A surviving bare
   class distinction falsifies the interpretation.
4. **One-class control.** The `Delta=-4` and `Delta=-20` families must have the
   same bare modulus-one topology despite different decorated class data.
5. **Scalar-shadow calibration.** Exact evaluation and composition relations
   should be present in the `U=200` strict positive-spine prefix. Complete
   coverage is expected saturation and is not selective evidence for forms.
6. **Stage integrity.** No node or edge first appearing after stage 200 may
   support a `U=200` claim.
7. **Operand integrity.** Zero and signed coordinates may be annotations or
   results, but may not become speculative operands. For `x=-y`, retain
   `|x|-|y| -> 0` only in a coordinate-relation side ledger.

## Fixed Event Normalization

Representation fibres retain every signed ordered pair. Primary composition
events use proper-automorphism orbit representatives. Equal-class source pairs
are unordered; mixed-class events place `A` on the left. The report separately
counts every ordered signed-witness event so normalization cannot hide raw
multiplicity.

Each primary event must record source and target orbit IDs, raw bilinear output,
canonical target orbit, polynomial identity status, target-fibre membership,
scalar multiplication relation, and source/result residues modulo one.

## Fixed Metrics

- raw witness, proper-orbit, represented-integer, and residue counts;
- per-form value-set overlap and holes;
- arithmetic evaluation, coordinate rewrite, and relational-zero role counts;
- distinct ordered evaluation relations and commutative composition relations;
- missing relations, confirmation-at-edge status, and maximum evidence stage;
- normalized and raw signed composition counts by class signature;
- target-fibre and polynomial-identity failure counts;
- the `2*3=6` node/edge witness and its `0*0=0` quotient image;
- constant-bucket equality and one-class/two-class bare-topology equality.

## Kill Rules

The run is invalid if corpus alignment fails, a complete bounded fibre fails its
brute-force regression, automorphism orbits do not partition a fibre, a
bilinear identity fails, an output orbit is absent from its target fibre, a
reported positive-spine step uses zero, any required scalar relation is absent
at `U=200`, or the quotient has anything other than the sole residue zero.

The interpretation is killed—not rescued—if a purported class signal remains
after stripping the external decorations, if it depends on edges after stage
200, if it disappears after automorphism normalization, or if complete scalar
coverage is presented as selection rather than saturation.

## Promotion Boundary

This run may establish an exact finite decorated-collapse example. It may not
establish graph-native form classes, a general class-group theorem, an Euler
product, an analytic continuation, a functional equation, or a claim about
zeta zeros. A later promotion study should replicate across bounds and use a
second discriminant; modern `Delta=-23` is preferred because its inverse
nonprincipal proper classes share the same scalar value set.

## Pre-Artifact Reporting Amendment

An independent schema audit after the design freeze, but before the final JSON
artifact, required reporting-only changes. Arithmetic-DAG completeness is now
separate from coordinate-side completeness; ordered relation IDs,
commutative-normalized keys, and directed graph edge IDs are counted
separately; the eight relational-zero edges have an aggregate; node lifecycle
fields distinguish cutoff status from eventual full-corpus confirmation; and
division is explicitly excluded from the total `Z/1Z` ring signature.

No form, bound, hypothesis, expected outcome, metric source, control, kill rule,
or interpretation changed. The final implementation hash is:

```text
75F80ED39D14C962535D1A83A93B313236BD2E7153ED4A1C4581367D73F7C306
```

## Frozen Command

```text
python3 moo_quadratic_form_probe.py
  --db out/experiments/pascal_edge_probe_u300.sqlite
  --max-n 200
  --graph-stage-cutoff 200
  --edge-limit 8
  --composition-event-limit 10000
  --experiment-id gauss_quadratic_forms_d20_u300_v1
  --with-checksums
  --write out/experiments/gauss/gauss_quadratic_forms_d20_u300_v1.json
  --pretty
```
