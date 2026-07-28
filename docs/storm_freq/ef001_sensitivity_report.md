# MKM-EF-001 — Sensitivity Report (Poisson storm-arrival model)

**Component:** Event Frequency Model — `MKM-EF-001` (governance record v1.1.0)
**Purpose:** Demonstrate and log the model's sensitivity to the Poisson storm-
arrival assumption on which every PRS spread rests — the evidence for "we
understand where this model is sensitive, and by how much" (SR 11-7).
**Catchment:** halong · **λ = 4.5 events/yr** (config seed)
**Date:** 2026-07-28
**Reproduce:** `models.frequency.rate_sensitivity` / `distributional_sensitivity`
(unit-tested; this report logs their output at representative operating points).

---

## 0. The pricing identity, and why this matters

A PRS severe-trigger spread is

```
spread = P(at least one qualifying flood in a year) = 1 − exp(−λ · p)
```

where **λ** is the Poisson arrival rate of storm *events* and **p** is the
per-event conditional exceedance. λ is therefore a linear multiplier on the
hazard, and the sensitivity of the price to the Poisson model splits into three
measurable parts — the **rate** λ, the **distributional form** (Poisson vs its
over-dispersed alternative), and the **sampling** of the Monte Carlo — plus one
part that cannot be measured on synthetic data: the **level** of λ.

---

## 1. Sensitivity to the rate λ — dominant, and near-linear

Because `λ·p ≪ 1` at realistic conditionals, `1 − exp(−λp) ≈ λp`, so the spread
tracks λ **almost one-for-one**. Logged across representative spreads spanning
the halong book (each row is the spread in bps after the λ shock, with the
relative change):

| base spread | p | ∂spread/∂λ | λ×50% | λ×80% | λ×100% | λ×120% | λ×150% |
|---|---|---|---|---|---|---|---|
| 100 bp | 0.00223 | 22.1 bp | 50 (−50%) | 80 (−20%) | 100 | 120 (+20%) | 150 (+50%) |
| 200 bp | 0.00449 | 44.0 bp | 101 (−50%) | 160 (−20%) | 200 | 240 (+20%) | 298 (+49%) |
| 300 bp | 0.00677 | 65.7 bp | 151 (−50%) | 241 (−20%) | 300 | 359 (+20%) | 447 (+49%) |
| 500 bp | 0.01140 | 108.3 bp | 253 (−49%) | 402 (−20%) | 500 | 597 (+19%) | 741 (+48%) |

**Finding.** The response is characterised in closed form (∂spread/∂λ =
10⁴·p·exp(−λp)) and is essentially proportional: **an X% error in λ is an X%
error in the spread**, at every point in the book. The rate is where the
model's price risk is concentrated.

---

## 2. Sensitivity to the distributional form (Poisson vs Negative Binomial)

Holding the mean flood count fixed and replacing the Poisson with an
increasingly over-dispersed Negative Binomial (the clustering alternative the
Stage 2 dispersion test guards against). Logged at a 200 bp operating point
(mean count μ = λ·p = 0.0202/yr):

| dispersion α | family | spread | change vs Poisson |
|---|---|---|---|
| 0.0 | Poisson | 200.0 bp | — |
| 0.5 | NegBin | 199.0 bp | −0.5% |
| 1.0 | NegBin | 198.0 bp | −1.0% |
| 2.0 | NegBin | 196.1 bp | −1.9% |

**Finding.** At the rare-flood mean counts realistic here, the *occurrence*
probability is governed by the mean, not the tail shape, so switching to a
strongly clustered NegBin moves the spread by **under 2%**. The Poisson
*assumption itself* is a second-order sensitivity; the rate (§1) dominates it by
an order of magnitude. Over-dispersion lowers the spread (it puts more mass at
zero), so a mistaken Poisson choice is mildly *conservative*, not aggressive.

**The assumption is tested, not assumed.** Stage 2 runs a per-gauge chi-square
dispersion test and selects NegBin where counts are significantly over-dispersed.
On halong the counts came back **under-dispersed** (a declustering artefact, not
a physical regularity), which no family on the Poisson–NegBin axis can represent
below the Poisson variance floor; it is flagged and Poisson is selected as the
nearest fittable family. So the halong book sits on the side of the axis where
the distributional-form sensitivity in the table above is an *upper bound* on the
error, and the realised form is Poisson by construction.

---

## 3. Sensitivity to sampling — the Monte Carlo is provably the Poisson

The year simulation is reconciled against its exact closed form `1 − exp(−λp)` on
every run: the gap is measured in sampling standard errors (`√(p(1−p)/n)`) and
gated at 4σ. The statistic is verified to be a true z-score — mean `|z|` measures
0.81 at ten thousand years against the theoretical `√(2/π)=0.798` — so the
sampler faithfully *is* the Poisson process, with a quantified sampling error of
~1.6% of the annual probability at the default 10,000 simulated years (falling as
`1/√n`). This is a self-test on the numerics, independent of whether λ is right.

*(See `models.frequency.ylt._reconcile`; plan §4.10.)*

---

## 4. The residual — the *level* of λ is unvalidated

§1–§3 characterise how the price **responds** to the arrival model. What they
cannot establish on a synthetic catchment is that **λ = 4.5 is the right level**:
the gauge record is generated *from* an assumed frequency, and the per-gauge
peaks-over-threshold arm recovers whatever rate its threshold search targets, so
both validation routes are circular (plan §5). Sensitivity is not validation.

Because §1 shows the spread tracks λ one-for-one, **the level of λ is the single
largest model risk**, and it is recorded as the top limitation on the v1.1.0
governance record. The gating control is calibration against a threshold anchored
*outside* the rate — bankfull discharge or a published flood-frequency curve —
which requires **real gauge data**.

---

## 5. Conclusion

| Sensitivity | Magnitude | Status |
|---|---|---|
| **Rate λ** | ~1:1 (near-proportional) | Characterised in closed form + fanned across the book (§1) |
| **Distributional form** | < 2% at realistic means | Bounded, and empirically tested per gauge (§2) |
| **Sampling** | ~1.6% @ 10k yrs, `1/√n` | Proven by the reconciliation gate (§3) |
| **Level of λ** | one-for-one on price | **Unvalidated** on synthetic data; needs real gauge data (§4) |

The model's sensitivity to the Poisson storm-arrival assumption is understood and
concentrated: it lives almost entirely in the **rate**, is near-linear, and the
distributional form and sampling are demonstrably second-order. The open item is
not understanding the sensitivity — it is validating the *level* of λ, which is a
data question, not a modelling one.

---

## References

- Pricing / annualisation: `models.frequency.annualise`; plan §4.
- Family selection & dispersion test: `models.frequency.families`; plan §5.2.
- Reconciliation gate: `models.frequency.ylt._reconcile`; plan §4.10.
- λ circularity: plan §5. Governance limitations: MKM-EF-001 v1.1.0 (ModelRisk).
- Sensitivity functions (this report's engine): `models.frequency.sensitivity`
  (`rate_sensitivity`, `distributional_sensitivity`, `trend_sensitivity`).
