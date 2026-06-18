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

"""Tests for trading blotter GET and close-out endpoints."""

import json

import pytest


class TestGetBlotter:
    """GET /trading/blotter endpoint tests."""

    def test_get_blotter_returns_trades(self, trading_client, trading_env):
        """Blotter returns enriched trades with status success."""
        resp = trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert len(data['trades']) == 16  # 7 Thames Central gauges, 16 trades total

    def test_blotter_has_required_fields(self, trading_client, trading_env):
        """Each trade must have core identification and pricing fields."""
        resp = trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        for trade in data['trades']:
            assert 'swap_id' in trade
            assert 'gauge_id' in trade
            assert 'fair_spread_bps' in trade
            assert 'gauge_fs01' in trade
            assert 'mtm' in trade
            assert 'notional' in trade
            assert 'is_payer' in trade

    def test_blotter_has_pnl_fields(self, trading_client, trading_env):
        """Each trade must have P&L decomposition fields."""
        resp = trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        for trade in data['trades']:
            assert 'daily_pnl' in trade
            assert 'market_pnl' in trade
            assert 'new_trade_pnl' in trade
            assert 'running_pnl' in trade

    def test_blotter_has_prev_fair_spread(self, trading_client, trading_env):
        """Each trade must have prev_fair_spread_bps for curve-move indication."""
        resp = trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        for trade in data['trades']:
            assert 'prev_fair_spread_bps' in trade

    def test_blotter_summary_fields(self, trading_client, trading_env):
        """Summary must have all required aggregate fields."""
        resp = trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        summary = data['summary']
        assert 'num_trades' in summary
        assert 'total_notional' in summary
        assert 'total_daily_pnl' in summary
        assert 'total_running_pnl' in summary
        assert 'daily_pnl_from_trades' in summary
        assert 'daily_pnl_from_market' in summary

    def test_blotter_gauge_name_injected(self, trading_client, trading_env):
        """Trades should have gauge_name from gauge locations."""
        resp = trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        names = {t['gauge_name'] for t in data['trades'] if t.get('gauge_name')}
        assert 'Thames at Westminster' in names

    def test_blotter_fs01_sign_payer_positive(self, trading_client, trading_env):
        """Payer (long protection) trade should have positive gauge_fs01."""
        resp = trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        payer_trades = [t for t in data['trades'] if t['is_payer']]
        assert len(payer_trades) > 0
        for t in payer_trades:
            assert t['gauge_fs01'] >= 0, \
                f"Payer {t['swap_id']} should have non-negative FS01"

    def test_blotter_fs01_sign_receiver_negative(self, trading_client, trading_env):
        """Receiver (short protection) trade should have negative gauge_fs01."""
        resp = trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        rcv_trades = [t for t in data['trades'] if not t['is_payer']]
        assert len(rcv_trades) > 0
        for t in rcv_trades:
            assert t['gauge_fs01'] <= 0, \
                f"Receiver {t['swap_id']} should have non-positive FS01"

    def test_blotter_empty_when_no_trades(self, empty_trading_client,
                                          empty_trading_env):
        """Returns empty trades list when no PRS files exist."""
        resp = empty_trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert len(data['trades']) == 0


class TestBlotterClosedTrades:
    """Test filtering of closed trades in blotter."""

    def test_filters_closed_trades_by_default(self, trading_client, trading_env):
        """Closed trades excluded from blotter by default."""
        # Close a trade first
        trading_client.post('/api/v1/trading/close/PRS-TEST-001',
                            json={'closeout_spread_bps': 290.0})

        resp = trading_client.get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        swap_ids = [t['swap_id'] for t in data['trades']]
        assert 'PRS-TEST-001' not in swap_ids

    def test_include_closed(self, trading_client, trading_env):
        """include_closed=true returns closed trades too."""
        trading_client.post('/api/v1/trading/close/PRS-TEST-001',
                            json={'closeout_spread_bps': 290.0})

        resp = trading_client.get(
            '/api/v1/trading/blotter?include_closed=true')
        data = json.loads(resp.data)
        swap_ids = [t['swap_id'] for t in data['trades']]
        assert 'PRS-TEST-001' in swap_ids


class TestCloseOut:
    """POST /trading/close/<swap_id> endpoint tests."""

    def test_close_trade_success(self, trading_client, trading_env):
        """Closing a trade at a negotiated spread returns success with close spread."""
        resp = trading_client.post('/api/v1/trading/close/PRS-TEST-001',
                                   json={'closeout_spread_bps': 300.0})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'close_spread_bps' in data
        assert data['close_spread_bps'] == 300.0
        assert data['swap_id'] == 'PRS-TEST-001'

    def test_close_trade_requires_closeout_spread(self, trading_client, trading_env):
        """Close-out without closeout_spread_bps returns 400."""
        resp = trading_client.post('/api/v1/trading/close/PRS-TEST-001',
                                   json={})
        assert resp.status_code == 400

    def test_close_trade_not_found(self, trading_client, trading_env):
        """Closing non-existent trade returns 404."""
        resp = trading_client.post('/api/v1/trading/close/PRS-INVALID',
                                   json={'closeout_spread_bps': 300.0})
        assert resp.status_code == 404

    def test_close_trade_marks_closed(self, trading_client, trading_env):
        """After close, trade status is set to Closed in marks file."""
        trading_client.post('/api/v1/trading/close/PRS-TEST-002',
                            json={'closeout_spread_bps': 295.0})

        marks_file = trading_env['trading_dir'] / 'trade_marks.json'
        assert marks_file.exists()
        with open(marks_file) as f:
            marks = json.load(f)
        assert marks['PRS-TEST-002']['trade_status'] == 'Closed'
        assert 'close_date' in marks['PRS-TEST-002']
        assert 'close_spread_bps' in marks['PRS-TEST-002']

    def test_close_trade_settlement_uses_closeout_spread(self, trading_client, trading_env):
        """Settlement amount reflects the negotiated closeout spread, not fair spread."""
        resp = trading_client.post('/api/v1/trading/close/PRS-TEST-001',
                                   json={'closeout_spread_bps': 400.0})
        data = json.loads(resp.data)
        assert data['status'] == 'success'
        assert data['close_spread_bps'] == 400.0
        assert 'final_pnl' in data
        assert 'settlement_amount' in data

    def test_close_trade_has_final_pnl(self, trading_client, trading_env):
        """Close response includes final P&L."""
        resp = trading_client.post('/api/v1/trading/close/PRS-TEST-001',
                                   json={'closeout_spread_bps': 290.0})
        data = json.loads(resp.data)
        assert 'final_pnl' in data
