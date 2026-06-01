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

"""Non-fixture helpers and test data constants extracted from conftest.py.

Contains: shared constants, builder helpers for animation tests,
and factory functions for portfolio VaR / risk tests.
"""

import json


STORM_ID = "STORM-0001"
SEQ_ID = "STORM-seq0001"
PROP_ID = "PROP-001"
STORM_HOURS = 168

# ---------------------------------------------------------------------------
# Shared constants for claim report tests (claim_part*.py)
# ---------------------------------------------------------------------------

CLAIM_PROP_ID = "PROP-001"

CLAIM_PROP_FLOOD_DATA = {
    "property_id": CLAIM_PROP_ID,
    "location": {"lat": 51.5, "lon": -0.1},
    "elevation_m": 3.0,
    "floor_level_m": 3.2,
    "flood_events": [{
        "storm_id": "STORM-0001",
        "sequence_id": "STORM-seq0001",
        "flooded": True,
        "exceeded_severe": True,
        "flood_depth_m": 0.5,
        "damage_ratio": 0.1,
        "arrival_time_hrs": 5,
        "peak_time_hrs": 12,
        "travel_time_hrs": 5,
        "retention_factor": 0.9,
        "readings": [{"wse_m": 3.4, "depth_m": 0.2, "flooded": True}],
    }],
}

CLAIM_PROPERTY_JSON = {"properties": [{"PropertyHeader": {
    "Header": {"PropertyID": CLAIM_PROP_ID},
    "Valuation": {"PropertyValue": 400000},
}}]}

CLAIM_MORTGAGE_JSON = {"loans": [{"RLoan": {
    "Header": {"RLoanID": "MORT-001", "PropertyID": CLAIM_PROP_ID},
    "FinancialTerms": {"OriginalBalance": 300000},
    "CurrentStatus": {"OutstandingBalance": 280000},
}}]}

CLAIM_SEQUENCES_JSON = {"sequences": [{"sequence_id": "STORM-seq0001", "sequence_type": "isolated",
                                        "num_storms": 1, "intensity_category": "moderate",
                                        "storms": [{"storm_id": "STORM-0001"}]}]}


# ---------------------------------------------------------------------------
# Builder helpers — used by animation test files
# ---------------------------------------------------------------------------

def make_gauge_json(gauge_id="GAUGE-001", alert=4.0, warning=4.5, severe=5.0):
    return {"flood_gauges": [{"FloodGauge": {
        "Header": {"GaugeID": gauge_id, "GaugeName": "Test Gauge"},
        "SensorDetails": {"GaugeInformation": {
            "GaugeLatitude": 51.5, "GaugeLongitude": -0.1, "GroundLevelMeters": 3.0,
        }},
        "FloodStage": {"UK": {
            "FloodAlert": alert, "FloodWarning": warning, "SevereFloodWarning": severe,
        }},
    }}]}


def make_gaugets_json(gauge_id="GAUGE-001", level=4.2, n=STORM_HOURS, key="waterLevel"):
    return {
        "gauge_id": gauge_id,
        "flood_simulation": {"readings": [{key: level}] * n},
    }


def make_prop_file(property_id, storm_id, flood_depth=0.5, damage_ratio=0.1,
                   arrival=5, peak=12, n_readings=STORM_HOURS):
    readings = [
        {"wse_m": 3.4, "depth_m": max(0, flood_depth - 0.01 * h), "flooded": h < 20}
        for h in range(n_readings)
    ]
    return {
        "property_id": property_id,
        "location": {"lat": 51.5, "lon": -0.12},
        "elevation_m": 3.0,
        "floor_level_m": 3.2,
        "flood_events": [{
            "storm_id": storm_id,
            "flooded": flood_depth > 0,
            "exceeded_severe": True,
            "flood_depth_m": flood_depth,
            "damage_ratio": damage_ratio,
            "arrival_time_hrs": arrival,
            "peak_time_hrs": peak,
            "travel_time_hrs": 5,
            "retention_factor": 0.9,
            "readings": readings,
        }],
    }


def make_anim_client(tmp_path, monkeypatch, *,
                     pts_dir=True, gauge_json=None, gaugets=None, prop_files=None):
    """Build a minimal test client for animation routes."""
    from config import config
    if pts_dir:
        (tmp_path / "propertyts").mkdir(exist_ok=True)
    gaugets_dir = tmp_path / "gaugets"
    gaugets_dir.mkdir(exist_ok=True)
    if gauge_json is not None:
        (tmp_path / "gauge.json").write_text(json.dumps(gauge_json))
    for fname, data in (gaugets or {}).items():
        (gaugets_dir / fname).write_text(json.dumps(data))
    for fname, data in (prop_files or {}).items():
        (tmp_path / "propertyts" / fname).write_text(json.dumps(data))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
    monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ---------------------------------------------------------------------------
# Helpers for portfolio VaR / risk tests (risk_part*.py)
# ---------------------------------------------------------------------------

def make_storm_sequences(*storm_ids):
    """Build storm_sequences.json data.

    In the current model, storm_id in propertyts IS the sequence_id,
    so sequence_id must match the storm_id used in flood events.
    """
    return {
        "sequences": [
            {"sequence_id": sid, "storms": [{"storm_id": f"{sid}-pulse0"}]}
            for sid in storm_ids
        ]
    }


def make_prop_flood(property_id, flood_events):
    return {"property_id": property_id, "flood_events": flood_events}


def make_property_json(property_id, value):
    return {"properties": [{"PropertyHeader": {
        "Header": {"PropertyID": property_id},
        "Valuation": {"PropertyValue": value},
    }}]}


def make_mortgage_json(property_id, outstanding):
    return {"loans": [{"RLoan": {
        "Header": {"RLoanID": "MORT-001", "PropertyID": property_id},
        "FinancialTerms": {"OriginalBalance": outstanding},
        "CurrentStatus": {"OutstandingBalance": outstanding},
    }}]}


def make_risk_client(tmp_path, monkeypatch, *, pts_dir=True, sequences=None,
                     prop_floods=None, property_json=None, mortgage_json=None):
    """Generic factory for propertyts test clients."""
    from config import config

    if pts_dir:
        (tmp_path / "propertyts").mkdir(exist_ok=True)

    if sequences is not None:
        (tmp_path / "storm_sequences.json").write_text(json.dumps(sequences))

    for fname, data in (prop_floods or {}).items():
        (tmp_path / "propertyts" / fname).write_text(json.dumps(data))

    if property_json is not None:
        (tmp_path / "property.json").write_text(json.dumps(property_json))

    if mortgage_json is not None:
        (tmp_path / "loan.json").write_text(json.dumps(mortgage_json))

    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


PORTFOLIO_VAR_URL = "/api/v1/propertyts/portfolio-var"
