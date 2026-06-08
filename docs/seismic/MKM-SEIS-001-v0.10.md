# Building Seismic-Resilience Credit Model
## Poisson Occurrence · Fault-Geometry Spatial Draw · GMPE Intensity · Lognormal Fragility Chain
### MKM Research Labs — Version 0.10 — 08-June-2026 — David K Kelly
### CONFIDENTIAL — PROPRIETARY

---

## Legal Notice

PROPRIETARY AND CONFIDENTIAL

This document, including all algorithms, models, methodology, formulas, calculations, and intellectual
concepts contained herein, constitutes the exclusive intellectual property and confidential trade secrets
of MKM Research Labs ("MKM"). Any usage, reproduction, distribution, modification, or disclosure of this
document or any portion thereof, without the express prior written authorisation from MKM Research Labs is
strictly prohibited and constitutes an infringement of intellectual property rights. The document is
provided on an "as is" basis. MKM Research Labs makes no representations or warranties of any kind,
express or implied, regarding its accuracy, reliability, or suitability for any particular purpose.
All rights reserved. © 2021–2026 MKM Research Labs. Governed by the laws of the United Kingdom.

---

## Contents

1. Executive Summary
2. Model Purpose and Scope
   - 2.1 Purpose
   - 2.2 Scope
   - 2.3 Out of Scope
3. Mathematical Framework
   - 3.1 Occurrence (Model A)
   - 3.2 Fault Geometry and Spatial Draw (Model A — Spatial Sub-layer)
   - 3.3 Ground Motion Intensity (Model B)
   - 3.4 Seismic Response Effectiveness (Model C)
   - 3.5 Damage State, Loss and Resilience Credit (Model D)
   - 3.6 Post-Earthquake Fire Cascade
   - 3.7 Resilience Credit
4. Input Parameters and Calibration
5. Implementation Details
   - 5.1 Module Layout
   - 5.2 Randomness
6. Validation and Backtesting
   - 6.1 Automated Test Results
7. Sensitivity Analysis
   - 7.1 Baseline Definition
   - 7.2 Axis 1 — Distance (Source-to-Site R_JB)
   - 7.3 Axis 2 — Intensity (Seismic Hazard Zone / PGA)
   - 7.4 Axis 3 — Resilience (BRI Geoseismic Measures)
   - 7.5 Two-Way Interaction: Intensity × Resilience
   - 7.6 Two-Way Interaction: Distance × Resilience
   - 7.7 Sensitivity Design Requirement
8. Model Limitations and Known Weaknesses
9. Governance Validation Questions
   - 9.1 Q1 — Model purpose and use
   - 9.2 Q2 — Data quality and lineage
   - 9.3 Q3 — Conceptual soundness
   - 9.4 Q4 — Calibration and parameters
   - 9.5 Q5 — Implementation verification
   - 9.6 Q6 — Sensitivity and stability
   - 9.7 Q7 — Limitations and weaknesses
   - 9.8 Q8 — Ongoing monitoring
   - 9.9 Q9 — Governance and approval
10. Change History

**Appendices**

- A — Occurrence Parameters (Model A)
- B — Fault Trace File Format
- C — GMPE and Site Amplification Parameters (Model B)
- D — Response Effectiveness and BRI Measure Modifiers (Model C)
- E — Fragility Parameters and Damage-State Tables (Model D)

---

## 1 Executive Summary

The Building Seismic-Resilience Credit Model (**MKM-SEIS-001**) prices the seismic resilience of a
commercial asset so that seismic loss aggregates into the same resilience-credit currency as the existing
10,000-storm Monte Carlo engine and the fire model (MKM-FIRE-001). The credit is consumed by the
Commercial PRS Pricer as an independent seismic leg, combined with the flood, wind and fire legs through
a root-sum-of-squares all-in coupon. The model is built from four governance-separated component models:

- **Model A — Occurrence.** A Poisson occurrence model producing per-scenario earthquake events. The
  annual rate λ is sourced from a site-specific hazard lookup (`config/seismic_zones.json`). A spatial
  sub-layer draws the rupture location along the catchment fault-trace polyline — structured identically
  to the river-centreline geometry used in the storm module — and computes the Joyner-Boore
  source-to-site distance R_JB used by Model B.

- **Model B — Ground Motion Intensity.** A Ground Motion Prediction Equation (GMPE) maps the sampled
  (M, R_JB) pair to a site PGA, adjusted for local soil amplification via V_S30. PGA is the intensity
  measure passed to Models C and D.

- **Model C — Seismic Response Effectiveness.** A deterministic mapping from the asset's BRI geoseismic
  measures (GS01–GS18 flags from the CDM resilience section) to the fragility median multipliers,
  soil-amplification gate, post-earthquake fire cascade probability, and recovery acceleration factor
  consumed by Model D.

- **Model D — Damage State, Loss and Resilience Credit.** A single-step lognormal fragility draw assigns
  one of four damage states (DS0–DS3). Per-damage-state loss ratios produce a per-scenario structural
  loss. Aggregated over n_sim draws, the model emits annual expected loss, PML at 475-year and 2,475-year
  return periods, and the full-collapse (DS3) frequency in basis points — the seismic leg the Commercial
  PRS Pricer consumes.

The **point-of-no-return analogue** is DS3 (complete damage / collapse): once this state is assigned,
loss is 100% and recovery requires demolition and rebuild. The DS3 frequency,
`n_DS3 / n_sim × 1.0 × 10,000`, is the bps the PRS pricer charges for the seismic leg.

The model is designed to be **sensitive to all three primary axes**:

1. **Distance** — Source-to-site distance R_JB governs the GMPE attenuation: a building 2 km from the
   fault rupture receives materially higher PGA than one 50 km away, producing a measurable change in
   DS2/DS3 frequency and seismic spread.
2. **Intensity** — Seismic hazard zone (λ, m_max) governs how often high-magnitude events occur: the
   same building in a Very High zone receives far more DS3 events per 10,000 simulations than in a Low
   zone.
3. **Resilience** — BRI geoseismic measures (GS01–GS18) directly shift the fragility medians: a
   building with GS08 + GS12 + GS14 present has substantially higher median PGA at each damage threshold
   than one with no measures, producing a step-change in no-collapse rate and seismic spread.

**Status:** Development (Tier 2, RAG Amber). All four component models and the end-to-end orchestrator
are delivered with unit tests. Every numeric parameter is a first-pass engineering-judgement seed
(`config/seismicmatrices.json`, version `"seed-0"`); results are directional, not calibrated. Not
approved for production until historical calibration completes and the Model Risk Committee (MRC) issues
sign-off (remediation items SEIS-R1–R4).

---

## 2 Model Purpose and Scope

### 2.1 Purpose

To assign each commercial asset a seismic-resilience credit — expressed as an annual unconditional loss
frequency, a conditional no-collapse rate, and a full-collapse (DS3) frequency — that can be priced
pari-passu with the flood, wind and fire hazards already in the portfolio engine. The credit rewards
genuine, evidenced seismic resilience (seismic foundation design, lateral force resistance, base
isolation, independent audit) and penalises the configurations that historically drive total losses, most
notably unreinforced masonry or pre-code concrete frames in high-hazard zones without base isolation or
lateral bracing.

### 2.2 Scope

The model covers commercial assets described by the v2 commercial-asset and resilience sections of the
Common Data Model (CDM). It reads only the derived `AssetSeismicFeatures` bundle — never the raw CDM
record — so that the feature contract is explicit, testable and stable against CDM schema churn. The
in-scope drivers are: commercial type, construction type, number of storeys, soil type, seismic hazard
zone, the eighteen BRI geoseismic measures (GS01–GS18), and fault proximity. The catchment fault trace
is a companion spatial file (`catchments/<name>/fault_trace.json`) structured identically to the river
polyline used in the storm module.

The model produces a per-asset resilience credit and a portfolio roll-up; both are reproducible from a
single random seed.

### 2.3 Out of Scope

- Physical finite-element or nonlinear time-history structural analysis.
- Casualty, life-safety or evacuation modelling.
- Aftershock sequences (the Poisson model covers mainshock occurrence only; aftershock clustering is a
  documented limitation — SEIS-L2).
- Liquefaction or landslide as independent primary hazards (flagged as conditional cascades from the
  occurrence layer only).
- Business-interruption quantum (only the resilience credit is produced; loss-given-event for the
  collapse leg is fixed at 100%).
- Explicit floor-level geometry — building height enters only through `NumberOfStoreys`.

---

## 3 Mathematical Framework

### 3.1 Occurrence (Model A)

Earthquake occurrence is modelled as a homogeneous Poisson process (HPP). Under HPP, events occur
independently at a constant mean rate, the number of events in any interval t follows a Poisson
distribution, and inter-event times are exponentially distributed. This is the standard assumption in
Probabilistic Seismic Hazard Analysis (PSHA) for mainshock occurrence.

The per-asset annual occurrence rate is:

```
λ_i = λ_zone · m_fault · m_soil
```

where:

- `λ_zone` — mean annual rate of earthquakes M ≥ m_min at the asset's seismic hazard zone, from
  `config/seismic_zones.json`.
- `m_fault` — fault proximity modifier: `1.0 + δ_GS01 · 1[FaultProximityKm < 1.0 and GS01 absent]`,
  where `δ_GS01 = 0.15`.
- `m_soil` — soil recurrence modifier: 1.00 for Class A/B, 1.10 for Class C, 1.15 for Class D,
  1.20 for Class E.

The effective rate over run horizon h years is `λ_eff = λ_i · h`. For each of n_sim draws, a Poisson
count `N ~ Poisson(λ_eff)` is sampled; an earthquake instantiates for that draw when `N ≥ 1` — the
direct analogue of storm-event generation where only a subset of draws produce an event.

The magnitude M for each instantiated event is drawn from the truncated Gutenberg-Richter distribution:

```
P(M > m) = [10^(a − b·m) − 10^(a − b·m_max)] / [10^(a − b·m_min) − 10^(a − b·m_max)]
```

Default parameters: b = 1.0, m_min = 5.0, m_max = 7.5. All zone-configurable in
`config/seismic_zones.json`.

### 3.2 Fault Geometry and Spatial Draw (Model A — Spatial Sub-layer)

For each instantiated earthquake, the rupture location is sampled from the catchment fault-trace
polyline (`catchments/<name>/fault_trace.json`). The polyline is a JSON array of [lon, lat] coordinate
pairs, structured identically to the river-centreline files used in the storm module:

```json
[[107.020, 20.950], [107.080, 20.900], [107.140, 20.850], ...]
```

**Rupture centroid draw:**

1. Compute cumulative arc-length S(k) along the polyline at each vertex k using the Haversine formula.
2. Sample `u ~ Uniform(0, 1)`; set `s* = u · S(n_vertices)`.
3. Interpolate linearly to find the rupture centroid `(lon*, lat*)`.

**Rupture length:** The along-fault surface rupture half-length is drawn from the Wells-Coppersmith
scaling relation:

```
log10(L_r) = −2.44 + 0.59 · M
```

The rupture segment occupies `[s* − L_r/2, s* + L_r/2]` along the fault, clipped to fault endpoints.

**Source-to-site distance R_JB:** Compute the minimum Haversine distance from the asset `(lon, lat)`
(CDM fields `Longitude`, `Latitude`) to any point on the rupture segment. R_JB is the Joyner-Boore
distance — the horizontal distance to the surface projection of the rupture — used as the GMPE distance
metric.

This is the same spatial primitive as river-bank distance in the flood module; no new GIS dependency is
introduced.

**Sensitivity design note:** Distance is a first-order driver. The GMPE attenuation with R_JB typically
produces a factor of 3–5× reduction in median PGA from 2 km to 50 km at M6.5. The model must exhibit a
monotonically decreasing seismic spread as R_JB increases from 0 to 100 km, with the sharpest gradient
in the 0–20 km near-fault zone. See Section 7.2 for the required sensitivity table.

### 3.3 Ground Motion Intensity (Model B)

The site PGA is sampled from a GMPE in lognormal form:

```
ln(PGA) = ln_PGA_mean(M, R_JB, V_S30) + σ_total · ε,    ε ~ N(0, 1)
```

where `σ_total` is the total standard deviation (inter-event + intra-event, default 0.65 ln units) and
`V_S30` is the time-averaged shear-wave velocity in the top 30 m (mapped from CDM `SoilType`).

**Soil amplification** is applied implicitly through V_S30 in the GMPE. Where V_S30 is unavailable, a
class-based proxy is used (Appendix C, Table C2). If GS02 (seismic foundation design) is absent and
`SoilType` is Class D or E, an additional amplification factor F_a = 1.30 is applied to the GMPE
median before sampling.

**GMPE selection** is configurable per catchment zone in `config/seismic_zones.json`. Default: Boore-
Atkinson 2014 (NGA-West2) for active shallow crust; Zhao et al. 2006 for subduction zones (relevant for
Halong / Red River Fault system).

**Sensitivity design note:** PGA is the direct input to the fragility functions. A doubling of PGA
should produce a monotonic increase in DS2 and DS3 probability. The GMPE ε draw ensures that two assets
at the same (M, R_JB) receive different PGA realisations, preserving intra-event variability across the
portfolio.

### 3.4 Seismic Response Effectiveness (Model C)

Model C is a deterministic mapping from the asset's BRI geoseismic measure flags (GS01–GS18, from the
`AssetSeismicFeatures` bundle) to the modifiers that Model D consumes. No randomness is introduced in
Model C.

**Fragility median multiplier** θ_mult — the product of upward shifts on the damage-state median PGA
for each present measure:

```
θ_i_adj = θ_i_base · θ_mult,    θ_mult = Π_j (1 + δ_j · 1[measure_j present])
```

Individual measure modifiers δ_j are given in Appendix D, Table D1. The BRI weakest-link principle
applies in spirit: missing key structural measures (GS08, GS12, GS14) produce the largest downward
pressure on θ_mult and therefore the largest increase in DS2/DS3 frequency.

**Recovery acceleration factor** r_acc — derived from governance measures GS16–GS18. Used in the
functionality-recovery curve Q(t) in Model D. Faster recovery → higher resilience credit.

**Post-earthquake fire (PEF) probability** p_PEF — the conditional probability of a fire cascade given
damage state DS2 or DS3. GS15 (flexible gas piping with automatic seismic shut-off valve) is the
dominant modifier, reducing p_PEF by 80%.

**Sensitivity design note:** Resilience is the third required sensitivity axis. The model must exhibit
monotonically increasing no-collapse rate and monotonically decreasing seismic spread as BRI measures
accumulate from NR (no measures) to AA (all measures present). The GS12 (base isolation) × high-hazard
zone interaction is the primary non-linearity: base isolation should produce a step-change reduction in
DS3 frequency in high-hazard zones but a smaller absolute reduction in low-hazard zones. See Section 7.4
and 7.5.

### 3.5 Damage State, Loss and Resilience Credit (Model D)

For each scenario where an earthquake has been instantiated:

**Step 1 — Fragility draw.** Evaluate the lognormal fragility CDF at the sampled PGA_site for each
damage state threshold:

```
P(DS ≥ DS_i | PGA) = Φ( [ln(PGA) − ln(θ_i_adj)] / β )
```

where Φ is the standard normal CDF, θ_i_adj is the adjusted median from Model C, and β = 0.60
(configurable in `config/seismicmatrices.json`).

Damage state assignment: draw `U ~ Uniform(0, 1)` and assign the highest DS_i for which
`P(DS ≥ DS_i) > U`:

| State          | Code | Assignment condition                              |
|----------------|------|---------------------------------------------------|
| None / Slight  | DS0  | U > P(DS ≥ DS1)                                   |
| Moderate       | DS1  | P(DS ≥ DS2) < U ≤ P(DS ≥ DS1)                    |
| Extensive      | DS2  | P(DS ≥ DS3) < U ≤ P(DS ≥ DS2)                    |
| Complete       | DS3  | U ≤ P(DS ≥ DS3)                                   |

**Step 2 — Loss draw.** The per-scenario structural loss ratio L_s is sampled from a truncated
lognormal distribution conditioned on damage state (parameters in Appendix E, Table E2). For DS3,
L_s = 1.00 (fixed, no draw required) — the seismic analogue of the fire model's fixed 100%
loss-given-conflagration.

**Step 3 — PEF cascade.** If DS ≥ DS2, draw `V ~ Uniform(0, 1)`. If `V < p_PEF` (from Model C),
flag `cascade_fire = True` for this scenario. The fire module (MKM-FIRE-001) is then invoked with
`InitiationClass = EE` (External Exposure) for this scenario, and the combined scenario loss is
`max(L_seismic, L_fire)`.

**Step 4 — Functionality curve.** Post-event functionality Q(t₀) is read from the DS-to-functionality
table (Appendix E, Table E3). Recovery to Q = 1.0 follows a linear ramp over recovery time T_rec,
scaled by r_acc from Model C:

```
Q(t) = Q(t₀) + (1 − Q(t₀)) · min( (t − t₀) / (T_rec / r_acc), 1 )
```

The seismic resilience index for the scenario is the normalised area under Q(t) over the control
horizon T_LC = 12 months.

### 3.6 Post-Earthquake Fire Cascade

This sub-model connects MKM-SEIS-001 to MKM-FIRE-001 through a conditional cascade gate:

| Damage State | GS15 absent | GS15 present |
|---|---|---|
| DS0 or DS1 | 0.00 | 0.00 |
| DS2 | 0.08 | 0.016 |
| DS3 | 0.18 | 0.036 |

These are first-pass engineering-judgement seeds. Calibration against historical post-earthquake fire
records is open under SEIS-R1.

### 3.7 Resilience Credit

Aggregating over the n_sim draws (of which n_events instantiate earthquakes), with terminal counts
n_DS0, n_DS1, n_DS2, n_DS3 and n_PEF cascade flags:

```
loss frequency     = Σ_s L_s / n_sim

no-collapse rate   = (n_DS0 + n_DS1 + n_DS2) / n_events

seismic spread (bps) = (n_DS3 / n_sim) × 1.0 × 10,000
```

The seismic spread is the full-collapse leg the Commercial PRS Pricer consumes. It is combined with the
flood, wind and fire legs in an all-in coupon by root-sum-of-squares, treating the perils as independent:

```
all-in = sqrt( Σ_perils leg² )
```

---

## 4 Input Parameters and Calibration

All numeric seeds live in `config/seismicmatrices.json` (version `"seed-0"`) and are loaded by
`config/seismic.py`; no number is embedded in the model code. The resilience-measure vocabulary is
imported from `port.cdm.asset.resilience` so that the GS01–GS18 flag-to-modifier mapping stays
single-sourced with the rest of the CDM. The full parameter set — zone hazard rates, Gutenberg-Richter
coefficients, GMPE selection, V_S30 proxies, fragility medians and log-standard deviations by
construction type, BRI measure modifiers, loss-given-damage-state distributions, recovery times, and PEF
probabilities — is reproduced verbatim in the Appendices.

**Calibration status.** Every value is a first-pass engineering-judgement seed chosen for plausible
direction and ordering, not magnitude: e.g. unreinforced masonry is more fragile than modern RC; soft
soil amplifies damage; base isolation dramatically reduces DS3 frequency; GS18 (EGGAR) accelerates
recovery. Calibration against historical commercial seismic-loss data (SEIS-R1) and an independent
benchmarking exercise (SEIS-R2) are open remediation items; until they close, the outputs must be read
as relative resilience signals, not absolute loss probabilities.

---

## 5 Implementation Details

### 5.1 Module Layout

```
config/seismic.py                              parameter schema (enums, dataclasses, loader)
config/seismicmatrices.json                    seed numeric parameters
config/seismic_zones.json                      zone hazard rates, G-R coefficients, GMPE selection

catchments/<name>/fault_trace.json             fault polyline [[lon, lat], ...] per catchment

src/models/seismic/datastructures.py           runtime types:
                                                 AssetSeismicFeatures
                                                 OccurrenceResult
                                                 GroundMotionResult
                                                 SeismicResponseProfile
                                                 DamageOutcome
                                                 AssetSeismicResult

src/models/seismic/occurrence.py               Model A: Poisson draw, magnitude sample,
                                                 fault spatial draw, R_JB computation

src/models/seismic/groundmotion.py             Model B: GMPE evaluation, soil amplification

src/models/seismic/responseeffectiveness.py    Model C: BRI measure flag → modifier mapping

src/models/seismic/damage.py                   Model D: fragility draw, loss sample,
                                                 PEF cascade gate, functionality curve,
                                                 end-to-end orchestrator:
                                                   simulate_asset_seismic(asset, rng, n_sim)
                                                   simulate_portfolio_seismic(assets, rng, n_sim)

src/routes/commercial/hazard.py                read-time join attaching seismic_spread_bps
                                                 to the asset hazard payload

tests/models/seismic/
  test_occurrence.py
  test_groundmotion.py
  test_responseeffectiveness.py
  test_damage.py

docs/models/sensitivities/seismicresilience/   sensitivity harness (runs simulate_asset_seismic)
```

### 5.2 Randomness

All randomness flows through a single caller-owned `numpy.random.Generator`, so an entire portfolio
run is reproducible from one seed — matching the storm, typhoon and fire model convention. Model C is
deterministic. Model B introduces one `ε ~ N(0,1)` draw per scenario for the GMPE residual. Model D
introduces one `U ~ Uniform(0,1)` for the damage-state assignment, one draw for the
loss-given-damage-state sample, and one `V ~ Uniform(0,1)` for the PEF cascade gate. Model A
introduces one Poisson draw for event count, one fractional draw for rupture location along the fault
trace, and one draw for magnitude.

---

## 6 Validation and Backtesting

Historical calibration and backtesting are open remediation items (SEIS-R1, SEIS-R2) to be completed
before production sign-off. Current validation is by directional unit tests, which confirm the model
behaves as designed: a BRI-AA asset has materially lower DS3 frequency than a BRI-NR asset at the same
PGA; base isolation (GS12) produces a measurable shift in the fragility draw distribution; assets in
low-hazard zones have near-zero collapse frequency; the PEF cascade fires at the expected conditional
rate; and a whole-portfolio run is bit-for-bit reproducible from a single seed.

### 6.1 Automated Test Results

Automated test-result tables to be generated. Stage 1 + Stage 2 unit tests live under
`tests/models/seismic/` (`test_occurrence.py`, `test_groundmotion.py`,
`test_responseeffectiveness.py`, `test_damage.py`).

---

## 7 Sensitivity Analysis

Tables in this section are generated by `docs/models/sensitivities/seismicresilience/` running the real
`simulate_asset_seismic` against a fixed baseline and varying one input at a time over 20,000 Monte Carlo
draws per cell. The model is required to exhibit monotonic and material sensitivity along each of the
three primary axes — **distance, intensity and resilience** — before the sensitivity harness is
considered to have passed.

### 7.1 Baseline Definition

The baseline asset is a fully-occupied 4-storey Office in Fair condition, RC pre-code construction, Stiff
soil (Class B), Moderate seismic zone (λ = 0.008 events/yr, M ≥ 5.0), located 20 km from the fault
trace, with all BRI geoseismic measures absent (NR position). The sensitivity tables vary one axis at a
time from this baseline.

---

### 7.2 Axis 1 — Distance (Source-to-Site R_JB)

Distance is varied by fixing M = 6.5 and moving the asset's position relative to a fixed fault trace,
changing only R_JB. This isolates the GMPE attenuation curve from the occurrence layer. Seismic hazard
zone is held at Moderate; BRI measures held at all-absent.

All other inputs held at baseline. 20,000 draws per cell.

**Table 1: Seismic credit by source-to-site distance R_JB — RC pre-code, Moderate zone, all BRI absent**

| R_JB (km) | Median PGA_site (g) | No-collapse rate (%) | Loss freq (%) | Seismic spread (bps) |
|---|---|---|---|---|
| 2 | ~0.42 | TBD | TBD | TBD |
| 5 | ~0.28 | TBD | TBD | TBD |
| 10 | ~0.18 | TBD | TBD | TBD |
| 20 | ~0.11 | TBD | TBD | TBD |
| 50 | ~0.05 | TBD | TBD | TBD |
| 100 | ~0.02 | TBD | TBD | TBD |

*Median PGA values are indicative GMPE outputs at M 6.5, Stiff soil; actual values generated by model.*

**Required behaviour:** Seismic spread must decrease monotonically as R_JB increases from 2 km to
100 km. The gradient must be steepest in the 2–10 km near-fault zone (where GMPE attenuation is
fastest) and flatten beyond 50 km. A failure of this monotonicity is a model defect.

**Table 2: Seismic spread (bps) by R_JB × construction type — the near-fault construction interaction**

| R_JB (km) | RC pre-code | Masonry URM | RC modern seismic | Steel MRF |
|---|---|---|---|---|
| 2 | TBD | TBD | TBD | TBD |
| 10 | TBD | TBD | TBD | TBD |
| 20 | TBD | TBD | TBD | TBD |
| 50 | TBD | TBD | TBD | TBD |

**Required behaviour:** At any R_JB, masonry URM must exhibit higher spread than RC pre-code, which
must exhibit higher spread than RC modern seismic and steel MRF. The ordering must be stable across all
distances.

---

### 7.3 Axis 2 — Intensity (Seismic Hazard Zone / PGA Level)

Intensity is varied by changing the hazard zone (λ_zone and m_max), which changes both occurrence
frequency and the magnitude distribution. R_JB is held fixed at 20 km; BRI measures held at all-absent.

**Table 3: Seismic credit by hazard zone — RC pre-code, R_JB = 20 km, all BRI absent**

| Zone | λ_zone (M≥5/yr) | m_max | No-collapse rate (%) | Loss freq (%) | Seismic spread (bps) |
|---|---|---|---|---|---|
| Very low | 0.0005 | 6.5 | TBD | TBD | TBD |
| Low | 0.002 | 7.0 | TBD | TBD | TBD |
| Moderate | 0.008 | 7.5 | TBD | TBD | TBD |
| High | 0.030 | 8.0 | TBD | TBD | TBD |
| Very high | 0.080 | 8.5 | TBD | TBD | TBD |

**Required behaviour:** Seismic spread must increase monotonically from Very low to Very high zone.
The Very high zone must produce materially non-zero DS3 frequency even for RC modern seismic
construction. The Very low zone must produce near-zero DS3 frequency for all construction types.

**Table 4: Seismic spread (bps) by hazard zone × soil type — the soft-soil amplification interaction**

| Zone | Rock (A) | Stiff (B) | Soft (D) — GS02 absent | Soft (D) — GS02 present |
|---|---|---|---|---|
| Low | TBD | TBD | TBD | TBD |
| Moderate | TBD | TBD | TBD | TBD |
| High | TBD | TBD | TBD | TBD |
| Very high | TBD | TBD | TBD | TBD |

**Required behaviour:** Soft soil without GS02 must exhibit higher spread than stiff or rock, and higher
spread than soft soil with GS02 present. The GS02 effect must be larger in high-hazard zones (where the
amplified PGA is more likely to exceed DS2/DS3 fragility thresholds) than in low-hazard zones.

---

### 7.4 Axis 3 — Resilience (BRI Geoseismic Measures)

Resilience is varied by accumulating BRI measures from all-absent (NR) to the full AA stack. Hazard zone
is Moderate; R_JB = 20 km; RC pre-code baseline construction.

**Table 5: Seismic credit by BRI resilience level — RC pre-code, Moderate zone, R_JB = 20 km**

| BRI Position | Measures present | No-collapse rate (%) | Loss freq (%) | Seismic spread (bps) |
|---|---|---|---|---|
| NR (none) | — | TBD | TBD | TBD |
| B (basic) | GS01, GS05, GS07, GS10, GS11, GS14 | TBD | TBD | TBD |
| A (strong) | B + GS02, GS08, GS09, GS15, GS16 | TBD | TBD | TBD |
| AA (best practice) | A + GS03, GS12, GS13, GS17, GS18 | TBD | TBD | TBD |

**Required behaviour:** No-collapse rate must increase monotonically from NR to AA. Seismic spread must
decrease monotonically. The step from A to AA must be material (GS12 base isolation is the dominant
driver). The step from NR to B must be smaller in absolute bps terms than the step from B to AA.

**Table 6: Seismic credit by key individual BRI measures — single-measure sweeps, Moderate zone,
R_JB = 20 km, RC pre-code baseline, all others absent**

| Measure added | Description | No-collapse rate (%) | Seismic spread (bps) | Δ spread vs none |
|---|---|---|---|---|
| None (baseline) | — | TBD | TBD | — |
| GS08 | Lateral force resistance all floors | TBD | TBD | TBD |
| GS09 | Connected and braced structure | TBD | TBD | TBD |
| GS12 | Seismic base isolation | TBD | TBD | TBD |
| GS14 | No vertical irregularities | TBD | TBD | TBD |
| GS02 | Seismic foundation (removes F_a penalty) | TBD | TBD | TBD |

**Required behaviour:** GS12 (base isolation) must produce the largest single-measure reduction in
seismic spread. GS08 must produce a larger reduction than GS09. GS02 effect must be zero for Class A/B
soil (no F_a penalty to remove) and non-zero for Class D/E.

---

### 7.5 Two-Way Interaction: Intensity × Resilience

This is the headline non-linearity, directly analogous to the fire model's height × suppression cliff.

**Table 7: Seismic spread (bps) by hazard zone × BRI resilience level — RC pre-code, R_JB = 20 km**

| Zone | NR (no measures) | B | A | AA (GS12 present) |
|---|---|---|---|---|
| Very low | TBD | TBD | TBD | TBD |
| Low | TBD | TBD | TBD | TBD |
| Moderate | TBD | TBD | TBD | TBD |
| High | TBD | TBD | TBD | TBD |
| Very high | TBD | TBD | TBD | TBD |

**Required behaviour:** In the Very high zone, the spread difference between NR and AA must be large and
material — base isolation must produce a step-change reduction in DS3 frequency, not a smooth gradient.
In the Very low zone, the spread difference between NR and AA must be small in absolute bps terms (few
events means few DS3 outcomes regardless of resilience). This asymmetry is the economically important
behaviour the credit is designed to price: strong BRI measures are most valuable in high-hazard zones.

---

### 7.6 Two-Way Interaction: Distance × Resilience

**Table 8: Seismic spread (bps) by R_JB × BRI resilience level — RC pre-code, Moderate zone**

| R_JB (km) | NR (no measures) | B | A | AA (GS12 present) |
|---|---|---|---|---|
| 2 | TBD | TBD | TBD | TBD |
| 10 | TBD | TBD | TBD | TBD |
| 20 | TBD | TBD | TBD | TBD |
| 50 | TBD | TBD | TBD | TBD |

**Required behaviour:** At R_JB = 2 km (near-fault), the spread difference between NR and AA must be
large. At R_JB = 100 km, spread approaches zero for all resilience levels (PGA too low to cause DS2/DS3)
and the BRI differentiation becomes negligible. This is physically correct: resilience measures matter
most for buildings close to the fault.

---

### 7.7 Sensitivity Design Requirement

Before the sensitivity harness is considered to have passed, the following must hold simultaneously:

1. **Distance monotonicity:** Seismic spread is non-increasing in R_JB across all construction types
   and hazard zones.
2. **Intensity monotonicity:** Seismic spread is non-decreasing in hazard zone across all construction
   types and R_JB values.
3. **Resilience monotonicity:** No-collapse rate is non-decreasing and seismic spread is non-increasing
   as BRI measures accumulate from NR to AA, at all tested (zone, R_JB) combinations.
4. **Interaction ordering:** In the intensity × resilience grid, the spread for (Very high, NR) must
   exceed the spread for (High, AA), which must exceed (Moderate, AA).
5. **Near-zero floor:** In the Very low zone at R_JB = 100 km, seismic spread must be < 1 bps for all
   construction types and resilience levels.

Any cell that violates these conditions constitutes a model defect requiring investigation before the
sensitivity harness result is accepted.

---

## 8 Model Limitations and Known Weaknesses

- **No historical calibration (SEIS-L1).** Every parameter is a first-pass placeholder; outputs are
  relative signals, not absolute loss probabilities.
- **Mainshock-only Poisson (SEIS-L2).** The HPP assumption ignores aftershock clustering. Short-term
  hazard after a mainshock is underestimated; the Poisson model is appropriate for long-run annualised
  loss but not for real-time post-event risk updates.
- **Single fault trace per catchment (SEIS-L3).** Assets in zones with multiple independent fault
  sources require a superposition of Poisson processes (one draw per source). This is a planned
  extension (SEIS-R4); the current implementation uses a single fault file per catchment.
- **Deterministic GMPE median (SEIS-L4).** Only the aleatory residual ε is sampled; epistemic
  uncertainty in the GMPE (logic-tree ensemble) is not represented. Deferred to a future version.
- **Fixed loss-given-event for collapse leg.** The DS3 leg assumes 100% loss; partial-loss quantum
  within DS3 is not modelled.
- **Independence assumption.** The root-sum-of-squares all-in coupon treats seismic, fire, flood and
  wind as independent perils. Co-occurrence is partially addressed by the PEF cascade; full joint
  distribution of perils is not modelled.
- **Height proxy (SEIS-L5).** Building height enters only through `NumberOfStoreys`; floor-level
  geometry and structural irregularity are not modelled beyond the GS14 flag.

---

## 9 Governance Validation Questions

The following nine questions are mandated by Chapter 5 of the Model Risk Governance for Vendors handbook
and must be explicitly addressed for every model in the inventory. Response status is tracked in the
Model Governance Dashboard (MRC portal).

### 9.1 Q1 — Model purpose and use

*"What is the model used for, and is that use consistent with its design?"*

The model produces a seismic-resilience credit (loss frequency, no-collapse rate and a full-collapse
bps leg) consumed by the Commercial PRS Pricer as an independent peril. Use is consistent with design;
it is not a life-safety or absolute-loss model and must not be used as one.

### 9.2 Q2 — Data quality and lineage

*"Are the model inputs of sufficient quality, and is their lineage documented?"*

Inputs are the CDM-derived `AssetSeismicFeatures`; lineage runs from the v2 CDM resilience fields
(GS01–GS18) through Model C. Seismic zone and fault trace files are catchment-level spatial assets
versioned alongside the model. Missing GS flags default to the absence case (no modifier applied). Data
quality for calibration (historical seismic-loss records) is not yet established — open under SEIS-R1.

### 9.3 Q3 — Conceptual soundness

*"Is the methodology theoretically sound and appropriate?"*

The four-model decomposition (Poisson occurrence with fault-geometry spatial draw, GMPE intensity
sampling, BRI measure → modifier mapping, lognormal fragility with loss draw) is the standard PSHA/PBEE
framework used in academic and regulatory seismic risk assessment. The Poisson mainshock assumption is
well-supported for engineering annual loss estimation. The lognormal fragility function form is used
universally in HAZUS, GEM and Eurocode 8 risk assessments. The fault-trace spatial draw is a novel but
defensible extension of the PRS platform's existing river-centreline geometry.

### 9.4 Q4 — Calibration and parameters

*"How were parameters estimated, and are they appropriate?"*

All parameters are engineering-judgement seeds (version `"seed-0"`) chosen for direction and ordering,
not magnitude. Statistical calibration is an open remediation item (SEIS-R1, SEIS-R2). This is the
dominant model limitation.

### 9.5 Q5 — Implementation verification

*"Has the implementation been verified against the specification?"*

Yes, by unit tests covering each component model, the orchestrator and the PEF cascade gate, plus a
reproducibility test. The sensitivity harness exercises the full end-to-end path and must pass the seven
design requirements in Section 7.7 before the model is considered functionally verified.

### 9.6 Q6 — Sensitivity and stability

*"How sensitive are outputs to inputs and assumptions?"*

See Section 7. The model is required to exhibit monotonic and material sensitivity along all three
primary axes: distance, intensity and resilience. The intensity × resilience interaction (Table 7) must
exhibit the designed non-linearity: large BRI premium in high-hazard zones, negligible in very low
zones. Stability under draw count is adequate at n_sim = 20,000; formal stability bands are an open item.

### 9.7 Q7 — Limitations and weaknesses

*"Are the model's limitations understood and documented?"*

Yes — see Section 8 (SEIS-L1–L5 plus two further documented assumptions). The placeholder calibration
and the single fault-trace-per-catchment restriction are the most material.

### 9.8 Q8 — Ongoing monitoring

*"How will the model be monitored in production?"*

Not yet in production. A monitoring plan (drift in input distributions, backtest of realised vs.
predicted seismic-loss frequency) will be defined as part of SEIS-R3 before sign-off.

### 9.9 Q9 — Governance and approval

*"What is the approval status and who owns the model?"*

Owner: David K Kelly. Status: Development, Tier 2, RAG Amber. Not approved for production; MRC sign-off
is contingent on closing SEIS-R1–R4.

---

## 10 Change History

| Version | Date | Description |
|---|---|---|
| 0.10 | 08-June-2026 | Initial skeleton document. Architecture, mathematical framework (Models A–D), PEF cascade, three-axis sensitivity design (distance / intensity / resilience), interaction tables, sensitivity design requirements (Section 7.7), governance validation questions, and all appendix parameter tables. First-pass placeholder calibration (seed-0). |

---

## Appendix A — Occurrence Parameters (Model A)

**Table A1: Seismic hazard zone annual rates (M ≥ 5.0 mainshock) — seed-0**

| Zone Label | λ_zone (events/yr) | G-R b-value | m_max | Notes |
|---|---|---|---|---|
| Very low | 0.0005 | 1.0 | 6.5 | Intraplate stable continental |
| Low | 0.002 | 1.0 | 7.0 | e.g. UK, north-west Europe |
| Moderate | 0.008 | 1.0 | 7.5 | e.g. central Italy, Romania |
| High | 0.030 | 1.0 | 8.0 | e.g. Turkey, Greece, coastal Vietnam |
| Very high | 0.080 | 1.0 | 8.5 | e.g. Japan, Philippines, Sumatra |

**Table A2: Fault proximity modifier (GS01)**

| FaultProximityKm | GS01 present | δ_fault |
|---|---|---|
| ≥ 1.0 | Any | 0.00 |
| < 1.0 | Yes (seismically designed) | 0.00 |
| < 1.0 | No | +0.15 |

**Table A3: Soil recurrence modifier m_soil**

| CDM SoilType | Eurocode 8 Class | m_soil |
|---|---|---|
| Rock | A | 1.00 |
| Stiff soil | B | 1.00 |
| Dense soil | C | 1.10 |
| Soft soil | D | 1.15 |
| Very soft / liquefiable | E | 1.20 |

---

## Appendix B — Fault Trace File Format

The fault trace is a JSON array of [longitude, latitude] pairs ordered along the fault strike, one per
vertex. The format is identical to the river-centreline polylines in the storm module:

```json
[
  [107.020, 20.950],
  [107.080, 20.900],
  [107.140, 20.850],
  [107.200, 20.800],
  [107.260, 20.750]
]
```

**File path convention:** `catchments/<catchment_name>/fault_trace.json`

**Data source:** GEM Global Active Faults Database (primary); national geological surveys (secondary).
For the Halong catchment, the source is the Red River Fault Zone (RRFZ) — a right-lateral strike-slip
system running NW–SE through northern Vietnam with documented M7.0+ potential.

**Multiple fault sources:** Where a catchment has more than one independent active fault, each is stored
as `fault_trace_1.json`, `fault_trace_2.json`, etc., and the occurrence model runs a separate Poisson
draw per source, superposing annual rates. This is a planned extension (SEIS-R4); the current seed
implementation uses a single fault file per catchment.

---

## Appendix C — GMPE and Site Amplification Parameters (Model B)

**Table C1: GMPE selection by tectonic regime**

| Tectonic Regime | Default GMPE | Alternative |
|---|---|---|
| Active shallow crust | Boore-Atkinson 2014 (NGA-West2) | Campbell-Bozorgnia 2014 |
| Subduction interface | Zhao et al. 2006 | Atkinson-Boore 2003 |
| Subduction intraslab | Zhao et al. 2006 (intraslab) | Abrahamson et al. 2016 |
| Stable continental | Atkinson-Boore 2006 | Pezeshk et al. 2011 |

**Table C2: Site class V_S30 proxies and GS02 amplification gate**

| CDM SoilType | Eurocode 8 | V_S30 proxy (m/s) | F_a applied if GS02 absent |
|---|---|---|---|
| Rock | A | 800 | 1.00 |
| Stiff soil | B | 450 | 1.00 |
| Dense soil | C | 270 | 1.00 |
| Soft soil | D | 150 | 1.30 |
| Very soft / liquefiable | E | 100 | 1.30 |

**Table C3: GMPE total sigma (log-standard deviation)**

| GMPE | σ_total (ln units) |
|---|---|
| Boore-Atkinson 2014 | 0.65 |
| Zhao et al. 2006 | 0.68 |
| Default (seed-0) | 0.65 |

---

## Appendix D — Response Effectiveness and BRI Measure Modifiers (Model C)

**Table D1: Fragility median multiplier δ_j by BRI geoseismic measure — seed-0**

| BRI Measure | Description | Applies to | δ_j (if present) | Notes |
|---|---|---|---|---|
| GS01 | Fault distance / seismic design | Occurrence modifier | See Appendix A | |
| GS02 | Seismic foundation design | Soil F_a gate | Removes F_a = 1.30 | Class D/E only |
| GS03 | Foundation piling to rock | DS2, DS3 θ | +0.12 | |
| GS04 | Subsidence foundation design | DS2, DS3 θ | +0.08 | |
| GS08 | Lateral force resistance all floors | DS2, DS3 θ | +0.20 | |
| GS09 | Connected and braced structure | DS1–DS3 θ | +0.12 | |
| GS10 | Steel reinforced walls | DS1, DS2 θ | +0.08 | |
| GS12 | Seismic base isolation | All DS θ | +0.40 | Largest single modifier |
| GS14 | No vertical irregularities | DS2, DS3 θ | +0.15 | |
| GS15 | Flexible gas piping / seismic shut-off | PEF p_PEF | −80% on p_PEF | |
| GS16 | Seismic design review | Governance uplift | +0.03 all θ | Combined cap +0.05 (GS16–18) |
| GS17 | Seismic construction audit | Governance uplift | +0.03 all θ | Combined cap +0.05 (GS16–18) |
| GS18 | EGGAR completed | Governance + recovery | +0.03 all θ; r_acc × 1.30 | Combined cap +0.05 (GS16–18) |

Governance measures GS16–GS18 share a combined θ cap of +0.05 to prevent double-counting. They
primarily accelerate recovery rather than reduce structural fragility.

**Table D2: Recovery acceleration factor r_acc by BRI geoseismic rating**

| BRI Geoseismic Rating | r_acc | Effective T_rec multiplier |
|---|---|---|
| AA | 1.00 | × 1.0 (baseline fastest) |
| A | 0.67 | × 1.5 |
| B | 0.40 | × 2.5 |
| NR | 0.25 | × 4.0 |

---

## Appendix E — Fragility Parameters and Damage-State Tables (Model D)

**Table E1: Baseline fragility median PGA (g) by construction type — seed-0**

| Construction Type | CDM ConstructionType | DS1 θ₁ (g) | DS2 θ₂ (g) | DS3 θ₃ (g) | β |
|---|---|---|---|---|---|
| RC modern seismic design | RC_Modern | 0.15 | 0.35 | 0.65 | 0.60 |
| RC pre-code / gravity only | RC_PreCode | 0.10 | 0.22 | 0.42 | 0.60 |
| Masonry reinforced | Masonry_RC | 0.12 | 0.28 | 0.52 | 0.60 |
| Masonry unreinforced | Masonry_URM | 0.07 | 0.14 | 0.28 | 0.60 |
| Steel moment frame | Steel_MRF | 0.18 | 0.40 | 0.75 | 0.60 |
| Timber frame | Timber | 0.12 | 0.28 | 0.55 | 0.60 |
| Unknown / default | Default | 0.10 | 0.22 | 0.42 | 0.60 |

**Table E2: Loss-given-damage-state parameters (truncated lognormal, bounds [0,1])**

| Damage State | Mean L | Log-std | Notes |
|---|---|---|---|
| DS0 (None / Slight) | 0.01 | 0.50 | Negligible structural loss |
| DS1 (Moderate) | 0.10 | 0.50 | Repairable |
| DS2 (Extensive) | 0.35 | 0.40 | Major repair or partial rebuild |
| DS3 (Complete) | 1.00 | — | Fixed; no draw required |

**Table E3: Post-event functionality Q(t₀) and default recovery time T_rec by damage state**

| Damage State | Q(t₀) | T_rec default (months) | Notes |
|---|---|---|---|
| DS0 | 1.00 | 0 | Immediate full function |
| DS1 | 0.75 | 3 | Minor repairs; largely operational |
| DS2 | 0.30 | 12 | Significant works required |
| DS3 | 0.00 | 36 | Demolition and rebuild |

T_rec is divided by r_acc (Appendix D, Table D2) to give the effective recovery time for the asset's
BRI rating.

**Table E4: Post-earthquake fire (PEF) cascade probabilities — seed-0**

| Damage State | GS15 absent | GS15 present |
|---|---|---|
| DS0 / DS1 | 0.00 | 0.00 |
| DS2 | 0.08 | 0.016 |
| DS3 | 0.18 | 0.036 |

** Halong Catchment Fault Line Poly
[
  [103.980, 22.500],
  [104.200, 22.200],
  [104.450, 21.950],
  [104.700, 21.700],
  [104.950, 21.450],
  [105.200, 21.200],
  [105.450, 21.050],
  [105.680, 20.900],
  [105.850, 20.750],
  [106.100, 20.550],
  [106.400, 20.350],
  [106.700, 20.150],
  [107.000, 20.050],
  [107.300, 20.000]
]

**Thames Catchment Fault Line Poly
[
  [1.850, 50.950],
  [1.650, 50.850],
  [1.400, 50.750],
  [1.150, 50.700],
  [0.900, 50.680],
  [0.650, 50.700],
  [0.400, 50.750],
  [0.150, 50.820],
  [-0.100, 50.880],
  [-0.400, 50.950],
  [-0.700, 51.020],
  [-0.950, 51.080]
]