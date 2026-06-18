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

"""Coverage expansion tests for Block 1 CDM validation and mapping.

Targets missing lines in:
- src/port/cdm/asset/loan.py (lines 259,262,265,268,275,278,282-283,362-363)
- src/port/cdm/prs.py (lines 232-264, 333-334)
"""

import pytest

from port.cdm.asset.loan import LoanCDM
from port.cdm.prs import PhysicalRiskSwapCDM


# ---------------------------------------------------------------------------
# LoanCDM — validate() error paths (lines 259-283)
# ---------------------------------------------------------------------------

class TestLoanCDMValidation:

    def test_validate_missing_mortgage_id(self, mortgage_cdm):
        """Line 259: Missing MortgageID produces header error."""
        data = {"Mortgage": {"Header": {"CatchmentID": "thames", "PropertyID": "PROP-1"},
                             "FinancialTerms": {"OriginalLoan": 300000}}}
        errors = mortgage_cdm.validate(data)
        assert "Header" in errors
        assert any("RLoanID" in e for e in errors["Header"])

    def test_validate_missing_catchment_id(self, mortgage_cdm):
        """Line 262: Missing CatchmentID produces header error."""
        data = {"Mortgage": {"Header": {"MortgageID": "MORT-1", "PropertyID": "PROP-1"},
                             "FinancialTerms": {"OriginalLoan": 300000}}}
        errors = mortgage_cdm.validate(data)
        assert "Header" in errors
        assert any("CatchmentID" in e for e in errors["Header"])

    def test_validate_missing_property_id(self, mortgage_cdm):
        """Line 265: Missing PropertyID produces header error."""
        data = {"Mortgage": {"Header": {"MortgageID": "MORT-1", "CatchmentID": "thames"},
                             "FinancialTerms": {"OriginalLoan": 300000}}}
        errors = mortgage_cdm.validate(data)
        assert "Header" in errors
        assert any("PropertyID" in e for e in errors["Header"])

    def test_validate_header_errors_collected(self, mortgage_cdm):
        """Line 268: header_errors list appended to errors dict when non-empty."""
        data = {"Mortgage": {"Header": {},
                             "FinancialTerms": {"OriginalLoan": 300000}}}
        errors = mortgage_cdm.validate(data)
        assert "Header" in errors
        assert len(errors["Header"]) >= 2

    def test_validate_missing_original_loan(self, mortgage_cdm):
        """Line 275: Missing OriginalLoan produces FinancialTerms error."""
        data = {"Mortgage": {"Header": {"MortgageID": "MORT-1", "CatchmentID": "thames",
                                         "PropertyID": "PROP-1"},
                             "FinancialTerms": {}}}
        errors = mortgage_cdm.validate(data)
        assert "FinancialTerms" in errors
        assert any("OriginalLoan" in e for e in errors["FinancialTerms"])

    def test_validate_terms_errors_collected(self, mortgage_cdm):
        """Line 278: terms_errors appended when non-empty."""
        data = {"Mortgage": {"Header": {"MortgageID": "MORT-1", "CatchmentID": "thames",
                                         "PropertyID": "PROP-1"},
                             "FinancialTerms": {}}}
        errors = mortgage_cdm.validate(data)
        assert "FinancialTerms" in errors

    def test_validate_exception_returns_error_dict(self, mortgage_cdm):
        """Lines 282-283: exception in validate returns validation_error."""
        result = mortgage_cdm.validate(None)
        assert "validation_error" in result
        assert isinstance(result["validation_error"], list)

    def test_validate_all_valid_returns_empty(self, mortgage_cdm):
        """Line 280: valid data returns empty dict."""
        data = {"Mortgage": {"Header": {"MortgageID": "MORT-1", "CatchmentID": "thames",
                                         "PropertyID": "PROP-1"},
                             "FinancialTerms": {"OriginalLoan": 300000}}}
        assert mortgage_cdm.validate(data) == {}


# ---------------------------------------------------------------------------
# LoanCDM — create_mapping() exception (lines 362-363)
# ---------------------------------------------------------------------------

class TestLoanCDMMapping:

    def test_create_mapping_exception_raises_value_error(self, mortgage_cdm):
        """Lines 362-363: exception in create_mapping raises ValueError."""
        with pytest.raises((ValueError, AttributeError)):
            mortgage_cdm.create_mapping(None)


# ---------------------------------------------------------------------------
# PhysicalRiskSwapCDM — validate() full coverage (lines 232-264)
# ---------------------------------------------------------------------------

class TestPRSCDMValidation:

    def test_validate_missing_swap_id(self, prs_cdm):
        """Line 238-239: Missing SwapID."""
        data = {"PhysicalSwap": {"Header": {"CatchmentID": "thames"},
                                 "GaugeSet": {"GaugeSetID": "GS-1",
                                              "GaugeBasket": [{"GaugeID": "G-1"}]}}}
        errors = prs_cdm.validate(data)
        assert "Header" in errors
        assert any("SwapID" in e for e in errors["Header"])

    def test_validate_missing_catchment_id(self, prs_cdm):
        """Line 241-242: Missing CatchmentID."""
        data = {"PhysicalSwap": {"Header": {"SwapID": "PRS-1"},
                                 "GaugeSet": {"GaugeSetID": "GS-1",
                                              "GaugeBasket": [{"GaugeID": "G-1"}]}}}
        errors = prs_cdm.validate(data)
        assert "Header" in errors
        assert any("CatchmentID" in e for e in errors["Header"])

    def test_validate_header_errors_appended(self, prs_cdm):
        """Lines 244-245: header errors collected."""
        data = {"PhysicalSwap": {"Header": {},
                                 "GaugeSet": {"GaugeSetID": "GS-1",
                                              "GaugeBasket": [{"GaugeID": "G-1"}]}}}
        errors = prs_cdm.validate(data)
        assert "Header" in errors
        assert len(errors["Header"]) >= 2

    def test_validate_missing_gauge_set_id(self, prs_cdm):
        """Line 251-252: Missing GaugeSetID."""
        data = {"PhysicalSwap": {"Header": {"SwapID": "PRS-1", "CatchmentID": "thames"},
                                 "GaugeSet": {"GaugeBasket": [{"GaugeID": "G-1"}]}}}
        errors = prs_cdm.validate(data)
        assert "GaugeSet" in errors
        assert any("GaugeSetID" in e for e in errors["GaugeSet"])

    def test_validate_empty_gauge_basket(self, prs_cdm):
        """Lines 255-256: Empty GaugeBasket."""
        data = {"PhysicalSwap": {"Header": {"SwapID": "PRS-1", "CatchmentID": "thames"},
                                 "GaugeSet": {"GaugeSetID": "GS-1", "GaugeBasket": []}}}
        errors = prs_cdm.validate(data)
        assert "GaugeSet" in errors
        assert any("GaugeBasket" in e for e in errors["GaugeSet"])

    def test_validate_blank_gauge_id_in_basket(self, prs_cdm):
        """Gauge basket entry with blank GaugeID must fail validation."""
        data = {"PhysicalSwap": {"Header": {"SwapID": "PRS-1", "CatchmentID": "thames"},
                                 "GaugeSet": {"GaugeSetID": "GS-1",
                                              "GaugeBasket": [{"GaugeID": ""}]}}}
        errors = prs_cdm.validate(data)
        assert "GaugeSet" in errors
        assert any("GaugeID" in e for e in errors["GaugeSet"])

    def test_validate_missing_gauge_id_in_basket(self, prs_cdm):
        """Gauge basket entry with no GaugeID key must fail validation."""
        data = {"PhysicalSwap": {"Header": {"SwapID": "PRS-1", "CatchmentID": "thames"},
                                 "GaugeSet": {"GaugeSetID": "GS-1",
                                              "GaugeBasket": [{"Weight": 1.0}]}}}
        errors = prs_cdm.validate(data)
        assert "GaugeSet" in errors
        assert any("GaugeID" in e for e in errors["GaugeSet"])

    def test_validate_gauge_errors_appended(self, prs_cdm):
        """Lines 258-259: gauge errors collected."""
        data = {"PhysicalSwap": {"Header": {"SwapID": "PRS-1", "CatchmentID": "thames"},
                                 "GaugeSet": {}}}
        errors = prs_cdm.validate(data)
        assert "GaugeSet" in errors

    def test_validate_valid_returns_empty(self, prs_cdm):
        """Line 261: valid data returns empty dict."""
        data = {"PhysicalSwap": {"Header": {"SwapID": "PRS-1", "CatchmentID": "thames"},
                                 "GaugeSet": {"GaugeSetID": "GS-1",
                                              "GaugeBasket": [{"GaugeID": "G-1"}]}}}
        assert prs_cdm.validate(data) == {}

    def test_validate_empty_data(self, prs_cdm):
        """validate({}) returns errors."""
        errors = prs_cdm.validate({})
        assert isinstance(errors, dict)

    def test_validate_exception_returns_error_dict(self, prs_cdm):
        """Lines 263-264: exception returns validation_error."""
        result = prs_cdm.validate(None)
        assert "validation_error" in result


# ---------------------------------------------------------------------------
# PhysicalRiskSwapCDM — create_mapping() exception (lines 333-334)
# ---------------------------------------------------------------------------

class TestPRSCDMMapping:

    def test_create_mapping_exception_raises_value_error(self, prs_cdm):
        """Lines 333-334: exception in create_mapping raises ValueError."""
        with pytest.raises((ValueError, AttributeError)):
            prs_cdm.create_mapping(None)

    def test_create_mapping_full_data(self, prs_cdm):
        """Verify all sections of create_mapping produce correct keys."""
        data = {
            "PhysicalSwap": {
                "Header": {"SwapID": "PRS-1", "CatchmentID": "thames",
                           "TradeType": "PRS", "CounterParty": "CTPY-1",
                           "PartyId": "LEI-1", "ValuationDate": "2026-01-01",
                           "GaugeSetID": "GS-1", "ProtectionStart": "2026-01-01"},
                "LegData": {"LegType": "Fixed", "Payer": True, "Currency": "GBP",
                            "Notional": 1000000, "DayCounter": "ACT/365",
                            "FixedLegRate": 0.05},
                "ScheduleData": {"StartDate": "2026-01-01", "EndDate": "2027-01-01",
                                 "Tenor": "1Y", "Calendar": "London"},
                "GaugeSet": {"CatchmentID": "thames", "GaugeCount": 5,
                             "GaugeBasket": [{"GaugeID": "G-1", "Weight": 0.5}]},
                "Triggers": {"TriggerType": "Any", "TriggerThreshold": 1,
                             "FloodAlertTrigger": 3.0, "FloodWarningTrigger": 4.5,
                             "SevereFloodTrigger": 5.5},
                "Payouts": {"Currency": "GBP", "FloodAlertPayout": 10000,
                            "FloodWarningPayout": 50000, "SevereFloodPayout": 100000,
                            "MaxPayout": 200000},
            }
        }
        mapping = prs_cdm.create_mapping(data)
        assert mapping["swap_id"] == "PRS-1"
        assert mapping["notional"] == 1000000
        assert mapping["trigger_type"] == "Any"
        assert mapping["max_payout"] == 200000
        assert mapping["gauge_count"] == 5
