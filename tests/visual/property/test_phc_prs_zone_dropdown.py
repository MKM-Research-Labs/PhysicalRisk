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

"""Tests for EA Flood Zone dropdown in PRS controls."""

import pytest

from visual.interactivity.property import phc_prs


class TestZoneDropdownJS:
    """Verify the EA Zone dropdown is present and wired in the JS output."""

    @pytest.fixture
    def js(self):
        return phc_prs.get_js()

    def test_select_element_present(self, js):
        assert 'id="phc-ea-zone"' in js

    def test_all_zone_options_present(self, js):
        for zone in ['Zone 3b', 'Zone 3a', 'Zone 3', 'Zone 2', 'Zone 1']:
            assert zone in js

    def test_zone_order(self, js):
        """Zones should appear in risk order: 3b, 3a, 3, 2, 1."""
        idx_3b = js.index('Zone 3b')
        idx_3a = js.index('Zone 3a')
        idx_3 = js.index("'Zone 3'")  # Distinguish from Zone 3a/3b
        idx_2 = js.index('Zone 2')
        idx_1 = js.index('Zone 1')
        assert idx_3b < idx_3a < idx_3 < idx_2 < idx_1

    def test_default_from_phcdata(self, js):
        """Default selection reads from phcData.flood_zone."""
        assert 'phcData.flood_zone' in js

    def test_change_listener_includes_zone(self, js):
        """The change listener array must include the zone dropdown ID."""
        assert "'phc-ea-zone'" in js

    def test_label_present(self, js):
        assert 'EA Zone:' in js
