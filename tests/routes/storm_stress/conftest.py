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

"""Shared storm data and integration fixture for storm/stress integration tests."""

import json
import math
import pytest


SHARED_STORM_DATA = {
    'metadata': {'generated': '2026-03-01'},
    'storms': [
        {
            'storm_id': 'STORM-SEVERE-001',
            'name': 'Severe Storm Alpha',
            'intensity_category': 'severe',
            'duration_hours': 36,
            'peak_position': 0.4,
            'effective_precipitation_mm': 120.0,
            'trigger_summary': {
                'max_trigger': 'severe',
                'gauges_severe': 3,
                'gauges_warning': 2,
                'gauges_alert': 5,
            },
            'gauge_responses': [{
                'gauge_id': 'GAUGE-001',
                'base_level_m': 3.0,
                'peak_level_m': 6.5,
                'level_change_m': 3.5,
                'exceeded_alert': True,
                'exceeded_warning': True,
                'exceeded_severe': True,
            }],
        },
        {
            'storm_id': 'STORM-MODERATE-002',
            'name': 'Moderate Storm Beta',
            'intensity_category': 'moderate',
            'duration_hours': 18,
            'peak_position': 0.5,
            'effective_precipitation_mm': 55.0,
            'trigger_summary': {
                'max_trigger': 'warning',
                'gauges_severe': 0,
                'gauges_warning': 1,
                'gauges_alert': 2,
            },
            'gauge_responses': [{
                'gauge_id': 'GAUGE-001',
                'base_level_m': 3.0,
                'peak_level_m': 4.8,
                'level_change_m': 1.8,
                'exceeded_alert': True,
                'exceeded_warning': True,
                'exceeded_severe': False,
            }],
        },
    ],
}


@pytest.fixture
def integration_env(tmp_path, monkeypatch):
    """Full integration environment with stress_storms.json, gauge data,
    gaugehc.json, and PRS trades."""
    from config import config

    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    trading_dir = output_dir / 'trading'
    trading_dir.mkdir()
    eod_dir = trading_dir / 'eod'
    eod_dir.mkdir()
    prs_dir = output_dir / 'prs'
    prs_dir.mkdir()
    gaugets_dir = input_dir / 'gaugets'
    gaugets_dir.mkdir()
    # Default gaugets file for GAUGE-001 — stress scenarios require real
    # timeseries data (no synthetic fallback)
    _default_readings = [
        {"hour": h, "waterLevel": round(2.0 + 3.5 * math.sin(math.pi * h / 84), 4)}
        for h in range(168)
    ]
    (gaugets_dir / 'GAUGE-001.json').write_text(json.dumps({
        "flood_simulation": {"readings": _default_readings},
    }))
    gaugehd_dir = input_dir / 'gaugehd'
    gaugehd_dir.mkdir()

    # Write stress_storms/ directory with per-storm files + _index.json
    ss_dir = input_dir / 'stress_storms'
    ss_dir.mkdir()
    index_entries = []
    for storm in SHARED_STORM_DATA['storms']:
        (ss_dir / f"{storm['storm_id']}.json").write_text(json.dumps(storm))
        gauge_ids_alert = [
            r['gauge_id'] for r in storm.get('gauge_responses', [])
            if r.get('exceeded_alert')
        ]
        entry = {k: v for k, v in storm.items() if k != 'gauge_responses'}
        entry['gauge_ids_alert'] = gauge_ids_alert
        index_entries.append(entry)
    (ss_dir / '_index.json').write_text(json.dumps({
        'total_storms': len(SHARED_STORM_DATA['storms']),
        'storms': index_entries,
    }))

    gaugehc = {'hazard_curves': {'GAUGE-001': {
        'gauge_id': 'GAUGE-001',
        'gauge_name': 'Thames at Westminster',
        'latitude': 51.5007,
        'longitude': -0.1246,
        'flood_alert_m': 4.5,
        'flood_warning_m': 5.0,
        'severe_flood_warning_m': 5.5,
    }}}
    (input_dir / 'gaugehc.json').write_text(json.dumps(gaugehc))

    gauge_data = {'flood_gauges': [{'FloodGauge': {
        'GaugeID': 'GAUGE-001',
        'GaugeName': 'Thames at Westminster',
        'Location': {'Latitude': 51.5007, 'Longitude': -0.1246},
    }}]}
    (input_dir / 'gauge.json').write_text(json.dumps(gauge_data))
    (input_dir / 'property.json').write_text(json.dumps({'properties': []}))

    trade = {'PhysicalSwap': {
        'Header': {
            'SwapID': 'PRS-INT-001',
            'ValuationDate': '2026-03-01',
            'TradeDate': '2025-01-01',
            'TradeStatus': 'Open',
        },
        'LegData': {'Notional': 5_000_000, 'Payer': True, 'Currency': 'GBP'},
        'ScheduleData': {
            'StartDate': '2025-01-01', 'EndDate': '2028-01-01',
            'PaymentFrequency': 'Semi-Annual',
        },
        'Pricing': {'SpreadBps': 200.0, 'TriggerLevel': 'severe', 'Recovery': 0.0},
        'GaugeSet': {'GaugeBasket': [
            {'GaugeID': 'GAUGE-001', 'GaugeName': 'Westminster', 'Weight': 1.0}
        ]},
        'Counterparty': {'Name': 'Test Bank', 'CounterpartyID': 'CP-001'},
    }}
    (prs_dir / 'PRS-INT-001.json').write_text(json.dumps(trade))

    monkeypatch.setattr(config, 'get_input_dir', lambda: input_dir)
    monkeypatch.setattr(config, 'get_input_path', lambda f: input_dir / f)
    monkeypatch.setattr(config, 'get_trading_dir', lambda: trading_dir)
    monkeypatch.setattr(config, 'get_eod_dir', lambda: eod_dir)
    monkeypatch.setattr(config, 'get_reports_dir',
                        lambda subdir=None: (output_dir / subdir) if subdir else output_dir)
    monkeypatch.setattr(config, 'get_gaugets_dir', lambda: gaugets_dir)
    monkeypatch.setattr(config, 'get_gaugehd_dir', lambda: gaugehd_dir)
    monkeypatch.setattr(config, 'get_output_dir', lambda: output_dir)

    import routes.trading.stress._helpers as stress_helpers
    stress_helpers._stress_index_cache = None

    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    return {
        'client': client,
        'input_dir': input_dir,
        'gaugets_dir': gaugets_dir,
    }
