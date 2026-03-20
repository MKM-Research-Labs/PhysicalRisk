"""
Tests for models.hazard.builder — coverage expansion.

Targets uncovered lines: 61, 88, 152.
- Line 61: logger.info inside log() when verbose=True
- Line 88: exc_prob capping when 0 < exc_prob < 0.01
- Line 152: progress log every 10 gauges
"""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest


def _make_gauge_cdm(gauge_id, flood_alert=3.0, flood_warning=3.8, severe=4.5,
                    lat=51.5, lon=-0.1):
    """Create a flat gauge dict as produced by FloodGaugeCDM.create_mapping()."""
    return {
        'gauge_id': gauge_id,
        'gauge_name': f'Gauge {gauge_id}',
        'catchment_id': 'test',
        'gauge_latitude': lat,
        'gauge_longitude': lon,
        'flood_alert': flood_alert,
        'flood_warning': flood_warning,
        'severe_flood_warning': severe,
        'historical_high_level': severe * 1.1,
        'ground_level_meters': 10.0,
    }


def _make_storms(n=20):
    """Create minimal storm dicts."""
    return [
        {
            'storm_id': f'STORM-{i:04d}',
            'effective_precipitation_mm': 30.0 + i * 3,
            'duration_hours': 24,
            'intensity_factor': 0.8 + i * 0.03,
            'intensity_category': 'moderate',
            'peak_position': 0.5,
        }
        for i in range(n)
    ]


class TestBuilderLog:

    def test_verbose_true_emits_log(self, caplog):
        """Line 61: log() calls logger.info when verbose=True."""
        from models.hazard.builder import HazardCurveBuilder
        gauges = [_make_gauge_cdm("GAUGE-001")]
        storms = _make_storms(5)
        builder = HazardCurveBuilder(gauges, storms, verbose=True)

        with caplog.at_level(logging.INFO, logger="models.hazard.builder"):
            builder.log("test message")

        assert "test message" in caplog.text

    def test_verbose_false_no_log(self, caplog):
        """Line 61: log() does nothing when verbose=False."""
        from models.hazard.builder import HazardCurveBuilder
        gauges = [_make_gauge_cdm("GAUGE-001")]
        storms = _make_storms(5)
        builder = HazardCurveBuilder(gauges, storms, verbose=False)

        with caplog.at_level(logging.INFO, logger="models.hazard.builder"):
            builder.log("should not appear")

        assert "should not appear" not in caplog.text


class TestBuilderExcProbCapping:

    def test_exc_prob_capped_at_001(self):
        """Line 88: exceedance probs between 0 and 0.01 are capped to 0.01."""
        from models.hazard.builder import HazardCurveBuilder
        gauges = [_make_gauge_cdm("GAUGE-001")]
        storms = _make_storms(20)
        builder = HazardCurveBuilder(gauges, storms, verbose=False)
        curves, _ = builder.build()

        # Some curve points should have been capped at 0.01
        curve = curves['GAUGE-001']
        for pt in curve.curve_points:
            if pt.annual_exceedance_prob > 0:
                # If it was capped, it should be >= 0.01
                assert pt.annual_exceedance_prob >= 0.01 or pt.annual_exceedance_prob == 0


class TestBuilderProgressLog:

    def test_progress_log_every_10_gauges(self, caplog):
        """Line 152: progress logged every 10 gauges."""
        from models.hazard.builder import HazardCurveBuilder
        # Create 11 gauges to trigger the i+1 % 10 == 0 condition
        gauges = [_make_gauge_cdm(f"GAUGE-{i:03d}", lon=-0.1 + i * 0.01)
                  for i in range(11)]
        storms = _make_storms(10)
        builder = HazardCurveBuilder(gauges, storms, verbose=True)

        with caplog.at_level(logging.INFO, logger="models.hazard.builder"):
            curves, responses = builder.build()

        assert len(curves) == 11
        # Should see "Processed 10/11 gauges" in the log
        assert "10/11" in caplog.text or "Processed" in caplog.text
