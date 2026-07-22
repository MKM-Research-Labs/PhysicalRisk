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

"""Tests for peaks-over-threshold extraction (MKM-EF-001).

Covers declustering by the runs method, threshold search against a target
exceedance rate, annual binning into whole year blocks, and the degenerate
records the extractor must survive rather than raise on.

The central property under test is the one the platform currently gets wrong:
a multi-day flood is one event, not one event per day above the threshold.
"""

from datetime import datetime, timedelta

import pytest

from config.frequency import ANNUAL_BLOCK_DAYS, PotConfig
from models.frequency.datastructures import Peak
from models.frequency.pot import (
    annual_counts,
    candidate_thresholds,
    decluster,
    extract_pot,
    parse_date,
    quantile,
    rate_at_threshold,
    record_span_years,
    select_threshold,
    to_peaks,
)

_START = datetime(2000, 1, 1)


def _day(offset: int) -> str:
    """Return the ISO date *offset* days after the fixed start date."""
    return (_START + timedelta(days=offset)).strftime("%Y-%m-%d")


def _series(pairs):
    """Build a Peak series from (day_offset, value) pairs."""
    return [Peak(date=_day(offset), value=value) for offset, value in pairs]


def _flat_record(n_days, base=1.0):
    """Build a flat daily observation record of *n_days* days."""
    return [{"date": _day(i), "level_meters": base} for i in range(n_days)]


# ---------------------------------------------------------------- date parsing

def test_parse_date_accepts_bare_iso_date():
    assert parse_date("2020-03-04") == datetime(2020, 3, 4)


def test_parse_date_ignores_time_component():
    assert parse_date("2020-03-04T12:30:00Z") == datetime(2020, 3, 4)


def test_parse_date_rejects_non_iso():
    with pytest.raises(ValueError):
        parse_date("04/03/2020")


# ---------------------------------------------------------------- declustering

def test_decluster_empty_series_gives_no_peaks():
    assert decluster([], window_days=5) == []


def test_decluster_collapses_a_multiday_flood_to_one_peak():
    """The defect this whole model exists to fix: five days above threshold
    is one flood event, not five."""
    flood = _series([(0, 4.0), (1, 4.8), (2, 5.2), (3, 4.6), (4, 4.1)])
    peaks = decluster(flood, window_days=5)
    assert len(peaks) == 1
    assert peaks[0].value == 5.2
    assert peaks[0].date == _day(2)


def test_decluster_separates_events_beyond_the_window():
    two_events = _series([(0, 4.0), (10, 4.5)])
    peaks = decluster(two_events, window_days=5)
    assert [p.value for p in peaks] == [4.0, 4.5]


def test_decluster_gap_exactly_the_window_starts_a_new_event():
    """The window is the minimum separation, so a gap equal to it separates."""
    peaks = decluster(_series([(0, 4.0), (5, 4.5)]), window_days=5)
    assert len(peaks) == 2


def test_decluster_gap_one_short_of_the_window_stays_one_event():
    peaks = decluster(_series([(0, 4.0), (4, 4.5)]), window_days=5)
    assert len(peaks) == 1
    assert peaks[0].value == 4.5


def test_decluster_measures_the_gap_from_the_previous_exceedance():
    """A long flood stays one event however far it runs, because each day is
    within the window of the day before it."""
    long_flood = _series([(i, 4.0 + i * 0.1) for i in range(30)])
    peaks = decluster(long_flood, window_days=5)
    assert len(peaks) == 1


def test_decluster_keeps_the_first_of_equal_maxima():
    peaks = decluster(_series([(0, 5.0), (1, 5.0)]), window_days=5)
    assert peaks[0].date == _day(0)


def test_decluster_never_returns_more_peaks_than_exceedances():
    exceedances = _series([(i * 3, 4.0) for i in range(20)])
    assert len(decluster(exceedances, window_days=5)) <= len(exceedances)


# ------------------------------------------------------------------- quantiles

def test_quantile_returns_an_observed_value():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert quantile(values, 0.0) == 1.0
    assert quantile(values, 1.0) == 5.0
    assert quantile(values, 0.5) in values


def test_quantile_clamps_out_of_range_fractions():
    values = [1.0, 2.0, 3.0]
    assert quantile(values, 1.5) == 3.0
    assert quantile(values, -1.0) == 1.0


def test_candidate_thresholds_empty_record_gives_no_candidates():
    assert candidate_thresholds([], PotConfig()) == []


def test_candidate_thresholds_are_ascending_and_deduplicated():
    values = [float(i) for i in range(1000)]
    candidates = candidate_thresholds(values, PotConfig())
    assert candidates == sorted(set(candidates))


def test_candidate_thresholds_collapse_on_a_constant_record():
    """A flat record has one distinct value, so there is one candidate."""
    assert candidate_thresholds([2.0] * 100, PotConfig()) == [2.0]


def test_candidate_thresholds_survive_a_zero_step_count():
    config = PotConfig(search_steps=0)
    assert candidate_thresholds([float(i) for i in range(100)], config)


# ------------------------------------------------------------ threshold search

def test_rate_at_threshold_counts_events_not_days():
    flood = _series([(0, 4.0), (1, 4.5), (2, 4.2)])
    rate, n_peaks = rate_at_threshold(flood, 3.0, record_years=1.0, window_days=5)
    assert n_peaks == 1
    assert rate == pytest.approx(1.0)


def test_select_threshold_hits_the_target_rate():
    """One flood every 60 days over ten years is about six events a year. Every
    third flood is made larger, so a threshold delivering the configured two
    events a year exists for the search to find."""
    observations = []
    flood_index = 0
    for day in range(3650):
        if day % 60 == 0:
            observations.append(Peak(_day(day), 6.0 if flood_index % 3 == 0 else 5.0))
            flood_index += 1
        else:
            observations.append(Peak(_day(day), 1.0))

    threshold, rate, converged = select_threshold(
        observations, record_years=10.0, config=PotConfig())
    assert converged
    assert rate == pytest.approx(2.0, abs=PotConfig().target_rate_tolerance)
    # It must have found the discriminating level, not the flood floor.
    assert threshold == 6.0


def test_select_threshold_empty_record_reports_no_convergence():
    threshold, rate, converged = select_threshold([], 1.0, PotConfig())
    assert (threshold, rate, converged) == (0.0, 0.0, False)


def test_select_threshold_reports_failure_when_target_unreachable():
    """A record with a single flood cannot deliver two events a year."""
    observations = _series([(i, 5.0 if i == 0 else 1.0) for i in range(3650)])
    _, rate, converged = select_threshold(observations, 10.0, PotConfig())
    assert not converged
    assert rate < PotConfig().target_exceedance_rate_per_year


# --------------------------------------------------------------- record shapes

def test_to_peaks_sorts_into_chronological_order():
    unordered = [
        {"date": _day(5), "level_meters": 2.0},
        {"date": _day(1), "level_meters": 1.0},
    ]
    assert [p.date for p in to_peaks(unordered, "level_meters")] == [_day(1), _day(5)]


def test_to_peaks_skips_rows_missing_the_value_or_date():
    rows = [
        {"date": _day(0), "level_meters": 1.0},
        {"date": _day(1)},
        {"level_meters": 2.0},
        {"date": _day(2), "level_meters": None},
    ]
    assert len(to_peaks(rows, "level_meters")) == 1


def test_record_span_years_of_an_empty_record_is_zero():
    assert record_span_years([]) == 0.0


def test_record_span_years_is_inclusive_of_both_endpoints():
    one_year = _series([(0, 1.0), (364, 1.0)])
    assert record_span_years(one_year) == pytest.approx(1.0, abs=0.01)


# --------------------------------------------------------------- annual counts

def test_annual_counts_bins_peaks_into_year_blocks():
    peaks = _series([(10, 5.0), (20, 5.0), (ANNUAL_BLOCK_DAYS + 10, 5.0)])
    counts = annual_counts(peaks, _day(0), _day(2 * ANNUAL_BLOCK_DAYS - 1))
    assert counts == [2, 1]


def test_annual_counts_drops_a_trailing_partial_block():
    counts = annual_counts([], _day(0), _day(ANNUAL_BLOCK_DAYS + 100))
    assert len(counts) == 1


def test_annual_counts_of_a_short_record_is_empty():
    assert annual_counts([], _day(0), _day(100)) == []


def test_annual_counts_ignores_peaks_beyond_the_last_whole_block():
    peaks = _series([(ANNUAL_BLOCK_DAYS + 10, 5.0)])
    assert annual_counts(peaks, _day(0), _day(ANNUAL_BLOCK_DAYS + 100)) == [0]


# -------------------------------------------------------------- full extraction

def test_extract_pot_on_an_empty_record_is_inert():
    extraction = extract_pot([], "level_meters", PotConfig())
    assert extraction.peaks == ()
    assert extraction.record_years == 0.0
    assert not extraction.threshold_converged


def test_extract_pot_on_a_single_observation_is_inert():
    """A one-day record has a span of one day, which is a positive number of
    years, so this exercises the path where the record is real but unusable."""
    extraction = extract_pot(
        [{"date": _day(0), "level_meters": 1.0}], "level_meters", PotConfig())
    assert extraction.record_years > 0
    assert len(extraction.peaks) <= 1


def test_extract_pot_on_a_flat_record_finds_one_threshold():
    extraction = extract_pot(_flat_record(400), "level_meters", PotConfig())
    assert extraction.threshold == 1.0
    assert not extraction.threshold_converged


def test_extract_pot_reports_a_consistent_rate():
    observations = [
        {"date": _day(day), "level_meters": 5.0 if day % 30 == 0 else 1.0}
        for day in range(3650)
    ]
    extraction = extract_pot(observations, "level_meters", PotConfig())
    assert extraction.achieved_rate_per_year == pytest.approx(
        len(extraction.peaks) / extraction.record_years, rel=1e-9)


def test_extract_pot_annual_counts_sum_to_at_most_the_peak_count():
    """Peaks in a trailing partial block are excluded from the count series."""
    observations = [
        {"date": _day(day), "level_meters": 5.0 if day % 30 == 0 else 1.0}
        for day in range(1000)
    ]
    extraction = extract_pot(observations, "level_meters", PotConfig())
    assert sum(extraction.annual_counts) <= len(extraction.peaks)
