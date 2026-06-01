# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Shared fixtures and helpers for propertyts route tests."""

import json

import pytest

from tests.routes.propertyts._helpers import (
    STORM_ID,
    SEQ_ID,
    PROP_ID,
    STORM_HOURS,
    # Re-export so existing `from .conftest import X` / absolute imports work
    CLAIM_PROP_ID,
    CLAIM_PROP_FLOOD_DATA,
    CLAIM_PROPERTY_JSON,
    CLAIM_MORTGAGE_JSON,
    CLAIM_SEQUENCES_JSON,
    make_gauge_json,
    make_gaugets_json,
    make_prop_file,
    make_anim_client,
    make_storm_sequences,
    make_prop_flood,
    make_property_json,
    make_mortgage_json,
    make_risk_client,
    PORTFOLIO_VAR_URL,
)


@pytest.fixture
def pts_client_no_data(tmp_path, monkeypatch):
    """Flask test client where no propertyts directory exists."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: tmp_path / "gaugets")
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def pts_env(tmp_path, monkeypatch):
    """
    Flask test client with a minimal propertyts directory and supporting data.

    Creates:
      tmp_path/propertyts/PROP-001.json   -- one property with one flood event
      tmp_path/storm_sequences.json       -- one sequence with one storm
      tmp_path/gauge.json                 -- one gauge
      tmp_path/gaugets/GAUGE-001.json     -- minimal gauge timeseries
      tmp_path/property.json              -- property valuation
      tmp_path/loan.json              -- mortgage data

    Returns: dict with keys 'client', 'storm_id', 'seq_id'
    """
    from config import config

    pts_dir = tmp_path / "propertyts"
    pts_dir.mkdir()
    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir()

    sequences_data = {
        "schema_version": "2.0-multi-storm",
        "num_sequences": 1,
        "sequences": [{
            "sequence_id": SEQ_ID,
            "sequence_type": "isolated",
            "intensity_category": "moderate",
            "sequence_start": "2024-01-01T00:00:00+00:00",
            "total_duration_hours": 24.0,
            "event_window_hours": 168,
            "drainage_window_hours": 12.0,
            "storms": [{
                "storm_id": STORM_ID,
                "scenario_id": SEQ_ID,
                "storm_index": 0,
                "start_time_hours": 0.0,
                "duration_hours": 24.0,
                "intensity_category": "moderate",
                "intensity_factor": 1.0,
                "precipitation_mm": 55.0,
                "peak_position": 0.5,
            }],
            "num_storms": 1,
            "inter_storm_gaps_hours": [],
            "total_precipitation_mm": 55.0,
            "max_intensity_factor": 1.0,
            "avg_intensity_factor": 1.0,
            "cumulative_intensity_factor": 1.0,
        }],
    }
    (tmp_path / "storm_sequences.json").write_text(json.dumps(sequences_data))

    # stress_storms/_index.json — used by /propertyts/storms primary code path
    ss_dir = tmp_path / "stress_storms"
    ss_dir.mkdir()
    ss_index = {
        "storms": [{
            "storm_id": SEQ_ID,
            "name": "Moderate",
            "intensity_category": "moderate",
            "effective_precipitation_mm": 55.0,
            "duration_hours": 24.0,
            "peak_position": 0.5,
            "trigger_summary": {
                "gauges_severe": 1,
                "gauges_warning": 1,
                "gauges_alert": 1,
                "gauges_impacted": 1,
            },
        }],
    }
    (ss_dir / "_index.json").write_text(json.dumps(ss_index))

    gauge_data = {"flood_gauges": [{"FloodGauge": {
        "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test Gauge"},
        "SensorDetails": {"GaugeInformation": {
            "GaugeLatitude": 51.5, "GaugeLongitude": -0.1, "GroundLevelMeters": 3.0
        }},
        "FloodStage": {"UK": {
            "FloodAlert": 4.0, "FloodWarning": 4.5, "SevereFloodWarning": 5.0
        }},
    }}]}
    (tmp_path / "gauge.json").write_text(json.dumps(gauge_data))

    gauge_ts = {
        "gauge_id": "GAUGE-001",
        "flood_simulation": {"readings": [{"waterLevel": 4.2}] * 168},
        "storm_responses": {"responses": [{
            "storm_id": STORM_ID,
            "base_level_m": 2.5,
            "level_change_m": 2.7,
            "peak_level_m": 5.2,
            "exceeded_alert": True,
            "exceeded_warning": True,
            "exceeded_severe": True,
        }]},
    }
    (gaugets_dir / "GAUGE-001.json").write_text(json.dumps(gauge_ts))

    prop_data = {
        "property_id": PROP_ID,
        "location": {"lat": 51.5, "lon": -0.12},
        "elevation_m": 3.0,
        "floor_level_m": 3.2,
        "nearest_gauges": [{"gauge_id": "GAUGE-001", "distance_m": 500}],
        "summary": {"storms_flooded": 1, "max_depth_m": 0.5},
        "flood_events": [{
            "storm_id": SEQ_ID,
            "flooded": True,
            "exceeded_severe": True,
            "flood_depth_m": 0.5,
            "damage_ratio": 0.1,
            "arrival_time_hrs": 5,
            "peak_time_hrs": 12,
            "travel_time_hrs": 5,
            "retention_factor": 0.9,
            "readings": [
                {"wse_m": 3.4 + 0.01 * h, "depth_m": max(0, 0.2 - 0.005 * h),
                 "flooded": h < 20}
                for h in range(168)
            ],
        }],
    }
    (pts_dir / f"{PROP_ID}.json").write_text(json.dumps(prop_data))

    property_data = {"properties": [{
        "PropertyHeader": {
            "Header": {"PropertyID": PROP_ID},
            "Valuation": {"PropertyValue": 400000},
        }
    }]}
    (tmp_path / "property.json").write_text(json.dumps(property_data))

    rloan_data = {"loans": [{
        "RLoan": {
            "Header": {"RLoanID": "MORT-001", "PropertyID": PROP_ID},
            "FinancialTerms": {"OriginalBalance": 300000},
            "CurrentStatus": {
                "OutstandingBalance": 280000,
                "CurrentLTV": 70.0,
                "RemainingTerm": 240,
            },
        }
    }]}
    (tmp_path / "loan.json").write_text(json.dumps(rloan_data))

    summary = {"total_properties": 1, "storm_count": 1}
    (pts_dir / "portfolio_flood_summary.json").write_text(json.dumps(summary))

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_input_path", lambda fname: tmp_path / fname)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return {"client": app.test_client(), "storm_id": SEQ_ID, "seq_id": SEQ_ID}
