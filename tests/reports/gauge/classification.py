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

"""Tests for gauge status classification, level analysis, and exceedance probability."""

from tests.reports.gauge._helpers import (
    calculate_duration_above_threshold,
    calculate_level_trend,
    classify_gauge_status,
    estimate_annual_exceedance_probability,
    get_current_level,
    get_peak_level,
)
from datetime import datetime


class TestGaugeStatusClassification:
    """Test gauge flood status classification."""

    def test_normal_status(self, sample_gauge):
        """Level below alert = normal."""
        status = classify_gauge_status(3.0, sample_gauge)
        assert status == "NORMAL"

    def test_alert_status(self, sample_gauge):
        """Level at alert threshold."""
        status = classify_gauge_status(5.0, sample_gauge)
        assert status == "ALERT"

    def test_warning_status(self, sample_gauge):
        """Level at warning threshold."""
        status = classify_gauge_status(5.5, sample_gauge)
        assert status == "WARNING"

    def test_severe_status(self, sample_gauge):
        """Level at severe threshold."""
        status = classify_gauge_status(6.5, sample_gauge)
        assert status == "SEVERE"

    def test_between_thresholds(self, sample_gauge):
        """Level between alert and warning."""
        status = classify_gauge_status(5.3, sample_gauge)
        assert status == "ALERT"


class TestGaugeLevelAnalysis:
    """Test gauge level analysis functions."""

    def test_peak_level_detection(self, flood_event_readings):
        """Detect peak level in time series."""
        peak = get_peak_level(flood_event_readings)
        assert peak['level'] > 6.0  # Should exceed warning
        assert 'timestamp' in peak

    def test_peak_timing(self, flood_event_readings):
        """Peak should occur around hour 24."""
        peak = get_peak_level(flood_event_readings)
        peak_time = datetime.fromisoformat(peak['timestamp'])
        base_time = datetime.fromisoformat(flood_event_readings[0]['timestamp'])
        hours_to_peak = (peak_time - base_time).total_seconds() / 3600
        assert 20 < hours_to_peak < 28

    def test_current_level(self, flood_event_readings):
        """Get most recent reading."""
        current = get_current_level(flood_event_readings)
        assert current == flood_event_readings[-1]['level']

    def test_level_trend_rising(self):
        """Detect rising water levels."""
        readings = [
            {"level": 3.0}, {"level": 3.5}, {"level": 4.0}, {"level": 4.5}
        ]
        trend = calculate_level_trend(readings)
        assert trend == "RISING"

    def test_level_trend_falling(self):
        """Detect falling water levels."""
        readings = [
            {"level": 5.0}, {"level": 4.5}, {"level": 4.0}, {"level": 3.5}
        ]
        trend = calculate_level_trend(readings)
        assert trend == "FALLING"

    def test_level_trend_stable(self):
        """Detect stable water levels."""
        readings = [
            {"level": 4.0}, {"level": 4.05}, {"level": 3.98}, {"level": 4.02}
        ]
        trend = calculate_level_trend(readings)
        assert trend == "STABLE"


class TestFloodDuration:
    """Test flood duration calculations."""

    def test_duration_above_threshold(self, flood_event_readings, sample_gauge):
        """Calculate time above warning level."""
        warning_level = sample_gauge['flood_warning_level']
        duration = calculate_duration_above_threshold(flood_event_readings, warning_level)
        assert duration > 0

    def test_no_duration_normal_readings(self, normal_readings, sample_gauge):
        """No time above threshold for normal readings."""
        warning_level = sample_gauge['flood_warning_level']
        duration = calculate_duration_above_threshold(normal_readings, warning_level)
        assert duration == 0

    def test_duration_hours_calculation(self, flood_event_readings, sample_gauge):
        """Duration should be in reasonable range."""
        warning_level = sample_gauge['flood_warning_level']
        duration = calculate_duration_above_threshold(flood_event_readings, warning_level)
        assert 5 < duration < 30


class TestExceedanceProbability:
    """Test exceedance probability calculations."""

    def test_high_level_low_probability(self, sample_gauge):
        """Severe floods should be rare."""
        prob = estimate_annual_exceedance_probability(
            sample_gauge['severe_flood_level'],
            sample_gauge
        )
        assert prob <= 0.05 + 1e-9

    def test_low_level_high_probability(self, sample_gauge):
        """Normal levels should be common."""
        prob = estimate_annual_exceedance_probability(
            sample_gauge['typical_range_max'],
            sample_gauge
        )
        assert prob > 0.5

    def test_return_period_calculation(self, sample_gauge):
        """Return period should be inverse of probability."""
        level = sample_gauge['flood_warning_level']
        prob = estimate_annual_exceedance_probability(level, sample_gauge)
        return_period = 1.0 / prob if prob > 0 else float('inf')
        assert return_period > 1
