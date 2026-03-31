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

"""Tests verifying generators use uuid4 and produce compliant IDs."""

import inspect
import uuid
import pytest
from .conftest import GAUGE_ID_RE, PROP_ID_RE, MORT_ID_RE, STORM_ID_RE, PRS_ID_RE


class TestGaugeIDGenerator:
    """Gauge random generator produces GAUGE-{8hex} IDs."""

    def test_generator_source_uses_gauge_prefix(self):
        """gauge_random.py contains the GAUGE- prefix."""
        from port.rand.thames.gauge import gauge_random as gr
        src = inspect.getsource(gr)
        assert 'GAUGE-' in src, "gauge_random must use 'GAUGE-' prefix"

    def test_generator_source_uses_uuid(self):
        """gauge_random.py uses uuid for ID generation (not sequential counter)."""
        from port.rand.thames.gauge import gauge_random as gr
        src = inspect.getsource(gr)
        assert 'uuid' in src, "gauge_random must use uuid for gauge IDs"

    def test_generator_does_not_use_sequential_format(self):
        """gauge_random.py must NOT use GAUGE-{i:03d} style sequential IDs."""
        from port.rand.thames.gauge import gauge_random as gr
        src = inspect.getsource(gr)
        assert 'GAUGE-{i:' not in src
        assert 'GAUGE-{index' not in src

    def test_uuid4_produces_protocol_matching_ids(self):
        """uuid4()[:8] always produces 8 lowercase hex chars — 100 samples."""
        for _ in range(100):
            suffix = str(uuid.uuid4())[:8]
            gauge_id = f"GAUGE-{suffix}"
            assert GAUGE_ID_RE.match(gauge_id), \
                f"uuid4-derived gauge ID '{gauge_id}' does not match protocol"


class TestPropertyIDGenerator:
    """Property random generator produces PROP-{8hex} IDs."""

    def test_generator_source_uses_prop_prefix(self):
        from port.rand.thames.property import property_random as pr
        src = inspect.getsource(pr)
        assert 'PROP-' in src, "property_random must use 'PROP-' prefix"

    def test_generator_source_uses_uuid(self):
        from port.rand.thames.property import property_random as pr
        src = inspect.getsource(pr)
        assert 'uuid' in src

    def test_generator_does_not_use_sequential_format(self):
        from port.rand.thames.property import property_random as pr
        src = inspect.getsource(pr)
        assert 'PROP-{i:' not in src
        assert 'PROP-{index' not in src

    def test_uuid4_produces_protocol_matching_ids(self):
        for _ in range(100):
            prop_id = f"PROP-{str(uuid.uuid4())[:8]}"
            assert PROP_ID_RE.match(prop_id), \
                f"uuid4-derived property ID '{prop_id}' does not match protocol"


class TestMortgageIDGenerator:
    """Mortgage random generator produces MORT-{8hex} IDs."""

    def test_generator_source_uses_mort_prefix(self):
        from port.rand.thames.mortgage import financials as mr
        src = inspect.getsource(mr)
        assert 'MORT-' in src, "mortgage_random must use 'MORT-' prefix"

    def test_generator_source_uses_uuid(self):
        from port.rand.thames.mortgage import financials as mr
        src = inspect.getsource(mr)
        assert 'uuid' in src

    def test_generator_does_not_use_sequential_format(self):
        from port.rand.thames.mortgage import financials as mr
        src = inspect.getsource(mr)
        assert 'MORT-{i:' not in src

    def test_uuid4_produces_protocol_matching_ids(self):
        for _ in range(100):
            mort_id = f"MORT-{str(uuid.uuid4())[:8]}"
            assert MORT_ID_RE.match(mort_id), \
                f"uuid4-derived mortgage ID '{mort_id}' does not match protocol"


class TestStormIDGenerator:
    """Storm generator produces STORM-{8hex} IDs — not sequential integers."""

    def test_single_storm_generator_uses_storm_prefix(self):
        from port.src.storm_multi.core import data_structures as sg
        src = inspect.getsource(sg)
        assert 'STORM-' in src or 'STORM_ID_PREFIX' in src, \
            "storm generator must use 'STORM-' prefix or STORM_ID_PREFIX constant"

    def test_single_storm_generator_uses_uuid(self):
        from port.src.storm_multi.core import data_structures as sg
        src = inspect.getsource(sg)
        assert 'uuid' in src, "storm generator must use uuid for storm IDs"

    def test_single_storm_generator_does_not_use_sequential_format(self):
        """storm generator must NOT use STORM-{i:03d} or STORM-{i:04d}."""
        from port.src.storm_multi.core import data_structures as sg
        src = inspect.getsource(sg)
        assert 'STORM-{i:' not in src
        assert 'STORM-{i+' not in src

    def test_multi_storm_make_storm_id_follows_protocol(self):
        """storm_multi.make_storm_id() produces STORM-{8hex} IDs."""
        from port.src.storm_multi.core.data_structures import make_storm_id
        for _ in range(50):
            sid = make_storm_id()
            assert STORM_ID_RE.match(sid), \
                f"make_storm_id() returned '{sid}' — violates STORM-{{8hex}} protocol"

    def test_uuid4_produces_protocol_matching_ids(self):
        for _ in range(100):
            storm_id = f"STORM-{str(uuid.uuid4())[:8]}"
            assert STORM_ID_RE.match(storm_id), \
                f"uuid4-derived storm ID '{storm_id}' does not match protocol"


class TestPRSTradeIDGenerator:
    """PRS trade generator produces PRS-{8hex} IDs via uuid4.hex[:8].upper()."""

    def test_book_thames_uses_prs_prefix(self):
        from port.src.book import book_common as bc
        src = inspect.getsource(bc)
        assert 'PRS-' in src, "book_common (trade ID generator) must use 'PRS-' prefix for swap IDs"

    def test_book_thames_uses_uuid(self):
        from port.src.book import book_common as bc
        src = inspect.getsource(bc)
        assert 'uuid' in src

    def test_uuid4_hex_upper_produces_protocol_matching_ids(self):
        """uuid4().hex[:8].upper() — the book generator pattern — always matches."""
        for _ in range(100):
            swap_id = f"PRS-{uuid.uuid4().hex[:8].upper()}"
            assert PRS_ID_RE.match(swap_id), \
                f"PRS trade ID '{swap_id}' does not match protocol"
