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
Tests for PropertyLoader.

Tests property-specific loading and query functionality.
"""

import pytest


class TestPropertyLoaderBasics:
    """Test basic PropertyLoader functionality."""

    def test_load_properties(self, property_loader):
        """Test loading property portfolio."""
        properties = property_loader.load_all()

        assert len(properties) == 3

    def test_entity_id_extraction(self, property_loader):
        """Test PropertyID extraction from nested structure."""
        properties = property_loader.load_all()

        for prop in properties:
            prop_id = property_loader.get_entity_id(prop)
            assert prop_id is not None
            assert prop_id.startswith("PROP-")

    def test_entity_summary(self, property_loader):
        """Test property summary generation."""
        summaries = property_loader.list_all()

        assert len(summaries) == 3

        summary = summaries[0]
        assert 'propertyId' in summary
        assert 'address' in summary
        assert 'city' in summary
        assert 'state' in summary
        assert 'zipCode' in summary


class TestPropertyLoaderQueries:
    """Test property-specific query methods."""

    def test_find_by_id(self, property_loader):
        """Test finding property by ID."""
        prop = property_loader.find_by_id("PROP-001")

        assert prop is not None
        assert prop['PropertyHeader']['Location']['City'] == "Miami"

    def test_find_by_address(self, property_loader):
        """Test finding property by address."""
        prop = property_loader.find_by_address("Main Street")

        assert prop is not None
        assert "PROP-001" == property_loader.get_entity_id(prop)

    def test_find_by_address_case_insensitive(self, property_loader):
        """Test address search is case insensitive."""
        prop = property_loader.find_by_address("MAIN STREET")

        assert prop is not None

    def test_find_by_address_not_found(self, property_loader):
        """Test address search with no match."""
        prop = property_loader.find_by_address("Nonexistent Road")

        assert prop is None

    def test_find_by_zip(self, property_loader):
        """Test finding properties by zip code."""
        props = property_loader.find_by_zip("33101")

        assert len(props) == 1
        assert property_loader.get_entity_id(props[0]) == "PROP-001"

    def test_find_by_zip_multiple(self, property_loader):
        """Test finding multiple properties in same zip."""
        # Both FL properties have different zips in our test data
        props = property_loader.find_by_zip("33139")

        assert len(props) == 1

    def test_find_by_state(self, property_loader):
        """Test finding properties by state."""
        fl_props = property_loader.find_by_state("FL")

        assert len(fl_props) == 2

        tx_props = property_loader.find_by_state("TX")
        assert len(tx_props) == 1

    def test_find_by_state_case_insensitive(self, property_loader):
        """Test state search is case insensitive."""
        props = property_loader.find_by_state("fl")

        assert len(props) == 2


class TestPropertyLoaderLocation:
    """Test location-related methods."""

    def test_get_location(self, property_loader):
        """Test getting location data."""
        location = property_loader.get_location("PROP-001")

        assert location is not None
        assert location['City'] == "Miami"
        assert location['State'] == "FL"

    def test_get_location_not_found(self, property_loader):
        """Test getting location for non-existent property."""
        location = property_loader.get_location("NONEXISTENT")

        assert location is None

    def test_get_coordinates(self, property_loader):
        """Test getting coordinates."""
        coords = property_loader.get_coordinates("PROP-001")

        assert coords is not None
        lat, lon = coords
        assert lat == pytest.approx(25.7617, rel=1e-4)
        assert lon == pytest.approx(-80.1918, rel=1e-4)

    def test_get_coordinates_not_found(self, property_loader):
        """Test getting coordinates for non-existent property."""
        coords = property_loader.get_coordinates("NONEXISTENT")

        assert coords is None

    def test_get_properties_in_radius(self, property_loader):
        """Test finding properties within radius."""
        # Miami coordinates
        lat, lon = 25.7617, -80.1918

        # 10km radius should find Miami properties
        nearby = property_loader.get_properties_in_radius(lat, lon, 10)
        assert len(nearby) >= 1

        # 50km radius should find both FL properties
        nearby = property_loader.get_properties_in_radius(lat, lon, 50)
        assert len(nearby) == 2

        # 1km radius might only find exact match
        nearby = property_loader.get_properties_in_radius(lat, lon, 1)
        assert len(nearby) >= 1


class TestPropertyLoaderAggregations:
    """Test aggregation methods."""

    def test_get_total_value(self, property_loader):
        """Test total portfolio value calculation."""
        total = property_loader.get_total_value()

        # Sum of test data: 450000 + 1250000 + 350000
        assert total == 2050000

    def test_get_value_by_state(self, property_loader):
        """Test value aggregation by state."""
        values = property_loader.get_value_by_state()

        assert 'FL' in values
        assert 'TX' in values

        # FL: 450000 + 1250000 = 1700000
        assert values['FL'] == 1700000

        # TX: 350000
        assert values['TX'] == 350000
