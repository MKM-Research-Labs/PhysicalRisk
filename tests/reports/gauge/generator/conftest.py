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

"""Shared fixtures and factories for gauge generator tests."""

from pathlib import Path
from typing import Any, Dict

import pytest


def minimal_gauge(gauge_id: str = "GAUGE-001") -> Dict[str, Any]:
    """Minimal CDM-shaped single gauge dict."""
    return {
        "FloodGauge": {
            "Header": {
                "GaugeID": gauge_id,
                "GaugeName": f"Test Gauge {gauge_id}",
                "CatchmentID": "thames",
            },
            "SensorDetails": {
                "GaugeInformation": {
                    "GaugeType": "Pressure transducer",
                    "GaugeOwner": "Environment Agency",
                    "OperationalStatus": "Fully operational",
                    "GaugeLatitude": 51.461,
                    "GaugeLongitude": -0.303,
                    "GroundLevelMeters": 7.5,
                },
                "Measurements": {
                    "MeasurementFrequency": "15 minutes",
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
            "Location": {
                "GaugeLatitude": 51.461,
                "GaugeLongitude": -0.303,
                "GaugeElevation": 7.5,
            },
        }
    }


def timeseries_data() -> Dict[str, Any]:
    return {
        "gauge_id": "GAUGE-001",
        "readings": [
            {"timestamp": "2024-01-15T00:00:00", "level": 4.2},
            {"timestamp": "2024-01-15T01:00:00", "level": 5.1},
            {"timestamp": "2024-01-15T02:00:00", "level": 6.3},
        ],
    }


def make_generator(tmp_path: Path):
    from reports.gauge.gauge_generator import GaugeReportGenerator
    return GaugeReportGenerator(output_dir=tmp_path)


@pytest.fixture
def gauge_data() -> Dict[str, Any]:
    return minimal_gauge()


@pytest.fixture
def ts_data() -> Dict[str, Any]:
    return timeseries_data()


@pytest.fixture
def output_dir(tmp_path) -> Path:
    d = tmp_path / "gauge_out"
    d.mkdir(parents=True)
    return d
