# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Shared fixtures for typhoon model tests.

Fixtures use neutral test data only — no catchment-specific coordinates
or identifiers — so the model layer can be exercised without coupling
the tests to any particular catchment.
"""

from datetime import datetime

import pytest

from models.typhoon.data_structures import (
    RegimeClass,
    ScenarioFamily,
    TyphoonParticle,
    TyphoonState,
    TyphoonTrajectory,
    WindFieldOutput,
)
from models.typhoon.parameters import (
    CatchmentTyphoonConfig,
    GenesisPrior,
    IntensityParams,
    MotionParams,
    PeakWindParams,
    PlausibilityWeights,
    PropertyPoint,
    SizeParams,
    WindFieldParams,
)


# ---------------------------------------------------------------------------
# Sample state / particle / trajectory fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_state():
    """A canonical mid-event state, over water, moving west."""
    return TyphoonState(
        longitude=120.0,
        latitude=18.0,
        translation_speed_kmh=18.0,
        heading_deg=270.0,
        v_max_ms=40.0,
        r_max_km=35.0,
        r_outer_km=150.0,
        regime=RegimeClass.STRAIGHT_WESTWARD,
        land_flag=False,
        time_hours=24.0,
    )


@pytest.fixture
def landfall_state():
    """A state with the storm over land, decaying."""
    return TyphoonState(
        longitude=115.0,
        latitude=21.0,
        translation_speed_kmh=12.0,
        heading_deg=280.0,
        v_max_ms=25.0,
        r_max_km=40.0,
        r_outer_km=160.0,
        regime=RegimeClass.LANDFALL_DECAY,
        land_flag=True,
        time_hours=72.0,
    )


@pytest.fixture
def sample_particle(sample_state):
    return TyphoonParticle(
        state=sample_state,
        weight=0.001,
        particle_id=42,
        parent_id=7,
    )


@pytest.fixture
def sample_trajectory(sample_state, landfall_state):
    return TyphoonTrajectory(
        event_id="EVT-0001",
        particle_id=42,
        scenario_family=ScenarioFamily.SEVERE,
        genesis_time=datetime(2026, 9, 1, 0, 0, 0),
        states=[sample_state, landfall_state],
    )


# ---------------------------------------------------------------------------
# Minimal CatchmentTyphoonConfig fixture — built from model defaults only
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_config():
    """A self-contained config built from model defaults — exercises the
    parameter dataclass shape without referencing any catchment file."""
    return CatchmentTyphoonConfig(
        catchment_id="test",
        genesis_prior=GenesisPrior(
            bbox=(115.0, 15.0, 125.0, 20.0),
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
        land_mask=lambda lon, lat: lon < 117.0,
        property_points=[
            PropertyPoint(property_id="P1", longitude=115.0, latitude=21.0),
        ],
    )


@pytest.fixture
def sample_wind_output():
    return WindFieldOutput(
        point_id="P1",
        longitude=115.0,
        latitude=21.0,
        time_hours=[0.0, 1.0, 2.0, 3.0],
        sustained_ms=[5.0, 12.0, 22.0, 14.0],
        peak_sustained_ms=22.0,
        time_of_peak_hours=2.0,
        distance_at_peak_km=80.0,
        azimuth_at_peak_deg=125.0,
        duration_above_ms={17.5: 1.0, 25.0: 0.0},
    )
