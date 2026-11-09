# Shell / square branch search: frozen design

Date: 2026-09-11

Evidence layers: external exact candidate rules and read-only strict graph
witness audits. This is a new experiment, not a rerun of phase transport.

## Question and provisional hit

The user wants a repeated relation that selects further shell/square hits and
reduces the search space. For this experiment a direct hit means positive
integers x <= y < r with retained x*x, y*y, r*r self-product edges and a
retained x*x + y*y -> r*r edge. It is a rational-shell proxy, not equal-area
circle squaring or a definition of the completed Euclidean circle.

## Candidate mechanism fixed before the new corpus scan

For the same triple, put u=r-x and v=r+x. Test the alternative witnessed
relation u*v=y*y, together with the retained r-x and r+x edges. Also inspect
the quotient collision u/y=y/v=t. All operations must have confirmed positive
integer operands at their saved edge stage. Fractions are inspected outputs,
never new operands.

External algebra makes the factor identity equivalent to the shell identity.
This is a known difference-of-squares factorization, not a proposed new
theorem or a blind discovery from data. The empirical questions are whether
these exact motifs are actually retained and whether they provide earlier
access than the direct square/addition motif.

Predictions for a complete positive-spine corpus with sufficiently wide output
retention:

- Direct motif first completes at U_(y*y).
- Factor motif first completes at U_(r+x).
- Quotient motif first completes at U_(r+x).
- Predicted missing motifs remain missing when their largest operand is beyond
  the stage. Node co-presence alone never counts as completion.

The comparison uses x as the smaller leg so this choice minimizes r+x over
the two leg orientations. It does not assert this is the optimal construction
among all possible certificates.

## Scope and partitions

- Enumerate all integer triples with radius r <= 500 by a blind pair sweep.
- Separately enumerate candidates via square product factors and via the
  classical rational parameter / Euclid rule; compare exact sets.
- Separate primitive shapes from scaled copies using gcd(x,y,r).
- Development aperture: preserved pascal_edge_probe_u300.sqlite, U300.
- Later-stage validation: preserved gauss/strict_stage_u850_holdout_v1.sqlite,
  U850. Report newly available motifs separately from U300 repeats.
- Further validation: preserved pascal_cubic_scale_u1000.sqlite, U1000.
- These are nested stage apertures, not independent random samples. None is
  untouched by earlier repository research; only this predicate and these
  stage predictions are fixed before the present audit.
- Include the preserved narrow circle_as_one_u80.sqlite as a retention control.

## Controls and rejection rules

- Compare measured completion stages with the explicit operand-size baseline.
  If the baseline explains all timing, do not claim a new MoO ordering law.
- Keep complete, partial, and absent motifs, including node-presence cases
  without the defining edges.
- For every positive triple inspect the nearby nonhit (x,y,r+1), within the
  same radius envelope. Its shell discrepancy and factor/ratio discrepancies
  must be detected; it must not pass the joint predicate.
- Reject prime-only radius membership if any primitive composite-radius case
  has the required witnesses. Prime labels are external descriptors.
- Do not infer a common logarithmic spiral from a selected parametrization.
- Compare a one-child recursive subfamily with the full primitive set; never
  claim a single chosen ray covers the entire family.
- Record all exact nodes and defining edges, confirmation status, missing-edge
  reasons, input hashes, tool/dependency hashes, and neighborhood commands.
- Open saved corpora read-only and verify their hashes remain unchanged.

## Useful outcome

A useful outcome can be an exact candidate selector with measurable search or
stage reduction, even when its algebra is classical. A stronger MoO-specific
discovery would require an effect beyond the fixed arithmetic and operand-size
controls. A negative result should identify the exact rejected claim.

The final report must distinguish complete direct hits, earlier factor/ratio
certificates, external predicted triples, and normalized rational points.
