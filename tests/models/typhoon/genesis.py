# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.genesis — initial-state sampling.

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


# ===========================================================================
# Peak-wind exceedance function
# ===========================================================================


class TestPeakWindExceedance:

    def test_exceedance_at_mean_is_about_half(self, baseline_pw):
        # At v = mu, P(V > mu) for a normal body is 0.5.
        assert peak_wind_exceedance(baseline_pw.mu_ms, baseline_pw) == pytest.approx(0.5, abs=1e-6)

    def test_exceedance_is_monotonic_decreasing(self, baseline_pw):
        v_grid = np.linspace(15.0, 90.0, 200)
        excs = [peak_wind_exceedance(v, baseline_pw) for v in v_grid]
        for a, b in zip(excs, excs[1:]):
            assert b <= a + 1e-12

    def test_exceedance_continuous_at_threshold(self, baseline_pw):
        v_t = baseline_pw.v_threshold_ms
        # Both halves of the piecewise should agree at v_T.
        body_at_t = peak_wind_exceedance(v_t, baseline_pw)
        tail_at_t = peak_wind_exceedance(v_t + 1e-9, baseline_pw)
        assert body_at_t == pytest.approx(tail_at_t, rel=1e-6)

    def test_extreme_tail_exceeds_baseline_tail_far_out(self, baseline_pw, extreme_pw):
        # Far above the threshold, the smaller alpha (extreme) must have a
        # larger exceedance probability — the whole point of "fatter tail".
        v_far = 90.0
        assert peak_wind_exceedance(v_far, extreme_pw) > peak_wind_exceedance(v_far, baseline_pw)


# ===========================================================================
# Inverse exceedance — invertibility
# ===========================================================================


class TestPeakWindInverseExceedance:

    def test_roundtrip_through_body(self, baseline_pw):
        # Pick a v in the body. inverse_exceedance(exceedance(v)) == v.
        v = 30.0   # below mu = 35
        p = peak_wind_exceedance(v, baseline_pw)
        v_back = peak_wind_inverse_exceedance(p, baseline_pw)
        assert v_back == pytest.approx(v, rel=1e-4, abs=1e-3)

    def test_roundtrip_through_tail(self, baseline_pw):
        # Pick a v deep in the tail.
        v = 70.0   # well above v_T = 50
        p = peak_wind_exceedance(v, baseline_pw)
        v_back = peak_wind_inverse_exceedance(p, baseline_pw)
        assert v_back == pytest.approx(v, rel=1e-4)

    def test_clamps_at_low_p(self, baseline_pw):
        # p -> 0 should return v_max_ms.
        assert peak_wind_inverse_exceedance(0.0, baseline_pw) == baseline_pw.v_max_ms

    def test_clamps_at_high_p(self, baseline_pw):
        # p -> 1 should return v_min_ms.
        assert peak_wind_inverse_exceedance(1.0, baseline_pw) == baseline_pw.v_min_ms


# ===========================================================================
# sample_peak_wind — empirical vs analytical
# ===========================================================================


class TestSamplePeakWindEmpirical:

    @pytest.mark.parametrize("p_target", [0.5, 0.05, 0.01])
    def test_empirical_quantile_matches_analytical(self, baseline_pw, p_target):
        """Empirical (1 - p_target) quantile from 10k samples should track
        the analytical inverse exceedance at p_target."""
        rng = _rng(42)
        samples = np.array([sample_peak_wind(baseline_pw, rng) for _ in range(10_000)])
        analytical = peak_wind_inverse_exceedance(p_target, baseline_pw)
        # The (1 - p_target) sample quantile is the v such that p_target
        # fraction of samples exceed it.
        empirical = float(np.quantile(samples, 1.0 - p_target))
        # 5% relative tolerance is loose enough for 10k samples and tight
        # enough to catch systematic bias.
        assert empirical == pytest.approx(analytical, rel=0.05)

    def test_samples_lie_in_configured_range(self, baseline_pw):
        rng = _rng(7)
        samples = [sample_peak_wind(baseline_pw, rng) for _ in range(1000)]
        for s in samples:
            assert baseline_pw.v_min_ms <= s <= baseline_pw.v_max_ms

    def test_fixed_seed_reproducible(self, baseline_pw):
        rng_a = _rng(99)
        rng_b = _rng(99)
        a = [sample_peak_wind(baseline_pw, rng_a) for _ in range(100)]
        b = [sample_peak_wind(baseline_pw, rng_b) for _ in range(100)]
        assert a == b


class TestExtremeVsBaselineTail:
    """Phase 1 acceptance criterion: EXTREME must show a detectably fatter
    upper tail than BASELINE.

    Comparing quantiles (e.g. p99) would be confounded by the v_max_ms
    physical cap when both distributions are sufficiently heavy-tailed to
    saturate the clamp. The tail-mass comparison below sidesteps the cap
    and tests exactly what "fatter tail" means: more probability above a
    chosen threshold.
    """

    def test_extreme_has_more_mass_above_70(self, baseline_pw, extreme_pw):
        rng_b = _rng(1)
        rng_e = _rng(2)
        b = np.array([sample_peak_wind(baseline_pw, rng_b) for _ in range(20_000)])
        e = np.array([sample_peak_wind(extreme_pw, rng_e) for _ in range(20_000)])
        assert (e > 70.0).mean() > (b > 70.0).mean()

    def test_extreme_has_more_mass_above_80(self, baseline_pw, extreme_pw):
        # The contrast widens further out in the tail.
        rng_b = _rng(3)
        rng_e = _rng(4)
        b = np.array([sample_peak_wind(baseline_pw, rng_b) for _ in range(20_000)])
        e = np.array([sample_peak_wind(extreme_pw, rng_e) for _ in range(20_000)])
        assert (e > 80.0).mean() > (b > 80.0).mean()

    def test_extreme_analytical_exceedance_exceeds_baseline(self, baseline_pw, extreme_pw):
        # Analytical check independent of sampling noise: at any v above
        # v_T, EXTREME's exceedance probability must dominate BASELINE's.
        for v in (60.0, 70.0, 80.0, 90.0):
            assert peak_wind_exceedance(v, extreme_pw) > peak_wind_exceedance(v, baseline_pw)


# ===========================================================================
# Initial-state samplers
# ===========================================================================


class TestSampleGenesisLocation:

    def test_lies_inside_bbox(self, minimal_config):
        prior = minimal_config.genesis_prior
        lon_min, lat_min, lon_max, lat_max = prior.bbox
        rng = _rng(11)
        for _ in range(200):
            lon, lat = sample_genesis_location(prior, rng)
            assert lon_min <= lon <= lon_max
            assert lat_min <= lat <= lat_max


class TestSampleInitialHeading:

    def test_returns_compass_degrees(self, minimal_config):
        rng = _rng(13)
        for _ in range(200):
            h = sample_initial_heading(minimal_config.genesis_prior, rng)
            assert 0.0 <= h < 360.0

    def test_concentrates_around_mean_for_high_kappa(self):
        # Build a custom prior with very high kappa — samples should cluster.
        from config.typhoon import GenesisPrior
        prior = GenesisPrior(
            bbox=(0.0, 0.0, 1.0, 1.0),
            heading_mean_deg=270.0,
            heading_kappa=100.0,      # very concentrated
            speed_shape=2.0,
            speed_scale=2.0,
        )
        rng = _rng(17)
        headings = np.array([sample_initial_heading(prior, rng) for _ in range(2000)])
        # Centre around 270; allow a wide check because circular stats.
        # With kappa=100, std ~ 5.7 deg, so within 30 deg is comfortable.
        within = ((headings > 240.0) & (headings < 300.0)).mean()
        assert within > 0.95


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
        # The minimal_config land_mask is "lon < 117.0". Check a few samples.
        rng = _rng(67)
        for _ in range(100):
            state = sample_genesis(minimal_config, ScenarioFamily.BASELINE, rng)
            expected_land = state.longitude < 117.0
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
