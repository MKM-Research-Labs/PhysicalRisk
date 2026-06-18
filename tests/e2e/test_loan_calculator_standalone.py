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

"""End-to-end tests for the standalone Loan Calculator panel.

The standalone calculator is asset-independent: it opens with sensible
defaults, exposes the coupon build-up drivers (credit rating + flood/wind
category) and prices on demand against ``POST /api/v1/loan-pricer``. It is
launched in the browser via ``window.openLoanCalculator()`` (residential) or
``window.openCommercialLoanCalculator()`` (commercial, term capped at 7y).
"""

import pytest


class TestStandaloneLoanCalculator:
    """Drive the asset-independent Loan Calculator from the map."""

    def _open(self, map_page, fn_name):
        """Open the standalone calculator via the given window.* launcher.

        Returns False (caller skips) if the launcher isn't present.
        """
        has_fn = map_page.evaluate(
            f"() => typeof window.{fn_name} === 'function'"
        )
        if not has_fn:
            return False
        # No asset id → pure standalone (defaults only).
        map_page.evaluate(f"window.{fn_name}()")
        panel = map_page.locator("#loan-pricer-panel")
        panel.wait_for(state="visible", timeout=10_000)
        return True

    def test_residential_panel_opens(self, map_page):
        if not self._open(map_page, "openLoanCalculator"):
            pytest.skip("window.openLoanCalculator not available")

        panel = map_page.locator("#loan-pricer-panel")
        assert panel.is_visible()
        title = map_page.locator("#loan-pricer-title").inner_text()
        assert "Loan Calculator" in title

    def test_exposes_coupon_drivers(self, map_page):
        """Standalone-only inputs: credit rating select + user-defined
        contractual coupon.

        (Flood has no input here — its leg is PRS-driven from the asset curve
        or the server-side category fallback. The Wind Risk Category selector
        was removed, to be replaced later.)
        """
        if not self._open(map_page, "openLoanCalculator"):
            pytest.skip("window.openLoanCalculator not available")

        # The build-up drivers are only rendered in standalone mode.
        assert map_page.locator("#lp-credit_rating").count() > 0
        assert map_page.locator("#lp-contractual_coupon").count() > 0
        assert map_page.locator("#lp-wind_risk_category").count() == 0
        assert map_page.locator("#lp-reprice-btn").count() > 0

    def test_prices_and_shows_results(self, map_page):
        """The initial reprice should populate the results pane with pricing."""
        if not self._open(map_page, "openLoanCalculator"):
            pytest.skip("window.openLoanCalculator not available")

        # showStandalone() calls reprice() (async fetch) on open.
        map_page.wait_for_timeout(3_000)
        results = map_page.locator("#loan-pricer-results")
        text = results.inner_text().lower()
        assert "error" not in text, f"Pricing failed: {text[:200]}"
        has_pricing = (
            "usd" in text or "value" in text or "spread" in text
            or "coupon" in text or "%" in text
        )
        assert has_pricing, f"No pricing shown in results: '{text[:200]}'"

    def test_reprice_button_recomputes(self, map_page):
        """Clicking Re-price after editing an input recomputes without error."""
        if not self._open(map_page, "openLoanCalculator"):
            pytest.skip("window.openLoanCalculator not available")
        map_page.wait_for_timeout(2_000)

        amount = map_page.locator("#lp-loan_amount")
        if amount.count() == 0:
            pytest.skip("No #lp-loan_amount input")
        amount.fill("250000")
        map_page.locator("#lp-reprice-btn").click()
        map_page.wait_for_timeout(3_000)

        text = map_page.locator("#loan-pricer-results").inner_text().lower()
        assert "error" not in text, f"Re-price failed: {text[:200]}"
        assert len(text.strip()) > 0, "Results empty after re-price"

    def test_commercial_variant_labelled_and_capped(self, map_page):
        """The commercial launcher labels the panel and caps the term at 7y."""
        if not self._open(map_page, "openCommercialLoanCalculator"):
            pytest.skip("window.openCommercialLoanCalculator not available")

        title = map_page.locator("#loan-pricer-title").inner_text()
        assert "Commercial" in title

        map_page.wait_for_timeout(3_000)
        # After the server caps it, the repriced remaining-term input should
        # be <= 7 years for a commercial loan.
        term = map_page.locator("#lp-current_term")
        if term.count() > 0:
            val = term.input_value().strip()
            if val:
                assert float(val) <= 7.0, f"Commercial term not capped: {val}"
