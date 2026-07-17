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
