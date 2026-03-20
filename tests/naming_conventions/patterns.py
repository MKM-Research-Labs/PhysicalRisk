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

"""Tests for entity ID regex patterns."""

import pytest
from .conftest import GAUGE_ID_RE, PROP_ID_RE, MORT_ID_RE, STORM_ID_RE, PRS_ID_RE


class TestGaugeIDPattern:
    """GAUGE-{8 lowercase hex chars} is the canonical gauge ID format."""

    def test_accepts_valid_uuid_derived_ids(self):
        assert GAUGE_ID_RE.match('GAUGE-9042bd95')
        assert GAUGE_ID_RE.match('GAUGE-a1b2c3d4')
        assert GAUGE_ID_RE.match('GAUGE-00000000')
        assert GAUGE_ID_RE.match('GAUGE-ffffffff')

    def test_rejects_sequential_integers(self):
        """GAUGE-001, GAUGE-002 are NOT protocol-compliant."""
        assert not GAUGE_ID_RE.match('GAUGE-001')
        assert not GAUGE_ID_RE.match('GAUGE-002')
        assert not GAUGE_ID_RE.match('GAUGE-999')
        assert not GAUGE_ID_RE.match('GAUGE-1234')

    def test_rejects_uppercase_hex(self):
        """Gauge IDs must be lowercase; GAUGE-9042BD95 is invalid."""
        assert not GAUGE_ID_RE.match('GAUGE-9042BD95')
        assert not GAUGE_ID_RE.match('GAUGE-A1B2C3D4')

    def test_rejects_wrong_length(self):
        assert not GAUGE_ID_RE.match('GAUGE-9042bd9')    # 7 chars
        assert not GAUGE_ID_RE.match('GAUGE-9042bd951')  # 9 chars
        assert not GAUGE_ID_RE.match('GAUGE-')            # empty suffix

    def test_rejects_non_hex_chars(self):
        assert not GAUGE_ID_RE.match('GAUGE-9042xd95')
        assert not GAUGE_ID_RE.match('GAUGE-9042gd95')


class TestPropertyIDPattern:
    """PROP-{8 lowercase hex chars} is the canonical property ID format."""

    def test_accepts_valid(self):
        assert PROP_ID_RE.match('PROP-a3f7bc12')
        assert PROP_ID_RE.match('PROP-00000000')
        assert PROP_ID_RE.match('PROP-ffffffff')

    def test_rejects_sequential(self):
        assert not PROP_ID_RE.match('PROP-001')
        assert not PROP_ID_RE.match('PROP-1234')
        assert not PROP_ID_RE.match('PROP-00001')

    def test_rejects_uppercase(self):
        assert not PROP_ID_RE.match('PROP-A3F7BC12')


class TestMortgageIDPattern:
    """MORT-{8 lowercase hex chars} is the canonical mortgage ID format."""

    def test_accepts_valid(self):
        assert MORT_ID_RE.match('MORT-4d89e5a1')
        assert MORT_ID_RE.match('MORT-ffffffff')

    def test_rejects_sequential(self):
        assert not MORT_ID_RE.match('MORT-001')
        assert not MORT_ID_RE.match('MORT-9999')


class TestStormIDPattern:
    """STORM-{8 lowercase hex chars} is the canonical storm ID format."""

    def test_accepts_valid(self):
        assert STORM_ID_RE.match('STORM-c7f4b8e2')
        assert STORM_ID_RE.match('STORM-a1b2c3d4')
        assert STORM_ID_RE.match('STORM-00000000')

    def test_rejects_sequential_integers(self):
        """STORM-001, STORM-0001 violate the agreed protocol."""
        assert not STORM_ID_RE.match('STORM-001')
        assert not STORM_ID_RE.match('STORM-0001')
        assert not STORM_ID_RE.match('STORM-0015')

    def test_rejects_wrong_prefix_format(self):
        """STORM-PORT-001 uses a compound prefix — not protocol-compliant."""
        assert not STORM_ID_RE.match('STORM-PORT-001')
        assert not STORM_ID_RE.match('STORM-PORT-002')

    def test_rejects_descriptive_labels(self):
        """Human-readable names like STORM-FLOOD are not protocol-compliant."""
        assert not STORM_ID_RE.match('STORM-FLOOD')
        assert not STORM_ID_RE.match('STORM-SAFE')
        assert not STORM_ID_RE.match('STORM-TEST')

    def test_rejects_uppercase(self):
        assert not STORM_ID_RE.match('STORM-C7F4B8E2')


class TestPRSTradeIDPattern:
    """PRS-{8 hex chars, any case} is the canonical PRS trade ID format."""

    def test_accepts_uppercase(self):
        """book.py uses uuid4().hex[:8].upper() → uppercase hex."""
        assert PRS_ID_RE.match('PRS-A8B3C4D5')
        assert PRS_ID_RE.match('PRS-FFFFFFFF')
        assert PRS_ID_RE.match('PRS-00000000')

    def test_accepts_lowercase(self):
        """Some paths may produce lowercase — also accepted."""
        assert PRS_ID_RE.match('PRS-a8b3c4d5')
        assert PRS_ID_RE.match('PRS-ffffffff')

    def test_rejects_non_hex_suffix(self):
        """PRS-TEST-001 style IDs used in test fixtures are NOT production format."""
        assert not PRS_ID_RE.match('PRS-TEST-001')
        assert not PRS_ID_RE.match('PRS-VAUXHALL')
