# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.windspeed.query — windspeed() function and
WindSpeedModel class.
"""

from datetime import datetime

import numpy as np
import pytest

from config.typhoon import RegimeClass, ScenarioFamily
from models.typhoon.data_structures import TyphoonState, TyphoonTrajectory
from models.typhoon.pipeline import write_event_trajectory
from models.windspeed import WindSpeedModel, windspeed


def _trajectory():
    # Two-state trajectory moving east, intensifying.
    states = [
        TyphoonState(
            longitude=4.0, latitude=5.0,
            translation_speed_kmh=30.0, heading_deg=90.0,
            v_max_ms=40.0, r_max_km=30.0, r_outer_km=150.0,
            regime=RegimeClass.STRAIGHT_WESTWARD, land_flag=False, time_hours=0.0,
        ),
        TyphoonState(
            longitude=6.0, latitude=5.0,
            translation_speed_kmh=30.0, heading_deg=90.0,
            v_max_ms=50.0, r_max_km=30.0, r_outer_km=150.0,
            regime=RegimeClass.STRAIGHT_WESTWARD, land_flag=False, time_hours=2.0,
        ),
    ]
    return TyphoonTrajectory(
        event_id="EVT-TEST",
        particle_id=0,
        scenario_family=ScenarioFamily.BASELINE,
        genesis_time=datetime(2026, 1, 1),
        states=states,
    )


class TestWindspeedFunction:

    def test_returns_float_at_query_point(self, minimal_config):
        v = windspeed(
            event=_trajectory(),
            hour=1.0, lon=5.0, lat=5.0,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        assert isinstance(v, float)
        assert v >= 0.0

    def test_strength_grows_as_storm_intensifies(self, minimal_config):
        # The storm intensifies from V=40 at t=0 to V=50 at t=2.
        traj = _trajectory()
        v_early = windspeed(
            event=traj, hour=0.0, lon=4.0, lat=5.0,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        v_late = windspeed(
            event=traj, hour=2.0, lon=6.0, lat=5.0,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        # Both queries are at the storm centre at their respective times.
        # At t=2 the storm is stronger, so the centre wind is higher.
        assert v_late > v_early

    def test_far_point_has_lower_wind(self, minimal_config):
        traj = _trajectory()
        v_near = windspeed(
            event=traj, hour=0.0, lon=4.0, lat=5.0,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        v_far = windspeed(
            event=traj, hour=0.0, lon=4.0, lat=9.0,   # ~440 km north
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        assert v_far < v_near

    def test_accepts_path_via_pipeline_writer(self, minimal_config, tmp_path):
        traj = _trajectory()
        path = tmp_path / "EVT-TEST.json"
        write_event_trajectory(traj, path, event_idx=0)

        v_from_path = windspeed(
            event=path, hour=1.0, lon=5.0, lat=5.0,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        v_from_obj = windspeed(
            event=traj, hour=1.0, lon=5.0, lat=5.0,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        assert v_from_path == pytest.approx(v_from_obj, rel=1e-9)


class TestWindSpeedModel:

    def test_query_matches_function_form(self, minimal_config):
        ws = WindSpeedModel(minimal_config)
        traj = _trajectory()

        a = ws.query(traj, hour=1.0, lon=5.0, lat=5.0)
        b = windspeed(
            event=traj, hour=1.0, lon=5.0, lat=5.0,
            wind_field_params=minimal_config.wind_field,
            land_mask=minimal_config.land_mask,
        )
        assert a == pytest.approx(b, rel=1e-9)

    def test_call_is_query_alias(self, minimal_config):
        ws = WindSpeedModel(minimal_config)
        traj = _trajectory()
        assert ws(traj, 1.0, 5.0, 5.0) == ws.query(traj, 1.0, 5.0, 5.0)

    def test_caches_loaded_events_by_path(self, minimal_config, tmp_path):
        ws = WindSpeedModel(minimal_config)
        traj = _trajectory()
        path = tmp_path / "EVT-TEST.json"
        write_event_trajectory(traj, path, event_idx=0)

        assert ws.cached_event_keys == ()
        ws.query(path, hour=1.0, lon=5.0, lat=5.0)
        assert str(path) in ws.cached_event_keys
        ws.query(path, hour=1.5, lon=5.5, lat=5.0)
        # Still one cached entry — second query reused the cache.
        assert len(ws.cached_event_keys) == 1

    def test_clear_cache(self, minimal_config, tmp_path):
        ws = WindSpeedModel(minimal_config)
        path = tmp_path / "EVT-TEST.json"
        write_event_trajectory(_trajectory(), path, event_idx=0)
        ws.query(path, hour=1.0, lon=5.0, lat=5.0)
        assert ws.cached_event_keys != ()
        ws.clear_cache()
        assert ws.cached_event_keys == ()

    def test_in_memory_trajectory_is_not_cached(self, minimal_config):
        # Passing a TyphoonTrajectory bypasses the loader/cache entirely.
        ws = WindSpeedModel(minimal_config)
        ws.query(_trajectory(), hour=0.5, lon=5.0, lat=5.0)
        assert ws.cached_event_keys == ()
