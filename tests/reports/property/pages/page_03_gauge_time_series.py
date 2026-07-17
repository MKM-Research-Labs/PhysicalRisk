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

"""Tests for reports.property.property_page_03_gauge_time_series — GaugeTimeSeries."""


def _make_ts(n=3):
    return [
        {
            "timestamp": f"2024-01-15T{i:02d}:00:00",
            "waterLevel": 3.0 + i * 0.2,
            "alertLevel": 4.5,
            "warningLevel": 5.5,
            "severeLevel": 6.5,
            "alertStatus": "Normal",
        }
        for i in range(n)
    ]


class TestGaugeTimeSeries:

    def _page(self):
        from reports.property.property_page_03_gauge_time_series import GaugeTimeSeries
        return GaugeTimeSeries()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements({"Header": {"GaugeName": "TestGauge"}})
        assert isinstance(result, list)

    def test_no_timeseries_returns_short_list(self):
        page = self._page()
        result = page.generate_elements({"Header": {"GaugeName": "G"}}, timeseries_data=None)
        assert len(result) > 0

    def test_no_timeseries_message_included(self):
        page = self._page()
        from reportlab.platypus import Paragraph
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No time series data" in t for t in texts)

    def test_empty_timeseries_returns_short_list(self):
        page = self._page()
        result = page.generate_elements({}, timeseries_data=[])
        assert isinstance(result, list)
        assert len(result) > 0

    def test_with_timeseries_returns_more_elements(self):
        page = self._page()
        ts = _make_ts(5)
        result = page.generate_elements({"Header": {"GaugeName": "G"}}, timeseries_data=ts)
        empty_result = page.generate_elements({"Header": {"GaugeName": "G"}})
        assert len(result) >= len(empty_result)

    def test_gauge_name_in_title(self):
        page = self._page()
        from reportlab.platypus import Paragraph
        result = page.generate_elements({"Header": {"GaugeName": "Chelsea Gauge"}})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Chelsea Gauge" in t for t in texts)

    def test_missing_gauge_name_does_not_crash(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)

    def test_with_timeseries_table_included(self):
        page = self._page()
        from reportlab.platypus import Table
        ts = _make_ts(5)
        result = page.generate_elements({"Header": {"GaugeName": "G"}}, timeseries_data=ts)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_timeseries_with_thresholds(self):
        """Readings with non-zero thresholds exercising fill_between paths."""
        page = self._page()
        ts = _make_ts(6)
        result = page.generate_elements({"Header": {"GaugeName": "G"}}, timeseries_data=ts)
        assert isinstance(result, list)

    def test_timeseries_mixed_statuses(self):
        page = self._page()
        ts = _make_ts(4)
        ts[1]["alertStatus"] = "Alert"
        ts[2]["alertStatus"] = "Warning"
        ts[3]["alertStatus"] = "Severe"
        result = page.generate_elements({"Header": {"GaugeName": "G"}}, timeseries_data=ts)
        assert isinstance(result, list)
