# Flood Propagation Model — Time Dimension Review

**Version:** 2.1
**Date:** 26 March 2026
**Property:** PROP-b77d0d5f (Thames Blackfriars, 51.504°N, -0.109°W)
**Status:** Review for discussion with colleagues

---

## 1. Current Architecture

The flood propagation model operates on a **168-hour (7-day) event window**. Each storm sequence can contain multiple individual storm pulses (isolated: 1 pulse, doublet: 2, cluster: 3-4, persistent: up to 4) spanning the full window.

### Key Files
- `src/models/floodrisk/velocity.py` — Manning's velocity, travel time, retention, hydrograph builder
- `src/port/src/property/ts/flood.py` — Property flood computation, storm-to-property dispatch
- `config/models.py` — Physical constants

### Constants (config/models.py)
| Parameter | Value | Description |
|-----------|-------|-------------|
| `DEFAULT_ROUGHNESS` | 0.04 | Manning's n for urban floodplain |
| `DEFAULT_RETENTION_LENGTH` | 10,000 m | Exponential decay length scale |
| `MIN_SLOPE` | 0.001 | Floor for slope calculation |
| `DEFAULT_RECESSION_FACTOR` | 1.5 | Recession limb stretch factor |
| Near-field threshold | 2,000 m | Below this, retention = 1.0 (v2.1) |

---

## 2. Worked Example — PROP-b77d0d5f

### Property Details
| Field | Value |
|-------|-------|
| Location | 51.504°N, -0.109°W |
| Elevation | 8.43 m AOD |
| Floor level | 0.36 m |
| **Flood threshold** | **8.79 m AOD** (elevation + floor) |
| Flood zone | Zone 3a |
| Type | Semi-detached (2017) |

### Nearest Gauges
| Gauge | Name | Distance | Elevation | Alert | Warning | Severe |
|-------|------|----------|-----------|-------|---------|--------|
| GAUGE-9fffb377 | Thames Blackfriars Bridge | 636 m | 7.01 m | 4.65 m | 6.20 m | 7.36 m |
| SYNTH-f3c8a8e2 | Synthetic 085522ee-9fffb377 | 639 m | 7.01 m | 4.65 m | 6.20 m | 7.36 m |
| GAUGE-4c57aa15 | Thames Southwark Bridge | 701 m | 6.81 m | 4.74 m | 6.32 m | 7.51 m |

### Flood Statistics (from current data)
| Metric | Value |
|--------|-------|
| Total storm events at gauge | 1,536 |
| Events flooding property | 67 (4.4%) |
| Depth range | 0.04 – 4.74 m |
| Mean flood depth | 1.26 m |
| Retention factor | 0.9383 (all events) |

### Event Comparison
| | Near-miss (unflooded) | Just-flooded | Worst event |
|--|----------------------|--------------|-------------|
| Storm | STORM-c5749396 | STORM-21634bb1 | STORM-a449f1df |
| Interpolated WSE | 8.79 m | 8.83 m | 13.53 m |
| Attenuated WSE | 8.79 m | 8.83 m | 13.53 m |
| Flood depth | 0.0 m | 0.04 m | 4.74 m |
| Damage ratio | 0% | 4.4% | 92.4% |
| Arrival hour | — | 126 | 39 |
| Peak hour | — | 126 | 126 |
| Travel time | 0.0 h | 0.0 h | 0.06 h |

---

## 3. Time Flow — Step by Step

### Step 1: Storm Sequence Generation
Each sequence is assigned a type and contains 1-4 pulses within a 168-hour window:

```
Example cluster sequence (STORM-c823c827):
  Type: cluster (4 storms), Total: 156h, Drainage window: 12h
  Storm 0: t=0h,   dur=39h, precip=101mm
  Storm 1: t=39h,  dur=39h, precip=125mm
  Storm 2: t=78h,  dur=39h, precip=130mm
  Storm 3: t=117h, dur=39h, precip=140mm
```

### Step 2: Gauge Response (stressm)
For each storm pulse, `compute_sequence_gauge_response` calculates a peak water level at each gauge using the spatial correlation model. **Only the peak level is retained per gauge per sequence** — the full temporal shape is not preserved at this stage.

### Step 3: Flood Simulation (gaugets)
Each gauge has a **single base 168-hour hydrograph** in `gaugets/{GAUGE_ID}.json` representing a typical flood event shape. This is generated once and reused for all storms:

```
GAUGE-9fffb377 base simulation:
  Hours: 168 (0-167)
  Base level: 3.89 m
  Peak level: 5.73 m
  Peak hour: 126
```

### Step 4: Property Flood Event (`_build_flood_event`)

1. **Water above gauge**: `water_above_gauge = max(0, peak_WSE - gauge_elevation)`
2. **Apply retention**: `water_at_property = water_above_gauge * retention_factor`
   - For this property at 636m: retention = 1.0 (near-field bypass, < 2km)
3. **Flood threshold**: `threshold = (prop_elevation - gauge_elevation) + floor_level`
   - = (8.43 - 7.01) + 0.36 = **1.78 m** above gauge ground
4. **Estimated depth**: `depth = water_at_property - threshold`
5. **Travel time**: Manning's equation → velocity → time
   - v = (1/n) × R^(2/3) × S^(1/2)
   - At 636m, depth 1m, slope 0.002: v ≈ 0.5 m/s → t ≈ 0.35 hours

### Step 5: Property Hydrograph Construction (`build_property_hydrograph`)

The base gauge hydrograph is **time-shifted and scaled** to the property:

```
For each hour h in [0, 167]:
  if h < travel_time:
    wse = base_level (flood hasn't arrived)
  elif h <= peak_hour + travel_time:   (rising limb)
    scale = (gauge_level[h - travel_time] - base) / (gauge_peak - base)
    prop_wse = base + (peak_WSE_at_property - base) × scale
  else:                                 (recession limb)
    stretched_time = peak_hour + (h - shifted_peak) / recession_factor
    prop_wse = scaled gauge level at stretched_time

  depth = max(0, prop_wse - flood_threshold)
```

The recession factor (1.5) stretches the falling limb — water drains 50% slower than it rises. This is physically reasonable for overbank flooding where return flow is impeded.

---

## 4. Identified Gaps

### Gap 1: Multi-Storm Compounding Not Modelled (CRITICAL)

**Current behaviour:** When a sequence contains multiple storm pulses, only the **worst peak level** per gauge is kept. The other pulses are discarded.

**What this misses:**
- **Antecedent saturation**: Storm 1 saturates the ground, so Storm 2's runoff is much higher. A 50mm storm after 100mm of prior rainfall produces far more flooding than 50mm on dry ground.
- **Superposition of flood waves**: If Storm 1's recession overlaps Storm 2's rising limb, water levels compound. The combined peak can exceed either individual peak.
- **Reduced drainage**: In a cluster, the drainage window (12h in the example above) may be insufficient for water to recede before the next pulse arrives.

**Impact:** The current model treats a 4-storm cluster identically to its single worst pulse. For catastrophic cluster events (which represent ~16% of sequences), the model underestimates flood depth and duration.

**Illustration:**
```
Current model (worst-pulse-only):
  Peak depth: ████████░░░░░░░░░░░░  (single pulse peak)

Reality (compound):
  Pulse 1:    ███░░░░░░░░░░░░░░░░░
  Pulse 2:      █████░░░░░░░░░░░░░░  (higher due to saturation)
  Pulse 3:        ████████░░░░░░░░░  (superposition on recession)
  Combined:   ███████████████░░░░░░  (sustained flooding, higher peak)
```

### Gap 2: Single Base Hydrograph Shape

**Current behaviour:** All storms use the same 168-hour base shape from `gaugets/{GAUGE_ID}.json`, just scaled up or down to match the storm's peak level.

**What this misses:**
- Different storm types produce different hydrograph shapes. A flash flood has a sharp peak and rapid recession. A persistent frontal system has a broad, slow peak.
- The peak hour is fixed at hour 126 for all events (from the base simulation).
- Storm duration information (available in the sequence data: 33-52 hours per pulse) is not used to shape the property hydrograph.

**Impact:** All floods at a given property have the same temporal profile, just scaled vertically. This affects:
- Insurance loss modelling (duration of flooding matters for damage)
- Warning time (arrival_time is always relative to hour 126 peak)
- Time-to-peak (not correlated with storm intensity)

### Gap 3: No Infiltration / Ground Loss

**Current behaviour:** Water surface elevation propagates from gauge to property with no volumetric loss. The retention factor is distance-based signal decay, not infiltration.

**What this misses:**
- Permeable soils absorb water, reducing the flood volume reaching the property
- Antecedent moisture conditions affect infiltration capacity
- Urban vs rural land cover affects runoff/infiltration ratio

**Impact:** For properties on permeable soils or with significant green space between them and the river, the model may overestimate flood depth. For near-river properties on impermeable surfaces, this gap is minor.

### Gap 4: No Drainage / Recession Calibration

**Current behaviour:** The recession factor is a fixed 1.5× stretch of the rising limb. No calibration to actual drainage rates.

**What this misses:**
- Properties in basements or low points may have very slow drainage
- Pumped drainage areas have a fundamentally different recession profile
- Tidal influence on drainage (tidal lock preventing outflow at high tide)

---

## 5. Observed Timing Statistics (Current Data)

From 3,727 flooded events across 100 properties:

| Metric | Min | Mean | Max |
|--------|-----|------|-----|
| Travel time | 0.00 h | 0.42 h | 47.14 h |
| Arrival hour | 8 | 105.3 | 167 |
| Peak hour | 88 | 136.8 | 167 |
| Duration (arrival→peak) | 0 h | 31.5 h | 144 h |

**Note:** The 47-hour max travel time is from distant properties — the Manning's velocity at low depths and gentle slopes can produce very slow propagation. 99.8% of events have travel_time > 0 (only 9 events have zero travel time).

---

## 6. Recommended Remediation

### Phase 1 (Immediate — estimation)
**Compound storm scaling factor**: For multi-pulse sequences, apply a compound multiplier to the peak WSE based on antecedent precipitation. Simple formula:

```
compound_factor = 1.0 + 0.1 × log2(num_storms) × (1 - drainage_window / event_window)
```

This gives:
- Isolated (1 storm): factor = 1.0 (no change)
- Doublet with 50% drainage: factor ≈ 1.05
- Cluster (4 storms) with 7% drainage: factor ≈ 1.19

### Phase 2 (Near-term — shape)
**Storm-type-dependent hydrograph templates**: Create 4 base hydrograph shapes (isolated, doublet, cluster, persistent) with different peak positions and recession rates. Select template based on sequence_type.

### Phase 3 (Medium-term — physics)
**Per-pulse hydrograph superposition**: Build the property hydrograph by summing individual pulse contributions, each with its own start time, peak, and recession. Include a saturation curve that reduces infiltration capacity as cumulative precipitation increases.

### Phase 4 (Longer-term — calibration)
**Saint-Venant shallow water equations** for 1D channel routing, coupled with 2D overbank flow. This requires DEM data, channel cross-sections, and significant computational resources but is the physically correct approach.

---

## 7. Summary

The v2.1 model correctly handles:
- Gauge-to-property elevation difference
- Manning's velocity for travel time
- Recession limb stretching
- Near-field retention bypass

The main gap is **temporal compounding** — multi-storm sequences are reduced to their single worst pulse, losing the physical interaction between successive storms that makes compound events so dangerous. The 168-hour window and per-pulse timing data already exist in the storm sequence records; the model simply doesn't use them yet.

For a screening-level PRS pricing model, Phase 1 (compound scaling factor) would address the most material gap with minimal code change.
