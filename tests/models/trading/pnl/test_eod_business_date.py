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

"""New-trade P&L is judged against the EOD's business date, not the clock.

Submitting an EOD on a different day from its date used to book trades dated
"today" as new-trade P&L again: the 14 October EOD, run on 13 October, counted
the MTM of trades dated 13 October a second time.
"""

from datetime import date, timedelta


def _trade(trade_date, mtm=1_000.0, swap_id="PRS-NEW"):
    return {"swap_id": swap_id, "gauge_id": "G", "notional": 1_000_000, "trigger": "severe",
            "tenor": 1, "trade_spread_bps": 100.0, "fair_spread_bps": 100.0, "is_payer": True,
            "trade_date": trade_date, "trade_status": "Open", "risky_annuity": 0.9,
            "gauge_fs01": 0, "basis_dv01": 0, "mtm": mtm}


def test_a_trade_dated_the_eod_date_is_new(pnl_engine):
    out = pnl_engine.compute_daily_pnl([_trade("2026-10-13")], None, as_of="2026-10-13")
    assert out["daily_pnl_from_trades"] == 1_000.0


def test_a_trade_dated_another_day_is_not_new(pnl_engine):
    out = pnl_engine.compute_daily_pnl([_trade("2026-10-13")], None, as_of="2026-10-14")
    assert out["daily_pnl_from_trades"] == 0.0


def test_the_live_blotter_still_uses_today(pnl_engine):
    out = pnl_engine.compute_daily_pnl([_trade(date.today().isoformat())], None)
    assert out["daily_pnl_from_trades"] == 1_000.0


def test_an_eod_for_tomorrow_does_not_book_todays_trades_again(pnl_engine):
    today = date.today()
    tomorrow = (today + timedelta(days=1)).isoformat()
    trades = [_trade(today.isoformat())]
    pnl_engine.generate_eod_snapshot(trades, {}, today.isoformat())
    snap = pnl_engine.generate_eod_snapshot(trades, {}, tomorrow)
    assert snap["portfolio_summary"]["daily_pnl_from_trades"] == 0.0
    assert snap["portfolio_summary"]["total_daily_pnl"] == 0.0


def test_resubmitting_an_eod_compares_with_the_previous_day(pnl_engine):
    """A re-run EOD used to compare with the snapshot it replaced and show no
    market P&L; it must give the same answer as the first submission."""
    old = [_trade("2026-10-01", mtm=1_000.0, swap_id="PRS-OLD")]
    moved = [_trade("2026-10-01", mtm=1_250.0, swap_id="PRS-OLD")]
    pnl_engine.generate_eod_snapshot(old, {}, "2026-10-13")
    first = pnl_engine.generate_eod_snapshot(moved, {}, "2026-10-14")
    again = pnl_engine.generate_eod_snapshot(moved, {}, "2026-10-14")
    assert first["portfolio_summary"]["daily_pnl_from_market"] == 250.0
    assert again["portfolio_summary"]["daily_pnl_from_market"] == 250.0


def test_the_blotter_lookup_still_includes_the_same_day(pnl_engine):
    pnl_engine.generate_eod_snapshot([_trade("2026-10-01")], {}, "2026-10-14")
    assert pnl_engine._get_previous_eod("2026-10-14")["date"] == "2026-10-14"
    assert pnl_engine._get_previous_eod("2026-10-14", strictly_before=True) is None
