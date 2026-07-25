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

"""Poisson arrival family (MKM-EF-001, Stage 2).

The default and the physically-motivated baseline: events arrive independently
at a constant rate. Its single parameter is the mean, and the maximum-likelihood
estimate of the mean is the sample mean, so there is nothing to optimise.
"""

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

FAMILY_NAME = "poisson"

# Number of free parameters, for the AIC penalty.
N_PARAMS = 1


@dataclass(frozen=True)
class PoissonFit:
    """A Poisson fitted to an annual count series.

    Attributes:
        lam: the fitted rate (events per year), i.e. the sample mean.
        log_likelihood: the maximised log-likelihood of the counts.
        n_years: number of annual counts fitted.
    """

    lam: float
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
        return self.lam

    @property
    def variance(self) -> float:
        """Return the distribution variance (equal to the mean for Poisson)."""
        return self.lam

    def sample_annual_count(self, rng: np.random.Generator) -> int:
        """Draw one year's event count.

        Args:
            rng: caller-owned generator, for reproducibility.

        Returns:
            A non-negative integer.
        """
        return int(rng.poisson(self.lam))


def _log_likelihood(counts: Sequence[int], lam: float) -> float:
    """Return the Poisson log-likelihood of *counts* at rate *lam*.

    Args:
        counts: annual event counts.
        lam: the rate.

    Returns:
        The total log-likelihood. A zero rate is well defined only if every
        count is zero, in which case the likelihood is one (log zero).
    """
    if lam <= 0:
        return 0.0 if not any(counts) else -math.inf
    total = 0.0
    for k in counts:
        total += k * math.log(lam) - lam - math.lgamma(k + 1)
    return total


def fit_poisson(counts: Sequence[int]) -> PoissonFit:
    """Fit a Poisson to an annual count series.

    Args:
        counts: annual event counts; must be non-empty.

    Returns:
        The fitted Poisson. The rate is the sample mean — the exact MLE.
    """
    lam = float(np.mean(counts))
    return PoissonFit(
        lam=lam,
        log_likelihood=_log_likelihood(counts, lam),
        n_years=len(counts),
    )
