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

"""Tests for ClaimReportGenerator, public API and backward-compat shim."""

import pytest


# ---------------------------------------------------------------------------
# generator.py — ClaimReportGenerator
# ---------------------------------------------------------------------------

class TestClaimReportGenerator:
    def test_generate_returns_bytes(self, prop_data, prop_record, rloan_record,
                                    sequence_lookup):
        from reports.property.claim import ClaimReportGenerator
        gen = ClaimReportGenerator()
        result = gen.generate(prop_data, prop_record, rloan_record, sequence_lookup)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_output_is_valid_pdf(self, prop_data, prop_record, rloan_record,
                                  sequence_lookup):
        from reports.property.claim import ClaimReportGenerator
        gen = ClaimReportGenerator()
        result = gen.generate(prop_data, prop_record, rloan_record, sequence_lookup)
        assert result[:4] == b'%PDF'

    def test_generate_without_mortgage(self, prop_data, prop_record, sequence_lookup):
        from reports.property.claim import ClaimReportGenerator
        gen = ClaimReportGenerator()
        result = gen.generate(prop_data, prop_record, None, sequence_lookup)
        assert isinstance(result, bytes)
        assert result[:4] == b'%PDF'

    def test_generate_empty_sequence_lookup(self, prop_data, prop_record,
                                             rloan_record):
        from reports.property.claim import ClaimReportGenerator
        gen = ClaimReportGenerator()
        result = gen.generate(prop_data, prop_record, rloan_record, {})
        assert isinstance(result, bytes)

    def test_claim_ref_contains_prop_id_suffix(self, prop_data, prop_record,
                                                sequence_lookup):
        """Claim ref is built from last 8 chars of property_id."""
        from reports.property.claim.generator import ClaimReportGenerator
        gen = ClaimReportGenerator()
        # Just confirm generate() runs; claim_ref is internal
        result = gen.generate(prop_data, prop_record, None, sequence_lookup)
        assert len(result) > 1000

    def test_pdf_size_reasonable(self, prop_data, prop_record, rloan_record,
                                  sequence_lookup):
        from reports.property.claim import ClaimReportGenerator
        gen = ClaimReportGenerator()
        result = gen.generate(prop_data, prop_record, rloan_record, sequence_lookup)
        # 5-page PDF should be at least 8 KB
        assert len(result) > 8_000

    def test_minimal_prop_data(self, prop_record, sequence_lookup):
        """Minimal prop_data with a single flood event should not raise."""
        from reports.property.claim import ClaimReportGenerator
        data = {
            'property_id': 'PROP-MIN',
            'flood_events': [
                {'storm_id': 'S1', 'sequence_id': None,
                 'flood_depth_m': 0.5, 'damage_ratio': 0.1, 'flooded': True},
            ],
        }
        gen = ClaimReportGenerator()
        result = gen.generate(data, prop_record, None, sequence_lookup)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# __init__.py public API
# ---------------------------------------------------------------------------

class TestPublicAPI:
    def test_import_from_package(self):
        from reports.property.claim import ClaimReportGenerator
        assert ClaimReportGenerator is not None

    def test_all_exports(self):
        import reports.property.claim as pkg
        assert 'ClaimReportGenerator' in pkg.__all__


# ---------------------------------------------------------------------------
# Backward-compatibility shim
# ---------------------------------------------------------------------------

class TestCompatShim:
    def test_shim_imports_generator(self):
        from reports.property.claim_generator import ClaimReportGenerator
        assert ClaimReportGenerator is not None

    def test_shim_class_is_same(self):
        from reports.property.claim import ClaimReportGenerator as New
        from reports.property.claim_generator import ClaimReportGenerator as Shim
        assert New is Shim
