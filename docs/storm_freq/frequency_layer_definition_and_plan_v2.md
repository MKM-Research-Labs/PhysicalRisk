# PhysicalRisk Enhancement: Event Frequency Layer

**Document type:** Definition Document & Project Plan
**Component:** Event Frequency Model — `MKM-EF-001` (new)
**Version:** 2.1 — supersedes `frequency_layer_definition_and_plan.md` (v1.0, 2026-07-22)
**Status:** Stage 1 implemented; plan reconciled with the build
**Date:** 2026-07-22
**Owner:** CSO, MKM Research Labs

---

## 0. What changed from v1

### 0.1 What v2.1 changes

v2.0 was written before any code existed. Building it moved four things, one of
which was an outright error in v2.0's design.

| # | Change | Driver |
|---|--------|--------|
| C7 | **λ is a property of the catchment, not of a gauge.** v2.0 had per-gauge POT calibration feeding λ into pricing. That is wrong: a per-gauge exceedance rate is *already* λ × P(exceed \| event), so using it as λ squares the conditional and double-counts. λ is now a seeded per-catchment rate, and per-gauge POT became the **validation arm** | A storm arrives over the catchment and reaches every gauge in it. What differs per gauge is the conditional response, not the arrival rate |
| C8 | **The Monte Carlo year simulation is the engine, and has moved forward out of Track B.** v2.0 deferred the sampler and priced off the closed form; the order is now reversed — the simulation prices, the closed form is its self-test | The closed form is the simulation's *exact expectation*, not an approximation of it (§4.9), so it is worth more as a check than as an answer. The simulation additionally yields the annual distribution, which the closed form cannot |
| C9 | **10,000 simulated years, and the reconciliation gate is expressed in sampling standard errors rather than as a fixed percentage** | Measured on the target hardware (§6.1). A fixed 2% band false-alarmed on 17% of runs at ten thousand years while never binding at a million |
| C10 | **Landmine L3 resolved:** `num_storms` is kept and `num_events` added beside it | The storm/event distinction becomes visible in the data rather than hidden in a redefinition of a field existing consumers already read |

### 0.2 What v2.0 changed from v1

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

Simulate years. In each, draw `N ~ Poisson(λ)` qualifying events, ask of each whether
it floods gauge `g`, and record whether the year flooded:

```
P(flood in a year, g)  =  fraction of simulated years with at least one flood
Expected floods/year   =  mean number of flooding events per simulated year
Pure premium (g)       =  Expected floods/year × E[loss | flood, g]
```

with λ the **catchment** event arrival rate — an "event" being the hours-clause event,
not the individual storm (§4.3) — and the conditional response varying per gauge. λ is
a property of the catchment because a storm arrives over the catchment and reaches every
gauge in it (§3.1, C7).

The closed form `1 − exp(−λ · P(flood | event, g))` is the exact expectation of that
simulation and is retained as its reconciliation self-test (§4.9), not as the pricing
path.

---

## 2. Objectives

| # | Objective | Success measure |
|---|-----------|-----------------|
| O1 | Price reflects event frequency | AAL differs proportionally between high- and low-frequency gauges with equal conditional flood probability |
| O2 | Honest return periods | `return_period_years` derived from λ and the conditional, not from the storm count; the 100-year clamp reviewed (§9) |
| O3 | Independently validatable components | Frequency model backtestable separately from the vulnerability model; MKM-GH-001 outputs renamed so nothing claims to be annual that isn't |
| O4 | Compliance by construction | λ_g provenance recorded and reproducible (BCBS 239) — *including honest recording of generator-derived provenance, see §5*; validation artefacts auto-generated (SR 11-7) |
| O5 | No new technical debt | R1–R6 satisfied; calibration persisted through the `database` seam, not JSON |
| O6 | Quantified repricing before switchover | Per-gauge and per-property parallel-run delta report produced *before* the legacy metric is retired |

---

## 3. Scope

### 3.1 Locked decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pricing engine | **Monte Carlo year simulation.** Draw how many qualifying events arrive in a year, ask of each whether it floods, repeat. The annual flood probability is the fraction of simulated years that flooded | Retains the platform's simulation framework rather than replacing it with a formula, and yields the whole annual distribution — occurrence and aggregate views, and return periods — not just a mean |
| Closed form | **Reconciliation self-test, not an alternative answer** | It is the simulation's exact expectation (§4.9). Any disagreement beyond sampling error means one of the two is wrong, which makes it a real check rather than a restatement |
| λ granularity | **Per catchment**, not per gauge | A per-gauge exceedance rate is already λ × P(exceed \| event); using it as λ would square the conditional |
| λ source | **Configured per-catchment seed** (Thames 4.5 events/yr), with per-gauge POT as the validation arm: λ × P(exceed \| event) must reproduce each gauge's measured POT rate | Per house convention for a new probabilistic model. The data-driven estimator is blocked by §5 on synthetic catchments in any case |
| Peril scope | **Generic frequency abstraction with per-peril λ**; calibrate storm first | Wind carries the same defect; fire and seismic already have λ and fold in later |
| Event aggregation | **Maximum level across the storms of a sequence** | A PRS pays on a level being breached, and a week containing two breaches is one breach of the contract, not two. Matches hours-clause practice in reinsurance |
| Denominator | **Keep `num_storms`, add `num_events`** (landmine L3) | Existing consumers read `num_storms`; redefining it in place would change their meaning silently |
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

- ELT export in a third-party-comparable format.
- Loss-weighted aggregation. The simulation scores flood *occurrence* per event;
  attaching a loss quantum per event turns the same machinery into a full year
  loss table, but that is a separate step.
- Non-stationary / climate-conditioned λ(t). Architected for (§4.9), not implemented.
- Seasonal / NHPP rates.
- Wind, fire and seismic λ *calibration* — the abstraction accommodates them; only storm
  is calibrated in this phase.
- Changes to the inundation / spatial model or the DEM integration.
- Multi-year contract pricing and discounting.

Cross-gauge correlation is **no longer** out of scope. v2.0 deferred it; the
shared-draw design (§4.8) delivers it as a by-product of the event catalogue,
because every gauge's outcome for a given event sits in the same catalogue row.

---

## 4. Functional Specification

### 4.1 Package layout

Mirrors `src/models/seismic/occurrence/`. Every file under 300 lines (R2); no callable
code in any `__init__.py` (R4); canonical copyright header on every file (R5).

Items marked ✓ are built and under test; the rest are Stage 2 and beyond.

```
src/models/frequency/
  __init__.py             ✓ module docstring + re-exports only
  datastructures/
    _rate.py              ✓ FittedRate: lambda, threshold, diagnostics, provenance
    _diagnostics.py       ✓ annual count series, dispersion index
    _extraction.py        ✓ Peak, PotExtraction
    _provenance.py        ✓ CalibrationProvenance, ProvenanceClass
    _catalogue.py         ✓ EventCatalogue — events × gauges
    _simulation.py        ✓ EventDraws, YearSimulation
  pot/
    _threshold.py         ✓ rate-targeted threshold search
    _decluster.py         ✓ runs-method independent peaks
    _extract.py           ✓ series → declustered peaks → annual counts
  events/
    _aggregate.py         ✓ per-storm responses → per-event catalogue
  ylt/
    _sample.py            ✓ draw_event_years / apply_catalogue
    _reconcile.py         ✓ closed form and the sampling-error gate
  families/
    _poisson.py             Stage 2
    _negbin.py              Stage 2
    _select.py              Stage 2 — dispersion test + AIC tiebreak, logs overrides
  calibrate.py            ✓ orchestration: pure function of (series, config) → FittedRate
```

The composition of rate and conditional happens in `ylt/` and nowhere else.
Frequency logic must not leak into the event simulator or the pricing modules.

Note that `annualise.py`, which v2.0 nominated as the single seam, does not
exist: with the simulation as the engine the composition is the sampler itself,
and the closed form lives in `_reconcile.py` as a check rather than as the
production path.

### 4.2 Configuration

New `config/frequency/` package with `_schema.py` + `_loader.py`, following
`config/seismic/`'s hydrated-dataclass pattern. It owns (R1 — no literals outside
`config/`):

- Per-catchment event arrival rates (Thames 4.5/yr) and the default for an
  unseeded catchment.
- Declustering window (minimum inter-event separation).
- Target mean exceedance rate band for threshold selection. **Derived from the
  catchment arrival rate**, not set independently, so the qualifying-event
  threshold and λ describe the same event population by construction rather
  than by coincidence — the §4.3 alignment, enforced in one place.
- Minimum record length and event count for a per-gauge rate; regional fallback λ.
- Simulated years, seed, and the reconciliation band in sampling sigmas.
- Return-period grid for output tables.
- Dispersion-test critical value and AIC tiebreak policy (Stage 2).
- Per-peril family overrides, with the override itself logged (Stage 2, SR 11-7).

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

**Built.** The remedy as delivered:

1. `load_storms_from_sequences` tags each storm with its `sequence_id`. The key is
   **added, not substituted**, so every existing consumer of the storm fields is
   untouched. An untagged sequence falls back to a positional identity, so two
   untagged sequences cannot silently merge into one event.
2. `event_id` and `count_events` live with the loader that writes the tag, and the
   frequency aggregator imports them, so the fallback rule cannot drift between the
   two. This also keeps the dependency pointing downhill: frequency imports hazard,
   never the reverse.
3. The conditional is evaluated per event — the **maximum** peak level across the
   member storms, not one row per storm (§3.1).
4. Grouping is by storm **identity**, not position. The two coincide today, but
   position would break silently if response ordering ever changed.
5. λ is quoted in **hours-clause events per year**, matching that unit exactly.
6. `num_storms` is kept and `num_events` added beside it in both the hazard metadata
   and the build summary (landmine L3).

The physics is untouched: each storm is still routed through the gauge response model
individually. Only the grouping changes.

This step reprices on its own, before λ is applied, because the denominator changes.
It was sequenced first precisely so that its effect could be measured apart from the
λ effect — and doing so was worthwhile, because the two turned out to push the **same**
way rather than offsetting (§6.2).

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

### 4.7 The event catalogue

One row per event, one column per gauge, holding the highest level that event drove
at that gauge. This is what the year simulation resamples from.

Because every gauge's outcome for a given event sits in the **same row**, drawing an
event row draws a spatially coherent storm. The correlation between gauges is carried
by the catalogue itself, and does not have to be modelled again downstream.

The catalogue also exposes the conditional half of the decomposition directly:
`P(flood at g | event)` is the fraction of catalogue rows whose level at `g` clears the
trigger.

### 4.8 The Monte Carlo year simulation

For each simulated year: draw `N ~ Poisson(λ)` qualifying events, resample `N`
catalogue rows with replacement, and record how many of them flood. The annual flood
probability is the fraction of years with at least one flood.

**The draw is separated from its application.** `draw_event_years` runs once per run;
`apply_catalogue` runs per subject against those same draws. A storm arrives over the
catchment and reaches every gauge and property in it, so one set of draws must serve
every subject. Drawing independently per subject would discard the spatial correlation
the catalogue supplies: measured, two gauges on one reach correlate **0.78** under
shared draws and **−0.004** under independent ones, so a two-hundred-gauge book would
look two hundred times better diversified than it is.

**Resampling, not regeneration.** The catalogue's outcomes are already computed, so a
simulated year is index lookups rather than a re-run of the hydrology. That is what
makes the year count affordable (§6.1).

Outputs, all from the same run:

- **Annual flood probability** — the occurrence view; what the PRS spread is priced from.
- **Expected floods per year** — the aggregate view. It exceeds the occurrence
  probability whenever a year can carry more than one flood, which is exactly the case
  a conditional-only model cannot represent at all.
- **Return-period levels** — quantiles of the annual distribution.
- **EEF** — event exceedance frequency, valid below the 1-year return period, which
  matters at frequent-flood gauges and cannot be expressed as a probability.

All outputs carry the frequency-model identifier and calibration provenance in their
metadata.

### 4.9 The closed form, and why it is a test rather than the answer

For `N ~ Poisson(λ)` with each event flooding independently with probability `p`:

```
E[(1−p)^N] = exp(λ((1−p) − 1)) = exp(−λp)
```

so `P(at least one flood in a year) = 1 − exp(−λp)` **exactly**. The closed form is not
an approximation of the simulation — it is the simulation's expectation. The same
argument gives the aggregate view directly as `λp`.

That is precisely what makes it valuable as a check: any gap beyond sampling error means
one of the two is wrong. It is wired in as a reconciliation gate, not as the production
pricing path, because the simulation additionally yields the whole annual distribution.

The gate measures the gap in **sampling standard errors**, `sqrt(p(1−p)/n)`, against a
configured band, rather than as a fixed percentage. A fixed band cannot mean the same
thing at every year count: at ten thousand years a 2% band false-alarmed on 17% of runs,
while at a million it never bound at all. The statistic is verified to be a true
z-score — mean `|z|` measures 0.811 and 0.797 at ten and a hundred thousand years
against the theoretical `sqrt(2/π) = 0.798` — and that calibration is itself a test, so
the band cannot silently stop meaning what it says.

### 4.10 Wiring

| # | File | Change | State |
|---|------|--------|-------|
| 1 | `src/models/hazard/io/_load.py` | Sequence tagging; `event_id` / `count_events`; `num_events` in metadata and summary | **Built** |
| 2 | `src/models/hazard/builder.py:109-141` | GEV fits per-event peaks; outputs renamed to `event_exceedance_prob`; annual rates come from the simulation | Stage 3 |
| 3 | `src/port/src/property/hc/pricing/_process.py:54,119,250` | Property spread, gauge basis leg and return period become simulation-derived | Stage 4 |

### 4.11 Extension points (architected now, built later)

- λ as a process rather than a constant: the interface takes an optional covariate/time
  argument so a doubly stochastic or climate-conditioned rate can be added without an
  interface change.
- Per-peril λ registry, so wind/fire/seismic attach without restructuring.
- The simulation scores a boolean flood outcome per event. Replacing that boolean with
  a loss quantum turns the same machinery into a full year loss table without changing
  the sampler.

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

## 6. Measured results

Everything in this section is measured, not estimated. It supersedes the
corresponding estimates in v2.0.

### 6.1 Cost and accuracy of the year simulation

Apple M2, 8 cores, 8 GB. A full portfolio is 2,200 subjects (gauges plus
properties) scored against one shared set of draws.

| Simulated years | Full portfolio | Sampling error on the annual probability |
|-----------------|----------------|------------------------------------------|
| 1,000 | 0.07 s | ~5% |
| **10,000** *(configured)* | **0.40 s** | **~1.6%** |
| 100,000 | 4.1 s | ~0.5% |
| 1,000,000 | 43 s | ~0.16% |

The cost is linear in the year count and the error falls as its square root, so
this is a knob that can be turned without touching code.

**Run-to-run stability does not depend on the year count.** The seed is pinned,
so a re-run reprices identically at any setting. What the year count buys is
closeness to the true expectation, not repeatability — a distinction worth
holding onto, because the two are easily conflated when a number is described
as "noisy".

### 6.2 First repricing measurement

On a 500-event synthetic catalogue averaging 2.34 storms per event, with the
Thames seeded rate of 4.5 events/yr:

| Quantity | Value | |
|----------|-------|--|
| P(flood \| storm) — priced as annual today | 0.1301 | **1301 bps** |
| P(flood \| event) | 0.2740 | |
| λ | 4.5/yr | |
| P(flood in a year) | 0.7030 | **7030 bps** |
| **Reprice factor** | **5.40×** | reconciling at 1.23σ |

Two things to note.

First, **5.4× is above the 2–4× v2.0 estimated** in landmine L1, and the reason
is that two effects compound rather than offset. Most of the move is the missing
time dimension. But the conditional *itself* rises from 0.130 to 0.274, because
regrouping strips more from the denominator (1168 storms → 500 events) than
taking the maximum within an event costs the numerator. The denominator fix
therefore pushes the **same way** as λ. This is exactly why the two were staged
apart; had they landed together they could not have been attributed.

Second, this is a **synthetic catalogue at an arbitrary trigger level**, not the
Thames book. It establishes the mechanism and the order of magnitude. The real
figure requires a port run and is the Stage 3 deliverable.

### 6.3 Extraction against the existing calculation

On a thirty-year synthetic gauge record, at the severe trigger:

| Measure | Rate |
|---------|------|
| Exceedance **days** per year — what `statistics/timeseries.py` reports today | 1.234 |
| Declustered **events** per year | 0.967 |

A **28% overstatement**, being the mean flood duration in days. This is the
quantity §4.5's fix-and-promote removes.

The decomposition identity also holds exactly on that record: λ × P(severe \|
event) = 0.9672 against a directly measured severe rate of 0.9672. That identity
is the per-gauge validation arm described in §3.1.

---

## 7. Non-Functional Requirements

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

## 8. Project Plan

Leaves first; each stage independently shippable and tested; coverage checked at every
stage boundary (R3).

The staging has changed from v2.0. The year sampler was v2.0's Stage 6 and is now
built, because it became the engine rather than a deferred extension (C8). Stage 1
is correspondingly larger and partly done.

| Stage | Content | State | Reprices? |
|-------|---------|-------|-----------|
| **1a** | Event-definition alignment (§4.3); event catalogue; POT extraction with declustering; per-catchment λ; `num_events` | **Done** | Denominator only, and not yet consumed |
| **1b** | Monte Carlo year sampler; shared draws; closed-form reconciliation gate | **Done** *(was Stage 6)* | Not yet consumed |
| **1c** | `frequency_per_year` fix-and-promote (§6.3); λ and provenance persisted through the `database` seam | To do | No |
| **2** | Poisson / NegBin families; dispersion selection; override logging; POT round-trip validation (§5) | To do | No |
| **3** | Simulation wired into `builder.py`; legacy metric behind a deprecation flag; **parallel-run repricing report on the real book** | To do | **Yes** |
| **4** | Property and gauge legs in `_process.py`; return periods; clamp review (§9); wind-leg decision (L6) | To do | **Yes** |
| **5** | Governance: inventory entry, LaTeX documentation, registry wiring, auto-generated validation report, monitoring job | To do | No |
| **6** | *Separate approval:* loss-weighted YLT, ELT export, wind λ calibration, seasonal NHPP | To do | — |

**Stage acceptance.**

- **S1a/S1b** — *met.* Event-granular loader covered; catalogue and sampler under test;
  simulation reconciles with its closed form; no pricing path consumes λ. 204 tests,
  100% coverage on the frequency packages and `hazard/io`.
- **S1c** — POT series reproducibly generated for all gauges; provenance complete and
  persisted through the seam; the day-count consumers repointed.
- **S2** — families pass property tests (mean/variance recovery); calibration
  deterministic under fixed inputs; per-gauge selection report generated; round-trip
  recovers the injected rate within tolerance.
- **S3** — parallel-run report produced on the real book, quantifying repricing per
  gauge; legacy metric still available behind the flag; simulated and closed-form
  annual probabilities reconcile within the sampling band.
- **S4** — property-level repricing quantified; clamp decisions recorded; wind-leg
  decision recorded; UI and EOD consumers verified against the renamed fields.
- **S5** — validation report reviewed and signed off; monitoring scheduled; legacy metric
  formally deprecated.

---

## 9. Migration landmines

These bite between Stage 3 and Stage 5. Each needs a decision before Stage 3 lands.

| # | Landmine | Detail | Status |
|---|----------|--------|--------|
| L1 | **Magnitude of the reprice** | λ ≡ 1 today. First measurement is **5.40×** on a synthetic catalogue (§6.2) — above v2.0's 2–4× estimate, because the denominator change compounds with λ instead of offsetting it. | **Open, and larger than expected.** The Stage 3 parallel-run report on the real book is the gating business artefact. No switchover without it. |
| L2 | **Two compensating hacks become distortions** | `src/models/hazard/builder.py:87` clamps `exc_prob` up to 0.01; `MAX_RETURN_PERIOD: 100` in `config/port/_storm.py` caps return periods. Both exist *because* return periods were fake. | **Open.** Once return periods are real, both must be reviewed or removed. Removing them widens the tail — quantify alongside L1. |
| L3 | **`num_storms` is persisted and rendered** | A stored field read by the UI, the blotter and EOD. | **Resolved.** `num_storms` kept, `num_events` added beside it. Verified against the CDM property editor, hazard, stormgauge and intensity suites — no consumer changed. |
| L4 | **EOD history spans the cut** | Stored `annual_hazard_rate_*` values change semantics *and* magnitude; historical series become non-comparable across the switchover date. | **Open.** Mark the cut in the EOD record; do not silently backfill. |
| L5 | **Per-storm `flood_events` collapse** | Under an event definition, several storms in a sequence become one event; per-property flood counts drop even before λ is applied. | **Open at the property leg.** Measured at the gauge leg: 2.34 storms per event, and the conditional *rose* rather than fell (§6.2). The property pipeline still counts per storm. |
| L6 | **Wind leg diverges** | `_wind_union` (`_process.py:70`) divides by `num_storms` too. If flood moves to an annual basis and wind does not, the BOW/BAW union and joint legs become internally inconsistent. | **Open.** Either move both at Stage 4 or explicitly freeze the wind leg on the legacy metric with a recorded justification. |
| L7 | **Correlation is now load-bearing** | Portfolio risk depends on subjects sharing one set of event draws. A future caller that runs the single-subject convenience wrapper per subject would silently decorrelate the book — measured at 0.78 versus −0.004 (§4.8). | **Open.** Guard at the portfolio entry point when Stage 4 wires it, and treat as a review point for any new caller. |

---

## 10. Governance and registration

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

## 11. Risks and Assumptions

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

## 12. Glossary

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
