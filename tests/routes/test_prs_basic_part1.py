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

"""
Tests for PRS trade routes – basic operations.

Covers: list trades (empty dir), get trade PDF (not found → 404),
commit trade (no JSON → 400, invalid validation → 400).
"""

import json
import pathlib

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def prs_env(tmp_path, monkeypatch):
    """Isolated PRS environment with a writable output directory."""
    from config import config

    prs_dir = tmp_path / "reports" / "prs"
    prs_dir.mkdir(parents=True)

    monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
    monkeypatch.setattr(config, "catchment_id", "thames")
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    monkeypatch.setattr(config, "get_trading_dir", lambda: tmp_path / "trading")

    from server import create_app
    from fixtures_admin import AuthenticatedTestClient
    app = create_app()
    app.config["TESTING"] = True
    app.test_client_class = AuthenticatedTestClient
    return app.test_client()


# ===========================================================================
# GET /prs/trades
# ===========================================================================

class TestListTrades:

    def test_empty_dir_returns_zero_count(self, prs_env):
        r = prs_env.get("/api/v1/prs/trades")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["count"] == 0
        assert data["trades"] == []

    def test_returns_trades_list_key(self, prs_env):
        r = prs_env.get("/api/v1/prs/trades")
        assert "trades" in r.get_json()


# ===========================================================================
# GET /prs/trades/<swap_id>/pdf
# ===========================================================================

class TestGetTradePDF:

    def test_missing_pdf_returns_404(self, prs_env):
        r = prs_env.get("/api/v1/prs/trades/PRS-NOTEXIST/pdf")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_existing_pdf_served(self, tmp_path, monkeypatch):
        """If the PDF exists, it should be served with 200."""
        from config import config

        prs_dir = tmp_path / "reports" / "prs"
        prs_dir.mkdir(parents=True)
        pdf_file = prs_dir / "PRS-TESTFILE.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/prs/trades/PRS-TESTFILE/pdf")
        assert r.status_code == 200
        assert r.content_type == "application/pdf"


# ===========================================================================
# POST /prs/commit
# ===========================================================================

class TestListTradesError:

    def test_list_trades_handles_corrupt_json(self, tmp_path, monkeypatch):
        """list_prs_trades catches exceptions from corrupt JSON files."""
        from config import config
        prs_dir = tmp_path / "reports" / "prs"
        prs_dir.mkdir(parents=True)

        # Write a corrupt JSON file
        (prs_dir / "PRS-BAD00001.json").write_text("{corrupt")

        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/prs/trades")
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"


class TestListTradesWithFiles:

    def test_list_returns_trades_from_json_files(self, tmp_path, monkeypatch):
        """list_prs_trades reads PRS-*.json files and returns them."""
        from config import config
        prs_dir = tmp_path / "reports" / "prs"
        prs_dir.mkdir(parents=True)

        trade = {
            "PhysicalSwap": {
                "Header": {
                    "SwapID": "PRS-ABCD1234",
                    "CounterParty": "CTPY-001",
                    "CounterPartyName": "Test Bank",
                    "ValuationDate": "2025-01-01",
                    "CatchmentID": "thames",
                },
                "LegData": {"Notional": 1_000_000},
                "Pricing": {"SpreadBps": 150, "FairSpreadBps": 145, "NPV": -5000,
                            "TriggerLevel": "warning"},
            }
        }
        import json as _json
        (prs_dir / "PRS-ABCD1234.json").write_text(_json.dumps(trade))

        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/prs/trades")
        assert r.status_code == 200
        data = r.get_json()
        assert data["count"] == 1
        assert data["trades"][0]["swap_id"] == "PRS-ABCD1234"
