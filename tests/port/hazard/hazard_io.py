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
Tests for models.hazard.io — I/O functions for hazard curve data.

Covers: load_storms, load_gauges (success, no gauges, no gauge_id),
save_hazard_curves, save_gauge_storm_responses.
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pytest

from models.hazard.data_structures import (
    GaugeHazardCurve,
    GaugeResponse,
    HazardCurvePoint,
    TermStructurePoint,
)


# ===========================================================================
# Helpers
# ===========================================================================

def _make_gauge_json(gauge_id="GAUGE-001"):
    """Minimal gauge.json structure compatible with FloodGaugeCDM."""
    return {
        "flood_gauges": [
            {
                "FloodGauge": {
                    "Header": {
                        "GaugeID": gauge_id,
                        "GaugeName": "Test Gauge",
                    },
                    "Location": {
                        "GaugeLatitude": 51.5,
                        "GaugeLongitude": -0.1,
                        "GaugeDatum": 5.0,
                    },
                    "FloodStage": {
                        "UK": {
                            "FloodAlert": 4.0,
                            "FloodWarning": 4.5,
                            "SevereFloodWarning": 5.0,
                        }
                    },
                    "SensorDetails": {
                        "GaugeInformation": {
                            "GaugeType": "Pressure",
                            "GaugeOwner": "EA",
                            "OperationalStatus": "Active",
                            "GaugeLatitude": 51.5,
                            "GaugeLongitude": -0.1,
                            "GaugeDatum": 5.0,
                        },
                        "SensorSpecifications": {},
                        "Measurements": {},
                    },
                    "SensorStats": {},
                    "NRFAMetadata": {},
                }
            }
        ]
    }


def _make_storms_json(n=3):
    return {
        "storms": [
            {
                "storm_id": f"STORM-{i:04d}",
                "name": f"Storm {i}",
                "effective_precipitation_mm": 50.0 + i * 10,
            }
            for i in range(n)
        ]
    }


def _make_hazard_curve(gauge_id="GAUGE-001"):
    return GaugeHazardCurve(
        gauge_id=gauge_id,
        gauge_name="Test Gauge",
        latitude=51.5,
        longitude=-0.1,
        elevation_m=5.0,
        flood_alert_m=4.0,
        flood_warning_m=4.5,
        severe_flood_warning_m=5.0,
        gev_location=4.0,
        gev_scale=0.5,
        gev_shape=0.1,
        curve_points=[
            HazardCurvePoint(4.0, 0.20, 5.0),
            HazardCurvePoint(5.0, 0.05, 20.0),
        ],
        return_period_levels={"10yr": 4.5, "50yr": 5.0, "100yr": 5.5},
        annual_flood_prob_alert=0.15,
        annual_flood_prob_warning=0.08,
        annual_flood_prob_severe=0.03,
        annual_hazard_rate_alert=0.15,
        annual_hazard_rate_warning=0.08,
        annual_hazard_rate_severe=0.03,
        term_structure_alert=[
            TermStructurePoint(1, 0.15, 0.14, 0.86, 0.14),
            TermStructurePoint(2, 0.30, 0.26, 0.74, 0.26),
        ],
        term_structure_warning=[
            TermStructurePoint(1, 0.08, 0.077, 0.923, 0.077),
        ],
        term_structure_severe=[
            TermStructurePoint(1, 0.03, 0.030, 0.970, 0.030),
        ],
        num_storms_simulated=100,
        simulation_timestamp=datetime.now().isoformat(),
    )


# ===========================================================================
# load_storms
# ===========================================================================

class TestLoadStorms:

    def test_loads_list(self, tmp_path):
        from models.hazard.io import load_storms
        p = tmp_path / "storms.json"
        p.write_text(json.dumps(_make_storms_json(5)))
        result = load_storms(p)
        assert isinstance(result, list)
        assert len(result) == 5

    def test_storm_has_id(self, tmp_path):
        from models.hazard.io import load_storms
        p = tmp_path / "storms.json"
        p.write_text(json.dumps(_make_storms_json(2)))
        result = load_storms(p)
        assert result[0]["storm_id"] == "STORM-0000"

    def test_file_not_found_raises(self, tmp_path):
        from models.hazard.io import load_storms
        with pytest.raises((FileNotFoundError, OSError)):
            load_storms(tmp_path / "missing.json")


# ===========================================================================
# load_gauges
# ===========================================================================

class TestLoadGauges:

    def test_loads_gauges(self, tmp_path):
        from models.hazard.io import load_gauges
        p = tmp_path / "gauge.json"
        p.write_text(json.dumps(_make_gauge_json()))
        result = load_gauges(p)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_gauge_has_id(self, tmp_path):
        from models.hazard.io import load_gauges
        p = tmp_path / "gauge.json"
        p.write_text(json.dumps(_make_gauge_json("GAUGE-999")))
        result = load_gauges(p)
        assert result[0]["gauge_id"] == "GAUGE-999"

    def test_empty_gauge_list_raises(self, tmp_path):
        from models.hazard.io import load_gauges
        p = tmp_path / "gauge.json"
        p.write_text(json.dumps({"flood_gauges": []}))
        with pytest.raises(ValueError, match="No gauges found"):
            load_gauges(p)

    def test_file_not_found_raises(self, tmp_path):
        from models.hazard.io import load_gauges
        with pytest.raises((FileNotFoundError, OSError)):
            load_gauges(tmp_path / "missing.json")

    def test_gauge_without_gauge_id_raises(self, tmp_path):
        """Gauge that maps to no gauge_id raises ValueError."""
        from models.hazard.io import load_gauges
        # A gauge record with no Header/GaugeID → CDM maps gauge_id to None
        bad_gauge = {
            "flood_gauges": [
                {
                    "FloodGauge": {
                        "Header": {},  # No GaugeID
                        "Location": {},
                        "SensorDetails": {"GaugeInformation": {}},
                        "SensorStats": {},
                        "NRFAMetadata": {},
                        "FloodStage": {},
                    }
                }
            ]
        }
        p = tmp_path / "gauge.json"
        p.write_text(json.dumps(bad_gauge))
        with pytest.raises(ValueError, match="gauge_id"):
            load_gauges(p)


# ===========================================================================
# save_hazard_curves
# ===========================================================================

class TestSaveHazardCurves:

    def test_creates_file(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        output_path = tmp_path / "gaugehc.json"
        result = save_hazard_curves(
            {"GAUGE-001": curve}, output_path, "thames"
        )
        assert output_path.exists()
        assert result == output_path

    def test_file_has_metadata(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        output_path = tmp_path / "gaugehc.json"
        save_hazard_curves({"GAUGE-001": curve}, output_path, "thames")
        data = json.loads(output_path.read_text())
        assert "metadata" in data
        assert data["metadata"]["catchment_id"] == "thames"

    def test_file_has_hazard_curves(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        output_path = tmp_path / "gaugehc.json"
        save_hazard_curves({"GAUGE-001": curve}, output_path, "thames")
        data = json.loads(output_path.read_text())
        assert "GAUGE-001" in data["hazard_curves"]

    def test_creates_parent_dirs(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        output_path = tmp_path / "subdir" / "nested" / "gaugehc.json"
        save_hazard_curves({"GAUGE-001": curve}, output_path, "thames")
        assert output_path.exists()

    def test_metadata_merged(self, tmp_path):
        from models.hazard.io import save_hazard_curves
        curve = _make_hazard_curve()
        output_path = tmp_path / "gaugehc.json"
        save_hazard_curves(
            {"GAUGE-001": curve}, output_path, "thames",
            metadata={"num_storms": 100, "distribution": "gev"}
        )
        data = json.loads(output_path.read_text())
        assert data["metadata"]["num_storms"] == 100


# ===========================================================================
# save_gauge_storm_responses
# ===========================================================================

class TestSaveGaugeStormResponses:

    def _make_responses(self, gauge_id="GAUGE-001", n=2):
        return [
            GaugeResponse(
                gauge_id=gauge_id,
                storm_id=f"STORM-{i:04d}",
                base_level_m=3.0,
                level_change_m=1.0 + i * 0.5,
                peak_level_m=4.0 + i * 0.5,
                exceeded_alert=True,
                exceeded_warning=i > 0,
                exceeded_severe=False,
            )
            for i in range(n)
        ]

    def test_creates_gauge_file(self, tmp_path):
        from models.hazard.io import save_gauge_storm_responses
        responses = {"GAUGE-001": self._make_responses()}
        result = save_gauge_storm_responses(responses, tmp_path / "gaugets", "thames")
        assert (tmp_path / "gaugets" / "GAUGE-001.json").exists()

    def test_saved_file_has_responses(self, tmp_path):
        from models.hazard.io import save_gauge_storm_responses
        responses = {"GAUGE-001": self._make_responses(n=3)}
        gaugets_dir = tmp_path / "gaugets"
        save_gauge_storm_responses(responses, gaugets_dir, "thames")
        data = json.loads((gaugets_dir / "GAUGE-001.json").read_text())
        assert "storm_responses" in data
        assert len(data["storm_responses"]["responses"]) == 3

    def test_merges_with_existing_file(self, tmp_path):
        """If gauge file already exists, merge storm_responses into it."""
        from models.hazard.io import save_gauge_storm_responses
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        existing = {
            "gauge_id": "GAUGE-001",
            "flood_simulation": {"readings": []},
        }
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(existing))
        responses = {"GAUGE-001": self._make_responses(n=1)}
        save_gauge_storm_responses(responses, gaugets_dir, "thames")
        data = json.loads((gaugets_dir / "GAUGE-001.json").read_text())
        assert "flood_simulation" in data
        assert "storm_responses" in data

    def test_multiple_gauges(self, tmp_path):
        from models.hazard.io import save_gauge_storm_responses
        responses = {
            "GAUGE-001": self._make_responses("GAUGE-001", 2),
            "GAUGE-002": self._make_responses("GAUGE-002", 2),
        }
        gaugets_dir = tmp_path / "gaugets"
        save_gauge_storm_responses(responses, gaugets_dir, "thames")
        assert (gaugets_dir / "GAUGE-001.json").exists()
        assert (gaugets_dir / "GAUGE-002.json").exists()
