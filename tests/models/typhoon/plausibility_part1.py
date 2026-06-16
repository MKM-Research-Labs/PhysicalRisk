# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.plausibility — soft-constraint scoring.

Covers each component:
  - heading_jump_score: smooth, monotonic in |Δψ|, weight/sigma disabling
  - speed_jump_score: smooth, monotonic in |Δu|, weight/sigma disabling
  - basin_boundary_score: 1.0 inside, smooth decay outside, weight disabling
  - regime_consistency_score: standardised deviation behaviour, STALLED
    example from the spec, weight disabling

And the composer:
  - plausibility_score is the product of components, bounded in (0, 1]
  - "perfect" trajectory (no jumps, inside basin, on regime) -> 1.0
  - one weight up demonstrably tightens that dimension at fixed seed
  - hand-crafted "bad" trajectory accumulates a low cumulative score

Plus the ParticleFilter adapter:
  - make_particle_plausibility wraps the composer for compute_weights
  - prev_state=None returns 1.0 cleanly
 (part 1 of 3)
"""

import math
from dataclasses import replace

import numpy as np
import pytest

from config.typhoon import (
    PlausibilityWeights,
)
from models.typhoon.data_structures import (
    RegimeClass,
    ScenarioFamily,
    TyphoonParticle,
    TyphoonState,
)
from models.typhoon.plausibility import (
    basin_boundary_score,
    heading_jump_score,
    make_particle_plausibility,
    plausibility_score,
    regime_consistency_score,
    speed_jump_score,
)


# ===========================================================================
# Helpers
# ===========================================================================


def _state(
    lon=5.0,
    lat=5.0,
    speed=18.0,
    heading=270.0,
    regime=RegimeClass.STRAIGHT_WESTWARD,
    v=40.0,
    r_max=35.0,
    r_outer=150.0,
    land=False,
    t=0.0,
):
    return TyphoonState(
        longitude=lon,
        latitude=lat,
        translation_speed_kmh=speed,
        heading_deg=heading,
        v_max_ms=v,
        r_max_km=r_max,
        r_outer_km=r_outer,
        regime=regime,
        land_flag=land,
        time_hours=t,
    )


# ===========================================================================
# heading_jump_score
# ===========================================================================


class TestHeadingJumpScore:

    def test_no_jump_is_one(self):
        s = _state(heading=270.0)
        prev = _state(heading=270.0)
        assert heading_jump_score(s, prev, weight=0.1, sigma_deg=30.0) == 1.0

    def test_monotonic_in_delta(self):
        # Score must strictly decrease as the jump grows.
        prev = _state(heading=270.0)
        scores = [
            heading_jump_score(_state(heading=h), prev, 0.1, 30.0)
            for h in (270.0, 280.0, 300.0, 330.0, 0.0)
        ]
        for a, b in zip(scores, scores[1:]):
            assert b < a

    def test_circular_delta_uses_short_arc(self):
        # 350 -> 10 is a 20 deg jump, not 340.
        prev = _state(heading=350.0)
        s = _state(heading=10.0)
        score = heading_jump_score(s, prev, weight=0.1, sigma_deg=30.0)
        # Equivalent to a +20 deg jump on the same scale.
        equivalent = heading_jump_score(
            _state(heading=20.0), _state(heading=0.0), 0.1, 30.0,
        )
        assert score == pytest.approx(equivalent, abs=1e-12)

    def test_in_zero_to_one_range(self):
        prev = _state(heading=270.0)
        for h in np.linspace(0.0, 359.0, 36):
            score = heading_jump_score(_state(heading=h), prev, 0.5, 30.0)
            assert 0.0 < score <= 1.0

    def test_zero_weight_disables(self):
        prev = _state(heading=0.0)
        s = _state(heading=180.0)
        assert heading_jump_score(s, prev, weight=0.0, sigma_deg=30.0) == 1.0

    def test_non_positive_sigma_disables(self):
        prev = _state(heading=0.0)
        s = _state(heading=90.0)
        assert heading_jump_score(s, prev, weight=1.0, sigma_deg=0.0) == 1.0
        assert heading_jump_score(s, prev, weight=1.0, sigma_deg=-5.0) == 1.0


# ===========================================================================
# speed_jump_score
# ===========================================================================


class TestSpeedJumpScore:

    def test_no_jump_is_one(self):
        s = _state(speed=20.0)
        prev = _state(speed=20.0)
        assert speed_jump_score(s, prev, weight=0.1, sigma_kmh=10.0) == 1.0

    def test_monotonic_in_delta(self):
        prev = _state(speed=20.0)
        scores = [
            speed_jump_score(_state(speed=s_kmh), prev, 0.1, 10.0)
            for s_kmh in (20.0, 22.0, 30.0, 50.0, 100.0)
        ]
        for a, b in zip(scores, scores[1:]):
            assert b < a

    def test_in_zero_to_one_range(self):
        prev = _state(speed=20.0)
        for s_kmh in (0.0, 5.0, 20.0, 50.0, 200.0):
            score = speed_jump_score(_state(speed=s_kmh), prev, 0.5, 10.0)
            assert 0.0 < score <= 1.0

    def test_zero_weight_disables(self):
        s = _state(speed=100.0)
        prev = _state(speed=0.0)
        assert speed_jump_score(s, prev, weight=0.0, sigma_kmh=10.0) == 1.0

    def test_non_positive_sigma_disables(self):
        s = _state(speed=100.0)
        prev = _state(speed=0.0)
        assert speed_jump_score(s, prev, weight=1.0, sigma_kmh=0.0) == 1.0


# ===========================================================================
# basin_boundary_score
# ===========================================================================


class TestBasinBoundaryScore:

    @pytest.fixture
    def bbox(self):
        return (115.0, 15.0, 125.0, 20.0)

    def test_inside_is_one(self, bbox):
        s = _state(lon=120.0, lat=18.0)
        assert basin_boundary_score(s, bbox, weight=0.5) == 1.0

    def test_on_boundary_is_one(self, bbox):
        s = _state(lon=125.0, lat=20.0)
        assert basin_boundary_score(s, bbox, weight=0.5) == 1.0

    def test_outside_degrades_smoothly(self, bbox):
        # 1 degree outside the eastern boundary
        s_close = _state(lon=126.0, lat=18.0)
        s_far = _state(lon=130.0, lat=18.0)
        score_close = basin_boundary_score(s_close, bbox, weight=0.1)
        score_far = basin_boundary_score(s_far, bbox, weight=0.1)
        assert 0.0 < score_far < score_close < 1.0

    def test_diagonal_outside_counts_both_axes(self, bbox):
        # Outside on both lon and lat: penalty is larger than either alone.
        s_lon_only = _state(lon=130.0, lat=18.0)   # 5 deg lon overshoot
        s_lat_only = _state(lon=120.0, lat=25.0)   # 5 deg lat overshoot
        s_diag = _state(lon=130.0, lat=25.0)       # both
        score_diag = basin_boundary_score(s_diag, bbox, weight=0.1)
        score_lon = basin_boundary_score(s_lon_only, bbox, weight=0.1)
        score_lat = basin_boundary_score(s_lat_only, bbox, weight=0.1)
        # Diagonal overshoot has larger total distance, lower score.
        assert score_diag < score_lon
        assert score_diag < score_lat

    def test_zero_weight_disables(self, bbox):
        s = _state(lon=500.0, lat=80.0)   # absurdly outside
        assert basin_boundary_score(s, bbox, weight=0.0) == 1.0
