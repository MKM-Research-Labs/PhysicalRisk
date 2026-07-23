# PhysicalRisk Enhancement: Event Frequency Layer

**Document type:** Definition Document & Project Plan
**Component:** Event Frequency Model — `MKM-EF-001` (new)
**Version:** 2.2 — supersedes `frequency_layer_definition_and_plan.md` (v1.0, 2026-07-22)
**Status:** Stages 1a/1b, 3 and 4 implemented and wired to pricing
**Date:** 2026-07-23
**Owner:** CSO, MKM Research Labs

---

## 0. What changed from v1

### 0.1 What v2.2 changes

Wiring the layer into pricing and calibrating it on real halong data
exposed three defects — two of them pre-existing and more serious than the
problem this model was written to fix.

| # | Change | Driver |
|---|--------|--------|
| C11 | **The gauge response model was unseeded.** Fixed. Hazard curves were irreproducible at roughly ±40%; they are now byte-identical across rebuilds | Pre-existing, predating MKM-EF-001. Three `np.random.uniform` calls, two of which redrew each gauge's *character* on every build. The BCBS 239 reproducibility claim did not hold for this chain (§6.1) |
| C12 | **Missing mild events were reweighted onto the severe end.** Fixed by scaling the conditional by catalogue *coverage* rather than renormalising the weights | The catalogue holds no minimal or baseline events, and those carry 73% of the population mass. A configured 8% severe-or-worse share became an effective 29.6%, a 3.7× overstatement (§4.9) |
| C13 | **Stages 3 and 4 are built**: gauge, property, commercial and wind legs all price off the frequency layer | The reprice is **downward**, 0.35×–0.56× at the calibrated weights (§6.3), not the upward move earlier drafts predicted |
| C14 | **Two field-naming traps documented**, both of which produced confident wrong answers before being caught | `flood_events[].storm_id` holds *sequence* identifiers; `_load_gauge_hazard_curves` returns the *sequence* count while its caller names it `num_storms` (§4.11) |

### 0.2 What v2.1 changed

v2.0 was written before any code existed. Building it moved four things, one of
which was an outright error in v2.0's design.

| # | Change | Driver |
|---|--------|--------|
| C7 | **λ is a property of the catchment, not of a gauge.** v2.0 had per-gauge POT calibration feeding λ into pricing. That is wrong: a per-gauge exceedance rate is *already* λ × P(exceed \| event), so using it as λ squares the conditional and double-counts. λ is now a seeded per-catchment rate, and per-gauge POT became the **validation arm** | A storm arrives over the catchment and reaches every gauge in it. What differs per gauge is the conditional response, not the arrival rate |
| C8 | **The Monte Carlo year simulation is the engine, and has moved forward out of Track B.** v2.0 deferred the sampler and priced off the closed form; the order is now reversed — the simulation prices, the closed form is its self-test | The closed form is the simulation's *exact expectation*, not an approximation of it (§4.10), so it is worth more as a check than as an answer. The simulation additionally yields the annual distribution, which the closed form cannot |
| C9 | **10,000 simulated years, and the reconciliation gate is expressed in sampling standard errors rather than as a fixed percentage** | Measured on the target hardware (§6.1). A fixed 2% band false-alarmed on 17% of runs at ten thousand years while never binding at a million |
| C10 | **Landmine L3 resolved:** `num_storms` is kept and `num_events` added beside it | The storm/event distinction becomes visible in the data rather than hidden in a redefinition of a field existing consumers already read |

### 0.3 What v2.0 changed from v1

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
simulation and is retained as its reconciliation self-test (§4.10), not as the pricing
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
| Closed form | **Reconciliation self-test, not an alternative answer** | It is the simulation's exact expectation (§4.10). Any disagreement beyond sampling error means one of the two is wrong, which makes it a real check rather than a restatement |
| λ granularity | **Per catchment**, not per gauge | A per-gauge exceedance rate is already λ × P(exceed \| event); using it as λ would square the conditional |
| λ source | **Configured per-catchment seed** (Thames 4.5 events/yr), with per-gauge POT as the validation arm: λ × P(exceed \| event) must reproduce each gauge's measured POT rate | Per house convention for a new probabilistic model. The data-driven estimator is blocked by §5 on synthetic catchments in any case |
| Peril scope | **Generic frequency abstraction with per-peril λ**; calibrate storm first | Wind carries the same defect; fire and seismic already have λ and fold in later |
| Event aggregation | **Maximum level across the storms of a sequence** | A PRS pays on a level being breached, and a week containing two breaches is one breach of the contract, not two. Matches hours-clause practice in reinsurance |
| Absent categories | **Scale the conditional by catalogue coverage**, do not renormalise the weights | Mild events that never reach a trigger belong in the denominator at zero. Renormalising redistributes their mass to the severe end — measured at 3.7× on halong (§4.9) |
| Response-model seed | **Per gauge and per (gauge, storm)**, hashed from identifiers and a configured run seed | A single global seed would shift every gauge's character whenever an unrelated gauge joined or left the portfolio (§6.1) |
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

### 4.9 Catalogue coverage — counting the events that never flood

The generated catalogue holds no minimal or baseline events at all, and those
two categories carry **73%** of the population mass.

The first implementation normalised the sampling weights to one over whatever
categories were present. That silently redistributed the missing mass
proportionally across the severe end: a configured **8%** severe-or-worse share
became an effective **29.6%**, overstating the hazard by **3.7×**.

Those events are not missing data. They are real events that never reach a flood
trigger, so they belong in the denominator at a conditional of zero. The
catalogue therefore carries `coverage` — the population mass it represents — and

```
P(flood | event)  =  (weighted share within the catalogue) × coverage
```

with `effective_lambda(λ) = λ × coverage` giving the sampler the matching rate.
Scaling the conditional and scaling the rate are equivalent, and a test asserts
the two paths agree, so the sampler and the closed form cannot disagree by
construction.

The per-category conditionals on halong make the original error obvious in
hindsight: moderate and severe events **never** breach the severe level (0.0000);
only extreme (0.22) and catastrophic (0.96) do. Redistributing mild-event mass
across categories with those conditionals could only inflate the answer.

### 4.10 The closed form, and why it is a test rather than the answer

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

### 4.11 Two field-naming traps

Both produced confident, plausible, wrong answers before being caught. They are
recorded because the next person to touch this chain will meet them.

| Field | Says | Actually holds |
|-------|------|----------------|
| `flood_events[].storm_id` | a storm | a **sequence** identifier — the generator collapses storms onto sequences and the loop variable kept the old name. All 271 of 271 on halong |
| `_load_gauge_hazard_curves` → `num_storms` | a storm count | the **sequence** count. The docstring says so; the caller's variable name does not |

Consequences during development, both corrected:

- An early diagnosis claimed the property leg mixed units (events ÷ storms). It
  did not; the denominator was already the sequence count. The error was in the
  analysis, not the code.
- The event frame's first implementation silently dropped identifiers it did not
  recognise. Handed the property leg's sequence identifiers it returned a
  confident **0.0 conditional from 110 genuine flood events** — a zero spread,
  no error, no warning.

`EventFrame.resolve` therefore accepts either form and **counts what matches
neither**, and `conditional_probability` raises rather than returning a number
when anything is unresolved. Records that do not correspond to the catalogue
cannot produce a meaningful conditional, and a plausible small number is more
dangerous than a failure.

### 4.12 Wiring

| # | File | Change | State |
|---|------|--------|-------|
| 1 | `src/models/hazard/io/_load.py` | Sequence tagging; `event_id` / `count_events`; `num_events` in metadata and summary | **Built** |
| 2 | `src/models/hazard/builder.py` | Builds the event catalogue, computes weighted per-event conditionals at alert/warning/severe, annualises. GEV retained for severity curve points and return levels | **Built** |
| 3 | `src/port/src/property/hc/pricing/_process.py` | Property spread, gauge basis leg and return period annualised. The gauge side reads the annualised probability from `gaugehc` rather than re-deriving a ratio, so both sides of the basis share a footing | **Built** |
| 4 | `src/port/src/property/hc/pricing/_wind.py` | Wind, union and intersection legs annualised on the same frame, in sequence space | **Built** |
| 5 | `src/models/hazard/response_model.py` | Seeded per gauge and per (gauge, storm) | **Built** |

### 4.13 Extension points (architected now, built later)

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

Everything here is measured on the halong catchment (3 gauges, 1 residential
property, 10 commercial assets, 1000 storm sequences) unless stated otherwise.
It supersedes every estimate in earlier versions.

### 6.1 Reproducibility — a pre-existing defect, now fixed

`GaugeResponseModel` drew from three **unseeded** `np.random.uniform` calls. Two
of them redrew each gauge's *fundamental character* — its normal level and
response coefficient — on every build. Twelve rebuilds of one gauge, identical
inputs:

| Metric | Mean | Min | Max | Spread |
|--------|------|-----|-----|--------|
| Frequency-derived annual probability | 0.1821 | 0.1332 | 0.2201 | **48% of mean** |
| Legacy annual probability | 0.1168 | 0.0923 | 0.1341 | **36% of mean** |

This predates MKM-EF-001 entirely. **Every hazard curve the platform has ever
produced was irreproducible at roughly ±40%**, and the BCBS 239 reproducibility
claim did not hold for this chain. It is not a frequency-model problem; it was
found because calibrating the frequency model required repeatable measurements.

The fix seeds per gauge and per (gauge, storm), hashing the identifiers with a
configured run seed rather than drawing from one global stream. A global seed
would have been worse than useless: every gauge's character would shift whenever
an unrelated gauge joined or left the portfolio. Verified — identical across
rebuilds, unchanged when another gauge is removed, and hazard curves now hash
byte-identical between consecutive builds.

One consolation for work done before the fix: the *ratio* between old and new
metrics was stable, because both legs shared the same draw and the noise largely
cancelled. Comparisons were sound even while neither level was.

**This is a governance event in its own right.** Re-running any existing
catchment now gives a different — and from now on stable — answer, independent
of anything MKM-EF-001 does.

### 6.2 Cost and accuracy of the year simulation

Apple M2, 8 cores, 8 GB. A full portfolio is 2,200 subjects scored against one
shared set of draws.

| Simulated years | Full portfolio | Sampling error |
|-----------------|----------------|----------------|
| 1,000 | 0.07 s | ~5% |
| **10,000** *(configured)* | **0.40 s** | **~1.6%** |
| 100,000 | 4.1 s | ~0.5% |
| 1,000,000 | 43 s | ~0.16% |

Cost is linear in the year count and error falls as its square root. Run-to-run
stability does not depend on this number — the seed is pinned — so what the year
count buys is closeness to the true expectation, not repeatability.

### 6.3 Repricing on halong

Catalogue: 2112 storms → **1000 events** (2.11 storms/event). Event category mix
421 moderate, 336 severe, 197 extreme, 46 catastrophic — **no minimal or
baseline at all**, confirming the importance-weighting is load-bearing rather
than theoretical. Coverage 0.27. λ = 4.5 events/year. Severe-or-worse population
share calibrated to 8% by the model owner.

**Gauge leg:**

| Gauge | P(flood\|event) | New annual | Old annual | Ratio | New RP | Old RP |
|-------|-----------------|-----------|-----------|-------|--------|--------|
| GAUGE-419b4a25 | 0.0145 | 0.0632 | 0.1120 | 0.56× | 15.3y | 8.9y |
| GAUGE-635036ec | 0.0124 | 0.0542 | 0.1272 | 0.43× | 17.9y | 7.9y |
| GAUGE-789592e7 | 0.0125 | 0.0546 | 0.1022 | 0.53× | 17.8y | 9.8y |
| SYNTH-182600fa | 0.0100 | 0.0440 | 0.1266 | 0.35× | 22.2y | 7.9y |

**Property leg:** 1100 bps → 587 bps (0.53×), return period 9.1y → 16.5y.

**Commercial leg:** all ten assets priced, 6.8 to 518.1 bps, inclusion-exclusion
and union/intersection ordering verified across the peril legs.

The reprice is therefore **downward, 0.35×–0.56×**, not the upward move every
earlier draft of this document predicted. The direction reversed twice during
development — first when population weighting was added, again when the coverage
treatment was corrected — which is the strongest argument in this document for
not quoting a repricing figure until the mechanism underneath it is settled.

Severe-flood return periods of 15–22 years against the legacy model's 8–10 may
still be too benign for a typhoon-exposed catchment. The lever is
`EVENT_POPULATION_WEIGHTS`; it now behaves linearly and reproducibly, and a
rebuild is about ten seconds.

### 6.4 Extraction against the existing calculation

On a thirty-year synthetic gauge record, at the severe trigger:

| Measure | Rate |
|---------|------|
| Exceedance **days** per year — what `statistics/timeseries.py` reports today | 1.234 |
| Declustered **events** per year | 0.967 |

A **28% overstatement**, being the mean flood duration in days. This is what
§4.5's fix-and-promote removes; it is still outstanding (Stage 1c).

### 6.5 What has NOT been validated

- **The wind leg has never run on real data.** Halong's wind damage index holds
  asset identifiers that are not in the current commercial portfolio — the stale
  `commercial_peril_ts` and `property_peril_ts` steps the port run reports. Every
  asset prices wind at zero, on the baseline as well as after the change. The
  annualisation is covered by unit tests only, which is weaker evidence than a
  real run, and a port run with the peril steps regenerated is the outstanding
  check.
- **λ itself remains a seed**, and on synthetic catchments cannot be calibrated
  from the gauge record at all (§5).

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
| 1a | Event-definition alignment; event catalogue; POT extraction with declustering; per-catchment λ; `num_events` | **Done** | Denominator only |
| 1b | Monte Carlo year sampler; shared draws; closed-form reconciliation gate | **Done** *(was Stage 6)* | Not consumed directly |
| — | *Unplanned, forced by calibration:* seed the response model; catalogue coverage | **Done** | **Yes** (§6.1, §4.9) |
| 3 | Frequency layer wired into `builder.py`; legacy metric retained alongside | **Done** | **Yes** |
| 4 | Property, commercial, gauge-basis and wind legs; return periods | **Done** | **Yes** |
| 1c | Day-count fix-and-promote (§6.4); λ and provenance persisted through the `database` seam | To do | No |
| 2 | Poisson / NegBin families; dispersion selection; override logging; round-trip validation | To do | No |
| 5 | Governance: inventory entry, LaTeX documentation, registry wiring, validation report, monitoring job | To do | No |
| 6 | *Separate approval:* loss-weighted YLT, ELT export, wind λ calibration, seasonal rates | To do | — |

The clamp review promised for Stage 4 (`builder.py` exceedance floor and
`MAX_RETURN_PERIOD`) is **still outstanding**; return periods now run to 15–22
years where the cap is 100, so the clamps do not currently bind, but they remain
unreviewed.

**Stage acceptance.**

- **S1a/S1b** — *met.* Event-granular loader covered; catalogue and sampler under test;
  simulation reconciles with its closed form.
- **S3/S4** — *met, with one gap.* Gauge, property, commercial and wind legs price off
  the frequency layer; hazard curves reproducible across rebuilds; port suite 2812
  passed against a 2807 baseline with zero regressions; the legacy metric is retained
  alongside for parallel run. **The wind leg has not been exercised on real data** —
  see §6.5.
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
| L1 | **Magnitude of the reprice** | Measured at **0.35×–0.56×** on halong at the calibrated 8% share (§6.3) — *downward*. The direction reversed twice in development, so the figure is only as settled as the mechanism beneath it. | **Quantified, not signed off.** A full-book parallel run on regenerated data is the gating artefact. |
| L2 | **Compensating clamps** | `builder.py` clamps the exceedance probability up to 0.01; `MAX_RETURN_PERIOD: 100` caps return periods. Both exist because return periods were fake. | **Open.** Return periods now run 15–22 years so neither clamp binds today, but they remain unreviewed and would bind at a lower severe-or-worse share. |
| L3 | **`num_storms` is persisted and rendered** | Read by the UI, the blotter and end-of-day. | **Resolved.** Kept, with `num_events` added beside it. No consumer changed. |
| L4 | **End-of-day history spans the cut** | Stored `annual_hazard_rate_*` change semantics *and* magnitude; series become non-comparable across the switchover. | **Open, and wider than first thought.** The response-model seeding (§6.1) moves every curve independently of MKM-EF-001, so the discontinuity is not attributable to the frequency model alone. Mark the cut; do not backfill. |
| L5 | **Per-storm flood-event collapse** | | **Resolved — and the premise was wrong.** The property leg was already event-granular and already divided by the sequence count. The only thing missing was λ (§4.11). |
| L6 | **Wind leg diverges** | Wind divided by the scenario count while flood was annualised, making BOW/BAW union and intersection incoherent. | **Resolved in code, unvalidated on data.** Both legs annualise on the same frame in sequence space. Halong cannot exercise it — see L9. |
| L7 | **Correlation is load-bearing** | Portfolio risk depends on subjects sharing one set of event draws; a caller running the single-subject wrapper per subject would silently decorrelate the book (0.78 versus −0.004). | **Open.** Guard at the portfolio entry point; review point for any new caller. |
| L8 | **Population weights are load-bearing and unvalidated** | The conditional scales directly with `EVENT_POPULATION_WEIGHTS`. Set to an 8% severe-or-worse share on the owner's judgement. | **Open.** Nothing currently contradicts a wrong value; the per-gauge POT arm is the intended check and depends on Stage 1c. |
| L9 | **Peril data is stale relative to the asset portfolio** | Halong's wind damage index holds asset identifiers absent from the current commercial portfolio, so every asset prices wind at zero — before and after the change. The port run reports `commercial_peril_ts` and `property_peril_ts` as stale. | **Open.** A port run with the peril steps regenerated is required before the wind leg can be said to work. |
| L10 | **Silent-zero class of failure** | Records that do not correspond to the storm catalogue produced a confident 0.0 conditional from 110 genuine flood events, with no error. | **Resolved for this path.** `conditional_probability` now raises on unresolved identifiers. The same class of failure may exist elsewhere in the chain and has not been swept for. |

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
