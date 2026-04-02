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
