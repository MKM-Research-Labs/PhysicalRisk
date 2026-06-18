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

"""Coverage expansion tests for Block 1 CDM base, property, and gauge modules.

Targets missing lines in:
- src/port/cdm/asset/residential/validator.py (lines 60,62,65,69-70)
- src/port/cdm/gauge/validate.py (lines 61,64,68-69)
- src/port/cdm/base.py (lines 67,81,97,116,133,154)
"""

import pytest

from port.cdm.asset.loan import LoanCDM
from port.cdm.prs import PhysicalRiskSwapCDM
from port.cdm.asset.residential.validator import validate as property_validate
from port.cdm.asset.residential.validator import get_required_fields as property_required
from port.cdm.gauge.validate import validate_gauge
from port.cdm.base import BaseCDM


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
        assert any("RLoanID" in f for f in fields)
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
        info = mortgage_cdm.get_field_info("RLoan.Header.RLoanID")
        assert info is not None
        assert info["type"] == "text"

    def test_repr(self, mortgage_cdm):
        """Line 157: __repr__ returns class name."""
        assert "LoanCDM" in repr(mortgage_cdm)

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
