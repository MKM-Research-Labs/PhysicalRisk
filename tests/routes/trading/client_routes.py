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

"""Tests for the client (property PRS) blotter endpoint."""

import json

import pytest


def _make_pprs_trade(swap_id, property_id, property_address, postcode,
                     notional, is_payer=False, spread_bps=300.0):
    """Create a minimal PPRS trade JSON structure."""
    return {
        'PhysicalSwap': {
            'Header': {
                'SwapID': swap_id,
                'CatchmentID': 'thames',
                'TradeType': 'PropertyPRS',
                'CounterParty': 'CTPY-test-001',
                'CounterPartyName': 'Test Insurer (AA)',
                'PartyId': 'MKM-RESEARCH-001',
                'ValuationDate': '2026-04-07',
                'ProtectionStart': '2026-04-09',
                'TradeStatus': 'Committed',
            },
            'LegData': {
                'LegType': 'Fixed',
                'Payer': is_payer,
                'Currency': 'GBP',
                'Notional': notional,
                'DayCounter': 'ACT/360',
                'FixedLegRate': 0.035,
            },
            'ScheduleData': {
                'StartDate': '2026-04-09',
                'EndDate': '2029-04-09',
                'Tenor': '6M',
                'Calendar': 'London',
            },
            'PropertySet': {
                'PropertyID': property_id,
                'PropertyAddress': property_address,
                'Postcode': postcode,
                'LocalAuthority': 'Westminster',
                'PropertyValue': 1000000.0,
                'EAFloodZone': 'Zone 3a',
                'ReferenceGauge': 'SYNTH-test-001',
                'Latitude': 51.49,
                'Longitude': -0.13,
            },
            'GaugeSet': {
                'GaugeSetID': f'GSET-{property_id}',
                'CatchmentID': 'thames',
                'GaugeCount': 1,
                'GaugeBasket': [{
                    'GaugeID': 'SYNTH-test-001',
                    'GaugeName': 'Test Synthetic',
                    'Weight': 1.0,
                    'TriggerLevel': 'severe',
                }],
            },
            'Triggers': {'TriggerType': 'Any', 'TriggerThreshold': 1},
            'Payouts': {'Currency': 'GBP', 'MaxPayout': notional},
            'Pricing': {
                'SpreadBps': spread_bps,
                'FairSpreadBps': spread_bps - 5.0,
                'NPV': 50000.0,
                'PremiumLegPV': 500000.0,
                'ProtectionLegPV': 450000.0,
                'RiskyAnnuity': 2.5,
                'YieldCurve': {'1': 0.035, '2': 0.04, '3': 0.043},
                'Recovery': 0.0,
                'TriggerLevel': 'severe',
            },
        }
    }


SAMPLE_PPRS_TRADES = [
    _make_pprs_trade('PRS-PTEST001', 'PROP-aaa11111',
                     '10 Test Street', 'SW1 1AA', 50_000_000),
    _make_pprs_trade('PRS-PTEST002', 'PROP-bbb22222',
                     '20 Mock Road', 'W1 2BB', 100_000_000, is_payer=True),
    _make_pprs_trade('PRS-PTEST003', 'PROP-ccc33333',
                     '30 Sample Lane', 'SW1 3CC', 75_000_000, spread_bps=420.0),
]


@pytest.fixture
def client_env(trading_env):
    """Add PPRS trade files to the existing trading env."""
    prs_dir = trading_env['prs_dir']
    for t in SAMPLE_PPRS_TRADES:
        sid = t['PhysicalSwap']['Header']['SwapID']
        with open(prs_dir / f'{sid}.json', 'w') as f:
            json.dump(t, f)
    return trading_env


@pytest.fixture
def client_client(client_env):
    """Flask test client with property PRS trades available."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


class TestGetClientBlotter:
    """GET /trading/client endpoint tests."""

    def test_returns_success(self, client_client, client_env):
        resp = client_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'

    def test_returns_property_trades_only(self, client_client, client_env):
        """Should return property PRS trades (those with PropertySet), not gauge trades."""
        resp = client_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        trades = data['trades']
        assert len(trades) == 3

    def test_has_property_fields(self, client_client, client_env):
        """Each trade must have property-specific fields."""
        resp = client_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        for t in data['trades']:
            assert 'property_id' in t
            assert 'property_address' in t
            assert 'postcode' in t
            assert 'local_authority' in t
            assert 'ea_flood_zone' in t

    def test_has_trade_fields(self, client_client, client_env):
        """Each trade must have standard trade identification fields."""
        resp = client_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        for t in data['trades']:
            assert 'swap_id' in t
            assert 'counterparty' in t
            assert 'notional' in t
            assert 'is_payer' in t
            assert 'currency' in t
            assert 'spread_bps' in t
            assert 'fair_spread_bps' in t
            assert 'npv' in t

    def test_has_summary(self, client_client, client_env):
        """Response must include summary with trade count and total notional."""
        resp = client_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        summary = data['summary']
        assert summary['num_trades'] == 3
        assert summary['total_notional'] == 225_000_000

    def test_empty_when_no_pprs_trades(self, trading_client, trading_env):
        """Returns empty trades list when no PPRS files exist."""
        resp = trading_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert len(data['trades']) == 0

    def test_does_not_include_gauge_prs(self, client_client, client_env):
        """Gauge PRS trades (without PropertySet) must NOT appear in client blotter."""
        resp = client_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        for t in data['trades']:
            assert t['trade_type'] == 'PropertyPRS', \
                f"Gauge trade {t['swap_id']} should not appear in client blotter"

    def test_payer_receiver_direction(self, client_client, client_env):
        """is_payer field should match the trade direction."""
        resp = client_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        by_id = {t['swap_id']: t for t in data['trades']}
        assert by_id['PRS-PTEST001']['is_payer'] is False
        assert by_id['PRS-PTEST002']['is_payer'] is True

    def test_trade_type_is_property_prs(self, client_client, client_env):
        """trade_type field should be PropertyPRS for all trades."""
        resp = client_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        for t in data['trades']:
            assert t['trade_type'] == 'PropertyPRS'

    def test_fs01_computed(self, client_client, client_env):
        """Each trade must have gauge_fs01 computed from notional * risky_annuity."""
        resp = client_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        for t in data['trades']:
            assert 'gauge_fs01' in t
            assert t['gauge_fs01'] != 0

    def test_fs01_sign_matches_direction(self, client_client, client_env):
        """Payer FS01 positive, receiver FS01 negative."""
        resp = client_client.get('/api/v1/trading/client')
        data = json.loads(resp.data)
        for t in data['trades']:
            if t['is_payer']:
                assert t['gauge_fs01'] > 0, \
                    f"Payer {t['swap_id']} should have positive FS01"
            else:
                assert t['gauge_fs01'] < 0, \
                    f"Receiver {t['swap_id']} should have negative FS01"
