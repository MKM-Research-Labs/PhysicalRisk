# PRS Capital Relief — project proposal

**Status:** 2026-09-30. WP0 (recover and baseline) is done. All four decisions
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
| 1 | **Make it a model.** New package `src/models/capital/` (borrower, cover, dynamics, capital, engine — each under 300 lines, no logic in `__init__`, licence headers). Every parameter to a new `config/capital.py`; reuse `config.loan` spreads. Tests to `tests/models/capital/`, an attribution rule in `TEST_MODEL_RULES`, coverage at the gate | M |
| 2 | **Replace the illustrative hazard.** Adapters that build the hazard and loss inputs for one asset from the gauge GEV fit, floor level and depth-damage curve, read only through `database`. Premium from the PRS pricer at the loan tenor, reconciled against the study's level premium | M |
| 3 | **Pricing bridge.** `routes/_loan_pricing/_capital.py`; new override keys (cover mode, notional, attach, exhaust, liquidity, EBITDA vol); a `capital` block in the calculator payload with two views — `one_year` (PD, grade, IRB and SA RW, capital, capital cost in bps, premium in bps, net benefit, default attribution) and `over_term` (cumulative and annualised PD, IRB RW and marginal default by year for each cover mode). Read-only beside the coupon: `price_loan` and `_build_coupon` are not touched | M |
| 4 | **Calculator UI.** A "PRS cover and capital" section in `static/js/property/loanpricer/`: the one-year capital view, the over-term cover-mode comparison with marginal default by year, and the note explaining why the two PDs differ. Jest and Playwright tests, JS coverage gate | M |
| 5 | **Governance.** Register the model as Tier 1 (suggest `MKM-CR-001`), LaTeX documentation and sensitivity tables per `docs/models/new_model.md`, lineage entry, a page in the rloan / commercial loan report | L |
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
