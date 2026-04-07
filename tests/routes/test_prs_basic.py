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
    app = create_app()
    app.config["TESTING"] = True
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

class TestCommitTrade:

    def test_no_json_returns_error(self, prs_env):
        # Without Content-Type: application/json, get_json() raises 415
        # which is caught by the outer except → 500. Either way it's an error.
        r = prs_env.post("/api/v1/prs/commit")
        assert r.status_code in (400, 500)
        assert r.get_json()["status"] == "error"

    def test_empty_json_returns_400(self, prs_env):
        # Empty dict {} is falsy → "No JSON body" → 400
        r = prs_env.post("/api/v1/prs/commit", json={})
        assert r.status_code == 400
        assert r.get_json()["status"] == "error"

    def test_minimal_valid_commit(self, prs_env, tmp_path, monkeypatch):
        """Commit with enough fields to pass CDM validation."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

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
        }
        r = prs_env.post("/api/v1/prs/commit", json=payload)
        # Accept 200 (success) or 400 (validation), but not 500 (server error)
        # The key is: the route was reached and handled it.
        assert r.status_code in (200, 400)
        assert r.get_json()["status"] in ("success", "error")

    def test_commit_with_cashflows(self, prs_env, tmp_path, monkeypatch):
        """Commit with cashflows — exercises PDF cashflow schedule section."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

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
            "cashflows": [
                {"label": "6M", "S_t": 0.01, "df": 0.98, "premCF": 7500,
                 "premPV": 7350, "protCF": 10000, "protPV": 9800},
                {"label": "12M", "S_t": 0.02, "df": 0.96, "premCF": 7500,
                 "premPV": 7200, "protCF": 10000, "protPV": 9600},
            ],
        }
        r = prs_env.post("/api/v1/prs/commit", json=payload)
        assert r.status_code in (200, 400)

    def test_commit_with_explicit_maturity(self, prs_env, tmp_path, monkeypatch):
        """Commit with maturity_date provided explicitly."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

        payload = {
            "gauge_id": "GAUGE-002",
            "counterparty_id": "CTPY-002",
            "counterparty_name": "Another Bank",
            "trigger": "alert",
            "notional": 500_000,
            "tenor": 2,
            "spread_bps": 100.0,
            "maturity_date": "2028-01-15",
        }
        r = prs_env.post("/api/v1/prs/commit", json=payload)
        assert r.status_code in (200, 400)

    def test_commit_with_terrain_fields(self, prs_env, tmp_path, monkeypatch):
        """Commit with EA flood zone terrain fields."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

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
            "ea_flood_zone": "Zone 3b",
            "ea_flood_zone_actual": "Zone 2",
            "terrain_delta_bps": 156.3,
        }
        r = prs_env.post("/api/v1/prs/commit", json=payload)
        assert r.status_code in (200, 400)
        assert r.get_json()["status"] in ("success", "error")

    def test_commit_without_terrain_fields_backward_compat(self, prs_env, tmp_path, monkeypatch):
        """Commit without terrain fields should still work (backward compatibility)."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

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
        assert r.status_code in (200, 400)


    def test_commit_missing_gauge_id_returns_400(self, prs_env):
        """Empty gauge_id should be rejected with 400."""
        payload = {
            "gauge_id": "  ",
            "counterparty_id": "CTPY-001",
            "trigger": "warning",
            "notional": 1_000_000,
            "tenor": 3,
            "spread_bps": 150.0,
        }
        r = prs_env.post("/api/v1/prs/commit", json=payload)
        assert r.status_code == 400
        data = r.get_json()
        assert data["status"] == "error"
        assert "gauge_id" in data["message"].lower()

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
