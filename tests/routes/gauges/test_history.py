# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
