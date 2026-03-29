# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for port.src.gauge.gaugehd.runner — part 2: NRFA processing and CLI."""

import json
import logging
from pathlib import Path

import pytest

from tests.port.gauge.conftest import SAMPLE_GAUGE_ENTRY, setup_gauge_env, write_nrfa_csv


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
        write_nrfa_csv(tmp_path, station_id="39001", n_rows=10)
        write_nrfa_csv(tmp_path, station_id="39002", n_rows=10)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, output_dir=output_dir, years=5)
        assert len(result) == 2

    def test_station_id_from_filename(self, tmp_path):
        """Line 81: station_id extracted by stripping _gdf from stem."""
        from port.src.gauge.gaugehd.runner import process_nrfa_directory
        write_nrfa_csv(tmp_path, station_id="99999", n_rows=5)
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        result = process_nrfa_directory(tmp_path, output_dir=output_dir, years=5)
        assert len(result) == 1
        assert "99999" in result[0]

    def test_error_in_one_csv_continues(self, tmp_path, caplog):
        """Line 87-88: error on one file doesn't stop processing others."""
        from port.src.gauge.gaugehd.runner import process_nrfa_directory
        # One good, one bad
        write_nrfa_csv(tmp_path, station_id="GOOD1", n_rows=10)
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
        setup_gauge_env(tmp_path, monkeypatch)
        monkeypatch.setattr("sys.argv", ["gaugehd"])
        main()

    def test_main_with_years(self, tmp_path, monkeypatch):
        """Line 101: --years flag is passed through."""
        from port.src.gauge.gaugehd.runner import main
        setup_gauge_env(tmp_path, monkeypatch)
        monkeypatch.setattr("sys.argv", ["gaugehd", "--years", "10"])
        main()

    def test_main_with_catchment(self, tmp_path, monkeypatch):
        """Lines 107-108: --catchment sets config.CATCHMENT."""
        from config import config
        from port.src.gauge.gaugehd.runner import main
        setup_gauge_env(tmp_path, monkeypatch)
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
        write_nrfa_csv(nrfa_dir, station_id="39001", n_rows=10)
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
        setup_gauge_env(tmp_path, monkeypatch)
        monkeypatch.setattr("sys.argv", ["gaugehd", "-y", "3"])
        main()

    def test_main_short_catchment_flag(self, tmp_path, monkeypatch):
        """Line 102: -c short flag for catchment."""
        from config import config
        from port.src.gauge.gaugehd.runner import main
        setup_gauge_env(tmp_path, monkeypatch)
        original = config.CATCHMENT
        monkeypatch.setattr("sys.argv", ["gaugehd", "-c", "thames"])
        main()
        config.CATCHMENT = original

    def test_main_no_catchment_leaves_config_unchanged(self, tmp_path, monkeypatch):
        """Lines 107-108: without --catchment, config.CATCHMENT is untouched."""
        from config import config
        from port.src.gauge.gaugehd.runner import main
        setup_gauge_env(tmp_path, monkeypatch)
        original = config.CATCHMENT
        monkeypatch.setattr("sys.argv", ["gaugehd"])
        main()
        assert config.CATCHMENT == original
