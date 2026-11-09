# Prime Probes

> Program status: scoped exploratory agenda with uneven tool maturity and no
> frozen program-level result.

## Exact Question

Do prime, factorization, exponent, or return-corridor families exhibit
construction timing, witness, or neighborhood structure beyond their classical
value definitions and matched controls?

## Relation To The Core

Prime and congruence properties are external labels until they are read through
the strict graph. Exponentiation and modular arithmetic are not new Modulus of One runtime
operators in these probes.

## Status By Scope

| Scope | Evidence layer | Claim status | Tool status | Result status | Result scope |
| --- | --- | --- | --- | --- | --- |
| Fermat Little probe design | `external_probe` | `lead` | `maintained` | `active` | Implemented tool and focused test; historical example corpus absent; no saved report |
| Fermat-prime probe design | `external_probe` | `lead` | `maintained` | `active` | Implemented tool; historical example corpus absent; no saved report or focused test |
| Factor-profile and conjecture agenda | `external_probe` | `lead` | none | `active` | Proposed tool absent; no program-level result |
| Conditional prime-harmonics question | `external_probe` | `lead` | none | `active` | Source and Abel-summation obligations unresolved |

## Conceptual Dependencies And Reading Order

1. [Prime factors and conjecture agenda](../PRIME_FACTOR_AND_CONJECTURE_PROBES_NOTE.md)
2. [Fermat Little return corridor](../FERMAT_LITTLE_PROBE_NOTE.md)
3. [Fermat prime non-collapse](../FERMAT_PRIME_PROBE_NOTE.md)
4. [Prime harmonics](../PRIME_HARMONICS_NOTE.md)

## Tool Status

- [`moo/fermat_little_probe.py`](../../../moo/fermat_little_probe.py) and
  [`tests/test_fermat_little_probe.py`](../../../tests/test_fermat_little_probe.py) are
  implemented.
- [`moo/fermat_prime_probe.py`](../../../moo/fermat_prime_probe.py) is implemented, but
  it does not currently have a focused test.
- `prime_factor_profile.py` is named as a proposed build target but does not
  currently exist.
- Prime harmonics has no implemented Modulus of One tool and depends on an untracked
  "Axioms 1-21" source plus an unmet Abel-summation obligation.

The implemented Fermat probes are sibling tools, not stages of one pipeline.

Neither Fermat note has a retained machine report. Both record example commands
against the now-absent April 2026 smoke corpus, so they preserve probe designs
and bounded expectations rather than currently re-auditable corpus results.

## Current Disposition

- Fermat-style probes are graph inspection designs, not proof attempts or
  current corpus results.
- Small-corpus visibility and absent exponentiation edges limit current
  interpretation.
- The factor/conjecture note remains an agenda rather than a result.
- Prime harmonics is sufficiently scoped to remain here, but its conclusions
  stay conditional while its axiom source and analytic obligation are missing.

## Allowed And Forbidden Language

Allowed: external target corridor; bounded visibility observation; planned
factor-profile tool; conditional harmonic lens.

Forbidden: Modulus of One proves Fermat, Goldbach, twin-prime, or other classical
conjectures; a planned tool is runnable; the conditional harmonics note is a
project theorem.

## Next Admissible Work

First add focused contracts for the implemented Fermat-prime probe. Then either
implement and test the smallest factor-profile comparison with matched
composite controls, or resolve the missing prime-harmonics sources and proof
obligation before making that branch operational. Stop any value-only probe
that does not return discriminating construction evidence.
