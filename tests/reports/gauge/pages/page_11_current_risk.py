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

"""Tests for reports.gauge.gauge_page_11_current_risk — GaugeCurrentRiskPage."""

import datetime

import pytest
from reportlab.platypus import Paragraph


def _make_hd(n=10, with_flood=False, alert=4.5, warning=5.5, severe=6.5):
    base = datetime.date(2020, 1, 1)
    start_level = 2.0 if not with_flood else alert
    obs = [
        {
            "date": (base + datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
            "level_meters": start_level + i * 0.1,
        }
        for i in range(n)
    ]
    return {
        "daily_observations": obs,
        "gauge_metadata": {
            "flood_stages": {
                "FloodAlert": alert,
                "FloodWarning": warning,
                "SevereFloodWarning": severe,
            }
        },
        "statistics": {
            "total_years": 50,
            "max_level": max(o["level_meters"] for o in obs),
            "flood_exceedances": {
                "flood_alert": {"count": 3, "frequency_per_year": 0.06},
                "flood_warning": {"count": 1, "frequency_per_year": 0.02},
                "severe_warning": {"count": 0, "frequency_per_year": 0.0},
            },
        },
        "years_included": 50,
    }


class TestGaugeCurrentRiskPage:

    def _page(self):
        from reports.gauge.gauge_page_11_current_risk import GaugeCurrentRiskPage
        return GaugeCurrentRiskPage()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_timeseries_data_shows_fallback(self):
        page = self._page()
        result = page.generate_elements({}, timeseries_data=None)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No historical" in t or "No" in t for t in texts)

    def test_empty_historical_daily_shows_fallback(self):
        page = self._page()
        ts = {"historical_daily": {"daily_observations": []}}
        result = page.generate_elements({}, timeseries_data=ts)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any(t for t in texts)

    def test_with_observations_returns_elements(self):
        page = self._page()
        hd = _make_hd(n=30)
        hd["daily_observations"][-1]["date"] = "2024-06-30"
        ts = {"historical_daily": hd}
        result = page.generate_elements({}, timeseries_data=ts)
        assert len(result) > 2

    def test_with_observations_includes_content(self):
        page = self._page()
        hd = _make_hd(n=15)
        ts = {"historical_daily": hd}
        result = page.generate_elements({}, timeseries_data=ts)
        assert len(result) >= 2
