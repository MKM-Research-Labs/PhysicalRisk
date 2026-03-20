# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Coverage expansion tests for Block 1 CDM files.

Targets missing lines in:
- src/port/cdm/mortgage.py (lines 259,262,265,268,275,278,282-283,362-363)
- src/port/cdm/prs.py (lines 232-264, 333-334)
- src/port/cdm/property/validator.py (lines 60,62,65,69-70)
- src/port/cdm/gauge/validate.py (lines 61,64,68-69)
- src/port/cdm/base.py (lines 67,81,97,116,133,154)
"""

import pytest

from port.cdm.mortgage import MortgageCDM
from port.cdm.prs import PhysicalRiskSwapCDM
from port.cdm.property.validator import validate as property_validate
from port.cdm.property.validator import get_required_fields as property_required
from port.cdm.gauge.validate import validate_gauge
from port.cdm.base import BaseCDM


# ---------------------------------------------------------------------------
# MortgageCDM — validate() error paths (lines 259-283)
# ---------------------------------------------------------------------------

class TestMortgageCDMValidation:

    def test_validate_missing_mortgage_id(self, mortgage_cdm):
        """Line 259: Missing MortgageID produces header error."""
        data = {"Mortgage": {"Header": {"CatchmentID": "thames", "PropertyID": "PROP-1"},
                             "FinancialTerms": {"OriginalLoan": 300000}}}
        errors = mortgage_cdm.validate(data)
        assert "Header" in errors
        assert any("MortgageID" in e for e in errors["Header"])

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
# MortgageCDM — create_mapping() exception (lines 362-363)
# ---------------------------------------------------------------------------

class TestMortgageCDMMapping:

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


# ---------------------------------------------------------------------------
# Property validator — location validation + exception (lines 60,62,65,69-70)
# ---------------------------------------------------------------------------

class TestPropertyValidator:

    def test_missing_latitude(self):
        """Line 60: Missing LatitudeDegrees."""
        data = {"PropertyHeader": {
            "Header": {"PropertyID": "PROP-1", "CatchmentID": "thames"},
            "Location": {"LongitudeDegrees": -0.1}}}
        errors = property_validate(data)
        assert "Location" in errors
        assert any("LatitudeDegrees" in e for e in errors["Location"])

    def test_missing_longitude(self):
        """Line 62: Missing LongitudeDegrees."""
        data = {"PropertyHeader": {
            "Header": {"PropertyID": "PROP-1", "CatchmentID": "thames"},
            "Location": {"LatitudeDegrees": 51.5}}}
        errors = property_validate(data)
        assert "Location" in errors
        assert any("LongitudeDegrees" in e for e in errors["Location"])

    def test_location_errors_collected(self):
        """Line 65: location_errors appended when non-empty."""
        data = {"PropertyHeader": {
            "Header": {"PropertyID": "PROP-1", "CatchmentID": "thames"},
            "Location": {}}}
        errors = property_validate(data)
        assert "Location" in errors
        assert len(errors["Location"]) == 2

    def test_exception_returns_validation_error(self):
        """Lines 69-70: exception returns validation_error dict."""
        result = property_validate(None)
        assert "validation_error" in result
        assert isinstance(result["validation_error"], list)

    def test_valid_returns_empty(self):
        """Valid data returns no errors."""
        data = {"PropertyHeader": {
            "Header": {"PropertyID": "PROP-1", "CatchmentID": "thames"},
            "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1}}}
        assert property_validate(data) == {}

    def test_get_required_fields(self):
        """get_required_fields returns expected paths."""
        fields = property_required()
        assert len(fields) == 4
        assert "PropertyHeader.Header.PropertyID" in fields
        assert "PropertyHeader.Location.LatitudeDegrees" in fields


# ---------------------------------------------------------------------------
# Gauge validate — sensor menu validation + exception (lines 61,64,68-69)
# ---------------------------------------------------------------------------

class TestGaugeValidate:

    def test_invalid_menu_value_produces_sensor_error(self):
        """Lines 61,64: invalid menu field value appended to sensor_errors."""
        data = {"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-1", "CatchmentID": "thames"},
            "SensorDetails": {"GaugeInformation": {
                "DataSourceType": "InvalidSource"}}}}
        errors = validate_gauge(data)
        assert "SensorDetails" in errors
        assert any("DataSourceType" in e for e in errors["SensorDetails"])

    def test_multiple_invalid_menu_values(self):
        """Multiple invalid menu fields all collected."""
        data = {"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-1", "CatchmentID": "thames"},
            "SensorDetails": {"GaugeInformation": {
                "DataSourceType": "Bad",
                "GaugeType": "Bad",
                "OperationalStatus": "Bad"}}}}
        errors = validate_gauge(data)
        assert "SensorDetails" in errors
        assert len(errors["SensorDetails"]) == 3

    def test_valid_menu_values_no_sensor_errors(self):
        """Valid menu field values produce no SensorDetails errors."""
        data = {"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-1", "CatchmentID": "thames"},
            "SensorDetails": {"GaugeInformation": {
                "DataSourceType": "SensorGauge",
                "GaugeType": "Radar gauge",
                "OperationalStatus": "Fully operational"}}}}
        errors = validate_gauge(data)
        assert "SensorDetails" not in errors

    def test_exception_returns_validation_error(self):
        """Lines 68-69: exception returns validation_error dict."""
        result = validate_gauge(None)
        assert "validation_error" in result
        assert isinstance(result["validation_error"], list)


# ---------------------------------------------------------------------------
# BaseCDM — abstract bodies + get_field_info/list_all_fields/get_required_fields
# (lines 67,81,97,116,133,154)
# ---------------------------------------------------------------------------

class TestBaseCDMCoverage:

    def test_get_field_info_not_found_returns_none(self, mortgage_cdm):
        """Line 116: field path not found returns None."""
        assert mortgage_cdm.get_field_info("Mortgage.Nonexistent.Field") is None

    def test_get_field_info_partial_path_returns_none(self, mortgage_cdm):
        """Line 116: partial path that resolves to non-dict returns None."""
        assert mortgage_cdm.get_field_info("Nonexistent") is None

    def test_list_all_fields_returns_nested_paths(self, mortgage_cdm):
        """Line 133: list_all_fields recurses nested sections."""
        fields = mortgage_cdm.list_all_fields()
        assert isinstance(fields, list)
        assert len(fields) > 10
        assert any("MortgageID" in f for f in fields)
        assert any("OriginalLoan" in f for f in fields)

    def test_list_all_fields_prs(self, prs_cdm):
        """list_all_fields on PRS CDM covers nested GaugeSet section."""
        fields = prs_cdm.list_all_fields()
        assert any("GaugeSet" in f for f in fields)
        assert any("Triggers" in f for f in fields)

    def test_base_get_required_fields_default(self):
        """Line 154: BaseCDM.get_required_fields returns empty list by default."""
        class MinimalCDM(BaseCDM):
            @property
            def schema(self):
                return {"Root": {"Field": {"type": "text", "description": "test"}}}
            def validate(self, data):
                return {}
            def create_mapping(self, raw_data):
                return {}

        cdm = MinimalCDM()
        assert cdm.get_required_fields() == []

    def test_get_field_info_leaf_returns_dict(self, mortgage_cdm):
        """get_field_info on a leaf field returns its definition."""
        info = mortgage_cdm.get_field_info("Mortgage.Header.MortgageID")
        assert info is not None
        assert info["type"] == "text"

    def test_repr(self, mortgage_cdm):
        """Line 157: __repr__ returns class name."""
        assert "MortgageCDM" in repr(mortgage_cdm)

    def test_list_all_fields_skips_metadata_keys(self):
        """Line 133: 'type', 'options', 'values', 'description', 'items' are skipped."""
        class MetadataCDM(BaseCDM):
            @property
            def schema(self):
                # Section has NO 'type' key at its own level, so it is treated
                # as a nested section.  The metadata keys (options, values, etc.)
                # should be skipped during iteration, leaving only RealField.
                return {
                    "Section": {
                        "description": "A section",  # metadata key — skipped
                        "options": ["a", "b"],        # metadata key — skipped
                        "values": {"x": 1},           # metadata key — skipped
                        "items": {"y": 2},            # metadata key — skipped
                        "RealField": {"type": "text", "description": "actual field"},
                    }
                }
            def validate(self, data):
                return {}
            def create_mapping(self, raw_data):
                return {}

        cdm = MetadataCDM()
        fields = cdm.list_all_fields()
        # Only RealField should appear; metadata keys should be skipped
        assert len(fields) == 1
        assert fields[0] == "Section.RealField"

    def test_list_all_fields_nested_metadata_keys(self):
        """Line 133: metadata keys at nested level are also skipped."""
        class NestedMetaCDM(BaseCDM):
            @property
            def schema(self):
                return {
                    "Root": {
                        "options": {"val1": "opt1"},  # metadata — skipped
                        "Sub": {
                            "values": [1, 2, 3],       # metadata — skipped
                            "Name": {"type": "text", "description": "name"},
                        },
                    }
                }
            def validate(self, data):
                return {}
            def create_mapping(self, raw_data):
                return {}

        cdm = NestedMetaCDM()
        fields = cdm.list_all_fields()
        assert "Root.Sub.Name" in fields
        # 'options' and 'values' should not appear as field paths
        path_parts = [p.split('.')[-1] for p in fields]
        assert 'options' not in path_parts
        assert 'values' not in path_parts

    def test_get_field_info_returns_none_for_non_dict_leaf(self):
        """Line 118: get_field_info returns None when leaf is not a dict."""
        class LeafCDM(BaseCDM):
            @property
            def schema(self):
                return {"Root": {"Field": "just_a_string"}}
            def validate(self, data):
                return {}
            def create_mapping(self, raw_data):
                return {}

        cdm = LeafCDM()
        assert cdm.get_field_info("Root.Field") is None


# ---------------------------------------------------------------------------
# PRS CDM — custom gauge_basket_size
# ---------------------------------------------------------------------------

class TestPRSCDMInit:

    def test_default_gauge_basket_size(self):
        cdm = PhysicalRiskSwapCDM()
        assert cdm.gauge_basket_size == 20

    def test_custom_gauge_basket_size(self):
        cdm = PhysicalRiskSwapCDM(gauge_basket_size=10)
        assert cdm.gauge_basket_size == 10
