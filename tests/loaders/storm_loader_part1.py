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
Tests for loaders.storm_loader — StormLoader class (part 1).

Covers: get_entity_id, get_entity_summary, find_by_name, find_by_category,
find_by_season, find_by_basin.
"""

import pytest


# ===========================================================================
# get_entity_id
# ===========================================================================

class TestGetEntityId:

    def test_extracts_event_id(self, storm_loader):
        storms = storm_loader.load_all()
        assert storm_loader.get_entity_id(storms[0]) == "EVT-001"

    def test_missing_id_returns_none(self, storm_loader):
        entity = {"TCEvent": {"Header": {}}}
        assert storm_loader.get_entity_id(entity) is None

    def test_empty_entity_returns_none(self, storm_loader):
        assert storm_loader.get_entity_id({}) is None


# ===========================================================================
# get_entity_summary
# ===========================================================================

class TestGetEntitySummary:

    def test_returns_summary_dict(self, storm_loader):
        storms = storm_loader.load_all()
        summary = storm_loader.get_entity_summary(storms[0])
        assert summary["eventId"] == "EVT-001"
        assert summary["name"] == "Harvey"
        assert summary["category"] == 4
        assert summary["basin"] == "ATL"
        assert summary["season"] == 2017

    def test_missing_fields_return_none(self, storm_loader):
        entity = {"TCEvent": {"Header": {}}}
        summary = storm_loader.get_entity_summary(entity)
        assert summary["eventId"] is None
        assert summary["name"] is None


# ===========================================================================
# find_by_name
# ===========================================================================

class TestFindByName:

    def test_exact_match(self, storm_loader):
        result = storm_loader.find_by_name("Harvey")
        assert result is not None
        assert storm_loader.get_entity_id(result) == "EVT-001"

    def test_case_insensitive(self, storm_loader):
        result = storm_loader.find_by_name("harvey")
        assert result is not None

    def test_partial_match(self, storm_loader):
        result = storm_loader.find_by_name("Typhoon")
        assert result is not None
        assert storm_loader.get_entity_id(result) == "EVT-003"

    def test_no_match_returns_none(self, storm_loader):
        assert storm_loader.find_by_name("Nonsense Storm") is None


# ===========================================================================
# find_by_category
# ===========================================================================

class TestFindByCategory:

    def test_category_5(self, storm_loader):
        result = storm_loader.find_by_category(5)
        assert len(result) == 1
        assert storm_loader.get_entity_id(result[0]) == "EVT-002"

    def test_category_3(self, storm_loader):
        result = storm_loader.find_by_category(3)
        ids = [storm_loader.get_entity_id(s) for s in result]
        assert "EVT-003" in ids

    def test_no_matches_returns_empty(self, storm_loader):
        assert storm_loader.find_by_category(99) == []

    def test_all_category_4(self, storm_loader):
        result = storm_loader.find_by_category(4)
        assert all(
            s["TCEvent"]["Header"]["Category"] == 4
            for s in result
        )


# ===========================================================================
# find_by_season
# ===========================================================================

class TestFindBySeason:

    def test_season_2017(self, storm_loader):
        result = storm_loader.find_by_season(2017)
        assert len(result) == 1
        assert storm_loader.get_entity_id(result[0]) == "EVT-001"

    def test_season_with_multiple(self, storm_loader):
        result = storm_loader.find_by_season(2024)
        assert len(result) == 1

    def test_missing_season_returns_empty(self, storm_loader):
        assert storm_loader.find_by_season(1900) == []


# ===========================================================================
# find_by_basin
# ===========================================================================

class TestFindByBasin:

    def test_atl_basin(self, storm_loader):
        result = storm_loader.find_by_basin("ATL")
        ids = [storm_loader.get_entity_id(s) for s in result]
        assert "EVT-001" in ids
        assert "EVT-002" in ids
        assert "EVT-003" not in ids

    def test_case_insensitive(self, storm_loader):
        result = storm_loader.find_by_basin("atl")
        assert len(result) >= 1

    def test_wpac_basin(self, storm_loader):
        result = storm_loader.find_by_basin("WPAC")
        assert len(result) == 1
        assert storm_loader.get_entity_id(result[0]) == "EVT-003"

    def test_unknown_basin_returns_empty(self, storm_loader):
        assert storm_loader.find_by_basin("XYZ") == []
