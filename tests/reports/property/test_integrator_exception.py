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
        mort_file = tmp_path / "loan.json"
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
        mort_file = tmp_path / "loan.json"  # does not exist

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
