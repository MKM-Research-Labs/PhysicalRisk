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

    def test_malformed_file_returns_empty(self, tmp_path, monkeypatch):
        """The seismic twin of the fire case above.

        Fire had this covered and seismic did not, so a corrupt seismic model
        file would have propagated a JSONDecodeError as a 500 instead of the
        documented empty payload — and the commercial PRS panel reads this
        endpoint on open, so the whole panel would have failed rather than
        showing no seismic component.
        """
        (tmp_path / "seismic").mkdir()
        (tmp_path / "seismic" / "seismic.json").write_text("{not json")
        r = _client(tmp_path, monkeypatch).get("/api/v1/seismic")
        assert r.status_code == 200
        assert r.get_json() == {}

    def test_an_unreadable_file_returns_empty(self, tmp_path, monkeypatch):
        """A directory where the file should be raises OSError, not a decode
        error — the handler catches both for the same reason."""
        (tmp_path / "seismic" / "seismic.json").mkdir(parents=True)
        r = _client(tmp_path, monkeypatch).get("/api/v1/seismic")
        assert r.status_code == 200
        assert r.get_json() == {}
