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

"""Tests for routes.gauges.crud — list_gauges, get_gauge."""

import json

from .conftest import GAUGE_ID, GAUGE_DATA, make_client


class TestCrudListGauges:

    def test_list_gauges_returns_200(self, tmp_path, monkeypatch):
        """crud.py lines 40-50: successful gauge listing."""
        client = make_client(tmp_path, monkeypatch)
        r = client.get("/api/v1/gauges")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["count"] == 1
        assert len(data["gauges"]) == 1

    def test_list_gauges_options(self, tmp_path, monkeypatch):
        """crud.py lines 37-38: OPTIONS returns ok."""
        client = make_client(tmp_path, monkeypatch)
        r = client.options("/api/v1/gauges")
        assert r.status_code == 200

    def test_list_gauges_legacy_route(self, tmp_path, monkeypatch):
        """crud.py line 34: /list_gauges alias works."""
        client = make_client(tmp_path, monkeypatch)
        r = client.get("/api/v1/list_gauges")
        assert r.status_code == 200
        assert r.get_json()["count"] == 1

    def test_list_gauges_error_returns_500(self, tmp_path, monkeypatch):
        """crud.py lines 51-53: loader error -> 500."""
        from config import config
        (tmp_path / "gauge.json").write_text("NOT JSON")
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir(exist_ok=True)
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir(exist_ok=True)
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)
        monkeypatch.setattr(config, "get_input_path", lambda f: tmp_path / f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/gauges")
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"


class TestCrudGetGauge:

    def test_get_gauge_success(self, tmp_path, monkeypatch):
        """crud.py lines 59-72: valid gauge retrieval."""
        client = make_client(tmp_path, monkeypatch)
        r = client.get(f"/api/v1/gauges/{GAUGE_ID}")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert "gauge" in data

    def test_get_gauge_not_found(self, tmp_path, monkeypatch):
        """crud.py lines 63-67: gauge not found -> 404."""
        client = make_client(tmp_path, monkeypatch)
        r = client.get("/api/v1/gauges/GAUGE-NONEXISTENT")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"
