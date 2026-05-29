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

"""Tests for extract_*_ids and analyze_id_relationships."""

import pytest

from loaders.lookups import (
    extract_property_ids,
    extract_rloan_ids,
    extract_rloan_property_ids,
    extract_gauge_ids,
    analyze_id_relationships,
)


# ===========================================================================
# extract_property_ids
# ===========================================================================

class TestExtractPropertyIds:

    def test_none_returns_empty_set(self):
        assert extract_property_ids(None) == set()

    def test_empty_items_returns_empty_set(self):
        assert extract_property_ids({"items": []}) == set()

    def test_extracts_ids(self):
        data = {
            "items": [
                {"PropertyHeader": {"Header": {"PropertyID": "P1"}}},
                {"PropertyHeader": {"Header": {"PropertyID": "P2"}}},
            ]
        }
        assert extract_property_ids(data) == {"P1", "P2"}

    def test_missing_property_id_skipped(self):
        data = {"items": [{"PropertyHeader": {"Header": {}}}]}
        assert extract_property_ids(data) == set()


# ===========================================================================
# extract_rloan_ids
# ===========================================================================

class TestExtractRLoanIds:

    def test_none_returns_empty_set(self):
        assert extract_rloan_ids(None) == set()

    def test_extracts_ids(self):
        data = {
            "items": [
                {"Mortgage": {"Header": {"MortgageID": "M1"}}},
                {"Mortgage": {"Header": {"MortgageID": "M2"}}},
            ]
        }
        assert extract_rloan_ids(data) == {"M1", "M2"}


# ===========================================================================
# extract_rloan_property_ids
# ===========================================================================

class TestExtractMortgagePropertyIds:

    def test_none_returns_empty_set(self):
        assert extract_rloan_property_ids(None) == set()

    def test_extracts_property_ids_from_mortgages(self):
        data = {
            "items": [
                {"Mortgage": {"Header": {"MortgageID": "M1", "PropertyID": "P1"}}},
                {"Mortgage": {"Header": {"MortgageID": "M2", "PropertyID": "P2"}}},
            ]
        }
        assert extract_rloan_property_ids(data) == {"P1", "P2"}


# ===========================================================================
# extract_gauge_ids
# ===========================================================================

class TestExtractGaugeIds:

    def test_none_returns_empty_set(self):
        assert extract_gauge_ids(None) == set()

    def test_extracts_ids(self):
        data = {
            "items": [
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-001"}}},
                {"FloodGauge": {"Header": {"GaugeID": "GAUGE-002"}}},
            ]
        }
        assert extract_gauge_ids(data) == {"GAUGE-001", "GAUGE-002"}

    def test_missing_gauge_id_skipped(self):
        data = {"items": [{"FloodGauge": {"Header": {}}}]}
        assert extract_gauge_ids(data) == set()


# ===========================================================================
# analyze_id_relationships
# ===========================================================================

class TestAnalyzeIdRelationships:

    def test_all_none_returns_zeros(self):
        result = analyze_id_relationships()
        assert result["counts"]["properties"] == 0
        assert result["counts"]["mortgages"] == 0
        assert result["overlaps"]["properties_with_mortgages"] == 0

    def test_returns_required_keys(self):
        result = analyze_id_relationships()
        assert "counts" in result
        assert "overlaps" in result

    def test_counts_match_data(self):
        property_data = {
            "items": [
                {"PropertyHeader": {"Header": {"PropertyID": "P1"}}},
                {"PropertyHeader": {"Header": {"PropertyID": "P2"}}},
            ]
        }
        mortgage_data = {
            "items": [
                {"Mortgage": {"Header": {"MortgageID": "M1", "PropertyID": "P1"}}},
            ]
        }
        result = analyze_id_relationships(property_data, mortgage_data)
        assert result["counts"]["properties"] == 2
        assert result["counts"]["mortgages"] == 1
        assert result["overlaps"]["properties_with_mortgages"] == 1

    def test_flood_properties_overlap(self):
        property_data = {
            "items": [
                {"PropertyHeader": {"Header": {"PropertyID": "P1"}}},
                {"PropertyHeader": {"Header": {"PropertyID": "P2"}}},
            ]
        }
        flood_risk_data = {
            "property_hazard_curves": {"P1": {}, "P3": {}}  # P3 not in property_data
        }
        result = analyze_id_relationships(property_data, None, flood_risk_data)
        assert result["counts"]["flood_properties"] == 2
        assert result["overlaps"]["properties_with_flood_risk"] == 1  # Only P1 overlaps

    def test_flood_mortgages_counted(self):
        mortgage_data = {
            "items": [
                {"Mortgage": {"Header": {"MortgageID": "M1", "PropertyID": "P1"}}},
                {"Mortgage": {"Header": {"MortgageID": "M2", "PropertyID": "P2"}}},
            ]
        }
        flood_risk_data = {
            "property_hazard_curves": {"P1": {}}  # Only P1 has flood risk
        }
        result = analyze_id_relationships(None, mortgage_data, flood_risk_data)
        assert result["counts"]["flood_mortgages"] == 1
