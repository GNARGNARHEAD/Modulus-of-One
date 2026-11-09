# Public Snapshot And Provenance

This repository is the public edition of **Modulus of One**, prepared on
9 November 2026 from the reviewed working tree. It begins with fresh Git
history. The original working repository and its development history remain
private and preserved.

## What Is Included

The snapshot includes the philosophical account, definitions, code, tests,
worked examples, research notes, saved reports, figures, preregistrations,
negative results, and clearly labelled historical reviews. The main account
leads through branch inspection and its consequences; the detailed research
retains its individual assumptions and claim boundaries.

Raw conversations, local SQLite databases, scratch outputs, environment files,
editor or agent state, and the original Git history are excluded. Historical
source identifiers remain provenance records; they do not imply that an input
is downloadable. The [corpus inventory](../research/experiments/CORPUS_INVENTORY.md)
distinguishes historical sources from fresh demonstrations.

## Privacy-Redacted Research Copies

Some historical notes and reports contain local user-directory paths or the
author's first name. In this public edition, identifying directory components
are replaced with `USER`, and personal author references use the public handle
`GNARGNARHEAD`. Such paths are historical context, not executable local paths.
The private source artifacts remain unmodified.

The [redaction manifest](evidence/public_snapshot_redactions_20261109.json)
lists every such derivative with its original and public SHA-256 hashes and
the kind of redaction. Numerical observations, witness identifiers, source
hashes recorded inside reports, and mathematical claims are preserved.

A redacted report is not byte-identical to its historical original. Embedded
hashes and historical byte-for-byte verification statements refer to the
original evidence identities. They have not been silently changed to certify
these derivative copies. If a historical workflow requires an exact original,
the public derivative does not satisfy that requirement. Current code guards
retain their original checks.

Current repository links and citation metadata point to this public edition.
The foundations note's opening history was aligned with the area-first account;
these editorial changes do not alter the construction rules.

## Running The Public Examples

The [development guide](software/DEVELOPMENT.md) gives the standard-library-only
test command and walkthrough. The [branch example](examples/BRANCH_INSPECTION.md),
[square comparison](examples/FOURTH_ORDER_EXAMPLE.md), and
[circle/area example](examples/PI_FOURTH_ORDER_EXAMPLE.md) provide commands for
fresh fields with their own node and edge identities.

These commands build new demonstrations. They do not silently reconstruct
missing historical inputs or transfer historical edge IDs to a fresh graph.
Historical navigation snapshots retain their original context; see the
[archive guide](../archive/superseded_maps/README.md).

## Author And Licenses

Public author credit is **GNARGNARHEAD**. Code is licensed under **MIT**;
writing, figures and research reports are licensed under **CC BY 4.0**, as
specified in the [license notice](../LICENSE.md). The privacy redactions do not
change those grants. Use the [citation metadata](../CITATION.cff) and identify
the public commit or snapshot examined.
