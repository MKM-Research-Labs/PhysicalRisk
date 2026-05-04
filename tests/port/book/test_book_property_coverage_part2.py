"""Tests for property book generator — covers _select_properties,
_lookup_property_metadata, and generate_property_book."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from port.src.book.book_property import (
    _select_properties,
    _lookup_property_metadata,
    generate_property_book,
)


# ---------------------------------------------------------------------------
# Helpers — build minimal test data
# ---------------------------------------------------------------------------

def _make_phc_curve(flood_count, spreads=None, tenors=None, gauge_id='G001',
                    gauge_name='Test Gauge', flood_zone='Zone 3'):
    """Return a minimal propertyhc curve dict."""
    if spreads is None:
        spreads = [50, 80, 120, 200]
    if tenors is None:
        tenors = [1, 2, 3, 5]
    return {
        'flood_count': flood_count,
        'flood_zone': flood_zone,
        'term_structure': {
            'tenors': tenors,
            'severe': {
                'prs_spread_bps': spreads,
            },
        },
        'nearest_gauges': [
            {'gauge_id': gauge_id, 'gauge_name': gauge_name, 'distance_km': 1.5},
        ],
    }


def _make_property_entry(property_id, building_number='10',
                         street_name='Flood Lane', postcode='SW1A 1AA',
                         local_authority='Westminster',
                         property_value=450000, lat=51.5, lon=-0.12,
                         flood_zone='Zone 3'):
    """Return a minimal property.json entry."""
    return {
        'PropertyHeader': {
            'Header': {'PropertyID': property_id},
            'Location': {
                'BuildingNumber': building_number,
                'StreetName': street_name,
                'Postcode': postcode,
                'LocalAuthority': local_authority,
                'LatitudeDegrees': lat,
                'LongitudeDegrees': lon,
            },
            'Valuation': {'PropertyValue': property_value},
            'RiskAssessment': {'EAFloodZone': flood_zone},
        }
    }


def _make_counterparty_entry(name='Acme Re', lei='LEI123'):
    return {'name': name, 'lei': lei}


# ---------------------------------------------------------------------------
# _select_properties tests
# ---------------------------------------------------------------------------

class TestGeneratePropertyBook:

    def _write_json(self, path, data):
        path.write_text(json.dumps(data))

    def _setup_files(self, tmp_path, phc_curves=None, properties=None,
                     counterparties=None, num_storms=20000):
        phc_path = tmp_path / 'propertyhc.json'
        prop_path = tmp_path / 'property.json'
        ctpy_path = tmp_path / 'counterparty.json'
        out_dir = tmp_path / 'output'

        if phc_curves is None:
            phc_curves = {}
        phc_data = {
            'metadata': {'num_storms': num_storms},
            'property_hazard_curves': phc_curves,
        }
        self._write_json(phc_path, phc_data)

        if properties is None:
            properties = []
        self._write_json(prop_path, {'properties': properties})

        if counterparties is None:
            counterparties = [_make_counterparty_entry()]
        self._write_json(ctpy_path, counterparties)

        return phc_path, prop_path, ctpy_path, out_dir

    @patch('port.src.book.book_property._price_and_save_trade')
    @patch('port.src.book.book_property._load_counterparties')
    def test_happy_path(self, mock_load_ctpy, mock_price, tmp_path):
        """Full generation with a handful of properties."""
        ctpys = [_make_counterparty_entry('Bank A'), _make_counterparty_entry('Bank B')]
        mock_load_ctpy.return_value = ctpys

        call_count = 0

        def _side_effect(**kwargs):
            nonlocal call_count
            record = {
                'trade_id': f'PRS-P{call_count}',
                'gauge_id': kwargs.get('gauge_id', ''),
            }
            call_count += 1
            return (record, kwargs.get('ctpy_idx', 0) + 1)

        mock_price.side_effect = _side_effect

        curves = {}
        props = []
        for i in range(6):
            pid = f'PROP{i}'
            curves[pid] = _make_phc_curve(
                flood_count=(i + 1) * 15,
                gauge_id=f'G{i:03d}',
                gauge_name=f'Gauge {i}',
            )
            props.append(_make_property_entry(pid))

        phc_path, prop_path, ctpy_path, out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        trades = generate_property_book(
            phc_path, prop_path, ctpy_path, out_dir, catchment_id='thames', seed=99,
        )

        assert len(trades) > 0
        assert mock_price.call_count == len(trades)
        assert out_dir.exists()

        # Check _price_and_save_trade was called with property_set containing metadata
        first_call_kwargs = mock_price.call_args_list[0][1]
        assert 'property_set' in first_call_kwargs
        assert 'PropertyID' in first_call_kwargs['property_set']

    @patch('port.src.book.book_property._price_and_save_trade')
    @patch('port.src.book.book_property._load_counterparties')
    def test_empty_phc_curves(self, mock_load_ctpy, mock_price, tmp_path):
        """No property hazard curves => empty result, warning logged."""
        mock_load_ctpy.return_value = []

        phc_path, prop_path, ctpy_path, out_dir = self._setup_files(
            tmp_path, phc_curves={},
        )

        trades = generate_property_book(
            phc_path, prop_path, ctpy_path, out_dir, seed=1,
        )

        assert trades == []
        mock_price.assert_not_called()

    @patch('port.src.book.book_property._price_and_save_trade')
    @patch('port.src.book.book_property._load_counterparties')
    def test_no_eligible_properties(self, mock_load_ctpy, mock_price, tmp_path):
        """All curves have flood_count == 0 => _select returns [] => empty."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]

        curves = {
            'P1': _make_phc_curve(flood_count=0),
            'P2': _make_phc_curve(flood_count=0),
        }
        phc_path, prop_path, ctpy_path, out_dir = self._setup_files(
            tmp_path, phc_curves=curves,
        )

        trades = generate_property_book(
            phc_path, prop_path, ctpy_path, out_dir, seed=2,
        )

        assert trades == []
        mock_price.assert_not_called()

    @patch('port.src.book.book_property._price_and_save_trade')
    @patch('port.src.book.book_property._load_counterparties')
    def test_closest_tenor_matching(self, mock_load_ctpy, mock_price, tmp_path):
        """Curves with non-standard tenors should still match closest."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        curves = {
            'P1': _make_phc_curve(
                flood_count=50,
                tenors=[2, 4, 7],       # no exact match for 1, 3, 5
                spreads=[30, 60, 100],
            ),
        }
        props = [_make_property_entry('P1')]
        phc_path, prop_path, ctpy_path, out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        trades = generate_property_book(
            phc_path, prop_path, ctpy_path, out_dir, seed=7,
        )

        assert len(trades) == 1
        call_kw = mock_price.call_args[1]
        assert call_kw['fair_spread_override'] > 0

    @patch('port.src.book.book_property._price_and_save_trade')
    @patch('port.src.book.book_property._load_counterparties')
    def test_zero_spread_skipped(self, mock_load_ctpy, mock_price, tmp_path):
        """A curve whose matched spread is 0 should be skipped (line 213-214)."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        curves = {
            'P1': _make_phc_curve(
                flood_count=10,
                tenors=[1, 2, 3, 5],
                spreads=[0, 0, 0, 0],   # all zero
            ),
        }
        props = [_make_property_entry('P1')]
        phc_path, prop_path, ctpy_path, out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        trades = generate_property_book(
            phc_path, prop_path, ctpy_path, out_dir, seed=3,
        )

        assert trades == []
        mock_price.assert_not_called()

    @patch('port.src.book.book_property._price_and_save_trade')
    @patch('port.src.book.book_property._load_counterparties')
    def test_no_nearest_gauges_skipped(self, mock_load_ctpy, mock_price, tmp_path):
        """Property with empty nearest_gauges should be skipped (line 223)."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        curve = _make_phc_curve(flood_count=20)
        curve['nearest_gauges'] = []   # empty
        curves = {'P1': curve}
        props = [_make_property_entry('P1')]
        phc_path, prop_path, ctpy_path, out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        trades = generate_property_book(
            phc_path, prop_path, ctpy_path, out_dir, seed=4,
        )

        assert trades == []
        mock_price.assert_not_called()

    @patch('port.src.book.book_property._price_and_save_trade')
    @patch('port.src.book.book_property._load_counterparties')
    def test_all_trades_are_payer(self, mock_load_ctpy, mock_price, tmp_path):
        """PropertyPRS: REIT is always payer (buys protection), Trader always receiver."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        curves = {f'P{i}': _make_phc_curve(flood_count=(i + 1) * 10)
                  for i in range(6)}
        props = [_make_property_entry(f'P{i}') for i in range(6)]
        phc_path, prop_path, ctpy_path, out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        generate_property_book(
            phc_path, prop_path, ctpy_path, out_dir, seed=42,
        )

        for call in mock_price.call_args_list:
            assert call[1]['is_payer'] is True, \
                'All PropertyPRS trades must have is_payer=True (REIT buys protection)'

    @patch('port.src.book.book_property._price_and_save_trade')
    @patch('port.src.book.book_property._load_counterparties')
    def test_property_set_includes_reference_gauge(self, mock_load_ctpy,
                                                    mock_price, tmp_path):
        """property_set passed to _price_and_save_trade should contain ReferenceGauge."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        curves = {'P1': _make_phc_curve(flood_count=30, gauge_id='G999',
                                        gauge_name='River Test')}
        props = [_make_property_entry('P1')]
        phc_path, prop_path, ctpy_path, out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        generate_property_book(
            phc_path, prop_path, ctpy_path, out_dir, seed=5,
        )

        pset = mock_price.call_args[1]['property_set']
        assert 'ReferenceGauge' in pset
        assert pset['ReferenceGauge']['GaugeID'] == 'G999'
