# MKM-EF-001 — Test Results

**Component:** Event Frequency Model — `MKM-EF-001` (governance record v1.1.0)
**Scope:** Unit and property-wiring test evidence for the frequency layer
(`src/models/frequency/`) and its integration into gauge, property and
commercial PRS pricing.
**Result:** **325 tests passed, 0 failed** · **99.67% line coverage**
(908 statements, 3 missed) · Python 3.13, `pytest`.
**Date:** 2026-07-28.

---

## 1. Summary

| | |
|---|---|
| Tests passed | **325 / 325** |
| Failures | 0 |
| Line coverage (`models.frequency`) | **99.67%** |
| Test modules | 16 |

Every module the model added in Stages 1–6 carries its own suite; the loss,
event-loss-table, rate-process and sensitivity modules are at 100% line coverage.

## 2. Coverage by test module

| Module | Tests | Covers |
|---|---|---|
| `test_pot.py` | 34 | peaks-over-threshold extraction, declustering, threshold search |
| `test_weights.py` | 38 | population weights, catalogue coverage |
| `test_families.py` | 30 | Poisson / Negative-Binomial fit and calibrated selection |
| `test_ylt.py` | 33 | year-loss sampler and the closed-form reconciliation gate |
| `test_calibrate.py` | 24 | calibration orchestration, fallback, provenance |
| `test_events.py` | 22 | event aggregation, identity, hours-clause grouping |
| `test_rate_process.py` | 20 | constant / trend rate processes, term structure |
| `test_sensitivity.py` | 20 | rate, distributional and λ-uncertainty sensitivity |
| `test_losses.py` | 19 | loss-weighted YLT, AEP/OEP |
| `test_frame.py` | 14 | event frame, identifier resolution |
| `test_persist.py` | 14 | rate persistence and exact round-trip |
| `test_rate.py` | 13 | exceedance-rate estimation |
| `test_subject_losses.py` | 13 | loss adapter, coverage-scaling centralisation |
| `test_elt.py` | 10 | event loss table construction and export |
| `test_wind_lambda.py` | 9 | per-peril wind λ, decoupled-wind opt-in |
| `test_roundtrip.py` | 5 | serialisation golden-master |

## 3. Key properties under test (self-tests, not just line coverage)

- **Reconciliation gate.** The Monte Carlo year simulation is checked against its
  exact closed form `1 − exp(−λp)` on every run; tests pin that the deviation is
  within sampling standard errors and that the z-score statistic is itself
  calibrated (`test_ylt.py`).
- **Coverage-scaling trap closed.** The event loss table scales λ by catalogue
  coverage while the sampler does not; a test asserts the two paths agree so the
  units cannot drift (`test_subject_losses.py`).
- **Calibrated family selection.** The Negative-Binomial false-positive rate on
  genuine Poisson counts is held below the configured significance while real
  over-dispersion is still caught (`test_families.py`).
- **Behaviour-preserving seams.** The non-stationary term structure, decoupled
  wind and monetary-loss uplift each reduce to the prior behaviour by default,
  asserted directly (`test_rate_process.py`, `test_wind_lambda.py`,
  `test_subject_losses.py`).
- **Exact serialisation.** `rate_from_dict(rate_to_dict(r)) == r`, and a partial
  provenance record raises rather than defaulting (`test_persist.py`,
  `test_roundtrip.py`).

## 4. Scope and honesty

This is **unit and integration-wiring** evidence: it demonstrates that the code
implements its specification and that the numerical machinery is internally
exact. It is **not** back-testing or independent validation — the model's
outputs are not compared against observed flood frequencies, because the
catchment is synthetic and λ is unvalidated (see the model's limitations and the
λ sensitivity analysis). Those remain outstanding (validation questions VQ-002,
VQ-008, VQ-009).

---

*Reproduce: `pytest tests/models/frequency/ --cov=models.frequency` in the
PhysicalRisk repository.*
