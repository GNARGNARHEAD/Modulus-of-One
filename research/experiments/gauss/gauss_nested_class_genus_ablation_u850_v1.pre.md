# Gauss Nested Class/Genus Ablation: Preregistration

> Experiment ID: `gauss_nested_class_genus_ablation_u850_v1`
>
> Status: design frozen before creation or inspection of the confirmatory U850
> corpus.
>
> Evidence layer: exact external quadratic-form lens over read-only strict-stage
> MoO graph corpora.

## Purpose

This is a nested class/genus control, not a strict factorial experiment.  Every
proper class belongs to one genus, so class and genus are not independent
factors.  The experiment separates four progressively weaker objects:

```text
oriented form witness and exact composition
-> represented integer and class-support set
-> label-free scalar-node construction neighborhood
-> quotient residue, ending in the singleton Z/1Z residue
```

The experiment must not claim that the bare residue modulo one contains form,
class, genus, orientation, or composition information.  Its purpose is to
locate the layer at which each distinction is lost and to test whether native
MoO graph information adds anything beyond scalar arithmetic and externally
attached labels.

## Frozen Families

All forms use the modern convention `a*x^2+b*x*y+c*y^2`.

### Calibration: Delta = -20

```text
A  exponent 0  [1, 0, 5]
B  exponent 1  [2, 2, 3]
class group C2
genera: {A}, {B}
```

### Forced scalar null: Delta = -23

```text
A      exponent 0  [1,  1, 6]
B      exponent 1  [2,  1, 3]
B_inv  exponent 2  [2, -1, 3]
class group C3
one genus: {A, B, B_inv}
```

The exact involution `(x,y) -> (x,-y)` maps the complete `B` fibre to the
complete `B_inv` fibre.  Their value memberships, representation counts, and
proper-orbit counts must therefore agree at every bound.  Any scalar-node
method that distinguishes their oriented class labels is a leakage failure.

### Nested genus/class control: Delta = -56

```text
A      exponent 0  [1,  0, 14]
G      exponent 1  [3,  2,  5]
G2     exponent 2  [2,  0,  7]
G_inv  exponent 3  [3, -2,  5]
class group C4
genera: {A, G2}, {G, G_inv}
```

This family supplies both a within-genus contrast `A` versus `G2` and an
across-genus contrast.  The exact involution `(x,y) -> (x,-y)` must make `G`
and `G_inv` scalar-identical.

The configured class tables are classical external inputs.  The probe will
independently derive a reduced-form product table using exact proper
equivalence searches and direct Dirichlet composition where its coprimality
condition holds.  A declared cyclic lookup table is not sufficient evidence.
Witness-value product closure is a separate, weaker audit and must not be
called a bilinear witness-composition map.

## Frozen Hypotheses

```text
H0 bare quotient:
  Z/1Z has one residue and no recoverable class or genus distinction.

H1 classical genus:
  discriminant-sensitive congruence features may recover coarse genus.

H2 graph-conditioned genus:
  label-free, form-independent MoO node features may improve held-out genus
  prediction beyond the strongest frozen scalar baseline.

H3 class modulo inversion:
  within one genus, label-free node features may improve held-out recovery of
  the proper-class support modulo C ~ C^-1.

H4 oriented inverse class:
  oriented inverse classes with identical scalar support are not identifiable
  from a scalar node.  Any positive oriented recovery is leakage.

H5 composition:
  externally labelled composition is calibration only.  It becomes a
  graph-native candidate only if held-out target channels are predicted from
  form-independent scalar relation neighborhoods without class labels,
  coefficients, coordinates, or form-selected edge subsets.
```

H5 graph-native prediction is not required for this version.  If it is not
implemented, the report must say so explicitly rather than treating scalar
multiplication-edge coverage as class evidence.

## Experimental Units And Targets

The units must remain distinct:

1. proper representation orbit for exact external fibre accounting;
2. integer node for graph-native recovery;
3. deduplicated scalar multiplication relation for scalar composition shadows;
4. decorated composition record for classical calibration only.

Signed witnesses and proper-automorphism copies are not independent samples.

For an integer `n`, the exact primitive class-support set is

```text
S_Delta(n) = {proper classes with a primitive representation of n}.
```

Primary genus samples satisfy:

```text
gcd(n, |Delta|) = 1
n has a primitive representation
all primitive representing classes belong to one genus
```

Primary class samples are reduced modulo inversion.  Ambiguous support sets
containing more than one inversion orbit are excluded from single-label class
metrics and reported separately.  At `Delta=-56`, `A` versus `G2` is the
primary within-genus contrast.  At `Delta=-23`, `{A}` versus `{B,B_inv}` is a
secondary one-genus class-support contrast; values supported by both are
excluded.

## Frozen Development And Holdout Split

```text
development corpus:
  out/experiments/pascal_edge_probe_u300.sqlite
  SHA256 3D23228EA2A1926918D49BBDC89D9F7BF85ECFE4729EC96C7BD6E9F97E54B097
  values 1..200

confirmatory corpus, not yet created or inspected at design freeze:
  out/experiments/gauss/strict_stage_u850_holdout_v1.sqlite
  strict positive-spine stages through U850
  values 201..800
```

Every node is observed at a fixed exposure horizon of 50 stages after its
positive-spine confirmation:

```text
feature_cutoff(n) = n + 50
```

The U850 endpoint is therefore sufficient for the final value 800.  No integer
value belongs to both development and holdout.  The confirmatory corpus hash is
recorded only after generation.

Replication checkpoints are `N=100`, `N=200`, `N=400`, and `N=800`.  The first
two are developmental; values `201..400` and `201..800` are confirmatory.
The `N=100` and `N=200` records are exact support, exclusion, and class-count
diagnostics only; no held-out prediction score is manufactured inside the
development range.  The two predictive checkpoints are exactly `201..400`
and `201..800` against the fixed `1..200` training split.

## Frozen Evidence Ablations

| Level | Available information | Interpretation |
|---|---|---|
| A0 | form, class, genus, coefficients, coordinates, exact form product | decorated calibration |
| A1 | text class name removed but coefficients or coordinates retained | deliberate leakage sentinel |
| A2 | integer and frozen scalar arithmetic features | strongest scalar baseline |
| A3 | complete node neighborhood selected only by integer `n` | graph-native test |
| A4 | quotient residue and deduplicated bare quotient topology | erasure endpoint |

A3 excludes form ID, class ID, genus ID, coefficients, coordinates, signs,
orbit IDs, form-selected evaluation edges, composition targets, file order, and
identifiers encoding the answer.

## Frozen Features And Classifier

The scalar baseline contains:

```text
log(1+n)
divisor count
number of distinct prime factors
total prime-exponent count
squarefree indicator
gcd(n, |Delta|)
one-hot residues for every positive divisor of |Delta|
the complete prime-exponent vector over all primes <= 800
```

The topology-only feature block contains no numeric value or residue:

```text
confirmation lag
incoming and outgoing edge counts
incoming and outgoing operation histograms for +, -, *, /
distinct incoming operand count
distinct outgoing result count
```

All graph features are computed using the full form-independent neighborhood
available by `feature_cutoff(n)`.  The scalar-plus-graph model concatenates the
two blocks.

The sole classifier is training-set z-scoring followed by nearest class
centroid in Euclidean distance.  Ties resolve first to the training majority
and then to lexical class order.  The score is macro balanced accuracy.

The primary graph statistic is

```text
heldout_balanced_accuracy(scalar_plus_graph)
- heldout_balanced_accuracy(scalar_only).
```

The topology-only score is descriptive and cannot establish incremental graph
value by itself.

## Frozen Quotient Ladder

For each discriminant, use

```text
{1} union {positive divisors of |Delta|} union {809}.
```

`809 > 800`, so the last map is injective on the tested integers.  For every
modulus, report exact bucket sizes, occupied residues, genus/residue mutual
information, and conditional class/residue mutual information where defined.
Train-to-holdout majority-by-residue balanced accuracy is reported only when
at least one holdout residue was observed in training.  The injective `m=809`
endpoint is descriptive because its development and holdout residues are
disjoint.

Required endpoints:

```text
m=1:
  one occupied residue
  zero genus mutual information
  zero conditional class mutual information

m=809:
  integer identity is retained on the tested range
  inverse orientation remains non-identifiable from the integer
```

Character phases are auxiliary class labels and must never be interpreted as
extra residues in `Z/1Z`.

## Frozen Nulls And Promotion Rule

Use a deterministic seed derived from the experiment ID.  Run 10,000 label
permutations within each reported target for a one-sided null comparison.  Also
report:

- constant-bucket modulus-one control;
- exact inverse-pair observable-collision ceiling;
- graph-label absence and database-hash invariance;
- scalar multiplication-edge saturation as calibration, never selection;
- ambiguous target counts;
- a deliberate A1 leakage sentinel;
- an operation-block permutation control when sample size permits.

A graph-conditioned effect requires all of:

```text
held-out balanced-accuracy lift >= 0.05
one-sided permutation p <= 0.01 after Holm correction
positive lift at both confirmatory checkpoints
no banned feature or form-conditioned edge selection
no conflict with an exact identifiability ceiling
```

Three confirmatory families of tests are corrected together: genus,
within-genus class modulo inversion, and any implemented composition-recovery
test.

## Frozen Interpretation Matrix

| Outcome | Allowed reading |
|---|---|
| A0 succeeds; A2/A3 and A4 at `m=1` are null | externally supplied bookkeeping survives the decorated projection |
| A1 succeeds; A3 fails | coefficients or coordinates carried the answer |
| residues recover genus; graph adds nothing | classical congruence/genus recovery only |
| A3 improves genus but not within-genus class | graph-conditioned coarse arithmetic signal |
| A3 improves the `Delta=-56` `A` versus `G2` contrast | candidate graph-conditioned proper-class support |
| scalar A3 distinguishes `B` from `B_inv` or `G` from `G_inv` | leakage or split error; reject |
| multiplication edges are present only because the corpus is saturated | calibration, not graph selection |
| a signal is reproduced by the destructive operation-block ablation | compatible with exposure/degree structure; never composition evidence |
| any class/genus information is assigned to the bare `m=1` quotient | conceptual or implementation error; reject |

The expected honest result is exact A0 calibration, ordinary scalar genus
signal, little or no A3 lift beyond the scalar baseline, and exact A4 erasure.
That expected result is frozen before the holdout corpus exists.

## Pre-Holdout Design-Audit Amendments

These amendments close ambiguities found by a read-only design audit.  They
were fixed before the confirmatory corpus was created or inspected and take
precedence over any less-specific language above.

### Exact confirmatory corpus construction

Use Python `3.12.13` and exactly:

```text
python strict_stage_moo.py
  --db out/experiments/gauss/strict_stage_u850_holdout_v1.sqlite
  --max-stage 850
  --max-abs-p 1000000000
  --max-abs-q 850
  --max-abs-value 1000000000
  --commit-every 25
  --summary out/experiments/gauss/strict_stage_u850_holdout_v1.summary.json
  --quiet
```

Frozen generator inputs:

```text
strict_stage_moo.py SHA256
  E91574E0DF7C573EC6E36D56DFBE5C779DA632108D631EC22B4D2196ACFC099B
moo_graph_corpus.py SHA256
  5F863DC297B3B2136FA76835D13067AE41206A150885DD37BA2BB49DA5532C1F
```

The confirmed-edge exemption remains enabled.  The edge domain is all four
ordered strict operations `+,-,*,/` over confirmed positive-spine operands;
bounded outputs are controlled by the fixed numerator, denominator, and value
limits above.  The corpus must pass the standard strict-alignment audit.

Before any confirmatory metric is accepted, every frozen node-feature vector
for values `1..200`, evaluated at its own inclusive cutoff `n+50`, must agree
exactly between the U300 development corpus and the U850 corpus.  Failure is a
corpus-comparability stop, not an experimental outcome.

### Exact prediction tasks

Every classifier is fitted separately for one discriminant and one target.
There is no pooled-discriminant model.

All classifier samples, including the within-genus and one-genus class-support
contrasts, are restricted to `gcd(n, |Delta|)=1`.  This keeps every predictive
comparison on the same unramified coprime slice; class-support exclusions below
are applied after that common filter.

Primary tests entering the promotion rule and Holm correction:

```text
T1 Delta=-56 genus:
  genus {A,G2} versus genus {G,G_inv}; all qualified single-genus nodes

T2 Delta=-56 within-genus class modulo inversion:
  {A} versus {G2}; exclude support {A,G2}
```

Secondary descriptive tests, excluded from promotion and Holm correction:

```text
Delta=-23 class support modulo inversion:
  {A} versus {B,B_inv}; exclude support {A,B,B_inv}

Delta=-20:
  calibration only because class and genus coincide

oriented inverse pairs:
  exact collision/non-identifiability audit only; never a positive classifier
```

`Delta=-23` has one genus, so no genus classifier, genus permutation, or genus
balanced accuracy is defined for it.  A scored task requires at least four
training and four test samples in every label at the stated checkpoint.  If a
label is absent or below this minimum, that checkpoint is `insufficient_data`;
it cannot support promotion.  The final `201..800` checkpoint is mandatory.

### Exact graph-feature semantics

For node `n`, include edges with `stage <= n+50` (inclusive).

```text
incoming:
  every retained directed edge occurrence whose result node is n

outgoing:
  every retained directed edge occurrence in which n is the left or right
  operand, counted once when n occupies both positions

operation histograms:
  directed occurrence counts for +,-,*,/ with no commutative normalization

distinct incoming operands:
  cardinality of the union of left and right input node IDs

distinct outgoing results:
  cardinality of result node IDs, including rational, zero, and negative
  results retained by the corpus
```

No duplicate edge occurrence is removed.  `confirmation_lag` is
`confirmed_stage-first_stage`.  A missing or not-yet-confirmed positive node is
a hard sample error.  Training zero-variance features are standardized to
zero.  A missing training class or empty centroid is a hard scoring error.

### Exact scalar baseline and residue prediction

The complete prime-exponent vector uses the fixed ordered list of every prime
`<=800`; it encodes exact integer factorization on the tested domain.  Together
with the divisor/residue features above, this is the strongest frozen scalar
baseline.  Any positive graph result may claim only incremental predictive
value over this specified baseline, never information unavailable to scalar
arithmetic in principle.

For non-injective quotient moduli, majority-by-residue is trained on the
development split; an unseen holdout residue falls back to the overall
training majority, then lexical order.  If no holdout residue was seen during
training, accuracy is marked `descriptive_unseen_endpoint`.  Thus `m=809` has
no predictive score.

### Exact permutation and shuffle mechanics

The primary p-value is an exposure-matched graph-block permutation, not an
unstratified label permutation.  For T1 and T2 separately:

1. Keep scalar rows and labels fixed.
2. Within development and holdout separately, group rows by
   `(floor(log2(n)), floor(log2(1+incoming+outgoing)))`.  Confirmation lag
   remains inside the permuted graph block; it is not part of the matching
   key.
3. Permute complete graph-feature blocks among rows inside each stratum using
   10,000 deterministic permutations.
4. Refit both centroids and record the permuted
   `(scalar_plus_graph)-scalar` holdout balanced-accuracy lift.
5. Use `(1 + count(null_lift >= observed_lift)) / 10001`.

Report the fraction of rows belonging to nonsingleton strata.  If it is below
`0.50` in either split, the p-value is `insufficient_movable_rows` and cannot
support promotion.  Holm correction applies exactly to the valid T1 and T2
p-values.

An additional 1,000-run operation-histogram null is always performed for T1
and T2.  For incoming and outgoing directions separately, and separately
within the fixed development and holdout splits, expand the five reported
operation buckets `+,-,*,/,other` into one split-wide multiset of operation
labels.  Shuffle that multiset with the deterministic experiment RNG, then
repartition it in original row order using each row's original directional
edge total.  Thus every row keeps its incoming and outgoing totals and each
split keeps its global operation-bucket totals, while operation identities are
reassigned among nodes.  Lag, total degree, distinct-neighbor counts, scalar
features, and labels remain fixed.  If
the graph lift survives this null, the result may be described only as an
exposure/degree correlation, not a Gauss-composition signal.

### Composition status in this version

Composition is external calibration only.  Exact bilinear polynomial
identities, complete bounded target-fibre membership, and an independent
reduced-form product table will be verified, but no graph-native composition
prediction enters H5, promotion, or Holm correction.

For the independent table, enumerate proper substitutions
`[[p,q],[r,s]] in SL2(Z)` by increasing maximum-entry norm, then entry L1 norm,
then lexicographic order.  Transform both source forms with matrices whose
entries have absolute value at most `2`; retain exactly the concordant pairs
with a common middle coefficient and coprime leading coefficients.  Their
direct Dirichlet product is

```text
[a1*a2, b, (b*b-Delta)/(4*a1*a2)].
```

Choose the candidate minimizing
`(|b|,a1*a2,a1+a2,left_coefficients,right_coefficients,left_matrix,right_matrix)`.
Search matrices with entries of absolute value at most `4`, in the same fixed
order, for an exact proper equivalence from that product to one configured
reduced form.  Failure to derive every configured class product within either
complete frozen search is a hard stop.  The search does not inspect either
graph corpus.

### Final pre-holdout statistical audit amendment

A final implementation audit found and removed two channels that were not part
of the intended A2/A3 comparison.  This amendment was made while the U850
corpus and its summary were still absent.

First, modulus `809` is an injective descriptive endpoint in the quotient
ladder only.  It is not a classifier feature.  The scalar model receives
one-hot residues for the positive divisors of `|Delta|` and the complete prime
exponent vector through 800, exactly as specified above.  Including 809 would
have added an identity-like 809-column block and changed the weighting of the
nearest-centroid model.

Second, `primitive_class_support_count` is externally derived form information
and therefore cannot appear in the graph-block matching key.  The exact final
key is the two-coordinate key printed above: integer-size bin and observed
total-degree bin.  Development-only diagnostics showed that this retains
nonsingleton movable-row fractions above the frozen 0.50 threshold for both
primary tasks while removing the form-derived conditioner.

In addition to the frozen nonsingleton-row fraction, the report must show:

```text
potential rows in strata containing multiple labels and graph blocks
expected cross-label transfers under a uniform within-stratum permutation
expected transfers that change both label association and graph block
```

A primary p-value is non-estimable if the last expected fraction is zero in
either split.  These permutations are a coarse exposure-matched sensitivity
null.  Because graph features are deterministic functions of the integer and
the bins are coarse, they are not represented as proving literal conditional
exchangeability.

The Holm family remains the two frozen primary tests.  If a primary p-value is
non-estimable, it receives `p=1` for multiplicity accounting and cannot be
promoted; the correction family is never adaptively reduced.

Generation provenance is recorded immediately after the frozen corpus command
in
`out/experiments/gauss/strict_stage_u850_holdout_v1.provenance.json`.  It must
record Python `3.12.13`, the exact generator argument vector, both frozen
generator hashes, and the resulting database and summary hashes.  The analysis
hard-stops unless that sidecar, the SQLite metadata, and the summary agree.

The analysis stack itself is frozen before U850 is generated in
`out/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.analysis_manifest.json`.
That manifest contains Python `3.12.13`, the exact analysis CLI arguments, and
SHA-256 hashes for this preregistration, `moo_quadratic_form_nested_probe.py`,
`moo_quadratic_form_recovery.py`, `moo_quadratic_form_nested_math.py`,
`moo_quadratic_form_probe.py`, `moo_research_utils.py`, and the transitive
`moo_graph_invariants.py` and `rational_baselines.py` helpers used by the scalar
graph inspector.
The confirmatory command is exactly:

```text
python moo_quadratic_form_nested_probe.py
  --write out/experiments/gauss/gauss_nested_class_genus_ablation_u850_v1.json
  --pretty
  --quiet
  --with-checksums
```

Any source, argument, or manifest mismatch is a hard stop rather than a result.

The operation-histogram shuffle is likewise a destructive descriptive
ablation: it preserves the stated marginal counts but need not correspond to a
realizable graph.  It can diagnose dependence on operation identities versus
degree/exposure, but it is not promoted to a graph-generative inferential null.
No binary threshold is registered for this control, and it does not veto the
separate H2/H3 graph-increment promotion rule.  It always vetoes interpreting
the result as graph-native Gauss composition, which is unimplemented here in
any case.

## Claim Boundary

This experiment can establish exact finite representation fibres, inverse-pair
scalar identity, externally validated reduced-form composition, genus/class
ablation behavior, graph-conditioned correlations on the frozen holdout, and
the exact singleton modulus-one endpoint.

It cannot establish that the strict runtime contains quadratic forms or class
groups as native objects, that a scalar edge is a form-composition witness,
that `Z/1Z` contains hidden class structure, or that any finite graph
correlation is a theorem about class groups, theta series, zeta functions, or
their zeros.
