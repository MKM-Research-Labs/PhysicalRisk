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

"""Tests for distribution families and selection (MKM-EF-001, Stage 2).

Three things are pinned:

- **Recovery.** Each family fitted to data drawn from itself recovers its
  parameters and reproduces its mean and variance.
- **Calibrated selection.** The selector does not over-select Negative Binomial
  on small samples — a genuine Poisson process produces high dispersion indices
  by chance, and the naive "index above one" rule would fire far too often. It
  also does not miss genuine over-dispersion.
- **Honesty about under-dispersion.** No family is fitted to it; it is flagged
  and Poisson is selected.
"""

import numpy as np
import pytest

from config.frequency import SelectionConfig
from models.frequency.families import (
    OVER_DISPERSED,
    UNDER_DISPERSED,
    dispersion_test,
    fit_negbin,
    fit_poisson,
    select_family,
)

_CFG = SelectionConfig()


def _negbin_counts(mu, alpha, n, seed):
    rng = np.random.default_rng(seed)
    r = 1.0 / alpha
    return rng.negative_binomial(r, r / (r + mu), size=n)


# ------------------------------------------------------------------- Poisson

class TestPoisson:

    def test_the_rate_is_the_sample_mean(self):
        fit = fit_poisson([3, 5, 4, 6, 2])
        assert fit.lam == pytest.approx(4.0)

    def test_mean_equals_variance(self):
        fit = fit_poisson([3, 5, 4, 6, 2])
        assert fit.mean == fit.variance == pytest.approx(4.0)

    def test_recovers_its_own_rate(self):
        data = np.random.default_rng(1).poisson(4.5, 100_000)
        assert fit_poisson(data).lam == pytest.approx(4.5, abs=0.05)

    def test_sampling_reproduces_the_mean(self):
        fit = fit_poisson([4] * 20)
        rng = np.random.default_rng(0)
        draws = [fit.sample_annual_count(rng) for _ in range(20_000)]
        assert np.mean(draws) == pytest.approx(4.0, rel=0.05)

    def test_aic_penalises_one_parameter(self):
        fit = fit_poisson([3, 5, 4])
        assert fit.aic == pytest.approx(2 - 2 * fit.log_likelihood)

    def test_an_all_zero_series_is_well_defined(self):
        fit = fit_poisson([0, 0, 0])
        assert fit.lam == 0.0
        assert fit.log_likelihood == 0.0


# --------------------------------------------------------------- NegBin

class TestNegBin:

    def test_recovers_its_own_parameters(self):
        data = _negbin_counts(mu=4.5, alpha=0.5, n=50_000, seed=2)
        fit = fit_negbin(data)
        assert fit.mu == pytest.approx(4.5, rel=0.05)
        assert fit.alpha == pytest.approx(0.5, rel=0.15)

    def test_variance_exceeds_the_mean_when_dispersed(self):
        fit = fit_negbin(_negbin_counts(4.5, 0.5, 5000, 3))
        assert fit.variance > fit.mean

    def test_collapses_to_poisson_on_poisson_data(self):
        """With no over-dispersion the fitted alpha is ~0, i.e. the Poisson
        limit — the family strictly extends Poisson, never contradicts it."""
        data = np.random.default_rng(4).poisson(4.5, 20_000)
        assert fit_negbin(data).alpha < 0.05

    def test_cannot_represent_under_dispersion(self):
        """alpha is constrained non-negative, so the variance floor is the
        mean — the family has nothing to say below Poisson."""
        near_fixed = [4, 5] * 25
        assert fit_negbin(near_fixed).variance >= fit_negbin(near_fixed).mean

    def test_sampling_reproduces_mean_and_overdispersion(self):
        fit = fit_negbin(_negbin_counts(4.5, 0.5, 5000, 5))
        rng = np.random.default_rng(0)
        draws = np.array([fit.sample_annual_count(rng) for _ in range(30_000)])
        assert draws.mean() == pytest.approx(fit.mean, rel=0.05)
        assert draws.var() == pytest.approx(fit.variance, rel=0.1)

    def test_a_zero_mean_series_is_handled(self):
        fit = fit_negbin([0, 0, 0])
        assert fit.mu == 0.0
        assert fit.alpha == 0.0


# ------------------------------------------------------- dispersion test

class TestDispersionTest:

    def test_a_regular_series_is_under_dispersed(self):
        test = dispersion_test([4, 5] * 25, significance=0.05)
        assert test.regime == UNDER_DISPERSED
        assert test.dispersion_index < 1.0

    def test_a_clustered_series_is_over_dispersed(self):
        test = dispersion_test(_negbin_counts(4.5, 1.0, 50, 1), significance=0.05)
        assert test.regime == OVER_DISPERSED
        assert test.dispersion_index > 1.0

    def test_a_short_series_has_no_testable_dispersion(self):
        test = dispersion_test([4], significance=0.05)
        assert test.p_over == 1.0
        assert test.p_under == 1.0

    def test_a_zero_mean_series_has_no_testable_dispersion(self):
        test = dispersion_test([0, 0, 0], significance=0.05)
        assert test.dispersion_index == 0.0


# ------------------------------------------------------------- selection

class TestSelection:

    def test_the_false_positive_rate_respects_the_significance(self):
        """The property the whole design turns on. A genuine Poisson process
        must not be handed NegBin more often than the significance allows — the
        naive index-above-one rule fails this badly on fifty-year records."""
        rng = np.random.default_rng(42)
        negbin = sum(
            select_family(rng.poisson(4.5, 50), _CFG).family == "negbin"
            for _ in range(2000)
        )
        assert negbin / 2000 < 0.03

    def test_genuine_over_dispersion_is_caught(self):
        rng = np.random.default_rng(7)
        r = 1.0 / 0.5
        caught = sum(
            select_family(
                rng.negative_binomial(r, r / (r + 4.5), 50), _CFG).family == "negbin"
            for _ in range(500)
        )
        assert caught / 500 > 0.9

    def test_under_dispersion_selects_poisson_and_flags_it(self):
        sel = select_family([4, 5] * 25, _CFG)
        assert sel.family == "poisson"
        assert sel.dispersion.regime == UNDER_DISPERSED
        assert "under-dispersed" in sel.note

    def test_poisson_consistent_counts_keep_poisson(self):
        sel = select_family([4, 5, 3, 6, 4, 5, 4, 3, 5, 4], _CFG)
        assert sel.family == "poisson"
        assert not sel.forced

    def test_the_chosen_fit_is_returned(self):
        over = _negbin_counts(4.5, 1.0, 50, 9)
        sel = select_family(over, _CFG)
        assert sel.fit is sel.negbin

    def test_a_marginal_aic_gain_keeps_poisson(self):
        """NegBin nests Poisson, so a negligible AIC improvement is not
        evidence for the extra parameter."""
        cfg = SelectionConfig(prefer_poisson_within_aic=1e9)
        sel = select_family(_negbin_counts(4.5, 1.0, 50, 3), cfg)
        assert sel.family == "poisson"
        assert sel.negbin is not None  # it was fitted, just not chosen


class TestOverride:

    def test_a_forced_family_wins_and_is_logged(self):
        cfg = SelectionConfig(force_family="negbin")
        sel = select_family([4, 5, 3, 6, 4], cfg)
        assert sel.family == "negbin"
        assert sel.forced
        assert "override" in sel.note

    def test_forcing_poisson_skips_the_negbin_fit(self):
        cfg = SelectionConfig(force_family="poisson")
        sel = select_family(_negbin_counts(4.5, 1.0, 50, 2), cfg)
        assert sel.family == "poisson"
        assert sel.negbin is None
        assert sel.forced


class TestCoverageOfBranches:
    """Small but real behaviours: name accessors and the Poisson-limit paths."""

    def test_family_names(self):
        assert fit_poisson([4, 5, 3]).family == "poisson"
        assert fit_negbin(_negbin_counts(4.5, 1.0, 50, 1)).family == "negbin"

    def test_negbin_at_the_poisson_limit_samples_as_poisson(self):
        """A NegBin fitted to Poisson data has alpha ~ 0; sampling must take the
        Poisson branch rather than overflow the numpy (n, p) parameters."""
        fit = fit_negbin(np.random.default_rng(4).poisson(4.5, 20_000))
        rng = np.random.default_rng(0)
        draws = [fit.sample_annual_count(rng) for _ in range(5000)]
        assert np.mean(draws) == pytest.approx(fit.mean, rel=0.1)

    def test_the_chosen_fit_is_poisson_when_poisson_is_selected(self):
        sel = select_family([4, 5, 3, 6, 4, 5, 4, 3, 5, 4], _CFG)
        assert sel.family == "poisson"
        assert sel.fit is sel.poisson


class TestNegBinPoissonLimit:
    """The exact alpha == 0 branches: a NegBin whose dispersion has collapsed
    fully to the Poisson limit must sample and score as a Poisson, not divide
    by a zero alpha."""

    def test_a_constant_series_fits_at_alpha_zero(self):
        """No variance at all -> alpha pinned to exactly zero by the fit."""
        from models.frequency.families import fit_negbin

        fit = fit_negbin([4, 4, 4, 4, 4])
        assert fit.alpha == 0.0

    def test_alpha_zero_samples_via_the_poisson_branch(self):
        from models.frequency.families._negbin import NegBinFit

        fit = NegBinFit(mu=4.5, alpha=0.0, log_likelihood=0.0, n_years=10)
        rng = np.random.default_rng(0)
        draws = [fit.sample_annual_count(rng) for _ in range(10_000)]
        assert np.mean(draws) == pytest.approx(4.5, rel=0.05)

    def test_alpha_zero_log_likelihood_uses_the_poisson_form(self):
        """A constant series has a defined likelihood at the Poisson limit."""
        from models.frequency.families import fit_negbin

        fit = fit_negbin([4, 4, 4])
        assert fit.log_likelihood < 0.0
