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

"""Shared helpers for TCEventVisualization tests."""

import json
from pathlib import Path


def _write_minimal_inputs(path: Path):
    """Write gauge + property + mortgage files for validate_input_files."""
    (path / "gauge.json").write_text(json.dumps({
        "flood_gauges": [{
            "FloodGauge": {
                "Header": {"GaugeID": "GAUGE-001", "GaugeName": "T"},
                "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
                "FloodStage": {"UK": {"FloodAlert": 4.5, "FloodWarning": 5.5,
                                      "SevereFloodWarning": 6.5}},
                "SensorDetails": {"GaugeInformation": {"GaugeDatum": 0.0}},
                "SensorStats": {"HistoricalHighLevel": 6.5},
            }
        }]
    }))
    (path / "property.json").write_text(json.dumps({
        "properties": [{
            "PropertyHeader": {
                "Header": {"PropertyID": "PROP-001"},
                "Location": {"LatitudeDegrees": 51.5, "LongitudeDegrees": -0.1},
                "RiskAssessment": {"OverallFloodRisk": "Low"},
                "Valuation": {"PropertyValue": 300000},
            }
        }]
    }))
    (path / "mortgage.json").write_text(json.dumps({
        "mortgages": [{
            "Mortgage": {
                "Header": {"MortgageID": "MORT-001", "PropertyID": "PROP-001"},
                "FinancialTerms": {"OriginalLoan": 200000},
                "CurrentStatus": {"OutstandingBalance": 180000},
            }
        }]
    }))


def _make_loaded_data(gauge=True, prop=True, mortgage=True):
    """Build a minimal LoadedData-like mock."""
    from unittest.mock import MagicMock
    ld = MagicMock()
    ld.gauge_data = {"items": []} if gauge else None
    ld.property_data = {"properties": []} if prop else None
    ld.rloan_data = {"mortgages": []} if mortgage else None
    return ld


def _write_gaugets(gaugets_dir: Path, gauge_id: str = "GAUGE-001",
                   lat: float = 51.5, lon: float = -0.1):
    """Write a minimal gaugets JSON file with storm responses."""
    gaugets_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "gauge_id": gauge_id,
        "storm_responses": {
            "responses": [
                {"storm_id": "STORM-001", "peak_level_m": 3.5, "exceeded_alert": True},
                {"storm_id": "STORM-002", "peak_level_m": 2.1, "exceeded_alert": False},
            ]
        }
    }
    (gaugets_dir / f"{gauge_id}.json").write_text(json.dumps(data))
