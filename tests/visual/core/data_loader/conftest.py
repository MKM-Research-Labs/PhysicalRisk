# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Shared file-writing helpers for DataLoader tests."""

import json
from pathlib import Path

import pytest

import database
from db_helpers import tmp_catchment


@pytest.fixture(autouse=True)
def _data_loader_catchment(tmp_path):
    """Bind an isolated catchment rooted at the test's ``tmp_path`` so loaders that
    read through the database seam (gauge/property/loan/timeseries) resolve to this
    test's scratch dir rather than the real thames portfolio. ``write_*`` helpers
    seed both the file and the seam, so a test that writes nothing sees an empty
    portfolio (file lane reads ``tmp_path``; pg lane starts from a clean catchment)."""
    with tmp_catchment(tmp_path):
        yield


def write_gauge(path: Path, gauge_id: str = "GAUGE-001") -> None:
    data = {
        "flood_gauges": [{
            "FloodGauge": {
                "Header": {"GaugeID": gauge_id, "GaugeName": "Test"},
                "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
                "FloodStage": {"UK": {"FloodAlert": 4.5, "FloodWarning": 5.5,
                                      "SevereFloodWarning": 6.5}},
                "SensorDetails": {"GaugeInformation": {"GaugeDatum": 0.0}},
                "SensorStats": {"HistoricalHighLevel": 6.5},
            }
        }]
    }
    (path / "gauge.json").write_text(json.dumps(data))
    database.save_gauges(database.active_catchment(), data)


def write_property(path: Path) -> None:
    data = {"properties": [{
        "PropertyHeader": {
            "Header": {"PropertyID": "PROP-001"},
            "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
            "RiskAssessment": {"OverallFloodRisk": "Low"},
            "Valuation": {"PropertyValue": 300000},
        }
    }]}
    (path / "property.json").write_text(json.dumps(data))
    database.save_properties(database.active_catchment(), data)


def write_mortgage(path: Path) -> None:
    data = {"loans": [{
        "RLoan": {
            "Header": {"RLoanID": "RLOAN-001", "PropertyID": "PROP-001"},
            "FinancialTerms": {"OriginalLoan": 200000},
            "CurrentStatus": {"OutstandingBalance": 180000},
        }
    }]}
    (path / "loan.json").write_text(json.dumps(data))
    database.save_loans(database.active_catchment(), data)


def write_hazard(path: Path) -> None:
    data = {
        "hazard_curves": {"GAUGE-001": {"exceedance": [0.1, 0.05]}},
        "metadata": {"distribution": "GEV", "num_storms": 1000},
    }
    (path / "gaugehc.json").write_text(json.dumps(data))


def write_property_hazard(path: Path) -> None:
    data = {
        "property_hazard_curves": {"PROP-001": {"exceedance": [0.05, 0.02]}},
        "summary": {"total_properties": 10, "avg_basis_bps": 120},
    }
    (path / "propertyhc.json").write_text(json.dumps(data))


def write_storms(path: Path) -> None:
    data = {
        "schema_version": "2.0-multi-storm",
        "num_sequences": 1,
        "sequences": [{"sequence_id": "STORM-seq001", "storms": [{"storm_id": "EVT-001"}]}],
    }
    (path / "storm_sequences.json").write_text(json.dumps(data))


def write_counterparty(path: Path) -> None:
    data = {"counterparties": [{"id": "CTPY-001", "name": "Test Bank"}]}
    (path / "counterparty.json").write_text(json.dumps(data))
