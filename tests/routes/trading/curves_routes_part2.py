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

"""Tests for P&L series, curve history, null body handling, and error handlers."""

import json
from unittest.mock import patch

import pytest


class TestPnLSeries:
    """GET /trading/pnl-series endpoint tests."""

    def test_pnl_series_empty(self, trading_client, trading_env):
        """Returns empty series when no EOD snapshots exist."""
        resp = trading_client.get('/api/v1/trading/pnl-series')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert data['series'] == []

    def test_pnl_series_after_eod(self, trading_client, trading_env):
        """After an EOD snap, series has one entry."""
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-28'})
        resp = trading_client.get('/api/v1/trading/pnl-series')
        data = json.loads(resp.data)
        assert len(data['series']) == 1
        entry = data['series'][0]
        assert 'date' in entry
        assert 'daily_pnl' in entry
        assert 'running_pnl' in entry
        assert 'from_trades' in entry
        assert 'from_market' in entry


class TestCurveHistory:
    """GET /trading/curve-history endpoint tests."""

    def test_curve_history_requires_gauge_id(self, trading_client, trading_env):
        """Missing gauge_id returns 400."""
        resp = trading_client.get('/api/v1/trading/curve-history')
        assert resp.status_code == 400

    def test_curve_history_empty_when_no_eods(self, trading_client,
                                               trading_env):
        """Returns empty history when no snapshots exist."""
        resp = trading_client.get(
            '/api/v1/trading/curve-history?gauge_id=GAUGE-001')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['history'] == []

    def test_curve_history_with_eod(self, trading_client, trading_env):
        """After EOD, returns term structure history for that gauge."""
        # Submit EOD first to create a snapshot
        trading_client.post('/api/v1/trading/eod',
                            json={'date': '2026-02-28'})
        resp = trading_client.get(
            '/api/v1/trading/curve-history?gauge_id=GAUGE-001&trigger=severe')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['gauge_id'] == 'GAUGE-001'
        assert data['trigger'] == 'severe'


class TestCurvesNullBody:
    """Null JSON body returns 400 (lines 115, 145, 245, 282)."""

    def test_update_yield_curve_null_body(self, trading_client, trading_env):
        """POST yield-curve with null body -> 400 (line 115)."""
        resp = trading_client.post('/api/v1/trading/yield-curve',
                                   data=b'null',
                                   content_type='application/json')
        assert resp.status_code == 400

    def test_commit_yield_curve_null_body(self, trading_client, trading_env):
        """POST yield-curve/commit with null body -> 400 (line 145)."""
        resp = trading_client.post('/api/v1/trading/yield-curve/commit',
                                   data=b'null',
                                   content_type='application/json')
        assert resp.status_code == 400

    def test_update_hazard_ts_null_body(self, trading_client, trading_env):
        """POST hazard-term-structure with null body -> 400 (line 245)."""
        resp = trading_client.post('/api/v1/trading/hazard-term-structure',
                                   data=b'null',
                                   content_type='application/json')
        assert resp.status_code == 400

    def test_commit_hazard_ts_null_body(self, trading_client, trading_env):
        """POST hazard-term-structure/commit with null body -> 400 (line 282)."""
        resp = trading_client.post('/api/v1/trading/hazard-term-structure/commit',
                                   data=b'null',
                                   content_type='application/json')
        assert resp.status_code == 400


class TestCurvesErrorHandlers:
    """Error handling paths covering except blocks in curves.py."""

    def test_pnl_series_error_returns_500(self, trading_client, trading_env):
        """pnl-series returns 500 on engine error (lines 36-38)."""
        with patch('routes.trading.curves._get_engines',
                   side_effect=RuntimeError('fail')):
            resp = trading_client.get('/api/v1/trading/pnl-series')
            assert resp.status_code == 500

    def test_curve_history_error_returns_500(self, trading_client, trading_env):
        """curve-history returns 500 on engine error (lines 82-84)."""
        with patch('routes.trading.curves._get_engines',
                   side_effect=RuntimeError('fail')):
            resp = trading_client.get(
                '/api/v1/trading/curve-history?gauge_id=GAUGE-001')
            assert resp.status_code == 500

    def test_get_yield_curve_error_returns_500(self, trading_client, trading_env):
        """GET yield-curve returns 500 on engine error."""
        with patch('routes.trading.curves_yield._get_engines',
                   side_effect=RuntimeError('fail')):
            resp = trading_client.get('/api/v1/trading/yield-curve')
            assert resp.status_code == 500

    def test_update_yield_curve_error_returns_500(self, trading_client, trading_env):
        """POST yield-curve returns 500 on engine error."""
        with patch('routes.trading.curves_yield._get_engines',
                   side_effect=RuntimeError('fail')):
            resp = trading_client.post('/api/v1/trading/yield-curve',
                                       json={'tenor': 3, 'rate': 0.04})
            assert resp.status_code == 500

    def test_get_hazard_ts_error_returns_500(self, trading_client, trading_env):
        """GET hazard-term-structure returns 500 on engine error."""
        with patch('routes.trading.curves_hazard._get_engines',
                   side_effect=RuntimeError('fail')):
            resp = trading_client.get('/api/v1/trading/hazard-term-structure')
            assert resp.status_code == 500

    def test_reset_yield_curve_error_returns_500(self, trading_client, trading_env):
        """POST yield-curve/reset returns 500 on engine error."""
        with patch('routes.trading.curves_yield._get_engines',
                   side_effect=RuntimeError('fail')):
            resp = trading_client.post('/api/v1/trading/yield-curve/reset',
                                       json={})
            assert resp.status_code == 500

    def test_commit_hazard_ts_error_returns_500(self, trading_client, trading_env):
        """POST hazard-term-structure/commit returns 500 on error."""
        with patch('routes.trading.curves_hazard._get_engines',
                   side_effect=RuntimeError('fail')):
            resp = trading_client.post(
                '/api/v1/trading/hazard-term-structure/commit',
                json={'gauge_id': 'GAUGE-001', 'trigger': 'warning',
                      'rates': {'1': 0.05, '2': 0.06}})
            assert resp.status_code == 500

    def test_reset_hazard_ts_error_returns_500(self, trading_client, trading_env):
        """POST hazard-term-structure/reset returns 500 on error."""
        with patch('routes.trading.curves_hazard._get_engines',
                   side_effect=RuntimeError('fail')):
            resp = trading_client.post(
                '/api/v1/trading/hazard-term-structure/reset',
                json={})
            assert resp.status_code == 500
