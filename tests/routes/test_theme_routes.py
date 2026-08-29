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

"""Tests for src.routes.theme — the ``/theme.css`` and ``/api/theme`` endpoints.

These exist for parity with MKM-ModelRisk, which serves the same two. The Folium console
does not use them — it has the same payload inlined — so the thing worth holding is that
both deliveries come from the same ``config.theme`` and cannot drift apart.
"""

import json

import pytest
from flask import Flask

from config.theme import STATUS_COLOUR_DEFAULTS, STATUS_COLOUR_TOKENS, THEME
from routes.theme import CSS_MIMETYPE, theme_bp, theme_version
from visual.theme_css import theme_css, theme_status_js


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(theme_bp)
    return app.test_client()


class TestThemeCssRoute:
    def test_serves_a_stylesheet(self, client):
        response = client.get("/theme.css")
        assert response.status_code == 200
        assert response.mimetype == CSS_MIMETYPE

    def test_body_is_the_same_block_the_console_inlines(self, client):
        """One source, two deliveries — never two copies."""
        assert client.get("/theme.css").data.decode("utf-8") == theme_css()

    def test_declares_every_token(self, client):
        body = client.get("/theme.css").data.decode("utf-8")
        for name, value in THEME.items():
            assert f"--{name}: {value};" in body


class TestThemeApiRoute:
    def test_returns_tokens_and_ramps(self, client):
        payload = client.get("/api/theme").get_json()
        assert payload["tokens"] == THEME
        assert payload["status_colours"] == STATUS_COLOUR_TOKENS
        assert payload["status_defaults"] == STATUS_COLOUR_DEFAULTS

    def test_matches_what_the_console_inlines(self, client):
        """The fetched mapping and the inlined one are the same object."""
        inlined = json.loads(
            theme_status_js()[len("window.__THEME_STATUS = "):].rstrip(";"))
        payload = client.get("/api/theme").get_json()
        assert payload["status_colours"] == inlined["ramps"]
        assert payload["status_defaults"] == inlined["defaults"]

    def test_carries_no_colour_the_tokens_do_not_define(self, client):
        payload = client.get("/api/theme").get_json()
        for ramp, mapping in payload["status_colours"].items():
            for value, token in mapping.items():
                assert token in payload["tokens"], f"{ramp}[{value}] -> {token}"


class TestThemeVersion:
    def test_is_stable_for_unchanged_tokens(self):
        assert theme_version() == theme_version()

    def test_changes_when_a_token_changes(self):
        """A rebrand must not be masked by a browser cache.

        The mutation is on the group rather than on the flat ``THEME``: the served block
        is rendered from ``THEME_GROUPS`` and ``THEME`` is derived from it, so editing
        the flat view alone would change nothing — which is the correct behaviour, and
        the reason this test reaches for the group.
        """
        from config.theme import BRAND

        before = theme_version()
        original = BRAND["accent"]
        BRAND["accent"] = "#ff0000"
        try:
            assert theme_version() != before
        finally:
            BRAND["accent"] = original
        assert theme_version() == before

    def test_is_short_enough_for_a_query_string(self):
        assert len(theme_version()) == 12
