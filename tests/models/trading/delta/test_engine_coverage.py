# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage expansion tests for delta_engine/engine.py — lines 94-95, 150,
230, 237-238."""

import json

import pytest

from models.trading.delta_engine.engine import DeltaEngine


def _make_gaugehc(input_dir):
    gaugehc = [{
        'gauge_id': 'GAUGE-TEST-001',
        'gauge_name': 'Test Gauge',
        'annual_hazard_rate_alert': 0.04,
        'annual_hazard_rate_warning': 0.025,
        'annual_hazard_rate_severe': 0.01,
    }]
    with open(input_dir / 'gaugehc.json', 'w') as f:
        json.dump(gaugehc, f)


def _base_trade(swap_id='PRS-TEST001', is_payer=True, property_id=None,
                basis_bps=0, end_date='2031-01-01'):
    trade = {
        'PhysicalSwap': {
            'Header': {
                'SwapID': swap_id,
                'ValuationDate': '2026-01-01',
                'PropertyId': property_id,
            },
            'LegData': {'Notional': 10_000_000, 'Payer': is_payer},
            'ScheduleData': {'EndDate': end_date},
            'GaugeSet': {'GaugeBasket': [{'GaugeID': 'GAUGE-TEST-001'}]},
            'Pricing': {'SpreadBps': 250.0, 'TriggerLevel': 'warning', 'Recovery': 0.0},
        }
    }
    if property_id or basis_bps:
        trade['TradingMetadata'] = {
            'property_id': property_id,
            'basis_bps': basis_bps,
        }
    return trade


class TestPropertyBasisDelta:
    """Lines 94-95: property_id triggers basis_info computation."""

    def test_property_trade_has_basis_info(self, tmp_path):
        """Trade with property_id computes basis_delta_bps and basis_dv01."""
        from models.trading.market_state import MarketStateManager

        input_dir = tmp_path / 'input'
        input_dir.mkdir()
        trading_dir = tmp_path / 'trading'
        trading_dir.mkdir()
        _make_gaugehc(input_dir)

        market_mgr = MarketStateManager(trading_dir, input_dir)
        engine = DeltaEngine(market_mgr)

        trade = _base_trade(property_id='PROP-001', basis_bps=15)
        enriched = engine.enrich_trade(trade)

        assert enriched['property_id'] == 'PROP-001'
        assert 'basis_delta_bps' in enriched
        assert 'basis_dv01' in enriched
        # With non-zero basis_bps, basis_dv01 should be non-zero
        assert enriched['basis_dv01'] != 0


class TestRevalueAllDefaultMarketState:
    """Line 150: revalue_all with market_state=None loads it."""

    def test_revalue_all_loads_market_state(self, tmp_path):
        """revalue_all(trades, None) loads market state internally."""
        from models.trading.market_state import MarketStateManager

        input_dir = tmp_path / 'input'
        input_dir.mkdir()
        trading_dir = tmp_path / 'trading'
        trading_dir.mkdir()
        _make_gaugehc(input_dir)

        market_mgr = MarketStateManager(trading_dir, input_dir)
        engine = DeltaEngine(market_mgr)

        trades = [_base_trade()]
        # Pass market_state=None to trigger line 150
        enriched = engine.revalue_all(trades, market_state=None)
        assert len(enriched) == 1
        assert enriched[0]['swap_id'] == 'PRS-TEST001'
        assert enriched[0]['fair_spread_bps'] > 0


class TestRemainingTenorEdgeCases:
    """Lines 230, 237-238: _remaining_tenor with empty or invalid EndDate."""

    def test_empty_end_date_returns_5(self):
        """Empty EndDate returns default tenor of 5."""
        result = DeltaEngine._remaining_tenor({'EndDate': ''})
        assert result == 5

    def test_missing_end_date_returns_5(self):
        """Missing EndDate key returns default tenor of 5."""
        result = DeltaEngine._remaining_tenor({})
        assert result == 5

    def test_invalid_date_format_returns_5(self):
        """Invalid date format returns default tenor of 5 (ValueError path)."""
        result = DeltaEngine._remaining_tenor({'EndDate': 'not-a-date'})
        assert result == 5

    def test_none_end_date_returns_5(self):
        """None EndDate returns default tenor of 5 (TypeError path)."""
        result = DeltaEngine._remaining_tenor({'EndDate': None})
        assert result == 5

    def test_valid_end_date_returns_years(self):
        """Valid far-future EndDate returns positive tenor."""
        result = DeltaEngine._remaining_tenor({'EndDate': '2035-01-01'})
        assert result >= 1
