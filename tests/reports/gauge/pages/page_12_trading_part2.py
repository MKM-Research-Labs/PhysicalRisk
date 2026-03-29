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

import json

import pytest

from .conftest import make_page


# ===========================================================================
# _load_gauge_trades private branches
# ===========================================================================

class TestLoadGaugeTrades:

    def test_prs_dir_not_exist_returns_empty(self, tmp_path, monkeypatch):
        """Line 67: prs_dir doesn't exist -> return empty list."""
        from config import config
        monkeypatch.setattr(config, "get_reports_dir", lambda x: str(tmp_path / "prs"))
        page = make_page()
        result = page._load_gauge_trades("GAUGE-001")
        assert result == []

    def test_trade_matching_gauge_id_appended(self, tmp_path, monkeypatch):
        """Lines 75-76: trade with matching gauge_id -> appended to list."""
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
        page = make_page()
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
        page = make_page()
        result = page._load_gauge_trades("GAUGE-001")
        assert result == []

    def test_get_reports_dir_raises_fallback(self, tmp_path, monkeypatch):
        """Lines 59-64: get_reports_dir raises -> fallback to get_output_path."""
        from config import config

        def _bad_reports_dir(x):
            raise AttributeError("no such method")

        monkeypatch.setattr(config, "get_reports_dir", _bad_reports_dir)
        monkeypatch.setattr(config, "get_output_dir", lambda: tmp_path)
        page = make_page()
        result = page._load_gauge_trades("GAUGE-001")
        assert result == []  # prs subdir doesn't exist


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
