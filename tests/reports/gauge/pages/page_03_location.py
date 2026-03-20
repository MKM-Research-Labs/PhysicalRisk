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

"""Tests for reports.gauge.gauge_page_03_location — GaugeLocationPage."""

from reportlab.platypus import Paragraph, Table


def _make_gauge(lat=51.508, lon=-0.121, distance=150, risk_cat="High", risk_score=7.5):
    thames = {"DistanceToThamesMeters": distance}
    if risk_cat:
        thames["FloodRiskAssessment"] = {
            "FloodRiskScore": risk_score,
            "FloodRiskCategory": risk_cat,
            "LastAssessmentDate": "2024-01-01",
        }
    return {
        "FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test Gauge"},
            "SensorDetails": {
                "GaugeInformation": {
                    "GaugeLatitude": lat,
                    "GaugeLongitude": lon,
                    "GroundLevelMeters": 4.5,
                }
            },
            "ThamesInfo": thames,
        }
    }


class TestGaugeLocationPage:

    def _page(self):
        from reports.gauge.gauge_page_03_location import GaugeLocationPage
        return GaugeLocationPage()

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
        assert any("Geographic Location" in t for t in texts)

    def test_has_tables(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        assert any(isinstance(e, Table) for e in result)

    def test_geographic_coordinates_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Geographic Coordinates" in t for t in texts)

    def test_thames_context_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Thames River Context" in t for t in texts)

    def test_flood_risk_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Flood Risk" in t for t in texts)

    def test_positioning_summary_section(self):
        page = self._page()
        result = page.generate_elements(_make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Positioning Summary" in t for t in texts)

    def test_lat_north_london(self):
        """Latitude > 51.5 → 'North London area'."""
        page = self._page()
        result = page.generate_elements(_make_gauge(lat=51.6))
        assert "North London area" in str(result)

    def test_lat_central_london(self):
        """Latitude 51.4–51.5 → 'Central London area'."""
        page = self._page()
        result = page.generate_elements(_make_gauge(lat=51.45))
        assert "Central London area" in str(result)

    def test_lat_south_london(self):
        """Latitude < 51.4 → 'South London area'."""
        page = self._page()
        result = page.generate_elements(_make_gauge(lat=51.3))
        assert "South London area" in str(result)

    def test_distance_zero_on_thames(self):
        """Distance == 0 → 'On Thames River' and 'Directly on Thames'."""
        page = self._page()
        result = page.generate_elements(_make_gauge(distance=0))
        assert "On Thames River" in str(result)

    def test_distance_close_to_thames(self):
        """Distance < 100 → 'Very close to Thames'."""
        page = self._page()
        result = page.generate_elements(_make_gauge(distance=50))
        assert "Very close to Thames" in str(result)

    def test_risk_score_formatted_as_out_of_10(self):
        """Risk score shown as 'X/10'."""
        page = self._page()
        result = page.generate_elements(_make_gauge(risk_score=7.5))
        assert "7.5/10" in str(result)

    def test_risk_category_in_location_profile(self):
        page = self._page()
        result = page.generate_elements(_make_gauge(risk_cat="High"))
        assert "High flood risk location" in str(result)

    def test_no_thames_info_does_not_crash(self):
        data = {"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}}
        page = self._page()
        result = page.generate_elements(data)
        assert isinstance(result, list)
