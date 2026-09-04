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

"""Thames / London tropical-cyclone (windstorm) calibration — MILD regime.

Catchment-specific constants for the typhoon model in ``src/models/typhoon/``.
The model is catchment-agnostic; concrete values live here. The catchment
depends on the model's parameter dataclass API, never the other way around.

The Thames basin does not experience true tropical cyclones. What reaches the
UK are ex-tropical / extratropical Atlantic windstorms — the decaying remnants
of systems that recurve across the North Atlantic and arrive from the
south-west. This calibration deliberately models a **mild** hazard:

  - low peak-wind means across every scenario family (gale / severe-gale
    rather than hurricane-force),
  - thin Pareto tails (high alpha) so even the EXTREME family stays modest,
  - low hard caps (``v_max_ms``) that clamp any draw well below typhoon force,
  - neutral-to-negative over-water intensity drift and rapid land decay, so
    storms weaken as they cross the British Isles.

Contrast with ``data/catch/halong/tc.py``, which models genuine South China
Sea super-typhoons (mu up to 50 m/s, alpha down to 1.2). Thames is much milder
by design.

The track-regime enum (``RegimeClass``) is fixed by ``config.typhoon`` and
named for the NW-Pacific convention (``STRAIGHT_WESTWARD`` etc). For the
Thames Atlantic setting the regimes are *repurposed*: the actual direction of
travel is set per-regime in ``THAMES_TYPHOON_MOTION.mean_heading_deg`` and is
eastward / north-eastward (storms tracking off the Atlantic toward NW Europe),
not westward.

Exposed constants:
- THAMES_TYPHOON_GENESIS_PRIOR    — initial state distribution
- THAMES_TYPHOON_PEAK_WIND        — per-scenario-family peak-wind params
- THAMES_TYPHOON_MOTION           — regime-conditioned motion params
- THAMES_TYPHOON_INTENSITY        — wind intensity transition
- THAMES_TYPHOON_SIZE             — storm-size transition
- THAMES_TYPHOON_WIND_FIELD       — parametric wind-field params
- THAMES_TYPHOON_PLAUSIBILITY     — soft-constraint weights
- thames_land_mask                — callable (lon, lat) -> True if land
- THAMES_LONDON_REFERENCE         — London centre (lon, lat)
- THAMES_TYPHOON_PROPERTIES       — Phase 1 placeholder property points
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
# Genesis prior — eastern North Atlantic approaches, south-west of the UK
# ---------------------------------------------------------------------------
# bbox covers the open-Atlantic region south-west of Ireland from which
# ex-tropical systems track north-east toward the British Isles. Storms move
# broadly eastward (heading ~70 deg, ENE), opposite to the NW-Pacific basin.

THAMES_TYPHOON_GENESIS_PRIOR: GenesisPrior = GenesisPrior(
    bbox=(-14.0, 47.0, -8.0, 51.0),    # (lon_min, lat_min, lon_max, lat_max)
    heading_mean_deg=70.0,             # ENE — off the Atlantic toward the UK
    heading_kappa=8.0,                 # moderately concentrated
    speed_shape=4.0,                   # Gamma(4, 12) ~= mean 48 km/h (fast)
    speed_scale=12.0,                  # extratropical systems move quickly
    regime_weights={
        RegimeClass.STRAIGHT_WESTWARD: 0.45,   # repurposed: straight ENE track
        RegimeClass.NW_RECURVER:       0.20,   # poleward recurve toward NE
        RegimeClass.SHARP_RECURVE:     0.05,
        RegimeClass.STALLED:           0.05,
        RegimeClass.LANDFALL_DECAY:    0.25,   # decaying over the British Isles
    },
    scenario_mix={
        ScenarioFamily.HISTORICAL: 0.25,
        ScenarioFamily.BASELINE:   0.35,
        ScenarioFamily.MODERATE:   0.25,
        ScenarioFamily.SEVERE:     0.12,
        ScenarioFamily.EXTREME:    0.03,       # rare and still mild
    },
)


# ---------------------------------------------------------------------------
# Peak-wind distribution — hybrid truncated-normal + Pareto tail (MILD)
# ---------------------------------------------------------------------------
# Spec eq. 14. Means stay in the gale / severe-gale band, tails are thin
# (high alpha), and v_max_ms caps every draw well below hurricane force.
# EXTREME still has a fatter tail than BASELINE (lower alpha), as the model
# expects, but the whole distribution is far milder than a real typhoon.

THAMES_TYPHOON_PEAK_WIND: dict = {
    ScenarioFamily.HISTORICAL: PeakWindParams(
        mu_ms=14.0, sigma_ms=5.0, v_threshold_ms=30.0, alpha=4.5, v_max_ms=35.0,
    ),
    ScenarioFamily.BASELINE: PeakWindParams(
        mu_ms=17.0, sigma_ms=6.0, v_threshold_ms=32.0, alpha=4.0, v_max_ms=38.0,
    ),
    ScenarioFamily.MODERATE: PeakWindParams(
        mu_ms=20.0, sigma_ms=7.0, v_threshold_ms=35.0, alpha=3.5, v_max_ms=42.0,
    ),
    ScenarioFamily.SEVERE: PeakWindParams(
        mu_ms=23.0, sigma_ms=8.0, v_threshold_ms=38.0, alpha=3.0, v_max_ms=46.0,
    ),
    ScenarioFamily.EXTREME: PeakWindParams(
        mu_ms=27.0, sigma_ms=9.0, v_threshold_ms=40.0, alpha=2.5, v_max_ms=50.0,
    ),
}


# ---------------------------------------------------------------------------
# Motion transition — fast eastward / north-eastward Atlantic tracks
# ---------------------------------------------------------------------------
# Heading convention: compass degrees, 0=N, 90=E, 180=S, 270=W. Headings here
# are easterly (~70-90 deg) so storms move off the Atlantic toward NW Europe.

THAMES_TYPHOON_MOTION: MotionParams = MotionParams(
    mean_speed_kmh={
        RegimeClass.STRAIGHT_WESTWARD: 48.0,   # fast eastward steering flow
        RegimeClass.NW_RECURVER:       44.0,
        RegimeClass.SHARP_RECURVE:     40.0,
        RegimeClass.STALLED:            8.0,    # lowest — see plausibility test
        RegimeClass.LANDFALL_DECAY:    36.0,
    },
    sigma_speed_kmh={
        RegimeClass.STRAIGHT_WESTWARD: 8.0,
        RegimeClass.NW_RECURVER:       8.0,
        RegimeClass.SHARP_RECURVE:     9.0,
        RegimeClass.STALLED:           3.0,
        RegimeClass.LANDFALL_DECAY:    6.0,
    },
    mean_heading_deg={
        RegimeClass.STRAIGHT_WESTWARD: 75.0,    # ENE straight track
        RegimeClass.NW_RECURVER:       50.0,    # NE recurve (poleward)
        RegimeClass.SHARP_RECURVE:     30.0,    # NNE sharp recurve
        RegimeClass.STALLED:           75.0,
        RegimeClass.LANDFALL_DECAY:    85.0,    # nearly due east over land
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
    recurvature_latitude=52.0,                  # recurve poleward near the UK
    recurvature_bias_deg_per_step=4.0,
)


# ---------------------------------------------------------------------------
# Intensity transition — gentle over-water weakening, rapid land decay
# ---------------------------------------------------------------------------
# Extratropical systems over the cool North Atlantic do not re-intensify like
# tropical cyclones; a slightly negative drift reflects gradual weakening, and
# a high land-decay rate makes the storm fade quickly once it reaches the UK
# (so inland London exposure stays mild).

THAMES_TYPHOON_INTENSITY: IntensityParams = IntensityParams(
    drift_ms_per_hour=-0.2,       # gentle weakening over cool water
    sigma_ms_per_hour=1.0,
    k_land_per_hour=0.25,         # ~50% wind loss in ~3h over land (fast decay)
)


# ---------------------------------------------------------------------------
# Size transition — large but diffuse extratropical wind fields
# ---------------------------------------------------------------------------
# UK windstorms are physically large but diffuse: wide R_outer, modest core
# intensity. Kept close to the model defaults.

THAMES_TYPHOON_SIZE: SizeParams = SizeParams(
    r_max_intercept_log_km=3.7,    # ~40 km baseline R_max (broad core)
    r_max_v_coef=-0.1,
    r_max_sigma_log=0.1,
    r_outer_intercept_log_km=5.0,  # ~150 km baseline R_outer (wide field)
    r_outer_v_coef=0.3,
    r_outer_sigma_log=0.08,
    mean_reversion_rate=0.2,
)


# ---------------------------------------------------------------------------
# Parametric wind-field parameters
# ---------------------------------------------------------------------------

THAMES_TYPHOON_WIND_FIELD: WindFieldParams = WindFieldParams(
    alpha_eye=0.4,
    outer_shape_p=1.5,
    v_outer_ref_ms=17.5,           # gale-force calibration anchor
    eps_max=0.3,
    c_eps=0.6,
    eta_ms=1.0,
    asymmetry_phase_offset_deg=90.0,   # Northern-Hemisphere right-of-track peak
    rho_surf_sea=1.0,
    rho_surf_land=0.8,
)


# ---------------------------------------------------------------------------
# Plausibility weights — loose in Phase 1 to preserve trajectory breadth
# ---------------------------------------------------------------------------

THAMES_TYPHOON_PLAUSIBILITY: PlausibilityWeights = PlausibilityWeights(
    heading_jump_weight=0.1,
    speed_jump_weight=0.1,
    basin_boundary_weight=0.1,
    regime_consistency_weight=0.1,
    heading_jump_sigma_deg=30.0,
    speed_jump_sigma_kmh=12.0,
)


# ---------------------------------------------------------------------------
# Land mask — rough placeholder for the British Isles
# ---------------------------------------------------------------------------

def thames_land_mask(longitude: float, latitude: float) -> bool:
    """Phase 1 placeholder land mask for the British Isles.

    Treats two crude bounding boxes as land: Great Britain and Ireland. London
    at (-0.1278, 51.5074) is correctly land; the eastern Atlantic approaches
    (the genesis region south-west of Ireland) are correctly sea. Refine with a
    real coastline polygon in a later phase.
    """
    # Great Britain (crude bounding box: Cornwall to northern Scotland)
    if -5.7 <= longitude <= 1.8 and 49.9 <= latitude <= 58.7:
        return True
    # Ireland
    if -10.5 <= longitude <= -6.0 and 51.4 <= latitude <= 55.4:
        return True
    return False


# ---------------------------------------------------------------------------
# Property points (Phase 1 illustrative set around London / the Thames)
# ---------------------------------------------------------------------------
# The real property portfolio loader will replace these in a later phase.

THAMES_LONDON_REFERENCE: tuple = (-0.1278, 51.5074)

THAMES_TYPHOON_PROPERTIES: list = [
    PropertyPoint(property_id="LON-CENTRE",  longitude=-0.1278, latitude=51.5074),
    PropertyPoint(property_id="LON-WEST",    longitude=-0.3500, latitude=51.4500),  # toward Reading
    PropertyPoint(property_id="LON-EAST",    longitude=0.3000,  latitude=51.5000),  # toward the estuary
    PropertyPoint(property_id="LON-NORTH",   longitude=-0.1300, latitude=51.6000),
    PropertyPoint(property_id="LON-SOUTH",   longitude=-0.1300, latitude=51.4200),
]


# ---------------------------------------------------------------------------
# Historical reference anchors (mild UK windstorms)
# ---------------------------------------------------------------------------
# Two notable UK windstorms that anchor the (mild) upper end of the Thames
# wind distribution. These are extratropical / ex-tropical systems, not
# tropical cyclones, and their peak sustained winds are far below typhoon
# force — consistent with the mild calibration above.
# 1 mph = 0.44704 m/s.

THAMES_REFERENCE_STORMS: list = [
    {
        "name": "Great Storm of 1987",
        "year": 1987,
        "start_date": "1987-10-15",
        "end_date": "1987-10-16",
        "duration_days": 1,
        "peak_wind_mph": 86,             # sustained; gusts higher
        "peak_wind_ms": 86 * 0.44704,    # ~38.4 m/s
        "notes": "Severe extratropical windstorm, SE England.",
    },
    {
        "name": "Storm Eunice",
        "year": 2022,
        "start_date": "2022-02-18",
        "end_date": "2022-02-19",
        "duration_days": 1,
        "peak_wind_mph": 70,             # sustained over land
        "peak_wind_ms": 70 * 0.44704,    # ~31.3 m/s
        "notes": "Atlantic windstorm, sting jet, southern UK.",
    },
]


# ---------------------------------------------------------------------------
# Boundary helper: assemble the model-side CatchmentTyphoonConfig
# ---------------------------------------------------------------------------
# This is the canonical production path the orchestrator stage uses. It wires
# the catchment-specific constants above into the catchment-agnostic
# CatchmentTyphoonConfig dataclass that the typhoon model consumes.

def build_typhoon_config(catchment_id: str = "thames") -> CatchmentTyphoonConfig:
    """Assemble the CatchmentTyphoonConfig for the Thames catchment."""
    return CatchmentTyphoonConfig(
        catchment_id=catchment_id,
        genesis_prior=THAMES_TYPHOON_GENESIS_PRIOR,
        peak_wind=THAMES_TYPHOON_PEAK_WIND,
        motion=THAMES_TYPHOON_MOTION,
        intensity=THAMES_TYPHOON_INTENSITY,
        size=THAMES_TYPHOON_SIZE,
        wind_field=THAMES_TYPHOON_WIND_FIELD,
        plausibility=THAMES_TYPHOON_PLAUSIBILITY,
        land_mask=thames_land_mask,
        property_points=THAMES_TYPHOON_PROPERTIES,
    )


__all__ = [
    "THAMES_TYPHOON_GENESIS_PRIOR",
    "THAMES_TYPHOON_PEAK_WIND",
    "THAMES_TYPHOON_MOTION",
    "THAMES_TYPHOON_INTENSITY",
    "THAMES_TYPHOON_SIZE",
    "THAMES_TYPHOON_WIND_FIELD",
    "THAMES_TYPHOON_PLAUSIBILITY",
    "thames_land_mask",
    "THAMES_LONDON_REFERENCE",
    "THAMES_TYPHOON_PROPERTIES",
    "THAMES_REFERENCE_STORMS",
    "build_typhoon_config",
]
