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
Tests for generate() with multi-storm gaugets -- portfolio summary.

Verifies that the full generate() pipeline correctly counts all events
across multi-storm sequences in the portfolio summary.
"""

import json
from unittest.mock import patch

import pytest

from tests.port.property.conftest import make_prop, make_readings


class TestGenerateWithMultiStormGaugets:
    """Full generate() with a multi-storm gaugets directory."""

    def _write_gauge_json(self, path):
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
                                "SevereFloodWarning": 5.5,
                            }
                        },
                    }
                }
            ]
        }
        path.write_text(json.dumps(data))

    def _write_property_json(self, path):
        data = {"properties": [make_prop(elevation=4.0, floor_level=0.2)]}
        path.write_text(json.dumps(data))

    def _write_multi_storm_gaugets(self, gaugets_dir, storm_defs):
        gaugets_dir.mkdir(parents=True, exist_ok=True)
        gt_data = {
            "gauge_id": "GAUGE-001",
            "storm_responses": {
                "responses": [
                    {
                        "storm_id": sid,
                        "peak_level_m": peak,
                        "exceeded_alert": exceeded,
                    }
                    for sid, peak, exceeded in storm_defs
                ]
            },
            "flood_simulation": {
                "readings": make_readings(6.0)
            },
        }
        (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gt_data))

    def test_portfolio_summary_counts_all_sequence_storms(self, tmp_path):
        """Portfolio summary total_storms_at_gauge counts all alert storms."""
        from port.src.property.propertyts import PropertyTimeSeriesGenerator

        input_dir = tmp_path / "input" / "thames"
        input_dir.mkdir(parents=True)
        self._write_gauge_json(input_dir / "gauge.json")
        self._write_property_json(input_dir / "property.json")

        # Doublet: 2 alert-breaching storms
        storm_defs = [
            ("STORM-seq1a", 5.5, True),
            ("STORM-seq1b", 5.8, True),
        ]
        gaugets_dir = input_dir / "gaugets"
        self._write_multi_storm_gaugets(gaugets_dir, storm_defs)

        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False)

        with patch("port.src.property.ts.loader.config") as mock_cfg:
            mock_cfg.CATCHMENT = "thames"
            mock_cfg.get_input_path = lambda name: input_dir / name
            mock_cfg.get_gaugets_dir = lambda: gaugets_dir
            mock_cfg.get_input_dir = lambda: tmp_path
            with patch("models.audit.log_model_usage"):
                result = gen.generate()

        # 2 alert storms at gauge for 1 property
        assert result["total_storms_at_gauge"] == 2

    def test_portfolio_summary_written_for_cluster(self, tmp_path):
        """portfolio_flood_summary.json is written with per-property data."""
        from port.src.property.propertyts import PropertyTimeSeriesGenerator

        input_dir = tmp_path / "input" / "thames"
        input_dir.mkdir(parents=True)
        self._write_gauge_json(input_dir / "gauge.json")
        self._write_property_json(input_dir / "property.json")

        # Cluster: 3 alert storms
        storm_defs = [
            ("STORM-cl1a", 5.2, True),
            ("STORM-cl1b", 5.6, True),
            ("STORM-cl1c", 5.4, True),
        ]
        gaugets_dir = input_dir / "gaugets"
        self._write_multi_storm_gaugets(gaugets_dir, storm_defs)

        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False)

        pts_dir = tmp_path / "propertyts"

        with patch("port.src.property.ts.loader.config") as mock_cfg:
            mock_cfg.CATCHMENT = "thames"
            mock_cfg.get_input_path = lambda name: input_dir / name
            mock_cfg.get_gaugets_dir = lambda: gaugets_dir
            mock_cfg.get_input_dir = lambda: tmp_path
            with patch("models.audit.log_model_usage"):
                gen.generate()

        summary_path = pts_dir / "portfolio_flood_summary.json"
        assert summary_path.exists()

        with open(summary_path) as f:
            summary = json.load(f)

        assert summary["summary"]["total_gauges"] == 1
        assert "properties" in summary

    def test_no_alert_storms_in_sequence_zero_floods(self, tmp_path):
        """If all sequence storms are sub-alert, portfolio flood count is 0."""
        from port.src.property.propertyts import PropertyTimeSeriesGenerator

        input_dir = tmp_path / "input" / "thames"
        input_dir.mkdir(parents=True)
        self._write_gauge_json(input_dir / "gauge.json")
        self._write_property_json(input_dir / "property.json")

        storm_defs = [
            ("STORM-sub1", 3.0, False),
            ("STORM-sub2", 3.1, False),
            ("STORM-sub3", 2.9, False),
        ]
        gaugets_dir = input_dir / "gaugets"
        self._write_multi_storm_gaugets(gaugets_dir, storm_defs)

        gen = PropertyTimeSeriesGenerator(output_dir=tmp_path, verbose=False)

        with patch("port.src.property.ts.loader.config") as mock_cfg:
            mock_cfg.CATCHMENT = "thames"
            mock_cfg.get_input_path = lambda name: input_dir / name
            mock_cfg.get_gaugets_dir = lambda: gaugets_dir
            mock_cfg.get_input_dir = lambda: tmp_path
            with patch("models.audit.log_model_usage"):
                result = gen.generate()

        assert result["total_storms_at_gauge"] == 0
        assert result["properties_with_floods"] == 0
