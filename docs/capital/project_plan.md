# PRS Capital Relief — project proposal

**Status:** 2026-09-30. WP0 (recover and baseline) and WP1 (the package) are done.
WP2 is under way: the one-year view for a real asset is built (section 8). All four decisions
in section 6 are taken. Nothing built in `src/` yet.
**Aim:** turn the illustrative study in `docs/capital/` into a governed model and
surface it in the loan pricer / standalone loan calculator as a "PRS cover and
capital" extension.

---

## 1. What is in `docs/capital/` today

| file | what |
|---|---|
| `prs_capital_relief_example.py` | The base case: one-year Monte Carlo of a flood-exposed borrower with and without a PRS. Holds every building block and all parameters |
| `test_prs_capital_relief_example.py` | 17 tests, including the IRB formula against the Basel reference value (PD 1%, LGD 45%, M 2.5 gives 92.32%) |
| `prs_capital_relief_audit.json` | One run: 2,000,000 paths, seed 20260930 |
| `prs_multi_year.py` | The extension: the same borrower over the loan tenor under four cover modes. Imports the base case |
| `test_prs_multi_year.py` | 6 tests (mode equivalences, dominance ordering, marginal PDs sum to cumulative) |
| `prs_multi_year_audit.json` | One run: 1,000,000 paths, 5-year tenor, same seed |

The model: annual gauge maxima are GEV; a flood costs the borrower remediation
plus business interruption; a parametric PRS pays between an attach and an
exhaust gauge level; default is liquidity below zero. PD maps to a grade on an
illustrative master scale, and to a standardised and an IRB corporate risk
weight. Every figure below is illustrative and uncalibrated.

**WP0 is done (2026-09-30).** All 23 tests pass, and both recorded runs reproduce
exactly: same config hash, no differing figure. A full run takes under a second.

### One-year base case

| | without PRS | with PRS |
|---|---:|---:|
| 1y PD | 0.538% | 0.269% |
| grade | BB+ | BBB- |
| SA risk weight | 100% | 75% |
| IRB risk weight | 71.9% | 51.4% |
| PD given the site floods | 19.2% | 1.0% |

Economics, GBP m a year, on GBP 32m of debt and a GBP 6m notional: premium 0.091
(of which 0.030 is loading); bank capital-cost saving 0.101 under SA and 0.083
under IRB; expected-loss saving 0.039; borrower funding saving 0.40 if the
upgrade to investment grade is recognised.

### Five-year extension

| cover mode | 5y cumulative PD | annualised PD | grade | SA RW | IRB RW |
|---|---:|---:|---|---:|---:|
| none | 4.62% | 0.94% | BB | 100% | 90.3% |
| one year only | 4.36% | 0.89% | BB | 100% | 88.3% |
| annual renewal | 3.65% | 0.74% | BB | 100% | 82.4% |
| embedded (term-matched) | 3.26% | 0.66% | BB | 100% | 78.6% |

### What the two studies say together

1. **The headline result is a one-year result.** At one year the PRS halves the PD
   and carries the borrower across the investment-grade line, moving both risk
   weights. Over five years no mode changes the grade and only IRB moves.
2. **The two are not on the same footing.** The base case is a one-year PD, which
   is what a master scale and the IRB formula take. The extension annualises a
   five-year cumulative PD and feeds that to the same scale and formula. Year one
   agrees (0.54% marginal default in both); later years run near 1.05% because
   liquidity carries forward and is capped at its opening level, so the borrower
   cannot rebuild a buffer. Which PD the calculator shows is a modelling decision
   — see section 6.
3. **An earlier version of this plan read the economics as break-even.** That was
   a back-of-envelope on the five-year run alone, before the base case was
   available. The base case computes the economics itself and they are positive.

---

## 2. Why the loan pricer is the right home

The calculator already builds the coupon as
`risk-free + credit spread (rating) + all-in hazard spread`
(`src/routes/_loan_pricing/_coupon.py`), with the hazard leg PRS-priced from the
asset's own curve. It treats hazard only as something the borrower pays for. It
has no way to say "hedge the hazard with a PRS and see what that does to default
risk and capital", and it produces no PD, grade, risk weight, capital or
return-on-capital figure at all.

The capital study supplies exactly that missing half, and its inputs line up with
what the calculator already holds:

| study input | already in the platform |
|---|---|
| hand-set GEV (loc 4.0, scale 0.3, xi 0.1) | per-gauge fits, MKM-GH-001 (`models/hazard/gev.py`, `gaugehc.json`) |
| site flood level, depth slope | asset floor level, property flood response MKM-PF-001 |
| remediation cost from depth | depth-damage curves MKM-DD-001 |
| PRS attach / exhaust / loading | PRS analytical pricer MKM-PR-001 (`compute_prs_spread`, term structure) |
| debt, rate, tenor | the loan record / calculator inputs |
| income | net initial yield x value, already derived in `compute_standalone_pricing` |
| `ig_credit_spread_benefit` 125 bps | equals BB minus BBB in `config.loan.CREDIT_RATING_SPREADS` — a duplicate to remove |

Not in the platform and needing new inputs with config defaults: opening
liquidity, EBITDA volatility, contribution margin, insured share of damage, and
the renewal-market assumptions (post-payout uplift, withdrawal, hard market).

---

## 3. Proposed scope

**In:** commercial loans, flood peril, the four cover modes, the IRB corporate
risk weight as the headline measure, shown in the standalone calculator and the
commercial loan pricer panel, plus a report page. The relief is shown beside the
quoted coupon and does not change it.

**Out for now:** residential mortgages (different borrower model and a retail
IRB formula), wind/fire/seismic cover, portfolio-level capital, and feeding the
result back into the traded PRS book.

---

## 4. Work packages

| WP | what | size |
|---|---|---|
| 0 | **Recover and baseline.** Done 2026-09-30: both studies run, 23 tests pass, both recorded runs reproduce exactly (config hashes `fceb7d75…` and `f5bc1cdf…`) | done |
| 1 | **Make it a model.** Done 2026-09-30: package `src/models/capital/` (`regulatory`, `hazard`, `one_year`, `over_term`; largest 168 lines, `__init__` re-exports only), every parameter in `config/capital.py` with the investment-grade spread benefit taken from `config.loan`. 39 tests in `tests/models/capital/` at 100% coverage, including one that reproduces both recorded runs from the package | done |
| 2 | **Replace the illustrative hazard.** Build one asset's hazard, losses, PRS and borrower from platform data. One-year view built 2026-10-01 (section 8); the over-term view for an asset is next | L |
| 3 | **Pricing bridge.** `routes/_loan_pricing/_capital.py`; new override keys (cover mode, notional, attach, exhaust, liquidity, EBITDA vol); a `capital` block in the calculator payload with two views — `one_year` (PD, grade, IRB and SA RW, capital, capital cost in bps, premium in bps, net benefit, default attribution) and `over_term` (cumulative and annualised PD, IRB RW and marginal default by year for each cover mode). Read-only beside the coupon: `price_loan` and `_build_coupon` are not touched | M |
| 4 | **Calculator UI.** A "PRS cover and capital" section in `static/js/property/loanpricer/`: the one-year capital view, the over-term cover-mode comparison with marginal default by year, and the note explaining why the two PDs differ. Jest and Playwright tests, JS coverage gate | M |
| 5 | **Governance.** Register the model as Tier 1 (suggest `MKM-CR-001`) with its documentation, sensitivity tables and validation evidence. Model registration, model documentation and test-to-model attribution moved to MKM-ModelRisk in the governance extraction (September 2026), so this work package is done there, not in this repo; `docs/models/new_model.md` still describes the old in-repo process. Here: a page in the rloan / commercial loan report | L |
| 6 | **Calibration and validation.** Replace uncalibrated parameters, IRB formula checked against Basel worked values, path-count convergence, sensitivity to drift and renewal assumptions. Until done, every output carries the ILLUSTRATIVE label | L |

WP0 to WP3 give a working, tested back end; WP4 makes it visible; WP5 and WP6
make it defensible.

---

## 5. Design points

- **Speed.** Not a constraint. The full 2,000,000-path base case and the
  1,000,000-path five-year run each take under a second, so the calculator can
  run the recorded path counts on every edit, with the fixed seed and common
  random numbers the study already uses.
- **Three notions of credit risk.** The coupon uses a rating lookup, `price_loan`
  uses an affordability-driven spread, and this adds a cash-flow PD. They must not
  be silently mixed — see decision 2.
- **Reproducibility.** Keep the study's audit block (config hash, seed, status)
  in the payload and the report.

---

## 6. Decisions

Taken on 2026-09-30:

| decision | outcome | what it means for the build |
|---|---|---|
| Does the relief move the quoted coupon? | **No — it sits beside it** | The calculator shows the current coupon and the capital picture with embedded PRS side by side. `price_loan` and the coupon build-up stay as they are, so the three credit measures are never mixed |
| Headline risk-weight measure | **IRB** | The payload and the panel lead with the IRB corporate risk weight, which moves in both views. The standardised weight is secondary: it moves only in the one-year view, where the grade crosses into investment grade |
| Which PD the calculator shows | **Both, with the difference explained** | Two views. *Capital at one year*: one-year PD, grade, risk weights and the economics — the base case. *Cover over the loan term*: cumulative and annualised PD for the four cover modes — the extension. A short note beside them says why they differ: the one-year PD is what a rating scale and the IRB formula take; the term view carries liquidity forward, so later years default more often and the annualised figure is higher |
| Governance tier | **Tier 1** | Maximum governance from the start: full model documentation, sensitivity tables and validation evidence before it goes to the MRC. WP5 grows from M to L, and WP6 (calibration) becomes a condition of approval rather than a follow-up |

Nothing is open. One assumption to confirm when WP3 starts: IRB stays the
headline, and the one-year view also shows the standardised risk weight, because
the grade migration it reports is exactly what moves that weight (100% to 75%).

---

## 7. WP2 — design decided, paused 2026-09-30

No code written yet. The investigation below was done from code only: the
external data drive was unmounted at the time, so nothing was checked against
real data.

### What the platform has, and where it differs from the study

| input | study | platform | source |
|---|---|---|---|
| Gauge hazard | GEV of the **annual maximum** level | GEV of **per-storm peak** stage levels; annual probabilities come from the storm catalogue as `1 - exp(-lambda * p_event)` | `models/hazard/gev.py`, `builder.py:136-183`; read with `database.get_gauge_hazard_curves` |
| GEV shape | xi | stored as xi in `gev_shape` (positive = heavy tail). Data written before the xi fix in `gev.py:44-49` may hold scipy's c under the same name, with no version marker | `gev.py:37-57` |
| Asset to gauge | one gauge | depth is driven by the nearest **synthetic** gauge; the property PRS book triggers on the nearest **real** gauge. No gauge is stamped on the commercial CDM; it is chosen by haversine distance | `property/ts/flood/nearest.py:30`, `book_property/_core.py:150-160` |
| Gauge level to depth | `slope * (level - site level) + noise` | `max(0, (peak - bankfull) * retention - threshold)`, with bankfull = severe - 0.5 m, retention = `exp(-(dist / terrain scale) / 10 km)`, threshold = relative ground elevation + floor level. So slope = retention and site level = bankfull + threshold / retention. Deterministic: no basis noise | `property/ts/flood/propagation.py:119-176`, `velocity.py:84`, `floodrisk/elevation.py:24-47` |
| Damage | `1 - exp(-depth / 0.6)` | piecewise-linear depth-damage curve on depth above floor (`scalar_depth_damage`); a BRI polynomial variant. No commercial curve: `PROPERTY_TYPE_DAMAGE_FACTORS` is defined but unused | `floodrisk/depth_damage.py:66, 114`, `config/damage.py:40-55` |
| Business interruption | downtime = 3 months x damage | none anywhere in the platform | — |
| PRS payout | linear, attach 5.50 m to exhaust 6.05 m | binary: full notional once the reference gauge exceeds Severe Flood Warning. Property notionals are random, not tied to value | `hc/pricing/_process.py:41-83`, `_prs_schema.py:133-184` |
| PRS price | E[payout] x (1 + loading) | `compute_prs_spread(annual_hazard_rate, tenor, ...)`, CDS-style, floor 2 bps | `models/hazard/prs_analytical.py:69` |
| Borrower | operating company: revenue, EBITDA, liquidity | property investor: value, net initial yield, outstanding balance, rate, remaining term, LTV. No EBITDA, revenue or liquidity | `commercial.json`, `commercial_loan.json`; `database.list_commercial`, `list_commercial_loans` |

### Decisions (2026-09-30)

1. **A year's flood is simulated from storms.** Each year draws a Poisson number
   of storms at the gauge's rate and takes the highest per-storm GEV peak; a year
   with no storms has no flood. This matches how the platform turns storms into
   annual probabilities. Calibrated runs will not reproduce the illustrative
   ones, which stay available as the reference case.
2. **Two gauges, with basis risk modelled.** Depth from the controlling
   (synthetic) gauge, payout from the PRS reference (real) gauge, drawn jointly
   from the same storms. This replaces the study's random depth noise as the
   source of basis risk.
3. **The platform's binary Severe trigger** is the default payout, priced with
   `compute_prs_spread`. The linear layer stays available as an option.
4. **A property-investor borrower built from the CDM.** Income is passing rent
   (net initial yield x value); debt service from the loan's balance, rate and
   term; damage costed against the building's value; business interruption as
   lost rent. Liquidity and income volatility come from config defaults until
   calibrated.

### Things to resolve when WP2 resumes

- **Joint storm draws for two gauges.** The platform stores per-storm peaks per
  gauge (`database.get_gauge_timeseries`, `storm_responses`), which is where the
  dependence between the controlling and reference gauges would come from.
- **The GEV shape convention** of the stored data needs checking against real
  records once the drive is back.
- **`database.get_commercial` and `get_commercial_loan` look unable to find real
  records.** They match only top-level id fields, and real records are nested
  (`CommercialAsset.Header.PropertyID`, `Mortgage.Header.MortgageID`). Routes work
  around it by scanning the lists. Needs confirming against data, then either a
  fix in `database` or the same workaround.
- **Doc drift:** the retention length is documented as 3 km and set to 10 km
  (`velocity.py:89`, `config/models/_flood.py:108-113`).

---

## 8. WP2 progress — the one-year view for a real asset (2026-10-01)

Built and tested against a seeded local portfolio (`~/PhysicalRisk-testdata`,
thames, 10 commercial assets), since the data drive is unavailable.

### How it works

The investigation on resuming changed one thing about the design: the platform
already has the pieces, so the model uses them rather than recomputing.

- **Hazard: the platform's event catalogue, not the GEV fits.** Storms are
  grouped into hours-clause events (the storm sequences), each with a sampling
  weight and a catalogue coverage, arriving at the catchment's annual rate
  (MKM-EF-001). Years are drawn with the platform's own sampler,
  `draw_event_years`. The stored GEV shape is about 0.73 on every gauge, too heavy
  a tail to draw from directly.
- **Depth and damage: read, not recomputed.** The platform already writes each
  asset's flood depth and damage ratio per event in its commercial flood series,
  from the controlling gauge, ground and floor levels, distance and terrain.
- **Trigger: the reference gauge.** The asset's nearest real gauge passing Severe
  Flood Warning in any storm of an event. Depth and trigger come from different
  gauges, so basis risk arises from the platform's own data, both ways.
- **Year:** damage is summed over the year's events and capped at the whole
  building; the PRS pays its notional at most once a year.
- **Price:** `compute_prs_spread` on the annual trigger probability
  `1 - exp(-lambda x coverage x weighted share of triggering events)`, the
  platform's own rule.
- **Borrower:** the investor who owns the asset. Net rent (net initial yield x
  value) with a one-year shock, debt service from the loan (interest plus the
  amortising share for Repayment / Part and part), a liquidity buffer in months
  of debt service. Building value, insured share, downtime and PRS notional are
  in `config.capital.InvestorConfig`.
- **Who pays (decided 2026-10-01): the lender, out of the spread.** The overall
  coupon does not change; it is disaggregated. The credit spread drops by the PRS
  spread and the lender uses that slice to buy the cover. The borrower pays
  nothing extra and receives the payout, so its PD can only fall. The run reports
  the split (`coupon`: risk-free, credit spread before and after, PRS spread) and
  the lender's account (`bank_net_benefit`: expected-loss and capital savings
  less the premium). The study in `one_year` keeps its own convention, where the
  borrower pays.

Code: `src/models/capital/asset_inputs.py` (reads through `database`; scans the
lists because `get_commercial` / `get_commercial_loan` cannot find nested
records) and `src/models/capital/asset_one_year.py`. 27 new tests; the package is
at 100% line coverage. A run of 2,000,000 years takes about a quarter of a second.

### Results on the local portfolio (lender pays, notional sized to loss)

After the synthetic-gauge fix below and a regeneration with the same seed:

| asset | P(site floods) | PD without | PD with | grade | IRB without | IRB with | notional | PRS spread | lender net |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| CPROP-3612a41b | 1.10% | 0.895% | 0.402% | BB to BB+ | 88.6% | 62.9% | £13.7m | 22 bp | +£0.20m |
| CPROP-45e9d4e8 | 0.96% | 1.471% | 1.062% | BB- | 105.0% | 94.3% | £2.2m | 27 bp | +£0.00m |
| CPROP-03c61b6e | 0.28% | 2.235% | 2.155% | B+ | 118.5% | 117.3% | £18.6m | 12 bp | -£0.11m |
| CPROP-1c30d539 | 0.82% | 51.4% | 50.9% | B | 214% | 215% | £27.1m | 69 bp | -£0.19m |
| six others | 0.00% | unchanged | | | | | no cover | 0 bp | 0 |

The reference gauge triggers in 0.95% of years for every asset (they share it).

- **Where the asset's floods line up with the trigger, the PRS works as intended.**
  CPROP-3612a41b floods in 1.10% of years against a 0.95% trigger: its PD more
  than halves, it moves from BB to BB+, and the lender comes out £0.20m a year
  ahead after paying the premium from the spread.
- **Where they do not, the lender pays for basis risk.** CPROP-03c61b6e floods in
  only 0.28% of years, so most payouts land in years with no loss; the PD barely
  moves and the lender is £0.11m a year behind.
- **CPROP-1c30d539 defaults regardless** (debt service above rent), so the
  premium buys little.

### The synthetic-gauge fix (2026-10-01)

`_load_gaugets` (`src/port/src/property/ts/loader.py`) read only `GAUGE-` gauges,
so the synthetic gauge that is meant to control each asset's flood depth was
never loaded. Every depth came from a real gauge kilometres away, from which the
asset sat far above the water. The history:

- 2026-03-24: synthetic gauges added with the `SYNTH-` prefix; the loader already
  globbed `GAUGE-*.json`.
- 2026-04-03: a commit made the synthetic gauge "the single controlling
  authority". It never took effect because of the filter; the higher Zone 3
  spreads it reported came from the zone floor added in the same commit.
- 2026-09-05: a coverage-driven test pinned the exclusion and gave it a reason
  after the fact.

The loader now reads both prefixes, and the test asserts the opposite. On the
local portfolio the effect is large: 6 of 10 residential properties flood where
none did, and 4 of 10 commercial assets. **Every flood series, property and
commercial hazard curve and PRS price will change when the real portfolio is
regenerated.** Several routes keep their own `GAUGE-` filters
(`routes/propertyts/core_storm_list.py`, `routes/propertyts/animation/_helpers.py`,
`routes/gauges/storms.py`); they list or animate storms for display and have not
been reviewed against this change.

### Next

1. **A portfolio with flood-exposed commercial assets — done** by the
   synthetic-gauge fix (item 3); the local portfolio now has four.
2. **Notional sizing — done 2026-10-01.** The notional is the asset's uninsured
   loss (uninsured repair plus lost rent) in a typical flooding event: the
   catalogue-weighted mean over the events that flood it. An asset that never
   floods gets no cover and no spread is carved out of its loan.
3. **Blocker found and fixed: the flood series never used the synthetic gauge**
   (see above).
4. **The over-term view for an asset**, on the same event years.
