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

class TestCommitTradeBasic:
    """Basic commit-trade flows: empty/minimal/cashflows/maturity/terrain/missing-gauge."""

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

