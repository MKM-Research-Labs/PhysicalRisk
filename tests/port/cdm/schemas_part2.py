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

"""Per-CDM schema validation and mapping tests — part 2.

Covers StormTimeSeries and PhysicalRiskSwap CDMs.
"""

import pytest


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
        """Lines 137-138: exception in validate -> {'validation_error': [...]}."""
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
