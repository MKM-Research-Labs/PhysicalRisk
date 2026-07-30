# MKM-TC-001 — Wind-Field Sensitivity Analysis

**Component:** Tropical Cyclone Progression and Wind-Field — `MKM-TC-001`
**Scope:** How a property's priced **peak wind** responds to the two materially
uncertain drivers the model produces — storm **intensity** `V_max` and **track
offset** (the eye's closest approach) — evaluated over the model's own parametric
radial profile.
**Date:** 2026-07-30. **Method:** closed-form, data-free; composes
`calibrate_outer_decay_length` and `symmetric_profile` (default `WindFieldParams`)
via `models.typhoon.wind_field.sensitivity`.

Anchor storm: `V_max = 50 m/s`, `R_max = 30 km`, `R_outer = 250 km`,
gale anchor `v_outer_ref = 17.5 m/s`, `alpha_eye = 0.4`, `p = 1.5`
(outer-decay length calibrates to `L = 213 km`).

---

## 1. The two material inputs

The symmetric profile is a linear eyewall ramp inside `R_max` and a stretched-
exponential decay outside it:

```
inner (r < R_max):  V(r) = V_max * [ alpha_eye + (1 - alpha_eye) * r/R_max ]
outer (r >= R_max): V(r) = V_max * exp( -((r - R_max)/L)^p )
L calibrated so V(R_outer) = v_outer_ref (gale)
```

Peak wind at a property therefore depends on the storm's intensity `V_max` and on
where the property sits relative to the eye, `r`. Both are outputs of the Bayesian
particle filter and both carry real uncertainty; storm size (`R_max`, `R_outer`)
is held at the anchor here.

## 2. Intensity — near-proportional passthrough

The whole field scales with `V_max`, but the outer length `L` is re-anchored to
the gale radius as `V_max` moves, so a property in the outer field grows slightly
**sub**-linearly. At an offset of 60 km:

| V_max factor | V_max (m/s) | local wind (m/s) | rel. to base |
|---|---|---|---|
| 0.8 | 40 | 38.4 | 0.81 |
| 1.0 | 50 | 47.4 | 1.00 |
| 1.2 | 60 | 56.4 | 1.19 |

Passthrough to local wind is close to one. The material amplification is
downstream: the wind-damage curve (MKM-WD-001) is a steep sigmoid in gust speed
about a 50%-damage threshold `v_50`, so this near-proportional wind error becomes
a **larger** loss error once it passes through vulnerability. This model's own
output — peak wind — is not where intensity error is magnified.

## 3. Track offset — the dominant geometric uncertainty

The profile is steepest on the eyewall ramp. Local wind climbs from
`alpha_eye * V_max = 20 m/s` at the centre to the full `50 m/s` at `R_max` — a
factor `1/alpha_eye = 2.5` over 30 km — then decays gently once the gale radius is
far out:

| offset r (km) | 15 | 30 | 45 | 60 | 90 | 120 |
|---|---|---|---|---|---|---|
| local wind (m/s) | 35.0 | 50.0 | 49.1 | 47.4 | 43.1 | 38.0 |
| gradient dV/dr (m/s per km) | +1.00 | — | -0.09 | -0.13 | -0.16 | -0.17 |

The eyewall gradient (about **1 m/s per km**) is roughly **six to ten times**
steeper than the outer decay. So whether the eyewall band (`r ~ R_max`) sweeps
over a property, versus passing tens of km inside or outside it, swings its peak
wind far more than a plausible intensity error does.

There is a subtlety the model gets right: peak wind is **not** monotone in
closest approach. Propagating an uncertain offset shows it —

| percentile | offset r (km) | local wind (m/s) | move vs median |
|---|---|---|---|
| p05 | 10 | 30.0 | -19.1 |
| p50 | 45 | 49.1 | — |
| p95 | 90 | 43.1 | -6.0 |

A track passing **right over the eye** (10 km) gives a *lower* wind (30 m/s) than
one clipping the eyewall at 45 km (49 m/s), because the eye is calm. A validation
or exposure read that assumed "closer is always worse" would mis-rank exactly the
near-miss geometries that dominate the tail.

## 4. What this does and does not establish

The winds and gradients are exact readings of the calibrated radial profile at
the stated anchor, not sampled estimates; they bound how peak wind *responds* to
intensity and track error. They do not size those errors — the particle filter's
track and intensity spread is what sets the actual uncertainty, and on synthetic
tracks it is unvalidated (validation questions VQ-005 data quality and VQ-009
independent validation — outstanding). The control implication is that track
placement near `R_max`, not intensity precision, is the highest-value target for
the per-location wind, and that the eye-passage non-monotonicity must be
preserved in any downstream exposure ranking.

---

*Reproduce: `models.typhoon.wind_field.sensitivity` — `intensity_sensitivity`,
`track_offset_sensitivity`, `peak_wind_distribution`; figures from the default
`WindFieldParams` and the stated anchor storm, 2026-07-30.*
