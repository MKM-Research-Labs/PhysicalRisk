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
Tests for reports.gauge.gauge_integrator — file-level functions.

Covers: generate_report_for_gauge, validate_gauge_exists, get_available_gauges.
"""

import json
from pathlib import Path

import pytest


# ===========================================================================
# Helpers
# ===========================================================================

def _make_gauge_file(path: Path, gauge_id: str = "GAUGE-001") -> Path:
    data = {
        "floodGauges": [
            {
                "FloodGauge": {
                    "Header": {
                        "GaugeID": gauge_id,
                        "GaugeName": "Test Gauge",
                        "createdDate": "2024-01-01",
                        "lastModifiedDate": "2024-12-01",
                    },
                    "SensorDetails": {
                        "GaugeInformation": {
                            "GaugeType": "Pressure",
                            "GaugeOwner": "EA",
                            "OperationalStatus": "Active",
                            "GaugeLatitude": 51.5,
                            "GaugeLongitude": -0.1,
                        },
                        "SensorSpecifications": {
                            "Manufacturer": "OTT",
                            "Model": "Thalimedes",
                            "Accuracy": "±1mm",
                        },
                    },
                    "FloodStage": {
                        "UK": {
                            "FloodAlert": 4.5,
                            "FloodWarning": 5.5,
                            "SevereFloodWarning": 6.5,
                        }
                    },
                    "SensorStats": {
                        "HistoricalHighLevel": 6.85,
                        "HistoricalHighDate": "2024-01-15",
                    },
                }
            }
        ]
    }
    p = path / "gauge.json"
    p.write_text(json.dumps(data))
    return p


def _make_gauge_file_alt_key(path: Path, gauge_id: str = "GAUGE-002") -> Path:
    """Uses flood_gauges key (alternative structure)."""
    data = {
        "flood_gauges": [
            {
                "FloodGauge": {
                    "Header": {"GaugeID": gauge_id, "GaugeName": "Alt Gauge"},
                    "SensorDetails": {"GaugeInformation": {}, "SensorSpecifications": {}},
                    "FloodStage": {"UK": {}},
                    "SensorStats": {},
                }
            }
        ]
    }
    p = path / "gauge_alt.json"
    p.write_text(json.dumps(data))
    return p


# ===========================================================================
# generate_report_for_gauge
# ===========================================================================

class TestGenerateReportForGauge:

    def test_missing_file_returns_none(self, tmp_path):
        from reports.gauge.gauge_integrator import generate_report_for_gauge
        result = generate_report_for_gauge(
            "GAUGE-001",
            tmp_path / "nonexistent.json",
            tmp_path / "output",
        )
        assert result is None

    def test_gauge_not_found_returns_none(self, tmp_path):
        from reports.gauge.gauge_integrator import generate_report_for_gauge
        gauge_file = _make_gauge_file(tmp_path)
        result = generate_report_for_gauge(
            "GAUGE-NONEXISTENT",
            gauge_file,
            tmp_path / "output",
        )
        assert result is None

    def test_found_gauge_returns_path(self, tmp_path):
        from reports.gauge.gauge_integrator import generate_report_for_gauge
        gauge_file = _make_gauge_file(tmp_path)
        result = generate_report_for_gauge("GAUGE-001", gauge_file, tmp_path / "output")
        assert result is not None
        assert isinstance(result, Path)

    def test_output_file_created(self, tmp_path):
        from reports.gauge.gauge_integrator import generate_report_for_gauge
        gauge_file = _make_gauge_file(tmp_path)
        result = generate_report_for_gauge("GAUGE-001", gauge_file, tmp_path / "output")
        assert result.exists()

    def test_output_dir_created(self, tmp_path):
        from reports.gauge.gauge_integrator import generate_report_for_gauge
        gauge_file = _make_gauge_file(tmp_path)
        output_dir = tmp_path / "new_output_dir"
        generate_report_for_gauge("GAUGE-001", gauge_file, output_dir)
        assert output_dir.exists()

    def test_output_contains_gauge_id(self, tmp_path):
        from reports.gauge.gauge_integrator import generate_report_for_gauge
        gauge_file = _make_gauge_file(tmp_path)
        result = generate_report_for_gauge("GAUGE-001", gauge_file, tmp_path / "output")
        content = result.read_text()
        assert "GAUGE-001" in content

    def test_alt_key_structure_works(self, tmp_path):
        """gauge_integrator should handle flood_gauges key too."""
        from reports.gauge.gauge_integrator import generate_report_for_gauge
        gauge_file = _make_gauge_file_alt_key(tmp_path, "GAUGE-002")
        result = generate_report_for_gauge("GAUGE-002", gauge_file, tmp_path / "output")
        assert result is not None


# ===========================================================================
# validate_gauge_exists
# ===========================================================================

class TestValidateGaugeExists:

    def test_missing_file_returns_false(self, tmp_path):
        from reports.gauge.gauge_integrator import validate_gauge_exists
        assert validate_gauge_exists("GAUGE-001", tmp_path / "missing.json") is False

    def test_existing_gauge_returns_true(self, tmp_path):
        from reports.gauge.gauge_integrator import validate_gauge_exists
        gauge_file = _make_gauge_file(tmp_path)
        assert validate_gauge_exists("GAUGE-001", gauge_file) is True

    def test_nonexistent_gauge_returns_false(self, tmp_path):
        from reports.gauge.gauge_integrator import validate_gauge_exists
        gauge_file = _make_gauge_file(tmp_path)
        assert validate_gauge_exists("GAUGE-XXX", gauge_file) is False

    def test_alt_key_structure(self, tmp_path):
        from reports.gauge.gauge_integrator import validate_gauge_exists
        gauge_file = _make_gauge_file_alt_key(tmp_path, "GAUGE-002")
        assert validate_gauge_exists("GAUGE-002", gauge_file) is True


# ===========================================================================
# get_available_gauges
# ===========================================================================

class TestGetAvailableGauges:

    def test_missing_file_returns_empty_list(self, tmp_path):
        from reports.gauge.gauge_integrator import get_available_gauges
        result = get_available_gauges(tmp_path / "missing.json")
        assert result == []

    def test_returns_list(self, tmp_path):
        from reports.gauge.gauge_integrator import get_available_gauges
        gauge_file = _make_gauge_file(tmp_path)
        result = get_available_gauges(gauge_file)
        assert isinstance(result, list)

    def test_returns_correct_id(self, tmp_path):
        from reports.gauge.gauge_integrator import get_available_gauges
        gauge_file = _make_gauge_file(tmp_path, "GAUGE-001")
        result = get_available_gauges(gauge_file)
        assert "GAUGE-001" in result

    def test_returns_all_ids(self, tmp_path):
        """File with two gauges should return both IDs."""
        from reports.gauge.gauge_integrator import get_available_gauges
        data = {
            "floodGauges": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-A"}}},
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-B"}}},
            ]
        }
        p = tmp_path / "gauge2.json"
        p.write_text(json.dumps(data))
        result = get_available_gauges(p)
        assert set(result) == {"GAUGE-A", "GAUGE-B"}
