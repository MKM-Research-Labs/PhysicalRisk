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

"""
Test data constants and factory functions for trading route tests — Part 2.

Provides:
- 16 sample PRS trades across 7 gauges
- Portfolio stress storm definitions
- Single-gauge stress constants
"""

from ._data_part1 import (
    GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH,
    GAUGE_VAUXHALL, GAUGE_WATERLOO, GAUGE_BLACKFRIARS, GAUGE_LONDON,
    make_trade,
)


# =============================================================================
# Test Trades — 16 trades across 7 Thames Central gauges
# =============================================================================

CORE_TRADES = [
    make_trade('PRS-TEST-001', GAUGE_WESTMINSTER, 'Thames at Westminster',
               is_payer=True, spread_bps=200.0, tenor=3, notional=10_000_000),
    make_trade('PRS-TEST-002', GAUGE_WESTMINSTER, 'Thames at Westminster',
               is_payer=False, spread_bps=210.0, tenor=5, notional=8_000_000),
    make_trade('PRS-TEST-003', GAUGE_CHELSEA, 'Thames at Chelsea',
               is_payer=True, spread_bps=250.0, tenor=2, notional=5_000_000),
    make_trade('PRS-TEST-LAMBETH', GAUGE_LAMBETH, 'Thames Lambeth Bridge',
               is_payer=True, spread_bps=280.0, tenor=5, notional=7_500_000),
]

EXTENDED_TRADES = [
    make_trade('PRS-VAUXHALL-001', GAUGE_VAUXHALL, 'Thames Vauxhall Bridge',
               is_payer=True, spread_bps=220.0, tenor=5, notional=10_000_000),
    make_trade('PRS-VAUXHALL-002', GAUGE_VAUXHALL, 'Thames Vauxhall Bridge',
               is_payer=False, spread_bps=230.0, tenor=3, notional=8_000_000),
    make_trade('PRS-VAUXHALL-003', GAUGE_VAUXHALL, 'Thames Vauxhall Bridge',
               is_payer=True, spread_bps=210.0, tenor=1, notional=5_000_000),
    make_trade('PRS-WATERLOO-001', GAUGE_WATERLOO, 'Thames Waterloo Bridge',
               is_payer=True, spread_bps=225.0, tenor=3, notional=8_000_000),
    make_trade('PRS-WATERLOO-002', GAUGE_WATERLOO, 'Thames Waterloo Bridge',
               is_payer=False, spread_bps=235.0, tenor=5, notional=10_000_000),
    make_trade('PRS-WATERLOO-003', GAUGE_WATERLOO, 'Thames Waterloo Bridge',
               is_payer=True, spread_bps=215.0, tenor=2, notional=5_000_000),
    make_trade('PRS-BLACKFRIARS-001', GAUGE_BLACKFRIARS, 'Thames Blackfriars Bridge',
               is_payer=True, spread_bps=218.0, tenor=5, notional=8_000_000),
    make_trade('PRS-BLACKFRIARS-002', GAUGE_BLACKFRIARS, 'Thames Blackfriars Bridge',
               is_payer=False, spread_bps=228.0, tenor=2, notional=5_000_000),
    make_trade('PRS-BLACKFRIARS-003', GAUGE_BLACKFRIARS, 'Thames Blackfriars Bridge',
               is_payer=True, spread_bps=205.0, tenor=1, notional=5_000_000),
    make_trade('PRS-LONDON-001', GAUGE_LONDON, 'Thames London Bridge',
               is_payer=True, spread_bps=195.0, tenor=5, notional=12_000_000),
    make_trade('PRS-LONDON-002', GAUGE_LONDON, 'Thames London Bridge',
               is_payer=False, spread_bps=205.0, tenor=3, notional=8_000_000),
    make_trade('PRS-LONDON-003', GAUGE_LONDON, 'Thames London Bridge',
               is_payer=True, spread_bps=185.0, tenor=2, notional=6_000_000),
]

ALL_TRADES = CORE_TRADES + EXTENDED_TRADES
TOTAL_TRADES = len(ALL_TRADES)  # 16


# =============================================================================
# Portfolio Stress Constants
# =============================================================================

STORM_PORT_SEVERE = 'STORM-c9d0e1f2'
STORM_PORT_ALERT  = 'STORM-a3b4c5d6'

# =============================================================================
# Single-Gauge Stress Constants (used by stress_routes split tests)
# =============================================================================

STORM_SEVERE = 'STORM-a1b2c3d4'   # severe: Westminster peaked > flood_severe_m
STORM_WARNING = 'STORM-e5f6a7b8'  # warning: Westminster warning threshold only

SAMPLE_STRESS_STORMS = {
    'metadata': {'generated': '2026-01-01'},
    'storms': [
        {
            'storm_id': STORM_SEVERE,
            'name': 'Test Storm Alpha',
            'intensity_category': 'severe',
            'duration_hours': 24,
            'peak_position': 0.4,
            'trigger_summary': {'max_trigger': 'severe'},
            'gauge_responses': [
                {
                    'gauge_id': 'GAUGE-001',
                    'base_level_m': 3.0,
                    'peak_level_m': 6.0,
                    'level_change_m': 3.0,
                    'exceeded_alert': True,
                    'exceeded_warning': True,
                    'exceeded_severe': True,
                },
            ],
        },
        {
            'storm_id': STORM_WARNING,
            'name': 'Test Storm Beta',
            'intensity_category': 'moderate',
            'duration_hours': 18,
            'peak_position': 0.5,
            'trigger_summary': {'max_trigger': 'warning'},
            'gauge_responses': [
                {
                    'gauge_id': 'GAUGE-001',
                    'base_level_m': 3.0,
                    'peak_level_m': 5.2,
                    'level_change_m': 2.2,
                    'exceeded_alert': True,
                    'exceeded_warning': True,
                    'exceeded_severe': False,
                },
            ],
        },
    ],
}


# =============================================================================
# Portfolio Stress Constants
# =============================================================================

SAMPLE_PORT_STRESS_STORMS = {
    'metadata': {'generated': '2026-01-01'},
    'storms': [
        {
            'storm_id': STORM_PORT_SEVERE,
            'name': 'Portfolio Storm Alpha',
            'intensity_category': 'severe',
            'duration_hours': 36,
            'peak_position': 0.4,
            'effective_precipitation_mm': 85.0,
            'trigger_summary': {
                'max_trigger': 'severe',
                'gauges_severe': 2, 'gauges_warning': 1, 'gauges_alert': 3,
            },
            'gauge_responses': [
                {'gauge_id': 'GAUGE-001', 'base_level_m': 3.0, 'peak_level_m': 6.2,
                 'level_change_m': 3.2, 'exceeded_alert': True,
                 'exceeded_warning': True, 'exceeded_severe': True},
                {'gauge_id': 'GAUGE-002', 'base_level_m': 2.5, 'peak_level_m': 3.8,
                 'level_change_m': 1.3, 'exceeded_alert': True,
                 'exceeded_warning': True, 'exceeded_severe': False},
                {'gauge_id': 'GAUGE-9042bd95', 'base_level_m': 3.5, 'peak_level_m': 5.8,
                 'level_change_m': 2.3, 'exceeded_alert': True,
                 'exceeded_warning': True, 'exceeded_severe': True},
            ],
        },
        {
            'storm_id': STORM_PORT_ALERT,
            'name': 'Portfolio Storm Beta',
            'intensity_category': 'moderate',
            'duration_hours': 18,
            'peak_position': 0.5,
            'effective_precipitation_mm': 40.0,
            'trigger_summary': {
                'max_trigger': 'alert',
                'gauges_severe': 0, 'gauges_warning': 0, 'gauges_alert': 1,
            },
            'gauge_responses': [
                {'gauge_id': 'GAUGE-001', 'base_level_m': 3.0, 'peak_level_m': 4.8,
                 'level_change_m': 1.8, 'exceeded_alert': True,
                 'exceeded_warning': False, 'exceeded_severe': False},
            ],
        },
    ],
}
