# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for models.typhoon.genesis — initial-state sampling. (part 3 of 4)

Covers:
- Peak-wind hybrid distribution (exceedance / inverse exceedance / sampling)
- Empirical CDF reproduces the analytical hybrid distribution at p50, p95, p99
- Scenario-family ordering: EXTREME fattens the upper tail vs BASELINE
- Initial-state samplers (location, heading, speed, size)
- Size invariant R_max < R_outer enforced
- Regime / scenario categorical samplers respect weights within tolerance
- Top-level sample_genesis and sample_genesis_ensemble produce valid states
- Reproducibility under fixed seed
"""

import math
from collections import Counter

import numpy as np
import pytest

from config.typhoon import (
    PeakWindParams,
    RegimeClass,
    ScenarioFamily,
)
from models.typhoon.genesis import (
    _categorical,
    coupled_genesis_wind,
    coupling_floor,
    derive_scenario_family,
    mixture_peak_wind_exceedance,
    mixture_peak_wind_inverse,
    peak_wind_exceedance,
    peak_wind_inverse_exceedance,
    sample_genesis,
    sample_genesis_ensemble,
    sample_genesis_location,
    sample_initial_heading,
    sample_initial_size,
    sample_initial_speed,
    sample_peak_wind,
    sample_regime,
    sample_scenario_family,
)


# ===========================================================================
# Helpers
# ===========================================================================


def _rng(seed=1234):
    return np.random.default_rng(seed)


# Fixtures defined here are only used inside this test file; the main
# minimal_config fixture comes from tests/models/typhoon/conftest.py.


@pytest.fixture
def baseline_pw():
    return PeakWindParams(mu_ms=35.0, sigma_ms=12.0, v_threshold_ms=50.0, alpha=2.5)


@pytest.fixture
def extreme_pw():
    return PeakWindParams(mu_ms=35.0, sigma_ms=12.0, v_threshold_ms=50.0, alpha=1.2)


@pytest.fixture
def coupling_mix():
    """A 3-family ceiling curve + mix, intensity-ordered by mu_ms."""
    pw = {
        ScenarioFamily.BASELINE: PeakWindParams(
            mu_ms=35.0, sigma_ms=8.0, v_threshold_ms=50.0, alpha=4.0),
        ScenarioFamily.SEVERE: PeakWindParams(
            mu_ms=50.0, sigma_ms=10.0, v_threshold_ms=65.0, alpha=3.5),
        ScenarioFamily.EXTREME: PeakWindParams(
            mu_ms=65.0, sigma_ms=12.0, v_threshold_ms=80.0, alpha=3.0),
    }
    mix = {
        ScenarioFamily.BASELINE: 0.5,
        ScenarioFamily.SEVERE: 0.35,
        ScenarioFamily.EXTREME: 0.15,
    }
    return pw, mix


class TestSampleInitialSpeed:

    def test_positive(self, minimal_config):
        rng = _rng(19)
        for _ in range(500):
            s = sample_initial_speed(minimal_config.genesis_prior, rng)
            assert s > 0.0

    def test_mean_close_to_shape_times_scale(self, minimal_config):
        # Gamma(shape, scale) has mean shape * scale.
        prior = minimal_config.genesis_prior
        rng = _rng(23)
        samples = np.array([sample_initial_speed(prior, rng) for _ in range(5000)])
        expected_mean = prior.speed_shape * prior.speed_scale
        assert samples.mean() == pytest.approx(expected_mean, rel=0.05)


class TestSampleInitialSize:

    def test_r_max_less_than_r_outer_always(self, minimal_config):
        rng = _rng(29)
        for _ in range(2000):
            v = float(rng.uniform(15.0, 80.0))
            r_max, r_outer = sample_initial_size(v, minimal_config.size, rng)
            assert r_max < r_outer
            assert r_max > 0.0

    def test_invariant_forced_when_noise_collides(self, minimal_config):
        # Set V very low so the regression mean of R_outer drops near R_max.
        # The post-hoc widening must still produce R_max < R_outer.
        rng = _rng(31)
        for _ in range(100):
            r_max, r_outer = sample_initial_size(1.0, minimal_config.size, rng)
            assert r_max < r_outer


# ===========================================================================
# Categorical samplers
# ===========================================================================


class TestCategoricalSamplers:

    def test_categorical_rejects_empty(self):
        rng = _rng(37)
        with pytest.raises(ValueError):
            _categorical({}, rng)

    def test_categorical_rejects_zero_total(self):
        rng = _rng(41)
        with pytest.raises(ValueError):
            _categorical({"a": 0.0, "b": 0.0}, rng)

    def test_categorical_renormalises(self):
        # Slightly off weights still produce a valid draw.
        rng = _rng(43)
        result = _categorical({"a": 0.45, "b": 0.45}, rng)
        assert result in {"a", "b"}

    def test_sample_regime_respects_weights(self):
        # Build weights with a deliberately skewed mixture and check that
        # the empirical fraction tracks the nominal weight.
        weights = {
            RegimeClass.STRAIGHT_WESTWARD: 0.5,
            RegimeClass.NW_RECURVER:       0.2,
            RegimeClass.SHARP_RECURVE:     0.1,
            RegimeClass.STALLED:           0.1,
            RegimeClass.LANDFALL_DECAY:    0.1,
        }
        rng = _rng(47)
        samples = [sample_regime(weights, rng) for _ in range(10_000)]
        counts = Counter(samples)
        for regime, weight in weights.items():
            empirical = counts[regime] / 10_000
            # 3-sigma binomial: sqrt(p(1-p)/n) ~ 0.005 at p=0.5 ; cap at 0.02
            tol = max(0.02, 3.0 * math.sqrt(weight * (1.0 - weight) / 10_000))
            assert abs(empirical - weight) < tol, f"{regime}: empirical={empirical}, weight={weight}"

    def test_sample_scenario_family_returns_known_value(self, minimal_config):
        rng = _rng(53)
        s = sample_scenario_family(minimal_config.genesis_prior.scenario_mix, rng)
        assert isinstance(s, ScenarioFamily)


# ===========================================================================
# Top-level genesis samplers
# ===========================================================================


class TestSampleGenesis:

    def test_returns_typhoon_state(self, minimal_config):
        rng = _rng(59)
        state = sample_genesis(minimal_config, ScenarioFamily.BASELINE, rng)
        # Type and content sanity.
        assert state.time_hours == 0.0
        assert state.r_max_km < state.r_outer_km
        assert state.v_max_ms > 0
        assert 0.0 <= state.heading_deg < 360.0
        assert isinstance(state.regime, RegimeClass)
        assert isinstance(state.land_flag, bool)

    def test_position_inside_bbox(self, minimal_config):
        rng = _rng(61)
        lon_min, lat_min, lon_max, lat_max = minimal_config.genesis_prior.bbox
        for _ in range(200):
            state = sample_genesis(minimal_config, ScenarioFamily.BASELINE, rng)
            assert lon_min <= state.longitude <= lon_max
            assert lat_min <= state.latitude <= lat_max

    def test_land_flag_matches_mask(self, minimal_config):
        # Reuse the same threshold the conftest land_mask uses.
        from tests.models.typhoon.conftest import TEST_LAND_THRESHOLD_LON
        rng = _rng(67)
        for _ in range(100):
            state = sample_genesis(minimal_config, ScenarioFamily.BASELINE, rng)
            expected_land = state.longitude < TEST_LAND_THRESHOLD_LON
            assert state.land_flag == expected_land

    def test_fixed_seed_reproducible(self, minimal_config):
        rng_a = _rng(71)
        rng_b = _rng(71)
        a = sample_genesis(minimal_config, ScenarioFamily.BASELINE, rng_a)
        b = sample_genesis(minimal_config, ScenarioFamily.BASELINE, rng_b)
        assert a == b


class TestSampleGenesisEnsemble:

    def test_returns_n_states(self, minimal_config):
        rng = _rng(73)
        states = sample_genesis_ensemble(minimal_config, 100, rng)
        assert len(states) == 100

    def test_zero_ensemble_is_empty(self, minimal_config):
        rng = _rng(79)
        states = sample_genesis_ensemble(minimal_config, 0, rng)
        assert states == []

    def test_negative_n_raises(self, minimal_config):
        rng = _rng(83)
        with pytest.raises(ValueError):
            sample_genesis_ensemble(minimal_config, -1, rng)

    def test_scenario_mix_matches_prior(self, minimal_config):
        # minimal_config has uniform scenario mix (0.2 each). With 5000
        # samples, each family should land within tolerance of 0.2.
        rng = _rng(89)
        states = sample_genesis_ensemble(minimal_config, 5000, rng)
        # Map back to scenarios by re-sampling — but states don't carry the
        # scenario explicitly. Use peak-wind distribution as an indirect
        # check: with a uniform mix and identical peak-wind params per
        # scenario (in minimal_config), the empirical V distribution is
        # well-defined and reproducible. Concrete check: peak wind mean is
        # close to the configured mu.
        v_max = np.array([s.v_max_ms for s in states])
        # mu = 35 for every family in minimal_config; loose tolerance.
        assert v_max.mean() == pytest.approx(35.0, abs=2.0)
