# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Halong / Hanoi tropical-cyclone (typhoon) calibration.

Catchment-specific constants for the typhoon model in
``src/models/typhoon/``. The model is catchment-agnostic; concrete values
live here. The catchment depends on the model's parameter dataclass API,
never the other way around.

All values are first-pass placeholders calibrated against rough South
China Sea climatology. A future phase will recalibrate against JMA RSMC
Tokyo best-track data.

Exposed constants:
- HALONG_TYPHOON_GENESIS_PRIOR    — initial state distribution
- HALONG_TYPHOON_PEAK_WIND        — per-scenario-family peak-wind params
- HALONG_TYPHOON_MOTION           — regime-conditioned motion params
- HALONG_TYPHOON_INTENSITY        — wind intensity transition
- HALONG_TYPHOON_SIZE             — storm-size transition
- HALONG_TYPHOON_WIND_FIELD       — parametric wind-field params
- HALONG_TYPHOON_PLAUSIBILITY     — soft-constraint weights
- halong_land_mask                — callable (lon, lat) -> True if land
- HALONG_HANOI_REFERENCE          — Hanoi centre (lon, lat)
- HALONG_TYPHOON_PROPERTIES       — Phase 1 placeholder property points
"""

from config.typhoon import (
    CatchmentTyphoonConfig,
    GenesisPrior,
    IntensityParams,
    MotionParams,
    PeakWindParams,
    PlausibilityWeights,
    PropertyPoint,
    RegimeClass,
    ScenarioFamily,
    SizeParams,
    WindFieldParams,
)


# ---------------------------------------------------------------------------
# Genesis prior — Gulf of Tonkin / SCS typhoon formation zone
# ---------------------------------------------------------------------------
# bbox covers the typical genesis region for storms making landfall in
# northern Vietnam (Halong / Hai Phong / Red River delta).

HALONG_TYPHOON_GENESIS_PRIOR: GenesisPrior = GenesisPrior(
    bbox=(112.0, 14.0, 118.0, 20.0),   # (lon_min, lat_min, lon_max, lat_max)
    heading_mean_deg=280.0,            # westward with mild north bias
    heading_kappa=8.0,                 # moderately concentrated
    speed_shape=4.0,                   # Gamma(4, 4) ~= mean 16 km/h
    speed_scale=4.0,
    regime_weights={
        RegimeClass.STRAIGHT_WESTWARD: 0.45,
        RegimeClass.NW_RECURVER:       0.15,
        RegimeClass.SHARP_RECURVE:     0.05,
        RegimeClass.STALLED:           0.05,
        RegimeClass.LANDFALL_DECAY:    0.30,
    },
    scenario_mix={
        ScenarioFamily.HISTORICAL: 0.20,
        ScenarioFamily.BASELINE:   0.30,
        ScenarioFamily.MODERATE:   0.25,
        ScenarioFamily.SEVERE:     0.15,
        ScenarioFamily.EXTREME:    0.10,
    },
)


# ---------------------------------------------------------------------------
# Peak-wind distribution — hybrid truncated-normal + Pareto tail
# ---------------------------------------------------------------------------
# Spec eq. 14. EXTREME has lower alpha (fatter tail) than BASELINE.

# NOTE (2026-06-04): genesis intensity strengthened for the wind-PRS demo so
# the asset-level peak wind clears the commercial damage-onset bar (Minor =
# 55.6 m/s). Previous families topped at mu_ms=50 and attenuated to ~51 m/s at
# the (clustered) portfolio, so commercial never triggered. Shifted up ~+15 m/s
# with fatter tails (EXTREME eye ~78 m/s, Cat-5). Backup: tc.py.bak-*.
HALONG_TYPHOON_PEAK_WIND: dict = {
    ScenarioFamily.HISTORICAL: PeakWindParams(
        mu_ms=42.0, sigma_ms=12.0, v_threshold_ms=60.0, alpha=3.0,
    ),
    ScenarioFamily.BASELINE: PeakWindParams(
        mu_ms=48.0, sigma_ms=14.0, v_threshold_ms=62.0, alpha=2.5,
    ),
    ScenarioFamily.MODERATE: PeakWindParams(
        mu_ms=55.0, sigma_ms=15.0, v_threshold_ms=68.0, alpha=2.0,
    ),
    ScenarioFamily.SEVERE: PeakWindParams(
        mu_ms=65.0, sigma_ms=17.0, v_threshold_ms=72.0, alpha=1.5,
    ),
    ScenarioFamily.EXTREME: PeakWindParams(
        mu_ms=78.0, sigma_ms=20.0, v_threshold_ms=80.0, alpha=1.2,
    ),
}


# ---------------------------------------------------------------------------
# Motion transition — per-regime climatological speed and heading targets
# ---------------------------------------------------------------------------
# Heading convention: compass degrees, 0=N, 90=E, 180=S, 270=W.

HALONG_TYPHOON_MOTION: MotionParams = MotionParams(
    mean_speed_kmh={
        RegimeClass.STRAIGHT_WESTWARD: 18.0,
        RegimeClass.NW_RECURVER:       16.0,
        RegimeClass.SHARP_RECURVE:     14.0,
        RegimeClass.STALLED:            4.0,
        RegimeClass.LANDFALL_DECAY:    12.0,
    },
    sigma_speed_kmh={
        RegimeClass.STRAIGHT_WESTWARD: 4.0,
        RegimeClass.NW_RECURVER:       4.0,
        RegimeClass.SHARP_RECURVE:     5.0,
        RegimeClass.STALLED:           2.0,
        RegimeClass.LANDFALL_DECAY:    3.0,
    },
    mean_heading_deg={
        RegimeClass.STRAIGHT_WESTWARD: 270.0,    # due west
        RegimeClass.NW_RECURVER:       300.0,    # WNW
        RegimeClass.SHARP_RECURVE:     350.0,    # turning N
        RegimeClass.STALLED:           270.0,
        RegimeClass.LANDFALL_DECAY:    280.0,    # westward over land
    },
    sigma_heading_deg={
        RegimeClass.STRAIGHT_WESTWARD: 15.0,
        RegimeClass.NW_RECURVER:       20.0,
        RegimeClass.SHARP_RECURVE:     25.0,
        RegimeClass.STALLED:           45.0,    # wandering
        RegimeClass.LANDFALL_DECAY:    15.0,
    },
    speed_persistence=0.7,
    heading_persistence=0.7,
    recurvature_latitude=20.0,
    recurvature_bias_deg_per_step=4.0,
)


# ---------------------------------------------------------------------------
# Intensity transition — mild over-water drift, exponential land decay
# ---------------------------------------------------------------------------

HALONG_TYPHOON_INTENSITY: IntensityParams = IntensityParams(
    drift_ms_per_hour=0.0,        # neutral drift in Phase 1
    sigma_ms_per_hour=1.0,
    k_land_per_hour=0.15,         # ~50% wind loss in ~5h over land
)


# ---------------------------------------------------------------------------
# Size transition — placeholder log-space regression on V_max
# ---------------------------------------------------------------------------

HALONG_TYPHOON_SIZE: SizeParams = SizeParams(
    r_max_intercept_log_km=3.5,    # ~33 km baseline R_max
    r_max_v_coef=-0.1,             # slightly shrinks at higher V
    r_max_sigma_log=0.1,
    r_outer_intercept_log_km=4.8,  # ~120 km baseline R_outer
    r_outer_v_coef=0.3,
    r_outer_sigma_log=0.08,
    mean_reversion_rate=0.2,
)


# ---------------------------------------------------------------------------
# Parametric wind-field parameters
# ---------------------------------------------------------------------------

HALONG_TYPHOON_WIND_FIELD: WindFieldParams = WindFieldParams(
    alpha_eye=0.4,
    outer_shape_p=1.5,
    v_outer_ref_ms=17.5,           # gale-force calibration anchor
    eps_max=0.3,
    c_eps=0.6,
    eta_ms=1.0,
    asymmetry_phase_offset_deg=90.0,
    rho_surf_sea=1.0,
    rho_surf_land=0.8,
)


# ---------------------------------------------------------------------------
# Plausibility weights — loose in Phase 1 to preserve trajectory breadth
# ---------------------------------------------------------------------------

HALONG_TYPHOON_PLAUSIBILITY: PlausibilityWeights = PlausibilityWeights(
    heading_jump_weight=0.1,
    speed_jump_weight=0.1,
    basin_boundary_weight=0.1,
    regime_consistency_weight=0.1,
    heading_jump_sigma_deg=30.0,
    speed_jump_sigma_kmh=10.0,
)


# ---------------------------------------------------------------------------
# Land mask — rough placeholder for the SCS / northern Vietnam region
# ---------------------------------------------------------------------------

def halong_land_mask(longitude: float, latitude: float) -> bool:
    """Phase 1 placeholder land mask.

    Treats everything west of ~107°E at typhoon-relevant latitudes as
    mainland Vietnam, and a rough box around Hainan as land. Hanoi at
    (105.85, 21.03) is correctly land; the eastern Gulf of Tonkin is
    correctly sea. Refine with a real polygon in a later phase.
    """
    if longitude < 107.0 and 8.0 <= latitude <= 23.0:
        return True
    if 108.5 <= longitude <= 111.0 and 18.1 <= latitude <= 20.2:
        return True
    return False


# ---------------------------------------------------------------------------
# Property points (Phase 1 illustrative set around Hanoi)
# ---------------------------------------------------------------------------
# The real property portfolio loader will replace these in a later phase.

HALONG_HANOI_REFERENCE: tuple = (105.85, 21.03)

HALONG_TYPHOON_PROPERTIES: list = [
    PropertyPoint(property_id="HAN-CENTRE",  longitude=105.85, latitude=21.03),
    PropertyPoint(property_id="HAN-NORTH",   longitude=105.85, latitude=21.20),
    PropertyPoint(property_id="HAN-EAST",    longitude=106.05, latitude=21.03),
    PropertyPoint(property_id="HAN-COASTAL", longitude=106.80, latitude=20.85),  # closer to coast
    PropertyPoint(property_id="HAN-WEST",    longitude=105.65, latitude=21.00),
]


# ---------------------------------------------------------------------------
# Historical tail-calibration anchors
# ---------------------------------------------------------------------------
# Two famous super-typhoons from the broader NW Pacific / SCS region that
# anchor the upper tail of the peak-wind distribution. Both struck the
# Philippines / South China Sea sphere of influence. Phase 3 historical
# calibration will use these (and others) to tune EXTREME-family params.
#
# Source: Wolfram|Alpha "typhoon Durian | typhoon Angela" properties.
# 1 mph = 0.44704 m/s.

HALONG_TAIL_ANCHORS: list = [
    {
        "name": "Durian",
        "year": 2006,
        "start_date": "2006-11-24",
        "end_date": "2006-12-09",
        "duration_days": 15,
        "peak_wind_mph": 155,
        "peak_wind_ms": 155 * 0.44704,   # ~69.3 m/s
        "notes": "Devastating Cat-5 super-typhoon, Philippines / SCS.",
    },
    {
        "name": "Angela",
        "year": 1995,
        "start_date": "1995-10-20",
        "end_date": "1995-11-07",
        "duration_days": 18,
        "peak_wind_mph": 178,
        "peak_wind_ms": 178 * 0.44704,   # ~79.6 m/s
        "notes": "Cat-5 super-typhoon, peak Nov 2 1995, Philippines / SCS.",
    },
]


# ---------------------------------------------------------------------------
# Boundary helper: assemble the model-side CatchmentTyphoonConfig
# ---------------------------------------------------------------------------
# This is the canonical production path the orchestrator stage uses. It
# wires the catchment-specific constants above into the catchment-agnostic
# CatchmentTyphoonConfig dataclass that the typhoon model consumes.

def build_typhoon_config(catchment_id: str = "halong") -> CatchmentTyphoonConfig:
    """Assemble the CatchmentTyphoonConfig for the Halong catchment."""
    return CatchmentTyphoonConfig(
        catchment_id=catchment_id,
        genesis_prior=HALONG_TYPHOON_GENESIS_PRIOR,
        peak_wind=HALONG_TYPHOON_PEAK_WIND,
        motion=HALONG_TYPHOON_MOTION,
        intensity=HALONG_TYPHOON_INTENSITY,
        size=HALONG_TYPHOON_SIZE,
        wind_field=HALONG_TYPHOON_WIND_FIELD,
        plausibility=HALONG_TYPHOON_PLAUSIBILITY,
        land_mask=halong_land_mask,
        property_points=HALONG_TYPHOON_PROPERTIES,
    )


__all__ = [
    "HALONG_TYPHOON_GENESIS_PRIOR",
    "HALONG_TYPHOON_PEAK_WIND",
    "HALONG_TYPHOON_MOTION",
    "HALONG_TYPHOON_INTENSITY",
    "HALONG_TYPHOON_SIZE",
    "HALONG_TYPHOON_WIND_FIELD",
    "HALONG_TYPHOON_PLAUSIBILITY",
    "halong_land_mask",
    "HALONG_HANOI_REFERENCE",
    "HALONG_TYPHOON_PROPERTIES",
    "HALONG_TAIL_ANCHORS",
    "build_typhoon_config",
]
