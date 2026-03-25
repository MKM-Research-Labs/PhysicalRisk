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
Tests for GaugeLoader.

Tests gauge-specific loading and query functionality.
"""

import pytest


class TestGaugeLoaderBasics:
    """Test basic GaugeLoader functionality."""

    def test_load_gauges(self, gauge_loader):
        """Test loading gauge portfolio."""
        gauges = gauge_loader.load_all()

        assert len(gauges) == 3

    def test_entity_id_extraction(self, gauge_loader):
        """Test GaugeID extraction from nested structure."""
        gauges = gauge_loader.load_all()

        for gauge in gauges:
            gauge_id = gauge_loader.get_entity_id(gauge)
            assert gauge_id is not None
            assert gauge_id.startswith(("GAUGE-", "SYNTH-"))

    def test_entity_summary(self, gauge_loader):
        """Test gauge summary generation."""
        summaries = gauge_loader.list_all()

        assert len(summaries) == 3

        summary = summaries[0]
        assert 'gaugeId' in summary
        assert 'name' in summary
        assert 'type' in summary
        assert 'owner' in summary
        assert 'status' in summary
        assert 'location' in summary


class TestGaugeLoaderQueries:
    """Test gauge-specific query methods."""

    def test_find_by_id(self, gauge_loader):
        """Test finding gauge by ID."""
        gauge = gauge_loader.find_by_id("GAUGE-001")

        assert gauge is not None
        assert gauge['FloodGauge']['Header']['GaugeName'] == "Thames at Teddington"

    def test_find_by_name(self, gauge_loader):
        """Test finding gauge by name."""
        gauge = gauge_loader.find_by_name("Teddington")

        assert gauge is not None
        assert gauge_loader.get_entity_id(gauge) == "GAUGE-001"

    def test_find_by_name_case_insensitive(self, gauge_loader):
        """Test name search is case insensitive."""
        gauge = gauge_loader.find_by_name("TEDDINGTON")

        assert gauge is not None

    def test_find_by_owner(self, gauge_loader):
        """Test finding gauges by owner."""
        ea_gauges = gauge_loader.find_by_owner("Environment Agency")

        assert len(ea_gauges) == 2

        usgs_gauges = gauge_loader.find_by_owner("USGS")
        assert len(usgs_gauges) == 1

    def test_find_by_status_active(self, gauge_loader):
        """Test finding active gauges."""
        active = gauge_loader.find_by_status("Active")

        assert len(active) == 2

    def test_find_by_status_inactive(self, gauge_loader):
        """Test finding inactive gauges."""
        inactive = gauge_loader.find_by_status("Inactive")

        assert len(inactive) == 1
        assert gauge_loader.get_entity_id(inactive[0]) == "GAUGE-003"

    def test_find_by_type_river(self, gauge_loader):
        """Test finding river gauges."""
        river = gauge_loader.find_by_type("River")

        assert len(river) == 2

    def test_find_by_type_tidal(self, gauge_loader):
        """Test finding tidal gauges."""
        tidal = gauge_loader.find_by_type("Tidal")

        assert len(tidal) == 1


class TestGaugeLoaderHelpers:
    """Test helper methods."""

    def test_get_active_gauges(self, gauge_loader):
        """Test getting active gauges."""
        active = gauge_loader.get_active_gauges()

        assert len(active) == 2
        for gauge in active:
            status = gauge['FloodGauge']['SensorDetails']['GaugeInformation']['OperationalStatus']
            assert status == "Active"

    def test_get_gauge_name(self, gauge_loader):
        """Test getting gauge name by ID."""
        name = gauge_loader.get_gauge_name("GAUGE-001")

        assert name == "Thames at Teddington"

    def test_get_gauge_name_not_found(self, gauge_loader):
        """Test getting name for non-existent gauge."""
        name = gauge_loader.get_gauge_name("NONEXISTENT")

        assert name is None

    def test_get_coordinates(self, gauge_loader):
        """Test getting gauge coordinates."""
        coords = gauge_loader.get_coordinates("GAUGE-001")

        assert coords is not None
        lat, lon = coords
        assert lat == pytest.approx(51.4309, rel=1e-4)
        assert lon == pytest.approx(-0.3211, rel=1e-4)

    def test_get_flood_stages(self, gauge_loader):
        """Test getting flood stage thresholds."""
        stages = gauge_loader.get_flood_stages("GAUGE-001")

        assert stages is not None
        assert stages['ActionStage'] == 4.5
        assert stages['MinorFlood'] == 5.0
        assert stages['ModerateFlood'] == 5.5
        assert stages['MajorFlood'] == 6.0


class TestGaugeLoaderSpatial:
    """Test spatial query methods."""

    def test_get_gauges_in_radius(self, gauge_loader):
        """Test finding gauges within radius."""
        # Teddington coordinates
        lat, lon = 51.4309, -0.3211

        # 5km radius should find at least Teddington
        nearby = gauge_loader.get_gauges_in_radius(lat, lon, 5)
        assert len(nearby) >= 1

        # 20km radius should find all Thames gauges
        nearby = gauge_loader.get_gauges_in_radius(lat, lon, 20)
        assert len(nearby) >= 2

    def test_get_gauges_in_radius_none_found(self, gauge_loader):
        """Test radius search with no matches."""
        # Far away coordinates
        lat, lon = 0.0, 0.0

        nearby = gauge_loader.get_gauges_in_radius(lat, lon, 10)
        assert len(nearby) == 0
