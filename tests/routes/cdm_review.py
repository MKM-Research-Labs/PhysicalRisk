# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
