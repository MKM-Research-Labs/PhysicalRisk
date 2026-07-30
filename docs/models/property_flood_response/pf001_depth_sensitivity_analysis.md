# MKM-PF-001 — Depth Sensitivity Analysis

**Component:** Property Flood Response — `MKM-PF-001`
**Scope:** How the priced damage ratio responds to error in the model's single
most material uncertain input — the estimated flood **depth** at a property —
across both the intensive margin (given a flood, how much) and the extensive
margin (whether the property floods at all).
**Date:** 2026-07-30. **Method:** closed-form, data-free; composes the model's
own calibrated depth-damage curve (`config.damage.DD_POLY_COEFFS`) via
`models.floodrisk.sensitivity`.

---

## 1. Why depth is the material input

Everything the model prices flows from the effective depth
`d = max(0, depth - floor_level - stilt)` through the depth-damage curve
`g(d) = sum_i c_i * d^i`. The depth itself is the least certain quantity in that
chain: the water-surface elevation is interpolated from a sparse gauge network by
inverse-distance weighting (IDW) and then differenced against a DEM ground level,
so **both an interpolation bias and a DEM error land directly on `d`**. The curve
coefficients are calibrated and comparatively stable; the depth is not. This
analysis therefore holds the curve fixed and perturbs the depth.

## 2. Intensive margin — depth error is attenuated

Given that a property floods, the damage ratio is a **concave, saturating**
function of depth, so its elasticity `E(d) = d*g'(d)/g(d)` is below one
everywhere and falls as water deepens:

| depth d (m) | 0.1 | 0.5 | 1.0 | 2.0 | 4.0 |
|---|---|---|---|---|---|
| elasticity E(d) | 0.96 | 0.79 | 0.64 | 0.52 | 0.49 |

A representative 1.0 m flood sits at a 40.2% damage ratio. Propagating a
plus/minus 40% depth band through the curve gives:

| percentile | depth (m) | damage | rel. to median | passthrough |
|---|---|---|---|---|
| p05 | 0.60 | 0.281 | 0.70 | 0.75 |
| p50 | 1.00 | 0.402 | 1.00 | — |
| p95 | 1.40 | 0.492 | 1.22 | 0.56 |

A 40% depth error becomes roughly a -30% / +22% damage error — **damped, not
amplified**. Intensive-margin loss is robust to modest depth error, and the
robustness improves in deep water where the curve flattens toward total loss.

## 3. Extensive margin — incidence is the real exposure

The attenuation above assumes the property floods. Whether it floods is governed
by the same depth against the floor+BRI threshold, and there the response is a
**step**. Take a property whose water stands 0.15 m over its threshold (damage
0.085):

| depth bias (m) | effective depth | floods? | damage |
|---|---|---|---|
| -0.30 | -0.15 | no | 0.000 |
| -0.15 |  0.00 | no | 0.000 |
|  0.00 | +0.15 | yes | 0.085 |
| +0.15 | +0.30 | yes | 0.159 |

A -0.15 m depth bias — well inside DEM/IDW error — moves this property from a
positive damage ratio to **zero**. Aggregated over a portfolio, a small
*systematic* depth bias therefore swings the **flooded count**, not just each
property's severity. This is exactly the documented inverse-distance dilution
failure mode, in which IDW smoothing pushed most properties just below threshold
and left 178 of 200 unflooded. The marginal damage per metre `g'(d)` is largest
at the toe (0.55/m near the threshold vs 0.20/m at 1.4 m), which is why the
incidence margin dominates the model's loss uncertainty.

## 4. What this does and does not establish

The elasticities and the incidence step are exact properties of the calibrated
curve — they are reproducible and not a Monte-Carlo estimate. What they do **not**
establish is the accuracy of the depth estimate itself: on a synthetic catchment
the interpolation recovers an assumed water surface, so this analysis bounds the
*consequence* of a depth error, not its *size*. Sizing the depth error needs real
gauge and survey data (validation question VQ-005, data quality — outstanding).
The practical implication is a control priority: the model is most exposed at the
flood/no-flood boundary, so validation effort belongs on the interpolation and
DEM at threshold, not on the damage curve's shape.

---

*Reproduce: `models.floodrisk.sensitivity` — `depth_damage_sensitivity`,
`depth_bias_sensitivity`, `damage_distribution`; figures from the calibrated
`DD_POLY_COEFFS` of 2026-07-30.*
