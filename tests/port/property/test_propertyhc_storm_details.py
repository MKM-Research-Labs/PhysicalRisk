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
Tests for storm_details and gauge_thresholds in PropertyHazardCurveGenerator.

Covers:
  - storm_details array included in _process_property output
  - Per-storm fields: storm_id, gauge_peak_m, flood_depth_m, damage_ratio,
    flooded, retention_factor
  - gauge_thresholds attached to nearest_gauges entries
  - Edge cases: zero floods, non-flooded events excluded from flooded flag
"""

import pytest

import database
from port.src.property.propertyhc import (
    TENORS,
    PropertyHazardCurveGenerator,
)

from .conftest import write_gauge_hc, write_property_ts

# ===========================================================================
# storm_details — array present and populated
# ===========================================================================

class TestStormDetailsPresent:

    def test_storm_details_key_exists(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-SD01", n_floods=3)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert "storm_details" in result

    def test_storm_details_length_matches_flood_events(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-SD02", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert len(result["storm_details"]) == 5

    def test_storm_details_includes_non_flooded(self, basic_output_dir):
        """Non-flooded events appear in storm_details (unlike flood_count)."""
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-SD03", n_floods=3, include_non_flooded=True)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        # flood_events has 3 flooded + 1 non-flooded = 4 total
        assert len(result["storm_details"]) == 4
        # flood_count only counts flooded=True
        assert result["flood_count"] == 3

    def test_storm_details_empty_when_no_floods(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-SD04", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        assert result["storm_details"] == []


# ===========================================================================
# storm_details — per-storm fields
# ===========================================================================

class TestStormDetailsFields:

    @pytest.fixture
    def result_with_storms(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-FIELDS", n_floods=3, include_non_flooded=True)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        return gen._process_property(pdata, gauge_hazard, None, num_storms=100)

    def test_each_storm_has_storm_id(self, result_with_storms):
        for sd in result_with_storms["storm_details"]:
            assert "storm_id" in sd
            assert isinstance(sd["storm_id"], str)

    def test_each_storm_has_gauge_peak_m(self, result_with_storms):
        for sd in result_with_storms["storm_details"]:
            assert "gauge_peak_m" in sd
            assert isinstance(sd["gauge_peak_m"], (int, float))

    def test_each_storm_has_flood_depth_m(self, result_with_storms):
        for sd in result_with_storms["storm_details"]:
            assert "flood_depth_m" in sd
            assert isinstance(sd["flood_depth_m"], (int, float))

    def test_each_storm_has_damage_ratio(self, result_with_storms):
        for sd in result_with_storms["storm_details"]:
            assert "damage_ratio" in sd
            assert 0 <= sd["damage_ratio"] <= 1

    def test_each_storm_has_flooded_flag(self, result_with_storms):
        for sd in result_with_storms["storm_details"]:
            assert "flooded" in sd
            assert isinstance(sd["flooded"], bool)

    def test_each_storm_has_exceeded_severe(self, result_with_storms):
        for sd in result_with_storms["storm_details"]:
            assert "exceeded_severe" in sd
            assert isinstance(sd["exceeded_severe"], bool)

    def test_each_storm_has_retention_factor(self, result_with_storms):
        for sd in result_with_storms["storm_details"]:
            assert "retention_factor" in sd
            assert isinstance(sd["retention_factor"], (int, float))

    def test_flooded_storms_have_positive_depth(self, result_with_storms):
        for sd in result_with_storms["storm_details"]:
            if sd["flooded"]:
                assert sd["flood_depth_m"] > 0

    def test_non_flooded_storms_have_zero_depth(self, result_with_storms):
        non_flooded = [sd for sd in result_with_storms["storm_details"] if not sd["flooded"]]
        assert len(non_flooded) > 0  # fixture includes non-flooded
        for sd in non_flooded:
            assert sd["flood_depth_m"] == 0


# ===========================================================================
# storm_details — storm IDs match flood_events
# ===========================================================================

class TestStormDetailsConsistency:

    def test_storm_ids_match_flood_events(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-IDS", n_floods=4)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)

        # Use the source flood_events to get expected storm IDs
        expected_ids = {e["storm_id"] for e in pdata["flood_events"]}

        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        actual_ids = {sd["storm_id"] for sd in result["storm_details"]}
        assert actual_ids == expected_ids


# ===========================================================================
# gauge_thresholds — attached to nearest_gauges
# ===========================================================================

class TestGaugeThresholds:

    def _make_property_with_gauge_info(self, pts_dir, prop_id="PROP-GT01"):
        """Write a property with gauge_info in nearest_gauges."""
        pdata = {
            "property_id": prop_id,
            "location": {"lat": 51.45, "lon": -0.30},
            "elevation_m": 5.0,
            "floor_level_m": 0.3,
            "flood_zone": "Zone 2",
            "property_type": "Detached",
            "construction_year": 2000,
            "nearest_gauges": [
                {
                    "gauge_id": "GAUGE-001",
                    "distance_m": 1200,
                    "gauge_elevation_m": 3.5,
                    "gauge_info": {
                        "elevation": 3.5,
                        "alert_level": 3.5,
                        "warning_level": 4.5,
                        "severe_level": 5.0,
                    },
                },
            ],
            "flood_events": [
                {"storm_id": "S1", "flood_depth_m": 0.5, "flooded": True,
                 "damage_ratio": 0.1, "interpolated_wse_m": 5.5, "retention_factor": 0.8},
            ],
            "summary": {
                "property_id": prop_id,
                "floods_at_nearest_gauge": 10,
                "floods_at_property": 1,
            },
        }
        database.save_property_timeseries(
            database.active_catchment(), prop_id, pdata)
        return pdata

    def test_gauge_thresholds_key_exists(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = self._make_property_with_gauge_info(pts_dir)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        for ng in result["nearest_gauges"]:
            assert "gauge_thresholds" in ng

    def test_gauge_thresholds_has_alert_level(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = self._make_property_with_gauge_info(pts_dir)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        thresholds = result["nearest_gauges"][0]["gauge_thresholds"]
        assert thresholds["alert_level"] == 3.5

    def test_gauge_thresholds_has_warning_level(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = self._make_property_with_gauge_info(pts_dir)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        thresholds = result["nearest_gauges"][0]["gauge_thresholds"]
        assert thresholds["warning_level"] == 4.5

    def test_gauge_thresholds_has_severe_level(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        pdata = self._make_property_with_gauge_info(pts_dir)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        thresholds = result["nearest_gauges"][0]["gauge_thresholds"]
        assert thresholds["severe_level"] == 5.0

    def test_gauge_thresholds_empty_when_no_gauge_info(self, basic_output_dir):
        """When nearest_gauges lacks gauge_info, thresholds default to empty."""
        output_dir, pts_dir = basic_output_dir
        pdata = write_property_ts(pts_dir, "PROP-GT02", n_floods=2)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(pdata, gauge_hazard, None, num_storms=100)
        for ng in result["nearest_gauges"]:
            assert "gauge_thresholds" in ng
            assert isinstance(ng["gauge_thresholds"], dict)
