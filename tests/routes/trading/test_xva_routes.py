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

"""XVA endpoints and their wiring into the blotter and EOD (MKM-XV-001, WP4).

Runs use 200 paths: these tests check the plumbing, not the numbers, which
the model's own suite (tests/models/xva) covers.
"""

import json
from datetime import date, timedelta

import pytest

PATHS = 200
API = '/api/v1/trading'


def _run(client):
    resp = client.post(f'{API}/xva/run', json={'n_paths': PATHS})
    assert resp.status_code == 200
    return json.loads(resp.data)


class TestRunAndRead:

    def test_nothing_before_the_first_run(self, trading_client, trading_env):
        data = json.loads(trading_client.get(f'{API}/xva').data)
        assert data['status'] == 'empty'

    def test_run_is_stored_and_read_back(self, trading_client, trading_env):
        run = _run(trading_client)
        assert run['status'] == 'success'
        assert run['summary']['n_trades'] > 0
        assert run['audit']['n_paths'] == PATHS
        latest = json.loads(trading_client.get(f'{API}/xva').data)
        assert latest['as_of'] == run['as_of']
        assert latest['summary'] == run['summary']

    def test_run_error_is_a_500(self, trading_client, trading_env, monkeypatch):
        import routes.trading.xva as xva_routes
        monkeypatch.setattr(xva_routes, 'run_and_save',
                            lambda n=None: (_ for _ in ()).throw(RuntimeError('boom')))
        assert trading_client.post(f'{API}/xva/run', json={}).status_code == 500


class TestBlotter:

    def test_blotter_shows_the_stored_run(self, trading_client, trading_env):
        before = json.loads(trading_client.get(f'{API}/blotter').data)
        assert all(t['xva'] is None for t in before['trades'])
        assert before['summary']['xva_as_of'] is None

        run = _run(trading_client)
        after = json.loads(trading_client.get(f'{API}/blotter').data)
        by_swap = {t['swap_id']: t for t in run['trades']}
        shown = [t for t in after['trades'] if t['swap_id'] in by_swap]
        assert shown and all(t['xva'] == by_swap[t['swap_id']]['xva'] for t in shown)
        assert after['summary']['xva_total'] == run['summary']['xva_total']


class TestQuote:

    def _terms(self, **kw):
        terms = {'gauge_id': 'GAUGE-WM-001', 'trigger': 'severe', 'notional': 5e6,
                 'trade_spread_bps': 120.0, 'is_payer': False, 'counterparty_id': 'CP-NEW',
                 'maturity': (date.today() + timedelta(days=730)).isoformat(),
                 'n_paths': PATHS}
        terms.update(kw)
        return terms

    def test_quote(self, trading_client, trading_env):
        data = json.loads(trading_client.post(f'{API}/xva/quote', json=self._terms()).data)
        assert data['status'] == 'success'
        assert {'incremental_xva', 'incremental_kva', 'xva_spread_bps'} <= set(data)

    def test_missing_fields(self, trading_client, trading_env):
        resp = trading_client.post(f'{API}/xva/quote', json={'gauge_id': 'G'})
        assert resp.status_code == 400
        assert 'notional' in json.loads(resp.data)['message']

    def test_matured_trade(self, trading_client, trading_env):
        resp = trading_client.post(f'{API}/xva/quote',
                                   json=self._terms(maturity=date.today().isoformat()))
        assert resp.status_code == 400

    def test_unexpected_error_is_a_500(self, trading_client, trading_env, monkeypatch):
        import routes.trading.xva as xva_routes
        monkeypatch.setattr(xva_routes, 'xva_inputs',
                            lambda: (_ for _ in ()).throw(RuntimeError('boom')))
        assert trading_client.post(f'{API}/xva/quote', json=self._terms()).status_code == 500


class TestEod:

    def _eod(self, client, day):
        return json.loads(client.post(f'{API}/eod', json={
            'date': day, 'xva': True, 'xva_paths': PATHS}).data)

    def test_eod_stores_xva_with_its_own_pnl_line(self, trading_client, trading_env):
        first = self._eod(trading_client, '2026-02-27')
        assert 'xva_total' in first['summary'] and first['summary']['xva_pnl'] is None
        snapshot = json.loads((trading_env['eod_dir'] / 'EOD-20260227.json').read_text())
        assert snapshot['xva']['audit']['model_id'] == 'MKM-XV-001'

        second = self._eod(trading_client, '2026-02-28')
        assert second['summary']['xva_pnl'] == pytest.approx(
            second['summary']['xva_total'] - first['summary']['xva_total'])
        # Kept out of the market P&L explain.
        assert second['summary']['total_daily_pnl'] == pytest.approx(
            second['summary']['daily_pnl_from_trades'] + second['summary']['daily_pnl_from_market'])

    def test_history_carries_the_xva_tiles(self, trading_client, trading_env):
        """The EOD screen's XVA tiles read these; an EOD without XVA has None."""
        trading_client.post(f'{API}/eod', json={'date': '2026-02-26', 'xva': False})
        self._eod(trading_client, '2026-02-27')
        history = json.loads(trading_client.get(f'{API}/eod/history').data)['history']
        by_date = {h['date']: h for h in history}
        assert by_date['2026-02-26']['xva_total'] is None
        assert by_date['2026-02-27']['xva_total'] is not None
        assert by_date['2026-02-27']['kva_total'] < 0
        assert by_date['2026-02-27']['xva_pnl'] is None

    def test_eod_survives_an_xva_failure(self, trading_client, trading_env, monkeypatch):
        import routes.trading.xva as xva_routes
        monkeypatch.setattr(xva_routes, 'run_and_save',
                            lambda n=None: (_ for _ in ()).throw(RuntimeError('boom')))
        data = self._eod(trading_client, '2026-02-27')
        assert data['status'] == 'success' and 'xva_total' not in data['summary']

    def test_off_by_default_in_route_tests(self, trading_client, trading_env):
        data = json.loads(trading_client.post(f'{API}/eod', json={'date': '2026-02-27'}).data)
        assert 'xva_total' not in data['summary']


class TestHazardCurves:
    """Plan §16: the route bootstraps one curve per gauge from the market state."""

    def _state(self, hts):
        return {"yield_curve": {}, "risk_free_rate": 0.03, "hazard_term_structure": hts,
                "base_rates": {"G-FLAT": {"annual_hazard_rate_severe": 0.02}}}

    def _lookup(self, monkeypatch, hts):
        import routes.trading.xva as xva_routes
        from models.trading.market_state import MarketStateManager
        monkeypatch.setattr(MarketStateManager, "load", lambda self: self_state)
        self_state = self._state(hts)
        monkeypatch.setattr(xva_routes, "_load_open_trades", lambda: [])
        return xva_routes.xva_inputs()[3]

    def test_buckets_become_a_curve_and_flat_gauges_stay_flat(self, trading_env, monkeypatch):
        from models.xva import HazardCurve
        hazard_for = self._lookup(monkeypatch, {
            "G-TS": {"severe": {"1": 0.010, "3": 0.015, "5": 0.014}}})
        curve = hazard_for("G-TS", "severe")
        assert isinstance(curve, HazardCurve) and len(curve.rates) == 3
        assert hazard_for("G-TS", "severe") is curve          # bootstrapped once
        assert hazard_for("G-FLAT", "severe") == 0.02
        assert hazard_for.fallbacks == []

    def test_a_fallback_is_recorded(self, trading_env, monkeypatch):
        hazard_for = self._lookup(monkeypatch, {"G-BAD": {"severe": {"1": 0.20, "2": 0.01}}})
        hazard_for("G-BAD", "severe")
        assert hazard_for.fallbacks == ["G-BAD"]

    def test_the_run_records_fallbacks(self, trading_client, trading_env):
        run = json.loads(trading_client.post(f'{API}/xva/run', json={'n_paths': PATHS}).data)
        assert run["audit"]["hazard_curve_fallbacks"] == []
