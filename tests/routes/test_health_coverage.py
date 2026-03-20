# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage expansion tests for routes/health.py.

Targets uncovered lines: 41, 46, 51.
- 41: GET /favicon.ico → serves static/favicon.ico
- 46: GET /apple-touch-icon.png → serves static/apple-touch-icon.png
- 51: GET /apple-touch-icon-precomposed.png → serves static file
"""

import pytest


@pytest.fixture
def health_client(tmp_path, monkeypatch):
    """Flask test client for health routes."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


class TestStaticIcons:

    def test_favicon_ico(self, health_client):
        """Line 41: GET /favicon.ico returns the icon file."""
        r = health_client.get("/favicon.ico")
        assert r.status_code == 200
        assert r.content_type in ("image/x-icon", "image/vnd.microsoft.icon")

    def test_apple_touch_icon(self, health_client):
        """Line 46: GET /apple-touch-icon.png returns the PNG."""
        r = health_client.get("/apple-touch-icon.png")
        assert r.status_code == 200
        assert "image/png" in r.content_type

    def test_apple_touch_icon_precomposed(self, health_client):
        """Line 51: GET /apple-touch-icon-precomposed.png returns the PNG."""
        r = health_client.get("/apple-touch-icon-precomposed.png")
        assert r.status_code == 200
        assert "image/png" in r.content_type
