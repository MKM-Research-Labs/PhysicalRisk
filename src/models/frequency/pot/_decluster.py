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

"""Declustering for peaks-over-threshold extraction (MKM-EF-001).

This is the step the platform's existing frequency calculation is missing.
``src/models/statistics/timeseries.py`` counts every *day* on which the level
sits above a threshold, so a single five-day flood contributes five to the
count. An arrival rate needs events, not exceedance-days.

The runs method is used: consecutive exceedances separated by less than the
configured window belong to one flood event, and the event is represented by
its largest observation. The window is measured between successive
exceedances, so a long flood with a rising and falling limb stays one event
however long it runs.
"""

from datetime import datetime
from typing import List, Sequence

from ..datastructures import Peak

# Observation dates are ISO; a leading ``YYYY-MM-DD`` is all that is needed,
# so any time component is ignored rather than rejected.
_DATE_CHARS = 10
_DATE_FORMAT = "%Y-%m-%d"


def parse_date(date_str: str) -> datetime:
    """Parse an ISO observation date, ignoring any time component.

    Args:
        date_str: an ISO date, optionally with a time suffix.

    Returns:
        The parsed date as a ``datetime``.

    Raises:
        ValueError: if the leading characters are not an ISO date.
    """
    return datetime.strptime(date_str[:_DATE_CHARS], _DATE_FORMAT)


def decluster(exceedances: Sequence[Peak], window_days: int) -> List[Peak]:
    """Collapse clustered exceedances into independent peaks.

    Args:
        exceedances: exceedances in chronological order.
        window_days: minimum separation, in days, between independent peaks.
            Successive exceedances closer than this belong to one event.

    Returns:
        The peak of each cluster, in chronological order. An empty input gives
        an empty result.
    """
    if not exceedances:
        return []

    peaks: List[Peak] = []
    cluster_best = exceedances[0]
    previous_date = parse_date(exceedances[0].date)

    for observation in exceedances[1:]:
        observation_date = parse_date(observation.date)
        gap_days = (observation_date - previous_date).days
        if gap_days >= window_days:
            # Far enough from the previous exceedance to start a new event.
            peaks.append(cluster_best)
            cluster_best = observation
        elif observation.value > cluster_best.value:
            # Same event, higher water: this observation becomes the peak.
            cluster_best = observation
        previous_date = observation_date

    peaks.append(cluster_best)
    return peaks
