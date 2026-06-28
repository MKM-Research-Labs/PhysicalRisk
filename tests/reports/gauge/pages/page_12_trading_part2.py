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
Tests for GaugeTradingPage — part 2.

_load_gauge_trades private branches and _load_market_state.
"""

import pytest
from db_helpers import tmp_catchment

import database

from .conftest import make_page

# ===========================================================================
# _load_gauge_trades private branches
# ===========================================================================

class TestLoadGaugeTrades:

    def test_no_trades_returns_empty(self, tmp_path):
        """No PRS trades in the seam -> empty list."""
        with tmp_catchment(tmp_path, "thames"):
            assert make_page()._load_gauge_trades("GAUGE-001") == []

    def test_trade_matching_gauge_id_appended(self, tmp_path):
        """Trade whose GaugeBasket contains the gauge -> appended."""
        with tmp_catchment(tmp_path, "thames"):
            database.save_prs_trade("thames", "PRS-001", {
                "PhysicalSwap": {
                    "Header": {"SwapID": "PRS-001"},
                    "GaugeSet": {"GaugeBasket": [{"GaugeID": "GAUGE-001"}]},
                }
            })
            result = make_page()._load_gauge_trades("GAUGE-001")
            assert len(result) == 1

    def test_trade_not_matching_gauge_skipped(self, tmp_path):
        """Trade for a different gauge -> not appended."""
        with tmp_catchment(tmp_path, "thames"):
            database.save_prs_trade("thames", "PRS-001", {
                "PhysicalSwap": {
                    "Header": {"SwapID": "PRS-001"},
                    "GaugeSet": {"GaugeBasket": [{"GaugeID": "GAUGE-999"}]},
                }
            })
            assert make_page()._load_gauge_trades("GAUGE-001") == []


class TestLoadMarketState:

    def test_market_state_exception_returns_empty(self, monkeypatch):
        """Lines 89-91: exception -> returns {}."""
        from config import config

        def _bad_trading_dir():
            raise RuntimeError("no trading dir")

        monkeypatch.setattr(config, "get_trading_dir", _bad_trading_dir)
        page = make_page()
        result = page._load_market_state()
        assert result == {}
