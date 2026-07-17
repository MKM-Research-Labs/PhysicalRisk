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
Tests for _process_property flood path, _compute_property_flood, and
_build_flood_event.
"""

from .conftest import make_prop, make_gauge_lookup, make_gaugets, make_generator


# ===========================================================================
# _process_property — full flood path (lines 291-370)
# ===========================================================================

class TestProcessPropertyWithFloods:

    def test_writes_property_file(self, tmp_path):
        """Full processing writes a JSON file for the property."""
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        prop = make_prop()
        result = gen._process_property(
            prop, make_gauge_lookup(),
            make_gaugets(peak_level=5.5, exceeded_alert=True),
            pts_dir
        )
        assert result is not None
        assert (pts_dir / "PROP-001.json").exists()

    def test_summary_has_required_keys(self, tmp_path):
        """Summary dict has floods_at_nearest_gauge etc."""
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        result = gen._process_property(
            make_prop(), make_gauge_lookup(),
            make_gaugets(peak_level=5.5, exceeded_alert=True),
            pts_dir
        )
        s = result["summary"]
        assert "property_id" in s
        assert "floods_at_nearest_gauge" in s
        assert "floods_at_property" in s
        assert "max_depth_m" in s

    def test_no_alert_storms_zero_floods(self, tmp_path):
        """Gauge response with exceeded_alert=False -> 0 gauge storms."""
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        gaugets = make_gaugets(peak_level=3.0, exceeded_alert=False)
        result = gen._process_property(
            make_prop(), make_gauge_lookup(), gaugets, pts_dir
        )
        assert result["summary"]["floods_at_nearest_gauge"] == 0

    def test_high_elevation_property_does_not_flood(self, tmp_path):
        """Property with elevation > gauge peak -> depth 0."""
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        prop = make_prop(elevation=100.0, floor_level=0.5)
        result = gen._process_property(
            prop, make_gauge_lookup(elevation=3.0),
            make_gaugets(peak_level=5.5, exceeded_alert=True),
            pts_dir
        )
        assert result["summary"]["floods_at_property"] == 0


# ===========================================================================
# _compute_property_flood — IDW path (lines 385-426)
# ===========================================================================

class TestComputePropertyFlood:

    def test_returns_dict_with_storm_id(self, tmp_path):
        """Normal IDW path returns dict with storm_id."""
        gen = make_generator(tmp_path)
        nearest = [
            {"gauge_id": "GAUGE-001", "distance_m": 500.0,
             "gauge_info": {"elevation": 3.0}},
        ]
        gauge_responses = {
            "GAUGE-001": {"peak_level_m": 5.5, "exceeded_alert": True}
        }
        gaugets = make_gaugets()
        result = gen._compute_property_flood(
            "STORM-001", gauge_responses, nearest,
            51.5, -0.1, 5.0, 0.3, gaugets
        )
        assert result is not None
        assert result["storm_id"] == "STORM-001"

    def test_no_matching_gauge_returns_none(self, tmp_path):
        """gauge_responses has no entry for nearest gauge -> None."""
        gen = make_generator(tmp_path)
        nearest = [
            {"gauge_id": "GAUGE-999", "distance_m": 500.0,
             "gauge_info": {"elevation": 3.0}},
        ]
        result = gen._compute_property_flood(
            "STORM-001", {}, nearest, 51.5, -0.1, 5.0, 0.3, {}
        )
        assert result is None

    def test_dist_less_than_1m_short_circuits(self, tmp_path):
        """dist < 1.0 -> short-circuit to _build_flood_event directly."""
        gen = make_generator(tmp_path)
        nearest = [
            {"gauge_id": "GAUGE-001", "distance_m": 0.5,
             "gauge_info": {"elevation": 3.0}},
        ]
        gauge_responses = {
            "GAUGE-001": {"peak_level_m": 5.5, "exceeded_alert": True}
        }
        gaugets = make_gaugets()
        result = gen._compute_property_flood(
            "STORM-001", gauge_responses, nearest,
            51.5, -0.1, 5.0, 0.3, gaugets
        )
        assert result is not None
        assert result["storm_id"] == "STORM-001"

    def test_multiple_gauges_uses_idw(self, tmp_path):
        """Multiple gauges in nearest -> IDW path used."""
        gen = make_generator(tmp_path)
        nearest = [
            {"gauge_id": "GAUGE-001", "distance_m": 300.0,
             "gauge_info": {"elevation": 3.0}},
            {"gauge_id": "GAUGE-002", "distance_m": 600.0,
             "gauge_info": {"elevation": 3.5}},
        ]
        gauge_responses = {
            "GAUGE-001": {"peak_level_m": 5.5},
            "GAUGE-002": {"peak_level_m": 4.8},
        }
        gaugets = {
            "GAUGE-001": make_gaugets()["GAUGE-001"],
            "GAUGE-002": make_gaugets(gauge_id="GAUGE-002")["GAUGE-002"],
        }
        result = gen._compute_property_flood(
            "STORM-001", gauge_responses, nearest,
            51.5, -0.1, 5.0, 0.3, gaugets
        )
        assert result is not None


# ===========================================================================
# _build_flood_event (lines 434-497)
# ===========================================================================

class TestBuildFloodEvent:

    def _nearest(self, elevation=3.0):
        return {
            "gauge_id": "GAUGE-001",
            "distance_m": 500.0,
            "gauge_info": {"elevation": elevation},
        }

    def test_returns_expected_keys(self, tmp_path):
        """_build_flood_event returns dict with required keys."""
        gen = make_generator(tmp_path)
        gaugets = make_gaugets()
        result = gen._build_flood_event(
            "STORM-001", 5.5, 500.0, 0.9,
            5.0, 0.3, "GAUGE-001", gaugets, self._nearest()
        )
        for key in ("storm_id", "flood_depth_m", "damage_ratio",
                    "flooded", "retention_factor"):
            assert key in result
        # readings only present when flooded
        if result["flooded"]:
            assert "readings" in result

    def test_flooded_when_wse_exceeds_threshold(self, tmp_path):
        """High WSE above property elevation -> flooded=True."""
        gen = make_generator(tmp_path)
        gaugets = make_gaugets(peak_level=6.0)
        result = gen._build_flood_event(
            "STORM-001", 8.0, 100.0, 0.95,
            2.0, 0.1, "GAUGE-001", gaugets, self._nearest(elevation=2.0)
        )
        assert result["flooded"] is True
        assert result["flood_depth_m"] > 0

    def test_not_flooded_when_wse_below_threshold(self, tmp_path):
        """Low WSE -> flooded=False."""
        gen = make_generator(tmp_path)
        gaugets = make_gaugets(peak_level=2.0)
        result = gen._build_flood_event(
            "STORM-001", 2.0, 2000.0, 0.3,
            50.0, 5.0, "GAUGE-001", gaugets, self._nearest(elevation=50.0)
        )
        assert result["flooded"] is False

    def test_no_gauge_readings_empty_hydrograph(self, tmp_path):
        """Gaugets with empty readings -> no readings key (not flooded)."""
        gen = make_generator(tmp_path)
        gaugets = make_gaugets(with_readings=False)
        result = gen._build_flood_event(
            "STORM-001", 5.5, 500.0, 0.9,
            5.0, 0.3, "GAUGE-001", gaugets, self._nearest()
        )
        # No gauge readings means no hydrograph, so flood_depth=0 and
        # readings are omitted for non-flooded events.
        assert "readings" not in result

    def test_zero_distance_travel_time(self, tmp_path):
        """Distance=0 -> travel_time=0 path."""
        gen = make_generator(tmp_path)
        gaugets = make_gaugets()
        result = gen._build_flood_event(
            "STORM-001", 5.5, 0.0, 1.0,
            5.0, 0.3, "GAUGE-001", gaugets, self._nearest()
        )
        assert result["travel_time_hrs"] == 0.0

    def test_arrival_and_peak_times_set_when_flooded(self, tmp_path):
        """When flooded, arrival_time and peak_time are set."""
        gen = make_generator(tmp_path)
        gaugets = make_gaugets(peak_level=10.0)
        result = gen._build_flood_event(
            "STORM-001", 10.0, 100.0, 0.99,
            1.0, 0.0, "GAUGE-001", gaugets, self._nearest(elevation=1.0)
        )
        if result["flooded"]:
            assert result["arrival_time_hrs"] is not None
            assert result["peak_time_hrs"] is not None
