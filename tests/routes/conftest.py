# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Shared fixtures for tests/routes/properties_*.py."""

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
