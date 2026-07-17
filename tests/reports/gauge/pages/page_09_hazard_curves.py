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

"""Tests for reports.gauge.gauge_page_09_hazard_curves — GaugeHazardCurvesPage."""

from reportlab.platypus import Paragraph, Table


class TestGaugeHazardCurvesPage:

    def _page(self):
        from reports.gauge.gauge_page_09_hazard_curves import GaugeHazardCurvesPage
        return GaugeHazardCurvesPage()

    def test_no_hazard_curve_shows_fallback(self):
        page = self._page()
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No hazard" in t or "hazard" in t.lower() for t in texts)

    def test_with_hazard_curve_basic(self):
        page = self._page()
        gauge_data = {
            "hazard_curve": {
                "gev_location": 4.0,
                "gev_scale": 0.5,
                "gev_shape": 0.1,
                "annual_hazard_rate_alert": 0.15,
                "annual_hazard_rate_warning": 0.08,
                "annual_hazard_rate_severe": 0.03,
                "return_period_levels": {},
            }
        }
        result = page.generate_elements(gauge_data)
        assert len(result) > 2

    def test_with_return_period_levels_renders_table(self):
        page = self._page()
        gauge_data = {
            "hazard_curve": {
                "gev_location": 4.0,
                "gev_scale": 0.5,
                "gev_shape": 0.1,
                "annual_hazard_rate_alert": 0.15,
                "annual_hazard_rate_warning": 0.08,
                "annual_hazard_rate_severe": 0.03,
                "return_period_levels": {
                    "10yr": 4.5,
                    "50yr": 5.0,
                    "100yr": 5.5,
                },
            }
        }
        result = page.generate_elements(gauge_data)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 2

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)

    def test_empty_return_period_levels_no_extra_table(self):
        page = self._page()
        gauge_data = {
            "hazard_curve": {
                "gev_location": 4.0,
                "gev_scale": 0.5,
                "gev_shape": 0.1,
                "annual_hazard_rate_alert": 0.15,
                "annual_hazard_rate_warning": 0.08,
                "annual_hazard_rate_severe": 0.03,
                "return_period_levels": {},
            }
        }
        result = page.generate_elements(gauge_data)
        # Should still have at least the GEV params table
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1
