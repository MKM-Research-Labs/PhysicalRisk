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

import database
from db_helpers import tmp_catchment


@pytest.fixture(autouse=True)
def _loader_catchment(tmp_path):
    """Bind a tmp-rooted backend for every loader test so loaders that read through
    the database seam resolve to this test's scratch dir (file backend) or Postgres
    (under MKM_TEST_BACKEND=pg). Loaders not yet migrated keep reading the file
    directly, so this is harmless for them."""
    with tmp_catchment(tmp_path):
        yield


# Migrated loaders read their portfolio through the seam, so seed it as well as the
# file. Only artifacts whose loader has been migrated are listed here — others stay
# file-only until their loader moves over.
_ARTIFACT_SAVERS = {
    "gauge.json": "save_gauges",
    "property.json": "save_properties",
    "loan.json": "save_loans",
}


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
    # Real loan shape: nested under RLoan (what pg's `loan` collection keys on).
    return {
        "loans": [
            {
                "RLoan": {
                    "Header": {"RLoanID": f"RLOAN-{i:03d}",
                               "PropertyID": f"PROP-{i:03d}",
                               "CatchmentID": "thames"},
                    "Application": {"MortgageProvider": "Barclays"},
                    "FinancialTerms": {"OriginalLoan": 300_000,
                                       "OriginalLendingRate": 3.5},
                    "Features": {"MortgageType": "Residential"},
                    "CurrentStatus": {"OutstandingBalance": 250_000,
                                      "AccountStatus": "Active",
                                      "DefaultFlag": False},
                }
            }
            for i in range(n)
        ]
    }


def write_json(path: Path, data) -> Path:
    path = Path(path)
    path.write_text(json.dumps(data))
    # If a migrated loader reads this artifact via the seam, seed it too so the test
    # holds on both backends. (Malformed-shape docs that pg can't store raise here;
    # those tests carry skipif(pg).)
    saver = _ARTIFACT_SAVERS.get(path.name)
    if saver is not None:
        getattr(database, saver)(database.active_catchment(), data)
    return path


def make_gauge_ts_file(gaugets_dir: Path, gauge_id="GAUGE-001") -> Path:
    """Create a gauge timeseries inside a gaugets/ directory AND seed it through the
    seam (TimeseriesLoader reads via database.get_gauge_timeseries now)."""
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
    database.save_gauge_timeseries(database.active_catchment(), gauge_id, data)
    return f


def seed_gauge_ts(gaugets_dir: Path, gauge_id: str, data: dict) -> dict:
    """Write a CUSTOM gauge timeseries to gaugets/ AND seed it through the seam, so
    TimeseriesLoader (which reads via database.get_gauge_timeseries) holds on both
    backends."""
    (Path(gaugets_dir) / f"{gauge_id}.json").write_text(json.dumps(data))
    database.save_gauge_timeseries(database.active_catchment(), gauge_id, data)
    return data


# ---------------------------------------------------------------------------
# Storm loader fixtures (shared by storm_loader_part*.py)
# ---------------------------------------------------------------------------

def make_storm(event_id, name, category=2, basin="ATL", season=2024,
               track=None, impact=None):
    return {
        "TCEvent": {
            "Header": {
                "EventID": event_id,
                "EventName": name,
                "Category": category,
                "Basin": basin,
                "Season": season,
                "StartDate": "2024-08-01",
                "EndDate": "2024-08-10",
                "PeakIntensity": 120,
            },
            "Track": track or [{"Latitude": 25.0, "Longitude": -80.0}],
            "Impact": impact or {"TotalDamage": 1_000_000},
        }
    }


STORM_FILENAME = "storm_events.json"


def write_storms(directory, storms):
    path = directory / STORM_FILENAME
    path.write_text(json.dumps({"storms": storms}))
    return path


@pytest.fixture
def storm_dir(tmp_path):
    storms = [
        make_storm("EVT-001", "Harvey", category=4, basin="ATL", season=2017,
                    track=[{"Latitude": 29.7, "Longitude": -95.4}]),
        make_storm("EVT-002", "Katrina", category=5, basin="ATL", season=2005,
                    track=[{"Latitude": 29.9, "Longitude": -90.1}]),
        make_storm("EVT-003", "Typhoon Hagibis", category=3, basin="WPAC", season=2019,
                    track=[{"Latitude": 35.0, "Longitude": 140.0}]),
        make_storm("EVT-004", "Tropical Storm Alpha", category=1, basin="ATL", season=2024,
                    track=[{"Latitude": 40.0, "Longitude": -60.0}]),
    ]
    write_storms(tmp_path, storms)
    return tmp_path


@pytest.fixture
def storm_loader(storm_dir):
    from loaders.storm_loader import StormLoader
    return StormLoader(storm_dir)
