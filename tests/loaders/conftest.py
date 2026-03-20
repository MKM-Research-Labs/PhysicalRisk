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

"""Shared fixtures and data helpers for all loader tests."""

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Data builders
# ---------------------------------------------------------------------------

def gauge_json(n=2):
    return {
        "flood_gauges": [
            {
                "FloodGauge": {
                    "Header": {"GaugeID": f"GAUGE-{i:03d}", "GaugeName": f"Gauge {i}"},
                    "SensorDetails": {
                        "GaugeInformation": {
                            "GaugeType": "Pressure",
                            "GaugeOwner": "EA",
                            "OperationalStatus": "Active",
                            "GaugeLatitude": 51.5,
                            "GaugeLongitude": -0.1,
                        }
                    },
                    "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
                }
            }
            for i in range(n)
        ]
    }


def property_json(n=2):
    return {
        "properties": [
            {
                "PropertyHeader": {
                    "Header": {"PropertyID": f"PROP-{i:03d}"},
                    "Location": {
                        "Address": f"{i} Test St",
                        "City": "London",
                        "Latitude": 51.5 + i * 0.01,
                        "Longitude": -0.1,
                    },
                    "RiskAssessment": {"OverallFloodRisk": "Medium"},
                }
            }
            for i in range(n)
        ]
    }


def mortgage_json(n=2):
    return {
        "mortgages": [
            {
                "MortgageID": f"MORT-{i:03d}",
                "PropertyID": f"PROP-{i:03d}",
                "LoanAmount": 300_000,
                "InterestRate": 0.035,
                "LoanType": "Fixed",
                "Status": "Active",
            }
            for i in range(n)
        ]
    }


def write_json(path: Path, data) -> Path:
    path.write_text(json.dumps(data))
    return path


def make_gauge_ts_file(gaugets_dir: Path, gauge_id="GAUGE-001") -> Path:
    """Create a gauge timeseries JSON inside a gaugets/ directory."""
    f = gaugets_dir / f"{gauge_id}.json"
    data = {
        "gauge_id": gauge_id,
        "flood_simulation": {
            "readings": [
                {
                    "timestamp": "2024-01-01T00:00:00",
                    "waterLevel": 3.5,
                    "alertLevel": 4.0,
                    "warningLevel": 4.5,
                    "severeLevel": 5.0,
                    "alertStatus": "Normal",
                }
            ]
        },
    }
    f.write_text(json.dumps(data))
    return f
