# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.parameters — parameter dataclass shape.

These tests are catchment-agnostic. They verify that each parameter
dataclass can be constructed, that default values are internally
consistent, and that a complete CatchmentTyphoonConfig can be assembled
from neutral test data.

Catchment-specific config files are tested separately under
tests/catch/<catchment_id>/.
"""

import math

from models.typhoon.data_structures import RegimeClass, ScenarioFamily
from models.typhoon.parameters import (
    CatchmentTyphoonConfig,
    GenesisPrior,
    IntensityParams,
    MotionParams,
    PeakWindParams,
    PlausibilityWeights,
    SizeParams,
    WindFieldParams,
)


# ===========================================================================
# Parameter dataclass defaults
# ===========================================================================


class TestIntensityParamsDefaults:

    def test_construct_with_defaults(self):
        p = IntensityParams()
        assert p.k_land_per_hour > 0
        assert p.sigma_ms_per_hour > 0

    def test_drift_can_be_zero(self):
        # Neutral drift is the Phase 1 default — explicit zero must be valid.
        p = IntensityParams(drift_ms_per_hour=0.0)
        assert p.drift_ms_per_hour == 0.0


class TestSizeParamsDefaults:

    def test_construct_with_defaults(self):
        p = SizeParams()
        assert p.mean_reversion_rate > 0

    def test_r_outer_intercept_larger_than_r_max(self):
        # In log-space, R_outer baseline must exceed R_max baseline so the
        # invariant R_max < R_outer holds at climatological mean.
        p = SizeParams()
        assert math.exp(p.r_outer_intercept_log_km) > math.exp(p.r_max_intercept_log_km)


class TestWindFieldParamsDefaults:

    def test_alpha_eye_is_fractional(self):
        p = WindFieldParams()
        assert 0.0 < p.alpha_eye < 1.0

    def test_outer_shape_positive(self):
        p = WindFieldParams()
        assert p.outer_shape_p > 0

    def test_outer_anchor_below_typical_v_max(self):
        # The anchor wind at R_outer must be well below typical V_max so the
        # outer decay calibration has room to operate.
        p = WindFieldParams()
        assert p.v_outer_ref_ms < 30.0

    def test_land_reduction_no_stronger_than_sea(self):
        p = WindFieldParams()
        assert 0.0 <= p.rho_surf_land <= p.rho_surf_sea


class TestPlausibilityDefaultsArePhase1Loose:

    def test_all_weights_loose(self):
        # Phase 1 priority is breadth; defaults must not be aggressive.
        p = PlausibilityWeights()
        assert p.heading_jump_weight <= 0.5
        assert p.speed_jump_weight <= 0.5
        assert p.basin_boundary_weight <= 0.5
        assert p.regime_consistency_weight <= 0.5


class TestPeakWindParamsConstruction:

    def test_simple_construction(self):
        p = PeakWindParams(mu_ms=40.0, sigma_ms=12.0, v_threshold_ms=55.0, alpha=2.0)
        assert p.mu_ms == 40.0
        assert p.v_min_ms < p.mu_ms < p.v_max_ms

    def test_fatter_tail_smaller_alpha(self):
        # By construction, smaller alpha is a fatter tail.
        thin = PeakWindParams(mu_ms=30.0, sigma_ms=10.0, v_threshold_ms=50.0, alpha=3.0)
        fat = PeakWindParams(mu_ms=30.0, sigma_ms=10.0, v_threshold_ms=50.0, alpha=1.2)
        assert fat.alpha < thin.alpha


class TestGenesisPriorConstruction:

    def test_bbox_ordering(self):
        g = GenesisPrior(
            bbox=(115.0, 14.0, 125.0, 22.0),
            heading_mean_deg=270.0,
            heading_kappa=5.0,
            speed_shape=4.0,
            speed_scale=4.0,
        )
        lon_min, lat_min, lon_max, lat_max = g.bbox
        assert lon_min < lon_max
        assert lat_min < lat_max

    def test_empty_weights_acceptable_at_construction(self):
        # Catchments may construct piecewise — empty mixture dicts must not
        # error at construction time. Validation happens at sample time.
        g = GenesisPrior(
            bbox=(0.0, 0.0, 1.0, 1.0),
            heading_mean_deg=0.0,
            heading_kappa=1.0,
            speed_shape=2.0,
            speed_scale=2.0,
        )
        assert g.regime_weights == {}
        assert g.scenario_mix == {}


# ===========================================================================
# CatchmentTyphoonConfig assembly via the neutral fixture
# ===========================================================================


class TestMinimalConfig:

    def test_construction(self, minimal_config):
        assert isinstance(minimal_config, CatchmentTyphoonConfig)
        assert minimal_config.catchment_id == "test"

    def test_all_scenario_families_covered(self, minimal_config):
        for s in ScenarioFamily:
            assert s in minimal_config.peak_wind

    def test_all_regimes_covered_in_motion(self, minimal_config):
        for r in RegimeClass:
            assert r in minimal_config.motion.mean_speed_kmh
            assert r in minimal_config.motion.mean_heading_deg

    def test_land_mask_is_callable(self, minimal_config):
        assert callable(minimal_config.land_mask)
        # Bounds match the lambda in the fixture (lon < 117.0).
        assert minimal_config.land_mask(115.0, 21.0) is True
        assert minimal_config.land_mask(120.0, 18.0) is False

    def test_property_points_non_empty(self, minimal_config):
        assert len(minimal_config.property_points) >= 1

    def test_default_output_thresholds_ascending(self, minimal_config):
        thresholds = minimal_config.output_thresholds_ms
        assert thresholds == sorted(thresholds)
        assert all(t > 0 for t in thresholds)

    def test_default_horizon_is_one_week(self, minimal_config):
        assert minimal_config.horizon_hours == 168.0
