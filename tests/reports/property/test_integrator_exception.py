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
