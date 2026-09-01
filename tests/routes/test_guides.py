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

"""Tests for src.routes.guides — workflow user-guide PDF serving.

Relocated from tests/routes/governance/test_storm_control_guide.py when the
guides were extracted from the governance blueprint. These six guides document
operational workflows, not governance, and the Control tab's User Guide button
depends on one of them — so the route had to survive governance's removal.
"""

import pytest
from flask import Flask

from routes.guides import USER_GUIDE_PDFS, guides_bp


@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(guides_bp, url_prefix="/api/v1")
    return app.test_client()


class TestUserGuidePdfServing:
    @pytest.mark.parametrize("guide_key,doc_dir,pdf_name", [
        (k, v[0], v[1]) for k, v in USER_GUIDE_PDFS.items()
    ])
    def test_serves_pdf_when_present(self, client, tmp_path, monkeypatch,
                                     guide_key, doc_dir, pdf_name):
        """Route returns 200 and application/pdf when the PDF exists."""
        guide_dir = tmp_path / doc_dir
        guide_dir.mkdir()
        (guide_dir / pdf_name).write_bytes(b"%PDF-1.4 test content")
        monkeypatch.setattr("routes.guides._DOCS_DIR", str(tmp_path))

        r = client.get(f"/api/v1/guides/{guide_key}/pdf")
        assert r.status_code == 200
        assert r.mimetype == "application/pdf"

    @pytest.mark.parametrize("guide_key", sorted(USER_GUIDE_PDFS))
    def test_returns_404_when_missing(self, client, tmp_path, monkeypatch,
                                      guide_key):
        """A guide whose PDF has not been generated 404s with a build hint."""
        monkeypatch.setattr("routes.guides._DOCS_DIR", str(tmp_path))

        r = client.get(f"/api/v1/guides/{guide_key}/pdf")
        assert r.status_code == 404
        assert "not yet generated" in r.get_json()["message"]

    def test_unknown_guide_returns_404(self, client):
        r = client.get("/api/v1/guides/nonexistent-guide/pdf")
        assert r.status_code == 404
        assert "Unknown guide" in r.get_json()["message"]

    def test_all_six_workflows_registered(self):
        """The Control tab and the e2e control tests rely on these keys."""
        assert set(USER_GUIDE_PDFS) == {
            "storm-control", "gauge-prs-pricing", "property-prs-pricing",
            "market-making", "eod-process", "stress-testing",
        }
