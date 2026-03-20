# Storm Generator v2.0 — Project Plan

**Spec versions reviewed:**
- Storm Generator Specification v2.0-multi-storm (Mar 5 2026)
- Storm Generator Spatial Correlation Spec v2.0-multi-storm-spatial (Mar 5 2026)

**Last updated:** 2026-03-06 (restructured into subfolders)

---

## Status Summary

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Data structures | DONE |
| 1a | Duration sampler | DONE |
| 1b | Gap sampler | DONE |
| 1c | Intensity sampler | DONE |
| 1d | Sequence generator (core logic) | DONE |
| 1e | Validation | DONE |
| 1f | Unit tests (structures, duration, gap) | DONE |
| 2a | Batch generation + JSON I/O | DONE |
| 2b | End-to-end SequenceGenerator test | DONE |
| 3a | Antecedent conditions model (hydrology) | DONE |
| 3b | Sequence gauge response (compounding) | DONE |
| 3c | Integration tests | DONE |
| 4a | Spatial correlation module | DONE |
| 4b | Spatial gauge response integration | DONE |
| 4c | spatial_correlation.json config | DONE |
| 5 | app.py / pipeline integration | TODO |
| 6 | Historical validation | TODO |

---

## Package Structure

```
storm_multi/
├── __init__.py                            exports all public v2 symbols
├── core/
│   ├── __init__.py
│   └── data_structures.py                 SequenceStorm, StormSequence, enums, ID helpers
├── generators/
│   ├── __init__.py
│   ├── duration_sampler.py                triangular duration per category
│   ├── gap_sampler.py                     SHORT/MEDIUM/LONG gap types
│   ├── intensity_sampler.py               sequence probability + correlated intensities
│   ├── sequence_generator.py              SequenceGenerator class
│   └── batch_generator.py                 [Phase 2 TODO]
├── models/
│   ├── __init__.py                        placeholder
│   ├── hydrology.py                       [Phase 3 TODO]
│   ├── sequence_response.py               [Phase 3 TODO]
│   └── spatial_correlation.py             [Phase 4 TODO]
├── utils/
│   ├── __init__.py
│   ├── validation.py                      validate_sequence(), fits_in_window()
│   └── serialization.py                   [Phase 2 TODO]
└── docs/
    ├── PROJECT_PLAN.md
    ├── Storm Generator Specification.pdf
    └── Storm Generator Spatial Correlation Spec.pdf
```

---

## Phase 1 — DONE: Core Sequence Generation

| File | Description |
|------|-------------|
| `core/data_structures.py` | SequenceStorm, StormSequence, SequenceType (isolated/doublet/cluster/persistent), GapType |
| `generators/duration_sampler.py` | Triangular distribution, 6 categories, catastrophic up to 240h |
| `generators/gap_sampler.py` | SHORT(6-36h) / MEDIUM(24-72h) / LONG(48-144h) |
| `generators/intensity_sampler.py` | SEQUENCE_PROBABILITY, SEQUENCE_TYPE_WEIGHTS, correlated intensities |
| `generators/sequence_generator.py` | SequenceGenerator.generate(), retry logic, fallback to isolated |
| `utils/validation.py` | validate_sequence(), fits_in_window(), EVENT_WINDOW=168, MAX_PRECIP_END=156 |

Tests: `tests/port/test_storm_sequence.py`, `test_storm_duration.py`, `test_storm_gap.py` — 61 tests, all passing.

**Minor gap vs spec:** StormSequence uses `total_duration_hours` rather than a `sequence_end` field.
Functionally equivalent; `sequence_end = total_duration_hours` from hour 0. Can add field if needed.

---

## Phase 2 — TODO: Batch Generation + File I/O

### `generators/batch_generator.py` (NEW)

```python
def generate_event_set(
    count: int = 10000,
    catchment_id: str = "thames",
    intensity_weights: dict = None,
    # default: {moderate: 0.40, severe: 0.35, extreme: 0.20, catastrophic: 0.05}
    force_sequence_type: str = None,
    seed: int = 42,
) -> List[StormSequence]:
    """Generate N sequences across all intensity categories."""
```

### `utils/serialization.py` (NEW)

```python
def save_sequences(sequences: List[StormSequence], path: Path) -> None:
    """Save to storm_sequences.json (schema version 2.0-multi-storm)."""

def load_sequences(path: Path) -> List[StormSequence]:
    """Load and reconstruct StormSequence objects from JSON."""

def save_summary(sequences: List[StormSequence], path: Path) -> None:
    """Save sequences_summary.json — metadata only, ~200 KB."""
```

Output files (spec Section 7.3):
- `data/input/thames/storm_sequences.json` — ~10-12 MB
- `data/input/thames/sequences_summary.json` — ~200 KB

### `tests/port/test_sequence_generator.py` (NEW)

- End-to-end `SequenceGenerator.generate()` for all intensity categories
- Batch generation: verify sequence type distribution matches SEQUENCE_PROBABILITY weights
- All generated sequences pass `validate_sequence()` with no errors
- Timing constraint: all sequences have final storm end <= hour 156
- Serialization round-trip (save → load → equality check)

---

## Phase 3 — TODO: Antecedent Conditions + Compounding Gauge Response

This is the most complex phase. The existing `StormGaugeModel` (`src/models/stormgauge/forward_model.py`)
processes independent storms. Sequences require a continuous 168-hour compound response.

### Spec Section 5 requirements:

- Continuous 168-hour hydrograph for the full sequence
- River level partially drains during gap (does NOT return to baseline)
- Storm 2 rises from elevated baseline → higher peak than Storm 1 of equal intensity
- Final recession during drainage window (hours 156-168)
- **Validation criterion:** Storm 2 peak > Storm 1 peak in >= 60% of sequences

### `models/hydrology.py` (NEW — lives in storm_multi/models/)

Simplified state model (spec Section 5.3):

```
soil_moisture[h] = soil_moisture[h-1] * (1 - drainage_coeff) + precip[h] * infiltration_coeff
groundwater[h]   = groundwater[h-1] * (1 - baseflow_coeff) + soil_moisture[h] * percolation_coeff
quickflow[h]     = precip[h] * (1-infiltration_coeff) + alpha * soil_moisture[h] + beta * groundwater[h]
```

Initial parameter values:
- `infiltration_coeff`: 0.6-0.8
- `drainage_coeff`: 0.01-0.05 per hour
- `baseflow_coeff`: 0.005-0.02 per hour

### `models/sequence_response.py` (NEW — lives in storm_multi/models/)

```python
def compute_sequence_gauge_response(
    sequence: StormSequence,
    gauge_id: str,
    gauge_params: dict,
) -> np.ndarray:
    """
    Returns array[168] of hourly river levels for full event window.
    Captures compounding: Storm 2 peak > Storm 1 peak due to antecedent wetness.
    """
```

For each hour 0-167:
1. Determine precipitation at this hour (which storm, if any, is active)
2. Update soil moisture + groundwater state
3. Compute quickflow/runoff
4. Route quickflow to river level via hydraulic kernel (reuse existing StormGaugeModel kernel)
5. Record level

Output: `data/input/thames/gauge_responses.json` — ~20-30 MB

### `tests/port/test_sequence_gauge_response.py` (NEW)

- Storm 2 peak > Storm 1 peak in >= 60% of generated doublets
- Observable drainage during gap (level drops but does not return to baseline)
- Hours 156-168 are precipitation-free (drainage window intact)
- No negative river levels
- Baseline level is recovered (approximately) by hour 168

---

## Phase 4 — TODO: Spatial Correlation

Spatially correlated precipitation across 40 Thames gauges using exponential correlation kernel
(spec: Storm Generator Spatial Correlation Spec, Section 5).

### `models/spatial_correlation.py` (NEW — lives in storm_multi/models/)

Algorithm:
1. Build 40x40 distance matrix from `catchments/thames.GAUGE_POINTS` (Haversine) — once at module load
2. Build correlation matrix: `C[i,j] = exp(-d[i,j] / range_km) + nugget * I[i==j]`
3. Intensity-conditioned range: `range_km = base_range * (1 + rho_intensity * (intensity - 1))`
4. Cholesky decomposition: `L` such that `L @ L.T = C`
5. Per active precipitation hour:
   - Sample correlated Gaussians: `z = L @ N(0,1)`
   - Transform to lognormal multipliers: `M = exp(sigma * z - sigma^2/2)`
   - Normalise to preserve catchment mean: `M_norm = M / mean(M)`
   - Gauge precipitation: `precip_gauge[i] = catchment_precip * M_norm[i]`

Default parameters (Thames-calibrated, spec Table 2):
- `base_range_km`: 40.0 (half of Thames corridor length)
- `nugget`: 0.05 (5% micro-scale variability)
- `rho_intensity`: 0.4 (40% range increase for extreme events)
- `sigma_lognormal`: 0.4 (40% spatial CV)

Effective range by intensity:
- Moderate: ~40 km
- Severe: ~43 km
- Extreme: ~48 km

Performance: pre-compute distance matrix; cache Cholesky factors for identical parameters.
Expected: <0.01s per sequence, <2 min for 10K.

### Config: `data/input/thames/spatial_correlation.json` (NEW)

```json
{
  "spatial_correlation": {
    "enabled": true,
    "model_type": "exponential",
    "base_range_km": 40.0,
    "nugget": 0.05,
    "rho_intensity": 0.4,
    "sigma_lognormal": 0.4,
    "num_gauges": 40
  }
}
```

### Updated output: `gauge_responses_spatial.json`

Schema version: 2.1-spatial. Per-gauge hourly precipitation + river levels.
File size: ~1 GB uncompressed, ~300 MB gzip (acceptable for distribution).

### `tests/port/test_spatial_correlation.py` (NEW)

- Distance matrix: symmetric, diagonal = 0, values plausible (~65 km max along Thames corridor)
- Correlation matrix: positive definite, diagonal = 1, off-diagonal in (0, 1)
- Cholesky: `L @ L.T ≈ C` within numerical tolerance
- Lognormal multipliers: mean(M) ≈ 1 before normalisation
- Catchment mean preserved after normalisation
- Higher intensity sequences → stronger spatial coherence (shorter effective correlation length)

---

## Phase 5 — TODO: Pipeline Integration

1. Add `--sequences` step to `app.py port` (alongside existing `--storms`)
2. Wire `batch_generator.generate_event_set()` into port pipeline
3. Add `--gauge-response-sequences` step for compound gauge responses
4. Schema version metadata in all output files
5. `convert_v1_to_v2()` backward compat migration function (spec Section 9.3)

---

## Phase 6 — TODO: Historical Validation

Validate against (spec Section 8.3):
- Winter 2013/14 Thames floods (multi-storm over weeks)
- Storm Henk 2024 (single major event — comparison baseline)
- 2000 autumn floods (multi-storm sequence)
- 2003 summer convective sequences

Validation criteria:
- Storm durations within ±30% of historical mean
- Gap durations within ±30% of historical mean
- Peak 2 / Peak 1 ratios within 90% CI
- Total precipitation within ±20% of historical events
- Storm 2 peak > Storm 1 peak in >= 60% of generated doublets
- KS test p > 0.05 for duration and gap distributions
- Historical 1-in-100 year doublet events fall within synthetic 50-200 year range

---

## Key Parameter Reference

| Parameter | Value | Source |
|-----------|-------|--------|
| Event window | 168h | Insurance hours clause |
| Max precip end | 156h | 168 - 12h drainage |
| Min drainage window | 12h | Spec Section 3.4 |
| Target sequences | 10,000 | Spec Section 1.2 |
| Intensity weights | mod 40%, sev 35%, ext 20%, cat 5% | Spec Section 4.3 |
| Sequence probability (severe) | 50% | `intensity_sampler.py` |
| Sequence probability (extreme) | 70% | `intensity_sampler.py` |
| Type weights (severe) | doublet 30%, cluster 50%, persistent 20% | `intensity_sampler.py` |
| Intensity variation | ±20% | `intensity_sampler.py` |
| First storm dominant prob | 30% | `intensity_sampler.py` |
| Subsequent storms >= first | 70% | `intensity_sampler.py` |
| Performance target | <2 min for 10K | Spec Section 8.4 |
| File size target (pre-spatial) | <50 MB | Spec Section 1.2 |
| File size target (spatial, gzip) | ~300 MB | Spec Section 5.11 |
| Spatial range (Thames) | 40 km base | Spec Table 2 |
| Spatial nugget | 0.05 | Spec Table 2 |

---

## Files Reference

| File | Status | Description |
|------|--------|-------------|
| `core/data_structures.py` | DONE | Core dataclasses |
| `generators/duration_sampler.py` | DONE | Triangular duration sampling |
| `generators/gap_sampler.py` | DONE | Inter-storm gap sampling |
| `generators/intensity_sampler.py` | DONE | Intensity correlation |
| `generators/sequence_generator.py` | DONE | SequenceGenerator class |
| `utils/validation.py` | DONE | Sequence validation |
| `generators/batch_generator.py` | DONE Phase 2 | Batch event set generation |
| `utils/serialization.py` | DONE Phase 2 | JSON save/load |
| `models/hydrology.py` | DONE Phase 3 | Soil moisture / groundwater state |
| `models/sequence_response.py` | DONE Phase 3 | 168h compound gauge response |
| `models/spatial_correlation.py` | DONE Phase 4 | Spatial field generation |
| `data/input/thames/spatial_correlation.json` | DONE Phase 4 | Spatial config |
| `tests/port/storm/batch_generator.py` | DONE Phase 2 | E2E generator + batch + serialization tests (70 tests) |
| `tests/port/test_sequence_gauge_response.py` | TODO Phase 3 | Compounding response tests |
| `tests/port/test_spatial_correlation.py` | TODO Phase 4 | Spatial correlation tests |

---

## Future Enhancements (out of scope for now)

Per spec Section 11.5:
- Full state-space antecedent conditions model (Extended Kalman Filter / Particle Filter)
- Duration-intensity copula (Gaussian copula with negative correlation)
- Tidal signal injection (M2/S2 sinusoids scaled by estuary distance)
- Bayesian parameter uncertainty quantification
- Anisotropic spatial correlation model
- Extension to cluster (3-4 storms) and persistent (4-5 storms) sequences as primary focus
