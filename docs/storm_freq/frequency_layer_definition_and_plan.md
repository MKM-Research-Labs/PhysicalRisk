# PhysicalRisk Enhancement: Event Frequency Layer

**Document type:** Definition Document & Project Plan
**Component:** Hazard Frequency Model (new)
**Status:** Draft for review
**Date:** 2026-07-22
**Owner:** CSO, MKM Research Labs

---

## 1. Background and Problem Statement

### 1.1 Current state

The PhysicalRisk Monte Carlo simulator generates synthetic storm events and evaluates, at each river gauge, whether a given storm produces a flood. Insurance cost is currently priced as:

```
price ∝ (number of simulated storms that flood) / (total simulated storms)
```

This is a **conditional probability** — P(flood | storm) — and is dimensionless with respect to time.

### 1.2 The defect

The current metric conflates two distinct model components:

1. **Hazard frequency** — how often storms arrive at a location (events per year).
2. **Vulnerability / conditional response** — given a storm, whether the gauge floods.

Because the time dimension is absent, two gauges with identical P(flood | storm) receive identical prices even if one location experiences eight qualifying storms per year and the other experiences one. The true annualised risk differs by a factor of eight. This defect propagates into:

- Mispriced premiums and hedge ratios (no Average Annual Loss).
- No exceedance-probability outputs (OEP/AEP curves, return periods) — the standard currency of catastrophe risk transfer and of PRS term sheets.
- A model-validation weakness: hazard frequency and vulnerability cannot be independently validated, breaching the SR 11-7 expectation that model components be separately testable, and weakening BCBS 239 data-lineage claims (the frequency assumption is implicit rather than traceable to source data).

### 1.3 Proposed remedy (summary)

Introduce a **Frequency Layer**: a per-gauge (or per-region) stochastic event-arrival model calibrated from historical gauge records, composed with the existing per-event simulator via the industry-standard **Event Loss Table (ELT) → Year Loss Table (YLT)** pipeline. Pricing becomes rate-based:

```
Annual flood frequency (gauge g)  =  λ_g × P(flood | storm, g)
Pure premium (gauge g)            =  λ_g × P(flood | storm, g) × E[loss | flood, g]
```

with λ_g the calibrated annual storm arrival rate.

---

## 2. Objectives

| # | Objective | Success measure |
|---|-----------|-----------------|
| O1 | Price reflects event frequency | AAL differs proportionally between high- and low-frequency gauges with equal conditional flood probability |
| O2 | Produce standard cat-risk outputs | OEP, AEP, return-period loss tables generated per gauge and per portfolio |
| O3 | Independently validatable components | Frequency model backtestable against observed exceedance counts, separately from vulnerability model |
| O4 | Compliance by construction | Data lineage from raw gauge records to λ_g documented and reproducible (BCBS 239); validation artefacts generated automatically (SR 11-7) |
| O5 | No new technical debt | Full test coverage on new modules; single source of configuration; no duplication of existing simulator logic |

---

## 3. Scope

### 3.1 In scope

- Frequency model abstraction with Poisson and Negative Binomial implementations.
- Non-homogeneous (seasonal) rate extension as an optional variant.
- Calibration pipeline: peaks-over-threshold (POT) extraction from historical gauge series → arrival-rate estimation → dispersion diagnostics → model selection per gauge.
- YLT sampler composing frequency draws with the existing event simulator.
- Pricing outputs: AAL, pure premium, OEP/AEP curves, return-period losses, event exceedance frequency (EEF).
- Validation module: dispersion index test, count backtesting, frequency-model goodness of fit, sensitivity to threshold choice.
- Configuration schema extension (centralised; no per-module constants).
- Documentation: model specification, data lineage record, validation report template.

### 3.2 Out of scope (this phase)

- Non-stationary / climate-conditioned rates (doubly stochastic λ(t)). Architected for, not implemented — see §4.5.
- Spatial dependence of arrivals across gauges (storm footprint correlation). The existing per-event spatial model already correlates *severity* across gauges within an event; correlating *arrival counts* across gauges is deferred to Phase 2.
- Changes to the inundation / spatial model.
- Multi-year contract pricing and discounting.

### 3.3 Interfaces to existing components

- **Consumes:** existing per-event simulator unchanged (treated as the severity/vulnerability engine).
- **Produces:** YLT consumed by the pricing and hedging module.
- **Does not modify:** spatial model, DEM integration, gauge registry (reads only).

---

## 4. Functional Specification

### 4.1 Frequency model abstraction

A single abstract interface, e.g. `FrequencyModel`, with:

- `fit(counts: AnnualCountSeries) -> FittedFrequencyModel`
- `sample_annual_count(rng) -> int`
- `annual_rate() -> float`
- `diagnostics() -> FrequencyDiagnostics` (dispersion index, log-likelihood, AIC)

Concrete implementations:

| Class | Distribution | When selected |
|-------|--------------|---------------|
| `PoissonFrequency` | Poisson(λ) | Dispersion index ≈ 1 (default) |
| `NegativeBinomialFrequency` | NegBin(r, p) | Overdispersed counts (variance > mean); empirically common at UK gauges, especially slow-responding groundwater catchments |
| `SeasonalPoissonFrequency` | NHPP, log λ(s) = α + β·season | Sub-annual tenors; optional |

Model selection is **data-driven per gauge** via the dispersion index test (Cunnane) with an AIC tiebreak, recorded in the calibration output. A configuration override permits forcing a family per gauge or globally (with the override itself logged — an SR 11-7 requirement for expert judgement).

Design rules (per project standards): one responsibility per module; frequency logic must not leak into the event simulator or pricing modules; all distributional parameters live in the calibration output object, never hard-coded.

### 4.2 Calibration pipeline (POT)

Per gauge, from historical flow/level series:

1. **Threshold selection.** Default: threshold yielding a target mean exceedance rate (configurable, e.g. 1–3 events/year), with bankfull discharge as an a-priori anchor where available. Diagnostics: mean-excess plot, threshold-stability plot.
2. **Declustering / independence.** Enforce minimum inter-event separation (configurable, e.g. days) so peaks are independent; record the rule applied.
3. **Arrival rate.** λ̂ = (number of exceedances) / (years of record). Annual count series retained for dispersion testing.
4. **Dispersion test & model selection.** As §4.1.
5. **Severity check (validation only).** Fit GPD to exceedance magnitudes as a cross-check against the simulator's implied severity distribution at that gauge. Divergence beyond tolerance raises a validation flag (it does not silently recalibrate anything).

**Data lineage (BCBS 239):** every fitted λ_g carries provenance metadata — source dataset ID and version, record period, threshold, declustering rule, fit date, code version. Calibration is a pure function of (data, config); re-running with identical inputs must reproduce identical outputs (regression-tested).

### 4.3 Year Loss Table sampler

For each simulated year *y* and gauge/portfolio:

1. Draw annual event count N_y from the fitted frequency model.
2. Draw N_y events from the existing event simulator (or resample from a pre-generated event set with per-event weights).
3. Evaluate flood occurrence and loss per event (existing logic, unchanged).
4. Aggregate to annual loss; record both occurrence (max event) and aggregate views.

Outputs: YLT with per-year event lists, supporting both OEP (occurrence) and AEP (aggregate) construction.

Performance note: prefer resampling from a cached event set over regenerating events per year; the event set becomes an ELT with rates, which is also the natural export format for third-party comparison.

### 4.4 Pricing outputs

- **AAL / pure premium:** λ_g × P(flood|storm, g) × E[loss|flood, g], plus the empirical YLT mean as a cross-check (the two must reconcile within Monte Carlo error — a built-in self-test).
- **OEP(x):** P(at least one annual loss > x) = 1 − exp(−λ S(x)) analytically under Poisson; empirical from YLT generally.
- **AEP(x):** from annual aggregate losses.
- **Return-period table:** losses at configurable return periods (e.g. 2, 5, 10, 25, 50, 100, 200 years).
- **EEF:** event exceedance frequency, valid for return periods < 1 year (relevant for frequent-flood gauges).

All outputs carry the frequency-model identifier and calibration provenance in their metadata.

### 4.5 Extension points (architected now, built later)

- λ as a process rather than a constant: the `FrequencyModel` interface takes an optional covariate/time argument so a doubly stochastic or climate-conditioned rate can be added without interface change.
- Cross-gauge count correlation: YLT sampler accepts an optional joint-count sampler; default is independent per-gauge draws.

---

## 5. Non-Functional Requirements

| Area | Requirement |
|------|-------------|
| Testing | 100% branch coverage on new modules; property-based tests for distribution sampling (mean/variance recovery); golden-master regression tests for calibration reproducibility |
| Configuration | All thresholds, target exceedance rates, declustering windows, model-selection criteria, return periods in the central config schema; no literals in code |
| Duplication | Frequency layer must reuse existing gauge registry, loss evaluation, and RNG management; audit via `split_audit.py` extended with a duplication check on the new modules |
| Module boundaries | New package respects the cohesion/coupling rule (R2 replacement); no imports from pricing into frequency or vice versa — composition happens in the YLT sampler only |
| Reproducibility | Seeded RNG throughout; calibration and simulation runs fully reproducible from (data version, config version, seed) |
| Audit | Structured run log: inputs, config hash, code version, outputs, validation flags |
| Documentation | Model specification section added to the technical documentation, mirroring this document's §4; validation report auto-generated per calibration run |

---

## 6. Model Validation Plan (SR 11-7 alignment)

1. **Conceptual soundness.** Documented rationale for compound-frequency construction; literature basis (Poisson/POT flood frequency, NegBin overdispersion at UK gauges, ELT/YLT industry practice) recorded in the model specification.
2. **Frequency backtesting.** Per gauge: compare fitted model's predicted annual count distribution against held-out years (train/test split of the historical record); report PIT/χ² diagnostics.
3. **Dispersion coverage.** Report the share of gauges where NegBin is selected over Poisson; investigate spatial clustering of overdispersion (expected in groundwater-dominated catchments).
4. **Threshold sensitivity.** λ̂ and resulting AAL under ±1 threshold-band perturbation; flag gauges where pricing is threshold-sensitive beyond tolerance.
5. **Reconciliation tests.** Analytical AAL vs empirical YLT AAL; analytical Poisson OEP vs empirical OEP.
6. **Benchmarking.** Return-period flood levels vs published national flood frequency estimates for a sample of gauges.
7. **Ongoing monitoring.** Annual recalibration job; drift alert if λ̂ moves beyond a configured band (early non-stationarity signal, feeding the Phase 2 climate-conditioning case).
8. **Effective challenge artefacts.** Every run emits the validation report; overrides of automatic model selection require a recorded justification.

---

## 7. Project Plan

Incremental delivery consistent with the established refactoring approach (leaves first, each stage shippable and tested).

### Stage 1 — Specification & data groundwork
**Deliverables:** finalised version of this document; config schema extension; historical gauge data inventory with provenance records; POT extraction utility with tests.
**Acceptance:** POT series reproducibly generated for all gauges; lineage metadata complete.

### Stage 2 — Frequency models & calibration
**Deliverables:** `FrequencyModel` interface; Poisson and NegBin implementations; dispersion test and model selection; calibration pipeline emitting fitted models + diagnostics + provenance.
**Acceptance:** full coverage; property tests pass; calibration deterministic under fixed inputs; per-gauge model-selection report generated.

### Stage 3 — YLT sampler & integration
**Deliverables:** YLT sampler composing frequency models with existing event simulator; ELT export; seeded reproducibility.
**Acceptance:** YLT statistics reconcile with analytical AAL; no modification to event-simulator internals; `split_audit.py` clean.

### Stage 4 — Pricing outputs
**Deliverables:** AAL, OEP/AEP, return-period tables, EEF; pricing module consumes YLT via a single interface; legacy percentage metric retained behind a deprecation flag for parallel-run comparison.
**Acceptance:** parallel-run report quantifying repricing impact per gauge (the key business artefact — expect material repricing at frequency extremes).

### Stage 5 — Validation & documentation
**Deliverables:** validation module (§6 tests 2–6); auto-generated validation report; technical documentation update; monitoring job (test 7).
**Acceptance:** validation report reviewed and signed off; monitoring scheduled; legacy metric formally deprecated.

### Stage 6 (Phase 2, separate approval) — Extensions
Seasonal/NHPP rates; cross-gauge count dependence; non-stationary λ for climate scenarios and multi-year PRS tenors.

---

## 8. Risks and Assumptions

| Risk / assumption | Impact | Mitigation |
|-------------------|--------|------------|
| Short or gappy gauge records → noisy λ̂ | Mispricing at data-poor gauges | Minimum record-length rule; regional pooling fallback (flagged in provenance); wide-λ̂ uncertainty surfaced in outputs |
| Threshold choice materially moves λ̂ | Pricing instability | Sensitivity test (§6.4); threshold governance in config with change log |
| Simulator's "storm" definition ≠ POT exceedance definition | Frequency and vulnerability calibrated to different event populations — λ × P(flood\|storm) invalid | **Critical alignment task in Stage 1:** define the qualifying event consistently across historical extraction and simulation; document the mapping |
| Overdispersion ignored where present | Understated tail (AEP) | NegBin default where dispersion test rejects Poisson |
| Stationarity assumed | Understated forward risk under climate change | Explicit limitation in model documentation; drift monitoring; Phase 2 roadmap |
| Parallel-run reveals large repricing | Client communication risk | Stage 4 impact report before switchover; staged rollout |

---

## 9. Glossary

- **AAL** — Average Annual Loss; expected loss per year.
- **AEP** — Aggregate Exceedance Probability; P(total annual loss > x).
- **OEP** — Occurrence Exceedance Probability; P(largest single event loss in a year > x).
- **EEF** — Event Exceedance Frequency; annual frequency (not probability) of events exceeding a level.
- **ELT / YLT** — Event Loss Table / Year Loss Table.
- **POT** — Peaks Over Threshold; extreme-value sampling of all independent exceedances above a threshold.
- **GPD** — Generalised Pareto Distribution; standard model for POT exceedance magnitudes.
- **Dispersion index** — variance/mean of annual counts; ≈1 supports Poisson, >1 indicates overdispersion (NegBin).
- **NHPP** — Non-Homogeneous Poisson Process; time-varying arrival rate.
