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
