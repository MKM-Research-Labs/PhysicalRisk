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

"""Tests for trade marks management."""


class TestTradeMarks:
    """Tests for trade marks management."""

    def test_load_empty_marks(self, pnl_engine):
        assert pnl_engine.load_trade_marks() == {}

    def test_update_and_load_mark(self, pnl_engine):
        pnl_engine.update_trade_mark("PRS-001", {
            "trade_status": "Open",
            "inception_mark": {"fair_spread_bps": 250.0},
        })
        assert pnl_engine.load_trade_marks()["PRS-001"]["trade_status"] == "Open"

    def test_close_trade(self, pnl_engine):
        pnl_engine.update_trade_mark("PRS-001", {"trade_status": "Open"})
        mark = pnl_engine.close_trade("PRS-001", 260.0)
        assert mark["trade_status"] == "Closed"
        assert mark["close_spread_bps"] == 260.0
        assert "close_date" in mark

    def test_close_unmarked_trade(self, pnl_engine):
        """Closing a trade with no prior mark creates the entry first."""
        mark = pnl_engine.close_trade("PRS-NEW", 175.0, final_pnl=1234.5)
        assert mark["trade_status"] == "Closed"
        assert mark["close_spread_bps"] == 175.0
        assert mark["final_pnl"] == 1234.5
