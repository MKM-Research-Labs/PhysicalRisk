# MKM-ST-001 — Threshold Sensitivity Analysis

**Component:** Stress Test Pipeline — `MKM-ST-001`
**Scope:** How the pipeline's flood decision responds to error in the per-gauge
**severe-threshold calibration** — the single most material uncertain input to
the `FloodPoly` classifier surrogate that drives every flood label in the stress
catalogue.
**Date:** 2026-07-30. **Method:** closed-form, data-free; composes the calibrated
`FloodPoly` coefficients (`config.models.flood_poly_coeffs`) via
`models.stress.sensitivity`.

---

## 1. Why the severe threshold is the material input

The pipeline labels a flood through `FloodPoly`, a logistic surrogate for the
per-gauge GBM classifier:

```
P(flood) = logistic( a*h + b*t + c*h*t + d*h^2 + e*t^2 + f )
h = ln(w / s)      t = ln((hour + 1) / T)
```

Both features are gauge-independent, and the water level `w` enters **only**
through the log-margin `h = ln(w/s)` against the severe threshold `s`. That
threshold is a per-gauge calibration number, unvalidated on synthetic data, so a
relative error in `s` (or, symmetrically, in the stress water level `w`) shifts
`h` and moves the flood label. This analysis holds the coefficients fixed and
perturbs `s` about a gauge at `w = s = 6.58 m` at the final storm hour.

## 2. The transition band is sharply sensitive

At the severe threshold the surrogate reads `P(flood) = 0.292` (conservative by
design — the offset `f` keeps it below one-half at `w = s`). A plus/minus 5%
error in the threshold moves it enormously:

| percentile | severe s (m) | log-margin h | P(flood) | move vs median |
|---|---|---|---|---|
| p05 | 6.25 (-5%) | +0.051 | 0.631 | +0.34 |
| p50 | 6.58 | 0.000 | 0.292 | — |
| p95 | 6.91 (+5%) | -0.049 | 0.087 | -0.21 |

A 5% calibration error swings the flood probability across a **0.09–0.63** range
— tens of percentage points — from one gauge's threshold alone. The local slope
`dP/dh` peaks near six around `w = s`: a one-percent error in threshold or water
level is worth roughly six-tenths of a percentage point of flood probability at
its steepest.

## 3. The tails are robust

Away from the threshold the logistic saturates and the response collapses. At
`w/s = 1.35` (water 35% over threshold) `P(flood) = 0.997` and the slope falls to
`0.05` — a 5% calibration error is then worth a fraction of a percentage point.
Well-separated events — clearly safe or clearly flooded — are effectively immune
to threshold error; the model's own card records the same shape, over-predicting
in the alert-to-severe transition and under-predicting at the tails.

## 4. Implication for the catalogue

Because the entire stress catalogue is labelled through this one surrogate, its
fragility is concentrated exactly where events cluster near the severe threshold
— the alert-to-severe band the pipeline exists to probe. A systematic
mis-calibration of `s` across gauges would bias the **count** of stressed floods,
not merely individual probabilities, and would do so hardest for the marginal
events that matter most.

## 5. What this does and does not establish

The probabilities and slopes are exact readings of the calibrated surrogate, not
sampled estimates. They bound the *consequence* of a threshold error; they do not
size the error. On synthetic gauges the severe threshold is an assumed input, so
its realism is unvalidated (validation questions VQ-005 data quality and VQ-002
accuracy — outstanding). The control implication is direct: threshold calibration
is the highest-value validation target for the pipeline, and it matters most for
gauges whose stressed water levels sit near their severe marks.

---

*Reproduce: `models.stress.sensitivity` — `threshold_sensitivity`,
`flood_probability_distribution`; figures from the calibrated `FloodPoly`
coefficients of 2026-07-30.*
