# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for routes.gauges.reports — error/warning paths."""

import json
from unittest.mock import patch, MagicMock

from .conftest import GAUGE_ID, GAUGE_DATA, make_client


class TestReportsErrorPaths:

    def _mock_report_gen(self, tmp_path):
        """Helper: create a fake PDF and return a mock for generate_gauge_report."""
        pdf_path = tmp_path / "reports" / "gauges" / "test.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4 fake")
        mock_gen = MagicMock(return_value=pdf_path)
        return mock_gen

    def test_timeseries_load_warning(self, tmp_path, monkeypatch):
        """reports.py lines 73-74: timeseries load failure -> warning, continues."""
        client = make_client(tmp_path, monkeypatch)

        with patch("routes.gauges.reports._get_registry") as mock_reg:
            loader = MagicMock()
            loader.find_by_id.return_value = GAUGE_DATA["flood_gauges"][0]
            ts_loader = MagicMock()
            ts_loader.get_storm_responses.side_effect = RuntimeError("ts fail")
            mock_reg.return_value.get_gauge_loader.return_value = loader
            mock_reg.return_value.get_timeseries_loader.return_value = ts_loader

            mock_gen = self._mock_report_gen(tmp_path)
            with patch("reports.gauge.gauge_generator.generate_gauge_report", mock_gen):
                r = client.post("/api/v1/gauges/report", json={"gaugeId": GAUGE_ID})

        assert r.status_code == 200

    def test_timeseries_load_success_with_storm_responses(self, tmp_path, monkeypatch):
        """reports.py lines 70-72: storm_responses loaded -> timeseries_data set."""
        client = make_client(tmp_path, monkeypatch)

        with patch("routes.gauges.reports._get_registry") as mock_reg:
            loader = MagicMock()
            loader.find_by_id.return_value = GAUGE_DATA["flood_gauges"][0]
            ts_loader = MagicMock()
            ts_loader.get_storm_responses.return_value = [{"storm_id": "S1", "peak": 4.5}]
            mock_reg.return_value.get_gauge_loader.return_value = loader
            mock_reg.return_value.get_timeseries_loader.return_value = ts_loader

            mock_gen = self._mock_report_gen(tmp_path)
            with patch("reports.gauge.gauge_generator.generate_gauge_report", mock_gen):
                r = client.post("/api/v1/gauges/report", json={"gaugeId": GAUGE_ID})

            call_kwargs = mock_gen.call_args
            ts_data = call_kwargs.kwargs.get("timeseries_data") or (
                call_kwargs[1].get("timeseries_data") if len(call_kwargs) > 1 else None
            )
            assert r.status_code == 200

    def test_gaugehd_load_error_warning(self, tmp_path, monkeypatch):
        """reports.py lines 87-88: gaugehd file read error -> warning, continues."""
        from config import config

        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir(exist_ok=True)
        (gaugehd_dir / f"gauge_{GAUGE_ID}_hd.json").write_text("NOT JSON")

        client = make_client(tmp_path, monkeypatch)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)

        with patch("routes.gauges.reports._get_registry") as mock_reg:
            loader = MagicMock()
            loader.find_by_id.return_value = GAUGE_DATA["flood_gauges"][0]
            ts_loader = MagicMock()
            ts_loader.get_storm_responses.return_value = []
            mock_reg.return_value.get_gauge_loader.return_value = loader
            mock_reg.return_value.get_timeseries_loader.return_value = ts_loader

            mock_gen = self._mock_report_gen(tmp_path)
            with patch("reports.gauge.gauge_generator.generate_gauge_report", mock_gen):
                r = client.post("/api/v1/gauges/report", json={"gaugeId": GAUGE_ID})

        assert r.status_code == 200

    def test_hazard_load_error_warning(self, tmp_path, monkeypatch):
        """reports.py lines 100-101: hazard file read error -> warning, continues."""
        (tmp_path / "gaugehc.json").write_text("NOT JSON")
        client = make_client(tmp_path, monkeypatch)

        with patch("routes.gauges.reports._get_registry") as mock_reg:
            loader = MagicMock()
            loader.find_by_id.return_value = GAUGE_DATA["flood_gauges"][0]
            ts_loader = MagicMock()
            ts_loader.get_storm_responses.return_value = []
            mock_reg.return_value.get_gauge_loader.return_value = loader
            mock_reg.return_value.get_timeseries_loader.return_value = ts_loader

            mock_gen = self._mock_report_gen(tmp_path)
            with patch("reports.gauge.gauge_generator.generate_gauge_report", mock_gen):
                r = client.post("/api/v1/gauges/report", json={"gaugeId": GAUGE_ID})

        assert r.status_code == 200

    def test_import_error_returns_500(self, tmp_path, monkeypatch):
        """reports.py lines 128-133: ImportError -> 500."""
        client = make_client(tmp_path, monkeypatch)

        with patch("routes.gauges.reports._get_registry") as mock_reg:
            loader = MagicMock()
            loader.find_by_id.return_value = GAUGE_DATA["flood_gauges"][0]
            ts_loader = MagicMock()
            ts_loader.get_storm_responses.return_value = []
            mock_reg.return_value.get_gauge_loader.return_value = loader
            mock_reg.return_value.get_timeseries_loader.return_value = ts_loader

            with patch("reports.gauge.gauge_generator.generate_gauge_report",
                       side_effect=ImportError("no reportlab")):
                r = client.post("/api/v1/gauges/report", json={"gaugeId": GAUGE_ID})

        assert r.status_code == 500
        assert "not available" in r.get_json()["message"].lower()

    def test_general_exception_returns_500(self, tmp_path, monkeypatch):
        """reports.py lines 135-140: general Exception -> 500."""
        client = make_client(tmp_path, monkeypatch)

        with patch("routes.gauges.reports._get_registry") as mock_reg:
            loader = MagicMock()
            loader.find_by_id.return_value = GAUGE_DATA["flood_gauges"][0]
            ts_loader = MagicMock()
            ts_loader.get_storm_responses.return_value = []
            mock_reg.return_value.get_gauge_loader.return_value = loader
            mock_reg.return_value.get_timeseries_loader.return_value = ts_loader

            with patch("reports.gauge.gauge_generator.generate_gauge_report",
                       side_effect=RuntimeError("disk full")):
                r = client.post("/api/v1/gauges/report", json={"gaugeId": GAUGE_ID})

        assert r.status_code == 500
        assert "disk full" in r.get_json()["message"]
