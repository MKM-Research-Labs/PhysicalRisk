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
Tests for PropertyTimeSeriesGenerator.generate() — ratio branch and logging.
"""

import json
from unittest.mock import patch

from db_helpers import tmp_catchment

from .conftest import make_generator, make_prop

# ===========================================================================
# generate() — ratio branch (lines 170-176)
# ===========================================================================

class TestGenerateRatioBranch:

    def _make_gauge_json(self, path):
        """Write minimal gauge.json."""
        data = {
            "flood_gauges": [
                {
                    "FloodGauge": {
                        "Header": {"GaugeID": "GAUGE-001"},
                        "SensorDetails": {
                            "GaugeInformation": {
                                "GaugeLatitude": 51.50,
                                "GaugeLongitude": -0.10,
                                "GroundLevelMeters": 3.0,
                            }
                        },
                        "FloodStage": {
                            "UK": {
                                "FloodAlert": 3.5,
                                "FloodWarning": 4.5,
                                "SevereFloodWarning": 5.0,
                            }
                        },
                    }
                }
            ]
        }
        path.write_text(json.dumps(data))

    def _make_property_json(self, path):
        """Write minimal property.json with one property."""
        data = {"properties": [make_prop()]}
        path.write_text(json.dumps(data))

    def _make_gaugets_dir(self, gaugets_dir, with_alert_storms=True):
        """Write gaugets dir with per-gauge files."""
        gaugets_dir.mkdir(parents=True, exist_ok=True)
        gt_data = {
            "gauge_id": "GAUGE-001",
            "storm_responses": {
                "responses": [
                    {
                        "storm_id": "STORM-001",
                        "peak_level_m": 5.5,
                        "exceeded_alert": with_alert_storms,
                    }
                ]
            },
            "flood_simulation": {
                "readings": [
                    {"hour": h, "waterLevel": 5.5 * max(0, 1 - abs(h - 12) / 20)}
                    for h in range(25)
                ]
            },
        }
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gt_data))

    def test_ratio_computed_when_storms_present(self, tmp_path):
        """Line 171: ratio branch when total_storms_at_gauge > 0."""
        gen = make_generator(tmp_path)

        input_dir = tmp_path / "input" / "thames"
        input_dir.mkdir(parents=True)
        self._make_gauge_json(input_dir / "gauge.json")
        self._make_property_json(input_dir / "property.json")
        gaugets_dir = input_dir / "gaugets"
        self._make_gaugets_dir(gaugets_dir, with_alert_storms=True)

        with tmp_catchment(input_dir, "thames"):
            result = gen.generate()

        assert "gauge_to_property_ratio" in result
        assert result["gauge_to_property_ratio"] >= 0.0

    def test_ratio_zero_when_no_gauge_storms(self, tmp_path):
        """Line 176: ratio=0 branch when total_storms_at_gauge == 0."""
        gen = make_generator(tmp_path)

        input_dir = tmp_path / "input" / "thames"
        input_dir.mkdir(parents=True)
        self._make_gauge_json(input_dir / "gauge.json")
        self._make_property_json(input_dir / "property.json")
        gaugets_dir = input_dir / "gaugets"
        self._make_gaugets_dir(gaugets_dir, with_alert_storms=False)

        with tmp_catchment(input_dir, "thames"):
            with patch("models.audit.log_model_usage"):
                result = gen.generate()

        assert result["gauge_to_property_ratio"] == 0.0

    def test_logging_milestone_at_50(self, tmp_path):
        """Line 167: log milestone every 50 properties."""
        gen = make_generator(tmp_path)
        # Build 55 properties
        props = [make_prop(prop_id=f"PROP-{i:04d}", lat=51.5 + i*0.001)
                 for i in range(1, 56)]

        input_dir = tmp_path / "input" / "thames"
        input_dir.mkdir(parents=True)
        self._make_gauge_json(input_dir / "gauge.json")
        (input_dir / "property.json").write_text(
            json.dumps({"properties": props})
        )
        gaugets_dir = input_dir / "gaugets"
        self._make_gaugets_dir(gaugets_dir, with_alert_storms=False)

        log_messages = []
        original_log = gen.log
        gen.log = lambda msg: log_messages.append(msg)

        with tmp_catchment(input_dir, "thames"):
            with patch("models.audit.log_model_usage"):
                gen.generate()

        assert any("50" in m for m in log_messages)
