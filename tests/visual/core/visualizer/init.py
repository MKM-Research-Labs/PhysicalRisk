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

"""Tests for TCEventVisualization.__init__ and validate_input_files."""

import pytest
from .conftest import _write_minimal_inputs


class TestTCEventVisualizationInit:

    def _make(self, tmp_path, **kwargs):
        from visual.core.visualizer import TCEventVisualization
        return TCEventVisualization(
            input_dir=tmp_path / "input",
            output_dir=tmp_path / "output",
            **kwargs
        )

    def test_init_stores_input_dir(self, tmp_path):
        vis = self._make(tmp_path)
        assert vis.input_dir == tmp_path / "input"

    def test_init_stores_output_dir(self, tmp_path):
        vis = self._make(tmp_path)
        assert vis.output_dir == tmp_path / "output"

    def test_data_loader_created(self, tmp_path):
        from visual.core.data_loader import DataLoader
        vis = self._make(tmp_path)
        assert isinstance(vis.data_loader, DataLoader)

    def test_map_builder_created(self, tmp_path):
        from visual.core.map_builder import MapBuilder
        vis = self._make(tmp_path)
        assert isinstance(vis.map_builder, MapBuilder)

    def test_layers_available_flag(self, tmp_path):
        vis = self._make(tmp_path)
        assert isinstance(vis._layers_available, bool)

    def test_interactivity_available_flag(self, tmp_path):
        vis = self._make(tmp_path)
        assert isinstance(vis._interactivity_available, bool)

    def test_loaded_data_none_at_init(self, tmp_path):
        vis = self._make(tmp_path)
        assert vis.loaded_data is None

    def test_interactivity_disabled(self, tmp_path):
        vis = self._make(tmp_path, enable_interactivity=False)
        assert vis._interactivity_available is False
        assert vis.interactivity is None

    def test_server_url_stored(self, tmp_path):
        vis = self._make(tmp_path, server_url="http://localhost:5000")
        assert vis._server_url == "http://localhost:5000"

    def test_server_url_defaults_empty(self, tmp_path):
        vis = self._make(tmp_path)
        assert vis._server_url == ""


class TestValidateInputFiles:

    def test_missing_files_returns_false(self, tmp_path):
        from visual.core.visualizer import TCEventVisualization
        (tmp_path / "input").mkdir()
        vis = TCEventVisualization(input_dir=tmp_path / "input", output_dir=tmp_path / "output")
        assert vis.validate_input_files() is False

    def test_all_files_present_returns_true(self, tmp_path):
        from visual.core.visualizer import TCEventVisualization
        inp = tmp_path / "input"
        inp.mkdir()
        _write_minimal_inputs(inp)
        vis = TCEventVisualization(input_dir=inp, output_dir=tmp_path / "output")
        assert vis.validate_input_files() is True

    def test_missing_one_required_returns_false(self, tmp_path):
        from visual.core.visualizer import TCEventVisualization
        inp = tmp_path / "input"
        inp.mkdir()
        _write_minimal_inputs(inp)
        (inp / "gauge.json").unlink()
        vis = TCEventVisualization(input_dir=inp, output_dir=tmp_path / "output")
        assert vis.validate_input_files() is False
