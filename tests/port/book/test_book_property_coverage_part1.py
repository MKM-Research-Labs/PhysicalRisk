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

class TestSelectProperties:

    def test_empty_input(self):
        assert _select_properties({}, 5) == []

    def test_all_zero_flood_count_filtered(self):
        """Curves with flood_count == 0 should be excluded."""
        curves = {
            'P1': _make_phc_curve(flood_count=0),
            'P2': _make_phc_curve(flood_count=0),
        }
        assert _select_properties(curves, 5) == []

    def test_missing_spreads_filtered(self):
        """Curves with no prs_spread_bps should be excluded."""
        curves = {'P1': _make_phc_curve(flood_count=10, spreads=[])}
        assert _select_properties(curves, 5) == []

    def test_missing_tenors_filtered(self):
        curves = {'P1': _make_phc_curve(flood_count=10, tenors=[])}
        assert _select_properties(curves, 5) == []

    def test_single_item_returned(self):
        curves = {'P1': _make_phc_curve(flood_count=5)}
        result = _select_properties(curves, 1)
        assert len(result) == 1
        assert result[0]['property_id'] == 'P1'

    def test_bucketing_across_spectrum(self):
        """With 9 items across 3 buckets, requesting 6 should draw ~2 per bucket."""
        curves = {f'P{i}': _make_phc_curve(flood_count=(i + 1) * 10)
                  for i in range(9)}
        result = _select_properties(curves, 6)
        assert len(result) == 6
        ids = {r['property_id'] for r in result}
        assert len(ids) == 6  # all unique

    def test_result_capped_at_num(self):
        curves = {f'P{i}': _make_phc_curve(flood_count=(i + 1) * 5)
                  for i in range(20)}
        result = _select_properties(curves, 10)
        assert len(result) <= 10

    def test_fewer_items_than_requested(self):
        curves = {
            'P1': _make_phc_curve(flood_count=3),
            'P2': _make_phc_curve(flood_count=8),
        }
        result = _select_properties(curves, 10)
        assert len(result) == 2

    def test_items_contain_expected_keys(self):
        curves = {'P1': _make_phc_curve(flood_count=7)}
        result = _select_properties(curves, 1)
        item = result[0]
        assert 'property_id' in item
        assert 'flood_count' in item
        assert 'spreads' in item
        assert 'tenors' in item
        assert 'curve' in item


# ---------------------------------------------------------------------------
# _lookup_property_metadata tests
# ---------------------------------------------------------------------------

class TestLookupPropertyMetadata:

    def test_found(self):
        props = [_make_property_entry('P42', building_number='7',
                                      street_name='River Rd',
                                      postcode='OX1 2AB',
                                      property_value=300000)]
        result = _lookup_property_metadata(props, 'P42')
        assert result['PropertyID'] == 'P42'
        assert result['PropertyAddress'] == '7 River Rd'
        assert result['Postcode'] == 'OX1 2AB'
        assert result['PropertyValue'] == 300000

    def test_not_found(self):
        props = [_make_property_entry('P1')]
        result = _lookup_property_metadata(props, 'MISSING')
        assert result == {'PropertyID': 'MISSING'}

    def test_empty_list(self):
        result = _lookup_property_metadata([], 'P1')
        assert result == {'PropertyID': 'P1'}

    def test_partial_location_fields(self):
        """Property with missing BuildingNumber still returns address."""
        entry = _make_property_entry('P5', building_number='', street_name='Main St')
        result = _lookup_property_metadata([entry], 'P5')
        assert result['PropertyAddress'] == 'Main St'

    def test_metadata_fields_present(self):
        entry = _make_property_entry('P9', flood_zone='Zone 2',
                                     lat=52.0, lon=-1.5)
        result = _lookup_property_metadata([entry], 'P9')
        assert result['EAFloodZone'] == 'Zone 2'
        assert result['Latitude'] == 52.0
        assert result['Longitude'] == -1.5
        assert 'LocalAuthority' in result


# ---------------------------------------------------------------------------
# generate_property_book tests
# ---------------------------------------------------------------------------

