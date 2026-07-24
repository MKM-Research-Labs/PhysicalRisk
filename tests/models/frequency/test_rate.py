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

"""Tests for exceedance rates at a fixed threshold (MKM-EF-001).

A gauge's alert / warning / severe levels are already known, so there is no
threshold to search for — only to decluster and count.

The distinction these tests exist to protect: **days above a level are not a
rate**. A five-day flood is one event, and counting it five times overstates
the arrival rate by the mean event duration. Both numbers are reported,
because "how long does this gauge spend in flood" is a real question; it is
just a different one.
"""

from datetime import datetime, timedelta

import pytest

from config.frequency import PotConfig
from models.frequency import exceedance_rate

_START = datetime(2000, 1, 1)


def _day(offset):
    return (_START + timedelta(days=offset)).strftime("%Y-%m-%d")


def _record(values):
    """One observation per day from a list of levels."""
    return [{"date": _day(i), "level_meters": v} for i, v in enumerate(values)]


class TestDaysVersusEvents:

    def test_a_multiday_flood_is_one_event(self):
        """The whole point. Five consecutive days above the level is one flood,
        not five."""
        record = _record([1.0] * 100 + [5.0] * 5 + [1.0] * 100)
        rate = exceedance_rate(record, "level_meters", 4.0, PotConfig())

        assert rate.event_count == 1
        assert rate.exceedance_days == 5
        assert rate.mean_event_duration_days == pytest.approx(5.0)

    def test_the_day_rate_overstates_by_the_event_duration(self):
        record = _record([1.0] * 100 + [5.0] * 5 + [1.0] * 100)
        rate = exceedance_rate(record, "level_meters", 4.0, PotConfig())

        assert rate.exceedance_days_per_year == pytest.approx(
            rate.events_per_year * rate.mean_event_duration_days)

    def test_separate_floods_stay_separate(self):
        """Two floods a month apart are two events, not one."""
        record = _record([1.0] * 10 + [5.0] * 2 + [1.0] * 30 + [5.0] * 2 + [1.0] * 10)
        rate = exceedance_rate(record, "level_meters", 4.0, PotConfig())

        assert rate.event_count == 2
        assert rate.exceedance_days == 4

    def test_single_day_floods_make_the_two_measures_agree(self):
        """When nothing lasts more than a day there is nothing to decluster —
        which is why the correction is nearly invisible on a synthetic record
        that only injects single-day floods."""
        values = [5.0 if i % 100 == 0 else 1.0 for i in range(1000)]
        rate = exceedance_rate(_record(values), "level_meters", 4.0, PotConfig())

        assert rate.event_count == rate.exceedance_days
        assert rate.events_per_year == pytest.approx(rate.exceedance_days_per_year)

    def test_the_event_rate_is_never_above_the_day_rate(self):
        """Declustering can only merge, never split."""
        values = [5.0 if (i // 3) % 7 == 0 else 1.0 for i in range(2000)]
        rate = exceedance_rate(_record(values), "level_meters", 4.0, PotConfig())

        assert rate.events_per_year <= rate.exceedance_days_per_year


class TestThresholdBehaviour:

    def test_the_threshold_is_inclusive(self):
        rate = exceedance_rate(_record([4.0]), "level_meters", 4.0, PotConfig())
        assert rate.exceedance_days == 1

    def test_a_level_nothing_reaches_gives_no_events(self):
        rate = exceedance_rate(_record([1.0] * 500), "level_meters", 99.0, PotConfig())
        assert rate.event_count == 0
        assert rate.events_per_year == 0.0
        assert rate.mean_event_duration_days == 0.0

    def test_a_wider_declustering_window_never_finds_more_events(self):
        values = [5.0 if (i % 10) < 2 else 1.0 for i in range(500)]
        narrow = exceedance_rate(
            _record(values), "level_meters", 4.0, PotConfig(declustering_window_days=2))
        wide = exceedance_rate(
            _record(values), "level_meters", 4.0, PotConfig(declustering_window_days=30))
        assert wide.event_count <= narrow.event_count


class TestDegenerateRecords:

    def test_an_empty_record_is_inert(self):
        rate = exceedance_rate([], "level_meters", 1.0, PotConfig())
        assert rate.event_count == 0
        assert rate.record_years == 0.0
        assert rate.events_per_year == 0.0

    def test_a_single_observation_does_not_divide_by_zero(self):
        rate = exceedance_rate(_record([5.0]), "level_meters", 4.0, PotConfig())
        assert rate.events_per_year >= 0.0


class TestStatisticsModuleReportsBoth:
    """The statistics module keeps the day count and gains the event rate.

    Additive on purpose: ``count`` and ``frequency_per_year`` have existing
    consumers, and days-above-a-level remains a legitimate statistic. What
    changes is that the arrival rate is now available and correct beside it.
    """

    @staticmethod
    def _stats(values):
        from models.statistics.timeseries import calculate_timeseries_statistics

        return calculate_timeseries_statistics(
            _record(values), "level_meters",
            {"FloodAlert": 2.0, "FloodWarning": 3.0, "SevereFloodWarning": 4.0})

    def test_both_measures_are_reported(self):
        result = self._stats([1.0] * 50 + [5.0] * 4 + [1.0] * 50)
        severe = result["flood_exceedances"]["severe_warning"]

        assert severe["count"] == 4          # days, as before
        assert severe["event_count"] == 1    # events, the arrival rate
        assert severe["events_per_year"] < severe["frequency_per_year"]

    def test_the_legacy_keys_survive(self):
        """Existing consumers read count and frequency_per_year."""
        result = self._stats([1.0] * 50 + [5.0] * 4 + [1.0] * 50)
        for level in ("flood_alert", "flood_warning", "severe_warning"):
            entry = result["flood_exceedances"][level]
            assert {"threshold", "count", "frequency_per_year"} <= set(entry)

    def test_the_overstatement_factor_is_reported(self):
        result = self._stats([1.0] * 50 + [5.0] * 4 + [1.0] * 50)
        severe = result["flood_exceedances"]["severe_warning"]
        assert severe["mean_event_duration_days"] == pytest.approx(4.0)
