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

"""Tests for the standalone Loan Calculator menu entry + panel wiring.

The asset right-click menu gains a "Loan Calculator" item (distinct from the
asset-linked "Loan Pricer") that opens the LoanPricerPanel in standalone mode.
"""


class TestLoanCalculatorMenuItems:

    def test_property_menu_has_calculator(self):
        from visual.interactivity.context_menus import DEFAULT_PROPERTY_MENU
        actions = [i["action"] for i in DEFAULT_PROPERTY_MENU]
        labels = [i["label"] for i in DEFAULT_PROPERTY_MENU]
        assert "openLoanCalculator" in actions
        assert any("Loan Calculator" in lbl for lbl in labels)

    def test_commercial_menu_has_calculator(self):
        from visual.interactivity.context_menus import DEFAULT_COMMERCIAL_MENU
        actions = [i["action"] for i in DEFAULT_COMMERCIAL_MENU]
        labels = [i["label"] for i in DEFAULT_COMMERCIAL_MENU]
        assert "openCommercialLoanCalculator" in actions
        assert any("Loan Calculator" in lbl for lbl in labels)

    def test_calculator_distinct_from_pricer(self):
        """The standalone calculator must not alias the asset-linked pricer."""
        from visual.interactivity.context_menus import DEFAULT_PROPERTY_MENU
        actions = [i["action"] for i in DEFAULT_PROPERTY_MENU]
        assert "openLoanCalculator" in actions
        assert "viewLoanPricer" in actions
        assert actions.count("openLoanCalculator") == 1

    def test_property_and_commercial_calculator_actions_disjoint(self):
        from visual.interactivity.context_menus import (
            DEFAULT_PROPERTY_MENU, DEFAULT_COMMERCIAL_MENU)
        prop = {i["action"] for i in DEFAULT_PROPERTY_MENU}
        com = {i["action"] for i in DEFAULT_COMMERCIAL_MENU}
        assert prop.isdisjoint(com)


class TestLoanPricerPanelStandaloneJS:

    def _js(self):
        from visual.interactivity.property.loanpricer import LoanPricerPanel
        return LoanPricerPanel().get_js()

    def test_standalone_window_functions_registered(self):
        js = self._js()
        assert "window.openLoanCalculator" in js
        assert "window.openCommercialLoanCalculator" in js

    def test_standalone_helper_and_endpoint_present(self):
        js = self._js()
        assert "showStandalone" in js
        assert "/api/v1/loan-pricer" in js

    def test_standalone_defaults_present(self):
        js = self._js()
        assert "STANDALONE_DEFAULTS" in js
        # Calculator title shown in standalone mode.
        assert "Loan Calculator" in js

    def test_credit_rating_and_wind_inputs_present(self):
        js = self._js()
        assert "CREDIT_RATINGS" in js
        assert "lp-credit_rating" in js
        assert "lp-wind_risk_category" in js
        assert "WIND_OPTIONS" in js

    def test_coupon_buildup_rendered(self):
        js = self._js()
        # Standalone results show the coupon decomposition.
        assert "Coupon Build-up" in js
        assert "data.coupon" in js or "data && data.coupon" in js

    def test_coupon_legs_labelled_by_pricer(self):
        """Flood leg is PRS-priced; wind is the static placeholder — the
        labels must say so to keep the provenance visible."""
        js = self._js()
        assert "Flood Hazard (PRS)" in js
        assert "Wind Hazard (static)" in js

    def test_redundant_pricing_rows_removed(self):
        """The engine's affordability-derived credit spread, LTV factor, flood
        risk factor and affordability ratio were misleading in the results
        panel and must no longer be rendered there."""
        js = self._js()
        assert "LTV Factor" not in js
        assert "Flood Risk Factor" not in js
        assert "Affordability Ratio" not in js

    def test_ten_million_region_defaults(self):
        """Standalone defaults seed a ~10M property / loan, per spec."""
        js = self._js()
        assert "property_value: 10000000" in js
        assert "loan_amount: 7500000" in js

    def test_flood_leg_links_to_prs_pricer(self):
        """The Flood Hazard (PRS) leg deep-links to the asset's PRS pricer
        panel when the calculator was opened from a marker."""
        js = self._js()
        # The leg renders an anchor wired to the PRS pricer panel.
        assert "lp-flood-prs-link" in js
        assert "window.viewPropertyHazard(standaloneOriginAssetId)" in js
        assert "PRS pricer" in js

    def test_origin_asset_id_captured_from_launcher(self):
        """Launchers forward the right-clicked asset id so the flood leg can
        deep-link to that asset's PRS pricer."""
        js = self._js()
        assert "standaloneOriginAssetId" in js
        assert "openLoanCalculator = function(assetId)" in js
        assert "openCommercialLoanCalculator = function(assetId)" in js
        assert "showStandalone('residential', assetId)" in js
        assert "showStandalone('commercial', assetId)" in js

    def test_commercial_asset_class_sent(self):
        js = self._js()
        # Commercial launcher tags the request so the server caps the term.
        assert "standaloneAssetClass" in js
        assert "asset_class" in js
        assert "showStandalone('commercial', assetId)" in js
        assert "showStandalone('residential', assetId)" in js
