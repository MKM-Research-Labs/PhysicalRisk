# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.data_structures — enums, state, particle,
trajectory, and wind-field output.

Covers: RegimeClass / ScenarioFamily enum values; TyphoonState,
TyphoonParticle, TyphoonTrajectory, WindFieldOutput to_dict / from_dict
round-trips; trajectory properties (horizon_hours, n_steps).
"""

from datetime import datetime

import pytest

from config.typhoon import RegimeClass, ScenarioFamily
from models.typhoon.data_structures import (
    TyphoonParticle,
    TyphoonState,
    TyphoonTrajectory,
    WindFieldOutput,
)


# ===========================================================================
# RegimeClass enum
# ===========================================================================


class TestRegimeClass:

    def test_straight_westward_value(self):
        assert RegimeClass.STRAIGHT_WESTWARD.value == "straight_westward"

    def test_nw_recurver_value(self):
        assert RegimeClass.NW_RECURVER.value == "nw_recurver"

    def test_sharp_recurve_value(self):
        assert RegimeClass.SHARP_RECURVE.value == "sharp_recurve"

    def test_stalled_value(self):
        assert RegimeClass.STALLED.value == "stalled"

    def test_landfall_decay_value(self):
        assert RegimeClass.LANDFALL_DECAY.value == "landfall_decay"

    def test_five_regimes_exist(self):
        # The five regimes are the canonical Phase 1 set; adding more is a
        # deliberate spec change, so guard the count.
        assert len(RegimeClass) == 5

    def test_roundtrip_via_value(self):
        for r in RegimeClass:
            assert RegimeClass(r.value) is r


# ===========================================================================
# ScenarioFamily enum
# ===========================================================================


class TestScenarioFamily:

    def test_historical_value(self):
        assert ScenarioFamily.HISTORICAL.value == "historical"

    def test_baseline_value(self):
        assert ScenarioFamily.BASELINE.value == "baseline"

    def test_moderate_value(self):
        assert ScenarioFamily.MODERATE.value == "moderate"

    def test_severe_value(self):
        assert ScenarioFamily.SEVERE.value == "severe"

    def test_extreme_value(self):
        assert ScenarioFamily.EXTREME.value == "extreme"

    def test_five_families_exist(self):
        assert len(ScenarioFamily) == 5

    def test_roundtrip_via_value(self):
        for s in ScenarioFamily:
            assert ScenarioFamily(s.value) is s


# ===========================================================================
# TyphoonState
# ===========================================================================


class TestTyphoonState:

    def test_construction(self, sample_state):
        assert sample_state.longitude == 120.0
        assert sample_state.regime is RegimeClass.STRAIGHT_WESTWARD
        assert sample_state.land_flag is False

    def test_to_dict_encodes_regime_as_string(self, sample_state):
        d = sample_state.to_dict()
        assert d["regime"] == "straight_westward"

    def test_to_dict_contains_all_fields(self, sample_state):
        d = sample_state.to_dict()
        expected_keys = {
            "longitude", "latitude", "translation_speed_kmh", "heading_deg",
            "v_max_ms", "r_max_km", "r_outer_km", "regime", "land_flag",
            "time_hours",
        }
        assert set(d.keys()) == expected_keys

    def test_roundtrip(self, sample_state):
        d = sample_state.to_dict()
        restored = TyphoonState.from_dict(d)
        assert restored == sample_state

    def test_roundtrip_landfall_state(self, landfall_state):
        d = landfall_state.to_dict()
        restored = TyphoonState.from_dict(d)
        assert restored == landfall_state
        assert restored.land_flag is True
        assert restored.regime is RegimeClass.LANDFALL_DECAY


# ===========================================================================
# TyphoonParticle
# ===========================================================================


class TestTyphoonParticle:

    def test_construction(self, sample_particle):
        assert sample_particle.weight == 0.001
        assert sample_particle.particle_id == 42
        assert sample_particle.parent_id == 7

    def test_genesis_particle_has_no_parent(self, sample_state):
        p = TyphoonParticle(state=sample_state, weight=0.01, particle_id=1)
        assert p.parent_id is None

    def test_roundtrip(self, sample_particle):
        d = sample_particle.to_dict()
        restored = TyphoonParticle.from_dict(d)
        assert restored == sample_particle

    def test_roundtrip_with_none_parent(self, sample_state):
        p = TyphoonParticle(state=sample_state, weight=0.01, particle_id=1)
        d = p.to_dict()
        restored = TyphoonParticle.from_dict(d)
        assert restored == p
        assert restored.parent_id is None


# ===========================================================================
# TyphoonTrajectory
# ===========================================================================


class TestTyphoonTrajectory:

    def test_construction(self, sample_trajectory):
        assert sample_trajectory.event_id == "EVT-0001"
        assert sample_trajectory.scenario_family is ScenarioFamily.SEVERE
        assert sample_trajectory.n_steps == 2

    def test_horizon_hours_matches_final_state(self, sample_trajectory):
        assert sample_trajectory.horizon_hours == 72.0

    def test_empty_trajectory_horizon_is_zero(self):
        t = TyphoonTrajectory(
            event_id="EMPTY",
            particle_id=0,
            scenario_family=ScenarioFamily.BASELINE,
            genesis_time=datetime(2026, 1, 1),
        )
        assert t.n_steps == 0
        assert t.horizon_hours == 0.0

    def test_roundtrip(self, sample_trajectory):
        d = sample_trajectory.to_dict()
        restored = TyphoonTrajectory.from_dict(d)
        assert restored == sample_trajectory


# ===========================================================================
# WindFieldOutput
# ===========================================================================


class TestWindFieldOutput:

    def test_construction(self, sample_wind_output):
        assert sample_wind_output.point_id == "P1"
        assert sample_wind_output.peak_sustained_ms == 22.0
        assert sample_wind_output.duration_above_ms[17.5] == 1.0

    def test_peak_matches_max_of_series(self, sample_wind_output):
        assert sample_wind_output.peak_sustained_ms == max(sample_wind_output.sustained_ms)

    def test_to_dict_encodes_threshold_keys_as_strings(self, sample_wind_output):
        d = sample_wind_output.to_dict()
        # JSON object keys must be strings — the type takes care of this.
        for k in d["duration_above_ms"].keys():
            assert isinstance(k, str)

    def test_roundtrip(self, sample_wind_output):
        d = sample_wind_output.to_dict()
        restored = WindFieldOutput.from_dict(d)
        assert restored == sample_wind_output

    def test_roundtrip_recovers_float_threshold_keys(self, sample_wind_output):
        d = sample_wind_output.to_dict()
        restored = WindFieldOutput.from_dict(d)
        # After round-trip threshold keys must be float again so callers can
        # look up duration_above_ms[17.5] without converting.
        for k in restored.duration_above_ms.keys():
            assert isinstance(k, float)
