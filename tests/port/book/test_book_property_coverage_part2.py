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

"""Tests for property book generator — covers _select_properties,
_lookup_property_metadata, and generate_property_book. (part 2)"""

from unittest.mock import patch

import pytest
from db_helpers import tmp_catchment

import database
from port.src.book.book_property import (
    _lookup_property_metadata,
    _select_properties,
    generate_property_book,
)

_CATCHMENT = "thames"


@pytest.fixture(autouse=True)
def _seam_backend(tmp_path):
    """Bind a scratch backend so the property book reads seeded seam data."""
    with tmp_catchment(tmp_path, _CATCHMENT):
        yield


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

    def _setup_files(self, tmp_path, phc_curves=None, properties=None,
                     counterparties=None, num_storms=20000, bri_curves=None):
        """Seed the property hazard curves + portfolio into the database seam.

        Counterparties are not seeded — the property book uses a fixed REIT and
        the tests mock ``_load_counterparties`` — so the ``counterparties`` arg
        is accepted for back-compat but unused. Returns the output directory."""
        out_dir = tmp_path / 'output'

        if phc_curves is None:
            phc_curves = {}
        database.save_property_hazard_curves(_CATCHMENT, {
            'metadata': {'num_storms': num_storms},
            'property_hazard_curves': phc_curves,
        })

        if properties is None:
            properties = []
        database.save_properties(_CATCHMENT, {'properties': properties})

        # Optional BRI-adjusted curves (the resilient leg source, 'bri' mode).
        if bri_curves is not None:
            database.save_property_hazard_curves(_CATCHMENT, {
                'metadata': {'num_storms': num_storms},
                'property_hazard_curves': bri_curves,
            }, mode='bri')

        return out_dir

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
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

        out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        trades = generate_property_book(
            out_dir, catchment_id='thames', seed=99,
        )

        assert len(trades) > 0
        assert mock_price.call_count == len(trades)
        assert out_dir.exists()

        # Check _price_and_save_trade was called with property_set containing metadata
        first_call_kwargs = mock_price.call_args_list[0][1]
        assert 'property_set' in first_call_kwargs
        assert 'PropertyID' in first_call_kwargs['property_set']

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
    def test_empty_phc_curves(self, mock_load_ctpy, mock_price, tmp_path):
        """No property hazard curves => empty result, warning logged."""
        mock_load_ctpy.return_value = []

        out_dir = self._setup_files(
            tmp_path, phc_curves={},
        )

        trades = generate_property_book(
            out_dir, seed=1,
        )

        assert trades == []
        mock_price.assert_not_called()

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
    def test_no_eligible_properties(self, mock_load_ctpy, mock_price, tmp_path):
        """All curves have flood_count == 0 => _select returns [] => empty."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]

        curves = {
            'P1': _make_phc_curve(flood_count=0),
            'P2': _make_phc_curve(flood_count=0),
        }
        out_dir = self._setup_files(
            tmp_path, phc_curves=curves,
        )

        trades = generate_property_book(
            out_dir, seed=2,
        )

        assert trades == []
        mock_price.assert_not_called()

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
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
        out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        trades = generate_property_book(
            out_dir, seed=7,
        )

        assert len(trades) == 1
        call_kw = mock_price.call_args[1]
        assert call_kw['fair_spread_override'] > 0

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
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
        out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        trades = generate_property_book(
            out_dir, seed=3,
        )

        assert trades == []
        mock_price.assert_not_called()
