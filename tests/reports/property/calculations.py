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

"""Tests for core property flood risk calculations."""

import pytest

from tests.reports.property._helpers import (
    calculate_damage_ratio,
    calculate_distance_km,
    calculate_flood_depth,
    classify_risk_level,
)


class TestDistanceCalculations:
    """Test geographic distance calculations."""

    def test_haversine_same_point(self):
        lat, lon = 51.5074, -0.1278
        assert calculate_distance_km(lat, lon, lat, lon) == pytest.approx(0.0, abs=0.001)

    def test_haversine_known_distance(self):
        # Westminster to Tower Bridge ~7km
        distance = calculate_distance_km(51.4970, -0.1789, 51.5055, -0.0784)
        assert 6.0 < distance < 8.0

    def test_haversine_teddington_to_richmond(self):
        distance = calculate_distance_km(51.4310, -0.3215, 51.4613, -0.3037)
        assert 2.5 < distance < 4.0


class TestFloodDepthCalculation:
    """Test flood depth calculations."""

    def test_no_flood_below_trigger(self):
        depth = calculate_flood_depth(
            property_elevation=10.0, gauge_level=4.0, distance_km=1.0, trigger_level=5.5
        )
        assert depth == 0.0

    def test_flood_above_trigger(self):
        depth = calculate_flood_depth(
            property_elevation=5.0, gauge_level=7.0, distance_km=0.5, trigger_level=5.5
        )
        assert depth > 0.0

    def test_high_elevation_no_flood(self):
        depth = calculate_flood_depth(
            property_elevation=25.0, gauge_level=8.0, distance_km=1.0, trigger_level=5.5
        )
        assert depth == 0.0

    def test_flood_attenuates_with_distance(self):
        depth_close = calculate_flood_depth(
            property_elevation=5.0, gauge_level=7.0, distance_km=0.5, trigger_level=5.5
        )
        depth_far = calculate_flood_depth(
            property_elevation=5.0, gauge_level=7.0, distance_km=5.0, trigger_level=5.5
        )
        assert depth_close > depth_far


class TestDamageRatio:
    """Test depth-damage curve calculations."""

    def test_no_damage_no_flood(self):
        assert calculate_damage_ratio(0.0) == 0.0

    def test_damage_increases_with_depth(self):
        ratios = [calculate_damage_ratio(d) for d in [0.0, 0.5, 1.0, 2.0]]
        assert ratios == sorted(ratios)

    def test_damage_capped(self):
        assert calculate_damage_ratio(10.0) <= 1.0

    def test_commercial_higher_damage(self):
        res_ratio = calculate_damage_ratio(1.0, "residential")
        com_ratio = calculate_damage_ratio(1.0, "commercial")
        assert com_ratio >= res_ratio


class TestRiskClassification:
    """Test risk level classification."""

    def test_minimal_risk(self):
        assert classify_risk_level(0.0) == "MINIMAL"

    def test_low_risk(self):
        assert classify_risk_level(0.3) == "LOW"

    def test_medium_risk(self):
        assert classify_risk_level(1.0) == "MEDIUM"

    def test_high_risk(self):
        assert classify_risk_level(3.0) == "HIGH"
