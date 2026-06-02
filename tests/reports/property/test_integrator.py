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
Tests for generate_report_for_property in reports.property.property_integrator.

Covers: property not found, missing file, with mortgage data, without mortgage
data, and the output file structure.
"""

import json
from pathlib import Path


# ===========================================================================
# Helpers
# ===========================================================================

def _make_property_file(path: Path, property_id: str = "PROP-001") -> Path:
    data = {
        "properties": [
            {
                "PropertyHeader": {
                    "Header": {"PropertyID": property_id},
                    "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
                    "Valuation": {"PropertyValue": 400_000},
                    "RiskAssessment": {"OverallFloodRisk": "Medium"},
                }
            }
        ]
    }
    p = path / "property.json"
    p.write_text(json.dumps(data))
    return p


def _make_mortgage_file(path: Path, property_id: str = "PROP-001") -> Path:
    data = {
        "loans": [
            {
                "RLoan": {
                    "Header": {"RLoanID": "MORT-001", "PropertyID": property_id},
                    "FinancialTerms": {"OriginalLoan": 300_000},
                    "CurrentStatus": {"OutstandingBalance": 280_000},
                }
            }
        ]
    }
    p = path / "loan.json"
    p.write_text(json.dumps(data))
    return p


# ===========================================================================
# Tests
# ===========================================================================

class TestGenerateReportForProperty:

    def test_missing_property_file_returns_none(self, tmp_path):
        from reports.property.property_integrator import generate_report_for_property
        result = generate_report_for_property(
            "PROP-001",
            tmp_path / "nonexistent.json",
            tmp_path / "loan.json",
            tmp_path / "output",
        )
        assert result is None

    def test_property_not_found_returns_none(self, tmp_path):
        from reports.property.property_integrator import generate_report_for_property
        prop_file = _make_property_file(tmp_path, "PROP-001")
        result = generate_report_for_property(
            "PROP-NONEXISTENT",
            prop_file,
            tmp_path / "loan.json",
            tmp_path / "output",
        )
        assert result is None

    def test_found_property_returns_path(self, tmp_path):
        from reports.property.property_integrator import generate_report_for_property
        prop_file = _make_property_file(tmp_path)
        mort_file = _make_mortgage_file(tmp_path)
        output_dir = tmp_path / "output"
        result = generate_report_for_property("PROP-001", prop_file, mort_file, output_dir)
        assert result is not None
        assert isinstance(result, Path)

    def test_output_file_created(self, tmp_path):
        from reports.property.property_integrator import generate_report_for_property
        prop_file = _make_property_file(tmp_path)
        mort_file = _make_mortgage_file(tmp_path)
        output_dir = tmp_path / "output"
        result = generate_report_for_property("PROP-001", prop_file, mort_file, output_dir)
        assert result.exists()

    def test_output_dir_created(self, tmp_path):
        from reports.property.property_integrator import generate_report_for_property
        prop_file = _make_property_file(tmp_path)
        output_dir = tmp_path / "new_output_dir"
        # No mortgage file
        generate_report_for_property(
            "PROP-001", prop_file,
            tmp_path / "nomortgage.json",
            output_dir,
        )
        assert output_dir.exists()

    def test_no_mortgage_file_still_generates(self, tmp_path):
        from reports.property.property_integrator import generate_report_for_property
        prop_file = _make_property_file(tmp_path)
        output_dir = tmp_path / "output"
        # No mortgage.json at path
        result = generate_report_for_property(
            "PROP-001", prop_file,
            tmp_path / "no_mortgage.json",
            output_dir,
        )
        # Should return a path (report without mortgage info)
        assert result is not None

    def test_output_contains_property_id(self, tmp_path):
        from reports.property.property_integrator import generate_report_for_property
        prop_file = _make_property_file(tmp_path)
        mort_file = _make_mortgage_file(tmp_path)
        output_dir = tmp_path / "output"
        result = generate_report_for_property("PROP-001", prop_file, mort_file, output_dir)
        # Report file should mention PROP-001 somehow
        content = result.read_text()
        assert "PROP-001" in content
