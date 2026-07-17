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

"""
Tests for TimeseriesLoader.

Tests timeseries-specific loading and query functionality.
"""


import pytest


class TestTimeseriesLoaderBasics:
    """Test basic TimeseriesLoader functionality."""

    def test_load_timeseries(self, timeseries_loader):
        """Test loading timeseries data."""
        records = timeseries_loader.load_all()

        assert len(records) == 3  # 3 hourly records

    def test_entity_id_is_timestamp(self, timeseries_loader):
        """Test that entity ID is the timestamp."""
        records = timeseries_loader.load_all()

        for record in records:
            entity_id = timeseries_loader.get_entity_id(record)
            assert entity_id is not None
            assert "2025-01-01" in entity_id

    def test_entity_summary(self, timeseries_loader):
        """Test timeseries summary generation."""
        summaries = timeseries_loader.list_all()

        assert len(summaries) == 3

        summary = summaries[0]
        assert 'timestamp' in summary
        assert 'hour' in summary
        assert 'reading_count' in summary
        assert 'gauge_ids' in summary


class TestTimeseriesLoaderGaugeQueries:
    """Test gauge-specific timeseries queries."""

    def test_get_readings_for_gauge(self, timeseries_loader):
        """Test getting readings for a specific gauge."""
        readings = timeseries_loader.get_readings_for_gauge("GAUGE-001")

        assert len(readings) == 3  # 3 hourly readings

        for reading in readings:
            assert 'timestamp' in reading
            assert 'level' in reading

    def test_get_readings_for_gauge_by_name(self, timeseries_loader):
        """Test getting readings using gauge name."""
        readings = timeseries_loader.get_readings_for_gauge(
            "GAUGE-001",
            gauge_name="Thames at Teddington"
        )

        assert len(readings) == 3

    def test_get_readings_for_gauge_not_found(self, timeseries_loader):
        """Test getting readings for non-existent gauge."""
        readings = timeseries_loader.get_readings_for_gauge("NONEXISTENT")

        assert readings == []

    def test_get_latest_reading(self, timeseries_loader):
        """Test getting most recent reading."""
        latest = timeseries_loader.get_latest_reading("GAUGE-001")

        assert latest is not None
        assert latest['hour'] == 2  # Last hour in test data
        assert latest['level'] == 4.8

    def test_get_peak_reading(self, timeseries_loader):
        """Test getting peak (highest) reading."""
        peak = timeseries_loader.get_peak_reading("GAUGE-001")

        assert peak is not None
        assert peak['level'] == 4.8  # Highest in test data


class TestTimeseriesLoaderStatistics:
    """Test statistics methods."""

    def test_get_gauge_statistics(self, timeseries_loader):
        """Test calculating gauge statistics."""
        stats = timeseries_loader.get_gauge_statistics("GAUGE-001")

        assert stats['gauge_id'] == "GAUGE-001"
        assert stats['reading_count'] == 3
        assert stats['level_count'] == 3
        assert stats['min_level'] == 4.2
        assert stats['max_level'] == 4.8
        assert stats['mean_level'] == pytest.approx(4.5, rel=0.01)

    def test_get_gauge_statistics_not_found(self, timeseries_loader):
        """Test statistics for non-existent gauge."""
        stats = timeseries_loader.get_gauge_statistics("NONEXISTENT")

        assert stats['reading_count'] == 0
        assert 'error' in stats

    def test_get_available_gauge_ids(self, timeseries_loader):
        """Test getting list of gauge IDs in timeseries."""
        gauge_ids = timeseries_loader.get_available_gauge_ids()

        assert len(gauge_ids) == 2
        assert "GAUGE-001" in gauge_ids
        assert "GAUGE-002" in gauge_ids


class TestTimeseriesGaugeIntegration:
    """Test integration between timeseries and gauge loaders."""

    def test_timeseries_gauge_ids_match_portfolio(
        self, timeseries_loader, gauge_loader
    ):
        """Test that timeseries gauge IDs exist in portfolio."""
        ts_gauge_ids = timeseries_loader.get_available_gauge_ids()

        for gauge_id in ts_gauge_ids:
            gauge = gauge_loader.find_by_id(gauge_id)
            assert gauge is not None, f"Gauge {gauge_id} in timeseries but not portfolio"

    def test_can_get_timeseries_for_portfolio_gauge(
        self, timeseries_loader, gauge_loader
    ):
        """Test getting timeseries for a gauge from portfolio."""
        # Get first active gauge
        active_gauges = gauge_loader.get_active_gauges()
        assert len(active_gauges) > 0

        gauge = active_gauges[0]
        gauge_id = gauge_loader.get_entity_id(gauge)
        gauge_name = gauge_loader.get_gauge_name(gauge_id)

        # Get timeseries
        readings = timeseries_loader.get_readings_for_gauge(gauge_id, gauge_name)

        # Should have readings (if gauge is in test timeseries data)
        # GAUGE-001 and GAUGE-002 are in timeseries, GAUGE-003 is not
        if gauge_id in ["GAUGE-001", "GAUGE-002"]:
            assert len(readings) > 0
