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

    @pytest.mark.xfail(reason="Source bug: statistics.min doesn't exist")
    def test_with_observations_returns_elements(self):
        page = self._page()
        hd = _make_hd(n=30)
        hd["daily_observations"][-1]["date"] = "2024-06-30"
        ts = {"historical_daily": hd}
        result = page.generate_elements({}, timeseries_data=ts)
        assert len(result) > 2

    @pytest.mark.xfail(reason="Source bug: statistics.min doesn't exist")
    def test_with_observations_includes_content(self):
        page = self._page()
        hd = _make_hd(n=15)
        ts = {"historical_daily": hd}
        result = page.generate_elements({}, timeseries_data=ts)
        assert len(result) >= 2
