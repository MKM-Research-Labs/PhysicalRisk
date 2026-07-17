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

"""Tests for GaugeHistoricalDaily.filter_by_years."""

from port.cdm.gaugehd import GaugeHistoricalDaily


class TestFilterByYears:

    def test_none_years_returns_all(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2000-01-01", "flow_cumecs": 10.0},
            {"date": "2020-01-01", "flow_cumecs": 20.0},
        ]
        assert len(gen.filter_by_years(flows, years=None)) == 2

    def test_empty_flows_returns_empty(self):
        assert GaugeHistoricalDaily().filter_by_years([], years=10) == []

    def test_filter_keeps_recent(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2000-06-01", "flow_cumecs": 10.0},
            {"date": "2015-06-01", "flow_cumecs": 20.0},
            {"date": "2020-06-01", "flow_cumecs": 30.0},
        ]
        result = gen.filter_by_years(flows, years=10)
        dates = [f["date"] for f in result]
        assert "2000-06-01" not in dates
        assert "2020-06-01" in dates

    def test_filter_1_year_keeps_only_recent(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2010-01-01", "flow_cumecs": 5.0},
            {"date": "2022-01-01", "flow_cumecs": 6.0},
            {"date": "2022-06-01", "flow_cumecs": 7.0},
        ]
        result = gen.filter_by_years(flows, years=1)
        assert "2010-01-01" not in [f["date"] for f in result]


class TestFilterByYearsBoundary:

    def test_zero_years_returns_only_most_recent_year(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2019-12-31", "flow_cumecs": 40.0},
            {"date": "2020-01-01", "flow_cumecs": 50.0},
        ]
        result = gen.filter_by_years(flows, years=0)
        assert "2020-01-01" in [f["date"] for f in result]

    def test_all_dates_within_range_kept(self):
        gen = GaugeHistoricalDaily()
        flows = [
            {"date": "2023-01-01", "flow_cumecs": 10.0},
            {"date": "2023-06-01", "flow_cumecs": 20.0},
            {"date": "2024-01-01", "flow_cumecs": 30.0},
        ]
        assert len(gen.filter_by_years(flows, years=5)) == 3
