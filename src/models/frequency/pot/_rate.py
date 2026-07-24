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

"""Exceedance rates at a fixed threshold (MKM-EF-001).

The counterpart to ``_extract`` for the case where the threshold is already
known — a gauge's published alert / warning / severe levels — so there is
nothing to search for, only to decluster and count.

This is the calculation the platform's statistics module performed by counting
exceedance *days*: a five-day flood contributed five. That overstates the rate
by roughly the mean event duration in days — measured at 28% on a thirty-year
synthetic record at the severe level. An arrival rate needs events.
"""

from dataclasses import dataclass
from typing import Any, Dict, Sequence

from config.frequency import PotConfig

from ._decluster import decluster
from ._extract import record_span_years, to_peaks


@dataclass(frozen=True)
class ExceedanceRate:
    """Declustered exceedance statistics at one threshold.

    Attributes:
        threshold: the level tested against.
        event_count: independent exceedance events, after declustering.
        exceedance_days: raw observations at or above the threshold. Retained
            because "days of flooding" is a legitimate statistic in its own
            right; it is simply not a rate.
        record_years: length of the record in years.
        events_per_year: ``event_count / record_years`` — the arrival rate.
        exceedance_days_per_year: ``exceedance_days / record_years``, the
            quantity previously reported as the frequency. Kept so the two can
            be shown side by side rather than one silently replacing the other.
    """

    threshold: float
    event_count: int
    exceedance_days: int
    record_years: float
    events_per_year: float
    exceedance_days_per_year: float

    @property
    def mean_event_duration_days(self) -> float:
        """Return the mean number of days an event spends above the threshold.

        This is the factor by which counting days overstates the rate.

        Returns:
            Days per event, or ``0.0`` when no events were found.
        """
        return self.exceedance_days / self.event_count if self.event_count else 0.0


def exceedance_rate(
    observations: Sequence[Dict[str, Any]],
    value_key: str,
    threshold: float,
    config: PotConfig,
) -> ExceedanceRate:
    """Compute the declustered exceedance rate at a fixed threshold.

    Args:
        observations: daily observation dicts with ``date`` and *value_key*.
        value_key: the observation field to read, e.g. ``level_meters``.
        threshold: the level defining an exceedance.
        config: supplies the declustering window.

    Returns:
        An ``ExceedanceRate``. An empty or zero-span record yields all-zero
        counts rather than raising, so a caller iterating over gauges is not
        derailed by one bad record.
    """
    series = to_peaks(observations, value_key)
    years = record_span_years(series)
    above = [p for p in series if p.value >= threshold]

    if not series or years <= 0:
        return ExceedanceRate(
            threshold=threshold,
            event_count=0,
            exceedance_days=len(above),
            record_years=0.0,
            events_per_year=0.0,
            exceedance_days_per_year=0.0,
        )

    events = decluster(above, config.declustering_window_days)
    return ExceedanceRate(
        threshold=threshold,
        event_count=len(events),
        exceedance_days=len(above),
        record_years=years,
        events_per_year=len(events) / years,
        exceedance_days_per_year=len(above) / years,
    )
