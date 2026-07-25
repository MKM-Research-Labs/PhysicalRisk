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

"""Negative Binomial arrival family (MKM-EF-001, Stage 2).

For over-dispersed counts — variance above the mean — which is the physical
signature of storm *clustering*: a wet synoptic pattern produces several events
in quick succession, so some years carry many and others few.

Parameterised by mean ``mu`` and dispersion ``alpha`` (variance = mu + alpha
mu^2). As ``alpha`` tends to zero the Negative Binomial tends to the Poisson,
so this family strictly extends Poisson on the over-dispersed side and cannot
represent under-dispersion at all: ``alpha`` is constrained non-negative, so
the fitted variance is always at least the mean.
"""

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy import optimize, special

FAMILY_NAME = "negbin"

# Free parameters (mu, alpha), for the AIC penalty.
N_PARAMS = 2

# Smallest dispersion the fit will report. Below this the Negative Binomial is
# numerically indistinguishable from a Poisson, and the selection layer prefers
# the simpler family there anyway. Set above the bounded optimiser's resting
# point on a zero-variance series (~5e-6) so such a series snaps cleanly to the
# Poisson limit rather than reporting a spurious wisp of dispersion.
_MIN_ALPHA = 1e-4

# Search bounds for the dispersion parameter during the one-dimensional fit.
_ALPHA_LO = 1e-8
_ALPHA_HI = 1e6


@dataclass(frozen=True)
class NegBinFit:
    """A Negative Binomial fitted to an annual count series.

    Attributes:
        mu: the fitted mean (events per year).
        alpha: the fitted dispersion; variance is ``mu + alpha * mu**2``.
        log_likelihood: the maximised log-likelihood of the counts.
        n_years: number of annual counts fitted.
    """

    mu: float
    alpha: float
    log_likelihood: float
    n_years: int

    @property
    def family(self) -> str:
        """Return the family name."""
        return FAMILY_NAME

    @property
    def aic(self) -> float:
        """Return the Akaike information criterion, ``2k - 2 log L``."""
        return 2 * N_PARAMS - 2 * self.log_likelihood

    @property
    def mean(self) -> float:
        """Return the distribution mean."""
        return self.mu

    @property
    def variance(self) -> float:
        """Return the distribution variance, ``mu + alpha * mu**2``."""
        return self.mu + self.alpha * self.mu ** 2

    def _n_and_p(self) -> tuple:
        """Return the (n, p) numpy parameterisation of this fit.

        numpy draws a Negative Binomial as the number of failures before ``n``
        successes at success probability ``p``. In the (mu, alpha) form,
        ``n = 1/alpha`` and ``p = n / (n + mu)``.
        """
        n = 1.0 / self.alpha
        return n, n / (n + self.mu)

    def sample_annual_count(self, rng: np.random.Generator) -> int:
        """Draw one year's event count.

        Args:
            rng: caller-owned generator, for reproducibility.

        Returns:
            A non-negative integer. Falls back to a Poisson draw when the
            dispersion is negligible, where the numpy parameters would overflow.
        """
        if self.alpha <= _MIN_ALPHA:
            return int(rng.poisson(self.mu))
        n, p = self._n_and_p()
        return int(rng.negative_binomial(n, p))


def _neg_log_likelihood(counts: np.ndarray, mu: float, alpha: float) -> float:
    """Return the negative Negative-Binomial log-likelihood.

    Args:
        counts: annual event counts.
        mu: the mean.
        alpha: the dispersion.

    Returns:
        The negative total log-likelihood, for minimisation.
    """
    if alpha <= _MIN_ALPHA:
        # Poisson limit.
        return float(np.sum(mu - counts * math.log(mu) + special.gammaln(counts + 1)))
    r = 1.0 / alpha
    ll = (
        special.gammaln(counts + r)
        - special.gammaln(r)
        - special.gammaln(counts + 1)
        + r * math.log(r / (r + mu))
        + counts * np.log(mu / (r + mu))
    )
    return float(-np.sum(ll))


def fit_negbin(counts: Sequence[int]) -> NegBinFit:
    """Fit a Negative Binomial to an annual count series.

    The mean is fixed at the sample mean (its profile MLE), and the dispersion
    is found by a bounded one-dimensional search — stable where the joint
    two-dimensional optimisation is not, and exact enough given that the mean's
    MLE is closed-form.

    Args:
        counts: annual event counts; must be non-empty.

    Returns:
        The fitted Negative Binomial. Degenerate series (zero mean, or no
        over-dispersion) return the Poisson-limit fit at ``alpha = 0``.
    """
    data = np.asarray(counts, dtype=float)
    mu = float(data.mean())

    if mu <= 0:
        return NegBinFit(mu=0.0, alpha=0.0, log_likelihood=0.0, n_years=len(data))

    result = optimize.minimize_scalar(
        lambda a: _neg_log_likelihood(data, mu, a),
        bounds=(_ALPHA_LO, _ALPHA_HI),
        method="bounded",
    )
    alpha = float(result.x)
    if alpha <= _MIN_ALPHA:
        alpha = 0.0

    return NegBinFit(
        mu=mu,
        alpha=alpha,
        log_likelihood=-_neg_log_likelihood(data, mu, alpha),
        n_years=len(data),
    )
