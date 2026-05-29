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

"""
Tests for reports.property.property_page_11c_regulatory — RegulatoryPage.

Covers: no mortgage data → fallback, no regulatory data, with Common section,
with MCOB section (all fields), with HMDA section, exception path.
"""

import pytest
from reportlab.platypus import Paragraph, Table


def _page():
    from reports.property.property_page_11c_regulatory import RegulatoryPage
    return RegulatoryPage()


def _make_mortgage(regulatory=None):
    """Build minimal rloan_data dict."""
    return {"Mortgage": {"Regulatory": regulatory or {}}}


# ===========================================================================
# No mortgage data
# ===========================================================================

class TestNoMortgageData:

    def test_no_mortgage_returns_list(self):
        page = _page()
        result = page.generate_elements({}, rloan_data=None)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_mortgage_message(self):
        page = _page()
        result = page.generate_elements({})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No mortgage data" in t for t in texts)


# ===========================================================================
# No regulatory data
# ===========================================================================

class TestNoRegulatoryData:

    def test_empty_regulatory_returns_message(self):
        page = _page()
        result = page.generate_elements({}, rloan_data=_make_mortgage())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No regulatory information" in t for t in texts)

    def test_returns_list(self):
        page = _page()
        result = page.generate_elements({}, rloan_data=_make_mortgage())
        assert isinstance(result, list)


# ===========================================================================
# Common regulatory section
# ===========================================================================

class TestCommonRegulatory:

    def _mortgage_with_common(self, **kwargs):
        common = {"FCAReferenceNumber": "FCA123456", **kwargs}
        return _make_mortgage({"Common": common})

    def test_common_section_returns_elements(self):
        page = _page()
        result = page.generate_elements({}, rloan_data=self._mortgage_with_common())
        assert isinstance(result, list)
        assert len(result) > 2  # header + table + spacer

    def test_fca_reference_number(self):
        page = _page()
        result = page.generate_elements(
            {}, rloan_data=self._mortgage_with_common(FCAReferenceNumber="FCA99999")
        )
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_business_purpose_false(self):
        page = _page()
        result = page.generate_elements(
            {}, rloan_data=self._mortgage_with_common(BusinessOrCommercialPurpose=False)
        )
        assert isinstance(result, list)

    def test_business_purpose_true(self):
        page = _page()
        result = page.generate_elements(
            {}, rloan_data=self._mortgage_with_common(BusinessOrCommercialPurpose=True)
        )
        assert isinstance(result, list)

    def test_advised_flag(self):
        page = _page()
        result = page.generate_elements(
            {}, rloan_data=self._mortgage_with_common(AdvisedFlag=True)
        )
        assert isinstance(result, list)

    def test_multiple_regulatory_flags(self):
        page = _page()
        mortgage = _make_mortgage({"Common": {
            "FCAReferenceNumber": "FCA123",
            "AdvisedFlag": True,
            "ExecutionOnlyFlag": False,
            "InteractiveSaleFlag": True,
            "DistanceMarketingFlag": False,
            "RecordKeepingCompliantFlag": True,
            "VulnerableCustomerFlag": False,
        }})
        result = page.generate_elements({}, rloan_data=mortgage)
        assert isinstance(result, list)


# ===========================================================================
# MCOB section
# ===========================================================================

class TestMcobSection:

    def _mortgage_mcob(self, **kwargs):
        mcob = {
            "MMRCompliantFlag": True,
            "CrossBorderPassportingFlag": False,
            "OriginatingMemberState": "UK",
            "ESISProvidedDate": "2024-01-15",
            "ESISVersion": "2.0",
            "CoolingOffPeriodDays": 14,
            "ForeignCurrencyLoanFlag": False,
            "ExchangeRateProtectionType": "Fixed",
            "AdviceRejectionFlag": False,
            "APRCInitialRate": 0.05,
            "APRCSecondaryRate": 0.045,
            "StressTestCompliantFlag": True,
            "AffordabilityAssessmentDate": "2024-01-10",
            "SuitabilityAssessmentDate": "2024-01-10",
            "InitialDisclosureProvidedDate": "2024-01-05",
            "InitialDisclosureMethod": "Electronic",
            "CancellationRightsFlag": True,
            "MortgageClubCode": "MC001",
            "IntermediaryCode": "INT001",
            "AdviceRetentionPeriod": 5,
            **kwargs,
        }
        return _make_mortgage({"MCOB": mcob})

    def test_mcob_section_creates_tables(self):
        page = _page()
        result = page.generate_elements({}, rloan_data=self._mortgage_mcob())
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 2  # main MCOB table + advice table

    def test_mcob_with_minimal_fields(self):
        page = _page()
        mortgage = _make_mortgage({"MCOB": {"MMRCompliantFlag": True}})
        result = page.generate_elements({}, rloan_data=mortgage)
        assert isinstance(result, list)

    def test_mcob_all_fields_returns_list(self):
        page = _page()
        result = page.generate_elements({}, rloan_data=self._mortgage_mcob())
        assert isinstance(result, list)
        assert len(result) > 5

    def test_mcob_advice_rejection_reason(self):
        page = _page()
        mortgage = _make_mortgage({"MCOB": {
            "AdviceRejectionFlag": True,
            "AdviceRejectionReason": "Client refused to take advice",
        }})
        result = page.generate_elements({}, rloan_data=mortgage)
        assert isinstance(result, list)


# ===========================================================================
# HMDA section
# ===========================================================================

class TestHmdaSection:

    def _mortgage_hmda(self, **kwargs):
        hmda = {
            "HMDAReportableFlag": True,
            "HMDAHOEPAStatus": False,
            "HMDARateSpread": 2.5,
            "ManufacturedHomeSecured": False,
            "ManufacturedHomeLandPropertyInterest": "Direct",
            **kwargs,
        }
        return _make_mortgage({"HMDA": hmda})

    def test_hmda_section_creates_table(self):
        page = _page()
        result = page.generate_elements({}, rloan_data=self._mortgage_hmda())
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_hmda_minimal_fields(self):
        page = _page()
        mortgage = _make_mortgage({"HMDA": {"HMDAReportableFlag": True}})
        result = page.generate_elements({}, rloan_data=mortgage)
        assert isinstance(result, list)

    def test_hmda_rate_spread_formatted(self):
        page = _page()
        result = page.generate_elements({}, rloan_data=self._mortgage_hmda())
        assert isinstance(result, list)


# ===========================================================================
# Combined sections + edge cases
# ===========================================================================

class TestCombinedSections:

    def test_all_sections_together(self):
        page = _page()
        mortgage = _make_mortgage({
            "Common": {"FCAReferenceNumber": "FCA123"},
            "MCOB": {"MMRCompliantFlag": True, "CoolingOffPeriodDays": 14},
            "HMDA": {"HMDAReportableFlag": True},
        })
        result = page.generate_elements({}, rloan_data=mortgage)
        assert isinstance(result, list)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 2

    def test_flat_mortgage_structure(self):
        """rloan_data without 'Mortgage' key → uses top-level."""
        page = _page()
        result = page.generate_elements({}, rloan_data={"Regulatory": {}})
        # Should handle flat structure
        assert isinstance(result, list)

    def test_exception_handled_gracefully(self):
        """Feeding bad data (non-dict regulatory) exercises the except block."""
        page = _page()
        # Pass something that causes getattr failures in the regulatory section
        mortgage = {"Mortgage": {"Regulatory": "not_a_dict"}}
        result = page.generate_elements({}, rloan_data=mortgage)
        assert isinstance(result, list)
