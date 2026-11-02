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

"""Storm payouts on the REIT hedges and the desk's net position."""

import pytest
from db_helpers import tmp_catchment

import database
from models.trading import storm_hedges
from models.trading.storm_hedges import storm_hedge_report, storms_in

_CATCHMENT = "thames"
SEQ = "STORM-seq1"  # a two-storm sequence: STORM-a then STORM-b


@pytest.fixture(autouse=True)
def _seam_backend(tmp_path):
    with tmp_catchment(tmp_path, _CATCHMENT):
        database.save_storm_sequences(_CATCHMENT, {'sequences': [{
            'sequence_id': SEQ,
            'storms': [{'storm_id': 'STORM-a'}, {'storm_id': 'STORM-b'}],
        }]})
        yield


def _gauge(gauge_id, severe_in, peaks=None):
    """Gauge reaching severe in ``severe_in``; other storms stay below."""
    peaks = peaks or {}
    database.save_gauge_timeseries(_CATCHMENT, gauge_id, {
        'gauge_id': gauge_id,
        'storm_responses': {'responses': [
            {'storm_id': sid, 'peak_level_m': peaks.get(sid, 1.0),
             'exceeded_severe': sid in severe_in}
            for sid in ('STORM-a', 'STORM-b', 'STORM-c')
        ]},
    })


def _trade(swap_id, gauge_id, notional, trade_type='PropertyPRS', payer=True,
           asset_id='', purpose=''):
    header = {'SwapID': swap_id, 'TradeType': trade_type, 'CounterPartyName': 'X'}
    if purpose:
        header['TradePurpose'] = purpose
    record = {'PhysicalSwap': {
        'Header': header,
        'LegData': {'Notional': notional, 'Payer': payer},
        'GaugeSet': {'GaugeBasket': [{'GaugeID': gauge_id, 'GaugeName': gauge_id}]},
    }}
    if asset_id:
        record['PhysicalSwap']['PropertySet'] = {'PropertyID': asset_id,
                                                 'PropertyValue': notional * 4}
    database.save_prs_trade(_CATCHMENT, swap_id, record)


class TestStormsIn:
    def test_sequence_expands_to_its_storms(self):
        assert storms_in(_CATCHMENT, SEQ) == ['STORM-a', 'STORM-b']

    def test_unknown_id_is_a_single_storm(self):
        assert storms_in(_CATCHMENT, 'STORM-c') == ['STORM-c']


class TestReitHedges:
    def test_pays_notional_when_gauge_reaches_severe(self):
        _gauge('G1', severe_in={'STORM-b'}, peaks={'STORM-b': 6.4})
        _trade('PRS-P1', 'G1', 500_000, asset_id='PROP-1')
        report = storm_hedge_report(_CATCHMENT, [SEQ])
        hedge = report['reit']['hedges'][0]
        assert hedge['triggered'] is True
        assert hedge['payout'] == 500_000
        assert hedge['gauge_peak_m'] == 6.4
        assert report['reit']['total_payout'] == 500_000
        assert report['desk']['paid_to_reit'] == -500_000

    def test_nothing_when_gauge_stays_below_severe(self):
        _gauge('G1', severe_in={'STORM-c'})
        _trade('PRS-P1', 'G1', 500_000, asset_id='PROP-1')
        report = storm_hedge_report(_CATCHMENT, [SEQ])
        assert report['reit']['hedges'][0]['payout'] == 0
        assert report['reit']['num_triggered'] == 0
        assert report['desk']['net'] == 0

    def test_pays_once_when_several_storms_trigger(self):
        _gauge('G1', severe_in={'STORM-a', 'STORM-b'})
        _trade('PRS-P1', 'G1', 500_000, asset_id='PROP-1')
        assert storm_hedge_report(_CATCHMENT, [SEQ])['reit']['total_payout'] == 500_000

    def test_trade_without_gauge_is_ignored(self):
        _trade('PRS-P1', '', 500_000, asset_id='PROP-1')
        assert storm_hedge_report(_CATCHMENT, [SEQ])['reit']['hedges'] == []


class TestDesk:
    def test_net_is_reit_payout_less_lay_off_and_book(self):
        _gauge('G1', severe_in={'STORM-a'})
        _gauge('G2', severe_in={'STORM-a'})
        _gauge('G3', severe_in=set())
        _trade('PRS-P1', 'G1', 1_000_000, asset_id='PROP-1')
        # lay-off: desk bought 500k back on G1
        _trade('PRS-L1', 'G1', 500_000, trade_type='PRS', payer=True, purpose='REITLayoff')
        # gauge book: desk sold 200k on G2 (pays), bought 300k on G3 (no trigger)
        _trade('PRS-B1', 'G2', 200_000, trade_type='PRS', payer=False)
        _trade('PRS-B2', 'G3', 300_000, trade_type='PRS', payer=True)

        desk = storm_hedge_report(_CATCHMENT, [SEQ])['desk']
        assert desk['paid_to_reit'] == -1_000_000
        assert desk['layoff_cash'] == 500_000
        assert desk['book_cash'] == -200_000
        assert desk['net'] == -700_000
        roles = {t['swap_id']: t['role'] for t in desk['trades']}
        assert roles == {'PRS-L1': 'layoff', 'PRS-B1': 'book', 'PRS-B2': 'book'}

    def test_desk_payer_without_lay_off_mark_is_book(self):
        """Buying protection on a REIT gauge is not a lay-off unless marked."""
        _gauge('G1', severe_in={'STORM-a'})
        _trade('PRS-P1', 'G1', 1_000_000, asset_id='PROP-1')
        _trade('PRS-B1', 'G1', 400_000, trade_type='PRS', payer=True)
        desk = storm_hedge_report(_CATCHMENT, [SEQ])['desk']
        assert desk['layoff_cash'] == 0
        assert desk['book_cash'] == 400_000


class TestLoading:
    def test_unreadable_trade_is_skipped(self, monkeypatch):
        _gauge('G1', severe_in={'STORM-a'})
        _trade('PRS-P1', 'G1', 500_000, asset_id='PROP-1')
        real_get = database.get_prs_trade

        def flaky(catchment, swap_id):
            if swap_id == 'PRS-BAD':
                raise ValueError('corrupt')
            return real_get(catchment, swap_id)

        monkeypatch.setattr(database, 'iter_prs_trade_ids',
                            lambda c: iter(['PRS-BAD', 'PRS-P1']))
        monkeypatch.setattr(database, 'get_prs_trade', flaky)
        assert [t['swap_id'] for t in storm_hedges.load_trades(_CATCHMENT)] == ['PRS-P1']

    def test_gauge_responses_are_cached(self, monkeypatch):
        _gauge('G1', severe_in={'STORM-a'})
        calls = []
        real = database.get_gauge_timeseries
        monkeypatch.setattr(database, 'get_gauge_timeseries',
                            lambda c, g: calls.append(g) or real(c, g))
        storm_hedges.gauge_storm_responses(_CATCHMENT, 'G1')
        storm_hedges.gauge_storm_responses(_CATCHMENT, 'G1')
        assert calls == ['G1']
