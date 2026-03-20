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

"""Fixtures for historical EOD tests."""

import json
from pathlib import Path

import pytest


def _make_eod_snapshot(date_str, positions=None, gauge_id="GAUGE-001"):
    """Build a minimal EOD snapshot dict."""
    ts = {
        gauge_id: {
            "alert": {"1": 0.05, "2": 0.055, "3": 0.06},
            "warning": {"1": 0.03, "2": 0.033, "3": 0.036},
        }
    }
    return {
        "date": date_str,
        "portfolio_summary": {
            "total_daily_pnl": 1000.0,
            "num_open_trades": len(positions or []),
        },
        "market_state_snapshot": {"hazard_term_structure": ts},
        "positions": positions or [],
    }


def _make_position(swap_id, gauge_id="GAUGE-001", fair=210.0, mkt=500.0, running=5000.0):
    """Build a minimal position dict."""
    return {
        "swap_id": swap_id,
        "trade_date": "2026-01-01",
        "trade_spread_bps": 200.0,
        "gauge_id": gauge_id,
        "trigger": "alert",
        "notional": 1_000_000,
        "is_payer": True,
        "fair_spread_bps": fair,
        "market_pnl": mkt,
        "running_pnl": running,
    }


@pytest.fixture
def eod_dir(tmp_path):
    """Empty EOD snapshot directory."""
    d = tmp_path / "eod"
    d.mkdir()
    return d


@pytest.fixture
def eod_dir_with_snapshots(tmp_path):
    """EOD directory pre-populated with 3 snapshots."""
    d = tmp_path / "eod"
    d.mkdir()
    dates = ["2026-01-02", "2026-01-05", "2026-01-06"]
    for i, dt in enumerate(dates):
        pos = [_make_position(f"PRS-{j:03d}", fair=200.0 + i) for j in range(2)]
        snap = _make_eod_snapshot(dt, positions=pos)
        (d / f"EOD-{dt}.json").write_text(json.dumps(snap))
    return d, dates
