# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Shared fixtures for windspeed tests.

The windspeed model is a thin consumer of the same WindFieldParams +
land_mask that the typhoon pipeline uses, so we reuse the
catchment-agnostic minimal_config built for the typhoon tests.
"""

import pytest

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


# Same neutral geography as tests/models/typhoon/conftest.py — see that
# file for the rationale (no real cyclone basin, model catchment-agnostic).
TEST_BBOX = (0.0, 0.0, 10.0, 10.0)
TEST_LAND_THRESHOLD_LON = 2.0


def _default_land_mask(longitude: float, latitude: float) -> bool:
    return longitude < TEST_LAND_THRESHOLD_LON


@pytest.fixture
def minimal_config():
    """Reuse the typhoon model's neutral catchment-agnostic config."""
    return CatchmentTyphoonConfig(
        catchment_id="test",
        genesis_prior=GenesisPrior(
            bbox=TEST_BBOX,
            heading_mean_deg=270.0,
            heading_kappa=5.0,
            speed_shape=4.0,
            speed_scale=4.0,
            regime_weights={r: 0.2 for r in RegimeClass},
            scenario_mix={s: 0.2 for s in ScenarioFamily},
        ),
        peak_wind={
            s: PeakWindParams(mu_ms=35.0, sigma_ms=12.0, v_threshold_ms=50.0, alpha=2.0)
            for s in ScenarioFamily
        },
        motion=MotionParams(
            mean_speed_kmh={r: 15.0 for r in RegimeClass},
            sigma_speed_kmh={r: 4.0 for r in RegimeClass},
            mean_heading_deg={r: 270.0 for r in RegimeClass},
            sigma_heading_deg={r: 20.0 for r in RegimeClass},
        ),
        intensity=IntensityParams(),
        size=SizeParams(),
        wind_field=WindFieldParams(),
        plausibility=PlausibilityWeights(),
        land_mask=_default_land_mask,
        property_points=[
            PropertyPoint(property_id="P1", longitude=5.0, latitude=5.0),
        ],
    )
