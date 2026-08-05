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

"""Unit tests for ``visual.core.visualizer.heatmap.add_flood_heatmap``.

The overlay reads gauge and property timeseries through the database seam
(``database.iter_*_timeseries_ids`` / ``database.get_*_timeseries``), not from
disk, so every test seeds the seam directly. The autouse ``_visualizer_catchment``
fixture in ``conftest`` binds an isolated, empty catchment for each test.
"""

import folium
import pytest

import database

from .conftest import _write_gaugets


def _feature_group_count(base_map):
    """Number of FeatureGroup children attached to *base_map*."""
    return sum(
        1 for c in base_map._children.values()
        if type(c).__name__ == "FeatureGroup"
    )


def _loaded_with_gauges(*gauges):
    """Build a LoadedData-like object exposing ``gauge_data`` for *gauges*.

    Each gauge is ``(gauge_id, lat, lon)``.
    """
    from unittest.mock import MagicMock
    ld = MagicMock()
    ld.gauge_data = {
        "items": [
            {"FloodGauge": {
                "Header": {"GaugeID": gid},
                "Location": {"GaugeLatitude": lat, "GaugeLongitude": lon},
            }}
            for gid, lat, lon in gauges
        ]
    }
    return ld


def _map():
    return folium.Map(location=[51.5, -0.1], zoom_start=10)


class TestGaugeCollection:
    """Gauge-location lookup and storm-peak aggregation branches."""

    def test_no_gauge_data_returns_early(self, tmp_path):
        """gauge_data falsy → return before touching the seam (lines 46-47)."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        ld = _loaded_with_gauges()
        ld.gauge_data = None
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)
        assert _feature_group_count(base_map) == 0

    def test_no_storm_peaks_returns_early(self, tmp_path):
        """gauge_data present but no gauge timeseries → no peaks → early return."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)
        assert _feature_group_count(base_map) == 0

    def test_gauge_without_coords_skipped(self, tmp_path):
        """A gauge missing lat/lon is dropped from the location lookup, so its
        timeseries response is skipped and no overlay is produced (line 58)."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        catchment = database.active_catchment()
        ld = _loaded_with_gauges()
        # Gauge present in gauge_data but with no coordinates.
        ld.gauge_data = {"items": [{"FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001"},
            "Location": {"GaugeLatitude": None, "GaugeLongitude": None},
        }}]}
        database.save_gauge_timeseries(catchment, "GAUGE-001", {
            "gauge_id": "GAUGE-001",
            "storm_responses": {"responses": [
                {"storm_id": "STORM-001", "peak_level_m": 3.0},
            ]},
        })
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)
        assert _feature_group_count(base_map) == 0

    def test_timeseries_gauge_id_not_in_lookup_skipped(self, tmp_path):
        """A timeseries whose gauge_id is unknown to gauge_data is skipped
        (line 68 continue) while a known gauge still builds the overlay."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        catchment = database.active_catchment()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        _write_gaugets(tmp_path / "g", "GAUGE-001", 51.5, -0.1)
        # Stray timeseries for a gauge that is not in the location lookup.
        database.save_gauge_timeseries(catchment, "GAUGE-999", {
            "gauge_id": "GAUGE-999",
            "storm_responses": {"responses": [
                {"storm_id": "STORM-001", "peak_level_m": 9.9},
            ]},
        })
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)
        assert _feature_group_count(base_map) == 1

    def test_gauge_timeseries_exception_continues(self, tmp_path, monkeypatch):
        """get_gauge_timeseries raising is swallowed (lines 77-78); with no
        surviving peaks the overlay is skipped."""
        from visual.core.visualizer import heatmap as heatmap_mod
        catchment = database.active_catchment()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        database.save_gauge_timeseries(catchment, "GAUGE-001", {"gauge_id": "GAUGE-001"})

        def _boom(*_a, **_k):
            raise RuntimeError("seam read failed")

        monkeypatch.setattr(heatmap_mod.database, "get_gauge_timeseries", _boom)
        base_map = _map()
        heatmap_mod.add_flood_heatmap(base_map, tmp_path, ld)
        assert _feature_group_count(base_map) == 0

    def test_storm_responses_as_bare_list(self, tmp_path):
        """storm_responses may be a bare list rather than a {'responses': [...]}
        dict; both shapes are accepted (line 71 branch)."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        catchment = database.active_catchment()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        database.save_gauge_timeseries(catchment, "GAUGE-001", {
            "gauge_id": "GAUGE-001",
            "storm_responses": [
                {"storm_id": "STORM-001", "peak_water_level_m": 4.2},
            ],
        })
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)
        assert _feature_group_count(base_map) == 1


class TestWorstStormSelection:

    def test_worst_storm_is_highest_mean_peak(self, tmp_path):
        """Overlay is built from the storm with the highest mean peak."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        catchment = database.active_catchment()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        database.save_gauge_timeseries(catchment, "GAUGE-001", {
            "gauge_id": "GAUGE-001",
            "storm_responses": {"responses": [
                {"storm_id": "STORM-MILD", "peak_level_m": 1.0},
                {"storm_id": "STORM-SEVERE", "peak_level_m": 6.0},
            ]},
        })
        captured = {}
        import visual.core.visualizer.heatmap as heatmap_mod
        real_heatmap = heatmap_mod.HeatMap

        def _spy(data, *a, **k):
            captured["data"] = data
            return real_heatmap(data, *a, **k)

        heatmap_mod.HeatMap = _spy
        try:
            base_map = _map()
            add_flood_heatmap(base_map, tmp_path, ld)
        finally:
            heatmap_mod.HeatMap = real_heatmap
        # Single gauge, worst storm → one normalized point at intensity 1.0.
        assert captured["data"] == [[51.5, -0.1, 1.0]]

    def test_peak_zero_ignored(self, tmp_path):
        """Responses with a non-positive peak do not create storm peaks."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        catchment = database.active_catchment()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        database.save_gauge_timeseries(catchment, "GAUGE-001", {
            "gauge_id": "GAUGE-001",
            "storm_responses": {"responses": [
                {"storm_id": "STORM-001", "peak_level_m": 0.0},
            ]},
        })
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)
        assert _feature_group_count(base_map) == 0


class TestPropertyOverlay:
    """The property-timeseries loop (lines 94-111)."""

    def _seed_worst_gauge(self):
        catchment = database.active_catchment()
        database.save_gauge_timeseries(catchment, "GAUGE-001", {
            "gauge_id": "GAUGE-001",
            "storm_responses": {"responses": [
                {"storm_id": "STORM-001", "peak_level_m": 4.0},
            ]},
        })
        return catchment

    def test_property_flood_event_added(self, tmp_path):
        """A PROP- property flooded in the worst storm is added to the overlay."""
        from visual.core.visualizer import heatmap as heatmap_mod
        catchment = self._seed_worst_gauge()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        database.save_property_timeseries(catchment, "PROP-0001", {
            "location": {"lat": 51.501, "lon": -0.101},
            "flood_events": [
                {"storm_id": "STORM-001", "flood_depth_m": 2.0},
            ],
        })
        captured = {}
        real_heatmap = heatmap_mod.HeatMap

        def _spy(data, *a, **k):
            captured["data"] = data
            return real_heatmap(data, *a, **k)

        heatmap_mod.HeatMap = _spy
        try:
            base_map = _map()
            heatmap_mod.add_flood_heatmap(base_map, tmp_path, ld)
        finally:
            heatmap_mod.HeatMap = real_heatmap
        # Gauge point + one property point (depth 2.0 / max_peak 4.0 = 0.5).
        assert [51.501, -0.101, 0.5] in captured["data"]
        assert len(captured["data"]) == 2

    def test_property_depth_capped_at_one(self, tmp_path):
        """Property depth exceeding the gauge peak is clamped to intensity 1.0."""
        from visual.core.visualizer import heatmap as heatmap_mod
        catchment = self._seed_worst_gauge()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        database.save_property_timeseries(catchment, "PROP-0001", {
            "location": {"lat": 51.5, "lon": -0.1},
            "flood_events": [
                {"storm_id": "STORM-001", "flood_depth_m": 99.0},
            ],
        })
        captured = {}
        real_heatmap = heatmap_mod.HeatMap

        def _spy(data, *a, **k):
            captured["data"] = data
            return real_heatmap(data, *a, **k)

        heatmap_mod.HeatMap = _spy
        try:
            base_map = _map()
            heatmap_mod.add_flood_heatmap(base_map, tmp_path, ld)
        finally:
            heatmap_mod.HeatMap = real_heatmap
        assert [51.5, -0.1, 1.0] in captured["data"]

    def test_non_prop_id_skipped(self, tmp_path):
        """A non ``PROP-`` timeseries id (e.g. the summary singleton) is skipped."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        catchment = self._seed_worst_gauge()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        database.save_property_timeseries(catchment, "portfolio_flood_summary", {
            "location": {"lat": 51.6, "lon": -0.2},
            "flood_events": [
                {"storm_id": "STORM-001", "flood_depth_m": 3.0},
            ],
        })
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)
        # Only the gauge overlay; the summary singleton contributes nothing.
        assert _feature_group_count(base_map) == 1

    def test_property_missing_location_skipped(self, tmp_path):
        """A property with no lat/lon is skipped (lines 101-103)."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        catchment = self._seed_worst_gauge()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        database.save_property_timeseries(catchment, "PROP-0001", {
            "location": {},
            "flood_events": [
                {"storm_id": "STORM-001", "flood_depth_m": 3.0},
            ],
        })
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)
        assert _feature_group_count(base_map) == 1

    def test_property_other_storm_ignored(self, tmp_path):
        """A flood event for a different storm is not added to the overlay."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        catchment = self._seed_worst_gauge()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        database.save_property_timeseries(catchment, "PROP-0001", {
            "location": {"lat": 51.501, "lon": -0.101},
            "flood_events": [
                {"storm_id": "STORM-OTHER", "flood_depth_m": 3.0},
            ],
        })
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)
        assert _feature_group_count(base_map) == 1

    def test_property_zero_depth_ignored(self, tmp_path):
        """A worst-storm event with zero depth is not added."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        catchment = self._seed_worst_gauge()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        database.save_property_timeseries(catchment, "PROP-0001", {
            "location": {"lat": 51.501, "lon": -0.101},
            "flood_events": [
                {"storm_id": "STORM-001", "flood_depth_m": 0.0},
            ],
        })
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)
        assert _feature_group_count(base_map) == 1

    def test_property_read_exception_continues(self, tmp_path):
        """A malformed property payload raises inside the loop and is swallowed
        (lines 110-111) without aborting the overlay."""
        from visual.core.visualizer.heatmap import add_flood_heatmap
        catchment = self._seed_worst_gauge()
        ld = _loaded_with_gauges(("GAUGE-001", 51.5, -0.1))
        # flood_events contains a non-dict → ev.get(...) raises AttributeError.
        database.save_property_timeseries(catchment, "PROP-0001", {
            "location": {"lat": 51.501, "lon": -0.101},
            "flood_events": ["not-a-dict"],
        })
        base_map = _map()
        add_flood_heatmap(base_map, tmp_path, ld)  # must not raise
        assert _feature_group_count(base_map) == 1
