# MKM-EF-001 — λ Sensitivity Analysis (one-off)

**Component:** Event Frequency Model — `MKM-EF-001` (governance record v1.1.0)
**Purpose:** A dedicated study of the model's sensitivity to the Poisson arrival
rate **λ** — its single core uncertainty — propagating a plausible λ band both
deterministically and probabilistically through to the priced PRS spread.
**Catchment / book:** halong · 200 properties (188 with flood exposure) · seed
**λ = 4.5 events/yr**.
**Date:** 2026-07-28 · **Reproduce:** `models.frequency.rate_sensitivity`,
`lambda_price_distribution` over the halong `propertyhc` conditionals.

---

## 1. Why λ is the analysis that matters

A PRS severe-trigger spread is `1 − exp(−λ·p)`, so λ is a **linear multiplier**
on the annual hazard. The prior sensitivity report established that the spread
tracks λ almost one-for-one and that the distributional form and Monte-Carlo
sampling are second-order. What that report also established is the open item:
**λ's *level* is unvalidated on a synthetic catchment** — the gauge record is
generated from an assumed frequency and the per-gauge extraction recovers its own
target, so both validation routes are circular (plan §5).

λ therefore carries genuine uncertainty, and because it is a linear multiplier
that uncertainty flows straight into every quoted spread. This study quantifies
exactly how much, on the real book, over a **±50% plausible band on λ**
(2.25–6.75 /yr).

---

## 2. Deterministic transmission — the ±50% fan on the real book

Applying each λ shock to every property's fitted per-event conditional and
re-pricing `1 − exp(−λ·p)`, then averaging across the 200-property book (base
average **198.3 bps**, matching the port):

| λ shock | λ (/yr) | book avg spread | change |
|---|---|---|---|
| ×50% | 2.25 | 99.9 bp | −49.6% |
| ×80% | 3.60 | 159.1 bp | −19.7% |
| **×100%** | **4.50** | **198.3 bp** | — |
| ×120% | 5.40 | 237.1 bp | +19.6% |
| ×150% | 6.75 | 295.0 bp | +48.8% |

The response is **near-proportional**: a given percentage error in λ moves the
book's average spread by essentially the same percentage. The closed-form reason
is that `λ·p << 1` at realistic conditionals, so `1 − exp(−λp) ≈ λp` and the
derivative `∂spread/∂λ = p·exp(−λp)` is almost constant across the band.

---

## 3. Probabilistic propagation — λ's uncertainty becomes price uncertainty

Treating λ as uncertain with the ±50% band as the 5th–95th percentiles of its
prior (P5 = 2.25, P50 = 4.5, P95 = 6.75) and propagating through the monotonic
map `spread(λ)` — exactly, since a percentile of λ maps to the same percentile of
the spread:

**Book average spread**

| | P5 | P50 | P95 |
|---|---|---|---|
| λ (/yr) | 2.25 | 4.50 | 6.75 |
| book avg spread | 99.9 bp | 198.3 bp | 295.0 bp |
| vs median | −50% | — | +49% |

**Induced 90% credible interval on the book's average spread: [−50%, +49%].**
The **passthrough** — the ratio of the spread's relative span to λ's — is
**0.984** at book level (0.991 for a representative median-conditional property).

The interpretation is direct and important: **a ±50% uncertainty on λ is a ±50%
uncertainty on the entire book's PRS valuation.** The price carries the same
relative model-uncertainty band as the rate, because in this regime it *is* the
rate. There is no diversification of this uncertainty across the book — λ is a
catchment-wide multiplier, so it shifts every asset together.

---

## 4. Where the one-for-one relation weakens

Passthrough is below 1 only through the convexity of `1 − exp(−λp)`: as `λ·p`
grows the curve bends and the upside is compressed relative to the downside. On
this book the effect is small (passthrough 0.98) because conditionals are low
(median p ≈ 0.004, so `λp ≈ 0.02`). It would matter only for a gauge/asset with a
much higher conditional — a near-certain-flood location — where the spread
saturates towards 1 and further λ has diminishing effect. No such asset is
material in the halong book. So across the realistic range the one-for-one
approximation is safe to reason with.

---

## 5. Conclusion and implication for validation

| Finding | Value |
|---|---|
| Book base average spread | 198.3 bp (λ = 4.5) |
| Book avg spread under ±50% λ | 99.9 – 295.0 bp |
| Induced 90% CI on the book | **[−50%, +49%]** |
| λ-to-price passthrough | **0.98 (≈ one-for-one)** |
| Diversifiable across the book? | No — λ is a catchment-wide multiplier |

The model's exposure to the Poisson rate is now fully characterised: **the PRS
book inherits λ's uncertainty essentially one-for-one and undiversified.** A
±50% band on λ — entirely plausible for an unvalidated rate — is a ±50% band on
the book's PRS valuation.

This makes the **validation of λ's level the single highest-value control on the
model**, worth more than any refinement of the conditional, the distributional
family, or the sampling. Validation requires a threshold anchored *outside* the
rate — bankfull discharge or a published flood-frequency curve — and therefore
**real gauge data**; it cannot be done on the synthetic catchment (plan §5).
Until then, every PRS quote should be understood to carry a model-uncertainty
band from λ alone of roughly the same width as the assumed uncertainty on λ.

---

## References

- Pricing identity & annualisation: `models.frequency.annualise`; plan §4.
- λ sensitivity engine: `models.frequency.sensitivity`
  (`rate_sensitivity`, `lambda_price_distribution`).
- λ circularity / why the level is unvalidated: plan §5.
- Prior overview: `ef001_sensitivity_report.md`. Governance: MKM-EF-001 v1.1.0.
