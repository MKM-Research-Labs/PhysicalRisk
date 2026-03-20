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

"""Tests for reports.gauge.gauge_page_10_prs_pricing — GaugePRSPricingPage."""

from reportlab.platypus import Paragraph, Table


class TestGaugePRSPricingPage:

    def _page(self):
        from reports.gauge.gauge_page_10_prs_pricing import GaugePRSPricingPage
        return GaugePRSPricingPage()

    def test_no_hazard_curve_shows_fallback(self):
        page = self._page()
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No hazard" in t or "hazard" in t.lower() for t in texts)

    def test_with_zero_rates_renders_na(self):
        page = self._page()
        gauge_data = {
            "hazard_curve": {
                "annual_hazard_rate_alert": 0.0,
                "annual_hazard_rate_warning": 0.0,
                "annual_hazard_rate_severe": 0.0,
            }
        }
        result = page.generate_elements(gauge_data)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_with_nonzero_rates_renders_spreads(self):
        page = self._page()
        gauge_data = {
            "hazard_curve": {
                "annual_hazard_rate_alert": 0.15,
                "annual_hazard_rate_warning": 0.08,
                "annual_hazard_rate_severe": 0.03,
            }
        }
        result = page.generate_elements(gauge_data)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)
