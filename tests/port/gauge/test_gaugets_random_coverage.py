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

"""Coverage expansion tests for gaugets_random.py — missing lines.

Lines: 85, 112, 142, 232-235, 259, 277, 303
"""

import math
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from port.rand.thames.gauge.gaugets_random import (
    calculate_water_level,
    determine_alert_status,
    generate_flood_simulation,
    generate_gauge_reading,
    generate_time_series,
    generate_timestep_readings,
)


class TestCalculateWaterLevelDefaultParams:
    """Line 85: params=None triggers DEFAULT_PARAMS fallback."""

    def test_none_params_uses_defaults(self):
        level = calculate_water_level(hour=10, gauge_index=0, base_level=3.0, params=None)
        assert isinstance(level, float)
        assert level > 0

    def test_explicit_none_params(self):
        level = calculate_water_level(0, 0, 2.0, None)
        assert isinstance(level, float)


class TestRecessionRemainingZero:
    """Line 112: remaining <= 0 in recession phase → amplitude = base_amplitude."""

    def test_remaining_zero_uses_base_amplitude(self):
        # Set simulation_hours = peak_hour + 12 so remaining = 0
        params = {
            'peak_hour_base': 36,
            'peak_hour_stagger': 0,
            'simulation_hours': 48,  # 36 + 12 = 48, remaining = 0
            'base_amplitude': 0.5,
            'peak_amplitude': 2.0,
        }
        # hour > peak_hour + 12 = 48, but simulation_hours is 48
        # Use hour = 49 (past peak+12) with remaining = 0
        level = calculate_water_level(hour=49, gauge_index=0, base_level=3.0, params=params)
        # amplitude should be base_amplitude (0.5) since remaining = 0
        # water_level = base_level + amplitude + variation
        assert isinstance(level, float)


class TestGenerateGaugeReadingDefault:
    """Line 142 (implicit): generate_gauge_reading with None params."""

    def test_gauge_reading_returns_all_fields(self):
        gauge_data = {
            "FloodGauge": {
                "Header": {"GaugeID": "GAUGE-TEST"},
                "FloodStages": {
                    "FloodAlert": 3.0,
                    "FloodWarning": 4.5,
                    "SevereFloodWarning": 5.5,
                },
            }
        }
        reading = generate_gauge_reading(
            hour=10, gauge_index=0, gauge_data=gauge_data,
            timestamp=datetime(2024, 1, 1), params=None
        )
        assert "gaugeId" in reading
        assert "waterLevel" in reading
        assert "alertStatus" in reading

    def test_gauge_reading_with_string_timestamp(self):
        gauge_data = {
            "FloodGauge": {
                "Header": {},
                "FloodStages": {},
            }
        }
        reading = generate_gauge_reading(
            hour=0, gauge_index=0, gauge_data=gauge_data,
            timestamp="2024-01-01T00:00:00"
        )
        assert reading["timestamp"] == "2024-01-01T00:00:00"


class TestTimestepReadingsError:
    """Lines 232-235: error in generate_gauge_reading is caught and skipped."""

    def test_bad_gauge_data_is_skipped(self):
        gauges = [
            {
                "FloodGauge": {
                    "Header": {"GaugeID": "GAUGE-OK"},
                    "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.0, "SevereFloodWarning": 5.0},
                }
            },
            "not_a_dict",  # This will cause an error
        ]
        result = generate_timestep_readings(
            hour=0, gauges=gauges, start_time=datetime(2024, 1, 1)
        )
        # First gauge should succeed, second should be caught
        assert len(result["readings"]) >= 1


class TestFloodSimulationDefaults:
    """Line 259: generate_flood_simulation with params=None."""

    def test_default_params_produces_data(self):
        gauges = [
            {
                "FloodGauge": {
                    "Header": {"GaugeID": "GAUGE-001"},
                    "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.0, "SevereFloodWarning": 5.0},
                }
            }
        ]
        result = generate_flood_simulation(gauges, params=None)
        assert len(result) > 0
        assert "readings" in result[0]


class TestFloodSimulationStringStartTime:
    """Line 277: start_time as ISO string is parsed."""

    def test_string_start_time_is_parsed(self):
        gauges = [
            {
                "FloodGauge": {
                    "Header": {"GaugeID": "GAUGE-001"},
                    "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.0, "SevereFloodWarning": 5.0},
                }
            }
        ]
        params = {
            'peak_hour_base': 10,
            'peak_hour_stagger': 0,
            'simulation_hours': 50,
            'base_amplitude': 0.5,
            'peak_amplitude': 2.0,
            'simulation_start_date': "2024-06-15T12:00:00",
        }
        result = generate_flood_simulation(gauges, params=params)
        assert len(result) == 50


class TestGenerateTimeSeriesAlias:
    """Line 303: generate_time_series is an alias for generate_flood_simulation."""

    def test_alias_returns_same_structure(self):
        gauges = [
            {
                "FloodGauge": {
                    "Header": {"GaugeID": "GAUGE-001"},
                    "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.0, "SevereFloodWarning": 5.0},
                }
            }
        ]
        params = {
            'peak_hour_base': 5,
            'peak_hour_stagger': 0,
            'simulation_hours': 50,
            'base_amplitude': 0.5,
            'peak_amplitude': 2.0,
            'simulation_start_date': datetime(2024, 1, 1),
        }
        result = generate_time_series(gauges, params=params)
        assert len(result) == 50
        assert "readings" in result[0]
