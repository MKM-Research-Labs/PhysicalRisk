# PRS XVA — project proposal

**Status:** 2026-10-09. Proposal agreed. WP0 done bar input owners (section 9). WP1 analytic engine (section 10) and WP2 Monte Carlo engine (section 11) built and tested. The proposed defaults in section 8 were
accepted on 2026-10-09; the regulatory characterisation and the model ID still need owners outside the model team.
**Aim:** add credit, funding and capital valuation adjustments (CVA, DVA, FVA, KVA, and
later MVA) to the Physical Risk Swap pricer. This is a new model (proposed ID
**MKM-XV-001**, to be confirmed in ModelRisk) and needs full independent validation
before any figure reaches a price, a blotter or P&L.
**Source:** `docs/xva/Green_XVA_Mathematics_and_Framework.pdf` (9 Oct 2026), a summary of
Green, *XVA* (Wiley, 2015). It sits untracked in the main checkout; equation numbers
below are Green's.

---

## 1. What the Green summary gives us

There is one argument, applied five times:
- hedge the trade and both defaults with a self-financing portfolio;
- write the PDE that hedge forces;
- apply Feynman–Kac.

The result is a sum of integrals. Each one is a rate times a survival-discounted expected exposure:

```
V̂ = V + U,   U = CVA + DVA + FCA + COLVA + MVA + KVA (+ TVA)
U(t) = −∫ₜᵀ D(t,s) 𝔼ₜ[f(s)] ds,   D(t,s) = exp(−∫ₜˢ (r + λ_B + λ_C) du)
```

| term | rate × exposure (standard close-out) | Green |
|---|---|---|
| CVA | (1 − R_C) λ_C × E[(V − X)⁺] | 3.70 |
| DVA | (1 − R_B) λ_B × E[(V − X)⁻] | 3.71 |
| FVA, one bond | s_F × E[V], discounted at r_F + λ_C | 9.64–9.67 |
| MVA | ((1 − R_B) λ_B − s_I) × E[I] | 10.34 |
| KVA | (γ_K − φ r) × E[K] | 13.25 |

**The funding strategy decides which terms exist.** Green's validation table (p. 19)
lists the assumptions a validator must see documented. Section 6 maps each of them to a test.

---

## 2. What the PRS pricer has, and what XVA needs

A PRS is a CDS with a flood trigger in place of the credit event. The payer buys
protection for a running spread. The receiver pays the full notional (recovery 0) on
the first severe trigger.

| XVA needs | the platform today |
|---|---|
| Risk-free value V(t) | Analytic: `compute_prs_spread` (`src/models/hazard/prs_analytical.py:69`), `price_prs` (QuantLib ISDA engine, `src/models/prs/prshc/pricer.py:33`), and MTM = (s_fair − s_trade) × A × N (`src/models/trading/delta_engine/pricer.py:129`) |
| Future values V(s, ω) on paths | **None.** No pricer simulates. The YLT layer (`src/models/frequency/ylt/_sample.py:92`, `draw_event_years`) simulates events per year, correlated across gauges |
| Netting sets, CSA terms | Only the synthetic counterparty fields `ISDAMasterAgreement`, `CSAAgreement`, `CollateralPosted` (`src/port/src/counterparty/_records.py`). The trade carries no CSA or netting-set field |
| Counterparty and own credit curves (λ_C, λ_B, R) | **None.** "Hazard" in the repo always means flood hazard. Rating spreads exist for loans (`config/loan.py`) |
| Funding curve (s_F) | **None.** There are two separate risk-free sources: the market-state yield curve and `config.loan.DISCOUNT_CURVE` |
| Capital per path (SA-CCR, BA-CVA) | **None.** `src/models/capital/` holds borrower IRB/SA risk weights, not counterparty capital |
| Cost of capital | `config/capital.py` has `cost_of_equity` 0.12 and `capital_ratio` 0.105 (MKM-CR-001) |

---

## 3. What is different about XVA on a PRS

Green's examples are swaps and an oil forward, where exposure diffuses. A PRS behaves
like a CDS, and that changes the model in six ways.

1. **Exposure is a jump, not a diffusion.**
   - Before a trigger, the bank's value is a small spread MTM.
   - At the trigger it becomes ±N. When the bank buys protection, that is a receivable of the full notional from the seller.
   - The CVA that matters is on the triggered state, held open by the settlement lag Δ_s (trigger determination plus payment).
2. **With deterministic flood hazard, the model is closed form.**
   - Given no trigger by t, V(t) is deterministic, so EPE(t) = S_E(t) · V(t)⁺.
   - The only randomness is the event time.
   - That gives an exact benchmark for the Monte Carlo engine (section 4.3). This is the PRS analogue of Green's analytic swap CVA (5.8).
3. **Variation margin does not remove the jump.**
   - Under a CSA, collateral tracks the pre-trigger MTM, which is small.
   - The notional falls due inside one margin period of risk. This is CDS gap risk.
   - The exposure is reduced only by initial margin, or by prefunding the payout (a collateralised or cat-bond-style structure).
4. **Wrong-way risk is structural.**
   - The natural protection sellers are (re)insurers, property lenders and utilities, and their credit weakens on the same floods that trigger the PRS.
   - Under independence, the jump CVA is about (1 − R_C) N · λ_C Δ_s × P(trigger). That is small, and probably wrong.
   - The platform already has the means to model this. `draw_event_years` shares the event draws across subjects, so a counterparty's own flood loss can be simulated on the same paths. That loss then scales λ_C, using Green's normalised path-weighting (Ch. 7, as in the oil example).
5. **Direction decides which terms matter.**
   - **Bank buys protection:** CVA on the notional, plus WWR. FVA and DVA are small.
   - **Bank sells protection:** CVA is small, since the counterparty owes only premiums. The bank holds a contingent liability of N, which brings DVA/FBA, and its warehoused flood risk brings capital.
6. **The regulatory treatment is an open question, not a parameter.**
   - It is not yet settled whether a PRS is a derivative or insurance.
   - If it is a derivative, the SA-CCR asset class is undecided: "other" commodity/climatic (SF 18%), or a credit-derivative analogue.
   - It is also undecided whether the FRTB residual-risk add-on applies, which it would to an exotic underlying such as natural disasters (1% of gross notional).
   - KVA depends on all three answers. They need a sign-off from Compliance or Regulatory Policy, not a modelling choice.

---

## 4. Proposed design

### 4.1 Principle: an overlay, not a change to the pricer

The design follows Green's Step 1, V̂ = V + U.
- MKM-PR-001 keeps producing V. It is not modified, so its validation stands.
- MKM-XV-001 consumes V and its inputs, and returns U and its components.
- This keeps the validation boundary clean, and it is the route already used for the capital model (MKM-CR-001).

```
market state (yield curve, flood hazard term structure)      ┐
counterparty credit, own funding curve, CSA / netting set     ├─► MKM-XV-001 ──► U = Σ XVA
MKM-PR-001 pricer (V, annuity, fair spread)                   │      │
MKM-EF-001 YLT event draws (MC engine, WWR)                   ┘      ▼
                                                     all-in spread s* − U / (N · A_risky)
```

### 4.2 Package layout

The layout follows the capital package's conventions:
- small modules;
- `__init__` re-exports only;
- every parameter in a `config/` dataclass;
- an audit block on every output (config sha256, seed, status).

| module | role |
|---|---|
| `config/xva.py` | `XvaConfig`: funding strategy, close-out, φ, γ_K, settlement lag, grid, paths, seed, WWR β |
| `src/models/xva/inputs.py` | `CreditCurve` (λ, R, from CDS or rating), `FundingCurve` (s_F), `Csa` (threshold, MTA, MPoR, IM), `NettingSet` |
| `src/models/xva/curves.py` | Survival, piecewise-constant hazard bootstrap (Green 4.14), D(t,s) with r + λ_B + λ_C |
| `src/models/xva/exposure_analytic.py` | Deterministic-hazard EPE/ENE per trade, including the settlement-lag jump term |
| `src/models/xva/exposure_mc.py` | Path simulation: flood events from the YLT, stochastic hazard (WP2), repricing of V at each grid date, netting, collateral with lookback MPoR (Green 6.39) |
| `src/models/xva/integrals.py` | The five integrals as weights w(tᵢ) × profiles (Green 19.1). This is the one place the discounting convention lives |
| `src/models/xva/wwr.py` | Normalised path-weighting λ_C(t, ω) from the counterparty's simulated flood loss |
| `src/models/xva/capital.py` | SA-CCR EAD, BA-CVA reduced, optional RRAO, each computed per path for KVA (Green §13.4) |
| `src/models/xva/allocation.py` | Euler allocation of netting-set CVA/FVA to trades (Green 3.84–3.93) |
| `src/models/xva/result.py` | `XvaResult`: components, profiles, all-in spread, audit block |
| `tests/models/xva/` | Unit, benchmark and reconciliation tests (section 6) |

### 4.3 Two engines that must agree

- **Analytic engine** (WP1):
  - scope: single trade, deterministic flood hazard, independence, uncollateralised;
  - it gives every term in closed form.
  - For the bank buying protection, with E the flood trigger:

  ```
  V(t) = N [ Prot(t) − s · A(t) ]                    on {τ_E > t}
  CVA  = −(1−R_C) ∫ λ_C D(0,s) S_E(s) V(s)⁺ ds                        (pre-trigger MTM)
         −(1−R_C) N ∫ λ_E(s) S_E(s) D(0,s) · P(τ_C ∈ (s, s+Δ_s] | τ_E = s) ds   (jump, unpaid notional)
  ```

  - The other terms follow the same pattern, with ENE for DVA, E[V] and s_F for the one-bond FVA, and K(t) for KVA.
- **Monte Carlo engine** (WP2):
  - adds stochastic hazard, netting sets that mix trades on correlated gauges, CSA collateral and wrong-way risk;
  - its deterministic, independent, single-trade case must reproduce the analytic engine within the MC error.
  - This reconciliation is the backbone of the implementation testing.

### 4.4 Methodology choices, with proposed defaults

| choice | proposed default | alternatives | why |
|---|---|---|---|
| Funding strategy | One bond: unilateral CVA + symmetric FVA, no DVA booked | Semi-replication without shortfall (DVA + FCA); perfect replication | Green and practice both favour it. It avoids double-counting own credit (Morini–Prampolini, 9.2–9.9) |
| Close-out | Risk-free, M = V | Risky (non-linear, 9.77); survivor funding (9.83) | Linear, so the integrals separate |
| Survival discounting | r + λ_B + λ_C on every term | Discount at r only | Green: production often drops it, and it moves KVA materially for weak names |
| Flood hazard dynamics | WP1 deterministic. WP2: log-hazard OU with seasonality, calibrated to the history of rolling re-estimates | CIR or JCIR++ intensity (16.352) | Without hazard vol, pre-trigger MTM has no optionality |
| Counterparty credit | CDS where quoted; otherwise a rating-to-spread proxy (Green 4.25 cross-section, later) | Rating PD table | Most PRS counterparties have no CDS |
| Wrong-way risk | β = 0 in the price. β > 0 as a governed stress, and as a price only after sign-off | Gaussian copula (7.9) | Green: treat WWR correlation as a stress parameter |
| Capital | SA-CCR + BA-CVA reduced, φ = 0, γ_K from `config/capital.py` | SA-CVA; φ = 1 | No IMM; keeps γ_K consistent with MKM-CR-001 |
| MVA | Out of scope at first | SIMM-projected IM | PRS trades are bilateral and outside SIMM; revisit if the hedges are margined |
| Time grid | Monthly, plus every premium date and Δ_s after each | Weekly | Captures saw-tooth premium exposure (Green Ch. 17) |
| Paths | 10,000, seeded | More if the convergence tests in section 6 show the standard error is material | Agreed 2026-10-09 as the starting point. Rare triggers make the jump term the noisiest; report its standard error |

### 4.5 Integration points (WP4)

- **Pricer output:**
  - an optional `xva` block on `price_prs` and the trading `enrich_trade` record;
  - the all-in spread is s* − U / (N · A_risky).
- **Blotter and pricing views:**
  - XVA columns per trade and per netting set;
  - an XVA quote on new trades.
- **EOD:**
  - XVA in the revaluation snapshot;
  - ΔXVA as a separate P&L line, kept out of ΔMTM so the explain stays clean (Green 21.10).
- **Monitoring:** a daily KPI of the difference between the XVA engine's V and the front-office V (Green Ch. 17).
- **Loan pricer:** later. Counterparty risk on the PRS seller reduces the capital relief claimed by MKM-CR-001. Feeding CVA into WP3 of the capital plan is a natural follow-on.

---

## 5. Work packages

| WP | scope | exit test |
|---|---|---|
| **WP0** | Decisions (section 8); regulatory characterisation; data sources for λ_C, s_F and CSA terms; CDM extension for netting set and CSA; model registration in ModelRisk | Signed-off decisions log; MKM-XV-001 registered with tier and owner |
| **WP1** | Curves, analytic engine, integrals; gauge PRS only, single trade | Closed form matches an independent numerical integration to 1e-8; limiting cases (section 6) pass |
| **WP2** | MC engine: YLT events, stochastic hazard, netting, CSA/MPoR, WWR, Euler allocation | Deterministic case reconciles to WP1 within 3 standard errors; allocations sum to the total exactly |
| **WP3** | Capital per path, KVA; the RRAO switch if it applies | SA-CCR and BA-CVA against hand-worked Basel examples |
| **WP4** | Integration (section 4.5); Property PRS after gauge PRS | UI and EOD tests; blotter XVA equals the engine's figure |
| **WP5** | Model documentation and validation pack pushed to ModelRisk (section 6) | Independent validation report; findings closed or accepted with overlays |
| WP6 (later) | MVA, TVA, warehousing ψ (Green Ch. 14), portfolio KVA (Ch. 15) | — |

Every WP keeps the illustrative audit-block discipline of the capital package. No
figure is marked anything but ILLUSTRATIVE until WP5 is complete.

---

## 6. Validation plan

The pack is structured to SR 11-7 / PRA SS1/23. The proposed tier is **Tier 1**, because
the model's output changes a client price and fair value.

**Conceptual soundness**
- Re-derive the adjustment PDE for a jump-to-notional payoff. Green's derivation hedges a diffusion. Show that the flood jump either is hedgeable (it needs an offsetting PRS) or enters ε_h.
- Document the funding strategy, the close-out and the DVA treatment, each against Green's alternatives.
- Clear every misprint in the summary's list that touches an equation used (3.25, 3.37, 9.61, 13.15, 13.37), by re-derivation rather than by transcription.
- Justify the flood-hazard dynamics: deterministic versus stochastic, and how forecast-driven hazard spikes near events are handled.

**Implementation verification**
- An independent re-implementation of the analytic engine. Green recommends a parallel implementation.
- MC against analytic reconciliation, with convergence in paths and time step tested separately (Green's two discretisation errors).
- Limiting cases:
  - λ_C → 0 gives CVA → 0;
  - R_C = 1 gives CVA = 0;
  - s_F = 0 gives FVA = 0;
  - a balanced book of offsetting payer and receiver trades on one gauge gives net FVA ≈ 0;
  - perfect VM leaves only the jump term;
  - IM ≥ N gives jump CVA → 0;
  - β = 0 makes the WWR weights equal 1 and the profiles unchanged.
- Repricing V in the engine must match `price_prs` and `compute_prs_spread` at t = 0.
- RNG discipline: seeded, repeatable, skip-ahead streams, and common random numbers for sensitivities and incremental XVA.

**Data and inputs**
- Counterparty and CSA data are synthetic today. Real inputs and their lineage are a prerequisite, not a validation finding.
- The proxy-spread method, if used, needs its own fit statistics.

**Sensitivity and stress**
- λ_C, R_C, s_F, γ_K and φ.
- Settlement lag Δ_s.
- Hazard volatility.
- WWR β across counterparty types (insurer, lender, utility).
- Correlation between gauges in a netting set.
- The regulatory-treatment alternatives for KVA.

**Outcomes analysis**
- Triggers are rare, so exposure backtesting is weak.
- Instead, rely on the hazard backtests of MKM-EF-001, plus a P&L explain of ΔXVA.

**Dependencies**
- MKM-PR-001, MKM-EF-001, MKM-TD-001 (which has no core model document, HANDOVER §6.6) and MKM-CR-001 feed this model.
- Their validation status bounds this one's.

**Ongoing monitoring**
- The front-office versus XVA-engine V KPI.
- MC standard error on each component.
- Carry artefacts: grid roll and RNG shifts.

---

## 7. Issues found in the existing pricer that validation will hit

These predate XVA, but the XVA model inherits them. They are best fixed or recorded in WP0.

1. **Contract terms disagree.**
   - The CDS pricer ends protection at the first trigger.
   - The capital model allows one payout a year.
   - The guide documents semi-annual premiums, but the code prices quarterly.
   - XVA exposure depends on all of these, so one definition must be agreed.
2. **Property PRS spread is undiscounted.** It is the exceedance probability × 1e4 (`src/port/src/property/hc/pricing/_process.py`), so there is no V(t) to take an exposure of. A proper term pricer is needed before XVA on Property PRS.
3. **There are two risk-free curve sources** (the market-state yield curve and `config.loan.DISCOUNT_CURVE`), with no OIS/funding split.
4. **`price_prs` collapses the hazard term structure to a flat rate** (`src/models/prs/prshc/curves.py:71-87`), and `_remaining_tenor` rounds to whole years. Exposure profiles need fractional remaining tenors.

---

## 8. Decisions (agreed 2026-10-09)

The proposed option in each item below is the decision. Items 2 and 7 still need named owners.


1. **Funding strategy and DVA**: one-bond symmetric FVA with no DVA booked (proposed), or DVA + FCA.
2. **Regulatory characterisation**: derivative or insurance; the SA-CCR asset class; whether RRAO applies. This needs an owner outside the model team.
3. **Counterparty credit source** for unquoted names.
4. **First scope**: gauge PRS only, bank as protection buyer and seller, uncollateralised (proposed).
5. **WWR**: stress only (proposed), or priced from day one.
6. **Capital code**: SA-CCR and BA-CVA in a shared `regulatory` module used by both MKM-XV-001 and MKM-CR-001, or kept separate.
7. **Model ID and owner** in ModelRisk.

---

## 9. WP0 progress (2026-10-09)

WP0 has four deliverables. Three are done in code or documents. The fourth
(registration) is prepared and tested but has not been run against the live
inventory.

| deliverable | state |
|---|---|
| Decisions log | Below: D-01 to D-13. D-09 and D-11 to D-13 still need an input owner |
| Regulatory characterisation | Question paper written: [`regulatory_characterisation.md`](regulatory_characterisation.md). Needs an owner outside the model team |
| CDM extension | Done (see below). Tests: `tests/port/cdm/test_credit_support.py` |
| ModelRisk registration | `scripts/register_xv001.py` + `_xv001_data.py` on ModelRisk branch `claude/register-xv001` (commit `e993241`). Tests pass on a disposable database. **Deferred until development is complete** (owner, 2026-10-09). A first live run failed: the script exists only on that branch, and the local Postgres data directory was missing. Revisit both at WP5 |

### Decisions log

| ID | decision | source |
|---|---|---|
| D-01 | One-bond funding strategy: unilateral CVA + symmetric FVA at s_F. DVA is computed and shown, not booked | §8.1 |
| D-02 | Risk-free close-out, M = V | §4.4 |
| D-03 | Survival discounting at r + λ_B + λ_C on every term | §4.4 |
| D-04 | First scope: gauge PRS (`TradeType='PRS'`), bank as buyer and seller. Uncollateralised in WP1; CSA and netting in WP2 | §8.4 |
| D-05 | Wrong-way risk: β = 0 in the price, β > 0 as a governed stress | §8.5 |
| D-06 | Capital: SA-CCR + BA-CVA reduced, φ = 0. γ_K = `config/capital.py` `cost_of_equity` (0.12), shared with MKM-CR-001. Green's oil example uses 10%; the difference is a sensitivity, not a second parameter | §4.4 |
| D-07 | SA-CCR and BA-CVA live in one regulatory module used by MKM-XV-001 and MKM-CR-001 | §8.6 |
| D-08 | Monte Carlo: 10,000 seeded paths to start; each component reports its standard error. The closed form is the first control variate if the jump term is too noisy | agreed 2026-10-09 |
| D-09 | Settlement lag: `PRS_SETTLEMENT_DAYS` = 5 business days, carried on each trade as `Payouts.SettlementDays`. **Provisional**: the term sheet says "paid at the time of the trigger", and the real lag (calculation-agent confirmation plus payment) needs confirming by Product/Legal | WP0 |
| D-10 | Contract terms for XVA follow the trade pricer (MKM-PR-001): first-trigger termination, quarterly premium. The trade record's `ScheduleData.Tenor = '6M'` disagrees with the pricer, which prices quarterly; that is raised as a finding against MKM-PR-001, not resolved inside the XVA model | §7.1 |
| D-11 | Counterparty credit: CDS where quoted, otherwise a rating-to-hazard proxy in `config/xva.py`. `config/loan.py` `CREDIT_RATING_SPREADS` are loan margins, not CDS spreads, so they are **not** reused. **Open**: the source for the proxy table | §8.3 |
| D-12 | Own funding spread s_F and recovery R_B: a Treasury input in `config/xva.py`. **Open**: owner and source | WP0 |
| D-13 | Risk-free curve: the market-state yield curve, the same one the Trading Desk revalues on, so V agrees with the blotter. `config.loan.DISCOUNT_CURVE` is not used | §7.3 |
| D-14 | MC time integration: midpoint rule on cells that never straddle a premium date, maturity or settlement end; 26 cells per quarter (~3.5 days). Bias on the saw-tooth is O(h²), 0.05% at 26 cells (about 0.2 SE at 10,000 paths) | §11 |
| D-15 | Flood-hazard dynamics: CIR++ on a catchment factor Y (Y0 = θ = 1), gauge intensity λ_g Y + φ_g(t), with φ_g fitted to the pricer's flat hazard. Replaces the "log-hazard OU" of §4.4: CIR++ prices V(t) in closed form, reproduces the pricer at t = 0 on every path, and is exactly WP1 at σ = 0. κ = 0.5, σ = 0.3 are **placeholders**; calibration to the history of re-estimated hazard has no owner yet | §11 |

### CDM extension

All new fields are optional, so existing trade and counterparty files still validate.

- **PRS trade** (`src/port/cdm/_prs_schema.py`):
  - `Header.NettingSetID` references the counterparty's netting set.
  - `Payouts.SettlementDays` holds the payout lag (D-09).
  - Both are written by the book generator (`book_common/_records.py`) and by the trade-commit route (`routes/prs/blueprint.py`), and both appear in the flat mapping.
- **Counterparty** (`src/port/cdm/ctpy/_schema.py`): a new `CreditSupport.NettingSets[]` block holding:
  - `NettingSetID`, `MasterAgreement` and `CloseOutNetting`;
  - `CsaType` (None / VM / VM+IM) and `CollateralCurrency`;
  - `Threshold`, `MinimumTransferAmount` and `MarginPeriodOfRiskDays`;
  - `InitialMarginReceived` and `InitialMarginPosted`.

  When present, the block is validated (`ctpy/_credit_support.py`).
- **Generator:** the counterparty generator attaches one synthetic netting set per party (`NS-{PartyID}`).
  - The block is derived from the existing `_platform` flags (`CSAAgreement`, `NettingAgreement`, `ISDAMasterAgreement`), so the generator's random draws do not change.
  - The terms come from `config/port/_book.py` `SYNTHETIC_CSA_TERMS`. They are placeholders, not executed CSA terms.

### Next

- WP0 is complete except the open owners (D-09, D-11, D-12, the regulatory paper). Registration moves to WP5.
- WP1 (curves, the closed-form engine, the integrals) can start in parallel. It needs only placeholder inputs, and its outputs stay ILLUSTRATIVE.

---

## 10. WP1 — the analytic engine (2026-10-09)

**Exit criteria met.** The engine and an independent re-implementation agree to
between 1e-11 and 1e-15 relative, against a target of 1e-8. Every limiting case in
§6 passes. There are 82 tests and coverage is 100%.

### What was built

| file | role |
|---|---|
| `config/xva.py` | `XvaConfig` (frozen, fingerprinted). Holds the placeholder rating-to-CDS table (D-11) and the funding spread of 75bp, R_B 40% (D-12). γ_K is taken from `config/capital.py` |
| `src/models/xva/curves.py` | `ZeroCurve` (the pricer's own discounting), piecewise-constant `HazardCurve`, and a CDS bootstrap on the pricer's convention |
| `src/models/xva/inputs.py` | `PrsTrade`, `Market`, and `build_market` (rating proxy or an explicit curve) |
| `src/models/xva/valuation.py` | V(t) given no trigger, the fair spread, and the pending payout |
| `src/models/xva/exposure_analytic.py` | Exact EPE, ENE and EE: pre-trigger value plus the pending notional during the settlement lag |
| `src/models/xva/integrals.py` | The XVA integrals and kernels, the breakpoint grid (including the zeros of V), and the KVA integral for a given capital profile |
| `src/models/xva/analytic.py` | `run`: both funding views, booked view, DVA disclosure, exact break-even spread, profiles, audit block |
| `tests/models/xva/` | Pricer reconciliation, reference benchmark, an expectation-versus-replication Monte Carlo check, limiting cases, the engine and its guards |

### How it was tested

1. **Against the pricer.**
   - Fair spread and risky annuity equal `compute_prs_spread` and `compute_risky_annuity` to 1e-12, across 1–5y tenors and trigger probabilities of 0.5%–8%.
   - V(0) equals the Trading Desk MTM to the penny.
2. **Against an independent implementation** (`tests/models/xva/_reference.py`).
   - It shares no code with the engine: plain cash-flow loops and adaptive `quad` integration, where the engine uses fixed Gauss-Legendre.
   - Agreement is 1e-11 or better: both views, buyer and seller, flat and humped curves, and a 60-day lag.
3. **Expectation against replication.**
   - CVA and DVA are priced by sampling the three default times directly (Green 3.44).
   - Both match the replication integrals (3.70–3.71) within 4 standard errors.
4. **Limiting cases.**
   - λ_C = 0 or R_C = 1 gives no CVA; s_F = 0 gives no FVA, DVA or FCA.
   - Offsetting trades have zero net FVA.
   - With R_B = 0 the two funding views are identical to 1e-13.
   - Swapping the bank and the counterparty turns CVA into DVA.
   - With no settlement lag and an out-of-the-money buyer, there is no CVA.
   - With no flood hazard, the buyer has no CVA.
   - Jump CVA is linear in the lag.
   - KVA on constant capital matches its closed form.

### Correction to D-03

D-03 said every term is discounted at r + λ_B + λ_C. That is right for semi-replication, but the strategy booked under D-01 is the one-bond strategy. Green's one-bond result (9.64–9.67) discounts at **r_F + λ_C = r + s_F + λ_C**, and λ_B drops out. The engine therefore uses the kernel that matches the strategy:
- **one-bond:** DF · e^(−s_F s) · S_C;
- **semi-replication:** DF · S_B · S_C.

The two coincide exactly when R_B = 0, and that is one of the tests. D-03 should read: "survival discounting on every term, with the kernel the funding strategy implies."

### Illustrative results

Inputs:
- GBP 10m, 5y, trigger probability 2% a year (fair spread 203.56bp), traded at the fair spread;
- book default yield curve;
- rating-proxy counterparty;
- settlement lag of 5 business days.

GBP; a negative figure is a cost to the bank.

| counterparty | bank | CVA | FVA | booked (one-bond) | DVA (disclosed) | semi-rep total | all-in − fair (bp) |
|---|---|---:|---:|---:|---:|---:|---:|
| A | buys | −91 | +663 | +573 | +778 | +566 | +0.14 |
| A | sells | −574 | −663 | −1,237 | +123 | −1,223 | +0.30 |
| BBB | buys | −192 | +647 | +454 | +759 | +449 | +0.11 |
| BBB | sells | −1,219 | −647 | −1,866 | +120 | −1,844 | +0.46 |
| BB | buys | −448 | +603 | +156 | +708 | +154 | +0.04 |
| BB | sells | −2,834 | −603 | −3,438 | +112 | −3,399 | +0.88 |

The BBB buyer's CVA by settlement lag: 0 days gives 0; 5 days −192; 20 days −767; 60 days −2,281.

### What the results say

1. **Under independence, XVA on a PRS is below 1bp.** This is §3.4 made concrete.
   - When the bank buys protection at par, CVA is almost entirely the jump term: (1 − R_C) N λ_C Δ_s × P(trigger).
   - Before the trigger, the buyer's value is never positive at par, because premium is paid in arrears. So with no lag there is no CVA at all.
   - **The economics that matter are wrong-way risk (WP2) and capital (WP3), not this.**
2. **The seller's CVA is on premium, not notional.** The counterparty owes accrued premium, which is the saw-tooth, and that is what the seller is exposed to.
3. **The buyer earns a small funding benefit.** It owes accrued premium, so in effect it borrows from the counterparty. Hence an all-in spread slightly above fair.
4. **The two funding views agree within 1–2%** at these inputs. The difference is the discount kernel, s_F against λ_B.
5. **Solve the all-in spread exactly.**
   - The first-order approximation s* − U/(N A) understates the seller's charge by about 9% (BBB at λ_C = 5%).
   - The reason: a wider spread enlarges what the buyer owes, so CVA grows with the spread.

### Findings against MKM-PR-001 (record only)

- **F-1.** `compute_prs_spread` floors the fair spread at 2bp, and `compute_mark_to_market` uses that floored spread. For a trigger probability below about 0.02% a year, the MTM is therefore not the PV of the legs. The XVA engine uses the unfloored PV.
- **F-2.** The pricer discounts the payout at mid-period and ignores the settlement lag. The engine follows the pricer for V, so that V(0) reconciles, and applies the lag only to exposure. The error in V is O(r Δ_s), about 0.08% of the protection leg.
- **F-3.** `compute_mark_to_market` rounds to the penny. This is immaterial, but tests must allow for it.

### Next — WP2

- The Monte Carlo engine on the MKM-EF-001 event draws, at 10,000 paths (D-08).
- Stochastic hazard.
- Netting sets and CSA terms from the new CDM fields.
- Wrong-way risk as a stress (D-05).

Its deterministic, independent, single-trade case must reproduce this engine within 3 standard errors.

---

## 11. WP2 — the Monte Carlo engine (2026-10-09)

**Exit criterion met.** With σ = 0, one trade, no collateral and β = 0, every
term in both funding views is within 3 standard errors of the analytic engine
for both buyer and seller. The largest gap is 2.1 SE. Over 12 seeds the gaps
centre on zero (mean −0.07 and −0.13 SE), so the time rule adds no visible bias.

There are 144 tests in the package and coverage is 99.5%.

### What was built

| file | role |
|---|---|
| `src/models/xva/cir.py` | CIR factor: an exact noncentral-χ² step, and closed-form bonds written to stay stable as σ → 0. Also the CIR++ trigger fitted to the market curve (D-15) |
| `src/models/xva/events.py` | Correlated first-trigger times per gauge, built on the MKM-EF-001 catalogue (rate × coverage, weights, Severe flags). Events are a Cox process in the factor clock. Each gauge's marginal is held to the market rate by thinning or a top-up |
| `src/models/xva/netting.py` | `Csa`, `NettingSet`, and the parsers for the WP0 CDM `CreditSupport` fields. Collateral uses Green's lookback (6.39) with threshold and MTA. IM is static in each direction |
| `src/models/xva/paths.py` | The cell grid (D-14), factor paths, and trade values on paths: closed form while alive, the pending notional during the settlement lag |
| `src/models/xva/monte_carlo.py` | Netted, collateralised exposures (Green 9.30, 10.28, 10.31). A per-path estimator for every term, with its standard error. WWR path weights and Euler CVA allocation |
| `config/xva.py` | Adds `n_paths` 10,000, `seed`, `cells_per_quarter` 26, κ, σ and `wwr_beta` |

### How it was tested

1. **Reconciliation to WP1 and time error.**
   - Measured separately on the analytic profiles: the midpoint rule's error is under 0.05% and quarters when the cells halve, as O(h²) predicts.
2. **CIR.**
   - The bond price matches a 100,000-path simulation.
   - The exact step has the CIR mean and variance.
   - σ → 0 converges to the deterministic bond. This test exposed a cancellation in the textbook A(τ) at σ ≈ 1e-6 (error 3e-4), which is now fixed.
   - The CIR++ shift reproduces the market curve to 1e-13 at σ = 0, 0.3 and 0.8.
   - V(0) equals the pricer on every path.
3. **Triggers.**
   - Each gauge's simulated trigger probability equals the market's, within 4 SE, whether there is no catalogue, the catalogue is thinned or the catalogue is topped up, at σ = 0 and 0.5.
   - Shared catalogue events make gauges trigger together; independent gauges do not.
4. **Netting and collateral.**
   - Offsetting trades on one gauge have no exposure.
   - Netting never costs more than not netting.
   - Without netting, CVA is exactly the sum of the standalone CVAs (to 1e-12).
   - An infinite threshold equals no CSA.
   - IM equal to the notional removes the jump CVA.
5. **WWR and allocation.**
   - β = 0 gives unit weights, and the weights average 1 at every node.
   - β > 0 raises the buyer's CVA.
   - Euler contributions sum exactly to the uncollateralised netted CVA.
   - Runs are reproducible from the seed.

### Illustrative results

Inputs:
- GBP 10m, 5y, trigger probability 2% a year, at the fair spread (203.6bp);
- BBB-proxy counterparty;
- 10,000 paths.

GBP; a negative figure is a cost. The last column is |U| / (N A).

| case | CVA ± SE | FVA | booked total | ≈ bp |
|---|---:|---:|---:|---:|
| buys, σ = 0 | −201 ± 6 | 639 | 437 | 0.10 |
| buys, σ = 0.3 (default) | −933 ± 11 | 653 | −279 | 0.07 |
| buys, σ = 0.3, WWR β = 1 | −1,177 ± 17 | 653 | −523 | 0.12 |
| buys, σ = 0.3, WWR β = 3 | −2,677 ± 75 | 653 | −2,024 | 0.47 |
| buys, σ = 0.3, VM (thr 0, MPoR 10d) | −622 ± 5 | 13 | −610 | 0.14 |
| buys, σ = 0.3, VM + IM = notional | −1 ± 0 | 13 | 12 | 0.00 |
| sells, σ = 0 | −1,216 ± 2 | −639 | −1,855 | 0.43 |
| sells, σ = 0.3 (default) | −1,970 ± 13 | −653 | −2,623 | 0.61 |
| sells, σ = 0.3, WWR β = 1 | −1,841 ± 13 | −653 | −2,495 | 0.58 |
| sells, σ = 0.3, WWR β = 3 | −1,183 ± 8 | −653 | −1,837 | 0.43 |
| sells, σ = 0.3, VM (thr 0, MPoR 10d) | −643 ± 5 | −13 | −656 | 0.15 |
| sells, σ = 0.3, VM + IM = notional | 0 ± 0 | −13 | −13 | 0.00 |
| buy G1 + sell G2, independent gauges | −296 ± 9 | 2 | −294 | 0.07 |
| buy G1 + sell G2, shared catalogue events | −3 ± 1 | 1 | −2 | 0.00 |

A run takes about 0.5–1 s per trade at 10,000 paths.

### What the results say

1. **Hazard volatility is the first thing that moves CVA.**
   - At σ = 0.3 the buyer's CVA is 4.6× the deterministic figure. The buyer's MTM goes positive on paths where hazard rises, and that is option value WP1 cannot see.
   - σ is a placeholder (D-15), which makes its calibration the most important open input after the regulatory question.
2. **The same WWR stress is wrong-way for the buyer and right-way for the seller.**
   - The driver is the counterparty's flood losses, proxied by triggers in the netting set.
   - A buyer is owed the notional exactly when those losses occur. A seller is owed nothing then.
   - So β must be set per counterparty type and direction. It cannot be one desk-wide number (D-05).
3. **Variation margin does not reach the jump; initial margin does.** This is §3.3 confirmed. VM cuts the seller's premium exposure by two thirds, but for the buyer the residual is mostly the jump.
4. **Correlated offsetting trades net almost to zero.** A buy and a sell on gauges hit by the same events behave as one position. The catalogue's dependence is worth modelling: treated as independent, the same pair shows 100× the CVA.

### Limitations recorded for validation

- **L-1. The classical MPoR lookback freezes collateral but not trade cash flows.**
  - A buyer that has posted VM against accrued premium pays that premium inside the MPoR, so it is briefly over-collateralised.
  - At σ = 0 this makes the buyer's CVA *higher* with VM than without it (−499 against −194).
  - This is the effect Andersen, Pykhtin and Sokol (2017) analyse. Their "advanced" MPoR conventions are the remedy and are a candidate for WP6.
- **L-2. The event clock uses the trapezoid integral of Y on the simulation grid**, O(h²). The exposure valuation uses the exact CIR conditional. The two agree exactly at σ = 0.
- **L-3. The WWR driver is the number of the netting set's gauges triggered so far.** A counterparty's real flood exposure (its insured book, its loan book) needs counterparty data the platform does not have.
- **L-4. Euler allocation is exact only for an uncollateralised netted set.** With thresholds, IM or no netting the residual is reported, not hidden.
- **L-5. The CIR++ fit is implemented for a flat trigger hazard** (the pricer's convention). A term structure raises an error rather than being silently approximated.
- **L-6. Each run has a single seed and no variance reduction.** The closed form is available as a control variate if 10,000 paths prove too noisy (D-08).

### Next — WP3

Capital per path: SA-CCR EAD and BA-CVA computed in each Monte Carlo state, fed to the KVA integral (`integrals.kva` already exists). The RRAO is a switch, pending the regulatory paper.
