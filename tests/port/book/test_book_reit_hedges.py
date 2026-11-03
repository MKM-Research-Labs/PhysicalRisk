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

"""The REIT's hedge book and the desk's lay-off of it, end to end through the
database seam (no mocks): sizing, commercial assets, gauge names, lay-offs."""

import pytest
from db_helpers import tmp_catchment

import database
from config.port import PROPERTY_BOOK_HEDGE_RATIO, PROPERTY_BOOK_LAYOFF_RATIO
from port.src.book.book_property import (
    generate_property_book,
    generate_reit_layoff_book,
)
from port.src.book.book_property._core import LAYOFF_PURPOSE, _hedge_notional
from port.src.book.book_property._select import _lookup_commercial_metadata

_CATCHMENT = "thames"


@pytest.fixture(autouse=True)
def _seam_backend(tmp_path):
    with tmp_catchment(tmp_path, _CATCHMENT):
        yield


def _curve(flood_count=30, gauge_id='GAUGE-A', spreads=(40, 60, 80, 120)):
    return {
        'flood_count': flood_count,
        'flood_zone': 'Zone 3',
        'term_structure': {'tenors': [1, 2, 3, 5],
                           'severe': {'prs_spread_bps': list(spreads)}},
        'nearest_gauges': [
            {'gauge_id': 'SYNTH-1', 'distance_km': 0.4},  # never traded
            {'gauge_id': gauge_id, 'distance_km': 1.2},
        ],
    }


def _property(pid, value):
    return {'PropertyHeader': {
        'Header': {'PropertyID': pid},
        'Location': {'BuildingNumber': '1', 'StreetName': 'River Rd',
                     'LatitudeDegrees': 51.5, 'LongitudeDegrees': -0.1},
        'Valuation': {'PropertyValue': value},
        'RiskAssessment': {'EAFloodZone': 'Zone 3'},
    }}


def _commercial(cid, value):
    return {'CommercialAsset': {
        'Header': {'PropertyID': cid},
        'Location': {'BuildingName': 'Wharf House', 'StreetName': 'Quay St',
                     'LatitudeDegrees': 51.5, 'LongitudeDegrees': -0.1},
        'Valuation': {'PropertyValue': value},
        'RiskAssessment': {'EAFloodZone': 'Zone 2'},
    }}


def _seed(properties=(), commercials=()):
    database.save_gauge_hazard_curves(_CATCHMENT, {'hazard_curves': {
        'GAUGE-A': {'gauge_name': 'Thames Alpha', 'annual_hazard_rate_severe': 0.02},
        'GAUGE-B': {'gauge_name': 'Thames Bravo', 'annual_hazard_rate_severe': 0.03},
    }})
    database.save_property_hazard_curves(_CATCHMENT, {
        'metadata': {'num_storms': 1000},
        'property_hazard_curves': {pid: _curve(gauge_id=g) for pid, _, g in properties},
    })
    database.save_properties(_CATCHMENT, {
        'properties': [_property(pid, v) for pid, v, _ in properties]})
    database.save_commercial_hazard_curves(_CATCHMENT, {
        'metadata': {'num_storms': 1000},
        'property_hazard_curves': {cid: _curve(gauge_id=g) for cid, _, g in commercials},
    })
    database.save_commercial(_CATCHMENT, {
        'commercial_assets': [_commercial(cid, v) for cid, v, _ in commercials]})


def _ps(record):
    return record['PhysicalSwap']


class TestHedgeNotional:
    def test_share_of_value_rounded_to_step(self):
        assert _hedge_notional(1_000_000) == round(1_000_000 * PROPERTY_BOOK_HEDGE_RATIO / 50_000) * 50_000

    def test_never_below_one_step(self):
        assert _hedge_notional(10_000) == 50_000


class TestCommercialMetadata:
    def test_unknown_asset_gets_only_its_id(self):
        assert _lookup_commercial_metadata([_commercial('CPROP-1', 1)], 'CPROP-9') == {
            'PropertyID': 'CPROP-9'}


class TestReitHedgeBook:
    def test_one_hedge_per_asset_sized_from_value(self, tmp_path):
        _seed(properties=[('PROP-1', 800_000, 'GAUGE-A')],
              commercials=[('CPROP-1', 40_000_000, 'GAUGE-B')])
        trades = generate_property_book(tmp_path / 'out', _CATCHMENT, seed=1)

        by_asset = {_ps(t)['PropertySet']['PropertyID']: _ps(t) for t in trades}
        assert set(by_asset) == {'PROP-1', 'CPROP-1'}
        assert by_asset['PROP-1']['LegData']['Notional'] == _hedge_notional(800_000)
        assert by_asset['CPROP-1']['LegData']['Notional'] == _hedge_notional(40_000_000)
        assert by_asset['PROP-1']['PropertySet']['AssetClass'] == 'residential'
        assert by_asset['CPROP-1']['PropertySet']['AssetClass'] == 'commercial'

    def test_reit_buys_from_the_desk_on_the_nearest_real_gauge(self, tmp_path):
        _seed(properties=[('PROP-1', 800_000, 'GAUGE-A')])
        ps = _ps(generate_property_book(tmp_path / 'out', _CATCHMENT, seed=1)[0])
        assert ps['Header']['CounterParty'] == 'CTPY-REIT-001'
        assert ps['Header']['TradeType'] == 'PropertyPRS'
        assert ps['LegData']['Payer'] is True
        gauge = ps['GaugeSet']['GaugeBasket'][0]
        assert gauge['GaugeID'] == 'GAUGE-A'
        assert gauge['GaugeName'] == 'Thames Alpha'  # resolved, not the ID

    def test_asset_without_a_value_is_not_hedged(self, tmp_path):
        _seed(properties=[('PROP-1', 0, 'GAUGE-A')])
        assert generate_property_book(tmp_path / 'out', _CATCHMENT, seed=1) == []

    def test_hedges_are_saved_to_the_book(self, tmp_path):
        _seed(properties=[('PROP-1', 800_000, 'GAUGE-A')])
        trade = generate_property_book(tmp_path / 'out', _CATCHMENT, seed=1)[0]
        swap_id = _ps(trade)['Header']['SwapID']
        assert database.get_prs_trade(_CATCHMENT, swap_id) == trade


class TestLayoffBook:
    def test_desk_buys_back_a_share_of_each_gauge(self, tmp_path):
        _seed(properties=[('PROP-1', 800_000, 'GAUGE-A'), ('PROP-2', 1_200_000, 'GAUGE-A')],
              commercials=[('CPROP-1', 40_000_000, 'GAUGE-B')])
        reit = generate_property_book(tmp_path / 'out', _CATCHMENT, seed=1)
        layoffs = generate_reit_layoff_book(reit, tmp_path / 'out', _CATCHMENT, seed=2)

        sold = {}
        for t in reit:
            g = _ps(t)['GaugeSet']['GaugeBasket'][0]['GaugeID']
            sold[g] = sold.get(g, 0) + _ps(t)['LegData']['Notional']
        by_gauge = {_ps(t)['GaugeSet']['GaugeBasket'][0]['GaugeID']: _ps(t) for t in layoffs}
        assert set(by_gauge) == {'GAUGE-A', 'GAUGE-B'}
        for g, ps in by_gauge.items():
            expected = round(sold[g] * PROPERTY_BOOK_LAYOFF_RATIO / 50_000) * 50_000
            assert ps['LegData']['Notional'] == expected
            assert ps['LegData']['Payer'] is True  # the desk buys protection
            assert ps['Header']['TradeType'] == 'PRS'
            assert ps['Header']['TradePurpose'] == LAYOFF_PURPOSE
            assert ps['Header']['CounterParty'] != 'CTPY-REIT-001'

    def test_lay_off_purpose_is_saved(self, tmp_path):
        _seed(properties=[('PROP-1', 800_000, 'GAUGE-A')])
        reit = generate_property_book(tmp_path / 'out', _CATCHMENT, seed=1)
        layoff = generate_reit_layoff_book(reit, tmp_path / 'out', _CATCHMENT, seed=2)[0]
        saved = database.get_prs_trade(_CATCHMENT, _ps(layoff)['Header']['SwapID'])
        assert saved['PhysicalSwap']['Header']['TradePurpose'] == LAYOFF_PURPOSE

    def test_nothing_to_lay_off(self, tmp_path):
        assert generate_reit_layoff_book([], tmp_path / 'out', _CATCHMENT) == []
