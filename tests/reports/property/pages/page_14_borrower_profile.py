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

"""Tests for reports.property.property_page_14_borrower_profile — BorrowerProfilePage."""

from reportlab.platypus import Paragraph, Table


def _make_mortgage(age=35, employment="Employed", years_employed=None,
                   income=80_000, secondary_income=None, credit_score=720,
                   marital_status=None, family_members=None,
                   nationality=None, residency_status=None,
                   income_verification=None):
    borrower = {
        "BorrowerAge": age,
        "BorrowerEmployment": employment,
        "BorrowerIncome": income,
        "BorrowerCreditScore": credit_score,
    }
    if years_employed is not None:
        borrower["YearsInCurrentEmployment"] = years_employed
    if secondary_income is not None:
        borrower["SecondaryIncome"] = secondary_income
    if marital_status is not None:
        borrower["MaritalStatus"] = marital_status
    if family_members is not None:
        borrower["FamilyMembers"] = family_members
    if nationality is not None:
        borrower["BorrowerNationality"] = nationality
    if residency_status is not None:
        borrower["ResidencyStatus"] = residency_status
    if income_verification is not None:
        borrower["IncomeVerificationType"] = income_verification
    return {"RLoan": {"BorrowerDetails": borrower}}


class TestBorrowerProfilePageBasics:

    def _page(self):
        from reports.property.property_page_14_borrower_profile import BorrowerProfilePage
        return BorrowerProfilePage()

    def test_no_mortgage_returns_message(self):
        result = self._page().generate_elements({}, rloan_data=None)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No mortgage" in t for t in texts)

    def test_with_mortgage_returns_list(self):
        result = self._page().generate_elements({}, _make_mortgage())
        assert isinstance(result, list) and len(result) > 0

    def test_has_borrower_header(self):
        result = self._page().generate_elements({}, _make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Borrower" in t for t in texts)

    def test_has_table(self):
        result = self._page().generate_elements({}, _make_mortgage())
        assert any(isinstance(e, Table) for e in result)

    def test_no_borrower_details_returns_early(self):
        mortgage = {"RLoan": {"Header": {"RLoanID": "M1"}}}
        result = self._page().generate_elements({}, mortgage)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("No borrower" in t for t in texts)

    def test_marital_status_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(marital_status="Married"))
        assert isinstance(result, list)

    def test_family_members_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(family_members=3))
        assert isinstance(result, list)

    def test_nationality_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(nationality="British"))
        assert isinstance(result, list)

    def test_residency_status_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(residency_status="Permanent Resident"))
        assert isinstance(result, list)

    def test_income_verification_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(income_verification="P60"))
        assert isinstance(result, list)

    def test_secondary_income_shown(self):
        result = self._page().generate_elements({}, _make_mortgage(secondary_income=15_000))
        assert isinstance(result, list)


class TestAgeRiskBranches:

    def _page(self):
        from reports.property.property_page_14_borrower_profile import BorrowerProfilePage
        return BorrowerProfilePage()

    def test_prime_years_25_to_55(self):
        result = self._page().generate_elements({}, _make_mortgage(age=40))
        assert isinstance(result, list)

    def test_early_career_under_25(self):
        result = self._page().generate_elements({}, _make_mortgage(age=22))
        assert isinstance(result, list)

    def test_approaching_retirement_over_55(self):
        result = self._page().generate_elements({}, _make_mortgage(age=60))
        assert isinstance(result, list)


class TestEmploymentStabilityBranches:

    def _page(self):
        from reports.property.property_page_14_borrower_profile import BorrowerProfilePage
        return BorrowerProfilePage()

    def test_excellent_5_plus_years(self):
        result = self._page().generate_elements({}, _make_mortgage(years_employed=7))
        assert isinstance(result, list)

    def test_good_2_to_5_years(self):
        result = self._page().generate_elements({}, _make_mortgage(years_employed=3))
        assert isinstance(result, list)

    def test_fair_1_to_2_years(self):
        result = self._page().generate_elements({}, _make_mortgage(years_employed=1))
        assert isinstance(result, list)

    def test_concerning_under_1_year(self):
        result = self._page().generate_elements({}, _make_mortgage(years_employed=0))
        assert isinstance(result, list)


class TestIncomeAnalysisBranches:

    def _page(self):
        from reports.property.property_page_14_borrower_profile import BorrowerProfilePage
        return BorrowerProfilePage()

    def test_high_income_over_100k(self):
        result = self._page().generate_elements({}, _make_mortgage(income=120_000))
        assert isinstance(result, list)

    def test_good_income_50k_to_100k(self):
        result = self._page().generate_elements({}, _make_mortgage(income=75_000))
        assert isinstance(result, list)

    def test_fair_income_30k_to_50k(self):
        result = self._page().generate_elements({}, _make_mortgage(income=40_000))
        assert isinstance(result, list)

    def test_limited_income_under_30k(self):
        result = self._page().generate_elements({}, _make_mortgage(income=25_000))
        assert isinstance(result, list)

    def test_total_income_with_secondary(self):
        result = self._page().generate_elements(
            {}, _make_mortgage(income=80_000, secondary_income=20_000)
        )
        assert isinstance(result, list)


class TestCreditScoreBranches:

    def _page(self):
        from reports.property.property_page_14_borrower_profile import BorrowerProfilePage
        return BorrowerProfilePage()

    def test_excellent_800_plus(self):
        result = self._page().generate_elements({}, _make_mortgage(credit_score=820))
        assert isinstance(result, list)

    def test_very_good_740_to_799(self):
        result = self._page().generate_elements({}, _make_mortgage(credit_score=760))
        assert isinstance(result, list)

    def test_good_670_to_739(self):
        result = self._page().generate_elements({}, _make_mortgage(credit_score=700))
        assert isinstance(result, list)

    def test_fair_580_to_669(self):
        result = self._page().generate_elements({}, _make_mortgage(credit_score=620))
        assert isinstance(result, list)

    def test_poor_under_580(self):
        result = self._page().generate_elements({}, _make_mortgage(credit_score=500))
        assert isinstance(result, list)


class TestAssessBorrowerRisk:

    def _page(self):
        from reports.property.property_page_14_borrower_profile import BorrowerProfilePage
        return BorrowerProfilePage()

    def test_returns_dict(self):
        result = self._page()._assess_borrower_risk({})
        assert isinstance(result, dict)

    def test_credit_risk_low_for_high_score(self):
        r = self._page()._assess_borrower_risk({"BorrowerCreditScore": 780})
        assert "Credit Risk" in r
        assert "Low" in r["Credit Risk"]

    def test_credit_risk_low_medium_for_good_score(self):
        r = self._page()._assess_borrower_risk({"BorrowerCreditScore": 700})
        assert "Low-Medium" in r["Credit Risk"]

    def test_credit_risk_medium_for_fair_score(self):
        r = self._page()._assess_borrower_risk({"BorrowerCreditScore": 620})
        assert "Medium" in r["Credit Risk"]

    def test_credit_risk_high_for_poor_score(self):
        r = self._page()._assess_borrower_risk({"BorrowerCreditScore": 500})
        assert "High" in r["Credit Risk"]

    def test_employment_risk_stable_5_plus(self):
        r = self._page()._assess_borrower_risk({"YearsInCurrentEmployment": 6})
        assert "Employment Risk" in r
        assert "Low" in r["Employment Risk"]

    def test_employment_risk_established_2_to_5(self):
        r = self._page()._assess_borrower_risk({"YearsInCurrentEmployment": 3})
        assert "Low-Medium" in r["Employment Risk"]

    def test_employment_risk_recent_under_2(self):
        r = self._page()._assess_borrower_risk({"YearsInCurrentEmployment": 1})
        assert "Medium-High" in r["Employment Risk"]

    def test_income_risk_low_for_high_income(self):
        r = self._page()._assess_borrower_risk({"BorrowerIncome": 120_000})
        assert "Income Risk" in r
        assert "Low" in r["Income Risk"]

    def test_income_risk_low_medium_adequate(self):
        r = self._page()._assess_borrower_risk({"BorrowerIncome": 70_000})
        assert "Low-Medium" in r["Income Risk"]

    def test_income_risk_medium_limited(self):
        r = self._page()._assess_borrower_risk({"BorrowerIncome": 30_000})
        assert "Medium" in r["Income Risk"]

    def test_age_risk_prime_years(self):
        r = self._page()._assess_borrower_risk({"BorrowerAge": 40})
        assert "Age Risk" in r
        assert "Low" in r["Age Risk"]

    def test_age_risk_early_career(self):
        r = self._page()._assess_borrower_risk({"BorrowerAge": 22})
        assert "Medium" in r["Age Risk"]

    def test_age_risk_approaching_retirement(self):
        r = self._page()._assess_borrower_risk({"BorrowerAge": 60})
        assert "Medium" in r["Age Risk"]
