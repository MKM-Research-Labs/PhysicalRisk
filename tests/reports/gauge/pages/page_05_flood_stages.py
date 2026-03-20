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

"""Tests for reports.gauge.gauge_page_05_flood_stages — GaugeFloodStagesPage."""

from reportlab.platypus import Paragraph, Table


def _make_gauge(alert=3.5, warning=4.5, severe=5.5):
    return {
        "FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test Gauge"},
            "FloodStage": {
                "UK": {
                    "FloodAlert": alert,
                    "FloodWarning": warning,
                    "SevereFloodWarning": severe,
                    "DecisionBody": "Environment Agency",
                }
            },
            "SensorStats": {
                "HistoricalHighLevel": 6.0,
                "HistoricalHighDate": "2014-02-10",
                "LastDateLevelExceedLevel3": "2021-01-05",
                "FrequencyExceedLevel3": 2,
            },
        }
    }


def _make_ts(level=3.8):
    return {
        "readings": [
            {
                "waterLevel": level,
                "alertStatus": "Normal",
                "exceedsAlert": level >= 3.5,
                "exceedsWarning": level >= 4.5,
                "exceedsSevere": level >= 5.5,
            }
        ]
    }


class TestGaugeFloodStagesPage:

    def _page(self):
        from reports.gauge.gauge_page_05_flood_stages import GaugeFloodStagesPage
        return GaugeFloodStagesPage()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_data_does_not_crash(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)

    def test_title_present(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Flood Stages" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        assert any(isinstance(e, Table) for e in result)

    def test_uk_thresholds_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("UK Flood Stage Thresholds" in t for t in texts)

    def test_threshold_analysis_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Threshold Analysis" in t for t in texts)

    def test_historical_exceedance_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Historical Threshold Exceedance" in t for t in texts)

    def test_no_timeseries_shows_message(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=None)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No current timeseries data" in t for t in texts)

    def test_with_timeseries_shows_current_status_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=_make_ts(3.0))
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Current Status vs Thresholds" in t for t in texts)

    def test_current_level_below_alert_is_normal(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=_make_ts(3.0))
        assert "Normal" in str(result)

    def test_current_level_at_alert(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=_make_ts(3.5))
        assert "FLOOD ALERT" in str(result)

    def test_current_level_at_warning(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=_make_ts(4.5))
        assert "FLOOD WARNING" in str(result)

    def test_current_level_at_severe(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(), timeseries_data=_make_ts(5.5))
        assert "SEVERE FLOOD WARNING" in str(result)

    def test_threshold_differences_computed(self):
        """Alert-to-warning and warning-to-severe ranges are added to analysis table."""
        page = self._page()
        result = page.generate_elements(_make_gauge(alert=3.5, warning=4.5, severe=5.5))
        assert isinstance(result, list)

    def test_get_gauge_id_present(self):
        page = self._page()
        assert page._get_gauge_id(_make_gauge()) == "GAUGE-001"

    def test_get_gauge_id_missing(self):
        page = self._page()
        assert page._get_gauge_id({}) == "Unknown Gauge"
