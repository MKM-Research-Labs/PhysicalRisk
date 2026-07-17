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

"""Integration tests for single gauge flood analysis."""

from tests.reports.gauge._helpers import (
    count_gauges_above_warning,
    find_highest_level_gauge,
    load_gauge_metadata,
    load_gauge_readings,
    run_single_gauge_test,
)


class TestSingleGaugeAnalysis:
    """Integration tests for single gauge flood analysis."""

    def test_load_gauge_metadata(self, thames_input_dir):
        """Test loading gauge metadata from JSON."""
        gauges = load_gauge_metadata(thames_input_dir)

        assert gauges is not None
        assert len(gauges) == 4
        assert "gauge_id" in gauges.columns
        assert "flood_warning_level" in gauges.columns

    def test_load_gauge_readings(self, thames_input_dir):
        """Test loading gauge time series."""
        readings = load_gauge_readings(thames_input_dir)

        assert readings is not None
        assert "THAMES_TEDDINGTON" in readings
        assert len(readings["THAMES_TEDDINGTON"]) > 0

    def test_full_gauge_analysis(self, thames_input_dir):
        """Test complete gauge analysis workflow."""
        results = run_single_gauge_test(thames_input_dir, gauge_id="THAMES_TEDDINGTON")

        assert results['success'] is True
        assert results['gauge']['gauge_id'] == "THAMES_TEDDINGTON"
        assert 'flood_analysis' in results
        assert results['flood_analysis']['peak_level'] > 0

    def test_gauge_status_in_analysis(self, thames_input_dir):
        """Analysis should include flood status."""
        results = run_single_gauge_test(thames_input_dir, gauge_id="THAMES_TEDDINGTON")

        assert 'status' in results['flood_analysis']
        assert results['flood_analysis']['status'] in ["NORMAL", "ALERT", "WARNING", "SEVERE"]

    def test_gauge_not_found(self, thames_input_dir):
        """Handle non-existent gauge gracefully."""
        results = run_single_gauge_test(thames_input_dir, gauge_id="NONEXISTENT_GAUGE")

        assert results['success'] is False
        assert len(results['errors']) > 0


class TestMultiGaugeComparison:
    """Test comparing multiple gauges."""

    def test_find_highest_level_gauge(self, thames_input_dir):
        """Find gauge with highest current level."""
        highest = find_highest_level_gauge(thames_input_dir)

        assert highest is not None
        assert 'gauge_id' in highest
        assert 'level' in highest

    def test_count_gauges_above_threshold(self, thames_input_dir, sample_gauges_df):
        """Count gauges exceeding warning level."""
        count = count_gauges_above_warning(thames_input_dir)

        assert count >= 0
        assert count <= len(sample_gauges_df)
