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
Tests for PRS trade routes -- PDF generation (no cashflows, with cashflows,
close-out, close-out date, payable direction).
"""

import pytest


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
