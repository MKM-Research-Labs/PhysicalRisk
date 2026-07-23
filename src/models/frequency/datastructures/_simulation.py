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

"""Year-simulation structures for the Event Frequency Model (MKM-EF-001).

The simulated year is the unit the desk reasons in: draw how many qualifying
storm events arrive, ask of each whether it floods, and record whether the year
flooded at all. Repeating that gives the annual flood probability the PRS
spread is priced from, and the whole annual distribution alongside it.
"""

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass(frozen=True)
class EventDraws:
    """The events drawn for each simulated year, shared across a whole run.

    One set of draws serves every subject in a portfolio run, so gauges and
    properties stay correlated through the storms they share.

    Attributes:
        n_years: number of years simulated.
        lambda_per_year: the catchment arrival rate used.
        events_per_year: qualifying events drawn in each simulated year.
        event_indices: flat array of drawn catalogue indices, in year order and
            partitioned by ``events_per_year``.
        seed: the seed the run used.
    """

    n_years: int
    lambda_per_year: float
    events_per_year: np.ndarray
    event_indices: np.ndarray
    seed: int


@dataclass(frozen=True)
class YearSimulation:
    """The outcome of a Monte Carlo run of one-year simulations.

    Attributes:
        n_years: number of years simulated.
        lambda_per_year: the catchment arrival rate used.
        p_event: the per-event conditional flood probability used.
        events_per_year: qualifying events drawn in each simulated year.
        flood_events_per_year: how many of those events flooded, per year.
        seed: the seed the run used, so the run can be reproduced exactly.
    """

    n_years: int
    lambda_per_year: float
    p_event: float
    events_per_year: np.ndarray
    flood_events_per_year: np.ndarray
    seed: int

    def annual_flood_probability(self) -> float:
        """Return the fraction of simulated years with at least one flood.

        This is the number the PRS spread is priced from — the occurrence view.

        Returns:
            A probability in ``[0, 1]``.
        """
        if self.n_years == 0:
            return 0.0
        return float(np.count_nonzero(self.flood_events_per_year) / self.n_years)

    def expected_floods_per_year(self) -> float:
        """Return the mean number of flooding events per year.

        The aggregate view. It exceeds the occurrence probability whenever a
        year can carry more than one flood, which is exactly the case a
        conditional-only model cannot represent.

        Returns:
            Events per year.
        """
        if self.n_years == 0:
            return 0.0
        return float(self.flood_events_per_year.mean())

    def return_period_years(self, return_periods: Tuple[int, ...]) -> dict:
        """Return the flood-count level reached at each return period.

        Args:
            return_periods: return periods in years.

        Returns:
            Mapping of return period to the number of flooding events in a year
            that severe. An empty run maps every period to zero.
        """
        if self.n_years == 0:
            return {rp: 0.0 for rp in return_periods}
        return {
            rp: float(np.quantile(self.flood_events_per_year, 1.0 - 1.0 / rp))
            for rp in return_periods
        }
