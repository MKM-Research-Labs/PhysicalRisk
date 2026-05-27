# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the WindField convenience class — thin wrapper that binds a
CatchmentTyphoonConfig and exposes the functional core via methods.
"""

import pytest

from config.typhoon import PropertyPoint
from models.typhoon.wind_field import WindField, evaluate_point
from tests.models.typhoon.wind_field._helpers import (
    DEFAULT_LAT,
    DEFAULT_LON,
    make_state,
    synthetic_track,
)


class TestWindFieldClass:

    def test_constructs_from_config(self, minimal_config):
        wf = WindField(minimal_config)
        assert wf.config is minimal_config
        assert wf.params is minimal_config.wind_field
        assert wf.land_mask is minimal_config.land_mask

    def test_evaluate_matches_functional(self, minimal_config):
        wf = WindField(minimal_config)
        s = make_state(speed=0.0)
        functional = evaluate_point(
            s, DEFAULT_LON + 0.5, DEFAULT_LAT,
            minimal_config.wind_field, minimal_config.land_mask,
        )
        class_call = wf.evaluate(s, DEFAULT_LON + 0.5, DEFAULT_LAT)
        assert class_call == pytest.approx(functional, abs=1e-12)

    def test_evaluate_property_passes_lon_lat(self, minimal_config):
        wf = WindField(minimal_config)
        s = make_state(speed=0.0)
        prop = PropertyPoint(property_id="P1", longitude=DEFAULT_LON + 0.5, latitude=DEFAULT_LAT)
        a = wf.evaluate_property(s, prop)
        b = wf.evaluate(s, DEFAULT_LON + 0.5, DEFAULT_LAT)
        assert a == pytest.approx(b, abs=1e-12)

    def test_evaluate_trajectory_uses_config_thresholds_by_default(self, minimal_config):
        wf = WindField(minimal_config)
        traj = synthetic_track(start_lon=DEFAULT_LON - 2.0, start_lat=DEFAULT_LAT, n_steps=6)
        prop = PropertyPoint(property_id="P1", longitude=DEFAULT_LON, latitude=DEFAULT_LAT)
        out = wf.evaluate_trajectory(traj, prop)
        assert set(out.duration_above_ms.keys()) == set(minimal_config.output_thresholds_ms)

    def test_explicit_thresholds_override_default(self, minimal_config):
        wf = WindField(minimal_config)
        traj = synthetic_track(start_lon=DEFAULT_LON - 2.0, start_lat=DEFAULT_LAT, n_steps=6)
        prop = PropertyPoint(property_id="P1", longitude=DEFAULT_LON, latitude=DEFAULT_LAT)
        out = wf.evaluate_trajectory(traj, prop, thresholds_ms=[20.0, 30.0])
        assert set(out.duration_above_ms.keys()) == {20.0, 30.0}
