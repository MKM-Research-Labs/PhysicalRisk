"""Tests for client blotter Trader perspective fields (Phase 1)."""

import json
from datetime import date, timedelta

import pytest


def _make_property_prs(swap_id, gauge_id, property_id, notional,
                       spread_bps=150.0, property_value=500_000):
    """Create a PropertyPRS trade with PropertySet."""
    today = date.today().isoformat()
    end = (date.today() + timedelta(days=365 * 5)).isoformat()
    return {
        'PhysicalSwap': {
            'Header': {
                'SwapID': swap_id,
                'TradeType': 'PropertyPRS',
                'CounterParty': 'REIT-001',
                'CounterPartyName': 'Thames REIT plc',
                'ValuationDate': today,
                'TradeStatus': 'Committed',
            },
            'LegData': {
                'Notional': notional,
                'Payer': True,
                'Currency': 'GBP',
            },
            'ScheduleData': {
                'StartDate': today,
                'EndDate': end,
                'Tenor': '6M',
            },
            'Pricing': {
                'SpreadBps': spread_bps,
                'FairSpreadBps': spread_bps + 10,
                'NPV': -5000.0,
                'RiskyAnnuity': 4.5,
                'TriggerLevel': 'severe',
            },
            'GaugeSet': {
                'GaugeBasket': [{
                    'GaugeID': gauge_id,
                    'GaugeName': f'Gauge {gauge_id}',
                    'Weight': 1.0,
                }]
            },
            'PropertySet': {
                'PropertyID': property_id,
                'PropertyAddress': '10 River Lane',
                'Postcode': 'SW1A 1AA',
                'PropertyValue': property_value,
                'LocalAuthority': 'Westminster',
            },
        }
    }


@pytest.fixture
def client_env(tmp_path, monkeypatch):
    """Minimal environment with PropertyPRS trades."""
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    prs_dir = output_dir / 'prs'
    prs_dir.mkdir()

    from config import config
    monkeypatch.setattr(config, 'get_input_dir', lambda: input_dir)
    monkeypatch.setattr(config, 'get_input_path',
                        lambda f: input_dir / f)
    monkeypatch.setattr(config, 'get_reports_dir',
                        lambda subdir=None: (output_dir / subdir) if subdir else output_dir)

    trades = [
        _make_property_prs('PRS-PROP-001', 'G-001', 'PROP-001',
                           10_000_000, spread_bps=120.0,
                           property_value=800_000),
        _make_property_prs('PRS-PROP-002', 'G-002', 'PROP-002',
                           5_000_000, spread_bps=180.0,
                           property_value=600_000),
    ]
    for t in trades:
        sid = t['PhysicalSwap']['Header']['SwapID']
        (prs_dir / f'{sid}.json').write_text(json.dumps(t))

    return {'prs_dir': prs_dir, 'trades': trades}


@pytest.fixture
def client_app(client_env):
    """Flask test client with trading blueprint."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


class TestTraderPerspective:
    """Verify Trader perspective fields on client endpoint."""

    def test_trader_direction_always_rcv(self, client_env, client_app):
        resp = client_app.get('/api/v1/trading/client')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'success'

        for trade in data['trades']:
            assert trade['trader_direction'] == 'Rcv', \
                f"Trade {trade['swap_id']} should have trader_direction='Rcv'"

    def test_property_value_returned(self, client_env, client_app):
        resp = client_app.get('/api/v1/trading/client')
        data = resp.get_json()

        by_id = {t['swap_id']: t for t in data['trades']}
        assert by_id['PRS-PROP-001']['property_value'] == 800_000
        assert by_id['PRS-PROP-002']['property_value'] == 600_000

    def test_hedge_ratio_computed(self, client_env, client_app):
        resp = client_app.get('/api/v1/trading/client')
        data = resp.get_json()

        by_id = {t['swap_id']: t for t in data['trades']}
        # 10M / 800k = 1250%
        assert by_id['PRS-PROP-001']['hedge_ratio'] == 1250.0
        # 5M / 600k ≈ 833.3%
        assert by_id['PRS-PROP-002']['hedge_ratio'] == 833.3

    def test_trader_summary_present(self, client_env, client_app):
        resp = client_app.get('/api/v1/trading/client')
        data = resp.get_json()

        ts = data['trader_summary']
        assert ts['num_trades'] == 2
        assert ts['total_notional_sold'] == 15_000_000
        assert ts['total_property_value_covered'] == 1_400_000
        assert ts['avg_spread_collected'] == 150.0  # (120 + 180) / 2

    def test_no_property_prs_returns_empty(self, tmp_path, monkeypatch):
        """When no PropertyPRS trades exist, returns empty with zero summaries."""
        input_dir = tmp_path / 'input'
        input_dir.mkdir()
        output_dir = tmp_path / 'output'
        output_dir.mkdir()
        prs_dir = output_dir / 'prs'
        prs_dir.mkdir()

        from config import config
        monkeypatch.setattr(config, 'get_input_dir', lambda: input_dir)
        monkeypatch.setattr(config, 'get_reports_dir',
                            lambda subdir=None: (output_dir / subdir) if subdir else output_dir)

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        resp = client.get('/api/v1/trading/client')
        data = resp.get_json()
        assert data['status'] == 'success'
        assert data['trades'] == []
        assert data['trader_summary']['num_trades'] == 0
        assert data['trader_summary']['total_notional_sold'] == 0
        assert data['trader_summary']['avg_spread_collected'] == 0
