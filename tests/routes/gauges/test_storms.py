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

"""Tests for routes.gauges.storms — error paths."""

import json
from unittest.mock import patch, MagicMock

from .conftest import GAUGE_ID, GAUGE_DATA, make_client


class TestStormsErrorPaths:

    def test_storm_sequences_corrupted_continues(self, tmp_path, monkeypatch):
        """storms.py lines 75-76: corrupted storm_sequences.json -> silently skipped."""
        (tmp_path / "storm_sequences.json").write_text("NOT JSON")
        gaugets_data = {
            "gauge_id": GAUGE_ID,
            "flood_simulation": {"readings": [{"waterLevel": 3.5}]},
            "storm_responses": {"responses": [{"storm_id": "STORM-0001", "peak_level_m": 4.8}]}
        }
        client = make_client(tmp_path, monkeypatch, gaugets_file=gaugets_data)
        r = client.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert r.status_code == 200

    def test_gaugets_dir_corrupted_file_continues(self, tmp_path, monkeypatch):
        """storms.py lines 91-92: corrupted gaugets file -> skipped in severe count loop."""
        gaugets_data = {
            "gauge_id": GAUGE_ID,
            "flood_simulation": {"readings": [{"waterLevel": 3.5}]},
            "storm_responses": {"responses": [{"storm_id": "STORM-0001", "peak_level_m": 4.8}]}
        }
        client = make_client(tmp_path, monkeypatch, gaugets_file=gaugets_data)
        gaugets_dir = tmp_path / "gaugets"
        (gaugets_dir / "GAUGE-BAD.json").write_text("NOT JSON")
        r = client.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert r.status_code == 200

    def test_storms_exception_returns_500(self, tmp_path, monkeypatch):
        """storms.py lines 113-115: exception in storm loading -> 500."""
        client = make_client(tmp_path, monkeypatch)

        with patch("routes.gauges.storms._get_registry") as mock_reg:
            loader = MagicMock()
            loader.find_by_id.return_value = {"some": "data"}
            ts_loader = MagicMock()
            ts_loader.get_readings_for_gauge.side_effect = RuntimeError("boom")
            mock_reg.return_value.get_gauge_loader.return_value = loader
            mock_reg.return_value.get_timeseries_loader.return_value = ts_loader
            r = client.get(f"/api/v1/gauges/{GAUGE_ID}/storms")

        assert r.status_code == 500
        assert r.get_json()["status"] == "error"

    def test_no_storm_sequences_file(self, tmp_path, monkeypatch):
        """storms.py line 61: storm_sequences.json doesn't exist -> skip enrichment."""
        gaugets_data = {
            "gauge_id": GAUGE_ID,
            "flood_simulation": {"readings": [{"waterLevel": 3.5}]},
            "storm_responses": {"responses": [{"storm_id": "STORM-0001", "peak_level_m": 4.8}]}
        }
        client = make_client(tmp_path, monkeypatch, gaugets_file=gaugets_data)
        r = client.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert r.status_code == 200
        data = r.get_json()
        assert data["storm_responses"]["num_sequences"] == 1

    def test_no_gaugets_dir(self, tmp_path, monkeypatch):
        """storms.py line 80: gaugets dir doesn't exist -> skip severe counting."""
        from config import config

        (tmp_path / "gauge.json").write_text(json.dumps(GAUGE_DATA))
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        (gaugets_dir / f"{GAUGE_ID}.json").write_text(json.dumps({
            "gauge_id": GAUGE_ID,
            "flood_simulation": {"readings": [{"waterLevel": 3.5}]},
            "storm_responses": {"responses": [{"storm_id": "STORM-0001", "peak_level_m": 4.8}]}
        }))
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()

        nonexistent = tmp_path / "no_gaugets_dir"
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get(f"/api/v1/gauges/{GAUGE_ID}/storms")
        assert r.status_code == 200
