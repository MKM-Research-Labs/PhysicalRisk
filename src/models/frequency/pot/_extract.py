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

"""Peaks-over-threshold extraction (MKM-EF-001).

Turns a daily observation record into an independent peak series and the
annual count series that supports dispersion testing.

Year blocks are fixed 365-day windows measured from the first observation, not
calendar years. A calendar-year split would discard a partial first and last
year — up to two years out of five on the record lengths in use here — and a
seasonal record split mid-flood-season would bias the counts. Any trailing
partial block is dropped from the count series, so the mean of
``annual_counts`` can differ slightly from the reported rate, which uses the
whole span.
"""

from typing import Any, Dict, List, Sequence

from config.frequency import ANNUAL_BLOCK_DAYS, DAYS_PER_YEAR, PotConfig

from ..datastructures import Peak, PotExtraction
from ._decluster import decluster, parse_date
from ._threshold import select_threshold


def to_peaks(observations: Sequence[Dict[str, Any]], value_key: str) -> List[Peak]:
    """Convert raw observation dicts into ``Peak`` records, chronologically.

    Args:
        observations: dicts carrying a ``date`` and a numeric *value_key*.
        value_key: the observation field to read, e.g. ``level_meters``.

    Returns:
        Peaks in ascending date order. Observations missing either field are
        skipped rather than raising: a gappy record is normal and is handled by
        the record-length rule, not by an exception.
    """
    usable = [
        Peak(date=o["date"], value=float(o[value_key]))
        for o in observations
        if o.get("date") is not None and o.get(value_key) is not None
    ]
    return sorted(usable, key=lambda p: p.date)


def record_span_years(observations: Sequence[Peak]) -> float:
    """Return the length of the record in years.

    Args:
        observations: peaks in chronological order.

    Returns:
        The inclusive span in years, or ``0.0`` for an empty record.
    """
    if not observations:
        return 0.0
    first = parse_date(observations[0].date)
    last = parse_date(observations[-1].date)
    return ((last - first).days + 1) / DAYS_PER_YEAR


def annual_counts(peaks: Sequence[Peak], record_start: str, record_end: str) -> List[int]:
    """Bin declustered peaks into whole year blocks from the record start.

    Args:
        peaks: declustered peaks in chronological order.
        record_start: first observation date, ISO ``YYYY-MM-DD``.
        record_end: last observation date, ISO ``YYYY-MM-DD``.

    Returns:
        One count per whole year block. A trailing partial block is dropped.
        Empty when the record is shorter than a single block.
    """
    start = parse_date(record_start)
    whole_blocks = ((parse_date(record_end) - start).days + 1) // ANNUAL_BLOCK_DAYS
    if whole_blocks < 1:
        return []

    counts = [0] * whole_blocks
    for peak in peaks:
        block = (parse_date(peak.date) - start).days // ANNUAL_BLOCK_DAYS
        if 0 <= block < whole_blocks:
            counts[block] += 1
    return counts


def extract_pot(
    observations: Sequence[Dict[str, Any]],
    value_key: str,
    config: PotConfig,
) -> PotExtraction:
    """Run a full peaks-over-threshold extraction over a daily record.

    Selects a threshold targeting the configured mean exceedance rate,
    declusters the exceedances into independent peaks, and bins them into
    annual counts.

    Args:
        observations: daily observation dicts with ``date`` and *value_key*.
        value_key: the observation field to read.
        config: extraction knobs.

    Returns:
        A ``PotExtraction``. An empty or single-day record yields a zero-peak
        extraction rather than raising, so a caller iterating over gauges is
        not derailed by one bad record; the rate layer turns that into a
        regional fallback.
    """
    series = to_peaks(observations, value_key)
    record_years = record_span_years(series)
    if not series or record_years <= 0:
        return PotExtraction(
            threshold=0.0,
            peaks=(),
            annual_counts=(),
            record_start="",
            record_end="",
            record_years=0.0,
            achieved_rate_per_year=0.0,
            threshold_converged=False,
        )

    threshold, achieved_rate, converged = select_threshold(series, record_years, config)
    exceedances = [o for o in series if o.value >= threshold]
    peaks = decluster(exceedances, config.declustering_window_days)

    record_start, record_end = series[0].date, series[-1].date
    return PotExtraction(
        threshold=threshold,
        peaks=tuple(peaks),
        annual_counts=tuple(annual_counts(peaks, record_start, record_end)),
        record_start=record_start,
        record_end=record_end,
        record_years=record_years,
        achieved_rate_per_year=achieved_rate,
        threshold_converged=converged,
    )
