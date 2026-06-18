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

"""Tests for models.typhoon.genesis — initial-state sampling. (part 2 of 4)

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
