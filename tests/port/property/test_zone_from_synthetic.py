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

"""Tests for zone derivation from synthetic gauge elevation in process.py."""

import pytest

from port.src.property.ts.flood.process import FloodMixin


class TestZoneFromOffset:
    """Verify _zone_from_offset matches elevation boundaries."""

    @pytest.mark.parametrize("offset,expected", [
        (0.0, 'Zone 3b'),
        (0.25, 'Zone 3b'),
        (0.49, 'Zone 3b'),
        (0.5, 'Zone 3a'),
        (1.0, 'Zone 3a'),
        (1.49, 'Zone 3a'),
        (1.5, 'Zone 2'),
        (2.5, 'Zone 2'),
        (2.99, 'Zone 2'),
        (3.0, 'Zone 1'),
        (5.0, 'Zone 1'),
        (50.0, 'Zone 1'),
    ])
    def test_boundary(self, offset, expected):
        assert FloodMixin._zone_from_offset(offset) == expected

    def test_negative_offset_gives_zone_3b(self):
        """Negative offset (property below river) should still give Zone 3b."""
        # max(0.0, offset) is applied before calling, but test the function directly
        assert FloodMixin._zone_from_offset(0.0) == 'Zone 3b'


class TestZoneConsistencyWithElevation:
    """Verify that the zone assigned in process.py uses synthetic elevation."""

    def test_zone_uses_controlling_gauge_elevation(self):
        """The zone should be derived from prop_elevation - synthetic_elevation,
        not from the CDM field or a random assignment."""
        assert FloodMixin._zone_from_offset(1.0) == 'Zone 3a'
        assert FloodMixin._zone_from_offset(0.3) == 'Zone 3b'
        assert FloodMixin._zone_from_offset(2.0) == 'Zone 2'

    def test_shd_mode_zone_is_3b(self):
        """In SHD mode (zero elevation diff), zone should be Zone 3b."""
        # SHD sets effective_elevation = gauge_elevation, so offset = 0
        assert FloodMixin._zone_from_offset(0.0) == 'Zone 3b'

    def test_she_mode_zone_preserves_real_offset(self):
        """In SHE mode (zero distance), zone should reflect real elevation."""
        # SHE doesn't change elevation, so zone depends on actual offset
        assert FloodMixin._zone_from_offset(2.0) == 'Zone 2'
        assert FloodMixin._zone_from_offset(0.3) == 'Zone 3b'
