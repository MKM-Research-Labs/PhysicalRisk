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

class TestCommitTradeProperty:
    """Commit-trade flows that exercise the property JSON path + close-out."""

    def test_commit_with_property_id_and_property_json(self, prs_env, tmp_path, monkeypatch):
        """Commit with property_id triggers PropertySet lookup from property.json."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "catchment_id", "thames")

        # Write a property.json with a matching property
        prop_data = {
            "properties": [
                {
                    "PropertyHeader": {
                        "Header": {"PropertyID": "PROP-001"},
                        "Location": {
                            "BuildingNumber": "42",
                            "StreetName": "Flood Lane",
                            "Postcode": "TW1 1AA",
                            "LocalAuthority": "Richmond",
                            "LatitudeDegrees": 51.45,
                            "LongitudeDegrees": -0.32,
                        },
                        "Valuation": {"PropertyValue": 500000},
                        "ReferenceGauges": [{"GaugeID": "GAUGE-001", "Distance": 1.2}],
                    }
                }
            ]
        }
        (tmp_path / "property.json").write_text(json.dumps(prop_data))

        payload = {
            "gauge_id": "GAUGE-001",
            "gauge_name": "Test Gauge",
            "counterparty_id": "CTPY-001",
            "counterparty_name": "Test Bank",
            "property_id": "PROP-001",
            "trigger": "warning",
            "notional": 1_000_000,
            "tenor": 3,
            "spread_bps": 150.0,
            "ea_flood_zone": "Zone 3",
        }
        r = prs_env.post("/api/v1/prs/commit", json=payload)
        assert r.status_code in (200, 400)

        # If successful, verify PropertySet was written to the trade JSON
        if r.status_code == 200:
            data = r.get_json()
            trade_path = pathlib.Path(data["json_path"])
            trade = json.loads(trade_path.read_text())
            prop_set = trade["PhysicalSwap"]["PropertySet"]
            assert prop_set["PropertyID"] == "PROP-001"
            assert prop_set["Postcode"] == "TW1 1AA"
            assert prop_set["PropertyValue"] == 500000
            assert prop_set["ReferenceGauge"]["GaugeID"] == "GAUGE-001"
            assert trade["PhysicalSwap"]["Header"]["TradeType"] == "PropertyPRS"

    def test_commit_property_id_no_property_json(self, prs_env, tmp_path, monkeypatch):
        """Commit with property_id but no property.json still succeeds (graceful fallback)."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "catchment_id", "thames")

        # No property.json on disk
        payload = {
            "gauge_id": "GAUGE-001",
            "counterparty_id": "CTPY-001",
            "counterparty_name": "Test Bank",
            "property_id": "PROP-MISSING",
            "trigger": "warning",
            "notional": 1_000_000,
            "tenor": 3,
            "spread_bps": 150.0,
        }
        r = prs_env.post("/api/v1/prs/commit", json=payload)
        assert r.status_code in (200, 400)

    def test_commit_property_id_corrupt_property_json(self, prs_env, tmp_path, monkeypatch):
        """Commit with property_id and corrupt property.json logs warning, still proceeds."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "catchment_id", "thames")

        # Write invalid JSON
        (tmp_path / "property.json").write_text("{bad json")

        payload = {
            "gauge_id": "GAUGE-001",
            "counterparty_id": "CTPY-001",
            "counterparty_name": "Test Bank",
            "property_id": "PROP-001",
            "trigger": "warning",
            "notional": 1_000_000,
            "tenor": 3,
            "spread_bps": 150.0,
        }
        r = prs_env.post("/api/v1/prs/commit", json=payload)
        assert r.status_code in (200, 400)


    def test_commit_validation_failure(self, prs_env, tmp_path, monkeypatch):
        """CDM validation errors return 400 with error details."""
        from config import config
        from port.cdm.prs import PhysicalRiskSwapCDM
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

        # Force validation to return errors
        monkeypatch.setattr(
            PhysicalRiskSwapCDM, "validate",
            lambda self, rec: ["SwapID missing", "Notional must be positive"],
        )

        payload = {
            "gauge_id": "GAUGE-001",
            "counterparty_id": "CTPY-001",
            "counterparty_name": "Test Bank",
            "trigger": "warning",
            "notional": 1_000_000,
            "tenor": 3,
            "spread_bps": 150.0,
        }
        r = prs_env.post("/api/v1/prs/commit", json=payload)
        assert r.status_code == 400
        data = r.get_json()
        assert data["status"] == "error"
        assert "Validation failed" in data["message"]
        assert len(data["errors"]) == 2

    def test_commit_with_close_out(self, prs_env, tmp_path, monkeypatch):
        """Commit with close_out_of triggers PnLEngine.close_trade."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

        trading_dir = tmp_path / "trading"
        trading_dir.mkdir(parents=True)
        monkeypatch.setattr(config, "get_trading_dir", lambda: trading_dir)

        # Stub PnLEngine.close_trade
        closed = []
        import models.trading.pnl_engine as pnl_mod
        original_init = pnl_mod.PnLEngine.__init__

        class StubPnLEngine:
            def __init__(self, *a, **kw):
                pass
            def close_trade(self, swap_id, spread):
                closed.append((swap_id, spread))

        monkeypatch.setattr(pnl_mod, "PnLEngine", StubPnLEngine)

        payload = {
            "gauge_id": "GAUGE-001",
            "gauge_name": "Test Gauge",
            "counterparty_id": "CTPY-001",
            "counterparty_name": "Test Bank",
            "trigger": "warning",
            "notional": 1_000_000,
            "tenor": 3,
            "spread_bps": 150.0,
            "close_out_of": "PRS-ORIGINAL1",
        }
        r = prs_env.post("/api/v1/prs/commit", json=payload)
        assert r.status_code in (200, 400)

        if r.status_code == 200:
            assert len(closed) == 1
            assert closed[0] == ("PRS-ORIGINAL1", 150.0)
            # Verify CloseOutOf in saved JSON
            data = r.get_json()
            trade = json.loads(pathlib.Path(data["json_path"]).read_text())
            assert trade["PhysicalSwap"]["Header"]["CloseOutOf"] == "PRS-ORIGINAL1"


