# PRS Capital Relief — project proposal

**Status:** proposal, 2026-09-30. Nothing built.
**Aim:** turn the illustrative study in `docs/capital/` into a governed model and
surface it in the loan pricer / standalone loan calculator as a "PRS cover and
capital" extension.

---

## 1. What is in `docs/capital/` today

| file | what |
|---|---|
| `prs_multi_year.py` | Monte Carlo of a corporate borrower's liquidity over the loan tenor under four PRS cover modes |
| `test_prs_multi_year.py` | 6 tests (mode equivalences, dominance ordering, marginal PDs sum to cumulative) |
| `prs_multi_year_audit.json` | One run: 1,000,000 paths, 5-year tenor, seed 20260930 |

The model: annual gauge maxima are GEV with a location drift; a flood costs the
borrower remediation plus business interruption; a parametric PRS pays between an
attach and an exhaust gauge level; default is liquidity below zero in any year.
Cumulative PD is annualised, mapped to a grade, and turned into a standardised
and an IRB corporate risk weight.

Recorded result (illustrative, uncalibrated):

| cover mode | 5y cumulative PD | annualised PD | grade | SA RW | IRB RW |
|---|---:|---:|---|---:|---:|
| none | 4.62% | 0.94% | BB | 100% | 90.3% |
| one year only | 4.36% | 0.89% | BB | 100% | 88.3% |
| annual renewal | 3.65% | 0.74% | BB | 100% | 82.4% |
| embedded (term-matched) | 3.26% | 0.66% | BB | 100% | 78.6% |

Embedded level premium: GBP 0.095m a year on a GBP 6m notional against GBP 32m debt.

### Three things to know before building on it

1. **It cannot run as it stands.** Every building block — `ExampleConfig`,
   `prs_payout`, `flood_losses`, `grade_for_pd`, `irb_corporate_rw` — comes from
   `prs_capital_relief_example`, which is not in the folder and was not found by a
   Spotlight search of this machine. That file is the first thing the project needs.
2. **No mode changes the grade.** All four stay BB, so the standardised risk weight
   never moves. The whole benefit shows up only under IRB (90.3% to 78.6%).
3. **On these parameters the economics are roughly break-even.** My own
   back-of-envelope from the audit JSON, not something the script computes:
   the IRB saving is about GBP 0.047m a year of capital cost (11.7 points of RW x
   GBP 32m x 10.5% x 12%) and the expected-loss saving about GBP 0.040m (0.28
   points of PD x 45% LGD x GBP 32m) — GBP 0.087m against a GBP 0.095m premium.
   The case turns on calibration, or on cover large enough to move the grade.

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

**In:** commercial loans, flood peril, the four cover modes, SA and IRB corporate
risk weights, shown in the standalone calculator and the commercial loan pricer
panel, plus a report page.

**Out for now:** residential mortgages (different borrower model and a retail
IRB formula), wind/fire/seismic cover, portfolio-level capital, and feeding the
result back into the traded PRS book.

---

## 4. Work packages

| WP | what | size |
|---|---|---|
| 0 | **Recover and baseline.** Obtain `prs_capital_relief_example.py`; run the 6 tests; reproduce the audit JSON (config hash `f5bc1cdf…`) as a golden file | S |
| 1 | **Make it a model.** New package `src/models/capital/` (borrower, cover, dynamics, capital, engine — each under 300 lines, no logic in `__init__`, licence headers). Every parameter to a new `config/capital.py`; reuse `config.loan` spreads. Tests to `tests/models/capital/`, an attribution rule in `TEST_MODEL_RULES`, coverage at the gate | M |
| 2 | **Replace the illustrative hazard.** Adapters that build the hazard and loss inputs for one asset from the gauge GEV fit, floor level and depth-damage curve, read only through `database`. Premium from the PRS pricer at the loan tenor, reconciled against the study's level premium | M |
| 3 | **Pricing bridge.** `routes/_loan_pricing/_capital.py`; new override keys (cover mode, notional, attach, exhaust, liquidity, EBITDA vol); a `capital` block in the calculator payload: PD by mode, grade, SA/IRB RW, capital, capital cost in bps, premium in bps, net benefit | M |
| 4 | **Calculator UI.** A "PRS cover and capital" section in `static/js/property/loanpricer/`: cover-mode selector, four-mode comparison table, marginal default by year. Jest and Playwright tests, JS coverage gate | M |
| 5 | **Governance.** Register the model (suggest `MKM-CR-001`), LaTeX documentation and sensitivity tables per `docs/models/new_model.md`, lineage entry, a page in the rloan / commercial loan report | M |
| 6 | **Calibration and validation.** Replace uncalibrated parameters, IRB formula checked against Basel worked values, path-count convergence, sensitivity to drift and renewal assumptions. Until done, every output carries the ILLUSTRATIVE label | L |

WP0 to WP3 give a working, tested back end; WP4 makes it visible; WP5 and WP6
make it defensible.

---

## 5. Design points

- **Speed.** The calculator re-prices on every edit. One million paths is for the
  report; the interactive path should use a smaller configured count (the tests
  already hold at 150,000) with a fixed seed and common random numbers across
  modes, cached on the config fingerprint the study already computes.
- **Three notions of credit risk.** The coupon uses a rating lookup, `price_loan`
  uses an affordability-driven spread, and this adds a cash-flow PD. They must not
  be silently mixed — see decision 2.
- **Reproducibility.** Keep the study's audit block (config hash, seed, status)
  in the payload and the report.

---

## 6. Decisions needed

1. **Where is `prs_capital_relief_example.py`?** Blocks WP0.
2. **Does the relief move the quoted coupon, or sit beside it?** Recommended for
   the first release: display only — show the current coupon and a "with embedded
   PRS" coupon side by side, and leave `price_loan` untouched. Pricing it in
   means choosing which credit measure governs.
3. **SA, IRB or both as the headline?** On current numbers only IRB shows a benefit.
4. **Governance tier.** It produces regulatory-capital figures, which argues for
   Tier 1; Tier 2 is defensible while it is display-only and labelled illustrative.
