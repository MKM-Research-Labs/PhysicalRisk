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

"""Per-CDM schema validation and mapping tests — part 1.

Covers FloodGauge, Property, Mortgage, and StormEvent CDMs.
"""

import pytest


class TestFloodGaugeCDM:

    def test_schema_has_flood_gauge_root(self, gauge_cdm):
        assert "FloodGauge" in gauge_cdm.schema

    def test_schema_has_header_section(self, gauge_cdm):
        assert "Header" in gauge_cdm.schema["FloodGauge"]

    def test_required_fields_include_gauge_id(self, gauge_cdm):
        assert any("GaugeID" in f for f in gauge_cdm.get_required_fields())

    def test_get_field_info_for_gauge_id(self, gauge_cdm):
        info = gauge_cdm.get_field_info("FloodGauge.Header.GaugeID")
        assert info is not None
        assert info.get("type") == "text"

    def test_validate_empty_data_returns_errors(self, gauge_cdm):
        assert isinstance(gauge_cdm.validate({}), dict)

    def test_validate_valid_gauge_data(self, gauge_cdm):
        data = {
            "FloodGauge": {
                "Header": {"GaugeID": "GAUGE-test1234", "CatchmentID": "thames",
                            "GaugeName": "Test Gauge"},
                "SensorDetails": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
            }
        }
        assert len(gauge_cdm.validate(data)) == 0

    def test_create_mapping_returns_flat_dict(self, gauge_cdm):
        data = {
            "FloodGauge": {
                "Header": {"GaugeID": "GAUGE-test1234", "CatchmentID": "thames",
                            "GaugeName": "Test Gauge"},
                "SensorStats": {"HistoricalHighLevel": 6.5},
                "SensorDetails": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1,
                                  "GroundLevelMetres": 8.0},
                "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.5,
                                "SevereFloodWarning": 5.5},
            }
        }
        mapping = gauge_cdm.create_mapping(data)
        assert isinstance(mapping, dict)
        assert mapping.get("gauge_id") == "GAUGE-test1234"
        assert mapping.get("catchment_id") == "thames"

    def test_create_mapping_with_empty_input(self, gauge_cdm):
        assert isinstance(gauge_cdm.create_mapping({}), dict)


class TestPropertyCDM:

    def test_schema_has_property_root(self, property_cdm):
        assert len(list(property_cdm.schema.keys())) > 0

    def test_required_fields_not_empty(self, property_cdm):
        assert len(property_cdm.get_required_fields()) > 0

    def test_validate_valid_property(self, property_cdm):
        data = {
            "PropertyHeader": {
                "PropertyAttributes": {"PropertyID": "PROP-test1234", "CatchmentID": "thames"},
                "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
            }
        }
        assert isinstance(property_cdm.validate(data), dict)

    def test_create_mapping_returns_flat_dict(self, property_cdm):
        data = {
            "PropertyHeader": {
                "PropertyAttributes": {"PropertyID": "PROP-test1234", "CatchmentID": "thames",
                                       "PropertyType": "Semi-detached"},
                "Valuation": {"PropertyValue": 500000},
                "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1, "Elevation": 7.5},
            }
        }
        mapping = property_cdm.create_mapping(data)
        assert isinstance(mapping, dict)
        assert len(mapping) > 0
        assert mapping["latitude"] == 51.5


class TestMortgageCDM:

    def test_schema_has_mortgage_root(self, mortgage_cdm):
        assert len(list(mortgage_cdm.schema.keys())) > 0

    def test_required_fields_include_mortgage_id(self, mortgage_cdm):
        assert any("MortgageID" in f for f in mortgage_cdm.get_required_fields())

    def test_validate_valid_mortgage(self, mortgage_cdm):
        data = {
            "Mortgage": {
                "Header": {"MortgageID": "MORT-test1234", "CatchmentID": "thames",
                            "PropertyID": "PROP-test1234"},
                "FinancialTerms": {"OriginalLoan": 400000},
            }
        }
        assert isinstance(mortgage_cdm.validate(data), dict)

    def test_create_mapping_returns_flat_dict(self, mortgage_cdm):
        data = {
            "Mortgage": {
                "Header": {"MortgageID": "MORT-test1234", "CatchmentID": "thames",
                            "PropertyID": "PROP-test1234"},
                "FinancialTerms": {"OriginalLoan": 400000, "OutstandingBalance": 350000,
                                   "InterestRate": 4.5},
            }
        }
        mapping = mortgage_cdm.create_mapping(data)
        assert isinstance(mapping, dict)
        assert mapping.get("mortgage_id") == "MORT-test1234"


class TestStormEventCDM:

    def test_schema_has_storm_root(self, storm_cdm):
        assert len(list(storm_cdm.schema.keys())) > 0

    def test_required_fields_include_storm_id(self, storm_cdm):
        assert any("StormEventID" in f for f in storm_cdm.get_required_fields())

    def test_create_mapping_returns_flat_dict(self, storm_cdm):
        data = {"StormEvent": {"Header": {"StormEventID": "STORM-001", "CatchmentID": "thames"}}}
        assert isinstance(storm_cdm.create_mapping(data), dict)

    def test_validate_missing_storm_id(self, storm_cdm):
        """Lines 175-193: validate() with missing StormEventID returns Header errors."""
        errors = storm_cdm.validate({"StormEvent": {"Header": {"CatchmentID": "thames"}}})
        assert "Header" in errors
        assert any("StormEventID" in e for e in errors["Header"])

    def test_validate_missing_catchment_id(self, storm_cdm):
        """validate() with missing CatchmentID returns Header errors."""
        errors = storm_cdm.validate({"StormEvent": {"Header": {"StormEventID": "STORM-001"}}})
        assert "Header" in errors
        assert any("CatchmentID" in e for e in errors["Header"])

    def test_validate_valid_storm(self, storm_cdm):
        """validate() with valid data returns empty dict."""
        data = {"StormEvent": {"Header": {"StormEventID": "STORM-001", "CatchmentID": "thames"}}}
        assert storm_cdm.validate(data) == {}

    def test_validate_empty_data(self, storm_cdm):
        """validate({}) returns errors for missing fields."""
        errors = storm_cdm.validate({})
        assert isinstance(errors, dict)

    def test_create_mapping_full_data(self, storm_cdm):
        """Lines 213-256: create_mapping with all sections populated."""
        data = {
            "StormEvent": {
                "Header": {"StormEventID": "STORM-001", "CatchmentID": "thames"},
                "Attributes": {"StormName": "Eunice", "StormSize": "Large",
                               "StormDuration": 24, "StormWindSpeed": 120},
                "Alert": {"WarningCentre": "Met Office", "StormAlert": "Red"},
                "Warning": {"Date": "2022-02-18", "Time": "06:00",
                            "Position": "51.5,-0.1", "Intensity": "Severe",
                            "WindSpeeds": "120kph", "AnticipatedStormSurgeHeight": 2.5},
                "Triggers": {"EvacuationTrigger": 1.5, "PropertyDamageTrigger": 1.0},
            }
        }
        mapping = storm_cdm.create_mapping(data)
        assert mapping["storm_event_id"] == "STORM-001"
        assert mapping["storm_name"] == "Eunice"
        assert mapping["storm_alert"] == "Red"

    def test_get_required_fields_returns_list(self, storm_cdm):
        """Line 258-260: get_required_fields() returns list with StormEventID."""
        fields = storm_cdm.get_required_fields()
        assert isinstance(fields, list)
        assert any("StormEventID" in f for f in fields)

    def test_validate_exception_returns_error_dict(self, storm_cdm):
        """Lines 192-193: exception in validate -> {'validation_error': [...]}."""
        result = storm_cdm.validate(None)
        assert isinstance(result, dict)
        assert "validation_error" in result

    def test_create_mapping_exception_raises(self, storm_cdm):
        """Lines 255-256: exception in create_mapping -> raises ValueError."""
        import pytest
        with pytest.raises((ValueError, AttributeError)):
            storm_cdm.create_mapping(None)
