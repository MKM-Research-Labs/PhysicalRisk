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

"""Tests for market state management endpoints."""

import json
from unittest.mock import patch

import pytest


class TestGetMarketState:
    """GET /trading/market-state endpoint tests."""

    def test_get_market_state(self, trading_client, trading_env):
        """GET returns market_state with yield_curve and hazard_term_structure."""
        resp = trading_client.get('/api/v1/trading/market-state')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        ms = data['market_state']
        assert 'yield_curve' in ms
        assert 'hazard_term_structure' in ms

    def test_get_market_state_has_effective_rates(self, trading_client,
                                                   trading_env):
        """Response includes per-gauge effective rates."""
        resp = trading_client.get('/api/v1/trading/market-state')
        data = json.loads(resp.data)
        assert 'gauges' in data
        # Should have entries for our 2 test gauges
        gauge_ids = {g['gauge_id'] for g in data['gauges']
                     if isinstance(g, dict) and 'gauge_id' in g}
        if isinstance(data['gauges'], dict):
            gauge_ids = set(data['gauges'].keys())
        assert len(gauge_ids) >= 1

    def test_market_state_initial_load_creates_defaults(self, trading_client,
                                                         trading_env):
        """First load creates default yield curve."""
        resp = trading_client.get('/api/v1/trading/market-state')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        ms = data['market_state']
        yc = ms.get('yield_curve', {})
        assert len(yc) > 0


class TestUpdateMarketState:
    """POST /trading/market-state endpoint tests."""

    def test_update_market_state(self, trading_client, trading_env):
        """POST updates gauge rate successfully."""
        resp = trading_client.post('/api/v1/trading/market-state',
                                   json={'gauge_id': 'GAUGE-001',
                                         'trigger': 'severe',
                                         'new_rate': 0.05})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert data['gauge_id'] == 'GAUGE-001'

    def test_update_market_state_returns_pnl_impact(self, trading_client,
                                                     trading_env):
        """Update returns affected_trades and total_pnl_impact."""
        resp = trading_client.post('/api/v1/trading/market-state',
                                   json={'gauge_id': 'GAUGE-001',
                                         'trigger': 'severe',
                                         'new_rate': 0.05})
        data = json.loads(resp.data)
        assert 'affected_trades' in data
        assert 'total_pnl_impact' in data

    def test_update_market_state_missing_gauge(self, trading_client,
                                                trading_env):
        """Missing gauge returns 400."""
        resp = trading_client.post('/api/v1/trading/market-state',
                                   json={'trigger': 'severe',
                                         'new_rate': 0.05})
        assert resp.status_code == 400

    def test_update_market_state_no_body(self, trading_client, trading_env):
        """No JSON body returns error (500 — Flask BadRequest caught)."""
        resp = trading_client.post('/api/v1/trading/market-state',
                                   content_type='application/json')
        assert resp.status_code in (400, 500)

    def test_market_state_persists(self, trading_client, trading_env):
        """Updated state persists across requests."""
        trading_client.post('/api/v1/trading/market-state',
                            json={'gauge_id': 'GAUGE-001',
                                  'trigger': 'severe',
                                  'new_rate': 0.07})
        resp = trading_client.get('/api/v1/trading/market-state')
        data = json.loads(resp.data)
        # State file should have been updated
        assert resp.status_code == 200
        assert data['market_state']['num_adjusted'] >= 1


class TestResetMarketState:
    """POST /trading/market-state/reset endpoint tests."""

    def test_reset_market_state_all(self, trading_client, trading_env):
        """Reset clears all adjustments."""
        # First make a change
        trading_client.post('/api/v1/trading/market-state',
                            json={'gauge_id': 'GAUGE-001',
                                  'trigger': 'severe',
                                  'new_rate': 0.10})
        # Then reset
        resp = trading_client.post('/api/v1/trading/market-state/reset',
                                   json={})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'all' in data['message']

    def test_reset_market_state_single_gauge(self, trading_client, trading_env):
        """Reset clears one gauge only."""
        resp = trading_client.post('/api/v1/trading/market-state/reset',
                                   json={'gauge_id': 'GAUGE-001'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert 'GAUGE-001' in data['message']


class TestMarketStateErrorHandlers:
    """Error handling paths in market state endpoints."""

    def test_get_market_state_engine_error_returns_500(self, trading_client,
                                                        trading_env):
        """GET market-state returns 500 when engine raises (lines 44-46)."""
        with patch('routes.trading.market_state._get_engines',
                   side_effect=RuntimeError('engine fail')):
            resp = trading_client.get('/api/v1/trading/market-state')
            assert resp.status_code == 500
            data = json.loads(resp.data)
            assert data['status'] == 'error'

    def test_update_market_state_null_body_returns_400(self, trading_client,
                                                        trading_env):
        """POST market-state with null JSON body → 400 (line 55)."""
        resp = trading_client.post('/api/v1/trading/market-state',
                                   data=b'null',
                                   content_type='application/json')
        assert resp.status_code == 400

    def test_reset_market_state_engine_error_returns_500(self, trading_client,
                                                          trading_env):
        """POST market-state/reset returns 500 when engine raises (lines 119-121)."""
        with patch('routes.trading.market_state._get_engines',
                   side_effect=RuntimeError('reset fail')):
            resp = trading_client.post('/api/v1/trading/market-state/reset',
                                       json={})
            assert resp.status_code == 500
