# MKM-EF-001 Stage 6k — Activation Decision Brief

**Component:** Event Frequency Model — `MKM-EF-001` (governance record v1.1.0)
**Purpose:** Decision brief for the Model Risk Committee (MRC) on whether to
activate either of the two reprices Track B built and left switched off.
**Status:** Awaiting MRC decision + external data. No code change is outstanding.
**Date:** 2026-07-28
**Owner:** CSO, MKM Research Labs

---

## 1. What this brief decides

Track B (Stages 6a–6j, plan `frequency_layer_definition_and_plan_v2.md` v2.14)
built two capabilities that **change priced quantities** and deliberately
shipped them **switched off** behind empty per-catchment registries:

| # | Capability | Registry (empty today) | Stage |
|---|------------|------------------------|-------|
| A | **Non-stationary term structure** — a climate trend compounding the arrival rate over a contract tenor | `CATCHMENT_ANNUAL_GROWTH` | 6h |
| B | **Decoupled wind** — wind priced as an independent arrival process that counts the unpaired typhoons the coupled model drops | `DECOUPLED_WIND_CATCHMENTS` | 6i |

With both registries empty, every catchment reproduces the prior stationary and
coupled numbers **byte-identically** — nothing reprices. Activating either is a
one-line config change that moves live pricing, so it is an MRC decision, not an
engineering one. This brief is the evidence for that decision.

The 6j sensitivity harness (`models.frequency.sensitivity.trend_sensitivity`,
`port…pricing._sensitivity.wind_decoupling_sensitivity`) exists precisely to
quantify each reprice **before** it is switched on, without touching production.

---

## 2. Decision A — climate trend (`CATCHMENT_ANNUAL_GROWTH`)

### 2.1 What activation does

Seeding a non-zero annual growth `g` for a catchment makes its arrival rate
compound over the tenor, `λ_t = λ₀·(1+g)^t`, so a T-year contract compounds
distinct annual rates instead of one repeated. Single-year pricing is unchanged;
the reprice is entirely in the **multi-year term structure**.

### 2.2 Evidence — the magnitude of the reprice

Produced by `trend_sensitivity` at the config arrival rate **λ = 4.5/yr**, tenor
**5 years**, across the plausible range of per-event severe conditionals `p`.
Cells show the 5-year severe exceedance probability and its relative change from
the stationary (g=0) baseline:

| `p_event` | stationary | g=1% | g=2% | g=3% | g=5% |
|-----------|-----------|------|------|------|------|
| 0.005 | 0.1064 | 0.1084 (+1.9%) | 0.1105 (+3.8%) | 0.1126 (+5.8%) | 0.1169 (+9.9%) |
| 0.010 | 0.2015 | 0.2051 (+1.8%) | 0.2088 (+3.6%) | 0.2125 (+5.5%) | 0.2201 (+9.3%) |
| 0.020 | 0.3624 | 0.3681 (+1.6%) | 0.3740 (+3.2%) | 0.3799 (+4.8%) | 0.3918 (+8.1%) |
| 0.030 | 0.4908 | 0.4977 (+1.4%) | 0.5047 (+2.8%) | 0.5117 (+4.2%) | 0.5257 (+7.1%) |

**Reading:** the reprice is modest, bounded, and scales cleanly with the growth
assumption. A 2%/yr trend lifts the 5-year severe exceedance by roughly 3–4%
relative; a 5%/yr trend by 7–10%. The effect is larger at low `p` (the tail),
smaller where the baseline is already high.

### 2.3 What activation needs

- **A defensible growth value** — this is the crux. `g` is a *climate signal*,
  not a modelling free parameter: it must come from an observed or projected
  trend in the catchment's storm-event frequency, not engineering judgement.
  On synthetic catchments the arrival rate is itself unvalidated (plan §5), so a
  trend on top of it compounds an unvalidated base.
- **MRC sign-off** on that value and on repricing multi-year contracts.
- A **parallel run** (regenerated data) to confirm the book-level effect matches
  §2.2's per-gauge magnitude.

### 2.4 The change, once decided

```python
# config/frequency/_schema.py
CATCHMENT_ANNUAL_GROWTH: Dict[str, float] = {"halong": 0.02}  # example
```

---

## 3. Decision B — decoupled wind (`DECOUPLED_WIND_CATCHMENTS`)

### 3.1 What activation does

Opting a catchment in prices its wind peril as an **independent** Poisson process
rather than coupled 1:1 to storm sequences. The wind conditional then runs over
the whole typhoon catalogue, so the **unpaired, off-sequence typhoons the coupled
model silently drops are counted**; the union and intersection legs follow from
the two marginal annual probabilities (`1-(1-P_f)(1-P_w)`, `P_f·P_w`).

This closes the coupling finding of Stage 6f: the coupled model understates wind
wherever unpaired typhoons are common.

### 3.2 Evidence — status

The **mechanism** is built and unit-tested (coupled vs decoupled, inclusion-
exclusion, independence bounds). The **quantified reprice** — the coupled-versus-
decoupled spread delta and the count of dropped typhoons for a real book — is
produced by `wind_decoupling_sensitivity`, but that needs the **typhoon damage
index**, which is a port artifact. So the wind half of the evidence is pending a
**user-run port** with the typhoon stage enabled; it has not been produced here.

### 3.3 What activation needs

- A **port run** with typhoon damage, to populate the wind index and let
  `wind_decoupling_sensitivity` report the delta per asset.
- **Real typhoon data** — the decoupled wind rate is unvalidated on synthetic
  catchments, and the mode assumes flood/wind independence and uniform weights
  over the damage-bearing typhoon population (both recorded as limitations on the
  v1.1.0 governance record).
- **MRC sign-off** on repricing the wind, union and intersection legs.

### 3.4 The change, once decided

```python
# config/frequency/_schema.py
DECOUPLED_WIND_CATCHMENTS: frozenset = frozenset({"halong"})  # example
```

---

## 4. Recommendation

Neither flip should be made on engineering judgement alone.

- **Decision A (trend)** is the more tractable: the reprice is quantified (§2.2),
  bounded, and needs only a defensible growth value and MRC sign-off. Recommend
  the MRC treat §2.2 as the impact assessment and decide against a real climate
  signal.
- **Decision B (decoupled wind)** should wait on a port run to produce §3.2's
  book-level evidence before it reaches the MRC. Recommend commissioning that
  port run next.

Both are reversible one-line config changes, fully behaviour-preserving until
made. The engineering work is complete; what remains is data and governance.

---

## 5. References

- Plan: `docs/storm_freq/frequency_layer_definition_and_plan_v2.md` (v2.14, §6h/6i/6j).
- Governance record: MKM-EF-001 **v1.1.0** in the ModelRisk inventory — the two
  reprices and their assumptions are recorded there as limitations.
- Harness: `models.frequency.sensitivity.trend_sensitivity`;
  `port.src.property.hc.pricing._sensitivity.wind_decoupling_sensitivity`.
- The λ circularity that makes both rates unvalidated on synthetic catchments:
  plan §5.
