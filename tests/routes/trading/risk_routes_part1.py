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

"""Tests for portfolio risk grid and trade map endpoints. (part 1 of 2)"""

import json
from unittest.mock import patch

import pytest


class TestRiskGrid:
    """GET /trading/risk-grid endpoint tests."""

    def test_risk_grid_returns_grid(self, trading_client, trading_env):
        """GET returns a risk grid structure."""
        resp = trading_client.get('/api/v1/trading/risk-grid')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'grid' in data

    def test_risk_grid_has_gauges(self, trading_client, trading_env):
        """Grid should contain entries for traded gauges."""
        resp = trading_client.get('/api/v1/trading/risk-grid')
        data = json.loads(resp.data)
        grid = data['grid']
        # Grid should be a list or dict with gauge entries
        assert len(grid) > 0

    def test_risk_grid_with_no_trades(self, empty_trading_client,
                                       empty_trading_env):
        """Returns empty grid when no trades exist."""
        resp = empty_trading_client.get('/api/v1/trading/risk-grid')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'


class TestTradeMap:
    """GET /trading/trade-map endpoint tests."""

    def test_trade_map_returns_positions(self, trading_client, trading_env):
        """GET returns gauge positions."""
        resp = trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert 'gauges' in data

    def test_trade_map_gauge_has_coordinates(self, trading_client, trading_env):
        """Each gauge position has lat, lon, gauge_name."""
        resp = trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        for g in data['gauges']:
            assert 'lat' in g
            assert 'lon' in g
            assert 'gauge_name' in g
            assert 'gauge_id' in g

    def test_trade_map_includes_notional(self, trading_client, trading_env):
        """Each gauge has total and net notional."""
        resp = trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        for g in data['gauges']:
            assert 'total_notional' in g
            assert 'net_notional' in g
            assert g['total_notional'] > 0

    def test_trade_map_includes_fs01(self, trading_client, trading_env):
        """Each gauge has net_fs01."""
        resp = trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        for g in data['gauges']:
            assert 'net_fs01' in g

    def test_trade_map_includes_pnl(self, trading_client, trading_env):
        """Gauge positions include daily P&L."""
        resp = trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        for g in data['gauges']:
            assert 'daily_pnl' in g
            assert 'running_pnl' in g

    def test_trade_map_fs01_by_tenor(self, trading_client, trading_env):
        """Gauge positions include FS01 broken down by tenor."""
        resp = trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        for g in data['gauges']:
            assert 'fs01_by_tenor' in g
            assert isinstance(g['fs01_by_tenor'], dict)

    def test_trade_map_num_trades(self, trading_client, trading_env):
        """Gauge positions show number of trades."""
        resp = trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        gauges_by_id = {g['gauge_id']: g for g in data['gauges']}
        # GAUGE-001 has 2 trades (PRS-TEST-001 + PRS-TEST-002)
        assert gauges_by_id['GAUGE-001']['num_trades'] == 2
        # GAUGE-002 has 1 trade (PRS-TEST-003)
        assert gauges_by_id['GAUGE-002']['num_trades'] == 1

    def test_trade_map_with_no_trades(self, empty_trading_client,
                                       empty_trading_env):
        """Returns empty positions when no trades exist."""
        resp = empty_trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert len(data['gauges']) == 0
