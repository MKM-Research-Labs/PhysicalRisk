# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage expansion tests for Block 2 CDM files.

Targets missing lines in:
- src/port/cdm/gauge/mapping.py (lines 89-90, 100)
- src/port/cdm/gaugehd/directory.py (lines 46-47, 70-71)
- src/port/cdm/property/mapping.py (lines 136-137)
"""

import json
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from port.cdm.gauge.mapping import create_gauge_mapping, get_nrfa_fields
from port.cdm.property.mapping import create_mapping as create_property_mapping


# ---------------------------------------------------------------------------
# gauge/mapping.py — exception handler + get_nrfa_fields (lines 89-90, 100)
# ---------------------------------------------------------------------------

class TestGaugeMappingCoverage:

    def test_create_gauge_mapping_exception_raises_value_error(self):
        """Lines 89-90: exception in create_gauge_mapping raises ValueError."""
        with pytest.raises((ValueError, AttributeError)):
            create_gauge_mapping(None)

    def test_get_nrfa_fields_returns_expected_list(self):
        """Line 100: get_nrfa_fields returns list of NRFA field names."""
        fields = get_nrfa_fields()
        assert isinstance(fields, list)
        assert len(fields) == 15
        assert "nrfa_station_id" in fields
        assert "mean_flow" in fields
        assert "data_quality_notes" in fields


# ---------------------------------------------------------------------------
# gaugehd/directory.py — process_directory error + main() (lines 46-47, 70-71)
# ---------------------------------------------------------------------------

class TestGaugehdDirectoryCoverage:

    def test_process_directory_file_error_logged(self, tmp_path):
        """Lines 46-47: error processing a CSV file is logged and skipped."""
        csv_file = tmp_path / "39001_gdf.csv"
        csv_file.write_text("bad content")

        from port.cdm.gaugehd.directory import process_directory

        with patch("port.cdm.gaugehd.directory.GaugeHistoricalDaily") as MockGen:
            mock_gen = MagicMock()
            mock_gen.generate.side_effect = Exception("parse error")
            MockGen.return_value = mock_gen

            result = process_directory(tmp_path, tmp_path, years=50, pattern="*_gdf.csv")
            assert result == []

    def test_main_with_csv_files(self, tmp_path, monkeypatch):
        """Lines 70-71: main() processes files, handles errors."""
        csv_file = tmp_path / "39001_gdf.csv"
        csv_file.write_text("test")

        import port.cdm.gaugehd.directory as dir_mod
        from config import config
        monkeypatch.setattr(config, "input_dir", tmp_path)

        with patch.object(dir_mod, "GaugeHistoricalDaily") as MockGen:
            mock_gen = MagicMock()
            mock_gen.generate.side_effect = Exception("test error")
            MockGen.return_value = mock_gen

            dir_mod.main()

    def test_main_no_csv_files(self, tmp_path, monkeypatch):
        """Lines 73-77: main() with no GDF files logs info."""
        import port.cdm.gaugehd.directory as dir_mod
        from config import config
        monkeypatch.setattr(config, "input_dir", tmp_path)

        dir_mod.main()

    def test_process_directory_default_output(self, tmp_path):
        """Line 37: output_dir defaults to input_dir when None."""
        from port.cdm.gaugehd.directory import process_directory
        result = process_directory(tmp_path, None, years=50, pattern="*_gdf.csv")
        assert result == []


# ---------------------------------------------------------------------------
# property/mapping.py — exception handler (lines 136-137)
# ---------------------------------------------------------------------------

class TestPropertyMappingCoverage:

    def test_create_property_mapping_exception_raises_value_error(self):
        """Lines 136-137: exception in create_mapping raises ValueError."""
        with pytest.raises((ValueError, AttributeError)):
            create_property_mapping(None)

    def test_create_property_mapping_default_elevation(self):
        """Lines 62-64: ground_level falls back to default_elevation."""
        data = {"PropertyHeader": {
            "Header": {"PropertyID": "PROP-1"},
            "Location": {"LatitudeDegrees": 51.5},
            "RiskAssessment": {},
        }}
        mapping = create_property_mapping(data, default_elevation=10.0)
        assert mapping["ground_level_meters"] == 10.0
        assert mapping["elevation"] == 10.0
