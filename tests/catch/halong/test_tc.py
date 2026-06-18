# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for the Halong catchment's tropical-cyclone configuration.

These tests load data/catch/halong/tc.py and verify:
- The constants are the correct parameter dataclass types
- Mixture weights sum to 1 over the full enum domain
- Per-scenario severity orderings make sense (means ascend, tails fatten)
- The land-mask gets the obvious land/sea calls right
- Property points are well-formed
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
def halong_tc():
    """Load the Halong catchment TC module via the standard import path."""
    return importlib.import_module("catch.halong.tc")


# ===========================================================================
# Genesis prior
# ===========================================================================


class TestGenesisPrior:

    def test_is_genesis_prior(self, halong_tc):
        assert isinstance(halong_tc.HALONG_TYPHOON_GENESIS_PRIOR, GenesisPrior)

    def test_bbox_inside_scs(self, halong_tc):
        lon_min, lat_min, lon_max, lat_max = halong_tc.HALONG_TYPHOON_GENESIS_PRIOR.bbox
        # Must lie inside the SCS genesis region for storms approaching
        # northern Vietnam.
        assert 105.0 <= lon_min < lon_max <= 125.0
        assert 5.0 <= lat_min < lat_max <= 25.0

    def test_regime_weights_sum_to_one(self, halong_tc):
        weights = halong_tc.HALONG_TYPHOON_GENESIS_PRIOR.regime_weights
        assert set(weights.keys()) == set(RegimeClass)
        assert math.isclose(sum(weights.values()), 1.0, abs_tol=1e-9)

    def test_scenario_mix_sums_to_one(self, halong_tc):
        mix = halong_tc.HALONG_TYPHOON_GENESIS_PRIOR.scenario_mix
        assert set(mix.keys()) == set(ScenarioFamily)
        assert math.isclose(sum(mix.values()), 1.0, abs_tol=1e-9)


# ===========================================================================
# Peak-wind distribution
# ===========================================================================


class TestPeakWind:

    def test_covers_all_scenarios(self, halong_tc):
        pw = halong_tc.HALONG_TYPHOON_PEAK_WIND
        assert set(pw.keys()) == set(ScenarioFamily)
        for params in pw.values():
            assert isinstance(params, PeakWindParams)

    def test_extreme_has_fatter_tail_than_baseline(self, halong_tc):
        pw = halong_tc.HALONG_TYPHOON_PEAK_WIND
        assert pw[ScenarioFamily.EXTREME].alpha < pw[ScenarioFamily.BASELINE].alpha

    def test_means_weakly_increase_with_severity(self, halong_tc):
        pw = halong_tc.HALONG_TYPHOON_PEAK_WIND
        means = [
            pw[ScenarioFamily.HISTORICAL].mu_ms,
            pw[ScenarioFamily.BASELINE].mu_ms,
            pw[ScenarioFamily.MODERATE].mu_ms,
            pw[ScenarioFamily.SEVERE].mu_ms,
            pw[ScenarioFamily.EXTREME].mu_ms,
        ]
        assert means == sorted(means)


# ===========================================================================
# Motion / intensity / size / wind-field / plausibility
# ===========================================================================


class TestMotion:

    def test_is_motion_params(self, halong_tc):
        assert isinstance(halong_tc.HALONG_TYPHOON_MOTION, MotionParams)

    def test_all_regimes_covered(self, halong_tc):
        m = halong_tc.HALONG_TYPHOON_MOTION
        for r in RegimeClass:
            assert r in m.mean_speed_kmh
            assert r in m.sigma_speed_kmh
            assert r in m.mean_heading_deg
            assert r in m.sigma_heading_deg

    def test_stalled_regime_has_lowest_mean_speed(self, halong_tc):
        speeds = halong_tc.HALONG_TYPHOON_MOTION.mean_speed_kmh
        assert speeds[RegimeClass.STALLED] == min(speeds.values())


class TestIntensitySizeWindfieldPlausibility:

    def test_intensity(self, halong_tc):
        assert isinstance(halong_tc.HALONG_TYPHOON_INTENSITY, IntensityParams)

    def test_size(self, halong_tc):
        assert isinstance(halong_tc.HALONG_TYPHOON_SIZE, SizeParams)

    def test_wind_field(self, halong_tc):
        assert isinstance(halong_tc.HALONG_TYPHOON_WIND_FIELD, WindFieldParams)

    def test_plausibility(self, halong_tc):
        assert isinstance(halong_tc.HALONG_TYPHOON_PLAUSIBILITY, PlausibilityWeights)


# ===========================================================================
# Land mask
# ===========================================================================


class TestLandMask:

    def test_hanoi_is_land(self, halong_tc):
        lon, lat = halong_tc.HALONG_HANOI_REFERENCE
        assert halong_tc.halong_land_mask(lon, lat) is True

    def test_gulf_of_tonkin_is_sea(self, halong_tc):
        # Mid-Gulf of Tonkin, east of the Vietnamese coastline.
        assert halong_tc.halong_land_mask(108.0, 20.0) is False

    def test_open_scs_is_sea(self, halong_tc):
        # Open SCS east of Hainan.
        assert halong_tc.halong_land_mask(115.0, 18.0) is False

    def test_hainan_is_land(self, halong_tc):
        # Hainan island centre.
        assert halong_tc.halong_land_mask(109.5, 19.0) is True


# ===========================================================================
# Property points
# ===========================================================================


class TestProperties:

    def test_non_empty(self, halong_tc):
        assert len(halong_tc.HALONG_TYPHOON_PROPERTIES) >= 1

    def test_each_is_property_point(self, halong_tc):
        for p in halong_tc.HALONG_TYPHOON_PROPERTIES:
            assert isinstance(p, PropertyPoint)

    def test_ids_unique(self, halong_tc):
        ids = [p.property_id for p in halong_tc.HALONG_TYPHOON_PROPERTIES]
        assert len(ids) == len(set(ids))

    def test_centre_matches_reference(self, halong_tc):
        ref_lon, ref_lat = halong_tc.HALONG_HANOI_REFERENCE
        centre = next(p for p in halong_tc.HALONG_TYPHOON_PROPERTIES if p.property_id == "HAN-CENTRE")
        assert centre.longitude == ref_lon
        assert centre.latitude == ref_lat


# ===========================================================================
# End-to-end assembly into CatchmentTyphoonConfig
# ===========================================================================


class TestAssembly:
    """Verifies the build_typhoon_config() boundary adapter."""

    def test_build_typhoon_config_returns_valid_assembly(self, halong_tc):
        cfg = halong_tc.build_typhoon_config()
        assert cfg.catchment_id == "halong"
        ref_lon, ref_lat = halong_tc.HALONG_HANOI_REFERENCE
        assert cfg.land_mask(ref_lon, ref_lat) is True
        assert cfg.land_mask(110.0, 18.0) is False
        assert len(cfg.property_points) >= 1

    def test_build_typhoon_config_accepts_explicit_catchment_id(self, halong_tc):
        # The orchestrator passes config.catchment_id through to the builder
        # so the resulting CatchmentTyphoonConfig.catchment_id matches the
        # active catchment exactly.
        cfg = halong_tc.build_typhoon_config(catchment_id="halong")
        assert cfg.catchment_id == "halong"
