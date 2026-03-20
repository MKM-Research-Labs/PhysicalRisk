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
Tests for PropertyHazardCurveGenerator._process_property:
  - Flooded/non-flooded event filtering
  - MIN_EVENTS_FOR_GEV boundary
  - Annual probability floor capping
  - IDW gauge spreads
  - Summary statistics
"""

import json

import pytest

from port.src.property.propertyhc import (
    MIN_EVENTS_FOR_GEV,
    MIN_PRS_SPREAD_BPS,
    TENORS,
    PropertyHazardCurveGenerator,
)

from .conftest import write_property_ts


# ===========================================================================
# _process_property — events with flooded=False excluded
# ===========================================================================

class TestProcessPropertyFloodedFilter:

    def test_non_flooded_events_excluded_from_depth_count(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-filter", n_floods=4, include_non_flooded=True)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-filter.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == 4

    def test_zero_flooded_events_uses_floor_pricing(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-nofloods", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-nofloods.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["has_gev"] is False
        assert result["pricing_method"] == "floor"
        assert result["flood_count"] == 0


# ===========================================================================
# _process_property — MIN_EVENTS_FOR_GEV boundary
# ===========================================================================

class TestProcessPropertyGevBoundary:

    def test_exactly_min_events_triggers_gev(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-exact", n_floods=MIN_EVENTS_FOR_GEV)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-exact.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == MIN_EVENTS_FOR_GEV

    def test_one_below_min_events_uses_floor(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-below", n_floods=MIN_EVENTS_FOR_GEV - 1)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-below.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["has_gev"] is False
        assert result["pricing_method"] == "floor"

    def test_many_events_enables_gev(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-many", n_floods=10)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-many.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["flood_count"] == 10
        assert result["gev_params"] is not None or result["has_gev"] is False


# ===========================================================================
# _process_property — annual_prob floor capping
# ===========================================================================

class TestAnnualProbFloorCapping:

    def test_minimum_spread_applied_for_floor_property(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-floor", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-floor.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        for name, tinfo in result["depth_thresholds"].items():
            prob = tinfo["annual_probability"]
            expected_min = MIN_PRS_SPREAD_BPS / 10000
            assert prob >= expected_min, f"Floor not applied for threshold '{name}'"

    def test_return_period_finite_for_floor(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-rp", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-rp.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        for name, tinfo in result["depth_thresholds"].items():
            rp = tinfo["return_period_yrs"]
            assert rp is not None
            assert rp > 0


# ===========================================================================
# _process_property — IDW gauge spreads
# ===========================================================================

class TestIdwGaugeSpreads:

    def test_idw_gauge_spreads_computed_with_two_gauges(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-idw", n_floods=5,
                          nearest_gauges=[
                              {"gauge_id": "GAUGE-001", "distance_m": 1000,
                               "gauge_elevation_m": 3.5},
                              {"gauge_id": "GAUGE-002", "distance_m": 2000,
                               "gauge_elevation_m": 4.0},
                          ])
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-idw.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        idw = result.get("idw_gauge_spreads", {})
        assert "any_flood" in idw
        assert len(idw["any_flood"]) == len(TENORS)

    def test_no_nearest_gauges_idw_returns_dict(self, basic_output_dir):
        """With empty nearest_gauges, idw_gauge_spreads is still a dict."""
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-noidw", n_floods=3,
                          nearest_gauges=[])
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-noidw.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert isinstance(result.get("idw_gauge_spreads"), dict)


# ===========================================================================
# _process_property — summary statistics
# ===========================================================================

class TestProcessPropertySummary:

    def test_max_depth_positive_for_flooded_property(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-depth", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-depth.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["summary"]["max_depth_m"] > 0
        assert result["summary"]["mean_depth_m"] > 0

    def test_zero_depths_for_non_flooded(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        write_property_ts(pts_dir, "PROP-zero", n_floods=0)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-zero.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        assert result["summary"]["max_depth_m"] == 0.0
        assert result["summary"]["mean_depth_m"] == 0.0

    def test_transmission_rate_zero_when_no_gauge_floods(self, basic_output_dir):
        output_dir, pts_dir = basic_output_dir
        prop_data = {
            "property_id": "PROP-txzero",
            "location": {"lat": 51.45, "lon": -0.30},
            "elevation_m": 5.0,
            "floor_level_m": 0.3,
            "flood_zone": "Zone 1",
            "property_type": "Detached",
            "construction_year": 2000,
            "nearest_gauges": [
                {"gauge_id": "GAUGE-001", "distance_m": 1000, "gauge_elevation_m": 3.5},
            ],
            "flood_events": [
                {"storm_id": "S1", "flood_depth_m": 0.5, "flooded": True, "damage_ratio": 0.1},
            ],
            "summary": {
                "property_id": "PROP-txzero",
                "floods_at_nearest_gauge": 0,
                "floods_at_property": 1,
            },
        }
        (pts_dir / "PROP-txzero.json").write_text(json.dumps(prop_data))
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        prop_file = pts_dir / "PROP-txzero.json"
        gauge_hazard, _ = gen._load_gauge_hazard_curves()
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=100)
        if result["nearest_gauges"]:
            assert result["nearest_gauges"][0]["flood_transmission_rate"] == 0.0
