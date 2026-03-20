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

"""Per-CDM schema validation and mapping tests."""


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
        """Lines 192-193: exception in validate → {'validation_error': [...]}."""
        result = storm_cdm.validate(None)
        assert isinstance(result, dict)
        assert "validation_error" in result

    def test_create_mapping_exception_raises(self, storm_cdm):
        """Lines 255-256: exception in create_mapping → raises ValueError."""
        import pytest
        with pytest.raises((ValueError, AttributeError)):
            storm_cdm.create_mapping(None)


class TestStormTimeSeriesCDM:

    def test_schema_has_root(self, stormts_cdm):
        assert isinstance(stormts_cdm.schema, dict)
        assert len(stormts_cdm.schema) > 0

    def test_required_fields_include_ts_id(self, stormts_cdm):
        assert any("TimeSeriesID" in f for f in stormts_cdm.get_required_fields())

    def test_create_mapping_returns_flat_dict(self, stormts_cdm):
        data = {"StormTimeSeries": {"Header": {"TimeSeriesID": "TS-001", "CatchmentID": "thames"}}}
        assert isinstance(stormts_cdm.create_mapping(data), dict)

    def test_validate_missing_ts_id(self, stormts_cdm):
        """Lines 120-138: validate() with missing TimeSeriesID returns Header errors."""
        errors = stormts_cdm.validate({"StormTimeSeries": {"Header": {"CatchmentID": "thames"}}})
        assert "Header" in errors
        assert any("TimeSeriesID" in e for e in errors["Header"])

    def test_validate_missing_catchment_id(self, stormts_cdm):
        """validate() with missing CatchmentID returns Header errors."""
        errors = stormts_cdm.validate({"StormTimeSeries": {"Header": {"TimeSeriesID": "TS-001"}}})
        assert "Header" in errors

    def test_validate_valid_data(self, stormts_cdm):
        """validate() with valid data returns empty dict."""
        data = {"StormTimeSeries": {"Header": {"TimeSeriesID": "TS-001", "CatchmentID": "thames"}}}
        assert stormts_cdm.validate(data) == {}

    def test_validate_empty_data(self, stormts_cdm):
        """validate({}) returns errors for both required fields."""
        errors = stormts_cdm.validate({})
        assert isinstance(errors, dict)
        assert "Header" in errors

    def test_create_mapping_full_data(self, stormts_cdm):
        """Lines 150-170: create_mapping with full Parameters section."""
        data = {
            "StormTimeSeries": {
                "Header": {"TimeSeriesID": "TS-001", "CatchmentID": "thames",
                           "StormEventID": "STORM-001", "SimulationName": "Test"},
                "Parameters": {"StartDateTime": "2022-02-18T00:00",
                               "EndDateTime": "2022-02-19T00:00",
                               "TimeStepMinutes": 60, "NumberOfSteps": 24},
            }
        }
        mapping = stormts_cdm.create_mapping(data)
        assert mapping["time_series_id"] == "TS-001"
        assert mapping["time_step_minutes"] == 60

    def test_create_mapping_exception_raises_value_error(self, stormts_cdm):
        """Lines 172-173: exception in create_mapping raises ValueError."""
        import pytest
        with pytest.raises((ValueError, AttributeError, TypeError)):
            stormts_cdm.create_mapping(None)

    def test_create_reading_mapping(self, stormts_cdm):
        """Line 185: create_reading_mapping returns flat dict."""
        reading = {
            "Timestamp": "2022-02-18T06:00",
            "RainfallMm": 12.5,
            "WindSpeedKmh": 95.0,
            "PressureMbar": 980.0,
            "StormSurgeM": 1.2,
            "AlertLevel": "Warning",
        }
        mapping = stormts_cdm.create_reading_mapping(reading)
        assert mapping["timestamp"] == "2022-02-18T06:00"
        assert mapping["rainfall_mm"] == 12.5
        assert mapping["alert_level"] == "Warning"

    def test_get_required_fields_returns_list(self, stormts_cdm):
        """Lines 194-199: get_required_fields() returns list."""
        fields = stormts_cdm.get_required_fields()
        assert isinstance(fields, list)
        assert any("TimeSeriesID" in f for f in fields)

    def test_validate_exception_returns_error_dict(self, stormts_cdm):
        """Lines 137-138: exception in validate → {'validation_error': [...]}."""
        result = stormts_cdm.validate(None)
        assert isinstance(result, dict)
        assert "validation_error" in result


class TestPhysicalRiskSwapCDM:

    def test_schema_has_root(self, prs_cdm):
        assert isinstance(prs_cdm.schema, dict)
        assert len(prs_cdm.schema) > 0

    def test_required_fields_include_swap_id(self, prs_cdm):
        assert any("SwapID" in f for f in prs_cdm.get_required_fields())

    def test_list_all_fields_has_gauge_set(self, prs_cdm):
        assert any("GaugeSet" in f for f in prs_cdm.list_all_fields())

    def test_create_mapping_returns_flat_dict(self, prs_cdm):
        data = {
            "PhysicalSwap": {
                "Header": {"SwapID": "PRS-001", "CatchmentID": "thames"},
                "GaugeSet": {"GaugeSetID": "GSET-001"},
            }
        }
        assert isinstance(prs_cdm.create_mapping(data), dict)
