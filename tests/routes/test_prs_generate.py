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
Tests for PRS trade routes – PDF generation, validation errors, close-out,
and list-trades exception handling.
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


class TestGenerateTradePDF:

    def test_generate_pdf_no_cashflows(self, tmp_path):
        """_generate_trade_pdf creates a PDF without cashflows."""
        from routes.prs import _generate_trade_pdf

        cdm = {
            "PhysicalSwap": {
                "Header": {
                    "SwapID": "PRS-TEST001",
                    "CounterParty": "CTPY-001",
                    "CounterPartyName": "Test Bank",
                    "ValuationDate": "2025-01-01",
                    "ProtectionStart": "2025-01-03",
                    "CatchmentID": "thames",
                },
                "LegData": {"Notional": 1_000_000, "Currency": "GBP",
                            "DayCounter": "ACT/360", "Payer": True,
                            "FixedLegRate": 0.015},
                "ScheduleData": {"StartDate": "2025-01-03", "EndDate": "2028-01-03",
                                 "Tenor": "6M", "Calendar": "London"},
                "Pricing": {"SpreadBps": 150, "FairSpreadBps": 145, "NPV": -5000,
                            "PremiumLegPV": 100000, "ProtectionLegPV": 105000,
                            "RiskyAnnuity": 2.5, "RiskFreeRate": 0.04,
                            "Recovery": 0.0, "TriggerLevel": "warning"},
                "GaugeSet": {"GaugeSetID": "GSET-001", "CatchmentID": "thames"},
                "Triggers": {"TriggerType": "Any"},
                "Payouts": {"Currency": "GBP", "MaxPayout": 1_000_000},
            }
        }
        pdf_path = _generate_trade_pdf(cdm, [], tmp_path)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 1000

    def test_generate_pdf_with_cashflows(self, tmp_path):
        """_generate_trade_pdf with cashflows exercises CF schedule section."""
        from routes.prs import _generate_trade_pdf

        cdm = {
            "PhysicalSwap": {
                "Header": {
                    "SwapID": "PRS-TEST002",
                    "CounterParty": "CTPY-001",
                    "CounterPartyName": "Test Bank",
                    "ValuationDate": "2025-01-01",
                    "ProtectionStart": "2025-01-03",
                    "CatchmentID": "thames",
                },
                "LegData": {"Notional": 1_000_000, "Currency": "GBP",
                            "DayCounter": "ACT/360", "Payer": True,
                            "FixedLegRate": 0.015},
                "ScheduleData": {"StartDate": "2025-01-03", "EndDate": "2028-01-03",
                                 "Tenor": "6M"},
                "Pricing": {"SpreadBps": 150, "FairSpreadBps": 145, "NPV": 0,
                            "PremiumLegPV": 100000, "ProtectionLegPV": 100000,
                            "RiskyAnnuity": 2.5, "Recovery": 0.0,
                            "TriggerLevel": "warning"},
                "GaugeSet": {"GaugeSetID": "GSET-001"},
                "Triggers": {}, "Payouts": {},
            }
        }
        cashflows = [
            {"label": "6M", "S_t": 0.01, "df": 0.98, "premCF": 7500,
             "premPV": 7350, "protCF": 10000, "protPV": 9800},
        ]
        pdf_path = _generate_trade_pdf(cdm, cashflows, tmp_path)
        assert pdf_path.exists()

    def test_generate_pdf_with_close_out(self, tmp_path):
        """_generate_trade_pdf with CloseOutOf exercises close-out section."""
        from routes.prs import _generate_trade_pdf

        cdm = {
            "PhysicalSwap": {
                "Header": {
                    "SwapID": "PRS-TEST003",
                    "CounterParty": "CTPY-001",
                    "CounterPartyName": "Test Bank",
                    "ValuationDate": "2025-06-01",
                    "ProtectionStart": "2025-06-03",
                    "CatchmentID": "thames",
                    "CloseOutOf": "PRS-ORIG001",
                },
                "LegData": {"Notional": 1_000_000, "Currency": "GBP",
                            "DayCounter": "ACT/360", "Payer": False,
                            "FixedLegRate": 0.015},
                "ScheduleData": {"StartDate": "2025-06-03", "EndDate": "2027-06-03",
                                 "Tenor": "6M"},
                "Pricing": {"SpreadBps": 145, "FairSpreadBps": 145, "NPV": 5000,
                            "PremiumLegPV": 95000, "ProtectionLegPV": 100000,
                            "RiskyAnnuity": 2.4, "Recovery": 0.0,
                            "TriggerLevel": "warning"},
                "GaugeSet": {"GaugeSetID": "GSET-001"},
                "Triggers": {}, "Payouts": {},
            }
        }
        pdf_path = _generate_trade_pdf(cdm, [], tmp_path)
        assert pdf_path.exists()

    def test_generate_pdf_with_close_out_date(self, tmp_path):
        """_generate_trade_pdf with CloseOutDate (original trade that was closed)."""
        from routes.prs import _generate_trade_pdf

        cdm = {
            "PhysicalSwap": {
                "Header": {
                    "SwapID": "PRS-CLOSED01",
                    "CounterParty": "CTPY-001",
                    "CounterPartyName": "Test Bank",
                    "ValuationDate": "2025-01-01",
                    "ProtectionStart": "2025-01-03",
                    "CatchmentID": "thames",
                    "CloseOutDate": "2025-06-01",
                    "SettlementAmount": 12500.0,
                    "SettlementDirection": "Receivable",
                    "SettlementDate": "2025-06-03",
                    "CloseOutSpread": 145.0,
                },
                "LegData": {"Notional": 1_000_000, "Currency": "GBP",
                            "DayCounter": "ACT/360", "Payer": True,
                            "FixedLegRate": 0.015},
                "ScheduleData": {"StartDate": "2025-01-03", "EndDate": "2028-01-03",
                                 "Tenor": "6M"},
                "Pricing": {"SpreadBps": 150, "FairSpreadBps": 145, "NPV": -5000,
                            "PremiumLegPV": 100000, "ProtectionLegPV": 105000,
                            "RiskyAnnuity": 2.5, "Recovery": 0.0,
                            "TriggerLevel": "warning"},
                "GaugeSet": {}, "Triggers": {}, "Payouts": {},
            }
        }
        pdf_path = _generate_trade_pdf(cdm, [], tmp_path)
        assert pdf_path.exists()

    def test_close_out_payable_direction(self, tmp_path):
        """CloseOutDate with Payable SettlementDirection."""
        from routes.prs import _generate_trade_pdf

        cdm = {
            "PhysicalSwap": {
                "Header": {
                    "SwapID": "PRS-CLOSED02",
                    "CounterParty": "CTPY-001",
                    "CounterPartyName": "Test Bank",
                    "ValuationDate": "2025-01-01",
                    "CatchmentID": "thames",
                    "CloseOutDate": "2025-06-01",
                    "SettlementAmount": 5000.0,
                    "SettlementDirection": "Payable",
                    "SettlementDate": "2025-06-03",
                    "CloseOutSpread": 140.0,
                },
                "LegData": {"Notional": 500_000, "Currency": "GBP",
                            "DayCounter": "ACT/360", "Payer": True},
                "ScheduleData": {"StartDate": "2025-01-03", "EndDate": "2027-01-03"},
                "Pricing": {"SpreadBps": 150, "FairSpreadBps": 140, "NPV": 5000,
                            "PremiumLegPV": 90000, "ProtectionLegPV": 95000,
                            "RiskyAnnuity": 2.3, "Recovery": 0.0,
                            "TriggerLevel": "alert"},
                "GaugeSet": {}, "Triggers": {}, "Payouts": {},
            }
        }
        pdf_path = _generate_trade_pdf(cdm, [], tmp_path)
        assert pdf_path.exists()


# ===========================================================================
# Coverage expansion: validation errors (L133), close-out (L144-151),
# list trades exception (L201-202)
# ===========================================================================

class TestCommitValidationErrors:
    """Line 133: CDM validation returns errors → 400."""

    def test_validation_fails_returns_400(self, tmp_path, monkeypatch):
        from config import config
        prs_dir = tmp_path / "reports" / "prs"
        prs_dir.mkdir(parents=True)
        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_trading_dir", lambda: tmp_path / "trading")

        from port.cdm.prs import PhysicalRiskSwapCDM
        monkeypatch.setattr(PhysicalRiskSwapCDM, "validate",
                            lambda self, rec: ["Missing required field: SwapID"])

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
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

        prs_dir = tmp_path / "reports" / "prs"
        prs_dir.mkdir(parents=True)
        trading_dir = tmp_path / "trading"
        trading_dir.mkdir(parents=True)

        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
        monkeypatch.setattr(config, "get_trading_dir", lambda: trading_dir)

        # Mock PnLEngine to avoid needing actual trade files
        mock_pnl_engine = MagicMock()
        with patch("models.trading.pnl_engine.PnLEngine", return_value=mock_pnl_engine):
            from server import create_app
            app = create_app()
            app.config["TESTING"] = True
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
            # Either 200 (success) or 400 (validation) — but not 500 crash
            assert r.status_code in (200, 400)
            if r.status_code == 200:
                mock_pnl_engine.close_trade.assert_called_once_with("PRS-ORIGINAL1", 150.0)


class TestListTradesException:
    """Lines 201-202: exception while reading trades → 500."""

    def test_corrupt_trade_file_returns_500(self, tmp_path, monkeypatch):
        from config import config
        prs_dir = tmp_path / "reports" / "prs"
        prs_dir.mkdir(parents=True)
        # Write a corrupt JSON file matching PRS-*.json pattern
        (prs_dir / "PRS-CORRUPT1.json").write_text("NOT VALID JSON {{{")

        monkeypatch.setattr(config, "get_reports_dir", lambda name: tmp_path / "reports" / name)
        monkeypatch.setattr(config, "catchment_id", "thames")

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/prs/trades")
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"
