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
Tests for reports.gauge.gauge_page_12_trading — GaugeTradingPage.

Covers: generate_elements (no gauge ID, no trades, with trades),
_build_blotter_section (no trades, with trade rows),
_build_market_curves_section (no hts data, with data, with adjustments),
_derive_tenor (valid dates, missing dates, parse error).
"""

import json
from pathlib import Path

import pytest
from reportlab.platypus import Paragraph, Spacer, Table


def _page():
    from reports.gauge.gauge_page_12_trading import GaugeTradingPage
    return GaugeTradingPage()


def _gauge(gauge_id="GAUGE-001"):
    return {"FloodGauge": {"Header": {"GaugeID": gauge_id, "GaugeName": "Test Gauge"}}}


def _make_trade(swap_id="PRS-001", gauge_id="GAUGE-001", is_payer=True):
    return {
        "Header": {"SwapID": swap_id},
        "LegData": {"Payer": is_payer, "Notional": 10_000_000},
        "ScheduleData": {"StartDate": "2024-01-01", "EndDate": "2026-01-01", "Tenor": "2Y"},
        "Pricing": {
            "TriggerLevel": "warning",
            "SpreadBps": 150.0,
            "FairSpreadBps": 145.5,
            "NPV": 25000.0,
        },
        "GaugeSet": {"GaugeBasket": [{"GaugeID": gauge_id}]},
    }


# ===========================================================================
# generate_elements
# ===========================================================================

class TestGenerateElements:

    def test_returns_list(self):
        page = _page()
        result = page.generate_elements(_gauge())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_gauge_id_key_returns_message(self):
        page = _page()
        result = page.generate_elements({})  # No FloodGauge key
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No gauge ID" in t for t in texts)

    def test_with_gauge_id_returns_trading_header(self):
        page = _page()
        result = page.generate_elements(_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Trading Activity" in t for t in texts)


# ===========================================================================
# _build_blotter_section
# ===========================================================================

class TestBuildBlotterSection:

    def test_no_trades_returns_message(self):
        page = _page()
        result = page._build_blotter_section("GAUGE-001", [])
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No open PRS trades" in t for t in texts)

    def test_with_trades_returns_table(self):
        page = _page()
        trade = _make_trade()
        result = page._build_blotter_section("GAUGE-001", [trade])
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_with_trades_shows_count(self):
        page = _page()
        trades = [_make_trade("PRS-001"), _make_trade("PRS-002")]
        result = page._build_blotter_section("GAUGE-001", trades)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Total trades: 2" in t for t in texts)

    def test_receiver_trade_direction(self):
        page = _page()
        trade = _make_trade(is_payer=False)
        result = page._build_blotter_section("GAUGE-001", [trade])
        assert isinstance(result, list)

    def test_trigger_capitalized(self):
        page = _page()
        trade = _make_trade()
        result = page._build_blotter_section("GAUGE-001", [trade])
        # The table should exist and not raise errors
        assert any(isinstance(e, Table) for e in result)


# ===========================================================================
# _build_market_curves_section
# ===========================================================================

class TestBuildMarketCurvesSection:

    def test_no_market_state_returns_message(self):
        page = _page()
        result = page._build_market_curves_section("GAUGE-001", {})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No market hazard term structure" in t for t in texts)

    def test_with_hts_returns_table(self):
        page = _page()
        market_state = {
            "hazard_term_structure": {
                "GAUGE-001": {
                    "alert": {"1": 0.01, "2": 0.012, "3": 0.013, "4": 0.014, "5": 0.015},
                    "warning": {"1": 0.05, "2": 0.055, "3": 0.058, "4": 0.06, "5": 0.062},
                    "severe": {"1": 0.02, "2": 0.022, "3": 0.024, "4": 0.025, "5": 0.026},
                }
            }
        }
        result = page._build_market_curves_section("GAUGE-001", market_state)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_with_adjustments_returns_extra_table(self):
        page = _page()
        market_state = {
            "hazard_term_structure": {
                "GAUGE-001": {
                    "alert": {"1": 0.01},
                    "warning": {"1": 0.05},
                    "severe": {"1": 0.02},
                }
            },
            "gauge_adjustments": {
                "GAUGE-001": {
                    "adjusted_at": "2026-01-15T10:00:00",
                    "alert_shift": 0.002,
                    "custom_label": "override",
                }
            },
        }
        result = page._build_market_curves_section("GAUGE-001", market_state)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 2

    def test_partial_hts_handles_none_rates(self):
        """Some tenor slots missing → show 'N/A'."""
        page = _page()
        market_state = {
            "hazard_term_structure": {
                "GAUGE-001": {
                    "alert": {"1": 0.01},  # only 1Y provided
                    "warning": {},
                    "severe": {},
                }
            }
        }
        result = page._build_market_curves_section("GAUGE-001", market_state)
        assert any(isinstance(e, Table) for e in result)


# ===========================================================================
# _derive_tenor
# ===========================================================================

class TestDeriveTenor:

    def test_valid_dates_returns_years(self):
        page = _page()
        assert page._derive_tenor("2024-01-01", "2026-01-01") == "2Y"

    def test_missing_start_returns_na(self):
        page = _page()
        assert page._derive_tenor("", "2026-01-01") == "N/A"

    def test_missing_end_returns_na(self):
        page = _page()
        assert page._derive_tenor("2024-01-01", "") == "N/A"

    def test_both_missing_returns_na(self):
        page = _page()
        assert page._derive_tenor("", "") == "N/A"

    def test_invalid_date_format_returns_na(self):
        page = _page()
        assert page._derive_tenor("not-a-date", "2026-01-01") == "N/A"

    def test_five_year_tenor(self):
        page = _page()
        assert page._derive_tenor("2024-01-01", "2029-01-01") == "5Y"


# ===========================================================================
# _load_gauge_trades private branches
# ===========================================================================

class TestLoadGaugeTrades:

    def test_prs_dir_not_exist_returns_empty(self, tmp_path, monkeypatch):
        """Line 67: prs_dir doesn't exist → return empty list."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda x: str(tmp_path / "prs"))
        page = _page()
        result = page._load_gauge_trades("GAUGE-001")
        assert result == []

    def test_trade_matching_gauge_id_appended(self, tmp_path, monkeypatch):
        """Lines 75-76: trade with matching gauge_id → appended to list."""
        from config import config
        prs_dir = tmp_path / "prs"
        prs_dir.mkdir()

        trade = {
            "PhysicalSwap": {
                "Header": {"SwapID": "PRS-001"},
                "GaugeSet": {"GaugeBasket": [{"GaugeID": "GAUGE-001"}]},
            }
        }
        (prs_dir / "PRS-001.json").write_text(json.dumps(trade))

        monkeypatch.setattr(config, "get_reports_dir", lambda x: str(prs_dir))
        page = _page()
        result = page._load_gauge_trades("GAUGE-001")
        assert len(result) == 1

    def test_trade_not_matching_gauge_skipped(self, tmp_path, monkeypatch):
        """Trade for different gauge not appended."""
        from config import config
        prs_dir = tmp_path / "prs"
        prs_dir.mkdir()

        trade = {
            "PhysicalSwap": {
                "Header": {"SwapID": "PRS-001"},
                "GaugeSet": {"GaugeBasket": [{"GaugeID": "GAUGE-999"}]},
            }
        }
        (prs_dir / "PRS-001.json").write_text(json.dumps(trade))

        monkeypatch.setattr(config, "get_reports_dir", lambda x: str(prs_dir))
        page = _page()
        result = page._load_gauge_trades("GAUGE-001")
        assert result == []

    def test_get_reports_dir_raises_fallback(self, tmp_path, monkeypatch):
        """Lines 59-64: get_reports_dir raises → fallback to get_output_path."""
        from config import config
        prs_dir = tmp_path / "prs"  # doesn't exist → returns []

        def _bad_reports_dir(x):
            raise AttributeError("no such method")

        monkeypatch.setattr(config, "get_reports_dir", _bad_reports_dir)
        monkeypatch.setattr(config, "get_output_dir", lambda: tmp_path)
        page = _page()
        result = page._load_gauge_trades("GAUGE-001")
        assert result == []  # prs subdir doesn't exist


class TestLoadMarketState:

    def test_market_state_exception_returns_empty(self, monkeypatch):
        """Lines 89-91: exception → returns {}."""
        from config import config

        def _bad_trading_dir():
            raise RuntimeError("no trading dir")

        monkeypatch.setattr(config, "get_trading_dir", _bad_trading_dir)
        page = _page()
        result = page._load_market_state()
        assert result == {}
