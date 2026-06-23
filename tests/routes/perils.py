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

"""Tests for routes.perils — fire / seismic peril-model endpoints.

Covers: /api/v1/fire and /api/v1/seismic — present file → JSON passthrough,
missing file → empty object, malformed file → empty object.
"""

import json

from flask import Flask


def _client(input_dir, monkeypatch):
    """A minimal app with just the perils blueprint, rooted at input_dir."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: input_dir)
    from routes.perils import perils_bp
    app = Flask(__name__)
    app.register_blueprint(perils_bp, url_prefix="/api/v1")
    app.config["TESTING"] = True
    return app.test_client()


def _write(input_dir, subdir, filename, payload):
    (input_dir / subdir).mkdir(parents=True, exist_ok=True)
    (input_dir / subdir / filename).write_text(json.dumps(payload))


class TestFire:

    def test_returns_fire_json(self, tmp_path, monkeypatch):
        import database
        from db_helpers import tmp_catchment
        with tmp_catchment(tmp_path):
            database.save_fire_results(database.active_catchment(),
                {"metadata": {"model": "MKM-FIRE-001"},
                 "assets": [{"asset_id": "CPROP-1"}, {"asset_id": "CPROP-2"}]})
            r = _client(tmp_path, monkeypatch).get("/api/v1/fire")
            assert r.status_code == 200
            d = r.get_json()
        assert d["metadata"]["model"] == "MKM-FIRE-001"
        assert len(d["assets"]) == 2

    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        r = _client(tmp_path, monkeypatch).get("/api/v1/fire")
        assert r.status_code == 200
        assert r.get_json() == {}

    def test_malformed_file_returns_empty(self, tmp_path, monkeypatch):
        (tmp_path / "fire").mkdir()
        (tmp_path / "fire" / "fire.json").write_text("{not json")
        assert _client(tmp_path, monkeypatch).get("/api/v1/fire").get_json() == {}


class TestSeismic:

    def test_returns_seismic_json(self, tmp_path, monkeypatch):
        import database
        from db_helpers import tmp_catchment
        with tmp_catchment(tmp_path):
            database.save_seismic_results(database.active_catchment(),
                {"metadata": {"model": "MKM-SEIS-001"},
                 "assets": [{"asset_id": "CPROP-1"}]})
            r = _client(tmp_path, monkeypatch).get("/api/v1/seismic")
            assert r.status_code == 200
            d = r.get_json()
        assert d["metadata"]["model"] == "MKM-SEIS-001"

    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        assert _client(tmp_path, monkeypatch).get("/api/v1/seismic").get_json() == {}
