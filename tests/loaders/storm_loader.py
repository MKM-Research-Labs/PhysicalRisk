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
Tests for loaders.storm_loader — StormLoader class.

Covers: get_entity_id, get_entity_summary, find_by_name, find_by_category,
find_by_season, find_by_basin, get_major_hurricanes, get_track, get_impact,
and get_storms_affecting_location.
"""

import json

import pytest

from loaders.storm_loader import StormLoader


# ===========================================================================
# Fixtures
# ===========================================================================

def _make_storm(event_id, name, category=2, basin="ATL", season=2024,
                track=None, impact=None):
    return {
        "TCEvent": {
            "Header": {
                "EventID": event_id,
                "EventName": name,
                "Category": category,
                "Basin": basin,
                "Season": season,
                "StartDate": "2024-08-01",
                "EndDate": "2024-08-10",
                "PeakIntensity": 120,
            },
            "Track": track or [{"Latitude": 25.0, "Longitude": -80.0}],
            "Impact": impact or {"TotalDamage": 1_000_000},
        }
    }


STORM_FILENAME = "storm_events.json"


def _write_storms(directory, storms):
    path = directory / STORM_FILENAME
    path.write_text(json.dumps({"storms": storms}))
    return path


@pytest.fixture
def storm_dir(tmp_path):
    storms = [
        _make_storm("EVT-001", "Harvey", category=4, basin="ATL", season=2017,
                    track=[{"Latitude": 29.7, "Longitude": -95.4}]),
        _make_storm("EVT-002", "Katrina", category=5, basin="ATL", season=2005,
                    track=[{"Latitude": 29.9, "Longitude": -90.1}]),
        _make_storm("EVT-003", "Typhoon Hagibis", category=3, basin="WPAC", season=2019,
                    track=[{"Latitude": 35.0, "Longitude": 140.0}]),
        _make_storm("EVT-004", "Tropical Storm Alpha", category=1, basin="ATL", season=2024,
                    track=[{"Latitude": 40.0, "Longitude": -60.0}]),
    ]
    _write_storms(tmp_path, storms)
    return tmp_path


@pytest.fixture
def loader(storm_dir):
    return StormLoader(storm_dir)


# ===========================================================================
# get_entity_id
# ===========================================================================

class TestGetEntityId:

    def test_extracts_event_id(self, loader):
        storms = loader.load_all()
        assert loader.get_entity_id(storms[0]) == "EVT-001"

    def test_missing_id_returns_none(self, loader):
        entity = {"TCEvent": {"Header": {}}}
        assert loader.get_entity_id(entity) is None

    def test_empty_entity_returns_none(self, loader):
        assert loader.get_entity_id({}) is None


# ===========================================================================
# get_entity_summary
# ===========================================================================

class TestGetEntitySummary:

    def test_returns_summary_dict(self, loader):
        storms = loader.load_all()
        summary = loader.get_entity_summary(storms[0])
        assert summary["eventId"] == "EVT-001"
        assert summary["name"] == "Harvey"
        assert summary["category"] == 4
        assert summary["basin"] == "ATL"
        assert summary["season"] == 2017

    def test_missing_fields_return_none(self, loader):
        entity = {"TCEvent": {"Header": {}}}
        summary = loader.get_entity_summary(entity)
        assert summary["eventId"] is None
        assert summary["name"] is None


# ===========================================================================
# find_by_name
# ===========================================================================

class TestFindByName:

    def test_exact_match(self, loader):
        result = loader.find_by_name("Harvey")
        assert result is not None
        assert loader.get_entity_id(result) == "EVT-001"

    def test_case_insensitive(self, loader):
        result = loader.find_by_name("harvey")
        assert result is not None

    def test_partial_match(self, loader):
        result = loader.find_by_name("Typhoon")
        assert result is not None
        assert loader.get_entity_id(result) == "EVT-003"

    def test_no_match_returns_none(self, loader):
        assert loader.find_by_name("Nonsense Storm") is None


# ===========================================================================
# find_by_category
# ===========================================================================

class TestFindByCategory:

    def test_category_5(self, loader):
        result = loader.find_by_category(5)
        assert len(result) == 1
        assert loader.get_entity_id(result[0]) == "EVT-002"

    def test_category_3(self, loader):
        result = loader.find_by_category(3)
        ids = [loader.get_entity_id(s) for s in result]
        assert "EVT-003" in ids

    def test_no_matches_returns_empty(self, loader):
        assert loader.find_by_category(99) == []

    def test_all_category_4(self, loader):
        result = loader.find_by_category(4)
        assert all(
            s["TCEvent"]["Header"]["Category"] == 4
            for s in result
        )


# ===========================================================================
# find_by_season
# ===========================================================================

class TestFindBySeason:

    def test_season_2017(self, loader):
        result = loader.find_by_season(2017)
        assert len(result) == 1
        assert loader.get_entity_id(result[0]) == "EVT-001"

    def test_season_with_multiple(self, loader):
        result = loader.find_by_season(2024)
        assert len(result) == 1

    def test_missing_season_returns_empty(self, loader):
        assert loader.find_by_season(1900) == []


# ===========================================================================
# find_by_basin
# ===========================================================================

class TestFindByBasin:

    def test_atl_basin(self, loader):
        result = loader.find_by_basin("ATL")
        ids = [loader.get_entity_id(s) for s in result]
        assert "EVT-001" in ids
        assert "EVT-002" in ids
        assert "EVT-003" not in ids

    def test_case_insensitive(self, loader):
        result = loader.find_by_basin("atl")
        assert len(result) >= 1

    def test_wpac_basin(self, loader):
        result = loader.find_by_basin("WPAC")
        assert len(result) == 1
        assert loader.get_entity_id(result[0]) == "EVT-003"

    def test_unknown_basin_returns_empty(self, loader):
        assert loader.find_by_basin("XYZ") == []


# ===========================================================================
# get_major_hurricanes
# ===========================================================================

class TestGetMajorHurricanes:

    def test_returns_category_3_plus(self, loader):
        result = loader.get_major_hurricanes()
        categories = [s["TCEvent"]["Header"]["Category"] for s in result]
        assert all(c >= 3 for c in categories)

    def test_excludes_category_1_and_2(self, loader):
        result = loader.get_major_hurricanes()
        ids = [loader.get_entity_id(s) for s in result]
        # EVT-004 is cat 1, should be excluded
        assert "EVT-004" not in ids

    def test_includes_cat_3_4_5(self, loader):
        result = loader.get_major_hurricanes()
        ids = [loader.get_entity_id(s) for s in result]
        assert "EVT-001" in ids  # cat 4
        assert "EVT-002" in ids  # cat 5
        assert "EVT-003" in ids  # cat 3


# ===========================================================================
# get_track
# ===========================================================================

class TestGetTrack:

    def test_returns_track_for_existing_storm(self, loader):
        track = loader.get_track("EVT-001")
        assert track is not None
        assert isinstance(track, list)
        assert len(track) >= 1

    def test_track_has_lat_lon(self, loader):
        track = loader.get_track("EVT-001")
        assert "Latitude" in track[0]
        assert "Longitude" in track[0]

    def test_missing_id_returns_none(self, loader):
        assert loader.get_track("EVT-NONEXISTENT") is None


# ===========================================================================
# get_impact
# ===========================================================================

class TestGetImpact:

    def test_returns_impact_dict(self, loader):
        impact = loader.get_impact("EVT-001")
        assert isinstance(impact, dict)
        assert "TotalDamage" in impact

    def test_missing_id_returns_none(self, loader):
        assert loader.get_impact("EVT-NONEXISTENT") is None


# ===========================================================================
# get_storms_affecting_location
# ===========================================================================

class TestGetStormsAffectingLocation:

    def test_finds_nearby_storm(self, loader):
        # Harvey track: (29.7, -95.4) — search near Houston
        result = loader.get_storms_affecting_location(29.7, -95.4, radius_km=50)
        ids = [loader.get_entity_id(s) for s in result]
        assert "EVT-001" in ids

    def test_empty_for_remote_location(self, loader):
        # Middle of Pacific, far from all storms
        result = loader.get_storms_affecting_location(0.0, 180.0, radius_km=100)
        assert result == []

    def test_large_radius_finds_more(self, loader):
        # Small radius near ATL coast
        small = loader.get_storms_affecting_location(29.7, -95.4, radius_km=10)
        large = loader.get_storms_affecting_location(29.7, -95.4, radius_km=10000)
        assert len(large) >= len(small)

    def test_each_storm_returned_at_most_once(self, tmp_path):
        # Storm with multiple track points in range — should only appear once
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
        _write_storms(subdir, storms)
        local_loader = StormLoader(subdir)
        result = local_loader.get_storms_affecting_location(51.1, 0.1, radius_km=50)
        assert len(result) == 1
