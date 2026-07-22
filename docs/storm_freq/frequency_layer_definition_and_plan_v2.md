# PhysicalRisk Enhancement: Event Frequency Layer

**Document type:** Definition Document & Project Plan
**Component:** Event Frequency Model — `MKM-EF-001` (new)
**Version:** 2.0 — supersedes `frequency_layer_definition_and_plan.md` (v1.0, 2026-07-22)
**Status:** Draft for review
**Date:** 2026-07-22
**Owner:** CSO, MKM Research Labs

---

## 0. What changed from v1

v1 diagnosed the problem correctly. v2 keeps the diagnosis and reworks the plan against
what the codebase actually does. Six substantive changes:

| # | Change | Driver |
|---|--------|--------|
| C1 | The layer is no longer greenfield — it is a **port of the existing seismic/fire occurrence pattern** onto the storm chain | `src/models/seismic/occurrence/` and `src/models/fire/initiation.py` already implement precisely the proposed λ → Poisson → event → severity construction. Storm/flood is the outlier, not the pioneer. |
| C2 | Delivery is split into **Track A (analytic annualisation)** and **Track B (ELT→YLT)**; only Track A is in scope | v1 went straight to the YLT sampler before any pricing benefit landed. Track A fixes pricing at one node without touching port generation. |
| C3 | Scope is **generic per-peril frequency**, calibrated for storm first | The wind leg carries the identical defect; fire and seismic already carry their own λ. A flood-only layer would need a second frequency layer within months. |
| C4 | New §5: **λ provenance is currently circular** on synthetic catchments | The "historical" gauge series is generated *from* the frequency field it would be used to calibrate. This materially changes what Stage 1 can claim. |
| C5 | The v1 "critical alignment task" (§8) is **already broken in a specific, locatable way** — sequences are shredded into storms before the denominator is taken | `src/models/hazard/io/_load.py:52` |
| C6 | NFRs restated against the actual house rules (`docs/rules/coding_rules.md` R1–R6) and the actual audit tooling | v1 cited `split_audit.py`, which no longer exists, specified 100% branch coverage against a house rule of ≥99% line, and did not mention the `database` seam (R6) at all. |

---

## 1. Background and Problem Statement

### 1.1 Current state

The simulator generates synthetic storm events and evaluates, at each river gauge, whether
a storm produces a flood. Insurance cost is priced as the ratio of flooding storms to
total storms. This is a **conditional probability** — P(flood | storm) — dimensionless
with respect to time.

### 1.2 The defect, with evidence

The defect is not conceptual. It is written out in three places:

| Location | Code | Meaning |
|----------|------|---------|
| `src/port/src/property/hc/pricing/_process.py:54` | `spread_bps = (flood_count / num_storms) * 10000` | The property PRS spread **is** P(flood\|storm), expressed in bps |
| `src/port/src/property/hc/pricing/_process.py:250` | `return_period_yrs = num_storms / flood_count` | The assumption stated explicitly: **1 storm = 1 year**, λ ≡ 1.0 |
| `src/models/hazard/builder.py:109-141` | GEV fitted to the peak level of *every* simulated storm; `exceedance_probability(...)` assigned to `annual_exceedance_prob` and `annual_hazard_rate_*` | A per-event conditional is relabelled *annual* at the point of assignment |

The same ratio construction appears on the gauge basis leg (`_process.py:119`) and the
wind leg (`_process.py:70`, via `_wind_union`).

### 1.3 What is already correct

The downstream plumbing is rate-shaped and needs no rework:

- `src/models/hazard/gev.py:66` `compute_term_structure` is already a Poisson compounding
  (`P(≥1 flood by year t) = 1 − e^{−λt}`).
- `src/models/hazard/prs_analytical.py:100` already converts an annual probability to a
  continuous hazard rate via `−log(1−p)`.

Both are being fed a per-event number. **The remedy is a substitution at one node, not a
pricer rewrite.**

### 1.4 The pattern already exists in this repo

Two production models already do exactly what v1 proposed to invent:

- `src/models/seismic/occurrence/` — `_rates.py` computes a per-asset annual λ;
  `_simulate.py:89` draws `rng.poisson(lambda_annual * horizon_years, size=n_sim)` and
  instantiates events where the count ≥ 1; severity and damage follow.
- `src/models/fire/initiation.py` — the same construction ("Model A — Poisson
  initiation").

MKM-EF-001 should mirror this package shape rather than introduce a parallel
`FrequencyModel` abstraction with different conventions.

### 1.5 Remedy (summary)

```
Annual flood frequency (gauge g)  =  λ_g × P(flood | event, g)
Annual exceedance probability     =  1 − exp(−λ_g × P(flood | event, g))
Pure premium (gauge g)            =  λ_g × P(flood | event, g) × E[loss | flood, g]
```

with λ_g the calibrated annual **event** arrival rate — where "event" is the
hours-clause event, not the individual storm (see §3.2).

---

## 2. Objectives

| # | Objective | Success measure |
|---|-----------|-----------------|
| O1 | Price reflects event frequency | AAL differs proportionally between high- and low-frequency gauges with equal conditional flood probability |
| O2 | Honest return periods | `return_period_years` derived from λ and the conditional, not from the storm count; the 100-year clamp reviewed (§8) |
| O3 | Independently validatable components | Frequency model backtestable separately from the vulnerability model; MKM-GH-001 outputs renamed so nothing claims to be annual that isn't |
| O4 | Compliance by construction | λ_g provenance recorded and reproducible (BCBS 239) — *including honest recording of generator-derived provenance, see §5*; validation artefacts auto-generated (SR 11-7) |
| O5 | No new technical debt | R1–R6 satisfied; calibration persisted through the `database` seam, not JSON |
| O6 | Quantified repricing before switchover | Per-gauge and per-property parallel-run delta report produced *before* the legacy metric is retired |

---

## 3. Scope

### 3.1 Locked decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Delivery | **Track A first** — analytic annualisation at the hazard-curve node. Track B (ELT→YLT, AEP) is a separate approval | Track A is shippable without touching port generation, timeseries generation or the per-property `flood_events` pipeline |
| Peril scope | **Generic frequency abstraction with per-peril λ**; calibrate storm first | Wind carries the same defect; fire and seismic already have λ and fold in later |
| λ source | **POT over the gauge record**, with a configured regional fallback for short records, choice recorded in provenance | Matches the target architecture for real EA/NRFA data; see §5 for the synthetic-catchment caveat |
| Chain position | **Downstream of storm severity** | See §3.3 |
| Model ID | `MKM-EF-001` — *Event Frequency Model* | `EF` is unused in `docs/models/governance_data/model_inventory.json` |
| Tier | **1** (proposed) | λ is a linear multiplier on every PRS spread — more material than MKM-SI-001 (Tier 2, "not directly into pricing"). Peers at Tier 1: MKM-GH-001, MKM-PR-001, MKM-DE-001 |

### 3.2 In scope

- Frequency abstraction with Poisson and Negative Binomial implementations, per-peril.
- Calibration pipeline: POT extraction → declustering → arrival-rate estimation →
  dispersion diagnostics → per-gauge model selection.
- **Event-definition alignment**: the hours-clause event (a storm *sequence*), not the
  individual storm, becomes the unit of both λ and the conditional. See §4.3.
- The `annualise` seam and its wiring into `MKM-GH-001`.
- Repricing of the property and gauge PRS legs.
- Calibration persistence and provenance through the `database` seam.
- Validation module: dispersion test, count backtest, threshold sensitivity,
  reconciliation, POT round-trip (§5).
- Config schema extension in a new `config/frequency/` package.
- Governance pack: inventory entry, LaTeX model documentation, registry wiring.

### 3.3 Chain position

```
MKM-SI-001 (severity)  →  MKM-SG-001 (gauge response)  →  MKM-GH-001 (GEV: per-EVENT exceedance)
                                                            ↓
                                                       MKM-EF-001 (λ_g, annualisation)
                                                            ↓
                                                       MKM-PR-001 (PRS pricing)
```

Physically, frequency is a *sibling* of severity rather than a descendant. As an
implementation seam, downstream is the right choice: nothing upstream changes,
MKM-GH-001 is merely **relabelled** (its outputs become honest per-event conditionals),
and `builder.py` is the single switch point.

Inventory `upstream_models` / `downstream_models` must be updated on MKM-GH-001 and
MKM-PR-001 accordingly (chain consistency is scanned by full-audit §4.7).

### 3.4 Out of scope (this phase)

- **Track B**: ELT export, YLT sampler, AEP (aggregate) construction, portfolio
  aggregation and cross-gauge count correlation.
- Non-stationary / climate-conditioned λ(t). Architected for (§4.7), not implemented.
- Seasonal / NHPP rates.
- Wind, fire and seismic λ *calibration* — the abstraction accommodates them; only storm
  is calibrated in this phase.
- Changes to the inundation / spatial model or the DEM integration.
- Multi-year contract pricing and discounting.

---

## 4. Functional Specification

### 4.1 Package layout

Mirrors `src/models/seismic/occurrence/`. Every file under 300 lines (R2); no callable
code in any `__init__.py` (R4); canonical copyright header on every file (R5).

```
src/models/frequency/
  __init__.py             # module docstring + re-exports only
  datastructures/
    _rate.py              # FittedRate: lambda, family, params, provenance
    _diagnostics.py       # dispersion index, log-likelihood, AIC
  pot/
    _threshold.py         # threshold selection + stability diagnostics
    _decluster.py         # minimum inter-event separation
    _extract.py           # series → declustered exceedances → annual count series
  families/
    _poisson.py
    _negbin.py
    _select.py            # dispersion test + AIC tiebreak; logs any override
  annualise.py            # p_annual = 1 - exp(-λ · p_event)     ← the single seam
  calibrate.py            # orchestration: pure function of (series, config) → FittedRate
```

`annualise.py` is deliberately tiny and deliberately the only place the composition
happens. Frequency logic must not leak into the event simulator or the pricing modules;
composition occurs at this seam only.

### 4.2 Configuration

New `config/frequency/` package with `_schema.py` + `_loader.py`, following
`config/seismic/`'s hydrated-dataclass pattern. It owns (R1 — no literals outside
`config/`):

- Target mean exceedance rate band for threshold selection.
- Declustering window (minimum inter-event separation).
- Dispersion-test critical value; AIC tiebreak policy.
- Minimum record length for per-gauge calibration; regional fallback λ.
- Return-period grid for output tables.
- Per-peril family overrides (with the override itself logged — SR 11-7).

It also absorbs an existing orphan: `src/models/intensity/distribution/_core.py:198`
carries `storms_per_year: float = 20` as a default argument — an undocumented frequency
assumption living inside the severity model, and an R1 breach. That parameter moves here
and the severity model takes it as an injected value.

### 4.3 Event-definition alignment (v1 §8's "critical alignment task")

This is not a hypothetical risk; it is already wrong, and locatably so.

MKM-SS-001 produces **sequences** — 1 to 5 related storms fitted inside a 168-hour
insurance hours clause (`EVENT_WINDOW_HOURS` in `config/port/_storm.py`). But
`src/models/hazard/io/_load.py:52-61` (`load_storms_from_sequences`) flattens every
sequence into its member storms before the hazard model sees them. `num_storms` is
therefore 1–5× the event count, and today's denominator is **neither events nor years**.

Remedy:

1. Add an event-granular loader alongside the existing flattening one (which stays for
   consumers that genuinely want individual storms).
2. The conditional is evaluated per sequence — the gauge response over the whole 168-hour
   window, i.e. the maximum peak level across member storms, not one row per storm.
3. λ is quoted in **hours-clause events per year**, matching that unit exactly.

This step alone reprices, before λ is applied — the denominator changes. It is
sequenced first (Stage 1) precisely so that its effect can be measured in isolation from
the λ effect.

### 4.4 Frequency abstraction

A single interface, per-peril, following the seismic `_rates.py` / `_simulate.py` split:

- `fit(counts: AnnualCountSeries) -> FittedRate`
- `annual_rate() -> float`
- `sample_annual_count(rng) -> int`   *(unused in Track A; required by Track B)*
- `diagnostics() -> FrequencyDiagnostics`

| Implementation | Distribution | Selected when |
|----------------|--------------|---------------|
| `PoissonFrequency` | Poisson(λ) | Dispersion index ≈ 1 (default) |
| `NegativeBinomialFrequency` | NegBin(r, p) | Overdispersed counts (variance > mean) |

Selection is data-driven per gauge via the dispersion index with an AIC tiebreak,
recorded in the calibration output. A config override may force a family; the override is
logged with its justification.

### 4.5 Calibration pipeline (POT)

Per gauge, from the gauge level record:

1. **Threshold selection** — default: the threshold yielding a target mean exceedance
   rate (configurable), anchored on bankfull discharge where available. Diagnostics:
   mean-excess and threshold-stability.
2. **Declustering** — enforce a minimum inter-event separation so peaks are independent.
   Record the rule applied.
3. **Arrival rate** — λ̂ = exceedances / years of record; the annual count series is
   retained for dispersion testing.
4. **Dispersion test and family selection** — per §4.4.
5. **Severity cross-check (validation only)** — fit a GPD to exceedance magnitudes and
   compare against the simulator's implied severity at that gauge. Divergence beyond
   tolerance raises a validation flag; it never silently recalibrates anything.

**Prior art to fix, not to write from scratch.**
`src/models/statistics/timeseries.py:103-122` already computes a per-gauge
`frequency_per_year` for alert / warning / severe. It counts **days over threshold**, not
declustered events — POT with step 2 missing — and therefore overstates λ by roughly the
mean event duration in days. Stage 1 is a fix-and-promote of this calculation into the
new package, with the existing consumers repointed.

**Provenance (BCBS 239).** Every `FittedRate` carries: source dataset identifier and
version, record period, threshold, declustering rule, family selected and why, fit
timestamp, code version, config hash, and — per §5 — a **provenance class**
(`observed` / `generator-derived` / `regional-fallback`). Calibration is a pure function
of (data, config): re-running with identical inputs must reproduce identical outputs, and
this is regression-tested against a golden master.

### 4.6 Persistence

`FittedRate` and its provenance are written and read **exclusively through the
`src/database/` seam** (R6). No JSON artefact is created at any point — full-audit §4.5
is walking `.json` writes toward zero tolerance and a new model must be born DB-native.

Deliverables: a new table plus Alembic migration following the pattern of
`src/database/_pg/migrations/versions/cb463f03ebec_create_gauge_hazard_curve_prs_trade_eod_.py`,
with matching entries in `src/database/_pg/_models.py` and `_columns.py`, and accessor
functions in the `database` package API.

Note the CLI gotcha: any new command touching the seam must call `use_configured_backend()`
before its first seam call — tests bind backends themselves and will not catch its
absence.

### 4.7 Wiring — three edits

Only the third reprices via λ; the first reprices via the denominator (§4.3).

| # | File | Change |
|---|------|--------|
| 1 | `src/models/hazard/io/_load.py:52` | Add the event-granular loader; sequences stop being shredded before the denominator is taken |
| 2 | `src/models/hazard/builder.py:109-141` | GEV fits per-event peaks; outputs renamed to `event_exceedance_prob`; `annual_hazard_rate_*` populated via `annualise()` |
| 3 | `src/port/src/property/hc/pricing/_process.py:54,119,250` | Property spread, gauge basis leg and return period become λ-based |

### 4.8 Pricing outputs (Track A)

- **AAL / pure premium** — `λ_g × P(flood|event, g) × E[loss|flood, g]`.
- **Annual exceedance probability** — `1 − exp(−λ_g · p_event)`, replacing the current
  direct assignment.
- **Return periods** — derived from the annualised probability; the compensating clamps
  reviewed (§8).
- **EEF** — event exceedance frequency, valid below the 1-year return period, which
  matters at frequent-flood gauges and cannot be expressed by a probability at all.

OEP and AEP curves require the YLT and are **Track B**. Track A can state OEP
analytically under Poisson (`1 − exp(−λ S(x))`) but not empirically, and AEP not at all.

All outputs carry the frequency-model identifier and calibration provenance in their
metadata.

### 4.9 Extension points (architected now, built later)

- λ as a process rather than a constant: the interface takes an optional covariate/time
  argument so a doubly stochastic or climate-conditioned rate can be added without an
  interface change.
- `sample_annual_count` exists from day one, unused by Track A, so Track B needs no
  interface change.
- Per-peril λ registry, so wind/fire/seismic attach without restructuring.

---

## 5. The λ provenance problem (new in v2)

**Finding.** On synthetic catchments, calibrating λ from the gauge "historical" record is
circular.

`src/models/statistics/synthetic.py:122-124` generates the daily series by injecting
severe exceedances at exactly the rate implied by the gauge's `FrequencyExceedLevel3`
field:

```python
severe_floods_expected    = max(freq_exceed_level3, 1)
severe_flood_prob_per_day = severe_floods_expected / (years * 365)
```

and `FrequencyExceedLevel3` is itself produced by
`src/port/rand/shared/gauge/gauge_field_generators.py:168-170` as a `random.choices(...)`
draw over a five-year window.

A POT extraction over that series therefore recovers the injected rate. **The only
per-gauge frequency number the platform currently holds is a random integer.**

**Consequences.**

1. v1 §8's stated risk ("short or gappy records → noisy λ̂") is the wrong risk. The real
   one is that λ has no observational content on synthetic catchments.
2. It does not invalidate the POT pipeline. POT is exactly what would be run against real
   EA / NRFA series, and building it now is correct.
3. It does change what Stage 1 may claim. The provenance class must record
   `generator-derived`, not `observed`, and the validation report must say so.

**Approach adopted.**

- **Now:** build POT as specified. On synthetic catchments, validate it by **round-trip** —
  the extracted λ̂ must recover the injected rate within tolerance once declustering is
  accounted for. This is a genuinely strong test of the extraction code, and it is
  labelled as such rather than presented as calibration.
- **Follow-on (separate approval, requires port regeneration):** make
  `FrequencyExceedLevel3` a *modelled* field rather than a random one — give the gauge
  generator a catchment-level λ prior so synthetic frequencies are physically plausible
  and spatially coherent (gauges on the same reach should not carry independent λ). This
  touches the shared `rand` tree and requires a port regeneration, which is not
  undertaken without explicit instruction.

---

## 6. Non-Functional Requirements

Restated against `docs/rules/coding_rules.md`.

| Rule | Requirement for this project |
|------|------------------------------|
| R1 — no params outside `config` | All thresholds, declustering windows, selection criteria, fallback λ and return-period grids live in `config/frequency/`. The orphan `storms_per_year=20` (§4.2) is absorbed. |
| R2 — no file over 300 lines | Package layout per §4.1 from the outset. |
| R3 — ≥99% coverage, per stage | Verified at the end of **each** stage, not at the end. (v1 specified 100% branch coverage; aligning to the house rule avoids a bespoke standard for one package.) Plus property-based tests for mean/variance recovery and a golden-master calibration regression. |
| R4 — no functions in `__init__.py` | Re-exports only. |
| R5 — canonical copyright header | On every new `.py`. Enforced by the self-healing header audit. |
| R6 — data store only via `database` | §4.6. Zero direct SQL, ORM or connections; zero JSON artefacts. |

Additional:

- **Reproducibility** — seeded RNG throughout; calibration and simulation reproducible
  from (data version, config version, seed).
- **Audit** — structured run log: inputs, config hash, code version, outputs, validation
  flags.
- **Verification tooling** — the full audit (`docs/models/full_audit`), *not*
  `split_audit.py`, which v1 cited and which no longer exists. Relevant sections: §4.3
  (path definitions), §4.5 (JSON files), §4.6 (database usage), §4.7 (model chain
  consistency).

---

## 7. Project Plan

Leaves first; each stage independently shippable and tested; coverage checked at every
stage boundary (R3).

| Stage | Content | Reprices? |
|-------|---------|-----------|
| **1** | Event-definition alignment (§4.3); POT extraction with declustering; `frequency_per_year` fix-and-promote; λ persisted through the seam with provenance | Denominator only |
| **2** | Poisson / NegBin families; dispersion selection; diagnostics; override logging; POT round-trip validation (§5) | No |
| **3** | `annualise()` wired into `builder.py`; legacy metric behind a deprecation flag; **parallel-run repricing report** | **Yes — via λ** |
| **4** | Property and gauge legs in `_process.py`; return periods; clamp review (§8) | **Yes** |
| **5** | Governance: inventory entry, LaTeX documentation, registry wiring, auto-generated validation report, monitoring job | No |
| **6** | *Separate approval:* Track B — ELT export, YLT sampler, OEP/AEP, portfolio aggregation, wind λ, seasonal NHPP, cross-gauge dependence | — |

**Stage acceptance.**

- **S1** — POT series reproducibly generated for all gauges; provenance complete;
  event-granular loader covered; no pricing path yet consumes λ.
- **S2** — families pass property tests (mean/variance recovery); calibration
  deterministic under fixed inputs; per-gauge selection report generated; round-trip
  recovers the injected rate within tolerance.
- **S3** — parallel-run report produced, quantifying repricing per gauge; legacy metric
  still available behind the flag; analytical and empirical AAL reconcile within Monte
  Carlo error.
- **S4** — property-level repricing quantified; clamp decisions recorded; UI and EOD
  consumers verified against the renamed fields.
- **S5** — validation report reviewed and signed off; monitoring scheduled; legacy metric
  formally deprecated.

---

## 8. Migration landmines

These are the things that will bite between Stage 3 and Stage 5. Each needs a decision
before Stage 3 lands.

| # | Landmine | Detail | Action |
|---|----------|--------|--------|
| L1 | **Magnitude of the reprice** | λ ≡ 1 today. A plausible λ of 2–4 events/year scales spreads by roughly that factor at small p. This is a 2–4× move on **every** PRS quote. | The Stage 3 parallel-run report is the gating business artefact. No switchover without it. |
| L2 | **Two compensating hacks become distortions** | `src/models/hazard/builder.py:87` clamps `exc_prob` up to 0.01; `MAX_RETURN_PERIOD: 100` in `config/port/_storm.py` caps return periods. Both exist *because* return periods were fake. | Once return periods are real, both must be reviewed or removed. Removing them widens the tail — quantify alongside L1. |
| L3 | **`num_storms` is persisted and rendered** | It is a stored field read by the UI, the blotter and EOD. Changing the denominator to events changes its meaning and value. | Either keep `num_storms` and add `num_events`, or rename with a migration. Decide before Stage 1 ships. |
| L4 | **EOD history spans the cut** | Stored `annual_hazard_rate_*` values change semantics *and* magnitude; historical series become non-comparable across the switchover date. | Mark the cut in the EOD record; do not silently backfill. |
| L5 | **Per-storm `flood_events` collapse** | Under an event definition, several storms in a sequence become one event; per-property flood counts drop even before λ is applied. | This is the §4.3 denominator effect. Measure it separately at Stage 1 so it is not confused with the λ effect at Stage 3. |
| L6 | **Wind leg diverges** | `_wind_union` (`_process.py:70`) divides by `num_storms` too. If flood is annualised and wind is not, the BOW/BAW union and joint legs become internally inconsistent. | Either annualise both at Stage 4 or explicitly freeze the wind leg on the legacy metric with a recorded justification. |

---

## 9. Governance and registration

Per `docs/models/new_model.md`, and noting that a new model doc must be wired into **five
registries** plus the Makefile filter:

1. Inventory entry `MKM-EF-001` in `docs/models/governance_data/model_inventory.json` —
   tier 1 (proposed), category Hazard, `source_module: src/models/frequency/`,
   `upstream_models: [MKM-GH-001]`, `downstream_models: [MKM-PR-001]`.
2. Corresponding `upstream_models` / `downstream_models` amendments on MKM-GH-001 and
   MKM-PR-001 (full-audit §4.7 scans chain consistency; the chain is hand-maintained).
3. `docs/models/event_frequency/event_frequency.tex` + Makefile, with the standard
   sections and `\input{test_results}` / `\input{sensitivity_tables}`.
4. Registry wiring (five registries + Makefile filter).
5. Assumptions and limitations recorded — including, explicitly, the §5 provenance
   limitation and the stationarity assumption.

**Validation plan (SR 11-7).** Conceptual soundness; per-gauge count backtesting on a
held-out split; dispersion coverage reporting (share of gauges selecting NegBin);
threshold sensitivity (λ̂ and AAL under ±1 threshold band); reconciliation (analytical
vs empirical AAL); POT round-trip (§5); annual recalibration with a drift alert; and an
effective-challenge artefact emitted on every run.

Note that benchmarking return-period levels against published national flood-frequency
estimates — v1's validation test 6 — is **not meaningful** while catchments are synthetic.
It is retained in the plan but flagged as pending real gauge data.

---

## 10. Risks and Assumptions

| Risk / assumption | Impact | Mitigation |
|-------------------|--------|------------|
| λ has no observational content on synthetic catchments (§5) | Pricing is precise but not accurate; validation claims could overstate | Provenance class recorded on every fitted rate; round-trip framed as extraction validation, not calibration; real-data path built and ready |
| Repricing of 2–4× on every quote (L1) | Client and book impact | Stage 3 parallel-run report before switchover; staged rollout; legacy metric retained behind a flag |
| Event-definition change reprices before λ does (L5) | Two effects confounded in the impact analysis | Sequenced deliberately: Stage 1 isolates the denominator effect, Stage 3 the λ effect |
| Threshold choice materially moves λ̂ | Pricing instability | Sensitivity test; threshold governance in `config/frequency/` with a change log |
| Overdispersion ignored where present | Understated tail | NegBin selected wherever the dispersion test rejects Poisson |
| Stationarity assumed | Understated forward risk under climate change | Explicit limitation in the model documentation; drift monitoring; Track B roadmap |
| Wind leg left on the legacy metric (L6) | Internally inconsistent peril comparison | Decide explicitly at Stage 4; do not leave implicit |
| Clamp removal widens the tail (L2) | Compounds L1 | Quantify jointly with the repricing report, not separately |

---

## 11. Glossary

- **AAL** — Average Annual Loss; expected loss per year.
- **AEP** — Aggregate Exceedance Probability; P(total annual loss > x). *Track B.*
- **OEP** — Occurrence Exceedance Probability; P(largest single event loss in a year > x). *Track B.*
- **EEF** — Event Exceedance Frequency; annual frequency (not probability) of events exceeding a level.
- **ELT / YLT** — Event Loss Table / Year Loss Table. *Track B.*
- **Event** — here, the insurance hours-clause event (a storm *sequence* within
  `EVENT_WINDOW_HOURS`), not an individual storm. See §4.3.
- **POT** — Peaks Over Threshold; extreme-value sampling of all independent exceedances
  above a threshold.
- **GPD** — Generalised Pareto Distribution; standard model for POT exceedance magnitudes.
- **Dispersion index** — variance/mean of annual counts; ≈1 supports Poisson, >1 indicates
  overdispersion.
- **NHPP** — Non-Homogeneous Poisson Process; time-varying arrival rate. *Track B.*
- **Provenance class** — `observed` / `generator-derived` / `regional-fallback`; records
  what a fitted λ is actually based on. See §5.
