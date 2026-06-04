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


SAMPLE_PROPERTYSHD = {
    "metadata": {
        "generated_at": "2026-01-01T00:00:00",
        "catchment": "thames",
        "mode": "shd",
    },
    "summary": {
        "total_properties": 2,
        "avg_distance_km": 1.0,
    },
    "property_hazard_curves": {
        "PROP-001": {
            "property_id": "PROP-001",
            "distance_km": 1.2,
            "hazard_curve": [[0.1, 0.04], [0.5, 0.008]],
        },
        "PROP-002": {
            "property_id": "PROP-002",
            "distance_km": 0.8,
            "hazard_curve": [[0.1, 0.02]],
        },
    },
}

SAMPLE_PROPERTYSHE = {
    "metadata": {
        "generated_at": "2026-01-01T00:00:00",
        "catchment": "thames",
        "mode": "she",
    },
    "summary": {
        "total_properties": 2,
        "avg_elevation_m": 25.0,
    },
    "property_hazard_curves": {
        "PROP-001": {
            "property_id": "PROP-001",
            "elevation_m": 22.5,
            "hazard_curve": [[0.1, 0.03], [0.5, 0.006]],
        },
        "PROP-002": {
            "property_id": "PROP-002",
            "elevation_m": 27.5,
            "hazard_curve": [[0.1, 0.015]],
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


@pytest.fixture
def shd_env(tmp_path, monkeypatch):
    """Client with a minimal propertyshd.json in tmp_path."""
    from config import config
    (tmp_path / "propertyshd.json").write_text(json.dumps(SAMPLE_PROPERTYSHD))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def she_env(tmp_path, monkeypatch):
    """Client with a minimal propertyshe.json in tmp_path."""
    from config import config
    (tmp_path / "propertyshe.json").write_text(json.dumps(SAMPLE_PROPERTYSHE))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# Wind-coupled peril scenario curves (win / faw / fow). Same shape as shd/she —
# property_hazard_curves keyed by PropertyID, with a peril spread on the spine.
def _sample_peril(mode: str) -> dict:
    return {
        "metadata": {"catchment": "thames", "mode": mode},
        "summary": {"total_properties": 1},
        "property_hazard_curves": {
            "PROP-001": {
                "property_id": "PROP-001",
                "flood_count": 5,
                "term_structure": {"severe": {"prs_spread_bps": [5000.0] * 5}},
            },
        },
    }


@pytest.fixture
def win_env(tmp_path, monkeypatch):
    """Client with a minimal propertywin.json in tmp_path."""
    from config import config
    (tmp_path / "propertywin.json").write_text(json.dumps(_sample_peril("win")))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def faw_env(tmp_path, monkeypatch):
    """Client with a minimal propertyfaw.json in tmp_path."""
    from config import config
    (tmp_path / "propertyfaw.json").write_text(json.dumps(_sample_peril("faw")))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def fow_env(tmp_path, monkeypatch):
    """Client with a minimal propertyfow.json in tmp_path."""
    from config import config
    (tmp_path / "propertyfow.json").write_text(json.dumps(_sample_peril("fow")))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
