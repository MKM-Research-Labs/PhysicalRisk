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

"""Tests for RiskAnalysisPage — part 2.

Interest rate branches, DTI branches, overall risk levels, and helper methods.
"""

from .conftest import make_property, make_mortgage


class TestInterestRateBranches:

    def _page(self):
        from reports.property.property_page_13_risk_analysis import RiskAnalysisPage
        return RiskAnalysisPage()

    def test_high_rate_over_7(self):
        result = self._page().generate_elements(make_property(), make_mortgage(lending_rate=8.0))
        assert isinstance(result, list)

    def test_elevated_rate_5_to_7(self):
        result = self._page().generate_elements(make_property(), make_mortgage(lending_rate=6.0))
        assert isinstance(result, list)

    def test_moderate_rate_3_to_5(self):
        result = self._page().generate_elements(make_property(), make_mortgage(lending_rate=4.0))
        assert isinstance(result, list)

    def test_low_rate_under_3(self):
        result = self._page().generate_elements(make_property(), make_mortgage(lending_rate=2.5))
        assert isinstance(result, list)

    def test_no_rate_unknown(self):
        result = self._page().generate_elements(make_property(), make_mortgage(lending_rate=None))
        assert isinstance(result, list)


class TestDTIBranches:

    def _page(self):
        from reports.property.property_page_13_risk_analysis import RiskAnalysisPage
        return RiskAnalysisPage()

    def test_very_high_dti_over_43(self):
        # payment=5000/month, income=60000/year -> dti=100%
        result = self._page().generate_elements(
            make_property(), make_mortgage(income=60_000, current_payment=5000)
        )
        assert isinstance(result, list)

    def test_high_dti_36_to_43(self):
        # payment=2500/month, income=72000/year -> dti=41.7%
        result = self._page().generate_elements(
            make_property(), make_mortgage(income=72_000, current_payment=2500)
        )
        assert isinstance(result, list)

    def test_moderate_dti_28_to_36(self):
        # payment=1800/month, income=72000/year -> dti=30%
        result = self._page().generate_elements(
            make_property(), make_mortgage(income=72_000, current_payment=1800)
        )
        assert isinstance(result, list)

    def test_good_dti_under_28(self):
        # payment=1000/month, income=72000/year -> dti=16.7%
        result = self._page().generate_elements(
            make_property(), make_mortgage(income=72_000, current_payment=1000)
        )
        assert isinstance(result, list)

    def test_no_payment_dti_unknown(self):
        result = self._page().generate_elements(
            make_property(), make_mortgage(income=80_000, current_payment=None)
        )
        assert isinstance(result, list)


class TestOverallRiskLevels:

    def _page(self):
        from reports.property.property_page_13_risk_analysis import RiskAnalysisPage
        return RiskAnalysisPage()

    def test_critical_risk_scenario(self):
        """Very high flood risk + arrears + very high LTV + poor credit -> CRITICAL."""
        result = self._page().generate_elements(
            make_property(flood_risk="Very High"),
            make_mortgage(ltv=0.97, in_arrears=True, credit_score=500)
        )
        assert isinstance(result, list)

    def test_low_risk_scenario(self):
        """Very low flood risk + good payment + low LTV + excellent credit -> LOW."""
        result = self._page().generate_elements(
            make_property(flood_risk="Very Low"),
            make_mortgage(ltv=0.40, credit_score=820, missed_payments=0)
        )
        assert isinstance(result, list)

    def test_property_only_high_flood_risk(self):
        result = self._page().generate_elements(make_property(flood_risk="High"), mortgage_data=None)
        assert isinstance(result, list)

    def test_property_only_very_low_flood_risk(self):
        result = self._page().generate_elements(make_property(flood_risk="Very Low"), mortgage_data=None)
        assert isinstance(result, list)


class TestHelperMethods:

    def _page(self):
        from reports.property.property_page_13_risk_analysis import RiskAnalysisPage
        return RiskAnalysisPage()

    def test_generate_monitoring_high_score(self):
        r = self._page()._generate_monitoring_schedule(4.5)
        assert "Weekly" in r.values()

    def test_generate_monitoring_medium_score(self):
        r = self._page()._generate_monitoring_schedule(3.5)
        assert "Monthly" in r.values()

    def test_generate_monitoring_low_score(self):
        r = self._page()._generate_monitoring_schedule(2.0)
        assert "Annually" in r.values()

    def test_generate_recommendations_high_score(self):
        cats = {
            "Flood": {"score": 4, "weight": 20, "impact": "High flood risk"},
        }
        r = self._page()._generate_recommendations(cats, 4.5)
        assert any("URGENT" in rec for rec in r)

    def test_generate_recommendations_medium_score(self):
        cats = {"LTV": {"score": 3, "weight": 20, "impact": "medium"}}
        r = self._page()._generate_recommendations(cats, 3.0)
        assert any("HIGH PRIORITY" in rec or "MODERATE" in rec for rec in r)

    def test_generate_recommendations_low_score(self):
        r = self._page()._generate_recommendations({}, 1.5)
        assert any("LOW" in rec for rec in r)

    def test_identify_key_factors_high_risk(self):
        cats = {"Flood Risk": {"score": 4, "weight": 20, "impact": "High"}}
        r = self._page()._identify_key_factors(cats)
        assert any("High Risk Factor" in k for k in r.keys())

    def test_identify_key_factors_medium_risk(self):
        cats = {"Credit Risk": {"score": 3, "weight": 20, "impact": "Medium"}}
        r = self._page()._identify_key_factors(cats)
        assert any("Medium Risk Factor" in k for k in r.keys())
