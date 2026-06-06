# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Shared loader, module-level symbols, and helper functions for historical_eod tests."""

import json
from pathlib import Path
import importlib.util


def _load_heod():
    """Load historical_eod directly from file, bypassing port.src.__init__ chain.

    Registers the module under 'port.src.historical_eod' in sys.modules so that
    pytest-cov can track coverage for it when using --cov=port.src.historical_eod.
    """
    import sys
    mod_name = 'port.src.historical_eod'
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    mod_path = (
        Path(__file__).parent.parent.parent.parent.parent
        / 'src' / 'port' / 'src' / 'historical_eod' / '__init__.py'
    )
    spec = importlib.util.spec_from_file_location(mod_name, mod_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod  # register before exec to allow coverage tracing
    spec.loader.exec_module(mod)
    return mod


_heod = _load_heod()
_business_days = _heod._business_days
generate_hazard_curve_history_file = _heod.generate_hazard_curve_history_file
generate_trade_pnl_history_file = _heod.generate_trade_pnl_history_file
generate_historical_eod_series = _heod.generate_historical_eod_series


def _write_eod(eod_dir, eod_id, date_str, gauge_id='GAUGE-001'):
    """Write a minimal EOD snapshot with hazard term structure."""
    snapshot = {
        'eod_id': eod_id,
        'date': date_str,
        'market_state_snapshot': {
            'hazard_term_structure': {
                gauge_id: {
                    'severe': {'1': 0.03, '2': 0.04, '3': 0.05},
                    'warning': {'1': 0.08, '2': 0.09, '3': 0.10},
                }
            }
        },
        'positions': [],
        'portfolio_summary': {},
    }
    path = eod_dir / f'{eod_id}.json'
    path.write_text(json.dumps(snapshot))
    return path


def _write_eod_with_positions(eod_dir, eod_id, date_str, swap_id='PRS-001'):
    """Write a minimal EOD snapshot that contains a position."""
    snapshot = {
        'eod_id': eod_id,
        'date': date_str,
        'market_state_snapshot': {'hazard_term_structure': {}},
        'positions': [
            {
                'swap_id': swap_id,
                'trade_date': date_str,
                'trade_spread_bps': 200.0,
                'gauge_id': 'GAUGE-001',
                'trigger': 'severe',
                'notional': 10_000_000,
                'is_payer': True,
                'fair_spread_bps': 205.0,
                'market_pnl': 1200.0,
                'running_pnl': 1200.0,
            }
        ],
        'portfolio_summary': {},
    }
    (eod_dir / f'{eod_id}.json').write_text(json.dumps(snapshot))


def _make_gaugehc(input_dir, gauge_id='GAUGE-001'):
    """Write a minimal gaugehc.json understood by MarketStateManager."""
    data = {
        'hazard_curves': {
            gauge_id: {
                'gauge_id': gauge_id,
                'gauge_name': 'Test Gauge',
                'flood_alert_m': 4.5,
                'flood_warning_m': 5.0,
                'flood_severe_m': 5.5,
                'annual_flood_prob_severe': 0.03,
                'annual_hazard_rate_alert': 0.10,
                'annual_hazard_rate_warning': 0.06,
                'annual_hazard_rate_severe': 0.03,
                'term_structure_severe': [
                    {'year': 1, 'cum_prob': 0.03},
                    {'year': 2, 'cum_prob': 0.06},
                    {'year': 3, 'cum_prob': 0.09},
                ],
            }
        }
    }
    (input_dir / 'gaugehc.json').write_text(json.dumps(data))


def _make_trade(swap_id='PRS-TEST-001', gauge_id='GAUGE-001'):
    """Return a minimal trade dict matching PRS CDM structure."""
    return {
        'PhysicalSwap': {
            'Header': {
                'SwapID': swap_id,
                'TradeDate': '2026-01-01',
                'ValuationDate': '2026-01-01',
                'TradeStatus': 'Open',
            },
            'LegData': {'Notional': 10_000_000, 'Payer': True, 'Currency': 'GBP'},
            'ScheduleData': {'StartDate': '2026-01-01', 'EndDate': '2028-01-01'},
            'Pricing': {'SpreadBps': 200.0, 'TriggerLevel': 'severe', 'Recovery': 0.0},
            'GaugeSet': {'GaugeBasket': [{'GaugeID': gauge_id, 'Weight': 1.0}]},
            'Counterparty': {'Name': 'TestBank', 'CounterpartyID': 'CP-001'},
        }
    }
