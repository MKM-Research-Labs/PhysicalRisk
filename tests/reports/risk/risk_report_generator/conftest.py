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

"""Shared fixtures and helpers for RiskReportGenerator tests."""

from pathlib import Path
from typing import Any, Dict
import pytest


@pytest.fixture
def output_dir(tmp_path) -> Path:
    d = tmp_path / "risk_out"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def minimal_flood_data() -> Dict[str, Any]:
    """Absolute minimum data needed to drive the report pipeline."""
    return {
        "timestamp": "2026-01-01T00:00:00",
        "catchment": "Thames",
        "summary": {
            "total_properties": 10,
            "properties_at_risk": 2,
            "percentage_at_risk": 20.0,
            "total_value": 5_000_000,
            "value_at_risk": 500_000,
            "percentage_value_at_risk": 10.0,
        },
        "gauge_data": {},
        "property_risk": {},
    }


@pytest.fixture
def full_flood_data() -> Dict[str, Any]:
    """Richer data set including mortgage summary and multiple properties/gauges."""
    gauges: Dict[str, Any] = {}
    for i in range(5):
        gid = f"GAUGE_{i:03d}"
        gauges[gid] = {
            "gauge_id": gid,
            "gauge_name": f"Station {i}",
            "latitude": 51.5 + i * 0.01,
            "longitude": -0.3 + i * 0.01,
            "elevation": 3.0 + i * 0.5,
            "max_level": 5.0 + i * 0.3,
            "severe_level": 6.0,
            "current_level": 4.5,
        }

    properties: Dict[str, Any] = {}
    for i in range(20):
        pid = f"PROP_{i:04d}"
        properties[pid] = {
            "property_id": pid,
            "latitude": 51.5 + i * 0.002,
            "longitude": -0.3 + i * 0.002,
            "elevation": 5.0 + i * 0.5,
            "property_value": 400_000 + i * 10_000,
            "flood_depth": 0.5 if i % 3 == 0 else 0.0,
            "risk_value": 0.3 if i % 3 == 0 else 0.0,
            "value_at_risk": 120_000 if i % 3 == 0 else 0.0,
            "risk_level": "Medium" if i % 3 == 0 else "Minimal",
        }

    return {
        "timestamp": "2026-01-01T00:00:00",
        "catchment": "Thames",
        "summary": {
            "total_properties": 20,
            "properties_at_risk": 7,
            "percentage_at_risk": 35.0,
            "total_value": 10_000_000,
            "value_at_risk": 2_000_000,
            "percentage_value_at_risk": 20.0,
            "mortgage_summary": {
                "total_mortgages": 15,
                "total_mortgage_value": 7_500_000,
                "mortgages_at_risk_count": 5,
                "percentage_mortgages_at_risk": 33.3,
                "mortgage_value_at_risk": 1_000_000,
                "percentage_mortgage_value_at_risk": 13.3,
            },
        },
        "gauge_data": gauges,
        "property_risk": properties,
    }


def _make_generator(tmp_path: Path):
    from reports.risk.generator import RiskReportGenerator
    return RiskReportGenerator(output_dir=tmp_path)
