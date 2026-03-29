# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Test data constants and factory functions for trading route tests — Part 1.

Provides:
- Thames Central gauge IDs and hazard curve entries
- CDM trade factory (make_trade)
- Gauge hazard curve sample data (SAMPLE_GAUGEHC, SAMPLE_GAUGE_JSON)
"""

from datetime import date, timedelta


# =============================================================================
# Thames Central Test Gauge IDs
# =============================================================================

GAUGE_WESTMINSTER  = 'GAUGE-001'
GAUGE_CHELSEA      = 'GAUGE-002'
GAUGE_LAMBETH      = 'GAUGE-9042bd95'
GAUGE_VAUXHALL     = 'GAUGE-d5f2b301'
GAUGE_WATERLOO     = 'GAUGE-a8c5e604'
GAUGE_BLACKFRIARS  = 'GAUGE-b9d6f705'
GAUGE_LONDON       = 'GAUGE-ca1e8b06'

ALL_TEST_GAUGE_IDS = [
    GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH,
    GAUGE_VAUXHALL, GAUGE_WATERLOO, GAUGE_BLACKFRIARS, GAUGE_LONDON,
]


# =============================================================================
# CDM Trade Factory
# =============================================================================

def make_trade(swap_id: str, gauge_id: str, gauge_name: str,
               is_payer: bool, spread_bps: float, tenor: int,
               notional: float, trigger: str = 'severe',
               counterparty: str = 'TestBank AG',
               trade_date: str = None) -> dict:
    """Create a minimal CDM-format PRS trade dict."""
    if trade_date is None:
        trade_date = date.today().isoformat()
    end_date = (date.today() + timedelta(days=365 * tenor)).isoformat()

    return {
        'PhysicalSwap': {
            'Header': {
                'SwapID': swap_id,
                'ValuationDate': date.today().isoformat(),
                'TradeDate': trade_date,
                'TradeStatus': 'Open',
            },
            'LegData': {
                'Notional': notional,
                'Payer': is_payer,
                'Currency': 'GBP',
            },
            'ScheduleData': {
                'StartDate': trade_date,
                'EndDate': end_date,
                'PaymentFrequency': 'Semi-Annual',
            },
            'Pricing': {
                'SpreadBps': spread_bps,
                'TriggerLevel': trigger,
                'Recovery': 0.0,
            },
            'GaugeSet': {
                'GaugeBasket': [
                    {
                        'GaugeID': gauge_id,
                        'GaugeName': gauge_name,
                        'Weight': 1.0,
                    }
                ]
            },
            'Counterparty': {
                'Name': counterparty,
                'CounterpartyID': 'CP-001',
            },
        },
    }


# =============================================================================
# Helper: build a complete gaugehc entry
# =============================================================================

def make_gauge_entry(gauge_id, gauge_name, lat, lon,
                     alert_m, warning_m, severe_m,
                     rate_alert, rate_warning, rate_severe,
                     gev_loc=4.2, gev_scale=0.7, gev_shape=0.08):
    """Build a complete gaugehc dict entry with both legacy and new field names."""
    def _ts(rate):
        return [
            {'year': y,
             'cum_prob': round(1 - (1 - rate) ** y, 6),
             'survival_prob': round((1 - rate) ** y, 6)}
            for y in (1, 2, 5)
        ]

    return {
        'gauge_id': gauge_id,
        'gauge_name': gauge_name,
        'latitude': lat,
        'longitude': lon,
        'gev_location': gev_loc,
        'gev_scale': gev_scale,
        'gev_shape': gev_shape,
        'flood_alert_m': alert_m,
        'flood_warning_m': warning_m,
        'flood_severe_m': severe_m,
        'severe_flood_warning_m': severe_m,
        'annual_flood_prob_alert': rate_alert,
        'annual_flood_prob_warning': rate_warning,
        'annual_flood_prob_severe': rate_severe,
        'annual_hazard_rate_alert': rate_alert,
        'annual_hazard_rate_warning': rate_warning,
        'annual_hazard_rate_severe': rate_severe,
        'curve_points': [
            {'water_level_m': alert_m - 0.5, 'exceedance_prob': round(rate_alert * 1.5, 4)},
            {'water_level_m': warning_m, 'exceedance_prob': rate_warning},
            {'water_level_m': severe_m + 0.5, 'exceedance_prob': round(rate_severe * 0.3, 5)},
        ],
        'return_period_levels': {
            '10yr': warning_m,
            '50yr': severe_m,
            '100yr': round(severe_m + 0.5, 1),
        },
        'term_structure_alert': _ts(rate_alert),
        'term_structure_warning': _ts(rate_warning),
        'term_structure_severe': _ts(rate_severe),
    }


# =============================================================================
# Test Data Constants — 7 Thames Central Gauges
# =============================================================================

SAMPLE_GAUGEHC = {
    'metadata': {'generated': '2026-01-01', 'catchment': 'thames'},
    'hazard_curves': {
        GAUGE_WESTMINSTER: make_gauge_entry(
            GAUGE_WESTMINSTER, 'Thames at Westminster',
            lat=51.5007, lon=-0.1246,
            alert_m=4.5, warning_m=5.0, severe_m=5.5,
            rate_alert=0.15, rate_warning=0.08, rate_severe=0.03,
        ),
        GAUGE_CHELSEA: make_gauge_entry(
            GAUGE_CHELSEA, 'Thames at Chelsea',
            lat=51.4837, lon=-0.1687,
            alert_m=3.0, warning_m=3.5, severe_m=4.0,
            rate_alert=0.20, rate_warning=0.10, rate_severe=0.04,
        ),
        GAUGE_LAMBETH: make_gauge_entry(
            GAUGE_LAMBETH, 'Thames Lambeth Bridge',
            lat=51.4955, lon=-0.1193,
            alert_m=4.2, warning_m=4.8, severe_m=5.4,
            rate_alert=0.18, rate_warning=0.09, rate_severe=0.035,
        ),
        GAUGE_VAUXHALL: make_gauge_entry(
            GAUGE_VAUXHALL, 'Thames Vauxhall Bridge',
            lat=51.4853, lon=-0.1217,
            alert_m=4.0, warning_m=4.6, severe_m=5.2,
            rate_alert=0.17, rate_warning=0.085, rate_severe=0.028,
        ),
        GAUGE_WATERLOO: make_gauge_entry(
            GAUGE_WATERLOO, 'Thames Waterloo Bridge',
            lat=51.5074, lon=-0.1145,
            alert_m=4.3, warning_m=5.0, severe_m=5.3,
            rate_alert=0.16, rate_warning=0.080, rate_severe=0.030,
        ),
        GAUGE_BLACKFRIARS: make_gauge_entry(
            GAUGE_BLACKFRIARS, 'Thames Blackfriars Bridge',
            lat=51.5124, lon=-0.1040,
            alert_m=4.4, warning_m=5.1, severe_m=5.4,
            rate_alert=0.14, rate_warning=0.070, rate_severe=0.025,
        ),
        GAUGE_LONDON: make_gauge_entry(
            GAUGE_LONDON, 'Thames London Bridge',
            lat=51.5083, lon=-0.0879,
            alert_m=4.6, warning_m=5.2, severe_m=5.6,
            rate_alert=0.12, rate_warning=0.060, rate_severe=0.022,
        ),
    },
}

SAMPLE_GAUGE_JSON = {
    'flood_gauges': [
        {'FloodGauge': {'GaugeID': gid, 'GaugeName': name,
                        'Location': {'Latitude': lat, 'Longitude': lon}}}
        for gid, name, lat, lon in [
            (GAUGE_WESTMINSTER, 'Thames at Westminster', 51.5007, -0.1246),
            (GAUGE_CHELSEA, 'Thames at Chelsea', 51.4837, -0.1687),
            (GAUGE_LAMBETH, 'Thames Lambeth Bridge', 51.4955, -0.1193),
            (GAUGE_VAUXHALL, 'Thames Vauxhall Bridge', 51.4853, -0.1217),
            (GAUGE_WATERLOO, 'Thames Waterloo Bridge', 51.5074, -0.1145),
            (GAUGE_BLACKFRIARS, 'Thames Blackfriars Bridge', 51.5124, -0.1040),
            (GAUGE_LONDON, 'Thames London Bridge', 51.5083, -0.0879),
        ]
    ]
}
