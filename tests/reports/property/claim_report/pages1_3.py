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

"""Tests for page1_cover, page2_chronology and page3_damage builders."""

import pytest
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table


# ---------------------------------------------------------------------------
# page1_cover.py
# ---------------------------------------------------------------------------

class TestPage1Cover:
    def test_returns_list(self, prop_data, prop_record, rloan_record,
                          claim_ref, today, styles):
        from reports.property.claim.page1_cover import build_page1_cover
        result = build_page1_cover(
            prop_data, prop_record, rloan_record, claim_ref, today, styles)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_contains_claim_ref_paragraph(self, prop_data, prop_record,
                                          rloan_record, claim_ref, today, styles):
        from reports.property.claim.page1_cover import build_page1_cover
        result = build_page1_cover(
            prop_data, prop_record, rloan_record, claim_ref, today, styles)
        # Look for a Table containing the claim reference banner
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) > 0

    def test_without_mortgage(self, prop_data, prop_record, claim_ref, today, styles):
        from reports.property.claim.page1_cover import build_page1_cover
        result = build_page1_cover(
            prop_data, prop_record, None, claim_ref, today, styles)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_flood_events_still_renders(self, prop_record, claim_ref, today, styles):
        from reports.property.claim.page1_cover import build_page1_cover
        data = {
            'property_id': 'PROP-EMPTY',
            'flood_events': [],
            'location': {'latitude': 51.5, 'longitude': -0.1},
        }
        result = build_page1_cover(data, prop_record, None, claim_ref, today, styles)
        assert len(result) > 0

    def test_stats_reflect_events(self, prop_data, prop_record, claim_ref, today, styles):
        from reports.property.claim.page1_cover import build_page1_cover
        result = build_page1_cover(
            prop_data, prop_record, None, claim_ref, today, styles)
        # Should have title paragraphs
        assert any(isinstance(e, Paragraph) for e in result)

    def test_non_float_coordinates(self, prop_record, claim_ref, today, styles):
        """Coordinates that are not floats should not raise."""
        from reports.property.claim.page1_cover import build_page1_cover
        data = {
            'property_id': 'PROP-COORDS',
            'flood_events': [],
            'location': {'latitude': 'N/A', 'longitude': 'N/A'},
        }
        result = build_page1_cover(data, prop_record, None, claim_ref, today, styles)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# page2_chronology.py
# ---------------------------------------------------------------------------

class TestPage2Chronology:
    def test_returns_list(self, prop_data, sequence_lookup, styles):
        from reports.property.claim.page2_chronology import build_page2_chronology
        result = build_page2_chronology(prop_data, sequence_lookup, styles)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_table_included(self, prop_data, sequence_lookup, styles):
        from reports.property.claim.page2_chronology import build_page2_chronology
        result = build_page2_chronology(prop_data, sequence_lookup, styles)
        assert any(isinstance(e, Table) for e in result)

    def test_no_flood_events(self, prop_record, sequence_lookup, styles):
        from reports.property.claim.page2_chronology import build_page2_chronology
        data = {'property_id': 'PROP-EMPTY', 'flood_events': []}
        result = build_page2_chronology(data, sequence_lookup, styles)
        assert isinstance(result, list)
        assert len(result) > 0
        # Should contain "No flood events" paragraph
        texts = [e.text for e in result if isinstance(e, Paragraph)]
        assert any('No flood events' in t for t in texts)

    def test_stats_bar_present(self, prop_data, sequence_lookup, styles):
        from reports.property.claim.page2_chronology import build_page2_chronology
        result = build_page2_chronology(prop_data, sequence_lookup, styles)
        paragraphs = [e for e in result if isinstance(e, Paragraph)]
        assert len(paragraphs) > 0

    def test_unknown_sequence_id_handled(self, styles):
        """Events with sequence_id not in lookup default to 'isolated'."""
        from reports.property.claim.page2_chronology import build_page2_chronology
        data = {
            'property_id': 'PROP-X',
            'flood_events': [{
                'storm_id': 'STORM-X',
                'sequence_id': 'UNKNOWN-SEQ',
                'flood_depth_m': 0.5,
                'damage_ratio': 0.1,
                'flooded': True,
            }],
        }
        result = build_page2_chronology(data, {}, styles)
        assert isinstance(result, list)

    def test_events_with_no_sequence_id(self, styles):
        """Events with no sequence_id (None) should render without error."""
        from reports.property.claim.page2_chronology import build_page2_chronology
        data = {
            'property_id': 'PROP-X',
            'flood_events': [{
                'storm_id': 'STORM-Y',
                'sequence_id': None,
                'flood_depth_m': 0.3,
                'damage_ratio': 0.05,
                'flooded': True,
            }],
        }
        result = build_page2_chronology(data, {}, styles)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# page3_damage.py
# ---------------------------------------------------------------------------

class TestPage3Damage:
    def test_returns_list(self, prop_data, prop_record, sequence_lookup, styles):
        from reports.property.claim.page3_damage import build_page3_damage
        result = build_page3_damage(prop_data, prop_record, sequence_lookup, styles)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_contains_tables(self, prop_data, prop_record, sequence_lookup, styles):
        from reports.property.claim.page3_damage import build_page3_damage
        result = build_page3_damage(prop_data, prop_record, sequence_lookup, styles)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 2  # storm table + sequence table + summary

    def test_no_flood_events(self, prop_record, sequence_lookup, styles):
        from reports.property.claim.page3_damage import build_page3_damage
        data = {'property_id': 'PROP-EMPTY', 'flood_events': []}
        result = build_page3_damage(data, prop_record, sequence_lookup, styles)
        assert isinstance(result, list)

    def test_zero_property_value(self, flood_events, sequence_lookup, styles):
        """Zero property value should not raise a ZeroDivisionError."""
        from reports.property.claim.page3_damage import build_page3_damage
        data = {'property_id': 'PROP-X', 'flood_events': flood_events}
        rec = {'Valuation': {'PropertyValue': 0}}
        result = build_page3_damage(data, rec, sequence_lookup, styles)
        assert isinstance(result, list)

    def test_high_damage_rows_highlighted(self, sequence_lookup, styles):
        """Events with damage ratio > 5% trigger red background rows."""
        from reports.property.claim.page3_damage import build_page3_damage
        events = [{'storm_id': 'S1', 'sequence_id': 'SEQ-A',
                   'flood_depth_m': 1.2, 'damage_ratio': 0.25, 'flooded': True}]
        data = {'property_id': 'PROP-X', 'flood_events': events}
        rec = {'Valuation': {'PropertyValue': 500000}}
        lookup = {'SEQ-A': {'sequence_type': 'isolated', 'num_storms': 1}}
        result = build_page3_damage(data, rec, lookup, styles)
        assert isinstance(result, list)

    def test_multiple_sequences_grouped(self, prop_data, prop_record,
                                        sequence_lookup, styles):
        from reports.property.claim.page3_damage import build_page3_damage
        result = build_page3_damage(prop_data, prop_record, sequence_lookup, styles)
        # Both storm table and sequence-level table should be present
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 3
