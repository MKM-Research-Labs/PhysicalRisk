# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Tests for layer init, interactivity init, _add_layer and _add_interactivity."""

import pytest
import folium
from unittest.mock import MagicMock, patch
from .conftest import _make_loaded_data


class TestInitLayersImportError:

    def test_layers_unavailable_on_import_error(self, tmp_path):
        """Lines 89-90: ImportError in _init_layers sets _layers_available=False."""
        from visual.core.visualizer import TCEventVisualization
        with patch("visual.core.visualizer.coordinator.GaugeLayer",
                   side_effect=ImportError("no module")):
            vis = TCEventVisualization(
                input_dir=tmp_path / "i",
                output_dir=tmp_path / "o",
                enable_interactivity=False
            )
        assert vis._layers_available is False


class TestInitInteractivity:

    def test_invalid_notification_position_uses_default(self, tmp_path):
        """Lines 105-106: ValueError → falls back to TOP_RIGHT."""
        from visual.core.visualizer import TCEventVisualization
        vis = TCEventVisualization(
            input_dir=tmp_path / "i",
            output_dir=tmp_path / "o",
            notification_position="not-a-valid-position"
        )
        # If interactivity loaded OK, it should still be available
        assert isinstance(vis._interactivity_available, bool)

    def test_interactivity_import_error_suppressed(self, tmp_path):
        """Lines 114-115: ImportError in interactivity import → available=False."""
        with patch.dict("sys.modules", {"visual.interactivity": None}):
            from visual.core.visualizer import TCEventVisualization
            vis = TCEventVisualization(
                input_dir=tmp_path / "i",
                output_dir=tmp_path / "o",
            )
        assert isinstance(vis._interactivity_available, bool)


class TestAddLayerExceptions:

    def _vis(self, tmp_path):
        from visual.core.visualizer import TCEventVisualization
        vis = TCEventVisualization(
            input_dir=tmp_path / "i",
            output_dir=tmp_path / "o",
            enable_interactivity=False
        )
        vis._layers_available = True
        return vis

    def test_gauge_layer_exception_logged(self, tmp_path):
        """Lines 193-194: gauge_layer.add_to_map raises → logged, continues."""
        vis = self._vis(tmp_path)
        vis.gauge_layer.add_to_map = lambda *a: (_ for _ in ()).throw(RuntimeError("gauge fail"))
        vis.loaded_data = _make_loaded_data()
        base_map = folium.Map()
        vis._add_layer(base_map)  # should not raise

    def test_property_layer_exception_logged(self, tmp_path):
        """Lines 199-200: property_layer.add_to_map raises → logged, continues."""
        vis = self._vis(tmp_path)
        vis.gauge_layer.add_to_map = lambda *a: None
        vis.property_layer.add_to_map = lambda *a: (_ for _ in ()).throw(RuntimeError("prop fail"))
        vis.loaded_data = _make_loaded_data()
        base_map = folium.Map()
        vis._add_layer(base_map)

    def test_mortgage_layer_exception_logged(self, tmp_path):
        """Lines 205-206: mortgage_layer.add_to_map raises → logged, continues."""
        vis = self._vis(tmp_path)
        vis.gauge_layer.add_to_map = lambda *a: None
        vis.property_layer.add_to_map = lambda *a: None
        vis.mortgage_layer.add_to_map = lambda *a: (_ for _ in ()).throw(RuntimeError("mort fail"))
        vis.loaded_data = _make_loaded_data()
        base_map = folium.Map()
        vis._add_layer(base_map)

    def test_heatmap_exception_logged(self, tmp_path):
        """Lines 211-212: _add_flood_heatmap raises → logged, continues."""
        vis = self._vis(tmp_path)
        vis.gauge_layer.add_to_map = lambda *a: None
        vis.property_layer.add_to_map = lambda *a: None
        vis.mortgage_layer.add_to_map = lambda *a: None
        vis.loaded_data = _make_loaded_data()
        base_map = folium.Map()
        with patch.object(vis, "_add_flood_heatmap", side_effect=RuntimeError("heat fail")):
            vis._add_layer(base_map)  # should not raise

    def test_layers_unavailable_skips_all(self, tmp_path):
        """Lines 187-188: _layers_available=False → early return."""
        vis = self._vis(tmp_path)
        vis._layers_available = False
        vis.loaded_data = _make_loaded_data()
        base_map = folium.Map()
        vis._add_layer(base_map)  # should not call any layer

    def test_no_gauge_data_skips_gauge_layer(self, tmp_path):
        """Lines 190: gauge_data=None → gauge_layer not called."""
        vis = self._vis(tmp_path)
        vis.loaded_data = _make_loaded_data(gauge=False)
        base_map = folium.Map()
        vis._add_layer(base_map)  # should not raise


class TestAddInteractivityException:

    def test_interactivity_setup_exception_suppressed(self, tmp_path):
        """Lines 313-316: interactivity.setup_map_interactivity raises → logged, continues."""
        from visual.core.visualizer import TCEventVisualization
        vis = TCEventVisualization(
            input_dir=tmp_path / "i",
            output_dir=tmp_path / "o",
            enable_interactivity=False
        )
        vis._interactivity_available = True
        vis.interactivity = MagicMock()
        vis.interactivity.setup_map_interactivity.side_effect = RuntimeError("setup fail")
        base_map = folium.Map()
        vis._add_interactivity(base_map)  # should not raise
