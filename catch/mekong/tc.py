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

"""Mekong / Phnom Penh tropical-cyclone (typhoon) calibration.

Catchment-specific constants for the typhoon model in
``src/models/typhoon/``. The model is catchment-agnostic; concrete values live
here. The catchment depends on the model's parameter dataclass API, never the
other way around.

All values are first-pass placeholders. Cambodia and the lower Mekong sit at
the western edge of the South China Sea typhoon basin: storms typically cross
southern Vietnam first and arrive weakened, but direct hits (e.g. Linda 1997,
Ketsana 2009) do occur. Genesis, motion, land-mask and reference geometry are
tuned for a WSW approach into Cambodia; the peak-wind / intensity physics are
carried over from the SCS calibration and should be recalibrated against
JMA / MRC best-track data before production use.

Exposed constants:
- MEKONG_TYPHOON_GENESIS_PRIOR    — initial state distribution
- MEKONG_TYPHOON_PEAK_WIND        — per-scenario-family peak-wind params
- MEKONG_TYPHOON_MOTION           — regime-conditioned motion params
- MEKONG_TYPHOON_INTENSITY        — wind intensity transition
- MEKONG_TYPHOON_SIZE             — storm-size transition
- MEKONG_TYPHOON_WIND_FIELD       — parametric wind-field params
- MEKONG_TYPHOON_PLAUSIBILITY     — soft-constraint weights
- mekong_land_mask                — callable (lon, lat) -> True if land
- MEKONG_PHNOM_PENH_REFERENCE     — Phnom Penh centre (lon, lat)
- MEKONG_TYPHOON_PROPERTIES       — Phase 1 placeholder property points
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
# Genesis prior — SCS formation zone off southern Vietnam
# ---------------------------------------------------------------------------
# bbox covers the typical genesis region for storms tracking WSW across
# southern Vietnam into Cambodia / the lower Mekong.

MEKONG_TYPHOON_GENESIS_PRIOR: GenesisPrior = GenesisPrior(
    bbox=(110.0, 9.0, 117.0, 15.0),    # (lon_min, lat_min, lon_max, lat_max)
    heading_mean_deg=260.0,            # west-south-west toward Cambodia
    heading_kappa=8.0,                 # moderately concentrated
    speed_shape=4.0,                   # Gamma(4, 4) ~= mean 16 km/h
    speed_scale=4.0,
    regime_weights={
        RegimeClass.STRAIGHT_WESTWARD: 0.50,
        RegimeClass.NW_RECURVER:       0.10,
        RegimeClass.SHARP_RECURVE:     0.05,
        RegimeClass.STALLED:           0.05,
        RegimeClass.LANDFALL_DECAY:    0.30,
    },
    scenario_mix={
        ScenarioFamily.HISTORICAL: 0.20,
        ScenarioFamily.BASELINE:   0.32,
        ScenarioFamily.MODERATE:   0.26,
        ScenarioFamily.SEVERE:     0.14,
        ScenarioFamily.EXTREME:    0.08,
    },
)


# ---------------------------------------------------------------------------
# Peak-wind distribution — hybrid truncated-normal + Pareto tail
# ---------------------------------------------------------------------------
# Carried over from the SCS calibration but shifted down ~5 m/s across families
# to reflect Cambodia's weaker (post-Vietnam-landfall) exposure, while keeping
# a meaningful EXTREME tail for direct-hit scenarios (Linda / Ketsana class).
MEKONG_TYPHOON_PEAK_WIND: dict = {
    ScenarioFamily.HISTORICAL: PeakWindParams(
        mu_ms=37.0, sigma_ms=12.0, v_threshold_ms=56.0, alpha=3.0,
    ),
    ScenarioFamily.BASELINE: PeakWindParams(
        mu_ms=43.0, sigma_ms=14.0, v_threshold_ms=58.0, alpha=2.5,
    ),
    ScenarioFamily.MODERATE: PeakWindParams(
        mu_ms=50.0, sigma_ms=15.0, v_threshold_ms=64.0, alpha=2.0,
    ),
    ScenarioFamily.SEVERE: PeakWindParams(
        mu_ms=60.0, sigma_ms=17.0, v_threshold_ms=70.0, alpha=1.5,
    ),
    ScenarioFamily.EXTREME: PeakWindParams(
        mu_ms=72.0, sigma_ms=20.0, v_threshold_ms=78.0, alpha=1.2,
    ),
}


# ---------------------------------------------------------------------------
# Motion transition — per-regime climatological speed and heading targets
# ---------------------------------------------------------------------------
# Heading convention: compass degrees, 0=N, 90=E, 180=S, 270=W.

MEKONG_TYPHOON_MOTION: MotionParams = MotionParams(
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
        RegimeClass.STRAIGHT_WESTWARD: 260.0,    # WSW toward Cambodia
        RegimeClass.NW_RECURVER:       300.0,    # WNW
        RegimeClass.SHARP_RECURVE:     350.0,    # turning N
        RegimeClass.STALLED:           260.0,
        RegimeClass.LANDFALL_DECAY:    255.0,    # WSW over land
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
    recurvature_latitude=18.0,
    recurvature_bias_deg_per_step=4.0,
)


# ---------------------------------------------------------------------------
# Intensity transition — mild over-water drift, exponential land decay
# ---------------------------------------------------------------------------

MEKONG_TYPHOON_INTENSITY: IntensityParams = IntensityParams(
    drift_ms_per_hour=0.0,        # neutral drift in Phase 1
    sigma_ms_per_hour=1.0,
    k_land_per_hour=0.18,         # faster decay — Cambodia is well inland
)


# ---------------------------------------------------------------------------
# Size transition — placeholder log-space regression on V_max
# ---------------------------------------------------------------------------

MEKONG_TYPHOON_SIZE: SizeParams = SizeParams(
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

MEKONG_TYPHOON_WIND_FIELD: WindFieldParams = WindFieldParams(
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

MEKONG_TYPHOON_PLAUSIBILITY: PlausibilityWeights = PlausibilityWeights(
    heading_jump_weight=0.1,
    speed_jump_weight=0.1,
    basin_boundary_weight=0.1,
    regime_consistency_weight=0.1,
    heading_jump_sigma_deg=30.0,
    speed_jump_sigma_kmh=10.0,
)


# ---------------------------------------------------------------------------
# Land mask — rough placeholder for the lower-Mekong / Cambodia region
# ---------------------------------------------------------------------------

def mekong_land_mask(longitude: float, latitude: float) -> bool:
    """Phase 1 placeholder land mask.

    Treats the mainland from the Gulf of Thailand coast eastward across
    Cambodia and the southern-Vietnam Mekong delta (roughly 103-106.7°E,
    9.5-14.5°N) as land. Phnom Penh at (104.93, 11.56) is correctly land; the
    Gulf of Thailand to the south-west and the South China Sea offshore of the
    delta are correctly sea. Refine with a real polygon in a later phase.
    """
    if 103.0 <= longitude < 106.7 and 9.5 <= latitude <= 14.5:
        return True
    return False


# ---------------------------------------------------------------------------
# Property points (Phase 1 illustrative set around Phnom Penh)
# ---------------------------------------------------------------------------
# The real property portfolio loader will replace these in a later phase.

MEKONG_PHNOM_PENH_REFERENCE: tuple = (104.9282, 11.5564)

MEKONG_TYPHOON_PROPERTIES: list = [
    PropertyPoint(property_id="PNH-CENTRE", longitude=104.928, latitude=11.556),
    PropertyPoint(property_id="PNH-NORTH",  longitude=104.912, latitude=11.700),
    PropertyPoint(property_id="PNH-SOUTH",  longitude=104.940, latitude=11.450),
    PropertyPoint(property_id="PNH-EAST",   longitude=105.040, latitude=11.550),
    PropertyPoint(property_id="PNH-WEST",   longitude=104.820, latitude=11.560),
]


# ---------------------------------------------------------------------------
# Historical tail-calibration anchors
# ---------------------------------------------------------------------------
# Two Cambodia-relevant systems that anchor the upper tail of the peak-wind
# distribution. Both tracked across southern Vietnam into Cambodia / the lower
# Mekong. Phase 3 historical calibration will use these (and others) to tune
# the EXTREME-family params. 1 mph = 0.44704 m/s.

MEKONG_TAIL_ANCHORS: list = [
    {
        "name": "Linda",
        "year": 1997,
        "start_date": "1997-11-02",
        "end_date": "1997-11-09",
        "duration_days": 7,
        "peak_wind_mph": 100,
        "peak_wind_ms": 100 * 0.44704,   # ~44.7 m/s
        "notes": "Crossed the Mekong delta into Cambodia; catastrophic for "
                 "southern Vietnam / Cambodia despite modest peak winds.",
    },
    {
        "name": "Ketsana",
        "year": 2009,
        "start_date": "2009-09-26",
        "end_date": "2009-09-30",
        "duration_days": 4,
        "peak_wind_mph": 105,
        "peak_wind_ms": 105 * 0.44704,   # ~46.9 m/s
        "notes": "Tracked Vietnam -> Cambodia -> Laos; major Mekong flooding.",
    },
]


# ---------------------------------------------------------------------------
# Boundary helper: assemble the model-side CatchmentTyphoonConfig
# ---------------------------------------------------------------------------
# This is the canonical production path the orchestrator stage uses. It wires
# the catchment-specific constants above into the catchment-agnostic
# CatchmentTyphoonConfig dataclass that the typhoon model consumes.

def build_typhoon_config(catchment_id: str = "mekong") -> CatchmentTyphoonConfig:
    """Assemble the CatchmentTyphoonConfig for the Mekong catchment."""
    return CatchmentTyphoonConfig(
        catchment_id=catchment_id,
        genesis_prior=MEKONG_TYPHOON_GENESIS_PRIOR,
        peak_wind=MEKONG_TYPHOON_PEAK_WIND,
        motion=MEKONG_TYPHOON_MOTION,
        intensity=MEKONG_TYPHOON_INTENSITY,
        size=MEKONG_TYPHOON_SIZE,
        wind_field=MEKONG_TYPHOON_WIND_FIELD,
        plausibility=MEKONG_TYPHOON_PLAUSIBILITY,
        land_mask=mekong_land_mask,
        property_points=MEKONG_TYPHOON_PROPERTIES,
    )


__all__ = [
    "MEKONG_TYPHOON_GENESIS_PRIOR",
    "MEKONG_TYPHOON_PEAK_WIND",
    "MEKONG_TYPHOON_MOTION",
    "MEKONG_TYPHOON_INTENSITY",
    "MEKONG_TYPHOON_SIZE",
    "MEKONG_TYPHOON_WIND_FIELD",
    "MEKONG_TYPHOON_PLAUSIBILITY",
    "mekong_land_mask",
    "MEKONG_PHNOM_PENH_REFERENCE",
    "MEKONG_TYPHOON_PROPERTIES",
    "MEKONG_TAIL_ANCHORS",
    "build_typhoon_config",
]
