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

"""Tests for models.typhoon.genesis — initial-state sampling. (part 1 of 4)

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
