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
Tests for models.hazard.io — coverage expansion.

Targets uncovered lines: 235, 242, 247, 254, 273, 280-281, 288.
All in build_hazard_curves(): missing files, verbose logging branches.
"""

import json
import logging

import pytest


# ===========================================================================
# build_hazard_curves — missing files
# ===========================================================================

class TestBuildHazardCurvesMissingFiles:

    def test_missing_storm_sequences_raises(self, tmp_path):
        """Line 235: FileNotFoundError when storm_sequences.json missing."""
        from models.hazard.io import build_hazard_curves
        with pytest.raises(FileNotFoundError, match="storm_sequences.json"):
            build_hazard_curves(tmp_path, "test_catchment")

    def test_missing_gauge_json_raises(self, tmp_path):
        """Line 247: FileNotFoundError when gauge.json missing."""
        from models.hazard.io import build_hazard_curves
        # Create storm_sequences.json but not gauge.json
        seq_data = {
            "sequences": [
                {
                    "sequence_id": "STORM-seq001",
                    "storms": [
                        {
                            "storm_id": "STORM-001",
                            "precipitation_mm": 50.0,
                            "duration_hours": 24,
                            "intensity_factor": 1.0,
                        }
                    ],
                }
            ]
        }
        (tmp_path / "storm_sequences.json").write_text(json.dumps(seq_data))
        with pytest.raises(FileNotFoundError, match="gauge.json"):
            build_hazard_curves(tmp_path, "test_catchment")


# ===========================================================================
# build_hazard_curves — verbose logging
# ===========================================================================

class TestBuildHazardCurvesVerbose:

    @pytest.fixture
    def hazard_dir(self, tmp_path):
        """Set up a minimal valid directory for build_hazard_curves."""
        # Storm sequences
        seq_data = {
            "sequences": [
                {
                    "sequence_id": f"STORM-seq{i:03d}",
                    "storms": [
                        {
                            "storm_id": f"STORM-{i:04d}",
                            "precipitation_mm": 30.0 + i * 2,
                            "duration_hours": 24,
                            "intensity_factor": 0.8 + i * 0.05,
                        }
                    ],
                }
                for i in range(20)
            ]
        }
        (tmp_path / "storm_sequences.json").write_text(json.dumps(seq_data))

        # Gauge data — one gauge in CDM format
        gauge_data = {
            "flood_gauges": [
                {
                    "FloodGauge": {
                        "Header": {
                            "GaugeID": "GAUGE-001",
                            "CatchmentID": "test",
                            "GaugeName": "Test Gauge",
                        },
                        "SensorStats": {
                            "HistoricalHighLevel": 5.5,
                            "HistoricalHighDate": "2020-02-14",
                            "FrequencyExceedLevel3": 3,
                        },
                        "SensorDetails": {
                            "GaugeInformation": {
                                "GaugeLatitude": 51.5,
                                "GaugeLongitude": -0.1,
                                "GroundLevelMeters": 10.0,
                            },
                            "Measurements": {},
                        },
                        "FloodStage": {
                            "UK": {
                                "FloodAlert": 3.0,
                                "FloodWarning": 3.8,
                                "SevereFloodWarning": 4.5,
                            }
                        },
                    }
                }
            ]
        }
        (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))
        return tmp_path

    def test_verbose_true_logs_messages(self, hazard_dir, caplog):
        """Lines 242, 254, 273, 280-281, 288: verbose logging."""
        from models.hazard.io import build_hazard_curves
        with caplog.at_level(logging.INFO, logger="models.hazard.io"):
            result = build_hazard_curves(hazard_dir, "test", verbose=True)

        assert result['summary']['num_gauges'] == 1
        assert result['summary']['num_storms'] == 20
        assert (hazard_dir / "gaugehc.json").exists()
        assert (hazard_dir / "gaugets").is_dir()

        # Check log messages were emitted
        log_text = caplog.text
        assert "storms" in log_text.lower() or "gauge" in log_text.lower()

    def test_verbose_false_no_log(self, hazard_dir, caplog):
        """Verbose=False should skip log messages."""
        from models.hazard.io import build_hazard_curves
        with caplog.at_level(logging.INFO, logger="models.hazard.io"):
            result = build_hazard_curves(hazard_dir, "test", verbose=False)

        assert result['summary']['num_gauges'] == 1
        # With verbose=False, no info messages from the builder or io
        info_msgs = [r for r in caplog.records if r.levelno == logging.INFO
                     and r.name == "models.hazard.io"]
        assert len(info_msgs) == 0
