"""Tests for EA_FLOOD_ZONE_RATES configuration constant."""

import pytest

from config.models import EA_FLOOD_ZONE_RATES


class TestEAFloodZoneRates:
    """Validate EA_FLOOD_ZONE_RATES structure and ordering."""

    EXPECTED_ZONES = {'Zone 3b', 'Zone 3a', 'Zone 3', 'Zone 2', 'Zone 1'}

    def test_has_all_five_zones(self):
        assert set(EA_FLOOD_ZONE_RATES.keys()) == self.EXPECTED_ZONES

    def test_all_rates_positive(self):
        for zone, rate in EA_FLOOD_ZONE_RATES.items():
            assert rate > 0, f"{zone} rate must be positive, got {rate}"

    def test_all_rates_below_one(self):
        for zone, rate in EA_FLOOD_ZONE_RATES.items():
            assert rate < 1.0, f"{zone} rate must be < 1.0, got {rate}"

    def test_zone_ordering_3b_gt_3a(self):
        assert EA_FLOOD_ZONE_RATES['Zone 3b'] > EA_FLOOD_ZONE_RATES['Zone 3a']

    def test_zone_ordering_3a_gt_2(self):
        assert EA_FLOOD_ZONE_RATES['Zone 3a'] > EA_FLOOD_ZONE_RATES['Zone 2']

    def test_zone_ordering_2_gt_1(self):
        assert EA_FLOOD_ZONE_RATES['Zone 2'] > EA_FLOOD_ZONE_RATES['Zone 1']

    def test_zone_3_equals_3a(self):
        """Zone 3 (generic) should have same rate as Zone 3a."""
        assert EA_FLOOD_ZONE_RATES['Zone 3'] == EA_FLOOD_ZONE_RATES['Zone 3a']

    @pytest.mark.parametrize("zone", EXPECTED_ZONES)
    def test_rate_is_float(self, zone):
        assert isinstance(EA_FLOOD_ZONE_RATES[zone], float)
