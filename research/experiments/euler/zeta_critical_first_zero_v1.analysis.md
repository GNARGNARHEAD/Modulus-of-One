# First Critical-Line Reference Coordinate: U80 / U40-Wide Comparison

Date: 2026-08-28

Status: external numerical calibration over strict graph evidence; not a zero
certificate and not a runtime complex-number construction.

## Declared input and method

The caller-supplied reference coordinate is

```text
s = 0.5 + 14.134725141734693 i
t binary64 = 0x1.c44fab19b6621p+3
```

Both reports use 64 outer Hasse rows (`k=0..63`), a residual tolerance of
`1e-10`, an independent relative cutoff-stability tolerance of `1e-12`, and a
horizontal/vertical control displacement of `0.01`. The Hasse weights are exact
external `Fraction` values. Complex powers, accumulation, and the eta bridge are
external binary64 calculations.

The reference label is caller supplied. The probe does not independently look
up or certify the ordinate.

Saved reports:

- `zeta_critical_first_zero_u80_v1.json`
- `zeta_critical_first_zero_u40_wide_v1.json`

Both reports include corpus and tool SHA-256 checksums. Their shared tool hash is
`95c0010bcc4e48339ba83526ee2487259af990067f849cf6c67db0d9d3a961db`.

## Numerical result

The numerical layer is identical across the two corpora, as it should be:

| Reading | Value |
| --- | ---: |
| `abs(zeta(s))` | `2.1570095574950392e-15` |
| cutoff change, `K=56 -> 60` | `3.3822620033034757e-13` |
| cutoff change, `K=60 -> 64` | `2.3149187697142205e-14` |
| binary64 roundoff proxy | `9.279306448540272e-16` |
| minimum of four local-control residuals | `0.00789954791004124` |
| minimum-control / target-residual ratio | `3.662268385688137e12` |
| zeta(2) binary64 calibration error | `0.0` |
| zeta(-2) residual | `6.10026131920585e-14` |

The empirical term preflight, both terminal cutoff checks, the roundoff proxy,
the four-point local control cross, and the calibration suite all pass. The pole
at `s=1` and the removable eta-bridge singularity at
`s=1+2*pi*i/log(2)` are distinguished and guarded.

This supports only the following reading: the finite external approximation is
well resolved at this configured coordinate and cutoff. In both JSON reports,
`target_certified_zero` remains `false`.

## Graph comparison

| Graph evidence | U80, max value 4 | U40, max value 40 |
| --- | ---: | ---: |
| corpus nodes / edges | `3522 / 9559` | `1019 / 4139` |
| Hasse source integers present | `64 / 64` | `40 / 64` |
| source integers operand-ready | `64 / 64` | `40 / 64` |
| reciprocal precursor edges complete | `64 / 64` | `40 / 64` |
| quarter-turn incoming edges | `20` | `10` |
| quarter-turn outgoing edges | `0` | `0` |
| sampled interior Pascal recurrences complete | `5 / 28` | `25 / 28` |

The U40 corpus is stage-censored for source integers `41..64`; all 24 associated
reciprocal precursor relations are explicitly absent with
`candidate_stage_beyond_corpus` aperture readings. U80 exposes all 64 integer
and reciprocal source relations.

The Pascal contrast runs in the opposite direction because the corpora change
two variables. U80 is deeper but bounded to absolute value 4, while U40-wide is
shallower and bounded to absolute value 40. The wider value aperture retains
more ordinary positive-integer addition edges. This is a corpus-bound effect,
not zeta-specific evidence. The audit is only a named sample through Pascal row
8; Hasse row 63 would be required for full interior-recurrence coverage.

## What the quarter-turn contributes

Both corpora contain the direct edge `1 / 4 -> 1/4`. Externally,

```text
1/4 mod 1 -> exp(2*pi*i/4) = i
```

But the `1/4` node is speculative and has zero outgoing construction edges in
both corpora. Phase addition is therefore not a runtime operation. In
particular:

```text
external phase multiplication: 1/4 + 1/4 = 1/2 mod 1  <->  i*i = -1
core rational multiplication:   1/4 * 1/4 = 1/16
```

These are deliberately kept separate. The nearest rational phases attached to
sampled external Hasse terms are post-hoc visualizations; node presence is not a
construction witness for the complex phases.

## Boundary of the result

The experiment does not add `i`, logarithms, exponentials, complex addition,
analytic continuation, or zeta values to the MoO runtime. It does not use the
ordinary Dirichlet series or Euler product as convergent critical-strip
constructions. It supplies no interval error bound, argument-principle count,
Hardy-Z/Turing check, or exclusion of zeros off the critical line.

The useful result is narrower: the newly named quarter-turn can anchor an honest
external complex phase view, while the strict graph can independently disclose
which rational/integer source constructions are present, operand-ready,
stage-censored, or absent.
