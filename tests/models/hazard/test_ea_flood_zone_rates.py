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
