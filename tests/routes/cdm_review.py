# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for routes.cdm_review — CDM Asset Review launch redirect.

Covers: /cdm-asset-review redirects to the standalone tool (default host:port)
and honours the CDM_REVIEW_URL override.
"""

from flask import Flask


def _client():
    from routes.cdm_review import cdm_review_bp
    app = Flask(__name__)
    app.register_blueprint(cdm_review_bp)
    app.config["TESTING"] = True
    return app.test_client()


class TestRedirect:

    def test_redirects_to_default_port(self, monkeypatch):
        monkeypatch.delenv("CDM_REVIEW_URL", raising=False)
        from routes import cdm_review
        r = _client().get("/cdm-asset-review")
        assert r.status_code == 302
        # default target is <scheme>://<host>:<CDM_REVIEW_PORT>/
        assert r.headers["Location"].endswith(":" + cdm_review.CDM_REVIEW_PORT + "/")

    def test_url_override_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("CDM_REVIEW_URL", "http://example.test/cdm/")
        r = _client().get("/cdm-asset-review")
        assert r.status_code == 302
        assert r.headers["Location"] == "http://example.test/cdm/"

    def test_only_get(self):
        r = _client().post("/cdm-asset-review")
        assert r.status_code == 405
