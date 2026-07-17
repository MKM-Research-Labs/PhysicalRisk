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

"""Tests for portfolio risk grid and trade map endpoints. (part 2 of 2)"""

import json
from unittest.mock import patch

import pytest


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
