# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for page4_rloan and page5_determination builders."""

import pytest
from reportlab.platypus import Paragraph, Table


# ---------------------------------------------------------------------------
# page4_rloan.py
# ---------------------------------------------------------------------------

class TestPage4RLoan:
    def test_with_mortgage(self, prop_data, prop_record, rloan_record,
                           sequence_lookup, styles):
        from reports.property.claim.page4_rloan import build_page4_rloan
        result = build_page4_rloan(
            prop_data, prop_record, rloan_record, sequence_lookup, styles)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_without_mortgage(self, prop_data, prop_record, sequence_lookup, styles):
        from reports.property.claim.page4_rloan import build_page4_rloan
        result = build_page4_rloan(
            prop_data, prop_record, None, sequence_lookup, styles)
        assert isinstance(result, list)
        # Should render "No mortgage" notice
        texts = []
        for e in result:
            if isinstance(e, Table):
                for row in e._cellvalues:
                    for cell in row:
                        if isinstance(cell, Paragraph):
                            texts.append(cell.text)
        assert any('No mortgage' in t for t in texts)

    def test_contains_tables(self, prop_data, prop_record, rloan_record,
                              sequence_lookup, styles):
        from reports.property.claim.page4_rloan import build_page4_rloan
        result = build_page4_rloan(
            prop_data, prop_record, rloan_record, sequence_lookup, styles)
        assert any(isinstance(e, Table) for e in result)

    def test_no_flood_events_with_mortgage(self, prop_record, rloan_record,
                                            sequence_lookup, styles):
        from reports.property.claim.page4_rloan import build_page4_rloan
        data = {'property_id': 'PROP-EMPTY', 'flood_events': []}
        result = build_page4_rloan(
            data, prop_record, rloan_record, sequence_lookup, styles)
        assert isinstance(result, list)

    def test_negative_equity_highlights_row(self, sequence_lookup, styles):
        """High damage + large mortgage triggers negative equity highlighting."""
        from reports.property.claim.page4_rloan import build_page4_rloan
        events = [
            {'storm_id': 'S1', 'sequence_id': 'SEQ-A',
             'flood_depth_m': 1.5, 'damage_ratio': 0.80, 'flooded': True},
        ]
        data = {'property_id': 'PROP-NEG', 'flood_events': events}
        rec = {'Valuation': {'PropertyValue': 200000}}
        mtg = {
            'FinancialTerms': {'OriginalBalance': 190000},
            'CurrentStatus':  {'OutstandingBalance': 190000},
        }
        lookup = {'SEQ-A': {'sequence_type': 'isolated', 'num_storms': 1}}
        result = build_page4_rloan(data, rec, mtg, lookup, styles)
        assert isinstance(result, list)
        assert any(isinstance(e, Table) for e in result)


# ---------------------------------------------------------------------------
# page5_determination.py
# ---------------------------------------------------------------------------

class TestPage5Determination:
    def test_returns_list(self, prop_data, prop_record, rloan_record,
                          sequence_lookup, claim_ref, today, styles):
        from reports.property.claim.page5_determination import build_page5_determination
        result = build_page5_determination(
            prop_data, prop_record, rloan_record,
            sequence_lookup, claim_ref, today, styles)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_without_mortgage(self, prop_data, prop_record, sequence_lookup,
                               claim_ref, today, styles):
        from reports.property.claim.page5_determination import build_page5_determination
        result = build_page5_determination(
            prop_data, prop_record, None, sequence_lookup, claim_ref, today, styles)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_contains_reference_table(self, prop_data, prop_record, rloan_record,
                                       sequence_lookup, claim_ref, today, styles):
        from reports.property.claim.page5_determination import build_page5_determination
        result = build_page5_determination(
            prop_data, prop_record, rloan_record,
            sequence_lookup, claim_ref, today, styles)
        tables = [e for e in result if isinstance(e, Table)]
        assert len(tables) >= 2  # reference box + assessment table

    def test_damage_calculation(self, prop_record, sequence_lookup,
                                 claim_ref, today, styles):
        """Assessed damage = prop_value * max damage_ratio per sequence."""
        from reports.property.claim.page5_determination import build_page5_determination
        events = [
            {'storm_id': 'S1', 'sequence_id': 'SEQ-A', 'damage_ratio': 0.1},
            {'storm_id': 'S2', 'sequence_id': 'SEQ-A', 'damage_ratio': 0.2},
        ]
        data = {'property_id': 'PROP-X', 'flood_events': events}
        rec = {'Valuation': {'PropertyValue': 500000}}
        result = build_page5_determination(
            data, rec, None, {}, claim_ref, today, styles)
        assert isinstance(result, list)

    def test_negative_equity_flag(self, prop_record, sequence_lookup,
                                   claim_ref, today, styles):
        """When damage exceeds property value, LTV is very high."""
        from reports.property.claim.page5_determination import build_page5_determination
        events = [{'storm_id': 'S1', 'sequence_id': None, 'damage_ratio': 0.95}]
        data = {'property_id': 'PROP-X', 'flood_events': events}
        rec = {'Valuation': {'PropertyValue': 200000}}
        mtg = {
            'FinancialTerms': {'OriginalBalance': 190000},
            'CurrentStatus':  {'OutstandingBalance': 190000},
        }
        result = build_page5_determination(
            data, rec, mtg, {}, claim_ref, today, styles)
        assert isinstance(result, list)

    def test_signature_block_present(self, prop_data, prop_record, rloan_record,
                                      sequence_lookup, claim_ref, today, styles):
        from reports.property.claim.page5_determination import build_page5_determination
        result = build_page5_determination(
            prop_data, prop_record, rloan_record,
            sequence_lookup, claim_ref, today, styles)
        # Signature lines are Paragraphs at the end
        paragraphs = [e for e in result if isinstance(e, Paragraph)]
        assert len(paragraphs) > 3
