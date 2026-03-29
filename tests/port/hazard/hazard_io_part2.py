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
Tests for models.hazard.io — save_hazard_curves, save_gauge_storm_responses.
"""

import json

import pytest

from models.hazard.data_structures import GaugeResponse
from tests.port.hazard.conftest import _make_hazard_curve


# ===========================================================================
# save_hazard_curves
# ===========================================================================

class TestSaveHazardCurves:

    def test_creates_file(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        output_path = tmp_path / "gaugehc.json"
        result = save_hazard_curves(
            {"GAUGE-001": curve}, output_path, "thames"
        )
        assert output_path.exists()
        assert result == output_path

    def test_file_has_metadata(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        output_path = tmp_path / "gaugehc.json"
        save_hazard_curves({"GAUGE-001": curve}, output_path, "thames")
        data = json.loads(output_path.read_text())
        assert "metadata" in data
        assert data["metadata"]["catchment_id"] == "thames"

    def test_file_has_hazard_curves(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        output_path = tmp_path / "gaugehc.json"
        save_hazard_curves({"GAUGE-001": curve}, output_path, "thames")
        data = json.loads(output_path.read_text())
        assert "GAUGE-001" in data["hazard_curves"]

    def test_creates_parent_dirs(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        output_path = tmp_path / "subdir" / "nested" / "gaugehc.json"
        save_hazard_curves({"GAUGE-001": curve}, output_path, "thames")
        assert output_path.exists()

    def test_metadata_merged(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        output_path = tmp_path / "gaugehc.json"
        save_hazard_curves(
            {"GAUGE-001": curve}, output_path, "thames",
            metadata={"num_storms": 100, "distribution": "gev"}
        )
        data = json.loads(output_path.read_text())
        assert data["metadata"]["num_storms"] == 100


# ===========================================================================
# save_gauge_storm_responses
# ===========================================================================

class TestSaveGaugeStormResponses:

    def _make_responses(self, gauge_id="GAUGE-001", n=2):
        return [
            GaugeResponse(
                gauge_id=gauge_id,
                storm_id=f"STORM-{i:04d}",
                base_level_m=3.0,
                level_change_m=1.0 + i * 0.5,
                peak_level_m=4.0 + i * 0.5,
                exceeded_alert=True,
                exceeded_warning=i > 0,
                exceeded_severe=False,
            )
            for i in range(n)
        ]

    def test_creates_gauge_file(self, tmp_path):
        from models.hazard.io import save_gauge_storm_responses
        responses = {"GAUGE-001": self._make_responses()}
        result = save_gauge_storm_responses(responses, tmp_path / "gaugets", "thames")
        assert (tmp_path / "gaugets" / "GAUGE-001.json").exists()

    def test_saved_file_has_responses(self, tmp_path):
        from models.hazard.io import save_gauge_storm_responses
        responses = {"GAUGE-001": self._make_responses(n=3)}
        gaugets_dir = tmp_path / "gaugets"
        save_gauge_storm_responses(responses, gaugets_dir, "thames")
        data = json.loads((gaugets_dir / "GAUGE-001.json").read_text())
        assert "storm_responses" in data
        assert len(data["storm_responses"]["responses"]) == 3

    def test_merges_with_existing_file(self, tmp_path):
        """If gauge file already exists, merge storm_responses into it."""
        from models.hazard.io import save_gauge_storm_responses
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        existing = {
            "gauge_id": "GAUGE-001",
            "flood_simulation": {"readings": []},
        }
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(existing))
        responses = {"GAUGE-001": self._make_responses(n=1)}
        save_gauge_storm_responses(responses, gaugets_dir, "thames")
        data = json.loads((gaugets_dir / "GAUGE-001.json").read_text())
        assert "flood_simulation" in data
        assert "storm_responses" in data

    def test_multiple_gauges(self, tmp_path):
        from models.hazard.io import save_gauge_storm_responses
        responses = {
            "GAUGE-001": self._make_responses("GAUGE-001", 2),
            "GAUGE-002": self._make_responses("GAUGE-002", 2),
        }
        gaugets_dir = tmp_path / "gaugets"
        save_gauge_storm_responses(responses, gaugets_dir, "thames")
        assert (gaugets_dir / "GAUGE-001.json").exists()
        assert (gaugets_dir / "GAUGE-002.json").exists()
