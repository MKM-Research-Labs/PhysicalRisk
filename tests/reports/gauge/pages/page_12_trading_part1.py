# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for GaugeTradingPage — part 1.

generate_elements, _build_blotter_section, _build_market_curves_section, _derive_tenor.
"""

import json

import pytest
from reportlab.platypus import Paragraph, Spacer, Table

from .conftest import make_page, make_gauge, make_trade


# ===========================================================================
# generate_elements
# ===========================================================================

class TestGenerateElements:

    def test_returns_list(self):
        page = make_page()
        result = page.generate_elements(make_gauge())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_gauge_id_key_returns_message(self):
        page = make_page()
        result = page.generate_elements({})  # No FloodGauge key
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No gauge ID" in t for t in texts)

    def test_with_gauge_id_returns_trading_header(self):
        page = make_page()
        result = page.generate_elements(make_gauge())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Trading Activity" in t for t in texts)


# ===========================================================================
# _build_blotter_section
# ===========================================================================

class TestBuildBlotterSection:

    def test_no_trades_returns_message(self):
        page = make_page()
        result = page._build_blotter_section("GAUGE-001", [])
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No open PRS trades" in t for t in texts)

    def test_with_trades_returns_table(self):
        page = make_page()
        trade = make_trade()
        result = page._build_blotter_section("GAUGE-001", [trade])
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 1

    def test_with_trades_shows_count(self):
        page = make_page()
        trades = [make_trade("PRS-001"), make_trade("PRS-002")]
        result = page._build_blotter_section("GAUGE-001", trades)
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("Total trades: 2" in t for t in texts)

    def test_receiver_trade_direction(self):
        page = make_page()
        trade = make_trade(is_payer=False)
        result = page._build_blotter_section("GAUGE-001", [trade])
        assert isinstance(result, list)

    def test_trigger_capitalized(self):
        page = make_page()
        trade = make_trade()
        result = page._build_blotter_section("GAUGE-001", [trade])
        # The table should exist and not raise errors
        assert any(isinstance(e, Table) for e in result)


# ===========================================================================
# _build_market_curves_section
# ===========================================================================

class TestBuildMarketCurvesSection:

    def test_no_market_state_returns_message(self):
        page = make_page()
        result = page._build_market_curves_section("GAUGE-001", {})
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, "text")]
        assert any("No market hazard term structure" in t for t in texts)

    def test_with_hts_returns_table(self):
        page = make_page()
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
        page = make_page()
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
        """Some tenor slots missing -> show 'N/A'."""
        page = make_page()
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
        page = make_page()
        assert page._derive_tenor("2024-01-01", "2026-01-01") == "2Y"

    def test_missing_start_returns_na(self):
        page = make_page()
        assert page._derive_tenor("", "2026-01-01") == "N/A"

    def test_missing_end_returns_na(self):
        page = make_page()
        assert page._derive_tenor("2024-01-01", "") == "N/A"

    def test_both_missing_returns_na(self):
        page = make_page()
        assert page._derive_tenor("", "") == "N/A"

    def test_invalid_date_format_returns_na(self):
        page = make_page()
        assert page._derive_tenor("not-a-date", "2026-01-01") == "N/A"

    def test_five_year_tenor(self):
        page = make_page()
        assert page._derive_tenor("2024-01-01", "2029-01-01") == "5Y"
