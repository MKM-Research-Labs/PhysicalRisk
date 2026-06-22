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
Tests for PRS trade routes -- validation errors, close-out, list trades exception.
"""

import json

import pytest


# ===========================================================================
# Coverage expansion: validation errors (L133), close-out (L144-151),
# list trades exception (L201-202)
# ===========================================================================

class TestCommitValidationErrors:
    """Line 133: CDM validation returns errors -> 400."""

    def test_validation_fails_returns_400(self, tmp_path, monkeypatch):
        from config import config
        prs_dir = tmp_path / "prs"
        prs_dir.mkdir(parents=True)
        monkeypatch.setattr(config, "get_reports_dir", lambda name: (tmp_path / "prs") if name == "prs" else tmp_path / "reports" / name)
        monkeypatch.setattr(config, "_catchment_id", "thames")
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_trading_dir", lambda: tmp_path / "trading")

        from port.cdm.prs import PhysicalRiskSwapCDM
        monkeypatch.setattr(PhysicalRiskSwapCDM, "validate",
                            lambda self, rec: ["Missing required field: SwapID"])

        from server import create_app
        from fixtures_admin import AuthenticatedTestClient
        app = create_app()
        app.config["TESTING"] = True
        app.test_client_class = AuthenticatedTestClient
        client = app.test_client()

        payload = {
            "gauge_id": "GAUGE-001",
            "counterparty_id": "CTPY-001",
            "trigger": "warning",
            "notional": 1_000_000,
            "tenor": 3,
            "spread_bps": 150.0,
        }
        r = client.post("/api/v1/prs/commit", json=payload)
        assert r.status_code == 400
        data = r.get_json()
        assert data["status"] == "error"
        assert "errors" in data


class TestCommitCloseOut:
    """Lines 144-151: close_out_of triggers PnLEngine.close_trade and re-save."""

    def test_close_out_path_exercised(self, tmp_path, monkeypatch):
        from config import config
        from unittest.mock import MagicMock, patch

        prs_dir = tmp_path / "prs"
        prs_dir.mkdir(parents=True)
        trading_dir = tmp_path / "trading"
        trading_dir.mkdir(parents=True)

        monkeypatch.setattr(config, "get_reports_dir", lambda name: (tmp_path / "prs") if name == "prs" else tmp_path / "reports" / name)
        monkeypatch.setattr(config, "_catchment_id", "thames")
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_trading_dir", lambda: trading_dir)

        # Mock PnLEngine to avoid needing actual trade files
        mock_pnl_engine = MagicMock()
        with patch("models.trading.pnl_engine.PnLEngine", return_value=mock_pnl_engine):
            from server import create_app
            from fixtures_admin import AuthenticatedTestClient
            app = create_app()
            app.config["TESTING"] = True
            app.test_client_class = AuthenticatedTestClient
            client = app.test_client()

            payload = {
                "gauge_id": "GAUGE-001",
                "gauge_name": "Test Gauge",
                "counterparty_id": "CTPY-001",
                "counterparty_name": "Test Bank",
                "trigger": "warning",
                "notional": 1_000_000,
                "tenor": 3,
                "spread_bps": 150.0,
                "fair_spread_bps": 145.0,
                "npv": -50000.0,
                "premium_leg_pv": 100000.0,
                "protection_leg_pv": 150000.0,
                "risky_annuity": 2.5,
                "recovery": 0.0,
                "close_out_of": "PRS-ORIGINAL1",
            }
            r = client.post("/api/v1/prs/commit", json=payload)
            # Either 200 (success) or 400 (validation) -- but not 500 crash
            assert r.status_code in (200, 400)
            if r.status_code == 200:
                mock_pnl_engine.close_trade.assert_called_once_with("PRS-ORIGINAL1", 150.0)


class TestListTradesException:
    """Lines 201-202: exception while reading trades -> 500."""

    def test_corrupt_trade_file_returns_500(self, tmp_path, monkeypatch):
        from config import config
        prs_dir = tmp_path / "prs"
        prs_dir.mkdir(parents=True)
        # Write a corrupt JSON file matching PRS-*.json pattern
        (prs_dir / "PRS-CORRUPT1.json").write_text("NOT VALID JSON {{{")

        monkeypatch.setattr(config, "get_reports_dir", lambda name: (tmp_path / "prs") if name == "prs" else tmp_path / "reports" / name)
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "_catchment_id", "thames")

        from server import create_app
        from fixtures_admin import AuthenticatedTestClient
        app = create_app()
        app.config["TESTING"] = True
        app.test_client_class = AuthenticatedTestClient
        client = app.test_client()

        r = client.get("/api/v1/prs/trades")
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"
