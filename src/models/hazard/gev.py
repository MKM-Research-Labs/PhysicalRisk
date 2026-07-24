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

"""
Generalized Extreme Value (GEV) distribution fitting and term structure computation.
"""

import math
from typing import List, Tuple

import numpy as np
from scipy import stats

from .data_structures import TermStructurePoint


class GEVFitter:
    """Fits Generalized Extreme Value distributions to peak level data.

    The shape parameter this class accepts and returns is the extreme-value
    convention, xi, in which a POSITIVE value is a heavy Frechet tail:

        xi > 0   Frechet, heavy tail, unbounded above
        xi = 0   Gumbel, exponential tail
        xi < 0   Weibull, bounded above

    scipy's ``genextreme`` parameterises the same family with ``c = -xi``, so a
    heavy tail is a *negative* c there. Every conversion happens inside this
    class: nothing outside it should see scipy's sign. The distinction is not
    cosmetic — the model's recorded weakness ("shape > 0.5 indicates a heavy
    tail that may be physically unrealistic") is written in xi, and against
    scipy's sign that test stays silent on exactly the fits it exists to catch.
    """

    # scipy's genextreme shape is the negative of the EVT xi, so one negation
    # converts in either direction. Named once so the conversion points cannot
    # drift apart, and so a reader is never left guessing which way a bare minus
    # sign was going.
    @staticmethod
    def _flip_convention(shape: float) -> float:
        return -shape

    def __init__(self, force_gumbel: bool = False):
        self.force_gumbel = force_gumbel

    def fit(self, peak_levels: np.ndarray) -> Tuple[float, float, float]:
        """Fit GEV distribution. Returns (xi, location, scale).

        ``xi`` is the extreme-value shape: positive means a heavy tail. Gumbel
        is xi = 0, which is the same number in either convention.
        """
        if self.force_gumbel:
            loc, scale = stats.gumbel_r.fit(peak_levels)
            return (0.0, loc, scale)
        else:
            c, loc, scale = stats.genextreme.fit(peak_levels)
            return (self._flip_convention(c), loc, scale)

    def exceedance_probability(self, threshold: float, shape: float, loc: float, scale: float) -> float:
        """Calculate P(X > threshold). ``shape`` is xi (positive = heavy tail)."""
        if abs(shape) < 1e-10:
            cdf = stats.gumbel_r.cdf(threshold, loc, scale)
        else:
            cdf = stats.genextreme.cdf(threshold, self._flip_convention(shape), loc, scale)
        return 1.0 - cdf

    def return_level(self, return_period: float, shape: float, loc: float, scale: float) -> float:
        """Calculate return level for a return period. ``shape`` is xi."""
        p = 1.0 / return_period
        if abs(shape) < 1e-10:
            return stats.gumbel_r.ppf(1 - p, loc, scale)
        else:
            return stats.genextreme.ppf(1 - p, self._flip_convention(shape), loc, scale)


def compute_term_structure(annual_hazard_rate: float, max_years: int = 5) -> List[TermStructurePoint]:
    """
    Compute term structure for PRS pricing using Poisson model.

    For Poisson process with annual intensity lambda:
    - P(no flood by year t) = e^(-lambda*t)
    - P(at least one flood by year t) = 1 - e^(-lambda*t)
    """
    term_structure = []

    for year in range(1, max_years + 1):
        expected_floods = annual_hazard_rate * year
        survival_prob = math.exp(-expected_floods)
        prob_at_least_one = 1.0 - survival_prob

        term_structure.append(TermStructurePoint(
            year=year,
            expected_floods=expected_floods,
            prob_at_least_one=prob_at_least_one,
            survival_prob=survival_prob,
            cumulative_default_prob=prob_at_least_one
        ))

    return term_structure
