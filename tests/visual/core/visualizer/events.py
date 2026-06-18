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

"""Tests for create_event_map, get_statistics and _add_flood_heatmap."""

import json
from pathlib import Path
import pytest
import folium
from unittest.mock import MagicMock, patch
from .conftest import _write_minimal_inputs, _make_loaded_data, _write_gaugets


class TestCreateEventMap:

    def test_no_data_returns_none(self, tmp_path):
        from visual.core.visualizer import TCEventVisualization
        inp = tmp_path / "input"
        inp.mkdir()
        out = tmp_path / "output"
        vis = TCEventVisualization(input_dir=inp, output_dir=out)
        result = vis.create_event_map("test_map.html")
        # Without gauge data, should fail gracefully and return None
        assert result is None

    def test_with_gauge_data_returns_path(self, tmp_path):
        from visual.core.visualizer import TCEventVisualization
        inp = tmp_path / "input"
        inp.mkdir()
        _write_minimal_inputs(inp)
        out = tmp_path / "output"
        vis = TCEventVisualization(input_dir=inp, output_dir=out, enable_interactivity=False)
        result = vis.create_event_map("test_map.html")
        assert result is not None
        assert result.exists()

    def test_output_is_html_file(self, tmp_path):
        from visual.core.visualizer import TCEventVisualization
        inp = tmp_path / "input"
        inp.mkdir()
        _write_minimal_inputs(inp)
        out = tmp_path / "output"
        vis = TCEventVisualization(input_dir=inp, output_dir=out, enable_interactivity=False)
        result = vis.create_event_map("viz.html")
        assert result is not None
        assert result.suffix == ".html"

    def test_property_coords_added_to_bounds(self, tmp_path):
        """Lines 149-159: property coords extracted for bounds fitting."""
        from visual.core.visualizer import TCEventVisualization
        inp = tmp_path / "input"
        inp.mkdir()
        _write_minimal_inputs(inp)
        out = tmp_path / "output"
        vis = TCEventVisualization(input_dir=inp, output_dir=out, enable_interactivity=False)
        result = vis.create_event_map("bounds.html")
        assert result is not None


class TestGetStatisticsComponents:

    def test_data_loader_stats_included(self, tmp_path):
        """Line 357: data_loader.get_statistics() included in stats dict."""
        from visual.core.visualizer import TCEventVisualization
        vis = TCEventVisualization(
            input_dir=tmp_path / "i",
            output_dir=tmp_path / "o",
            enable_interactivity=False
        )
        vis.data_loader.get_statistics = MagicMock(return_value={"files_loaded": 3})
        stats = vis.get_statistics()
        assert "data_loader" in stats
        assert stats["data_loader"]["files_loaded"] == 3

    def test_map_builder_stats_included(self, tmp_path):
        """Line 360: map_builder.get_statistics() included in stats dict."""
        from visual.core.visualizer import TCEventVisualization
        vis = TCEventVisualization(
            input_dir=tmp_path / "i",
            output_dir=tmp_path / "o",
            enable_interactivity=False
        )
        vis.map_builder.get_statistics = MagicMock(return_value={"maps_created": 1})
        stats = vis.get_statistics()
        assert "map_builder" in stats

    def test_interactivity_stats_included(self, tmp_path):
        """Line 363: interactivity.get_statistics() included when available."""
        from visual.core.visualizer import TCEventVisualization
        vis = TCEventVisualization(
            input_dir=tmp_path / "i",
            output_dir=tmp_path / "o",
            enable_interactivity=False
        )
        vis._interactivity_available = True
        vis.interactivity = MagicMock()
        vis.interactivity.get_statistics.return_value = {"events": 5}
        stats = vis.get_statistics()
        assert "interactivity" in stats


class TestAddFloodHeatmap:

    def _vis_with_gauge_data(self, tmp_path, gauge_id="GAUGE-001",
                              lat=51.5, lon=-0.1):
        """Create a TCEventVisualization with gauge_data pre-loaded."""
        from visual.core.visualizer import TCEventVisualization
        inp = tmp_path / "input"
        inp.mkdir(parents=True, exist_ok=True)
        vis = TCEventVisualization(
            input_dir=inp,
            output_dir=tmp_path / "output",
            enable_interactivity=False
        )
        vis.loaded_data = _make_loaded_data()
        vis.loaded_data.gauge_data = {
            "items": [{
                "FloodGauge": {
                    "Header": {"GaugeID": gauge_id},
                    "Location": {"GaugeLatitude": lat, "GaugeLongitude": lon},
                }
            }]
        }
        return vis, inp

    def test_no_gaugets_dir_returns_early(self, tmp_path):
        """Lines 223-224: no gaugets dir → early return."""
        vis, inp = self._vis_with_gauge_data(tmp_path)
        base_map = folium.Map(location=[51.5, -0.1], zoom_start=10)
        vis._add_flood_heatmap(base_map)  # should not raise

    def test_no_gauge_data_returns_early(self, tmp_path):
        """Lines 229-230: gauge_data=None → early return."""
        vis, inp = self._vis_with_gauge_data(tmp_path)
        vis.loaded_data.gauge_data = None
        (inp / "gaugets").mkdir()
        base_map = folium.Map(location=[51.5, -0.1], zoom_start=10)
        vis._add_flood_heatmap(base_map)  # should not raise

    def test_empty_gaugets_dir_returns_early(self, tmp_path):
        """Lines 264-265: no storm_peaks → early return."""
        vis, inp = self._vis_with_gauge_data(tmp_path)
        (inp / "gaugets").mkdir()  # exists but empty
        base_map = folium.Map(location=[51.5, -0.1], zoom_start=10)
        vis._add_flood_heatmap(base_map)  # no GAUGE-*.json → no peaks

    def test_heatmap_added_with_gaugets(self, tmp_path):
        """Lines 267-308: heatmap layer added for worst storm."""
        vis, inp = self._vis_with_gauge_data(tmp_path)
        _write_gaugets(inp / "gaugets", gauge_id="GAUGE-001", lat=51.5, lon=-0.1)
        base_map = folium.Map(location=[51.5, -0.1], zoom_start=10)
        vis._add_flood_heatmap(base_map)
        children_names = [str(type(c).__name__) for c in base_map._children.values()]
        assert any("FeatureGroup" in n for n in children_names)

    def test_heatmap_with_multiple_gauges(self, tmp_path):
        """Multiple gaugets files → picks worst storm."""
        vis, inp = self._vis_with_gauge_data(tmp_path)
        gaugets_dir = inp / "gaugets"
        _write_gaugets(gaugets_dir, "GAUGE-001", 51.5, -0.1)
        _write_gaugets(gaugets_dir, "GAUGE-002", 51.51, -0.11)
        vis.loaded_data.gauge_data = {
            "items": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"},
                                "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1}}},
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-002"},
                                "Location": {"GaugeLatitude": 51.51, "GaugeLongitude": -0.11}}},
            ]
        }
        base_map = folium.Map(location=[51.5, -0.1], zoom_start=10)
        vis._add_flood_heatmap(base_map)  # should not raise

    def test_heatmap_bad_gaugets_file_continues(self, tmp_path):
        """Lines 261-262: bad JSON file → exception caught, continues."""
        vis, inp = self._vis_with_gauge_data(tmp_path)
        gaugets_dir = inp / "gaugets"
        gaugets_dir.mkdir()
        (gaugets_dir / "GAUGE-001.json").write_text("not valid json")
        base_map = folium.Map(location=[51.5, -0.1], zoom_start=10)
        vis._add_flood_heatmap(base_map)  # should not raise

    def test_heatmap_with_propertyts(self, tmp_path):
        """Lines 278-296: propertyts flood events added to heatmap."""
        vis, inp = self._vis_with_gauge_data(tmp_path)
        _write_gaugets(inp / "gaugets", "GAUGE-001", 51.5, -0.1)
        pts_dir = inp / "propertyts"
        pts_dir.mkdir()
        prop_data = {
            "location": {"lat": 51.501, "lon": -0.101},
            "flood_events": [
                {"storm_id": "STORM-001", "flood_depth_m": 0.5, "flooded": True}
            ]
        }
        (pts_dir / "PROP-0001.json").write_text(json.dumps(prop_data))
        base_map = folium.Map(location=[51.5, -0.1], zoom_start=10)
        vis._add_flood_heatmap(base_map)  # should add property data to heatmap

    def test_heatmap_propertyts_bad_file_continues(self, tmp_path):
        """Lines 295-296: bad propertyts file → exception caught, continues."""
        vis, inp = self._vis_with_gauge_data(tmp_path)
        _write_gaugets(inp / "gaugets", "GAUGE-001", 51.5, -0.1)
        pts_dir = inp / "propertyts"
        pts_dir.mkdir()
        (pts_dir / "PROP-0001.json").write_text("bad json")
        base_map = folium.Map(location=[51.5, -0.1], zoom_start=10)
        vis._add_flood_heatmap(base_map)  # should not raise
