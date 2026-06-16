# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.genesis — initial-state sampling. (part 4 of 4)

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


# ===========================================================================
# Storm -> wind coupling (coupling_spec.md §3.3, §4 — Stage 3)
# ===========================================================================


class TestCouplingFloor:

    def test_beta_one_is_comonotone(self):
        # f(q) = 1 - (1-q)^1 = q  -> band collapses to a point at q.
        for q in (0.1, 0.5, 0.9, 0.99):
            assert coupling_floor(q, 1.0) == pytest.approx(q, abs=1e-12)

    def test_beta_to_zero_is_pure_ceiling(self):
        # f(q) = 1 - (1-q)^0 = 0  -> floor collapses to 0 (widest band).
        for q in (0.1, 0.5, 0.9):
            assert coupling_floor(q, 1e-12) == pytest.approx(0.0, abs=1e-6)

    def test_floor_never_exceeds_ceiling(self):
        for q in np.linspace(0.0, 1.0, 21):
            assert coupling_floor(float(q), 0.52) <= float(q) + 1e-12

    def test_floor_monotone_increasing_in_q(self):
        qs = np.linspace(0.0, 1.0, 50)
        f = [coupling_floor(float(q), 0.52) for q in qs]
        assert all(f[i] <= f[i + 1] + 1e-12 for i in range(len(f) - 1))

    def test_reproduces_expert_anchors(self):
        # coupling_spec.md: 90th-pct storm -> ~70th-pct wind floor,
        # 99th -> ~90th, at beta ~ 0.52.
        assert coupling_floor(0.90, 0.52) == pytest.approx(0.70, abs=0.02)
        assert coupling_floor(0.99, 0.52) == pytest.approx(0.90, abs=0.02)

    def test_negative_beta_clamped(self):
        # Negative beta clamps to 0 -> pure ceiling, no error.
        assert coupling_floor(0.5, -1.0) == pytest.approx(0.0, abs=1e-9)


class TestMixtureSurvival:

    def test_monotone_decreasing(self, coupling_mix):
        pw, mix = coupling_mix
        vs = np.linspace(10.0, 100.0, 40)
        s = [mixture_peak_wind_exceedance(float(v), pw, mix) for v in vs]
        assert all(s[i] >= s[i + 1] - 1e-12 for i in range(len(s) - 1))

    def test_weights_renormalised_over_active_families(self, coupling_mix):
        pw, mix = coupling_mix
        # Drop one family from the mix -> still a proper survival curve in [0,1].
        partial = {ScenarioFamily.BASELINE: 0.5, ScenarioFamily.SEVERE: 0.5}
        s = mixture_peak_wind_exceedance(40.0, pw, partial)
        assert 0.0 <= s <= 1.0

    def test_inverse_round_trips(self, coupling_mix):
        pw, mix = coupling_mix
        for u in (0.05, 0.2, 0.5, 0.8, 0.95):
            v = mixture_peak_wind_inverse(u, pw, mix)
            assert mixture_peak_wind_exceedance(v, pw, mix) == pytest.approx(u, abs=1e-2)

    def test_inverse_clamps_out_of_range(self, coupling_mix):
        pw, mix = coupling_mix
        v_lo = min(pw[f].v_min_ms for f in pw)
        v_hi = max(pw[f].v_max_ms for f in pw)
        # u >= S(v_lo) clamps to v_lo; u <= S(v_hi) clamps to v_hi.
        assert mixture_peak_wind_inverse(1.0, pw, mix) == pytest.approx(v_lo)
        assert mixture_peak_wind_inverse(0.0, pw, mix) == pytest.approx(v_hi)

    def test_lower_u_gives_higher_wind(self, coupling_mix):
        pw, mix = coupling_mix
        assert mixture_peak_wind_inverse(0.05, pw, mix) > mixture_peak_wind_inverse(0.5, pw, mix)


class TestDeriveScenarioFamily:

    def test_high_wind_tags_extreme(self, coupling_mix):
        pw, mix = coupling_mix
        # Vmax near the EXTREME body mean (65) tags EXTREME.
        assert derive_scenario_family(66.0, pw, mix) == ScenarioFamily.EXTREME

    def test_low_wind_tags_baseline(self, coupling_mix):
        pw, mix = coupling_mix
        assert derive_scenario_family(34.0, pw, mix) == ScenarioFamily.BASELINE


class TestCoupledGenesisWind:

    def test_rho_w_never_below_one_minus_q(self, coupling_mix):
        # No low-rain/high-wind: rho_w <= q  <=>  u = 1-rho_w >= 1-q  <=>
        # Vmax <= S_cat^-1(1-q). The coupled Vmax must not exceed the ceiling.
        pw, mix = coupling_mix
        rng = np.random.default_rng(7)
        for q in (0.2, 0.5, 0.9):
            ceiling_v = mixture_peak_wind_inverse(1.0 - q, pw, mix)
            for _ in range(200):
                v, _sc = coupled_genesis_wind(q, 0.52, pw, mix, rng)
                assert v <= ceiling_v + 1e-6

    def test_higher_severity_gives_stronger_wind_on_average(self, coupling_mix):
        pw, mix = coupling_mix
        rng = np.random.default_rng(11)
        mean_lo = np.mean([coupled_genesis_wind(0.2, 0.52, pw, mix, rng)[0] for _ in range(300)])
        mean_hi = np.mean([coupled_genesis_wind(0.9, 0.52, pw, mix, rng)[0] for _ in range(300)])
        assert mean_hi > mean_lo

    def test_beta_one_is_deterministic_given_q(self, coupling_mix):
        # beta=1 collapses the band to a point -> Vmax independent of the
        # within-band B draw, so two different RNGs give the same Vmax.
        pw, mix = coupling_mix
        v1, _ = coupled_genesis_wind(0.8, 1.0, pw, mix, np.random.default_rng(1))
        v2, _ = coupled_genesis_wind(0.8, 1.0, pw, mix, np.random.default_rng(999))
        assert v1 == pytest.approx(v2, abs=1e-6)

    def test_reproducible_under_fixed_seed(self, coupling_mix):
        pw, mix = coupling_mix
        v1, s1 = coupled_genesis_wind(0.7, 0.52, pw, mix, np.random.default_rng(42))
        v2, s2 = coupled_genesis_wind(0.7, 0.52, pw, mix, np.random.default_rng(42))
        assert v1 == pytest.approx(v2) and s1 == s2

    def test_returns_valid_family(self, coupling_mix):
        pw, mix = coupling_mix
        _v, sc = coupled_genesis_wind(0.95, 0.52, pw, mix, np.random.default_rng(3))
        assert sc in pw


class TestSampleGenesisOverride:

    def test_override_fixes_v_max(self, minimal_config):
        # v_max_override pins genesis Vmax exactly; other fields still sampled.
        rng = _rng(5)
        state = sample_genesis(
            minimal_config, ScenarioFamily.SEVERE, rng, v_max_override=58.3)
        assert state.v_max_ms == pytest.approx(58.3)

    def test_no_override_samples_from_scenario(self, minimal_config):
        rng = _rng(5)
        state = sample_genesis(minimal_config, ScenarioFamily.SEVERE, rng)
        # minimal_config peak-wind is clamped to [v_min, v_max]; just sane.
        assert 10.0 <= state.v_max_ms <= 100.0
