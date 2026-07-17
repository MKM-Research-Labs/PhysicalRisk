# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for PropertyPortfolioGenerator property values, gauge loading,
log method, processing stats, and output file structure.
"""

import json

import pytest

import database
from port.src.property.main import PropertyPortfolioGenerator
from db_helpers import test_backend, tmp_catchment

from .conftest import make_portfolio_gen, make_portfolio_params


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames") for every test in this module.

    The migrated property generator reads the gauge portfolio and writes properties
    through ``database``; rooting the backend at ``tmp_path`` means a test that
    pre-writes ``tmp_path / 'gauge.json'`` is read back by ``get_gauge_portfolio``,
    and property writes are isolated and readable via ``get_property_portfolio``."""
    with tmp_catchment(tmp_path):
        yield


# ===========================================================================
# _set_specific_property_values
# ===========================================================================

class TestSetSpecificPropertyValues:

    def test_property_id_set_in_header(self, tmp_path):
        """PropertyID lives at PropertyHeader.Header.PropertyID per schema."""
        gen = make_portfolio_gen(tmp_path)
        data = {}
        gen._set_specific_property_values(data, "PROP-abc", 0, {}, {"lat": 51.5, "lon": -0.1})
        assert data["PropertyHeader"]["Header"]["PropertyID"] == "PROP-abc"

    def test_catchment_id_set_in_header(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        data = {}
        gen._set_specific_property_values(data, "PROP-abc", 0, {}, {"lat": 51.5, "lon": -0.1})
        assert data["PropertyHeader"]["Header"]["CatchmentID"] == "thames"

    def test_lat_lon_set_in_location(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        data = {}
        gen._set_specific_property_values(data, "P", 0, {}, {"lat": 51.45, "lon": -0.31})
        loc = data["PropertyHeader"]["Location"]
        assert loc["LatitudeDegrees"] == pytest.approx(51.45)
        assert loc["LongitudeDegrees"] == pytest.approx(-0.31)

    def test_elevation_sets_ground_level(self, tmp_path):
        """GroundLevelMeters lives at PropertyHeader.RiskAssessment (sibling
        to Location), not under Location, per the current schema."""
        gen = make_portfolio_gen(tmp_path)
        data = {}
        gen._set_specific_property_values(data, "P", 0, {},
                                           {"lat": 51.5, "lon": -0.1, "elevation": 12.3})
        header = data["PropertyHeader"]
        assert header["RiskAssessment"]["GroundLevelMeters"] == pytest.approx(12.3, abs=0.01)

    def test_no_elevation_does_not_set_risk_assessment(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        data = {}
        gen._set_specific_property_values(data, "P", 0, {}, {"lat": 51.5, "lon": -0.1})
        assert "RiskAssessment" not in data["PropertyHeader"]

    def test_reference_gauges_use_synthetic_gauge_id_when_present(self, tmp_path):
        """When the location was placed relative to a synthetic gauge, the
        synthetic gauge ID takes precedence over reference_gauge_indices."""
        gen = make_portfolio_gen(tmp_path)
        gen._gauge_id_map = {0: "GAUGE-abc", 1: "GAUGE-def"}
        data = {}
        gen._set_specific_property_values(data, "P", 0, {},
                                           {"lat": 51.5, "lon": -0.1,
                                            "synthetic_gauge_id": "GAUGE-SYNTH-XYZ",
                                            "reference_gauge_indices": [0, 1]})
        # Synthetic ID wins; index-based fallback is not used
        assert data["PropertyHeader"]["ReferenceGauges"] == ["GAUGE-SYNTH-XYZ"]

    def test_reference_gauges_set_from_gauge_id_map(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        gen._gauge_id_map = {0: "GAUGE-abc", 1: "GAUGE-def", 2: "GAUGE-ghi"}
        data = {}
        gen._set_specific_property_values(data, "P", 0, {},
                                           {"lat": 51.5, "lon": -0.1,
                                            "reference_gauge_indices": [0, 1, 2]})
        ref = data["PropertyHeader"]["ReferenceGauges"]
        assert ref == ["GAUGE-abc", "GAUGE-def", "GAUGE-ghi"]

    def test_reference_gauges_fallback_when_not_in_map(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        gen._gauge_id_map = {}
        data = {}
        gen._set_specific_property_values(data, "P", 0, {},
                                           {"lat": 51.5, "lon": -0.1,
                                            "reference_gauge_indices": [0, 1, 2]})
        ref = data["PropertyHeader"]["ReferenceGauges"]
        assert ref == ["GAUGE-001", "GAUGE-002", "GAUGE-003"]

    def test_no_reference_gauge_indices_no_ref_key(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        data = {}
        gen._set_specific_property_values(data, "P", 0, {},
                                           {"lat": 51.5, "lon": -0.1})
        assert "ReferenceGauges" not in data.get("PropertyHeader", {})

    def test_empty_reference_gauge_indices_no_ref_key(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        data = {}
        gen._set_specific_property_values(data, "P", 0, {},
                                           {"lat": 51.5, "lon": -0.1,
                                            "reference_gauge_indices": []})
        assert "ReferenceGauges" not in data.get("PropertyHeader", {})


# ===========================================================================
# gauge.json loading in __init__
# ===========================================================================

class TestGaugeJsonLoading:

    def test_gauge_id_map_loaded_when_gauge_json_present(self, tmp_path):
        """When gauge.json exists with proper structure, gauge IDs are loaded."""
        gauge_data = {
            "flood_gauges": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-111"}}},
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-222"}}},
            ]
        }
        database.save_gauges(database.active_catchment(), gauge_data)  # seam (both backends)
        params = make_portfolio_params()
        gen = PropertyPortfolioGenerator(verbose=False,
                                          catchment_params=params)
        result = gen.generate(count=2)
        assert 0 in gen._gauge_id_map
        assert gen._gauge_id_map[0] == "GAUGE-111"

    def test_gauge_id_map_empty_when_no_gauge_json(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        gen.generate(count=2)
        assert isinstance(gen._gauge_id_map, dict)

    @pytest.mark.skipif(
        test_backend() == "pg",
        reason="legacy 'gauges'-only doc shape; Postgres normalises a gauge "
               "collection to 'flood_gauges' (no generator saves the legacy shape).")
    def test_gauge_id_map_works_with_gauges_key(self, tmp_path):
        """Also supports 'gauges' as the top-level key."""
        gauge_data = {
            "gauges": [
                {"FloodGauge": {"Header": {"GaugeID": "G-AAA"}}},
            ]
        }
        (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))
        params = make_portfolio_params()
        gen = PropertyPortfolioGenerator(verbose=False,
                                          catchment_params=params)
        gen.generate(count=2)
        assert gen._gauge_id_map.get(0) == "G-AAA"

    def test_corrupted_gauge_json_does_not_crash(self, tmp_path):
        (tmp_path / "gauge.json").write_text("not valid json {{")
        params = make_portfolio_params()
        gen = PropertyPortfolioGenerator(verbose=False,
                                          catchment_params=params)
        result = gen.generate(count=2)
        assert result["processing_stats"]["successful_properties"] == 2


# ===========================================================================
# log() method
# ===========================================================================

class TestLogMethod:

    def test_info_does_not_raise(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        gen.log("test", "INFO")

    def test_warning_does_not_raise(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        gen.log("test", "WARNING")

    def test_error_does_not_raise(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        gen.log("test", "ERROR")

    def test_debug_does_not_raise(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        gen.log("test", "DEBUG")

    def test_success_falls_back_gracefully(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        gen.log("success message", "SUCCESS")


# ===========================================================================
# Processing stats -- failure tracking
# ===========================================================================

class TestProcessingStatsFailureTracking:

    def test_failed_properties_tracked(self, tmp_path):
        """If a single property raises during generation, failed_properties
        increments."""
        params = make_portfolio_params()
        gen = PropertyPortfolioGenerator(verbose=False,
                                          catchment_params=params)
        original_fn = gen._generate_single_property
        call_count = [0]

        def patched(idx, schema, location):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("Injected failure")
            return original_fn(idx, schema, location)

        gen._generate_single_property = patched
        result = gen.generate(count=3)
        assert result["processing_stats"]["failed_properties"] >= 1
        assert result["processing_stats"]["successful_properties"] >= 2


# ===========================================================================
# Output file structure
# ===========================================================================

@pytest.mark.generator
class TestPropertyOutputFileStructure:

    def test_output_contains_properties_key(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        result = gen.generate(count=3)
        data = database.get_property_portfolio(result["catchment"])
        assert "properties" in data

    def test_output_contains_generation_metadata(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        result = gen.generate(count=2)
        data = database.get_property_portfolio(result["catchment"])
        meta = data["generation_metadata"]
        assert "generated_at" in meta
        assert "catchment" in meta
        assert meta["total_properties_generated"] == 2

    def test_property_header_has_property_id(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        result = gen.generate(count=3)
        for prop in result["data"]["properties"]:
            assert "PropertyHeader" in prop
            assert "PropertyAttributes" in prop["PropertyHeader"]

    def test_result_data_contains_locations(self, tmp_path):
        gen = make_portfolio_gen(tmp_path)
        result = gen.generate(count=3)
        assert len(result["data"]["locations"]) == 3
