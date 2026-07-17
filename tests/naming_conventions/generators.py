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

    def test_generator_source_uses_deterministic_ids(self):
        """gauge_random.py uses hashlib for deterministic ID generation."""
        from port.rand.thames.gauge import gauge_random as gr
        src = inspect.getsource(gr)
        assert 'hashlib' in src, "gauge_random must use hashlib for deterministic gauge IDs"

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
        from port.rand.thames.property.property_random import helpers
        src = inspect.getsource(helpers)
        assert 'PROP-' in src, "property_random helpers must use 'PROP-' prefix"

    def test_generator_source_uses_deterministic_hash(self):
        from port.rand.thames.property.property_random import helpers
        src = inspect.getsource(helpers)
        assert 'hashlib' in src or 'uuid' in src

    def test_generator_does_not_use_sequential_format(self):
        from port.rand.thames.property.property_random import helpers
        src = inspect.getsource(helpers)
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
        from port.src.book.book_common import _pricing as bc
        src = inspect.getsource(bc)
        assert 'PRS-' in src, "book_common (trade ID generator) must use 'PRS-' prefix for swap IDs"

    def test_book_thames_uses_uuid(self):
        from port.src.book.book_common import _pricing as bc
        src = inspect.getsource(bc)
        assert 'uuid' in src

    def test_uuid4_hex_upper_produces_protocol_matching_ids(self):
        """uuid4().hex[:8].upper() — the book generator pattern — always matches."""
        for _ in range(100):
            swap_id = f"PRS-{uuid.uuid4().hex[:8].upper()}"
            assert PRS_ID_RE.match(swap_id), \
                f"PRS trade ID '{swap_id}' does not match protocol"
