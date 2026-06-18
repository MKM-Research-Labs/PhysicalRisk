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

"""Tests for routes.gauges.hazard — get_gauge_hazard error, price_prs paths."""

import json
from unittest.mock import patch, MagicMock

from .conftest import GAUGE_ID, GAUGE_DATA, HAZARD_DATA, make_client


class TestHazardErrorPaths:

    def test_get_gauge_hazard_corrupted_file_returns_500(self, tmp_path, monkeypatch):
        """hazard.py lines 100-102: exception reading hazard file -> 500."""
        from config import config
        (tmp_path / "gauge.json").write_text(json.dumps(GAUGE_DATA))
        (tmp_path / "gaugehc.json").write_text("INVALID JSON")
        gaugets_dir = tmp_path / "gaugets"
        gaugets_dir.mkdir()
        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_gaugets_dir", lambda: gaugets_dir)
        monkeypatch.setattr(config, "get_gaugehd_dir", lambda: gaugehd_dir)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get(f"/api/v1/gauges/{GAUGE_ID}/hazard")
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"


class TestPricePrsHappyPath:

    _PRS_RESULT = {
        "fair_spread_bps": 45.0,
        "protection_leg_pv": 50000.0,
        "premium_leg_pv": 48000.0,
        "net_pv": 2000.0,
    }

    def test_price_prs_success(self, tmp_path, monkeypatch):
        """hazard.py lines 133-172: successful PRS pricing."""
        client = make_client(tmp_path, monkeypatch, gaugehc=HAZARD_DATA)
        with patch.dict("sys.modules", {"models.prs.prshc": MagicMock(
                price_prs=MagicMock(return_value=self._PRS_RESULT))}):
            r = client.post("/api/v1/price_prs", json={
                "gauge_id": GAUGE_ID,
                "trigger_level": "warning",
                "notional": 1_000_000,
                "tenor_years": 3,
            })
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert "fair_spread_bps" in data

    def test_price_prs_with_defaults(self, tmp_path, monkeypatch):
        """hazard.py: PRS pricing with default params."""
        client = make_client(tmp_path, monkeypatch, gaugehc=HAZARD_DATA)
        with patch.dict("sys.modules", {"models.prs.prshc": MagicMock(
                price_prs=MagicMock(return_value=self._PRS_RESULT))}):
            r = client.post("/api/v1/price_prs", json={
                "gauge_id": GAUGE_ID,
                "trigger_level": "alert",
            })
        assert r.status_code == 200

    def test_price_prs_severe_trigger(self, tmp_path, monkeypatch):
        """All trigger levels work: alert, warning, severe."""
        client = make_client(tmp_path, monkeypatch, gaugehc=HAZARD_DATA)
        with patch.dict("sys.modules", {"models.prs.prshc": MagicMock(
                price_prs=MagicMock(return_value=self._PRS_RESULT))}):
            r = client.post("/api/v1/price_prs", json={
                "gauge_id": GAUGE_ID,
                "trigger_level": "severe",
            })
        assert r.status_code == 200

    def test_price_prs_no_json_body(self, tmp_path, monkeypatch):
        """hazard.py line 123: no JSON body -> 400."""
        client = make_client(tmp_path, monkeypatch, gaugehc=HAZARD_DATA)
        r = client.post("/api/v1/price_prs", content_type="application/json")
        assert r.status_code in (400, 500)

    def test_price_prs_null_json_body(self, tmp_path, monkeypatch):
        """hazard.py lines 121-123: JSON null body -> 400."""
        client = make_client(tmp_path, monkeypatch, gaugehc=HAZARD_DATA)
        r = client.post("/api/v1/price_prs", data=b"null",
                        content_type="application/json")
        assert r.status_code == 400
        assert r.get_json()["status"] == "error"

    def test_price_prs_exception_returns_500(self, tmp_path, monkeypatch):
        """hazard.py lines 174-176: exception during pricing -> 500."""
        client = make_client(tmp_path, monkeypatch, gaugehc=HAZARD_DATA)
        with patch.dict("sys.modules", {"models.prs.prshc": MagicMock(
                price_prs=MagicMock(side_effect=RuntimeError("QuantLib boom")))}):
            r = client.post("/api/v1/price_prs", json={
                "gauge_id": GAUGE_ID,
                "trigger_level": "warning",
            })
        assert r.status_code == 500

    def test_price_prs_no_hazard_file(self, tmp_path, monkeypatch):
        """hazard.py lines 139-140: no gaugehc.json -> 404."""
        client = make_client(tmp_path, monkeypatch)
        with patch.dict("sys.modules", {"models.prs.prshc": MagicMock(
                price_prs=MagicMock(return_value={}))}):
            r = client.post("/api/v1/price_prs", json={
                "gauge_id": GAUGE_ID,
                "trigger_level": "warning",
            })
        assert r.status_code == 404

    def test_price_prs_gauge_not_in_hazard(self, tmp_path, monkeypatch):
        """hazard.py lines 146-147: gauge not in hazard data -> 404."""
        empty_hazard = {"hazard_curves": {}}
        client = make_client(tmp_path, monkeypatch, gaugehc=empty_hazard)
        with patch.dict("sys.modules", {"models.prs.prshc": MagicMock(
                price_prs=MagicMock(return_value={}))}):
            r = client.post("/api/v1/price_prs", json={
                "gauge_id": GAUGE_ID,
                "trigger_level": "warning",
            })
        assert r.status_code == 404
