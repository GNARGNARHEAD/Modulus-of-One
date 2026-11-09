# Research Lenses

> Status: operational scrutiny layer for graph-first Modulus of One research.
>
> A research lens is admissible only if it compiles down to a graph query, a
> measurable score, a null/control comparison, or an explicit speculative-only
> lead. Names from outside mathematics are labels for scrutiny, not authority.
> External researchers and traditions are peripheral framing lenses; they do
> not enter Modulus of One's core grammar. See [FRAMING_LENSES_NOTE.md](../../research/FRAMING_LENSES_NOTE.md).
>
> Lifecycle navigation now begins at [[README.md](../../research/README.md)](../../research/README.md)
> and the local program cards. This file remains the detailed 17-entry
> transitional registry. The program-card lifecycle protocol and complete
> ownership ledger are recorded in
> [[research-programs.md](../protocols/research-programs.md)](../protocols/research-programs.md).
> The lens-design contract below has not been transferred or retired by that
> routing pass and remains authoritative.

## Claim Discipline

Modulus of One claims must carry two independent labels:

```text
evidence_layer: strict | exploratory | external_probe
claim_status:  observation | lead | candidate | strict_result | rejected
```

Use `evidence_layer` to name where the evidence came from.

Use `claim_status` to name how strong the current claim is.

This prevents a useful exploratory observation from being discarded while also
preventing it from being promoted into strict-stage Modulus of One by wording alone.

Claim status is not tool or experiment lifecycle. Where a lens has a saved
versioned result, record these separately:

```text
tool_status: maintained | historical
result_status: active | completed_version | frozen_version | stopped_design
result_scope: the exact version, claim, or design to which that status applies
```

A negative result, rejected subclaim, or stopped design does not retire a
maintained instrument. Conversely, retaining a tool does not reopen a rejected
claim or alter a frozen stop rule.

## Required Lens Fields

Every new lens should fill these fields before it becomes part of the active
research workflow:

```text
name:
evidence_layer:
claim_status:
tool_status:              # when the lens has executable infrastructure
result_status:            # when a versioned experiment has a disposition
result_scope:             # prevents a result status from closing a whole lens
provocative_hypothesis:
false_positive_guarded_against:
graph_native_observable:
query_or_report:
metric:
null_model_or_control:
promotion_criteria:
kill_criteria:
allowed_claim_language:
disallowed_claim_language:
```

If any field cannot be filled, the lens stays a note, not an active research
tool.

Order-4 projected-object proposals must also fill the certificate in
[order4-projection.md](../protocols/order4-projection.md) before they gain credibility.

Graph-native metric language should use [graph-invariants.md](../protocols/graph-invariants.md) unless a
probe explicitly defines a stricter metric.

## Registered Lenses

### Rational Baseline Lens

```text
evidence_layer: strict
claim_status: observation
provocative_hypothesis:
  Some Modulus of One nodes may appear early or receive many construction witnesses
  relative to classical rational-complexity baselines.
false_positive_guarded_against:
  Mistaking ordinary low-denominator or standard rational-tree visibility for
  Modulus of One-native structure.
graph_native_observable:
  node first_stage, confirmation status, incoming edge occurrences, witness
  diversity, operation histogram, and shared-input neighborhood.
query_or_report:
  python3 -m moo.research_report --db <corpus.sqlite> --node 34/21 --pretty
  python3 -m moo.research_report --db <corpus.sqlite> --corpus-baselines --pretty
metric:
  denominator height, component height, continued-fraction length,
  Stern-Brocot depth, Farey neighbors, derivation events, normalized witnesses,
  peer-group percentile, residual from peer median.
null_model_or_control:
  denominator, component height, or Stern-Brocot-depth peer groups.
promotion_criteria:
  A node-level observation can become a candidate only after it survives a
  corpus-wide ranking with explicit corpus parameters and peer controls.
kill_criteria:
  The same scoring declares many denominator-matched ordinary rationals equally
  strong, or the lead disappears under nearby corpus bounds.
allowed_claim_language:
  "34/21 has these construction witnesses and these rational baseline features
  in this strict-stage corpus."
disallowed_claim_language:
  "34/21 is unusual" from a single-node dossier.
```

### Temporal Confirmation Lens

```text
evidence_layer: strict
claim_status: lead
provocative_hypothesis:
  Some speculative-first integers may reveal useful paths before the core loop
  later confirms them.
false_positive_guarded_against:
  Treating later confirmation as proof that the earlier speculative path was
  important.
graph_native_observable:
  nodes with first_stage < confirmed_stage, plus incoming construction edges.
query_or_report:
  python3 -m moo.graph_query --db <corpus.sqlite> --confirmations --pretty
  python3 -m moo.research_report --db <corpus.sqlite> --corpus-baselines \
    --kind confirmed --rank-by confirmation_lag --control component_height --pretty
metric:
  confirmation_lag, incoming witness diversity, operation histogram.
null_model_or_control:
  component-height or denominator-matched confirmed nodes.
promotion_criteria:
  Confirmation lag is accompanied by repeated or diverse strict construction
  witnesses and persists under nearby corpus bounds.
kill_criteria:
  The lag is only a predictable consequence of the core integer index or bounds.
allowed_claim_language:
  "This node was first recorded speculatively and later confirmed by the core
  loop."
disallowed_claim_language:
  "The speculative construction predicted the integer" without a control.
```

### Operation Ecology Lens

```text
evidence_layer: strict
claim_status: observation
provocative_hypothesis:
  The balance of +, -, *, and / around a node may reveal construction roles
  that value-only reports hide.
false_positive_guarded_against:
  Calling a node central solely because it has many raw edge occurrences.
graph_native_observable:
  incoming and outgoing operation histograms, normalized witness counts, and
  shared-input neighborhoods.
query_or_report:
  python3 -m moo.research_report --db <corpus.sqlite> --node <p/q> --pretty
metric:
  operation histogram, normalized witness count, outgoing participation.
null_model_or_control:
  denominator or component-height peer groups, with commutative duplicates
  reported separately from directed witnesses.
promotion_criteria:
  Operation imbalance persists in corpus-wide rankings and is visible in exact
  construction edges.
kill_criteria:
  The imbalance is explained by operation ordering, commutative duplication, or
  bounds.
allowed_claim_language:
  "This node's incoming construction events are division-heavy in this corpus."
disallowed_claim_language:
  "This operation signature has mathematical meaning" before controls.
```

### Gauss Congruence / Modulus-One Control

```text
evidence_layer: external_probe
claim_status: observation
provocative_hypothesis:
  A projection that erases every integer value distinction can test whether
  Modulus of One preserves auditable witness, operation, stage, and confirmation data
  independently of residue value.
false_positive_guarded_against:
  Treating the forced one-node/one-loop quotient as discovered structure;
  conflating integer congruence, rational phase, complex unit modulus, and
  Ref(1); importing Gauss as core authority.
graph_native_observable:
  integer source-node residue fibers; exact retained edge occurrences;
  operation-decorated signatures; first and confirmed stages; result status at
  event/checkpoint; the first operator fan.
query_or_report:
  python3 -m moo.congruence_quotient_probe --db <corpus.sqlite> \
    --moduli 1,2,3,4,5,6,8,12 --pretty
  Governance and primary-source boundary:
  research/number_theory/GAUSS_CONGRUENCE_AND_MODULUS_ONE_LENS_NOTE.md
metric:
  occupied residue count, node collapse count, conserved edge occurrences,
  operation signatures, status-by-operation counts, completeness, partition
  refinement, and CRT neutrality of the modulus-one coordinate.
null_model_or_control:
  bare one-bucket topology, m>1 ladder, confirmed-positive induced domain,
  stage checkpoints, and future injective-modulus / balanced-color controls.
promotion_criteria:
  The lens stays external. A stronger claim requires a preregistered retained-
  fiber statistic that predicts held-out graph structure beyond stage,
  operation, size, and random-color controls.
kill_criteria:
  Edge occurrences or statuses are deduplicated, rational results are silently
  folded into integer congruence, completeness failures are hidden, or all
  apparent signal reduces to the forced singleton quotient topology.
allowed_claim_language:
  "Modulo one erases all integer value distinctions in the named source domain,
  while the decorated projection retains these exact source witnesses."
disallowed_claim_language:
  "Gauss proves Modulus of One," "0 and 1 are identical in the source graph," or "rich
  arithmetic lives inside Z/1Z."
```

### Phase Metric Collapse / Triangle-Inequality Lens

```text
evidence_layer: external_probe
claim_status: observation
tool_status: maintained
result_status: completed_version
result_scope: U40 v1; no promoted special-fibre effect
provocative_hypothesis:
  Distinct rational source nodes that become zero-distance observations in
  Q/Z may retain systematic graph-visible construction differences.
false_positive_guarded_against:
  Treating a forced quotient identity as discovered structure; confusing
  Z/1Z, Q/Z, unit complex modulus, and Ref(1); calling a bounded pair search a
  global maximum; or calling an external return orbit a runtime path.
graph_native_observable:
  checkpoint-scoped node ids and values, first and confirmed stages, incoming
  edge references, operation counts, direct inputs, shared-input-result
  neighborhoods, and recorded +1 translation witnesses.
query_or_report:
  python3 -m moo.phase_metric_probe --db <corpus.sqlite> \
    --max-denominator 12 --max-phase-classes 16 \
    --pairs-per-phase 4 --pretty
  Interpretation:
  research/geometry/PHASE_METRIC_COLLAPSE_NOTE.md
metric:
  exact shortest-arc phase distance inherited from R/Z; source absolute
  distance; routed triangle slack; direct-input and shared-input-neighborhood
  Jaccard distance; operation-signature total variation.
null_model_or_control:
  integer Z/1Z one-class control, source-line triangle slack, deterministic
  different-phase controls matched by anchor/denominator/integer lift,
  multiplication non-descent, and fixed exact metric calibrations.
promotion_criteria:
  A preregistered checkpoint and corpus sweep shows a repeatable paired effect
  against exposure-matched controls, with explicit coverage and held-out or
  permutation controls.
kill_criteria:
  The effect stays comparable to matched controls, disappears under nearby
  bounds, depends on identity-fibre domination, or requires speculative
  rational nodes to act as operands without a runtime change.
allowed_claim_language:
  "These distinct source nodes have zero exact phase distance and retain these
  named graph differences at checkpoint U."
disallowed_claim_language:
  "Modulus of One has constructed the circle," "zero phase distance means equal source
  nodes," or "the corpus discovered the triangle inequality."
```

### Quadratic Shell Lens

```text
evidence_layer: strict
claim_status: observation
provocative_hypothesis:
  Modulus of One may expose rational point families satisfying exact quadratic invariants
  before any Euclidean circle language is earned.
false_positive_guarded_against:
  Smuggling in geometry, angle, circumference, area, or pi by calling
  x*x + y*y = r*r a circle too early.
graph_native_observable:
  rational component nodes x, y, r; exact Q(x, y) = r*r check; first stages;
  confirmation status; construction witnesses; operation histograms; sign
  symmetry coverage.
query_or_report:
  python3 -m moo.circle_probe --db <corpus.sqlite> --unit-circle --node 3/4 --pretty
  python3 -m moo.circle_probe --db <corpus.sqlite> --unit-circle --pretty
  python3 -m moo.circle_probe --db <corpus.sqlite> --pythagorean --pretty
metric:
  complete component-node count, max component first stage, component witness
  count, denominator distribution, sign-symmetry coverage.
null_model_or_control:
  denominator-matched rational controls, construction-cost matched controls,
  placebo quadratic forms, graph shuffles, and bound-sensitivity checks.
promotion_criteria:
  Quadratic-shell candidates show stable graph-visible structure across strict
  corpora and beat matched controls. Later orbit language requires exact
  Q-preserving transformations.
kill_criteria:
  Matched placebo curves score similarly, the effect disappears under small
  corpus-bound changes, or only hand-picked nodes support the observation.
allowed_claim_language:
  "Modulus of One has rational quadratic-shell candidates with graph-visible construction
  evidence."
disallowed_claim_language:
  "Modulus of One defines the circle" or "Modulus of One constructs pi."
```

### Quadratic-Form Class-Channel Lens

```text
evidence_layer: external_probe
evidence_scope: exact quadratic-form algebra over a strict graph ablation
claim_status: observation
tool_status: maintained
result_status: frozen_version
result_scope: U850 v1; no promoted lift for the tested feature/model
provocative_hypothesis:
  The scalar projection of a representation can hide form-class and bilinear
  composition information, while an exact class-character transform can
  recover multiplicative channels lost by inspecting one form in isolation.
false_positive_guarded_against:
  Calling any coefficient mixture multiplicative after a short scan, treating
  scalar nodes as form representations, or inferring RH from theta positivity
  and a Riemann-like functional equation.
graph_native_observable:
  scalar nodes for represented values and coordinates; their confirmation and
  operand-readiness status; retained directed occurrences of 2*3->6 and
  2*5->10. Form coefficients, representation fibres, pair operators, class
  labels, and character transforms remain exact external annotations.
query_or_report:
  python3 -m moo.quadratic_form_probe --db <corpus.sqlite> --max-n 200 --pretty
  python3 -m moo.quadratic_form_nested_probe --write
    research/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.json
    --pretty --quiet --with-checksums
  Governance and derivations are in
  research/number_theory/QUADRATIC_FORMS_CLASS_CHANNEL_LENS_NOTE.md.
metric:
  complete signed ordered representation counts; holes; bilinear identity
  checks; finite coprime multiplicativity defects; scalar-node coverage; exact
  edge occurrence counts for named product witnesses; held-out scalar-versus-
  graph balanced accuracy; matched graph-block nulls; quotient mutual
  information; inverse-pair collision ceilings.
null_model_or_control:
  D=-4 single-class norm control, the two separate D=-20 form ledgers, the
  noncharacter mixture a_A+2*a_B, brute-force enumeration cross-checks, and
  changed finite bounds; D=-23 inverse classes; D=-56 nested genus/class
  targets; modulus-one constant bucket; frozen U850 holdout.
promotion_criteria:
  The exact class structure and character transform remain correct under
  independent derivation and wider finite checks. Any graph increment must
  meet the preregistered lift, replication, matched-null, Holm, leakage, and
  identifiability gates. The companion theta/Weil layer must preserve these
  class components while adding an independently computed arithmetic
  functional and rigorous density/error arguments.
kill_criteria:
  Representation searches are coordinate-cropped, missing coefficients are
  treated as zero, form classes are assigned from scalar values alone, placebo
  mixtures pass equally, or analytic conclusions appear without the missing
  theorems and error bounds.
allowed_claim_language:
  "The D=-20 principal representation ledger has an exact 2*3=6
  multiplicativity defect, while both C2 character channels pass the same
  finite exact test through the named bound." "In the frozen U850 ablation,
  scalar congruence recovers D=-56 genus while the tested label-free graph block
  adds no promoted class/genus information, and the bare modulus-one quotient
  retains none."
disallowed_claim_language:
  "Modulus of One contains a form class group," "the finite scan proves an Euler product,"
  or "quadratic forms prove the Riemann hypothesis."
```

### Theta-Weil Cross-Term Calibration

```text
evidence_layer: external_probe
evidence_scope: exact external prefix plus external analytic calibration
claim_status: observation
tool_status: maintained
result_status: active
result_scope: finite calibration with six analytic obligations open
provocative_hypothesis:
  Dimensional collapse in the Weil criterion can be made operationally visible:
  replacing rho -> 1-conj(rho) by same-point pairing deletes precisely the
  displacement that distinguishes an off-line orbit from a critical-line one.
false_positive_guarded_against:
  Attaching raw constant 1 to normalized class coefficients, inferring a theta
  transform from symmetric samples, treating a coefficient Gram as Weil
  positivity, placing supplied points on the critical line and calling the
  forced PSD result evidence, or deleting matrix cross terms.
graph_native_observable:
  scalar source nodes, confirmation and operand-readiness status, retained
  arithmetic construction edges, and neighborhoods. Form coefficients, theta
  weights, Mellin transforms, zero points, and Weil matrices remain external.
query_or_report:
  python3 -m moo.theta_weil_probe --db <corpus.sqlite> --max-n 200 --pretty
  Governance and derivations are in
  research/number_theory/THETA_WEIL_CONSTRUCTIVE_OBLIGATIONS_NOTE.md.
metric:
  exact formal coefficients and constants; analytic theta-tail envelopes;
  t versus 1/t residuals with separate roundoff guards; full finite involutive
  matrix inertia; same-point and diagonal-only placebo outcomes; Hermitian and
  eigenpair residuals; explicit missing-obligation ledger.
null_model_or_control:
  D=-4 classical transform, D=-20 n=2 and n=6 exact cancellation fixtures,
  C2 basis-covariance fixture, synthetic critical-line pairs, a complete
  synthetic off-line quartet, exact 2J versus 2I involution fixture, and
  coefficient kernels that are labelled PSD by construction.
promotion_criteria:
  Compute the same finite Hermitian matrix independently from the arithmetic
  explicit formula with interval-enclosed pole, prime-power, gamma, and
  archimedean contributions; then prove a nested constrained test family dense
  in a theorem-sufficient topology with a valid all-dimensions limit.
kill_criteria:
  Incomplete zero orbits are accepted, same-point pairing replaces the Weil
  involution, cross terms are dropped, truncation and roundoff are conflated,
  or finite PSD is promoted beyond the displayed span.
allowed_claim_language:
  "The full finite involutive matrix detects the synthetic off-line quartet,
  while same-point and diagonal-only placebos erase that displacement."
disallowed_claim_language:
  "The graph computes a Weil form," "known-line PSD supports RH," or "this
  finite calibration proves the Riemann hypothesis."
```

### Euler Reciprocal Mass Lens

```text
evidence_layer: external_probe
claim_status: lead
provocative_hypothesis:
  Euler-style reciprocal-square and finite-product structures may give Modulus of One a
  graph-native route to pi shadows without decimal target-hunting.
false_positive_guarded_against:
  Treating zeta(2), sine products, or Euler products as internal Modulus of One objects
  before Modulus of One has exact finite rational structures and controls.
graph_native_observable:
  nodes for 1/n^2, partial sums S_N, finite prime products, denominator growth,
  construction witnesses, return-to-zero corridors, and prime/composite
  neighborhood differences.
query_or_report:
  moo/series_probe.py reports exact finite geometric calibration rows, zeta(2)
  partial sums, finite Euler products, local geometric factor truncations, and
  the distinction between rational endpoint presence and actual recurrence
  edges. Governance remains in
  research/euler/EULER_RECIPROCAL_MASS_AND_CIRCLE_LENS_NOTE.md.
  This v2 report covers the observation-layer primary families; the controls
  listed below remain outstanding.
metric:
  partial-sum construction cost, denominator growth, witness diversity,
  prime-product versus sum agreement, prime/composite residuals.
null_model_or_control:
  matched composite controls, denominator/height controls, constant placebos,
  and held-out strict corpora.
promotion_criteria:
  Exact finite reciprocal-mass/product structures show stable graph behavior
  beyond controls before any pi-shadow language is used.
kill_criteria:
  Raw approximation explains the observation, many unrelated constants score
  similarly, or graph shuffles preserve the signal.
allowed_claim_language:
  "Modulus of One can inspect exact finite reciprocal-square term and partial-sum nodes
  when they are present in this strict corpus."
disallowed_claim_language:
  "Modulus of One constructs pi from zeta(2)."
```

### Zeta Critical-Strip External Probe

```text
evidence_layer: external_probe
evidence_scope: external complex analysis over strict graph sources
claim_status: observation
tool_status: maintained
result_status: completed_version
result_scope: v1 numerical calibration; no zero certification
provocative_hypothesis:
  The exact quarter-turn phase and graph-audited integer source scaffold may
  support a disciplined external view of weighted complex cancellation at
  zeta inputs without extending the runtime number domain.
false_positive_guarded_against:
  Renaming rational 1/4 as a runtime complex operand, using the ordinary zeta
  series or Euler product in the critical strip, or calling a small binary64
  residual an exact or graph-witnessed zero.
graph_native_observable:
  quarter-phase source nodes and direct quotient edges, positive integer source
  nodes, rational reciprocal precursors, sampled interior Pascal recurrence edges,
  confirmation status, outgoing-edge aperture, and corpus censoring.
query_or_report:
  moo/zeta_critical_probe.py evaluates a finite external Hasse/eta
  approximation, keeps exact rational finite weights separate from external
  complex powers, and reports independent two-step cutoff stability,
  conditioning, conjugate consistency, a horizontal/vertical local control
  cross, zeta(2), trivial-zero, pole, and removable eta-bridge guards.
  A reference-zero coordinate is caller-supplied rather than verified by the
  probe. Governance remains in
  research/euler/EULER_RECIPROCAL_MASS_AND_CIRCLE_LENS_NOTE.md.
metric:
  target residual, finite-cutoff change, finite cancellation ratio, nearby
  control separation, source-node/edge coverage, and coefficient-edge aperture.
null_model_or_control:
  s=2 calibration, s=-2 trivial-zero calibration, s=1 pole guard, conjugate
  consistency, a removable eta-bridge singularity guard, predeclared horizontal
  and vertical neighbors, multiple cutoffs, and held-out corpora.
promotion_criteria:
  Stable calibration across cutoffs and corpora may promote the probe as a
  useful analysis lens; it cannot promote a numerical point to a certified zero
  without rigorous interval and zero-counting machinery.
kill_criteria:
  Residuals fail cutoff stability, nearby controls collapse similarly, source
  coverage is mistaken for complex construction, or binary64 roundoff dominates.
allowed_claim_language:
  "The external finite approximation shows controlled weighted cancellation
  over graph-audited integer and rational sources."
disallowed_claim_language:
  "Modulus of One constructs zeta(s), proves this zero, or proves the Riemann hypothesis."
```

### Zeta Cancellation-Arrival Probe

```text
evidence_layer: external_probe
evidence_scope: external complex analysis conditioned on strict graph arrival
claim_status: observation
tool_status: maintained
result_status: completed_version
result_scope: v1 negative graph-specific result
provocative_hypothesis:
  The strict positive-spine source order may expose a distinctive finite
  cancellation trajectory at a caller-supplied zeta reference coordinate.
false_positive_guarded_against:
  Treating speculative node presence as operand availability, calling a fixed-K
  source reveal a stage-u zeta approximation, or attributing ordinary n-prefix
  behavior to additional graph topology.
graph_native_observable:
  integer first stage, dynamic confirmation stage, direct reciprocal-edge stage,
  reciprocal reinforcement stages, corpus horizon, and retention aperture.
query_or_report:
  moo/zeta_arrival_probe.py holds the terminal Hasse basis fixed, reveals terms
  under named stage masks, and compares the aligned path with speculative,
  nearby-coordinate, height-grid, and endpoint-preserving local-permutation
  controls.
metric:
  normalized radius, active mass, remaining cancellation capacity, resolved
  inward/outward steps, longest inward streak, radial efficiency, persistent
  local-control separation, and empirical permutation tail rank.
null_model_or_control:
  sigma/t local cross, fixed-v1 critical-line heights, adjacent-block source
  permutations, cutoff stability, narrow/wide aperture comparison, and matched
  corpus-prefix reproduction. These controls were fixed after exploratory
  calibration, not preregistered.
promotion_criteria:
  An empirical trajectory reading requires a complete validated strict-stage
  prefix, a stable near-zero finite-K endpoint, operational-mask reconstruction,
  configured radial thresholds, local-control separation, and sufficient
  resolution plus an extreme rank under endpoint-preserving block perturbations.
kill_criteria:
  Reject effects confined to node presence, graph-specific language when the
  aligned schedule is merely n=1..K, tail behavior shared by controls, or any
  matched-prefix corpus discrepancy.
allowed_claim_language:
  "The natural positive-spine source order gives unusually monotone external
  finite cancellation at this caller-supplied reference coordinate."
disallowed_claim_language:
  "The graph constructs zeta, discovers or certifies a zero, or supplies
  evidence for the Riemann hypothesis."
```

### Centered Reciprocal-Shell Interaction Lens

```text
evidence_layer: external_probe
evidence_scope: exact external geometry over strict graph sources
claim_status: candidate
tool_status: maintained
result_status: active
result_scope: candidate geometry; global zeta-zero symmetry subclaim rejected
provocative_hypothesis:
  The exact t <-> 1/t rational-shell pairing may expose repeatable reciprocal
  and component aperture in strict graph corpora.
false_positive_guarded_against:
  Identifying the centered u-shell with the critical-line w-shell; identifying
  rational-coordinate shell points with roots of unity; calling centered
  inversion the C4 rotation; inferring a transformation edge from node
  co-presence; or treating coordinate symmetry as the proposed zeta-zero
  symmetry.
graph_native_observable:
  In the current strict positive-spine corpus: rational parameter and
  shell-component nodes, stages, confirmation and
  operand-readiness status, direct reciprocal/construction edge occurrences,
  and bounded corpus censoring. Complex points and Mobius actions stay external.
query_or_report:
  python3 -m moo.zeta_centered_inversion_probe \
    --db out/experiments/circle_as_one_u80.sqlite \
    --t '14.134725141734693' --hasse-terms 64 \
    --shell-max-integer 8 --near-zero-tolerance 1e-10 \
    --stability-tolerance 1e-12 \
    --target-label first_nontrivial_zero_coordinate --pretty
  Governance and derivations are in
  research/euler/CENTERED_RECIPROCAL_SHELL_LENS_NOTE.md.
metric:
  Exact identity pass rate, paired parameter/component coverage, direct-witness
  coverage, stage/status aperture, Hasse residual, and cutoff stability.
null_model_or_control:
  normalized-w-plane C4 rotation versus D4 reflection, u-shell versus
  punctured w-critical-line loci,
  U(Q) versus rational-phase domains, fixed points, involution round-trip,
  functional reflection, multiple Hasse cutoffs, and the analytic accumulation
  obstruction.
promotion_criteria:
  A preregistered multi-corpus sweep finds repeated, control-separated
  graph-visible reciprocal/component interaction under a named graph predicate
  with holdout behavior. This would strengthen the interaction lens, not by
  itself establish a runtime complex transformation.
kill_criteria:
  Co-presence is the only graph support, matched reciprocal controls behave the
  same, the effect vanishes under nearby corpus bounds, or a zeta zero-set
  invariance claim is required. The zeta-inversion subclaim is already rejected.
allowed_claim_language:
  "This external centered involution pairs these exact rational shell
  parameters and exposes this bounded strict-graph aperture."
disallowed_claim_language:
  "Modulus of One contains this Mobius map," "the inversion is the C4 cycle," "zeta has
  this proposed zero-set symmetry," "this supports RH," or "this is a formal branch."
```

The visible action on `{1,i,-1,-i}` in the normalized external `w` plane is a
`D4` reflection, although the named real determinant-one homogeneous
representative satisfies `S^2=-I`. The
order-four lift is representative/state data, not an automatic projective
runtime object. The proposed global zeta-zero symmetry is impossible because it
would send unbounded critical-line zero heights to distinct zeros accumulating
at the analytic point `s=1/2`. Precomposition `zeta(I_R(s))` moves that
accumulation to an essential singularity and is a new representation, not a
zero-set symmetry of zeta.

### Order-4 Projection Lens

```text
evidence_layer: external_probe
claim_status: lead
provocative_hypothesis:
  Stable strict graph families may support non-operational projected anchors
  such as non-rational constants, circle-like invariants, or asymptotic
  organizing points.
false_positive_guarded_against:
  Defining the projected object after seeing an exciting pattern, mistaking
  approximation accuracy for structure, or treating an analysis anchor as a
  runtime object.
graph_native_observable:
  exact source-family nodes and edges, source stages and corpus bounds,
  construction witnesses, neighborhoods, operation signatures, confirmation
  status, and held-out graph structure.
query_or_report:
  docs/protocols/order4-projection.md defines the projection certificate. Concrete
  reports must name a source family, projection rule, primary metric, controls,
  holdout, prediction, and kill rule.
metric:
  prediction lift over matched controls, projection stability, held-out error
  reduction, recurrence/compression improvement, control-adjusted witness
  diversity, or organization of held-out neighborhoods.
null_model_or_control:
  denominator-matched, first-stage-matched, construction-cost-matched,
  continued-fraction controls, placebo constants, placebo invariants, graph
  shuffles, and operation-label shuffles as appropriate.
promotion_criteria:
  Avoid the word promotion here. An Order-4 anchor gains credibility only when
  it predicts or organizes held-out strict graph structure better than controls.
kill_criteria:
  The anchor drifts under stage growth, many unrelated anchors fit equally
  well, the source family was target-selected after the fact, baselines explain
  the signal, shuffles preserve the effect, or the projection has no held-out
  predictive value.
allowed_claim_language:
  "This is an Order-4 projected inspection anchor inferred from this exact
  graph family by this projection rule."
disallowed_claim_language:
  "This Order-4 anchor is a certainty, runtime node, operand, theorem, or
  completed object inside strict Modulus of One."
```

### Stage Dynamics Lens

```text
evidence_layer: strict
claim_status: observation
provocative_hypothesis:
  Strict-stage Modulus of One may show reproducible deterministic stage dynamics:
  persistence, accumulation, threshold shifts, recurrence, and divergence.
false_positive_guarded_against:
  Calling ordinary graph growth, low-denominator bias, or raw edge popularity
  "chaos", "attractors", or "bifurcations".
graph_native_observable:
  stage snapshots G_U; node/edge growth; operation distribution; denominator
  bands; confirmation transitions; top-k construction-gathering nodes;
  edge-local symbolic motif distributions.
query_or_report:
  research/dynamics/DYNAMICS_TEST_PROTOCOL.md defines planned report shapes.
  Future tool target:
  python3 moo_dynamics_probe.py --stage-persistence --checkpoints 10,20,40,60,80
metric:
  top-k checkpoint appearances, witness diversity, operation diversity,
  confirmation lag, stage-window symbol frequency, neighborhood Jaccard
  divergence.
null_model_or_control:
  denominator-matched peers, first-stage-matched peers, stage-size null,
  exposure controls, operation-label shuffle, graph shuffle, held-out strict
  corpora.
promotion_criteria:
  A candidate survives preregistered thresholds, saved report review, matched
  controls, and at least one robustness check.
kill_criteria:
  Total corpus growth explains the observation, matched peers behave similarly,
  small bound changes erase it, or raw edge count is the only support.
allowed_claim_language:
  "persistent accumulation candidate" and "parameter-threshold shift candidate".
disallowed_claim_language:
  "Modulus of One is chaotic", "Modulus of One has attractors", "Modulus of One has bifurcations", "Modulus of One has
  Lyapunov exponents", or "Modulus of One has strange attractors".
```

## Design-Limited And Exploratory Lenses

These entries have different lifecycle states. Each keeps its own evidence
layer and claim status; none can make a strict-stage claim until the relevant
criteria and strict graph checks are met.

### Phase Operator-Descent / Provenance-Transport Lens

```text
evidence_layer: external_probe
evidence_scope: exact external Q/Z algebra over a read-only strict graph
claim_status: observation
tool_status: maintained
result_status: stopped_design
result_scope: U40/U80 design after insufficient aperture
provocative_hypothesis:
  After conditioning on exact denominator q, strict provenance may order
  externally attached division-result residues toward extra proper-prefix
  returns in ordinary additive C_q.
false_positive_guarded_against:
  Treating Q/Z as a rational ring, treating speculative results as operands,
  using same-stage SQLite insertion order as time, or mistaking ordinary step
  composition / stage / exposure / hub structure for transport.
graph_native_observable:
  exact division occurrences, source stages, confirmed shared-input witnesses,
  result nodes, exposure, and shared-input hub degree.
query_or_report:
  moo/phase_transport_probe.py over the checksum-bound U40 primary and the
  separately preregistered U80 aperture-resolution follow-up; see
  research/geometry/PHASE_OPERATOR_DESCENT_AND_TRANSPORT_NOTE.md.
metric:
  q-balanced proper-prefix return rate on held-out, occurrence-disjoint,
  strictly stage-increasing provenance paths.
null_model_or_control:
  exact-step permutations and exact-(q,stage,exposure,hub)-stratified residue
  shuffles, both compared with exact Fraction arithmetic.
promotion_criteria:
  A separately frozen corpus must first satisfy every unchanged aperture gate,
  then exceed the mean and 99th percentile of both controls.
kill_criteria:
  The preregistered U80 follow-up remained below the 25 percent mutable-position
  gate, so the current path/null design stops; do not tune bins, path length,
  thresholds, seed, or corpus after seeing these results.
allowed_claim_language:
  "Addition/subtraction descend exactly; retained integer division is a finite
  torsion-preimage relation; both frozen transport runs were underpowered for
  their strict stratified null."
disallowed_claim_language:
  "Modulus of One has circle motion," "rational phases operate in aligned Modulus of One," "the
  transport hypothesis was retained," or "the transport hypothesis was killed."
```

### Motif / Hinge Lens

```text
evidence_layer: exploratory
claim_status: lead
provocative_hypothesis:
  Some rational values act as construction hinges in bounded exploratory
  closure reports.
false_positive_guarded_against:
  Promoting exploratory closure artifacts into aligned Modulus of One claims.
graph_native_observable:
  repeated operation motifs, high-output neighborhoods, alternate witnesses.
query_or_report:
  historical motif reports first; strict reproduction must use
  moo/research_report.py or moo/graph_query.py over a strict graph corpus.
metric:
  motif membership, report-level hub count, strict witness count if reproduced.
null_model_or_control:
  denominator-matched controls and nearby corpus-bound sensitivity checks.
promotion_criteria:
  The same value or motif has a strict-stage graph observable with explicit
  controls.
kill_criteria:
  The hinge disappears when speculative operands are disallowed.
allowed_claim_language:
  "-4/3 is an exploratory hinge under the named closure mode and bounds."
disallowed_claim_language:
  "Modulus of One discovers -4/3 as a strict organizing center" without strict evidence.
```

### Aperture Lens

```text
evidence_layer: exploratory
claim_status: lead
provocative_hypothesis:
  Some constructions leave and return to a bounded value region in ways that
  expose lower-aperture witnesses.
false_positive_guarded_against:
  Mistaking final value admissibility for path admissibility.
graph_native_observable:
  first witness path, maximum intermediate aperture, alternate witnesses.
query_or_report:
  historical aperture reports until strict ancestry extraction exists.
metric:
  first witness aperture, alternate lower-aperture witness count.
null_model_or_control:
  denominator-matched and value-range controls.
promotion_criteria:
  Strict graph ancestry can reproduce the witness behavior without speculative
  operands.
kill_criteria:
  The effect depends on exploratory reuse of speculative nodes.
allowed_claim_language:
  "This is an aperture lead from exploratory closure."
disallowed_claim_language:
  "This is a strict Modulus of One cost" before strict ancestry support.
```

## Delayed Lenses

Fourier, Hodge, spectral, circle-method, constant-recognition, PSLQ, RIES, and
OEIS lenses stay delayed until a strict graph report produces candidate chains
or edge-flow data large enough to justify them.

Their allowed role is:

```text
strict graph -> candidate structure -> external scrutiny
```

not:

```text
external name -> rational search -> Modulus of One claim
```
