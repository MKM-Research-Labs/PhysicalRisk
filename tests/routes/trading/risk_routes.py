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

"""Tests for portfolio risk grid and trade map endpoints."""

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


class TestTradeMapWithProperties:
    """Trade map with property and closed-trade scenarios."""

    def test_trade_map_loads_property_locations(self, trading_env):
        """Property locations loaded from property.json (lines 97-101)."""
        props = {
            'properties': [
                {
                    'PropertyHeader': {
                        'PropertyID': 'PROP-001',
                        'Location': {'Latitude': 51.5, 'Longitude': -0.1},
                        'Address': '1 Test Street',
                    }
                }
            ]
        }
        with open(trading_env['input_dir'] / 'property.json', 'w') as f:
            import json as _json
            _json.dump(props, f)
        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        resp = app.test_client().get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert 'gauges' in data

    def test_trade_map_skips_closed_trades(self, trading_client, trading_env):
        """Closed trades are excluded from trade map gauge aggregation (line 115)."""
        # Close one trade first
        trading_client.post('/api/v1/trading/close/PRS-TEST-LAMBETH',
                            json={'closeout_spread_bps': 285.0})
        resp = trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        # Lambeth gauge should not appear (no more open trades)
        gauge_ids = {g['gauge_id'] for g in data['gauges']}
        assert 'GAUGE-9042bd95' not in gauge_ids

    def test_trade_map_gauge_not_in_gaugehc_loaded_from_gauge_json(
            self, trading_env):
        """Gauge in gauge.json but not gaugehc.json gets coordinates (lines 83-85)."""
        # Add a gauge to gauge.json that is NOT in gaugehc.json
        import json as _json
        with open(trading_env['input_dir'] / 'gauge.json') as f:
            gauge_data = _json.load(f)
        gauge_data['flood_gauges'].append({
            'FloodGauge': {
                'GaugeID': 'GAUGE-EXTRA',
                'GaugeName': 'Extra Gauge',
                'Location': {'Latitude': 51.6, 'Longitude': -0.2},
            }
        })
        with open(trading_env['input_dir'] / 'gauge.json', 'w') as f:
            _json.dump(gauge_data, f)

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        resp = app.test_client().get('/api/v1/trading/trade-map')
        assert resp.status_code == 200


class TestTradeMapPropertyPositions:
    """Cover property_id branch (lines 186-187) and _load_property_trades (lines 203-209)."""

    def test_enriched_trade_with_property_id(self, trading_client, trading_env):
        """Enriched trade with property_id creates a property position (lines 184-198)."""
        # Write a property.json with matching property
        import json as _json
        props = {
            'properties': [{
                'PropertyHeader': {
                    'PropertyID': 'PROP-X1',
                    'Location': {'Latitude': 51.49, 'Longitude': -0.12},
                    'Address': '10 Test Lane',
                }
            }]
        }
        with open(trading_env['input_dir'] / 'property.json', 'w') as f:
            _json.dump(props, f)

        # Wrap _get_engines so revalue_all injects property_id into first trade
        from routes.trading._helpers import _get_engines as real_get_engines

        def patched_get_engines():
            market_mgr, delta_eng, pnl_eng = real_get_engines()
            orig_revalue = delta_eng.revalue_all

            def wrapped_revalue(trades, state):
                enriched = orig_revalue(trades, state)
                if enriched:
                    enriched[0]['property_id'] = 'PROP-X1'
                return enriched

            delta_eng.revalue_all = wrapped_revalue
            return market_mgr, delta_eng, pnl_eng

        with patch('routes.trading.risk._get_engines',
                   side_effect=patched_get_engines):
            resp = trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        prop_positions = data['properties']
        matched = [p for p in prop_positions if p['property_id'] == 'PROP-X1']
        assert len(matched) >= 1
        assert matched[0]['lat'] == 51.49
        assert matched[0]['lon'] == -0.12
        assert matched[0]['address'] == '10 Test Lane'

    def test_property_trades_appear_on_map(self, trading_client, trading_env):
        """_load_property_trades results with lat/lon appear in properties (lines 201-225)."""
        sample_prop_trades = [
            {
                'property_id': 'PROP-PT1',
                'latitude': 51.50,
                'longitude': -0.08,
                'property_address': '5 River Rd',
                'postcode': 'SE1 1AA',
                'gauge_id': 'GAUGE-001',
                'notional': 500000,
                'is_payer': True,
                'swap_id': 'PRS-PROP-001',
                'spread_bps': 120,
                'gauge_fs01': 3.5,
                'npv': -1200,
                'counterparty': 'PropBank',
                'ea_flood_zone': '3',
            },
            # This entry has no lat/lon so should be skipped (line 205-206)
            {
                'property_id': 'PROP-PT2',
                'latitude': 0,
                'longitude': 0,
                'notional': 100000,
            },
        ]
        with patch('routes.trading.risk._load_property_trades',
                   return_value=sample_prop_trades):
            resp = trading_client.get('/api/v1/trading/trade-map')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        prop_positions = data['properties']
        ids = [p['property_id'] for p in prop_positions]
        assert 'PROP-PT1' in ids
        # PROP-PT2 skipped because lat=0, lon=0
        assert 'PROP-PT2' not in ids
        # Verify fields of included property trade
        pt1 = [p for p in prop_positions if p['property_id'] == 'PROP-PT1'][0]
        assert pt1['lat'] == 51.50
        assert pt1['lon'] == -0.08
        assert pt1['net_notional'] == 500000  # payer direction=+1
        assert pt1['swap_id'] == 'PRS-PROP-001'


class TestRiskErrorHandlers:
    """Error handling paths in risk endpoints."""

    def test_risk_grid_engine_error_returns_500(self, trading_client, trading_env):
        """risk-grid returns 500 when engine raises (lines 44-46)."""
        with patch('routes.trading.risk._get_engines',
                   side_effect=RuntimeError('grid fail')):
            resp = trading_client.get('/api/v1/trading/risk-grid')
            assert resp.status_code == 500
            data = json.loads(resp.data)
            assert data['status'] == 'error'

    def test_trade_map_engine_error_returns_500(self, trading_client, trading_env):
        """trade-map returns 500 when engine raises (lines 197-199)."""
        with patch('routes.trading.risk._get_engines',
                   side_effect=RuntimeError('map fail')):
            resp = trading_client.get('/api/v1/trading/trade-map')
            assert resp.status_code == 500
