# PhysicalRisk Enhancement: Event Frequency Layer

**Document type:** Definition Document & Project Plan
**Component:** Event Frequency Model — `MKM-EF-001` (new)
**Version:** 2.12 — supersedes `frequency_layer_definition_and_plan.md` (v1.0, 2026-07-22)
**Status:** Stages 1–5 complete — built, wired to pricing, validated end-to-end, and registered for governance. Stage 6 (Track B): 6a–6g plus the **non-stationary term structure** (6h: the arrival-rate process now compounds through `compute_term_structure`, defaulting to stationary via an empty per-catchment growth registry) are built and reconciled. Open: a genuine climate-trend seed (needs a real signal + MRC) and the decoupled wind-λ reprice
**Date:** 2026-07-27
**Owner:** CSO, MKM Research Labs

---

## 0. What changed from v1

### 0.1 What v2.12 changes

Stage 6h: the non-stationary rate now flows through the production multi-year
term structure — behaviour-preserving until a trend is seeded.

| # | Change | Driver |
|---|--------|--------|
| C32 | **Non-stationary term structure.** `compute_term_structure` now accepts a per-year hazard sequence as well as a single rate, compounding a running sum instead of `rate·t`; the builder feeds it `annual_hazard_by_year(rate_process, p, tenor)`, and the rate process comes from `rate_process_for(λ, catchment_annual_growth(catchment))`. A `catchment_annual_growth` registry (empty, default 0.0) sits in config as a leaf — numbers only — with the `RateProcess` built in the model layer. Empty registry → zero growth → `ConstantRate` → flat hazards → the term structure is byte-identical to before | Wires 6g's rate process into the one place multi-year pricing is computed, so a climate trend can be turned on per catchment. Because a non-zero growth moves a priced multi-year quantity, the registry ships empty and the seeding is a model-risk decision resting on a real climate signal — the seam is behaviour-preserving, the reprice is deferred |

### 0.2 What v2.11 changed

Stage 6g: the non-stationary rate-process seam — and the finding that a drifting
rate belongs on the tenor, not inside the Monte Carlo replications.

| # | Change | Driver |
|---|--------|--------|
| C31 | **`RateProcess` for λ(t)** (`rate_process.py`): `ConstantRate` (the pre-6g model), `TrendRate` (`λ_t = λ₀·(1+g)^t`), and `term_exceedance_probability`, the non-homogeneous multi-year survival `1 - exp(-p·Σλ_y)`. This is §4.14's time-varying-rate extension point. Behaviour-preserving: a constant rate compounds to exactly the stationary `1 - exp(-λ·T·p)` and at one year is the ordinary annualisation seam; a trend with zero growth reduces to the constant. **Finding:** the drift is indexed by *contract year*, not Monte Carlo sample — a rate compounded across the ten-thousand within-year replications overflows to nonsense (caught in a smoke test), because those replications are the *same* calendar year, so non-stationarity is a term-structure concern, not a sampler one | Addresses the stationarity limitation (climate drift) recorded since v2.0. The seam is built and reconciled but **not yet wired into the production multi-year term structure** (`gev.compute_term_structure`) or given per-catchment trend seeds — doing so moves a priced multi-year quantity, so it is governance-gated, deferred to the wiring stage exactly as 6a's machinery preceded 6c's wiring |

### 0.3 What v2.10 changed

Stage 6f: the per-peril wind-λ seam — and the finding that, under the current
coupling, wind has no independent rate to calibrate.

| # | Change | Driver |
|---|--------|--------|
| C30 | **Per-peril wind arrival-rate seam** (`catchment_wind_lambda`, `CATCHMENT_WIND_LAMBDA_PER_YEAR`) — the λ registry §4.14 architected. Wired into the **additive** wind-loss block (its own rate, its own draws). **Finding:** the wind leg works in sequence space and *drops any typhoon with no paired storm sequence*, so under the 1:1 coupling wind is not an independent arrival process — it shares the storm event rate. The registry is therefore empty and the accessor falls back to `catchment_lambda`, leaving all numbers unchanged; an entry overrides only the additive wind-loss view, never the priced spread | Completes the architected per-peril registry while being honest that a genuine wind-λ *reprice* is not a config tweak: it needs the unpaired, off-sequence typhoon events counted (a redesign of the coupled union/intersection legs) and, because it moves a priced spread, model-risk sign-off and real data — the same λ circularity as flood applies on synthetic catchments (§5). The seam is behaviour-preserving; the calibration is deferred with its blockers recorded |

### 0.4 What v2.9 changed

Stage 6e: the additive loss view reaches the wind peril.

| # | Change | Driver |
|---|--------|--------|
| C29 | **Wind-leg loss wiring.** Each asset now carries a second additive loss block, `loss_metrics_wind`, beside the flood one — same AAL/AEP/OEP/ELT machinery, same currency basis and shared draws, over the wind-triggered events. The authoritative per-event wind `damage_ratio` (BRI + persistence, already written into the typhoon damage files) is surfaced through `load_wind_damage_index` and reused, exactly as the flood leg reuses its depth-damage ratio; `_wind_union` maps each wind-triggered event back into sequence space and emits `wind_loss_records`, which `property_loss_block` — peril-agnostic, reading only `storm_id` + `damage_ratio` — turns into the block. Present only when the typhoon stage ran and the frequency config is supplied; the spread is untouched | Completes the additive loss view across both perils and all three subject types. Reusing the one loss builder for flood and wind keeps a single reconciled path rather than a parallel wind implementation |

### 0.5 What v2.8 changed

Stage 6d began: the property and commercial loss blocks are now a currency
amount, not a unit-exposure severity.

| # | Change | Driver |
|---|--------|--------|
| C28 | **Monetary uplift on the property/commercial legs.** Each asset's loss is now `damage_ratio × PropertyValue` — the same `value × damage_ratio` the routes and reports already use — so the loss block's AAL, AEP/OEP and ELT are in currency, with `basis: "currency"` and `exposure_value` recorded. Values come from a single lookup over the portfolio (`LoaderMixin._load_asset_values`), reading `<root_section_key>.Valuation.PropertyValue` — `PropertyHeader` for residential, `CommercialAsset` for commercial, both from `ASSET_CONFIG`, so one reader serves both. A missing value is zero-in-currency, not a rebasing to severity, so a portfolio data gap shows as `exposure_value = 0` rather than hiding. The gauge leg stays at unit exposure — a gauge has no value. Still additive: the spread is untouched | Turns the severity index from 6c into the money figure the desk actually reserves against, completing the loss view for the asset legs. An unreadable portfolio yields an empty lookup and prices every loss at zero rather than aborting the build |

### 0.6 What v2.7 changed

Stage 6c — the additive loss wiring itself — landed on the gauge and
property/commercial legs.

| # | Change | Driver |
|---|--------|--------|
| C27 | **Loss block wired into the gauge leg (`builder.py`) and the property/commercial legs (`_process.py`).** Each gauge hazard curve and each asset pricing record now carries an additive `loss_metrics` block — average annual loss, AEP and OEP curves and the attributed event-loss-table metadata — beside the unchanged spread. The gauge loss quantum is the depth-damage ratio applied to depth above the severe trigger; the asset legs regroup each asset's per-event `damage_ratio` onto the hours-clause events (worst-within-event). Both are at **unit exposure** — the damage ratio itself, no asset value multiplied in — so a gauge with no value and an asset are on one comparable footing, and the shared `compact_loss_block` keeps the two call sites identical. Every block reconciles against its closed-form AAL | The loss layer (6a/6b) had no callers; this consumes it. Additive by the owner's decision (§ v2.6 C26): the spread is untouched, so no price moves and no port regen is needed to keep current pricing valid. Gated on the frequency config being supplied, so the fallback path and every existing unit test stay byte-identical. **The monetary uplift — multiplying by `PropertyValue` / commercial value — is 6d: it needs the asset value threaded in, a separate change** |

### 0.7 What v2.6 changed

Stage 6b — the additive loss wiring — was scoped and its reusable core built.

| # | Change | Driver |
|---|--------|--------|
| C26 | **Loss wiring decided *additive*, and the subject-loss adapter built** (`subject_losses.py`). Reconnaissance established that today's PRS spread is pure `P(flood) × 10000` with **no monetary loss in it at all**, so the owner's decision is to emit AAL/AEP/OEP/ELT as *new* outputs beside the unchanged spread — no price moves, no port regen to keep current pricing valid, no MRC pricing-policy change. The adapter turns a gauge's `peak_levels` (via a caller-supplied damage curve) or an asset's per-storm records (regrouped onto events by their maximum) into an aligned per-event loss vector, and `loss_metrics` centralises the coverage scaling — the ELT takes the raw λ, the sampler λ×coverage — so the units trap that has bitten this project cannot recur at a call site | The loss machinery (6a) was dormant with no callers; the adapter is the seam every pricing leg calls. Keeping the damage model in the caller preserves 6a's boundary and the frequency layer's peril-generic shape (§4.14). The **leg wiring itself (6c/6d) is not yet done** |

### 0.8 What v2.5 changed

Stage 6 (Track B) began with the loss extension. The occurrence sampler now has
a loss-weighted twin: give each catalogue event a loss quantum and the same
draws yield a year-loss table, its AEP and OEP curves, and a standard event loss
table for third-party comparison.

| # | Change | Driver |
|---|--------|--------|
| C22 | **Loss-weighted YLT built.** `ylt/_losses.py` scores the shared `EventDraws` with a per-event loss instead of a boolean, giving `LossSimulation` — aggregate loss per year (AEP) and largest single occurrence per year (OEP), with AAL, exceedance probabilities and return-period curves | §4.14 anticipated exactly this: "replacing that boolean with a loss quantum turns the same machinery into a full year loss table without changing the sampler." The draws are shared, so a subject's loss run and occurrence run describe the same storms and portfolio subjects stay correlated |
| C23 | **Event loss table + export.** `elt/` builds an `EventLossTable` from a catalogue, per-event losses and λ (rates = `λ_effective × weight`, summing to `λ_effective`), and exports it as an attributed, JSON-serialisable document with the standard EventID/Rate/MeanLoss/StdDev/Exposure columns | The ELT is the reinsurance interchange format; carrying model identity and provenance alongside the rows is what makes it comparable rather than unattributable |
| C24 | **Loss reconciliation gate.** The ELT's `AAL = Σ rate × loss = λ_effective × Σ weight × loss` is the simulation's *exact expectation* (compound-Poisson mean); `reconcile_losses` measures the gap in sampling standard errors of that mean, mirroring §4.10's occurrence gate | Same principle as the occurrence self-test: the closed form is not a second opinion, it is what the simulation must converge to, so a gap beyond sampling error means one of the two is wrong. Measured deviation 0.30σ at the default 10,000 years |
| C25 | **The loss quantum stays the caller's.** The frequency layer supplies only the machinery; per-event losses come in as an argument, exactly as flood flags do. Wiring the platform's damage model to produce them per subject — and the pricing consequences — is the next Track B sub-step, not this one | Keeps the frequency layer generic and the damage model's integration a separate, separately-reviewable change, as Stage 1's machinery preceded Stage 3's wiring |

### 0.9 What v2.4 changed

The two remaining critical-path stages landed. The model is now built, wired,
validated and governed end-to-end; nothing on the critical path is outstanding.

| # | Change | Driver |
|---|--------|--------|
| C20 | **Stage 2 complete**: Poisson and Negative-Binomial families with a *calibrated* selector — a chi-square dispersion test gates the choice, not a bare `D > 1` rule, and an AIC margin guards the extra NegBin parameter | With fifty annual counts a genuine Poisson process throws dispersion indices up to ≈1.4 by chance, so the naive rule over-selects NegBin badly (§5.2). Under-dispersion — halong's actual regime — is flagged, never fitted: no family on the Poisson–NegBin axis represents it, so Poisson is selected as the nearest fittable family and the note says so. The selected family and its justification are persisted per gauge (SR 11-7) |
| C21 | **Stage 5 complete**, in the **ModelRisk** repo. MKM-EF-001 is registered through the governance command API, placed in the chain GH-001 → EF-001 → PR-001, with 4 assumptions, 4 limitations, 3 weaknesses and 9 SR 26-2 validation questions | Governance migrated to a separate event-sourced Postgres platform since v2.0 was written — there is no `model_inventory.json` and no LaTeX to wire (§10). This supersedes the JSON/registry/`.tex` plan §10 originally described. Version bumped 0.1.0 → **1.0.0** as a genuine release |

### 0.10 What v2.3 changed

| # | Change | Driver |
|---|--------|--------|
| C16 | **The per-gauge validation arm is circular.** It cannot check λ, because the threshold search targets λ | `load_frequency_config` sets the peaks-over-threshold target *from* the catchment rate, so the search finds whatever threshold delivers it and recovers the seed by construction. Halong returned 4.48–4.58 against a seed of 4.5 (§5.2). **Nothing now validates λ** |
| C17 | **Stage 1c complete**: exceedance *events* alongside exceedance *days* in the statistics module; fitted rates and provenance persisted through the `database` seam | The day count was never a rate. Persistence closes the BCBS 239 traceability requirement (§4.14) |
| C18 | **The wind threshold is traced and now per-asset.** 55.56 m/s was a deliberate uniform constant (200 km/h), not a unit bug; `DesignWindSpeedKmh` drives the threshold instead, and design speeds were raised 40 km/h | Wind vulnerability was undifferentiated across a portfolio. L12 partially closes; the calibration question remains (§6.8) |
| C19 | **L13 resolved**: the peril stages record the BRI spine they read, and a guard warns when any stage under-declares | The warning fired after every successful run and had already misled one root-cause investigation. The gap was real: a change to the BRI spine never invalidated the consuming step |

### 0.11 What v2.2 changed

Wiring the layer into pricing and calibrating it on real halong data
exposed three defects — two of them pre-existing and more serious than the
problem this model was written to fix.

| # | Change | Driver |
|---|--------|--------|
| C11 | **The gauge response model was unseeded.** Fixed. Hazard curves were irreproducible at roughly ±40%; they are now byte-identical across rebuilds | Pre-existing, predating MKM-EF-001. Three `np.random.uniform` calls, two of which redrew each gauge's *character* on every build. The BCBS 239 reproducibility claim did not hold for this chain (§6.1) |
| C12 | **Missing mild events were reweighted onto the severe end.** Fixed by scaling the conditional by catalogue *coverage* rather than renormalising the weights | The catalogue holds no minimal or baseline events, and those carry 73% of the population mass. A configured 8% severe-or-worse share became an effective 29.6%, a 3.7× overstatement (§4.9) |
| C13 | **Stages 3 and 4 are built**: gauge, property, commercial and wind legs all price off the frequency layer | The reprice is **downward**, 0.35×–0.56× at the calibrated weights (§6.3), not the upward move earlier drafts predicted |
| C15 | **The wind leg is validated on real data**; L6 and L9 close | A `--typhoon` run put real wind through all ten commercial assets with the peril coherence checks passing (§6.6). It also surfaced L12: the wind trigger is one global constant, not asset-differentiated |
| C14 | **Two field-naming traps documented**, both of which produced confident wrong answers before being caught | `flood_events[].storm_id` holds *sequence* identifiers; `_load_gauge_hazard_curves` returns the *sequence* count while its caller names it `num_storms` (§4.11) |

### 0.12 What v2.1 changed

v2.0 was written before any code existed. Building it moved four things, one of
which was an outright error in v2.0's design.

| # | Change | Driver |
|---|--------|--------|
| C7 | **λ is a property of the catchment, not of a gauge.** v2.0 had per-gauge POT calibration feeding λ into pricing. That is wrong: a per-gauge exceedance rate is *already* λ × P(exceed \| event), so using it as λ squares the conditional and double-counts. λ is now a seeded per-catchment rate, and per-gauge POT became the **validation arm** | A storm arrives over the catchment and reaches every gauge in it. What differs per gauge is the conditional response, not the arrival rate |
| C8 | **The Monte Carlo year simulation is the engine, and has moved forward out of Track B.** v2.0 deferred the sampler and priced off the closed form; the order is now reversed — the simulation prices, the closed form is its self-test | The closed form is the simulation's *exact expectation*, not an approximation of it (§4.10), so it is worth more as a check than as an answer. The simulation additionally yields the annual distribution, which the closed form cannot |
| C9 | **10,000 simulated years, and the reconciliation gate is expressed in sampling standard errors rather than as a fixed percentage** | Measured on the target hardware (§6.1). A fixed 2% band false-alarmed on 17% of runs at ten thousand years while never binding at a million |
| C10 | **Landmine L3 resolved:** `num_storms` is kept and `num_events` added beside it | The storm/event distinction becomes visible in the data rather than hidden in a redefinition of a field existing consumers already read |

### 0.13 What v2.0 changed from v1

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

Every item is built and under test.

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
    _poisson.py          ✓ MLE Poisson fit; AIC; seeded annual-count sampler
    _negbin.py           ✓ MLE Negative Binomial; collapses to Poisson at α→0
    _select.py           ✓ chi-square dispersion test + AIC tiebreak; logs overrides
  calibrate.py            ✓ orchestration: pure function of (series, config) → FittedRate
  persist.py              ✓ calibrate a catchment and save via the database seam (R6)
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

### 4.13 Persistence of fitted rates

`frequency_rates` is registered as a DOCUMENT artefact, so both backends carry
it with **no migration** — the PostgreSQL repository derives its document set
from the registry rather than a hand-maintained list.

`models/frequency/persist.py` calibrates every gauge in a catchment and writes
through `database.save_frequency_rates`. It names no file path (R6).

Two deliberate strictnesses:

- **The provenance class is a required argument with no default.** A synthetic
  catchment's record is generated from an assumed frequency (§5.1), so
  defaulting to `observed` would launder an assumption into evidence.
- **A partial provenance record raises rather than defaulting on read.**
  Provenance that cannot be read back in full looks like evidence and is not.

The round trip is exact and asserted: `rate_from_dict(rate_to_dict(r)) == r`.

### 4.14 Extension points (architected now, built later)

- λ as a process rather than a constant: the interface takes an optional covariate/time
  argument so a doubly stochastic or climate-conditioned rate can be added without an
  interface change.
- Per-peril λ registry, so wind/fire/seismic attach without restructuring.
- The simulation scores a boolean flood outcome per event. Replacing that boolean with
  a loss quantum turns the same machinery into a full year loss table without changing
  the sampler. **Built in Stage 6a** (`ylt/_losses.py`, `elt/`): `LossSimulation`
  (AEP/OEP/AAL) and `EventLossTable`, reconciled against the compound-Poisson closed
  form. The per-event loss is still passed in by the caller; wiring the damage model to
  produce it per subject is Stage 6b.

---

## 5. The λ provenance problem

### 5.1 The record is generated from the frequency it would calibrate

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

### 5.2 The validation arm cannot validate λ

v2.1 demoted per-gauge extraction from *producing* λ to *validating* it (C7).
Running that validation on halong in Stage 1c showed it cannot do the job
either, for a reason independent of §5.1.

`load_frequency_config` sets the peaks-over-threshold search target **from the
catchment arrival rate** — deliberately, so that the qualifying-event threshold
and λ describe the same event population rather than drifting apart (§4.2). But
the search then picks whatever threshold delivers that rate, so the recovered
rate equals the seed by construction:

| Gauge | Recovered λ | Seed |
|-------|-------------|------|
| GAUGE-419b4a25 | 4.523 | 4.5 |
| GAUGE-635036ec | 4.483 | 4.5 |
| GAUGE-789592e7 | 4.583 | 4.5 |
| SYNTH-74cf6170 | 4.503 | 4.5 |

A quantity that reproduces its own input is not a measurement of anything. The
arm validates the **extraction code** — that declustering and the threshold
search behave — not the rate. Combined with §5.1, **nothing in the platform
currently constrains λ**, and landmine L8 is correspondingly wider than earlier
versions of this document implied.

Two things the arm *can* still say, and both are worth having:

- **Dispersion.** Halong's four gauges returned a dispersion index of
  **0.46–0.97**, i.e. annual counts *less* variable than Poisson. That is a
  real property of the arrival process and it bears directly on Stage 2:
  under-dispersion is fitted badly by Poisson and worse by Negative Binomial,
  which only models the over-dispersed side.
- **The decomposition identity.** λ × P(exceed | event) reproducing a gauge's
  directly measured exceedance rate remains a genuine consistency check on the
  composition, independent of whether λ itself is right.

Breaking the circularity needs the threshold to come from somewhere other than
the rate being tested — a physical anchor such as bankfull discharge, or a
published national flood-frequency estimate. Both require real gauge data and
are Stage 2 work at the earliest.

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

### 6.5 The clean run

A full port with the frequency layer wired throughout (halong, 3 gauges, 1
property, 10 commercial assets, 1000 sequences, 2026-07-23):

| Check | Result |
|-------|--------|
| Hazard curves reproducible across rebuilds | **Identical** — the seeding fix holds outside the test harness |
| Gauge severe return period | **15.8–17.8 years** at λ = 4.5 and the 8% share |
| Property PRS | **587.2 bps**, return period 16.5 years |
| Commercial PRS | 10 assets, 75–606 bps |
| Wind leg | Zero everywhere — see below |

The run also caught a defect that no test had: **flood transmission rates of
183%, 196% and 200%**, against a quantity bounded by 1 by construction. The
basis leg derived its gauge count as annual probability × scenario count, which
was sound while that probability was a per-event conditional and became a units
error the moment Stage 3 annualised it. The hazard builder now writes a raw
catalogue count for the basis leg to use, and the rates return to 0.43–0.51. The
headline spread is unaffected, the basis leg feeding the decomposition display
rather than the price.

Two things worth drawing out. The error was found by a **summary line in a run
log**, not by 2800 passing tests — the invariant that would have caught it
(transmission ≤ 1) is not asserted anywhere. And it is the same class of units
error this document records twice already (§4.11), committed this time by the
author of those very warnings.

### 6.6 The wind leg, exercised at last

A second run with `--typhoon` (2026-07-23, 15:01–15:36) generated 1000 coupled
typhoons and put real wind through the peril legs for the first time.

| Check | Result |
|-------|--------|
| Commercial assets with a non-zero wind leg | **10 of 10** |
| Inclusion-exclusion on counts; union ≥ both legs; intersection ≤ either | **PASS** |
| Hazard curves reproducible across rebuilds | **Identical** |
| Flood transmission rate | **55.7%** property, **29.7%** commercial |

The peril fan is live throughout — property `win` 295.6, `faw` 151.8, `fow`
760.8 bps; commercial `win` 31.9, `faw` 24.2, `fow` 372.0 bps. **L6 and L9 are
both closed**, and the transmission rates confirm the §6.5 units fix in a fresh
run rather than in a patched rebuild.

Two observations from the run that are *not* frequency-layer problems but which
bear on any wind number quoted from it.

**The wind trigger is not asset-differentiated.** All ten commercial assets
trigger on the same five events. The wind field *is* sampled per location —
`peak_sustained_ms` differs per asset — but only in the fourth decimal, the
portfolio being tightly clustered. The deciding quantity, `v_50_eff_ms`, is
**55.56 for every asset**: a Hotel, an Office, three MultiFamily and two Retail
all share one vulnerability threshold. And 55.56 m/s is exactly 200 km/h
(200 ÷ 3.6 = 55.5556), a round design figure in one unit surfacing as a
threshold in another. Wind exposure is therefore currently driven by a single
global constant rather than by construction type. This sits in MKM-WD-001's
territory, not this model's — the annualisation is correct given whatever
trigger it is handed — but it means the wind spreads above describe one
threshold, not asset-level resilience.

**Run cost.** The typhoon stage took 15 minutes for 1000 events at 100
particles, and the ensemble write a further ~20 on a machine already deep into
swap; the 69 MB `ensemble.json` and 2100 damage files are the bulk of it. A run
that appears hung after the progress bar reaches 100% is most likely still
serialising.

### 6.7 The wind threshold, traced

L12 recorded that every asset shared one wind trigger. Tracing it settled what
it was — and it was neither of the two hypotheses on record.

**Not a unit bug.** `bri_codes.WIND_MINOR_KPH = 200.0`, converted to 55.56 m/s.
The arithmetic is right; this is not another instance of the m/s-versus-km/h
problem logged against the wind work.

**Not a missing default.** The configured fallback is 100 km/h (27.8 m/s), so
the 55.56 was actively supplied, not defaulted.

It was a **deliberate uniform prototype constant** — the comment beside it says
so — published identically into every asset. Meanwhile `DesignWindSpeedKmh`, the
one genuinely per-asset quantity, sat unused by the damage model.

Two changes followed:

| Change | Effect |
|--------|--------|
| `DesignWindSpeedKmh / 3.6` now resolves the threshold, falling back to the BRI level | Thresholds became per-asset; commercial wind triggers went 50 → 653 per 1000 events |
| Base design speeds raised 40 km/h to 120–200 (the previous 80–160 was a Thames "urban-low-wind" set applied to a typhoon coast) | Pulled the triggers back to 276 — the two changes oppose each other |

On the regenerated portfolio: design speeds **122–159 km/h**, thresholds
**33.9–44.2 m/s**, wind triggers **22–53 per asset**, wind-only spread
**162.0 bps** against 0.0 before. `fow` rose to 429.8 bps against a flood-only
313.1, so wind contributes roughly 37% of the combined leg where it previously
contributed nothing.

The sampling points, weights and jitter moved to `config.port`; the BRI
thresholds to `config.damage`. Both were literals outside the config package
(R1), and lowering a value in place would have perpetuated that.

### 6.8 Exceedance days against exceedance events

Stage 1c's fix, measured on halong's fifty-year gauge records:

| Level | Days/yr | Events/yr | Overstatement |
|-------|---------|-----------|---------------|
| Alert | 0.38 | 0.26 | 1.46× |
| Warning | 0.06 | 0.06 | 1.00× |
| Severe | 0.06 | 0.06 | 1.00× |

Smaller than the 28% recorded in §6.4 from an earlier synthetic record, and for
an informative reason: **this generator injects mostly single-day floods**, so
there is little to decluster. The correction is in the calculation, not the
data — on a real record with multi-day floods it matters considerably more, and
the platform now reports both numbers with the ratio between them
(`mean_event_duration_days`) so the difference is visible rather than implied.

### 6.9 What has NOT been validated

- **λ is unconstrained** (§5). Neither the synthetic gauge record nor the
  per-gauge extraction arm can test it. This is the single largest open item.
- **The wind threshold level.** It is now per-asset (§6.7), but whether a
  building's design wind speed is the right *damage-onset* level, and whether
  the 120–200 km/h band suits a typhoon coast, are modelling questions for
  MKM-WD-001 that no measurement here settles.
- **No full-book parallel run.** Everything measured here is a single
  small catchment: 3 gauges, 1 property, 10 commercial assets.
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

The staging changed from v2.0. The year sampler was v2.0's Stage 6 and became the
engine rather than a deferred extension (C8). Every stage on the critical path
(1a–5) is now built, tested and shipped; only the Track B extensions (Stage 6)
remain, under separate approval.

| Stage | Content | State | Reprices? |
|-------|---------|-------|-----------|
| 1a | Event-definition alignment; event catalogue; POT extraction with declustering; per-catchment λ; `num_events` | **Done** | Denominator only |
| 1b | Monte Carlo year sampler; shared draws; closed-form reconciliation gate | **Done** *(was Stage 6)* | Not consumed directly |
| — | *Unplanned, forced by calibration:* seed the response model; catalogue coverage | **Done** | **Yes** (§6.1, §4.9) |
| 3 | Frequency layer wired into `builder.py`; legacy metric retained alongside | **Done** | **Yes** |
| 4 | Property, commercial, gauge-basis and wind legs; return periods | **Done** | **Yes** |
| 1c | Day-count fix-and-promote (§6.8); λ and provenance persisted through the `database` seam | **Done** | No |
| 2 | Poisson / NegBin families; calibrated dispersion selection; override logging; per-gauge family persisted; round-trip validation. **Outcome (§5.2):** halong's gauges are *under*-dispersed (0.46–0.97), which no count family on the Poisson–NegBin axis can model — so it is flagged and Poisson selected as the nearest fittable family, the "honest neither-fits" outcome rather than a third family | **Done** | No |
| 5 | Governance: registered in the **ModelRisk** event-sourced platform (not JSON/LaTeX — §10); chain edges; assumptions/limitations/weaknesses; SR 26-2 questions | **Done** | No |
| 6a | *Separate approval:* **loss-weighted YLT + ELT export** — `LossSimulation` (AEP/OEP/AAL), `EventLossTable` (rates = λ_eff × weight), attributed JSON export, and a compound-Poisson `reconcile_losses` gate (0.30σ at 10k years). Loss quantum stays the caller's | **Done** *(machinery; not yet fed by the damage model)* | Not consumed directly yet |
| 6b | *Separate approval, **additive** — decided 2026-07-26:* the loss layer produces AAL/AEP/OEP/ELT as **new** outputs alongside the existing probability spread; the spread is **not** changed. **Adapter built** (`subject_losses.py`): `peak_level_losses` (gauge), `regrouped_event_losses` (asset legs, max-within-event), `shared_draws` + `loss_metrics` — the latter centralises the coverage scaling (ELT takes raw λ; sampler takes λ×coverage) so no call site can get it out of step. Damage model stays with the caller | **Adapter done** | Not consumed yet |
| 6c | **Loss block wired, additively, into the gauge leg** (`builder.py` → `GaugeHazardCurve.loss_metrics`) **and the property/commercial legs** (`_process.py` → `result['loss_metrics']`, via `pricing/_loss.py`; commercial inherits the same generator). AAL + AEP/OEP + attributed ELT metadata beside the unchanged spread, at **unit exposure** (damage ratio). Gated on the frequency config so the fallback and existing tests stay byte-identical; every block reconciles. 66 tests; new modules 100% cov; hazard suite 82 passed, property sweep 81 passed | **Done** | Additive (spread unchanged) |
| 6d | **Monetary uplift done** on the property/commercial legs: loss = `damage_ratio × PropertyValue`, `basis: "currency"`, `exposure_value` recorded; one `_load_asset_values` reader serves both asset shapes via `ASSET_CONFIG.root_section_key`; missing value → zero-in-currency, not a rebasing. Gauge leg stays unit exposure (no value). 27 property/adapter tests; `_load_asset_values` happy + unreadable paths covered; property sweep 55 passed | **Done** | Additive (spread unchanged) |
| 6e | **Wind-leg loss wiring done.** `loss_metrics_wind` beside the flood block, reusing the peril-agnostic `property_loss_block`; the authoritative per-event wind `damage_ratio` is surfaced through `load_wind_damage_index` and reused, and `_wind_union` emits sequence-space `wind_loss_records`. Currency basis + shared draws; gated on typhoon-ran + config. 13 loss tests; property sweep 72 passed | **Done** | Additive (spread unchanged) |
| 6f | **Per-peril wind-λ seam done** (`catchment_wind_lambda` + `CATCHMENT_WIND_LAMBDA_PER_YEAR`, §4.14 registry), wired into the additive wind-loss block on its own rate + draws. Defaults to the storm event rate (registry empty), so behaviour-preserving. **Finding recorded**: the coupling drops unpaired typhoons, so wind has no independent rate to calibrate without a union/intersection redesign + MRC + real data. Config files 100% cov; frequency + property suites 288 passed | **Done** *(seam; calibration deferred with blockers recorded)* | Additive default; a distinct rate touches only the additive wind-loss view |
| 6g | **Non-stationary rate-process seam done** (`rate_process.py`): `RateProcess`, `ConstantRate`, `TrendRate` (`λ₀·(1+g)^t`), `term_exceedance_probability` (the `1-exp(-p·Σλ_y)` multi-year survival). Behaviour-preserving — constant ≡ stationary `1-exp(-λTp)`, one-year ≡ the annualisation seam. **Finding**: drift is a tenor concern, not a per-MC-sample one (a per-sample trend overflows over 10k replications). New module 100% cov; frequency suite 294 passed | **Done** *(seam; term-structure wiring deferred)* | Behaviour-preserving |
| 6h | **Non-stationary term structure wired**, behaviour-preserving. `compute_term_structure` compounds a per-year hazard sequence; the builder feeds it `annual_hazard_by_year(rate_process, p, tenor)` with `rate_process_for(λ, catchment_annual_growth(catchment))`. Empty growth registry → stationary → byte-identical term structure. Config leaf holds the growth numbers; the process is built in the model layer. New config/frequency/gev paths tested; 6h suites 308+ passed | **Done** *(seam; trend seeding deferred to a real signal + MRC)* | Behaviour-preserving |
| 6i | *Remaining (both gated on external inputs):* a genuine per-catchment climate-trend seed in `CATCHMENT_ANNUAL_GROWTH` (needs a real climate signal + MRC); the decoupled wind-λ reprice (unpaired-typhoon counting + union/intersection redesign, MRC + real typhoon data). Measuring the data effect of the whole loss + term-structure view needs a user-run port | To do | — |

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
- **S2** — *met.* Each family recovers its own parameters, mean and variance from data
  drawn from itself; the selector holds its NegBin false-positive rate on genuine
  Poisson counts below the configured significance while still catching real
  over-dispersion; under-dispersion selects Poisson and is flagged; the chosen family
  and its justification round-trip through the persisted rate document. NegBin covers
  the over-dispersed side only — on halong, which is under-dispersed, the honest
  neither-fits path fires (§5.2).
- **S5** — *met, in the ModelRisk repo.* MKM-EF-001 registered v1.0.0 (tier 1, Amber)
  through the governance command API, placed in the chain GH-001 → EF-001 → PR-001,
  with the §5 λ-circularity and stationarity limitations recorded, and the SR 26-2
  validation questions seeded. Idempotent seed under test. The **still-outstanding**
  governance items are the MRC decision on retiring the pre-existing direct GH-001 →
  PR-001 chain edge, and formal deprecation of the legacy metric — both MRC actions,
  not build work.

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
| L6 | **Wind leg diverges** | Wind divided by the scenario count while flood was annualised, making BOW/BAW union and intersection incoherent. | **Resolved and validated.** Both legs annualise on the same frame in sequence space; verified on real wind data with the coherence checks passing (§6.6). |
| L7 | **Correlation is load-bearing** | Portfolio risk depends on subjects sharing one set of event draws; a caller running the single-subject wrapper per subject would silently decorrelate the book (0.78 versus −0.004). | **Open.** Guard at the portfolio entry point; review point for any new caller. |
| L8 | **λ and the population weights are load-bearing and unvalidated** | The conditional scales directly with `EVENT_POPULATION_WEIGHTS` (8% severe-or-worse, on the owner's judgement) and with λ (4.5/yr, seeded). | **Open and wider than previously recorded.** The per-gauge arm was the intended check and §5.2 shows it cannot be one: it recovers λ from its own target. Stage 1c is done and did not close this. Breaking the circularity needs a threshold anchored outside the rate — bankfull discharge or a published flood-frequency estimate — and therefore real gauge data. |
| L12 | **The wind trigger was a single global constant** | Traced (§6.7): a deliberate uniform prototype constant, correctly converted — not the m/s-versus-km/h bug it resembled, and not a missing default. | **Differentiation resolved; level open.** `DesignWindSpeedKmh` now drives the threshold and design speeds were raised to 120–200 km/h, so triggers vary 22–53 per asset. Whether a design speed is the right *damage-onset* level, and whether that band suits a typhoon coast, remain MKM-WD-001 modelling questions. |
| L13 | **The stale-lineage warning was unreliable** | Both peril stages read the BRI-resilient spine (`PERIL_BASE_MODE` maps bow/baw to `"bri"`) but omitted it from their recorded inputs. The freshness check cannot verify an input with no recorded hash, so the step reported stale permanently — **and the lineage graph had a real hole**: a change to that spine never invalidated the step. | **Resolved.** Both stages record it, and `StageContext.record` now warns when any stage records fewer inputs than the topology declares, so the class of gap announces itself where it is introduced. The warning clears on the next regen. |
| L9 | **The typhoon step is opt-in, so `--all` produces no wind** | Corrected 2026-07-23 from a clean run. The peril timeseries steps *do* regenerate under `--all`; the fault is upstream. `--all` does not run typhoon, so the damage records are whatever a previous run left behind — on halong, 25 asset identifiers with **zero overlap** against the 10 assets the run generated, since assets take fresh identifiers each port. Every asset therefore prices wind at zero. The stale-lineage warning naming the peril timeseries steps is a symptom, not the cause. | **Resolved.** A run with `--typhoon` on 2026-07-23 put real wind through all ten commercial assets and the peril coherence checks passed (§6.6). The flag requirement stands as an operational note: `--all` alone still produces no wind. |
| L11 | **Pricing invariants are not asserted at write time** | The transmission-rate defect (§6.5) was caught by reading a run-log summary, not by the test suite. Bounded quantities — transmission ≤ 1, union ≥ both legs, intersection ≤ either — hold by construction and are checked ad hoc, if at all. | **Open.** Assert them where the values are written, so a units error fails the run rather than being noticed by whoever happens to read the log. |
| L10 | **Silent-zero class of failure** | Records that do not correspond to the storm catalogue produced a confident 0.0 conditional from 110 genuine flood events, with no error. | **Resolved for this path.** `conditional_probability` now raises on unresolved identifiers. The same class of failure may exist elsewhere in the chain and has not been swept for. |

## 10. Governance and registration

**This supersedes what v2.0 planned here.** v2.0 described registration into
`docs/models/governance_data/model_inventory.json`, a LaTeX model document, and
wiring into five registries plus a Makefile filter. Since then model governance
has migrated out of PhysicalRisk into a separate **event-sourced Postgres
platform** (the ModelRisk repo). There is no `model_inventory.json` to amend and
no `.tex` to write; models are registered through a governance command API and
the inventory is a derived read-model. Stage 5 was therefore completed *there*,
not here.

**What was registered (ModelRisk, `scripts/register_ef001.py`).** The 24 existing
PhysicalRisk models were bulk-migrated from the old JSON; MKM-EF-001 post-dates
that inventory, so it is registered directly through the same API the migration
used. The seed is idempotent (`python -m scripts.register_ef001` is a no-op on a
re-run) and under test (`tests/test_register_ef001.py`):

1. **Scalar record** — `MKM-EF-001`, "Event Frequency Model", **v1.0.0**, tier 1,
   category Hazard, type "Analytical Model", materiality High, RAG **Amber**
   (mechanism built and validated, but λ and the population weights are
   unvalidated seeds — see limitations), `source_module: src/models/frequency/`.
   The version was bumped 0.1.0 → 1.0.0 as a genuine release: built, wired to
   pricing on all legs, and validated end-to-end.
2. **Chain edges** — `MKM-GH-001 → MKM-EF-001 → MKM-PR-001`, declared as
   dependency collection items on the producer (direction downstream), matching
   how the migration declared source edges. GH-001 produces per-event
   exceedance, EF-001 annualises it, PR-001 prices it.
3. **4 assumptions** — λ is a catchment property not a gauge property; qualifying
   events arrive Poisson; the 168-hour hours-clause sequence is one event; the
   catalogue is an importance sample reweighted by the population weights.
4. **4 limitations** — the §5 λ-circularity ("lambda is unvalidated", recorded
   verbatim and asserted by a test), the population-weight judgement, the
   stationarity assumption, and single-small-catchment calibration.
5. **3 weaknesses** — the circular per-gauge validation arm; under-dispersion
   being unrepresentable on the Poisson–NegBin axis; and Monte Carlo sampling
   error (~1.6% at 10,000 years).
6. **9 SR 26-2 validation questions** auto-seeded on registration.

**Implementation note carried forward.** The registration API guards chain edges
against models not yet visible in the inventory view, so the ordering is
load-bearing: register, `rebuild_inventory_view`, *then* declare the chain, then
rebuild again. Declaring the chain before the rebuild silently drops both edges —
the property `tests/test_register_ef001.py` exists to catch.

**Open for the MRC (not build work).** The chain now carries both the new
GH → EF → PR path *and* the pre-existing direct GH → PR edge; removing a declared
dependency is an MRC decision, so the shortcut was left in place and flagged.
Formal deprecation of the legacy `flood_count / num_storms` metric is likewise an
MRC action pending the full-book parallel run.

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
