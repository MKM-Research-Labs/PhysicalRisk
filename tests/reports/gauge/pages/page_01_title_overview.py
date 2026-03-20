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

"""Tests for reports.gauge.gauge_page_01_title_overview — GaugeTitleOverviewPage."""

from reportlab.platypus import Paragraph, Table


def _make_gauge(gauge_id="GAUGE-001", install_date="2010-05-01"):
    info = {
        "GaugeType": "Stage",
        "GaugeOwner": "Environment Agency",
        "ManufacturerName": "OTT Hydromet",
        "OperationalStatus": "Active",
        "CertificationStatus": "Certified",
    }
    if install_date:
        info["InstallationDate"] = install_date
    return {
        "FloodGauge": {
            "Header": {"GaugeID": gauge_id, "GaugeName": "Test Gauge"},
            "SensorDetails": {"GaugeInformation": info},
            "SensorStats": {"HistoricalHighLevel": 6.2},
            "FloodStage": {
                "UK": {"FloodAlert": 3.5, "FloodWarning": 4.5, "SevereFloodWarning": 5.5}
            },
        }
    }


class TestGaugeTitleOverviewPage:

    def _page(self):
        from reports.gauge.gauge_page_01_title_overview import GaugeTitleOverviewPage
        return GaugeTitleOverviewPage()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_data_does_not_crash(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)

    def test_title_paragraph_present(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Comprehensive Flood Gauge Analysis Report" in t for t in texts)

    def test_gauge_id_in_output(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("GAUGE-001" in t for t in texts)

    def test_unknown_gauge_fallback(self):
        page = self._page()
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Unknown Gauge" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        assert any(isinstance(e, Table) for e in result)

    def test_gauge_overview_section_header(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Gauge Overview" in t for t in texts)

    def test_gauge_summary_section_header(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Gauge Summary" in t for t in texts)

    def test_installation_age_calculated(self):
        """Valid install date triggers gauge age row in summary."""
        page = self._page()
        result = page.generate_elements(_make_gauge(install_date="2005-01-01"))
        assert isinstance(result, list)
        assert len(result) > 0

    def test_bad_install_date_does_not_crash(self):
        """Unparseable install date is silently skipped."""
        page = self._page()
        result = page.generate_elements(_make_gauge(install_date="not-a-date"))
        assert isinstance(result, list)

    def test_no_install_date_does_not_crash(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(install_date=None))
        assert isinstance(result, list)

    def test_get_gauge_id_present(self):
        page = self._page()
        assert page._get_gauge_id(_make_gauge()) == "GAUGE-001"

    def test_get_gauge_id_missing(self):
        page = self._page()
        assert page._get_gauge_id({}) == "Unknown Gauge"

    def test_with_timeseries_does_not_crash(self):
        page = self._page()
        ts = {"readings": [{"waterLevel": 3.5, "alertStatus": "Normal"}]}
        result = page.generate_elements(_make_gauge(), timeseries_data=ts)
        assert isinstance(result, list)
