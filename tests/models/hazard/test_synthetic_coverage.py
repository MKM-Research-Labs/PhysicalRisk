"""
Tests for models.statistics.synthetic — coverage expansion.

Targets uncovered lines: 138-141.
These lines handle injecting historical high when the date was in range
but was not placed during generation (historical_high_placed is False
after the while loop, meaning the date matched a date string but not
via datetime.date() comparison in the main loop).

Line 137: if historical_high_dt and not historical_high_placed:
Line 138:     for obs in daily_observations:
Line 139:         if obs["date"] == historical_high_date:
Line 140:             obs["level_meters"] = historical_high
Line 141:             break
"""

from datetime import datetime, timedelta

import pytest


def _make_gauge(historical_high=6.0, historical_high_date=None):
    return {
        "FloodGauge": {
            "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test"},
            "FloodStages": {
                "FloodAlert": 4.0,
                "FloodWarning": 4.5,
                "SevereFloodWarning": 5.0,
            },
            "SensorStats": {
                "HistoricalHighLevel": historical_high,
                "HistoricalHighDate": historical_high_date,
                "FrequencyExceedLevel3": 2,
            },
        }
    }


class TestHistoricalHighInjection:

    def test_historical_high_injected_post_loop(self):
        """Lines 138-141: historical high injected after main loop.

        The main loop checks `current_date.date() == historical_high_dt.date()`.
        If the date is in range but the string comparison at line 139 matches,
        the post-loop injection fires. We use a date within range and verify
        the historical high level appears in the output.
        """
        from models.statistics.synthetic import generate_synthetic_timeseries

        # Pick a date well within the 1-year range
        target_date = (datetime.now() - timedelta(days=50)).strftime("%Y-%m-%d")
        gauge = _make_gauge(historical_high=9.99, historical_high_date=target_date)

        result = generate_synthetic_timeseries(gauge, years=1, seed=42)

        # Find the observation for that date
        match = [o for o in result if o["date"] == target_date]
        assert len(match) == 1
        assert match[0]["level_meters"] == 9.99

    def test_historical_high_not_in_range_skipped(self):
        """When historical_high_dt is None (out of range), post-loop block skipped."""
        from models.statistics.synthetic import generate_synthetic_timeseries

        gauge = _make_gauge(historical_high=8.0, historical_high_date="1850-01-01")
        result = generate_synthetic_timeseries(gauge, years=1, seed=42)

        # No observation should have 8.0 (out of range date, so no injection)
        assert all(o["level_meters"] != 8.0 for o in result)

    def test_no_historical_high_date(self):
        """When historical_high_date is None, both branches skipped."""
        from models.statistics.synthetic import generate_synthetic_timeseries

        gauge = _make_gauge(historical_high=7.0, historical_high_date=None)
        result = generate_synthetic_timeseries(gauge, years=1, seed=42)
        assert isinstance(result, list)
        assert len(result) > 0
