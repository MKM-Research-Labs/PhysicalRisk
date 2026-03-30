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

"""
Generalized Extreme Value (GEV) distribution fitting and term structure computation.
"""

import math
from typing import List, Tuple

import numpy as np
from scipy import stats

from .data_structures import TermStructurePoint


class GEVFitter:
    """Fits Generalized Extreme Value distributions to peak level data."""

    def __init__(self, force_gumbel: bool = False):
        self.force_gumbel = force_gumbel

    def fit(self, peak_levels: np.ndarray) -> Tuple[float, float, float]:
        """Fit GEV distribution. Returns (shape, location, scale)."""
        if self.force_gumbel:
            loc, scale = stats.gumbel_r.fit(peak_levels)
            return (0.0, loc, scale)
        else:
            shape, loc, scale = stats.genextreme.fit(peak_levels)
            return (shape, loc, scale)

    def exceedance_probability(self, threshold: float, shape: float, loc: float, scale: float) -> float:
        """Calculate P(X > threshold)."""
        if abs(shape) < 1e-10:
            cdf = stats.gumbel_r.cdf(threshold, loc, scale)
        else:
            cdf = stats.genextreme.cdf(threshold, shape, loc, scale)
        return 1.0 - cdf

    def return_level(self, return_period: float, shape: float, loc: float, scale: float) -> float:
        """Calculate return level for a given return period."""
        p = 1.0 / return_period
        if abs(shape) < 1e-10:
            return stats.gumbel_r.ppf(1 - p, loc, scale)
        else:
            return stats.genextreme.ppf(1 - p, shape, loc, scale)


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
