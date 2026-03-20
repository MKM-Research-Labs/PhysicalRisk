# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for port.src.gauge.gaugehd.runner — batch runners and CLI."""

import json
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Shared gauge entry used across tests
_GAUGE_ENTRY = {
    "FloodGauge": {
        "Header": {
            "GaugeID": "GAUGE-TEST01",
            "GaugeName": "Test Gauge",
            "CatchmentID": "thames",
        },
        "FloodStages": {
            "FloodAlert": 3.0,
            "FloodWarning": 4.5,
            "SevereFloodWarning": 5.5,
        },
        "Location": {
            "GaugeLatitude": 51.5,
            "GaugeLongitude": -0.1,
            "GaugeElevation": 5.0,
        },
        "SensorStats": {
            "HistoricalHighLevel": 7.2,
        },
    }
}


def _write_nrfa_csv(path: Path, station_id: str = "39001", n_rows: int = 5) -> Path:
    """Write a minimal NRFA GDF CSV file."""
    from datetime import date, timedelta
    lines = [
        "file,timestamp,2024-01-01T00:00",
        "database,id,7",
        "database,name,NRFA",
        f"station,id,{station_id}",
        f"station,name,Thames at Kingston",
        "station,gridReference,TQ170699",
        "dataType,id,33",
        "dataType,name,gauged daily flow",
        "dataType,parameter,flow",
        "dataType,units,m3/s",
        "dataType,period,day",
        "dataType,measurementType,mean",
        "data,first,1970-01-01",
        "data,last,2024-01-01",
    ]
    start = date(2020, 1, 1)
    for i in range(n_rows):
        d = start + timedelta(days=i)
        lines.append(f"{d.isoformat()},{10.0 + i * 0.5}")
    p = path / f"{station_id}_gdf.csv"
    p.write_text("\n".join(lines))
    return p


def _setup_gauge_env(tmp_path, monkeypatch, gauge_entries=None):
    """Set up gauge.json and gaugehd dir, returns (gauge_file, gaugehd_dir)."""
    from config import config
    if gauge_entries is None:
        gauge_entries = [_GAUGE_ENTRY]
    gauge_data = {"flood_gauges": gauge_entries}
    gauge_file = tmp_path / "gauge.json"
    gauge_file.write_text(json.dumps(gauge_data))
    gaugehd_dir = tmp_path / "gaugehd"
    gaugehd_dir.mkdir()
    monkeypatch.setattr(config, "get_input_path", lambda f: gauge_file)
    monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
    return gauge_file, gaugehd_dir


# ===========================================================================
# generate_all_gauge_histories — stale file cleanup
# ===========================================================================

class TestStaleFileCleanup:

    def test_removes_stale_gauge_files(self, tmp_path, monkeypatch):
        """Lines 37-39: old gauge_GAUGE-*_hd.json files are removed."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        _, gaugehd_dir = _setup_gauge_env(tmp_path, monkeypatch)
        # Create a stale file that should be cleaned up
        stale = gaugehd_dir / "gauge_GAUGE-OLD_hd.json"
        stale.write_text("{}")
        assert stale.exists()
        generate_all_gauge_histories(years=5)
        assert not stale.exists()

    def test_does_not_remove_non_matching_files(self, tmp_path, monkeypatch):
        """Only gauge_GAUGE-*_hd.json files are removed, not other files."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        _, gaugehd_dir = _setup_gauge_env(tmp_path, monkeypatch)
        other = gaugehd_dir / "other_data.json"
        other.write_text("{}")
        generate_all_gauge_histories(years=5)
        assert other.exists()

    def test_removes_multiple_stale_files(self, tmp_path, monkeypatch):
        """Multiple stale files are all removed."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        _, gaugehd_dir = _setup_gauge_env(tmp_path, monkeypatch)
        stales = []
        for i in range(3):
            s = gaugehd_dir / f"gauge_GAUGE-STALE{i}_hd.json"
            s.write_text("{}")
            stales.append(s)
        generate_all_gauge_histories(years=5)
        for s in stales:
            assert not s.exists()


# ===========================================================================
# generate_all_gauge_histories — error handling
# ===========================================================================

class TestGenerateAllErrorPaths:

    def test_error_extracts_gauge_id_from_nested_header(self, tmp_path, monkeypatch, caplog):
        """Line 50: error path extracts GaugeID from FloodGauge.Header."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        bad_entry = {
            "FloodGauge": {
                "Header": {"GaugeID": "GAUGE-BADONE"},
                "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.5, "SevereFloodWarning": 5.5},
            }
        }
        _setup_gauge_env(tmp_path, monkeypatch, gauge_entries=[bad_entry])
        # Mock generate_from_gauge_portfolio to raise an error
        with patch("port.src.gauge.gaugehd.runner.generate_from_gauge_portfolio",
                   side_effect=ValueError("test error")):
            with caplog.at_level(logging.ERROR):
                result = generate_all_gauge_histories(years=5)
        assert len(result) == 0
        assert "GAUGE-BADONE" in caplog.text

    def test_error_with_no_header_uses_unknown(self, tmp_path, monkeypatch, caplog):
        """Line 50: completely empty entry uses UNKNOWN as gauge_id."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        _setup_gauge_env(tmp_path, monkeypatch, gauge_entries=[{}])
        with patch("port.src.gauge.gaugehd.runner.generate_from_gauge_portfolio",
                   side_effect=RuntimeError("boom")):
            with caplog.at_level(logging.ERROR):
                result = generate_all_gauge_histories(years=5)
        assert len(result) == 0
        assert "UNKNOWN" in caplog.text

    def test_mixed_good_and_bad_gauges(self, tmp_path, monkeypatch):
        """Good gauges succeed even when bad ones fail."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        _setup_gauge_env(tmp_path, monkeypatch, gauge_entries=[_GAUGE_ENTRY, _GAUGE_ENTRY])
        call_count = [0]
        real_generate = None

        def _side_effect(entry, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("first gauge fails")
            # Import and call real function for second gauge
            from port.src.gauge.gaugehd.synthetic import generate_from_gauge_portfolio as real
            return real(entry, **kwargs)

        with patch("port.src.gauge.gaugehd.runner.generate_from_gauge_portfolio",
                   side_effect=_side_effect):
            result = generate_all_gauge_histories(years=5)
        assert len(result) == 1  # only the second one

    def test_empty_portfolio_returns_empty(self, tmp_path, monkeypatch):
        """No gauges in portfolio returns empty list."""
        from port.src.gauge.gaugehd.runner import generate_all_gauge_histories
        _setup_gauge_env(tmp_path, monkeypatch, gauge_entries=[])
        result = generate_all_gauge_histories(years=5)
        assert result == []


# ===========================================================================
# process_nrfa_directory — additional coverage
# ===========================================================================

class TestProcessNrfaDirectoryRunner:

    def test_custom_pattern(self, tmp_path):
        """Line 61/80: custom glob pattern selects different files."""
        from port.src.gauge.gaugehd.runner import process_nrfa_directory
        # Write a file with non-default pattern
        csv_file = tmp_path / "station1_daily.csv"
        lines = [
            "file,timestamp,2024-01-01T00:00",
            "station,id,S001",
            "station,name,Test Station",
            "2020-01-01,10.0",
            "2020-01-02,11.0",
        ]
        csv_file.write_text("\n".join(lines))
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(
            tmp_path, output_dir=output_dir, years=5, pattern="*_daily.csv"
        )
        assert len(result) == 1

    def test_multiple_csv_files(self, tmp_path):
        """Multiple CSV files in directory are all processed."""
        from port.src.gauge.gaugehd.runner import process_nrfa_directory
        _write_nrfa_csv(tmp_path, station_id="39001", n_rows=10)
        _write_nrfa_csv(tmp_path, station_id="39002", n_rows=10)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, output_dir=output_dir, years=5)
        assert len(result) == 2

    def test_station_id_from_filename(self, tmp_path):
        """Line 81: station_id extracted by stripping _gdf from stem."""
        from port.src.gauge.gaugehd.runner import process_nrfa_directory
        _write_nrfa_csv(tmp_path, station_id="99999", n_rows=5)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, output_dir=output_dir, years=5)
        assert len(result) == 1
        assert "99999" in result[0]

    def test_error_in_one_csv_continues(self, tmp_path, caplog):
        """Line 87-88: error on one file doesn't stop processing others."""
        from port.src.gauge.gaugehd.runner import process_nrfa_directory
        # One good, one bad
        _write_nrfa_csv(tmp_path, station_id="GOOD1", n_rows=10)
        bad = tmp_path / "BAD1_gdf.csv"
        bad.write_text("not valid csv content at all")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        with caplog.at_level(logging.ERROR):
            result = process_nrfa_directory(tmp_path, output_dir=output_dir, years=5)
        # Good file should succeed
        assert len(result) >= 1


# ===========================================================================
# main() — CLI entry point
# ===========================================================================

class TestMain:

    def test_main_default_synthetic(self, tmp_path, monkeypatch):
        """Lines 120-122: default (no --nrfa-dir) calls generate_all_gauge_histories."""
        from port.src.gauge.gaugehd.runner import main
        _setup_gauge_env(tmp_path, monkeypatch)
        monkeypatch.setattr("sys.argv", ["gaugehd"])
        main()

    def test_main_with_years(self, tmp_path, monkeypatch):
        """Line 101: --years flag is passed through."""
        from port.src.gauge.gaugehd.runner import main
        _setup_gauge_env(tmp_path, monkeypatch)
        monkeypatch.setattr("sys.argv", ["gaugehd", "--years", "10"])
        main()

    def test_main_with_catchment(self, tmp_path, monkeypatch):
        """Lines 107-108: --catchment sets config.CATCHMENT."""
        from config import config
        from port.src.gauge.gaugehd.runner import main
        _setup_gauge_env(tmp_path, monkeypatch)
        original = config.CATCHMENT
        monkeypatch.setattr("sys.argv", ["gaugehd", "--catchment", "severn"])
        main()
        assert config.CATCHMENT == "severn"
        config.CATCHMENT = original  # restore

    def test_main_with_nrfa_dir(self, tmp_path, monkeypatch):
        """Lines 117-119: --nrfa-dir calls process_nrfa_directory."""
        from port.src.gauge.gaugehd.runner import main
        nrfa_dir = tmp_path / "nrfa"
        nrfa_dir.mkdir()
        _write_nrfa_csv(nrfa_dir, station_id="39001", n_rows=10)
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        from config import config
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
        monkeypatch.setattr("sys.argv", [
            "gaugehd", "--nrfa-dir", str(nrfa_dir), "--years", "5"
        ])
        main()
        # Should have created output file
        assert list(gaugehd_dir.glob("gauge_*_hd.json"))

    def test_main_short_years_flag(self, tmp_path, monkeypatch):
        """Line 101: -y short flag for years."""
        from port.src.gauge.gaugehd.runner import main
        _setup_gauge_env(tmp_path, monkeypatch)
        monkeypatch.setattr("sys.argv", ["gaugehd", "-y", "3"])
        main()

    def test_main_short_catchment_flag(self, tmp_path, monkeypatch):
        """Line 102: -c short flag for catchment."""
        from config import config
        from port.src.gauge.gaugehd.runner import main
        _setup_gauge_env(tmp_path, monkeypatch)
        original = config.CATCHMENT
        monkeypatch.setattr("sys.argv", ["gaugehd", "-c", "thames"])
        main()
        config.CATCHMENT = original

    def test_main_no_catchment_leaves_config_unchanged(self, tmp_path, monkeypatch):
        """Lines 107-108: without --catchment, config.CATCHMENT is untouched."""
        from config import config
        from port.src.gauge.gaugehd.runner import main
        _setup_gauge_env(tmp_path, monkeypatch)
        original = config.CATCHMENT
        monkeypatch.setattr("sys.argv", ["gaugehd"])
        main()
        assert config.CATCHMENT == original
