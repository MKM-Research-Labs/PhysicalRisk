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

"""Tests for config.typhoon — the parameter schema for the typhoon model.

These tests are catchment-agnostic. They verify that each parameter
dataclass can be constructed, that default values are internally
consistent, and that a complete CatchmentTyphoonConfig can be assembled
from neutral test data.

Tests for any specific catchment's tropical-cyclone configuration live
under tests/catch/<id>/.
"""

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


# ===========================================================================
# Enum shape
# ===========================================================================


class TestRegimeClass:

    def test_five_regimes_exist(self):
        assert len(RegimeClass) == 5

    def test_values_are_lower_snake_case(self):
        for r in RegimeClass:
            assert r.value == r.value.lower()
            assert " " not in r.value

    @pytest.mark.parametrize("regime", list(RegimeClass))
    def test_roundtrip_via_value(self, regime):
        assert RegimeClass(regime.value) is regime


class TestScenarioFamily:

    def test_five_families_exist(self):
        assert len(ScenarioFamily) == 5

    @pytest.mark.parametrize("scenario", list(ScenarioFamily))
    def test_roundtrip_via_value(self, scenario):
        assert ScenarioFamily(scenario.value) is scenario


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
# CatchmentTyphoonConfig assembly from neutral test data
# ===========================================================================


@pytest.fixture
def neutral_config():
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


class TestNeutralConfig:

    def test_construction(self, neutral_config):
        assert isinstance(neutral_config, CatchmentTyphoonConfig)
        assert neutral_config.catchment_id == "test"

    def test_all_scenario_families_covered(self, neutral_config):
        for s in ScenarioFamily:
            assert s in neutral_config.peak_wind

    def test_all_regimes_covered_in_motion(self, neutral_config):
        for r in RegimeClass:
            assert r in neutral_config.motion.mean_speed_kmh
            assert r in neutral_config.motion.mean_heading_deg

    def test_land_mask_is_callable(self, neutral_config):
        assert callable(neutral_config.land_mask)
        assert neutral_config.land_mask(115.0, 21.0) is True
        assert neutral_config.land_mask(120.0, 18.0) is False

    def test_property_points_non_empty(self, neutral_config):
        assert len(neutral_config.property_points) >= 1

    def test_default_output_thresholds_ascending(self, neutral_config):
        thresholds = neutral_config.output_thresholds_ms
        assert thresholds == sorted(thresholds)
        assert all(t > 0 for t in thresholds)

    def test_default_horizon_is_one_week(self, neutral_config):
        assert neutral_config.horizon_hours == 168.0
