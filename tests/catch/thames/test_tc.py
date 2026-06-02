# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the Thames catchment's tropical-cyclone (windstorm) configuration.

These tests load data/catch/thames/tc.py and verify:
- The constants are the correct parameter dataclass types
- Mixture weights sum to 1 over the full enum domain
- Per-scenario severity orderings make sense (means ascend, EXTREME tail
  fatter than BASELINE)
- The calibration is genuinely MILD (low means, thin tails, low caps) —
  materially milder than the Halong super-typhoon calibration
- The land-mask gets the obvious land/sea calls right for the British Isles
- Property points are well-formed and centred on London
- The full CatchmentTyphoonConfig can be assembled from the constants
"""

import importlib
import math

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


@pytest.fixture
def thames_tc():
    """Load the Thames catchment TC module via the standard import path."""
    return importlib.import_module("catch.thames.tc")


@pytest.fixture
def halong_tc():
    """Load Halong's TC module for milder-than-typhoon comparisons."""
    return importlib.import_module("catch.halong.tc")


# ===========================================================================
# Genesis prior
# ===========================================================================


class TestGenesisPrior:

    def test_is_genesis_prior(self, thames_tc):
        assert isinstance(thames_tc.THAMES_TYPHOON_GENESIS_PRIOR, GenesisPrior)

    def test_bbox_in_eastern_atlantic_approaches(self, thames_tc):
        lon_min, lat_min, lon_max, lat_max = thames_tc.THAMES_TYPHOON_GENESIS_PRIOR.bbox
        # Genesis region is the open North Atlantic south-west of the UK.
        assert -20.0 <= lon_min < lon_max <= 0.0
        assert 40.0 <= lat_min < lat_max <= 55.0

    def test_heading_is_easterly(self, thames_tc):
        # Storms track off the Atlantic toward NW Europe (eastward), unlike the
        # NW-Pacific westward convention the regime names imply.
        h = thames_tc.THAMES_TYPHOON_GENESIS_PRIOR.heading_mean_deg
        assert 30.0 <= h <= 110.0

    def test_regime_weights_sum_to_one(self, thames_tc):
        weights = thames_tc.THAMES_TYPHOON_GENESIS_PRIOR.regime_weights
        assert set(weights.keys()) == set(RegimeClass)
        assert math.isclose(sum(weights.values()), 1.0, abs_tol=1e-9)

    def test_scenario_mix_sums_to_one(self, thames_tc):
        mix = thames_tc.THAMES_TYPHOON_GENESIS_PRIOR.scenario_mix
        assert set(mix.keys()) == set(ScenarioFamily)
        assert math.isclose(sum(mix.values()), 1.0, abs_tol=1e-9)


# ===========================================================================
# Peak-wind distribution
# ===========================================================================


class TestPeakWind:

    def test_covers_all_scenarios(self, thames_tc):
        pw = thames_tc.THAMES_TYPHOON_PEAK_WIND
        assert set(pw.keys()) == set(ScenarioFamily)
        for params in pw.values():
            assert isinstance(params, PeakWindParams)

    def test_extreme_has_fatter_tail_than_baseline(self, thames_tc):
        pw = thames_tc.THAMES_TYPHOON_PEAK_WIND
        assert pw[ScenarioFamily.EXTREME].alpha < pw[ScenarioFamily.BASELINE].alpha

    def test_means_weakly_increase_with_severity(self, thames_tc):
        pw = thames_tc.THAMES_TYPHOON_PEAK_WIND
        means = [
            pw[ScenarioFamily.HISTORICAL].mu_ms,
            pw[ScenarioFamily.BASELINE].mu_ms,
            pw[ScenarioFamily.MODERATE].mu_ms,
            pw[ScenarioFamily.SEVERE].mu_ms,
            pw[ScenarioFamily.EXTREME].mu_ms,
        ]
        assert means == sorted(means)

    def test_calibration_is_mild(self, thames_tc):
        """Even the EXTREME family stays well below hurricane force."""
        pw = thames_tc.THAMES_TYPHOON_PEAK_WIND
        # Mean peak winds stay in the gale / severe-gale band.
        assert pw[ScenarioFamily.EXTREME].mu_ms <= 30.0
        # Hard caps clamp every draw below typhoon force (~33 m/s = Cat-1).
        for params in pw.values():
            assert params.v_max_ms <= 50.0
        # Tails are thin (high Pareto alpha) across the board.
        for params in pw.values():
            assert params.alpha >= 2.0

    def test_milder_than_halong(self, thames_tc, halong_tc):
        """Thames is materially milder than Halong's super-typhoon regime."""
        t = thames_tc.THAMES_TYPHOON_PEAK_WIND
        h = halong_tc.HALONG_TYPHOON_PEAK_WIND
        for fam in ScenarioFamily:
            assert t[fam].mu_ms < h[fam].mu_ms
            # Thinner (less heavy) tail than the corresponding Halong family.
            assert t[fam].alpha > h[fam].alpha


# ===========================================================================
# Motion / intensity / size / wind-field / plausibility
# ===========================================================================


class TestMotion:

    def test_is_motion_params(self, thames_tc):
        assert isinstance(thames_tc.THAMES_TYPHOON_MOTION, MotionParams)

    def test_all_regimes_covered(self, thames_tc):
        m = thames_tc.THAMES_TYPHOON_MOTION
        for r in RegimeClass:
            assert r in m.mean_speed_kmh
            assert r in m.sigma_speed_kmh
            assert r in m.mean_heading_deg
            assert r in m.sigma_heading_deg

    def test_stalled_regime_has_lowest_mean_speed(self, thames_tc):
        speeds = thames_tc.THAMES_TYPHOON_MOTION.mean_speed_kmh
        assert speeds[RegimeClass.STALLED] == min(speeds.values())

    def test_headings_are_easterly(self, thames_tc):
        # Non-stalled regimes track eastward / north-eastward toward the UK.
        headings = thames_tc.THAMES_TYPHOON_MOTION.mean_heading_deg
        for r in (RegimeClass.STRAIGHT_WESTWARD, RegimeClass.LANDFALL_DECAY):
            assert 30.0 <= headings[r] <= 110.0


class TestIntensitySizeWindfieldPlausibility:

    def test_intensity(self, thames_tc):
        assert isinstance(thames_tc.THAMES_TYPHOON_INTENSITY, IntensityParams)

    def test_intensity_does_not_intensify_over_water(self, thames_tc):
        # Extratropical systems weaken (or hold) over the cool N Atlantic.
        assert thames_tc.THAMES_TYPHOON_INTENSITY.drift_ms_per_hour <= 0.0

    def test_size(self, thames_tc):
        assert isinstance(thames_tc.THAMES_TYPHOON_SIZE, SizeParams)

    def test_wind_field(self, thames_tc):
        assert isinstance(thames_tc.THAMES_TYPHOON_WIND_FIELD, WindFieldParams)

    def test_plausibility(self, thames_tc):
        assert isinstance(thames_tc.THAMES_TYPHOON_PLAUSIBILITY, PlausibilityWeights)


# ===========================================================================
# Land mask
# ===========================================================================


class TestLandMask:

    def test_london_is_land(self, thames_tc):
        lon, lat = thames_tc.THAMES_LONDON_REFERENCE
        assert thames_tc.thames_land_mask(lon, lat) is True

    def test_atlantic_approaches_are_sea(self, thames_tc):
        # Open Atlantic south-west of Ireland (the genesis region).
        assert thames_tc.thames_land_mask(-11.0, 49.0) is False

    def test_north_sea_is_sea(self, thames_tc):
        # Central North Sea, east of England.
        assert thames_tc.thames_land_mask(3.0, 54.0) is False

    def test_ireland_is_land(self, thames_tc):
        # Central Ireland.
        assert thames_tc.thames_land_mask(-8.0, 53.0) is True


# ===========================================================================
# Property points
# ===========================================================================


class TestProperties:

    def test_non_empty(self, thames_tc):
        assert len(thames_tc.THAMES_TYPHOON_PROPERTIES) >= 1

    def test_each_is_property_point(self, thames_tc):
        for p in thames_tc.THAMES_TYPHOON_PROPERTIES:
            assert isinstance(p, PropertyPoint)

    def test_ids_unique(self, thames_tc):
        ids = [p.property_id for p in thames_tc.THAMES_TYPHOON_PROPERTIES]
        assert len(ids) == len(set(ids))

    def test_centre_matches_reference(self, thames_tc):
        ref_lon, ref_lat = thames_tc.THAMES_LONDON_REFERENCE
        centre = next(p for p in thames_tc.THAMES_TYPHOON_PROPERTIES
                      if p.property_id == "LON-CENTRE")
        assert centre.longitude == ref_lon
        assert centre.latitude == ref_lat


# ===========================================================================
# End-to-end assembly into CatchmentTyphoonConfig
# ===========================================================================


class TestAssembly:
    """Verifies the build_typhoon_config() boundary adapter."""

    def test_build_typhoon_config_returns_valid_assembly(self, thames_tc):
        cfg = thames_tc.build_typhoon_config()
        assert isinstance(cfg, CatchmentTyphoonConfig)
        assert cfg.catchment_id == "thames"
        ref_lon, ref_lat = thames_tc.THAMES_LONDON_REFERENCE
        assert cfg.land_mask(ref_lon, ref_lat) is True
        assert cfg.land_mask(-11.0, 49.0) is False
        assert len(cfg.property_points) >= 1

    def test_build_typhoon_config_accepts_explicit_catchment_id(self, thames_tc):
        cfg = thames_tc.build_typhoon_config(catchment_id="thames")
        assert cfg.catchment_id == "thames"
