# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Shared fixtures for tests/routes/ — properties and propertyhc."""

import json
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_registry(monkeypatch):
    """Return a mock LoaderRegistry wired into the properties route."""
    from routes.properties import _get_registry

    mock_reg = MagicMock()
    monkeypatch.setattr("routes.properties._get_registry", lambda: mock_reg)
    return mock_reg


@pytest.fixture
def prop_client(mock_registry, monkeypatch):
    """Flask test client with mocked loader registry."""
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), mock_registry


# ---------------------------------------------------------------------------
# Property hazard curve fixtures (shared by propertyhc_part*.py)
# ---------------------------------------------------------------------------

SAMPLE_PROPERTYHC = {
    "metadata": {
        "generated_at": "2026-01-01T00:00:00",
        "catchment": "thames",
        "num_properties": 2,
    },
    "summary": {
        "total_properties": 2,
        "avg_flood_count": 3.5,
    },
    "property_hazard_curves": {
        "PROP-001": {
            "property_id": "PROP-001",
            "flood_count": 4,
            "summary": {
                "avg_basis_bps": 5.2,
                "flood_transmission_rate": 0.08,
                "max_depth_m": 0.65,
            },
            "nearest_gauges": [
                {
                    "gauge_id": "GAUGE-AAA",
                    "distance_km": 1.2,
                    "event_basis": 4.8,
                    "flood_transmission_rate": 0.07,
                }
            ],
            "hazard_curve": [[0.1, 0.05], [0.5, 0.01]],
        },
        "PROP-002": {
            "property_id": "PROP-002",
            "flood_count": 3,
            "summary": {
                "avg_basis_bps": 3.1,
                "flood_transmission_rate": 0.06,
                "max_depth_m": 0.3,
            },
            "nearest_gauges": [
                {
                    "gauge_id": "GAUGE-BBB",
                    "distance_km": 0.8,
                    "event_basis": 2.9,
                    "flood_transmission_rate": 0.05,
                }
            ],
            "hazard_curve": [[0.1, 0.03]],
        },
    },
}


@pytest.fixture
def phc_client_no_data(tmp_path, monkeypatch):
    """Client where propertyhc.json does not exist."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def phc_env(tmp_path, monkeypatch):
    """Client with a minimal propertyhc.json in tmp_path."""
    from config import config
    (tmp_path / "propertyhc.json").write_text(json.dumps(SAMPLE_PROPERTYHC))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
