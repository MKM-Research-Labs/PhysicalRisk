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

"""Tests for routes.gauges.history — error paths (500 responses)."""

import json
from unittest.mock import patch, MagicMock

from .conftest import GAUGE_ID, GAUGE_DATA, make_client


class TestHistoryErrorPaths:

    def test_get_gauge_history_corrupted_file_returns_500(self, tmp_path, monkeypatch):
        """history.py lines 88-90: corrupted gaugehd file -> 500."""
        from config import config
        (tmp_path / "gauge.json").write_text(json.dumps(GAUGE_DATA))
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        (gaugehd_dir / f"gauge_{GAUGE_ID}_hd.json").write_text("BAD JSON")
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get(f"/api/v1/gauges/{GAUGE_ID}/history")
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"

    def test_get_gaugets_exception_returns_500(self, tmp_path, monkeypatch):
        """history.py lines 119-121: timeseries loader exception -> 500."""
        from config import config
        (tmp_path / "gauge.json").write_text(json.dumps(GAUGE_DATA))
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        with patch("routes.gauges.history._get_registry") as mock_reg:
            loader = MagicMock()
            loader.find_by_id.return_value = {"some": "data"}
            ts_loader = MagicMock()
            mock_reg.return_value.get_gauge_loader.return_value = loader
            mock_reg.return_value.get_timeseries_loader.return_value = ts_loader
            loader.get_gauge_name.side_effect = RuntimeError("boom")
            r = client.get(f"/api/v1/gauges/{GAUGE_ID}/timeseries")
        assert r.status_code == 500

    def test_get_gauge_statistics_exception_returns_500(self, tmp_path, monkeypatch):
        """history.py lines 144-146: statistics loader exception -> 500."""
        from config import config
        (tmp_path / "gauge.json").write_text(json.dumps(GAUGE_DATA))
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        with patch("routes.gauges.history._get_registry") as mock_reg:
            loader = MagicMock()
            loader.find_by_id.return_value = {"some": "data"}
            ts_loader = MagicMock()
            ts_loader.get_gauge_statistics.side_effect = RuntimeError("stats boom")
            mock_reg.return_value.get_gauge_loader.return_value = loader
            mock_reg.return_value.get_timeseries_loader.return_value = ts_loader
            r = client.get(f"/api/v1/gauges/{GAUGE_ID}/statistics")
        assert r.status_code == 500

    def test_get_gauge_history_invalid_days_returns_400(self, tmp_path, monkeypatch):
        """history.py line 76: days outside [1, 3650] -> 400."""
        from config import config

        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        # Provide a valid history file so the days check is reached
        (gaugehd_dir / f"gauge_{GAUGE_ID}_hd.json").write_text(json.dumps({
            "gauge_metadata": {"gauge_id": GAUGE_ID},
            "statistics": {},
            "daily_observations": [],
        }))
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        (tmp_path / "gauge.json").write_text(json.dumps(GAUGE_DATA))
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        # days too large
        r = client.get(f"/api/v1/gauges/{GAUGE_ID}/history?days=99999")
        assert r.status_code == 400
        assert "between 1 and 3650" in r.get_json()["message"]

        # days negative
        r2 = client.get(f"/api/v1/gauges/{GAUGE_ID}/history?days=-5")
        assert r2.status_code == 400

    def test_get_gauge_history_unexpected_exception_returns_500(
        self, tmp_path, monkeypatch
    ):
        """history.py lines 93-95: non-IO exception (eg in jsonify) -> 500.

        We patch jsonify to raise a generic Exception so the bare-except
        clause is exercised.
        """
        from config import config

        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        (gaugehd_dir / f"gauge_{GAUGE_ID}_hd.json").write_text(json.dumps({
            "gauge_metadata": {"gauge_id": GAUGE_ID},
            "statistics": {},
            "daily_observations": [],
        }))
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        (tmp_path / "gauge.json").write_text(json.dumps(GAUGE_DATA))
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        import routes.gauges.history as history_mod

        original_jsonify = history_mod.jsonify
        call = {"n": 0}

        def faulty_jsonify(*a, **kw):
            # Pass through the first call (the validation 400 etc., though
            # none should fire here); raise on the success-path call to
            # trigger the bare-except handler.
            call["n"] += 1
            if call["n"] == 1:
                raise RuntimeError("unexpected jsonify failure")
            return original_jsonify(*a, **kw)

        monkeypatch.setattr(history_mod, "jsonify", faulty_jsonify)

        r = client.get(f"/api/v1/gauges/{GAUGE_ID}/history")
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"
