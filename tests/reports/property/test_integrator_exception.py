"""
Tests for missing coverage in reports.property.property_integrator.

Covers:
- Lines 131-133: exception handler in generate_report_for_property returns None
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGenerateReportForPropertyException:
    """Lines 131-133: exception during report generation returns None."""

    def test_corrupt_property_file_returns_none(self, tmp_path):
        """A file with invalid JSON triggers an exception -> return None."""
        from reports.property.property_integrator import generate_report_for_property
        prop_file = tmp_path / "property.json"
        prop_file.write_text("{invalid json")
        mort_file = tmp_path / "mortgage.json"
        output_dir = tmp_path / "output"
        result = generate_report_for_property("PROP-001", prop_file, mort_file, output_dir)
        assert result is None

    def test_permission_error_returns_none(self, tmp_path):
        """Simulated write permission error returns None."""
        from reports.property.property_integrator import generate_report_for_property
        # Create valid property file
        data = {
            "properties": [
                {
                    "PropertyHeader": {
                        "Header": {"PropertyID": "PROP-001"},
                        "Location": {},
                    }
                }
            ]
        }
        prop_file = tmp_path / "property.json"
        prop_file.write_text(json.dumps(data))
        mort_file = tmp_path / "mortgage.json"  # does not exist

        # Patch open to raise on the report file write
        original_open = open

        def patched_open(path, *args, **kwargs):
            path_str = str(path)
            if "property_report_" in path_str:
                raise PermissionError("Simulated write error")
            return original_open(path, *args, **kwargs)

        with patch("builtins.open", side_effect=patched_open):
            result = generate_report_for_property(
                "PROP-001", prop_file, mort_file, tmp_path / "output"
            )
        assert result is None
