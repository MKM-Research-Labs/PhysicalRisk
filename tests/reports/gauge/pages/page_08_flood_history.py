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

"""Tests for reports.gauge.gauge_page_08_flood_history — GaugeFloodHistoryPage."""

import datetime

from reportlab.platypus import Paragraph, Table


def _make_daily_obs(n=10, start_level=2.0):
    base = datetime.date(2020, 1, 1)
    return [
        {
            "date": (base + datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
            "level_meters": start_level + i * 0.1,
        }
        for i in range(n)
    ]


def _make_hd(n=10, with_flood=False, alert=4.5, warning=5.5, severe=6.5):
    obs = _make_daily_obs(n, start_level=2.0 if not with_flood else alert)
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


def _make_storm(storm_id, peak, exceeded_alert=False, exceeded_warning=False,
                exceeded_severe=False):
    return {
        "storm_id": storm_id,
        "peak_level_m": peak,
        "level_change_m": peak - 2.0,
        "exceeded_alert": exceeded_alert,
        "exceeded_warning": exceeded_warning,
        "exceeded_severe": exceeded_severe,
    }


class TestGaugeFloodHistoryPage:

    def _page(self):
        from reports.gauge.gauge_page_08_flood_history import GaugeFloodHistoryPage
        return GaugeFloodHistoryPage()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_timeseries_data_shows_no_data_message(self):
        page = self._page()
        result = page.generate_elements({}, timeseries_data=None)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No historical" in t or "No storm" in t for t in texts)

    def test_with_historical_daily_returns_more_elements(self):
        page = self._page()
        hd = _make_hd(n=20)
        result = page.generate_elements({}, timeseries_data={"historical_daily": hd})
        assert len(result) > 2

    def test_with_storm_responses_includes_table(self):
        page = self._page()
        storms = [_make_storm(f"EVT-{i:03d}", 3.0 + i * 0.5) for i in range(5)]
        result = page.generate_elements({}, timeseries_data={"storm_responses": storms})
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_no_storm_responses_shows_message(self):
        page = self._page()
        result = page.generate_elements({}, timeseries_data={"storm_responses": []})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No storm" in t for t in texts)

    def test_worst_storms_table_top_10(self):
        page = self._page()
        storms = [_make_storm(f"EVT-{i:03d}", float(i)) for i in range(15)]
        result = page._build_worst_storms_table(storms)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) == 1

    def test_worst_storms_severity_classification(self):
        page = self._page()
        storms = [
            _make_storm("S1", 3.0, exceeded_alert=True),
            _make_storm("S2", 5.5, exceeded_alert=True, exceeded_warning=True),
            _make_storm("S3", 6.5, exceeded_alert=True, exceeded_warning=True, exceeded_severe=True),
        ]
        result = page._build_worst_storms_table(storms)
        assert isinstance(result, list)

    def test_realised_floods_no_exceedances(self):
        page = self._page()
        hd = _make_hd(n=5, with_flood=False, alert=100.0)
        result = page._build_realised_floods(hd)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No flood events" in t for t in texts)

    def test_realised_floods_with_exceedances(self):
        page = self._page()
        base = datetime.date(2022, 6, 1)
        obs = [
            {
                "date": (base + datetime.timedelta(days=i)).strftime("%Y-%m-%d"),
                "level_meters": 5.0,  # above alert=4.5
            }
            for i in range(5)
        ]
        hd = {
            "daily_observations": obs,
            "gauge_metadata": {
                "flood_stages": {"FloodAlert": 4.5, "FloodWarning": 5.5, "SevereFloodWarning": 6.5}
            },
            "years_included": 3,
        }
        result = page._build_realised_floods(hd)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_historical_graph_no_dates_fallback(self):
        page = self._page()
        hd = {
            "daily_observations": [{"date": "not-a-date", "level_meters": 3.0}],
            "gauge_metadata": {},
            "statistics": {},
        }
        result = page._build_historical_graph(hd)
        assert isinstance(result, list)

    def test_historical_graph_with_thresholds(self):
        page = self._page()
        hd = _make_hd(n=20)
        result = page._build_historical_graph(hd)
        assert isinstance(result, list)
        assert len(result) > 0
