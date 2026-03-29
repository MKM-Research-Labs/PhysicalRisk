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

"""
Tests for loaders.storm_loader — StormLoader class (part 2).

Covers: get_major_hurricanes, get_track, get_impact,
and get_storms_affecting_location.
"""

import pytest

from loaders.storm_loader import StormLoader
from tests.loaders.conftest import write_storms


# ===========================================================================
# get_major_hurricanes
# ===========================================================================

class TestGetMajorHurricanes:

    def test_returns_category_3_plus(self, storm_loader):
        result = storm_loader.get_major_hurricanes()
        categories = [s["TCEvent"]["Header"]["Category"] for s in result]
        assert all(c >= 3 for c in categories)

    def test_excludes_category_1_and_2(self, storm_loader):
        result = storm_loader.get_major_hurricanes()
        ids = [storm_loader.get_entity_id(s) for s in result]
        # EVT-004 is cat 1, should be excluded
        assert "EVT-004" not in ids

    def test_includes_cat_3_4_5(self, storm_loader):
        result = storm_loader.get_major_hurricanes()
        ids = [storm_loader.get_entity_id(s) for s in result]
        assert "EVT-001" in ids  # cat 4
        assert "EVT-002" in ids  # cat 5
        assert "EVT-003" in ids  # cat 3


# ===========================================================================
# get_track
# ===========================================================================

class TestGetTrack:

    def test_returns_track_for_existing_storm(self, storm_loader):
        track = storm_loader.get_track("EVT-001")
        assert track is not None
        assert isinstance(track, list)
        assert len(track) >= 1

    def test_track_has_lat_lon(self, storm_loader):
        track = storm_loader.get_track("EVT-001")
        assert "Latitude" in track[0]
        assert "Longitude" in track[0]

    def test_missing_id_returns_none(self, storm_loader):
        assert storm_loader.get_track("EVT-NONEXISTENT") is None


# ===========================================================================
# get_impact
# ===========================================================================

class TestGetImpact:

    def test_returns_impact_dict(self, storm_loader):
        impact = storm_loader.get_impact("EVT-001")
        assert isinstance(impact, dict)
        assert "TotalDamage" in impact

    def test_missing_id_returns_none(self, storm_loader):
        assert storm_loader.get_impact("EVT-NONEXISTENT") is None


# ===========================================================================
# get_storms_affecting_location
# ===========================================================================

class TestGetStormsAffectingLocation:

    def test_finds_nearby_storm(self, storm_loader):
        # Harvey track: (29.7, -95.4) -- search near Houston
        result = storm_loader.get_storms_affecting_location(29.7, -95.4, radius_km=50)
        ids = [storm_loader.get_entity_id(s) for s in result]
        assert "EVT-001" in ids

    def test_empty_for_remote_location(self, storm_loader):
        # Middle of Pacific, far from all storms
        result = storm_loader.get_storms_affecting_location(0.0, 180.0, radius_km=100)
        assert result == []

    def test_large_radius_finds_more(self, storm_loader):
        # Small radius near ATL coast
        small = storm_loader.get_storms_affecting_location(29.7, -95.4, radius_km=10)
        large = storm_loader.get_storms_affecting_location(29.7, -95.4, radius_km=10000)
        assert len(large) >= len(small)

    def test_each_storm_returned_at_most_once(self, tmp_path):
        # Storm with multiple track points in range -- should only appear once
        storms = [{
            "TCEvent": {
                "Header": {"EventID": "EVT-X", "EventName": "Test",
                           "Category": 1, "Basin": "ATL", "Season": 2024},
                "Track": [
                    {"Latitude": 51.0, "Longitude": 0.0},
                    {"Latitude": 51.1, "Longitude": 0.1},
                    {"Latitude": 51.2, "Longitude": 0.2},
                ],
                "Impact": {},
            }
        }]
        subdir = tmp_path / "sub"
        subdir.mkdir()
        write_storms(subdir, storms)
        local_loader = StormLoader(subdir)
        result = local_loader.get_storms_affecting_location(51.1, 0.1, radius_km=50)
        assert len(result) == 1
