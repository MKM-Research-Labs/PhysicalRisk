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

"""Tests for property book generator — covers _select_properties,
_lookup_property_metadata, and generate_property_book. (part 3)"""

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
# Shared setup mixin (the non-test members of TestGeneratePropertyBook from
# part 2, duplicated here for the classes below).
# ---------------------------------------------------------------------------

class _PropertyBookSetup:

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


# ---------------------------------------------------------------------------
# generate_property_book — remaining scenarios (continued from part 2)
# ---------------------------------------------------------------------------

class TestGeneratePropertyBookPart2(_PropertyBookSetup):

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
    def test_no_nearest_gauges_skipped(self, mock_load_ctpy, mock_price, tmp_path):
        """Property with empty nearest_gauges should be skipped (line 223)."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        curve = _make_phc_curve(flood_count=20)
        curve['nearest_gauges'] = []   # empty
        curves = {'P1': curve}
        props = [_make_property_entry('P1')]
        out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        trades = generate_property_book(
            out_dir, seed=4,
        )

        assert trades == []
        mock_price.assert_not_called()

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
    def test_all_trades_are_payer(self, mock_load_ctpy, mock_price, tmp_path):
        """PropertyPRS: REIT is always payer (buys protection), Trader always receiver."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        curves = {f'P{i}': _make_phc_curve(flood_count=(i + 1) * 10)
                  for i in range(6)}
        props = [_make_property_entry(f'P{i}') for i in range(6)]
        out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        generate_property_book(
            out_dir, seed=42,
        )

        for call in mock_price.call_args_list:
            assert call[1]['is_payer'] is True, \
                'All PropertyPRS trades must have is_payer=True (REIT buys protection)'

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
    def test_property_set_includes_reference_gauge(self, mock_load_ctpy,
                                                    mock_price, tmp_path):
        """property_set passed to _price_and_save_trade should contain ReferenceGauge."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        curves = {'P1': _make_phc_curve(flood_count=30, gauge_id='G999',
                                        gauge_name='River Test')}
        props = [_make_property_entry('P1')]
        out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        generate_property_book(
            out_dir, seed=5,
        )

        pset = mock_price.call_args[1]['property_set']
        assert 'ReferenceGauge' in pset
        assert pset['ReferenceGauge']['GaugeID'] == 'G999'


# ---------------------------------------------------------------------------
# Pure vs resilient (BRI-adjusted) flavours
# ---------------------------------------------------------------------------

class TestResilientFlavour(_PropertyBookSetup):
    """Booking the resilient (BRI) leg alongside the pure leg."""

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
    def test_no_resilient_when_bri_file_absent(self, mock_load_ctpy,
                                               mock_price, tmp_path):
        """Without include_resilient only the pure flavour is booked."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        curves = {'P1': _make_phc_curve(flood_count=40)}
        props = [_make_property_entry('P1')]
        out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props,
        )

        trades = generate_property_book(
            out_dir, seed=11,
        )

        assert len(trades) == 1
        variants = [c[1]['property_set'].get('PRSVariant')
                    for c in mock_price.call_args_list]
        assert variants == ['pure']

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
    def test_resilient_trade_added_when_bri_present(self, mock_load_ctpy,
                                                    mock_price, tmp_path):
        """A property with a BRI curve gets both a pure and a resilient trade,
        and the resilient fair spread is tighter (<=) than the pure spread."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        # Pure spreads higher than BRI-adjusted (resilience removes floods).
        curves = {'P1': _make_phc_curve(
            flood_count=40, tenors=[1, 2, 3, 5], spreads=[50, 80, 120, 200])}
        bri = {'P1': _make_phc_curve(
            flood_count=32, tenors=[1, 2, 3, 5], spreads=[40, 64, 96, 168])}
        props = [_make_property_entry('P1')]
        out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props, bri_curves=bri,
        )

        trades = generate_property_book(
            out_dir, seed=11,
            include_resilient=True,
        )

        assert len(trades) == 2
        calls = mock_price.call_args_list
        variants = [c[1]['property_set'].get('PRSVariant') for c in calls]
        assert variants == ['pure', 'resilient']

        # Both legs price the same tenor; resilient spread must be <= pure.
        pure_spread = calls[0][1]['fair_spread_override']
        resilient_spread = calls[1][1]['fair_spread_override']
        assert resilient_spread <= pure_spread

    @patch('port.src.book.book_property._core._price_and_save_trade')
    @patch('port.src.book.book_property._core._load_counterparties')
    def test_resilient_omitted_for_property_without_bri_curve(
            self, mock_load_ctpy, mock_price, tmp_path):
        """BRI file present but missing this property => pure-only."""
        mock_load_ctpy.return_value = [_make_counterparty_entry()]
        mock_price.return_value = ({'trade_id': 'T1'}, 1)

        curves = {'P1': _make_phc_curve(flood_count=40)}
        bri = {'P2': _make_phc_curve(flood_count=10)}  # different property
        props = [_make_property_entry('P1')]
        out_dir = self._setup_files(
            tmp_path, phc_curves=curves, properties=props, bri_curves=bri,
        )

        trades = generate_property_book(
            out_dir, seed=11,
            include_resilient=True,
        )

        assert len(trades) == 1
        variants = [c[1]['property_set'].get('PRSVariant')
                    for c in mock_price.call_args_list]
        assert variants == ['pure']
