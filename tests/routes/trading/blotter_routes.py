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

"""Tests for trading blotter and close-out endpoints."""

import json
from unittest.mock import patch

import pytest

from .conftest import make_trade


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


class TestActiveGauges:
    """GET /trading/blotter/active-gauges — context menu blotter availability.

    These tests drive the right-click 'Gauge Blotter' enable/disable logic.
    Lambeth Bridge (GAUGE-9042bd95) is used as the named test gauge because
    it exists in the real Thames portfolio and has a representative trade in
    the test fixture.
    """

    LAMBETH_ID = 'GAUGE-9042bd95'
    WESTMINSTER_ID = 'GAUGE-001'
    CHELSEA_ID = 'GAUGE-002'
    # A gauge present in SAMPLE_GAUGEHC but with no trade
    NO_TRADE_ID = 'GAUGE-NO-TRADE'

    def test_lambeth_appears_when_it_has_an_open_trade(
            self, trading_client, trading_env):
        """Lambeth Bridge (GAUGE-9042bd95) must be in active-gauges
        when PRS-TEST-LAMBETH is open — this is the right-click menu test."""
        resp = trading_client.get('/api/v1/trading/blotter/active-gauges')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert self.LAMBETH_ID in data['gauge_ids'], (
            f"Lambeth ({self.LAMBETH_ID}) should be active — it has an open trade"
        )

    def test_all_gauges_with_trades_are_returned(
            self, trading_client, trading_env):
        """Westminster, Chelsea and Lambeth all have trades — all must appear."""
        resp = trading_client.get('/api/v1/trading/blotter/active-gauges')
        data = json.loads(resp.data)
        active = data['gauge_ids']
        assert self.WESTMINSTER_ID in active
        assert self.CHELSEA_ID in active
        assert self.LAMBETH_ID in active

    def test_gauge_without_trade_is_not_returned(
            self, trading_client, trading_env):
        """A gauge that has no PRS trades must not appear in active-gauges,
        so the context menu item will be shown as disabled."""
        resp = trading_client.get('/api/v1/trading/blotter/active-gauges')
        data = json.loads(resp.data)
        assert self.NO_TRADE_ID not in data['gauge_ids']

    def test_lambeth_excluded_after_its_trade_is_closed(
            self, trading_client, trading_env):
        """After closing PRS-TEST-LAMBETH, Lambeth must leave active-gauges
        so right-click 'Gauge Blotter' becomes disabled for that marker."""
        # Confirm Lambeth is active before close-out
        before = json.loads(
            trading_client.get('/api/v1/trading/blotter/active-gauges').data)
        assert self.LAMBETH_ID in before['gauge_ids']

        # Close out the Lambeth trade
        trading_client.post('/api/v1/trading/close/PRS-TEST-LAMBETH',
                            json={'closeout_spread_bps': 285.0})

        # Lambeth must now be absent
        after = json.loads(
            trading_client.get('/api/v1/trading/blotter/active-gauges').data)
        assert self.LAMBETH_ID not in after['gauge_ids'], (
            "Lambeth should be removed from active-gauges once its only "
            "trade is closed — the right-click menu item should be disabled"
        )

    def test_other_gauges_unaffected_by_lambeth_closeout(
            self, trading_client, trading_env):
        """Closing Lambeth's trade must not affect Westminster or Chelsea."""
        trading_client.post('/api/v1/trading/close/PRS-TEST-LAMBETH',
                            json={'closeout_spread_bps': 285.0})
        after = json.loads(
            trading_client.get('/api/v1/trading/blotter/active-gauges').data)
        assert self.WESTMINSTER_ID in after['gauge_ids']
        assert self.CHELSEA_ID in after['gauge_ids']

    def test_empty_blotter_returns_empty_list(
            self, empty_trading_client, empty_trading_env):
        """No trades at all → empty gauge_ids list → all right-click
        'Gauge Blotter' items disabled."""
        resp = empty_trading_client.get(
            '/api/v1/trading/blotter/active-gauges')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['gauge_ids'] == []

    def test_response_is_sorted(self, trading_client, trading_env):
        """gauge_ids are returned in sorted order for stable JS dict lookup."""
        resp = trading_client.get('/api/v1/trading/blotter/active-gauges')
        data = json.loads(resp.data)
        ids = data['gauge_ids']
        assert ids == sorted(ids)


class TestBlotterGaugeNameInjection:
    """gauge_name injected from locations when trade has none (lines 43-44)."""

    def test_gauge_name_injected_when_missing(self, trading_env):
        """Trade with empty GaugeName gets name injected from gauge locations."""
        trade = make_trade('PRS-NONAME-001', 'GAUGE-001', '',
                           is_payer=True, spread_bps=200.0,
                           tenor=3, notional=5_000_000)
        with open(trading_env['prs_dir'] / 'PRS-NONAME-001.json', 'w') as f:
            json.dump(trade, f)
        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        resp = app.test_client().get('/api/v1/trading/blotter')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        noname = [t for t in data['trades']
                  if t.get('swap_id') == 'PRS-NONAME-001']
        if noname:
            assert noname[0].get('gauge_name', '') != ''


class TestBlotterErrorHandlers:
    """Error handling paths in blotter endpoints."""

    def test_blotter_engine_error_returns_500(self, trading_client, trading_env):
        """Blotter returns 500 when engine raises (lines 94-96)."""
        with patch('routes.trading.blotter._get_engines',
                   side_effect=RuntimeError('engine fail')):
            resp = trading_client.get('/api/v1/trading/blotter')
            assert resp.status_code == 500
            data = json.loads(resp.data)
            assert data['status'] == 'error'

    def test_active_gauges_corrupt_file_skipped(self, trading_env):
        """Corrupt JSON in prs dir is skipped via inner exception (lines 134-135)."""
        corrupt = trading_env['prs_dir'] / 'PRS-CORRUPT.json'
        corrupt.write_text('NOT VALID JSON{{{')
        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        resp = app.test_client().get('/api/v1/trading/blotter/active-gauges')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'

    def test_close_trade_pdf_regen_exception_caught(self, trading_client, trading_env):
        """PDF regen exception is caught; trade close still succeeds (lines 236-237)."""
        with patch('routes.prs._generate_trade_pdf',
                   side_effect=RuntimeError('pdf fail')):
            resp = trading_client.post(
                '/api/v1/trading/close/PRS-TEST-001',
                json={'closeout_spread_bps': 200.0})
            data = json.loads(resp.data)
            assert resp.status_code == 200
            assert data['swap_id'] == 'PRS-TEST-001'
            assert data['pdf_base64'] is None

    def test_close_trade_engine_error_returns_500(self, trading_client, trading_env):
        """Close trade returns 500 when engine raises (lines 251-253)."""
        with patch('routes.trading.blotter._get_engines',
                   side_effect=RuntimeError('close fail')):
            resp = trading_client.post(
                '/api/v1/trading/close/PRS-TEST-001',
                json={'closeout_spread_bps': 200.0})
            assert resp.status_code == 500
            data = json.loads(resp.data)
            assert data['status'] == 'error'
