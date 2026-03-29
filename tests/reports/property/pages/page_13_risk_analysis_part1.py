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

"""Tests for RiskAnalysisPage — part 1.

Basics, LTV branches, payment performance, and credit risk branches.
"""

from reportlab.platypus import Paragraph, Table

from .conftest import make_property, make_mortgage


class TestRiskAnalysisPageBasics:

    def _page(self):
        from reports.property.property_page_13_risk_analysis import RiskAnalysisPage
        return RiskAnalysisPage()

    def test_returns_list(self):
        assert isinstance(self._page().generate_elements(make_property()), list)

    def test_property_only_mode(self):
        result = self._page().generate_elements(make_property(), mortgage_data=None)
        assert isinstance(result, list) and len(result) > 0

    def test_combined_mode_with_mortgage(self):
        result = self._page().generate_elements(make_property(), make_mortgage())
        assert isinstance(result, list) and len(result) > 0

    def test_has_table(self):
        result = self._page().generate_elements(make_property(), make_mortgage())
        assert any(isinstance(e, Table) for e in result)

    def test_has_risk_header(self):
        result = self._page().generate_elements(make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Risk" in t for t in texts)

    def test_empty_property_does_not_crash(self):
        assert isinstance(self._page().generate_elements({}), list)


class TestLTVRiskBranches:

    def _page(self):
        from reports.property.property_page_13_risk_analysis import RiskAnalysisPage
        return RiskAnalysisPage()

    def test_very_high_ltv_over_95(self):
        result = self._page().generate_elements(make_property(), make_mortgage(ltv=0.97))
        assert isinstance(result, list)

    def test_high_ltv_90_to_95(self):
        result = self._page().generate_elements(make_property(), make_mortgage(ltv=0.92))
        assert isinstance(result, list)

    def test_medium_ltv_80_to_90(self):
        result = self._page().generate_elements(make_property(), make_mortgage(ltv=0.85))
        assert isinstance(result, list)

    def test_low_medium_ltv_70_to_80(self):
        result = self._page().generate_elements(make_property(), make_mortgage(ltv=0.75))
        assert isinstance(result, list)

    def test_low_ltv_under_70(self):
        result = self._page().generate_elements(make_property(), make_mortgage(ltv=0.60))
        assert isinstance(result, list)


class TestPaymentPerformanceBranches:

    def _page(self):
        from reports.property.property_page_13_risk_analysis import RiskAnalysisPage
        return RiskAnalysisPage()

    def test_in_arrears_score_5(self):
        result = self._page().generate_elements(make_property(), make_mortgage(in_arrears=True))
        assert isinstance(result, list)

    def test_many_missed_payments_over_3(self):
        result = self._page().generate_elements(make_property(), make_mortgage(missed_payments=4))
        assert isinstance(result, list)

    def test_some_missed_payments_1_to_3(self):
        result = self._page().generate_elements(make_property(), make_mortgage(missed_payments=2))
        assert isinstance(result, list)

    def test_no_missed_payments_good(self):
        result = self._page().generate_elements(make_property(), make_mortgage(missed_payments=0))
        assert isinstance(result, list)


class TestCreditRiskBranches:

    def _page(self):
        from reports.property.property_page_13_risk_analysis import RiskAnalysisPage
        return RiskAnalysisPage()

    def test_excellent_credit_800_plus(self):
        result = self._page().generate_elements(make_property(), make_mortgage(credit_score=820))
        assert isinstance(result, list)

    def test_very_good_credit_740_to_799(self):
        result = self._page().generate_elements(make_property(), make_mortgage(credit_score=760))
        assert isinstance(result, list)

    def test_good_credit_670_to_739(self):
        result = self._page().generate_elements(make_property(), make_mortgage(credit_score=700))
        assert isinstance(result, list)

    def test_fair_credit_580_to_669(self):
        result = self._page().generate_elements(make_property(), make_mortgage(credit_score=620))
        assert isinstance(result, list)

    def test_poor_credit_under_580(self):
        result = self._page().generate_elements(make_property(), make_mortgage(credit_score=500))
        assert isinstance(result, list)
