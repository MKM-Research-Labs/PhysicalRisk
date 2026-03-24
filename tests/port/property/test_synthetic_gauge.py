# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Tests for synthetic gauge creation, interpolation, and integration
into the propertyts and propertyhc pipelines.
"""

import math

import pytest

from models.floodrisk.spatial import (
    haversine_distance,
    nearest_point_on_polyline,
    nearest_point_on_segment,
)
from port.src.property.ts.synthetic import (
    SYNTH_PREFIX,
    create_synthetic_gauge,
    create_synthetic_gaugets,
    create_synthetic_hazard_curve,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# A simple 3-point polyline along a roughly east-west river
POLYLINE = [
    (51.45, -0.50, 3.0, "GAUGE-AAA00001"),
    (51.46, -0.30, 4.0, "GAUGE-BBB00002"),
    (51.47, -0.10, 5.0, "GAUGE-CCC00003"),
]

GAUGE_LOOKUP = {
    "GAUGE-AAA00001": {
        "gauge_id": "GAUGE-AAA00001",
        "lat": 51.45, "lon": -0.50,
        "elevation": 3.0,
        "alert_level": 3.5, "warning_level": 4.5, "severe_level": 5.0,
    },
    "GAUGE-BBB00002": {
        "gauge_id": "GAUGE-BBB00002",
        "lat": 51.46, "lon": -0.30,
        "elevation": 4.0,
        "alert_level": 4.0, "warning_level": 5.0, "severe_level": 6.0,
    },
    "GAUGE-CCC00003": {
        "gauge_id": "GAUGE-CCC00003",
        "lat": 51.47, "lon": -0.10,
        "elevation": 5.0,
        "alert_level": 4.5, "warning_level": 5.5, "severe_level": 7.0,
    },
}


# ---------------------------------------------------------------------------
# nearest_point_on_segment
# ---------------------------------------------------------------------------

class TestNearestPointOnSegment:

    def test_returns_t_at_midpoint(self):
        """Midpoint of a segment should yield t ~= 0.5."""
        ax, ay = 51.45, -0.50
        bx, by = 51.47, -0.10
        mid_lat = (ax + bx) / 2
        mid_lon = (ay + by) / 2
        nx, ny, dist_m, t = nearest_point_on_segment(
            mid_lat, mid_lon, ax, ay, bx, by)
        assert abs(t - 0.5) < 0.01
        assert dist_m < 1.0  # essentially on the segment

    def test_clamps_to_start(self):
        """Point before segment start clamps t to 0."""
        ax, ay = 51.45, -0.50
        bx, by = 51.47, -0.10
        # Far before A
        _, _, _, t = nearest_point_on_segment(51.43, -0.70, ax, ay, bx, by)
        assert t == 0.0

    def test_clamps_to_end(self):
        """Point past segment end clamps t to 1."""
        ax, ay = 51.45, -0.50
        bx, by = 51.47, -0.10
        # Far past B
        _, _, _, t = nearest_point_on_segment(51.49, 0.10, ax, ay, bx, by)
        assert t == 1.0

    def test_degenerate_segment(self):
        """Zero-length segment returns t=0 and distance to the point."""
        nx, ny, dist_m, t = nearest_point_on_segment(
            51.45, -0.50, 51.46, -0.30, 51.46, -0.30)
        assert t == 0.0
        assert dist_m > 0


# ---------------------------------------------------------------------------
# nearest_point_on_polyline
# ---------------------------------------------------------------------------

class TestNearestPointOnPolyline:

    def test_finds_closest_segment(self):
        """Property near second segment projects onto that segment."""
        # Point near midpoint of segment 1-2 (BBB-CCC), offset perpendicular
        prop_lat, prop_lon = 51.465, -0.20
        nx, ny, dist_m, seg_idx, t = nearest_point_on_polyline(
            prop_lat, prop_lon, POLYLINE)
        assert seg_idx == 1  # second segment
        assert 0 < t < 1
        assert dist_m > 0

    def test_returns_reasonable_distance(self):
        """Distance should be positive and within expected range."""
        prop_lat, prop_lon = 51.455, -0.40
        _, _, dist_m, _, _ = nearest_point_on_polyline(
            prop_lat, prop_lon, POLYLINE)
        assert 0 < dist_m < 5000  # should be a few km at most


# ---------------------------------------------------------------------------
# create_synthetic_gauge
# ---------------------------------------------------------------------------

class TestCreateSyntheticGauge:

    def test_creates_gauge_with_interpolated_fields(self):
        prop_lat, prop_lon = 51.455, -0.40  # near first segment
        result = create_synthetic_gauge(
            prop_lat, prop_lon, dict(GAUGE_LOOKUP), POLYLINE)
        assert result is not None
        synth, ga_id, gb_id, perp_dist, alpha = result

        assert synth['gauge_id'].startswith(SYNTH_PREFIX)
        assert ga_id in GAUGE_LOOKUP
        assert gb_id in GAUGE_LOOKUP
        assert perp_dist > 0
        assert 0 < alpha < 1

        # Elevation should be between the two flanking gauges
        ga = GAUGE_LOOKUP[ga_id]
        gb = GAUGE_LOOKUP[gb_id]
        assert min(ga['elevation'], gb['elevation']) <= synth['elevation'] <= max(ga['elevation'], gb['elevation'])

    def test_returns_none_for_short_polyline(self):
        """Single-point polyline cannot produce a synthetic gauge."""
        result = create_synthetic_gauge(
            51.45, -0.50, GAUGE_LOOKUP, [POLYLINE[0]])
        assert result is None

    def test_returns_none_at_polyline_start(self):
        """Property projecting to very start of polyline falls back."""
        # Far upstream of first gauge
        result = create_synthetic_gauge(
            51.43, -0.70, GAUGE_LOOKUP, POLYLINE)
        assert result is None

    def test_returns_none_at_polyline_end(self):
        """Property projecting to very end of polyline falls back."""
        # Far downstream of last gauge
        result = create_synthetic_gauge(
            51.49, 0.10, GAUGE_LOOKUP, POLYLINE)
        assert result is None

    def test_distance_is_perpendicular_to_river(self):
        """Synthetic gauge distance should match perpendicular river distance."""
        prop_lat, prop_lon = 51.455, -0.40
        result = create_synthetic_gauge(
            prop_lat, prop_lon, dict(GAUGE_LOOKUP), POLYLINE)
        _, _, _, perp_dist, _ = result

        # Compare with direct polyline projection
        _, _, polyline_dist, _, _ = nearest_point_on_polyline(
            prop_lat, prop_lon, POLYLINE)
        assert abs(perp_dist - polyline_dist) < 0.1  # should be identical


# ---------------------------------------------------------------------------
# create_synthetic_gaugets
# ---------------------------------------------------------------------------

class TestCreateSyntheticGaugets:

    def test_interpolates_storm_responses(self):
        gaugets = {
            "GAUGE-AAA00001": {
                "storm_responses": {"responses": [
                    {"storm_id": "S1", "peak_level_m": 4.0, "exceeded_alert": True},
                    {"storm_id": "S2", "peak_level_m": 3.0, "exceeded_alert": False},
                ]},
                "flood_simulation": {"readings": []},
            },
            "GAUGE-BBB00002": {
                "storm_responses": {"responses": [
                    {"storm_id": "S1", "peak_level_m": 6.0, "exceeded_alert": True},
                    {"storm_id": "S3", "peak_level_m": 5.0, "exceeded_alert": True},
                ]},
                "flood_simulation": {"readings": []},
            },
        }
        result = create_synthetic_gaugets(
            0.5, "GAUGE-AAA00001", "GAUGE-BBB00002", gaugets)

        responses = result['storm_responses']['responses']
        storm_ids = {r['storm_id'] for r in responses}
        # S1 appears in both, S2 only in A, S3 only in B
        assert storm_ids == {"S1", "S2", "S3"}

        # S1 should be interpolated (4+6)/2 = 5.0
        s1 = [r for r in responses if r['storm_id'] == 'S1'][0]
        assert s1['peak_level_m'] == 5.0

    def test_interpolates_readings(self):
        gaugets = {
            "GA": {
                "storm_responses": {"responses": []},
                "flood_simulation": {"readings": [
                    {"hour": 0, "waterLevel": 2.0},
                    {"hour": 1, "waterLevel": 4.0},
                ]},
            },
            "GB": {
                "storm_responses": {"responses": []},
                "flood_simulation": {"readings": [
                    {"hour": 0, "waterLevel": 6.0},
                    {"hour": 1, "waterLevel": 8.0},
                ]},
            },
        }
        result = create_synthetic_gaugets(0.5, "GA", "GB", gaugets)
        readings = result['flood_simulation']['readings']
        assert len(readings) == 2
        assert readings[0]['waterLevel'] == 4.0   # (2+6)/2
        assert readings[1]['waterLevel'] == 6.0   # (4+8)/2


# ---------------------------------------------------------------------------
# create_synthetic_hazard_curve
# ---------------------------------------------------------------------------

class TestCreateSyntheticHazardCurve:

    def test_interpolates_hazard_rates(self):
        hc_a = {
            "annual_hazard_rate_alert": 0.10,
            "annual_hazard_rate_warning": 0.04,
            "annual_hazard_rate_severe": 0.01,
            "latitude": 51.45, "longitude": -0.50,
        }
        hc_b = {
            "annual_hazard_rate_alert": 0.06,
            "annual_hazard_rate_warning": 0.02,
            "annual_hazard_rate_severe": 0.005,
            "latitude": 51.46, "longitude": -0.30,
        }
        result = create_synthetic_hazard_curve(0.5, hc_a, hc_b)
        assert abs(result['annual_hazard_rate_alert'] - 0.08) < 1e-6
        assert abs(result['annual_hazard_rate_warning'] - 0.03) < 1e-6

    def test_interpolates_term_structure(self):
        hc_a = {
            "term_structure_alert": [
                {"year": 1, "survival_prob": 0.90, "prob_at_least_one": 0.10},
            ],
            "latitude": 0, "longitude": 0,
        }
        hc_b = {
            "term_structure_alert": [
                {"year": 1, "survival_prob": 0.80, "prob_at_least_one": 0.20},
            ],
            "latitude": 0, "longitude": 0,
        }
        result = create_synthetic_hazard_curve(0.5, hc_a, hc_b)
        ts = result['term_structure_alert']
        assert len(ts) == 1
        assert abs(ts[0]['survival_prob'] - 0.85) < 1e-6

    def test_alpha_zero_equals_gauge_a(self):
        hc_a = {"annual_hazard_rate_alert": 0.10, "latitude": 0, "longitude": 0}
        hc_b = {"annual_hazard_rate_alert": 0.06, "latitude": 0, "longitude": 0}
        result = create_synthetic_hazard_curve(0.0, hc_a, hc_b)
        assert abs(result['annual_hazard_rate_alert'] - 0.10) < 1e-6

    def test_alpha_one_equals_gauge_b(self):
        hc_a = {"annual_hazard_rate_alert": 0.10, "latitude": 0, "longitude": 0}
        hc_b = {"annual_hazard_rate_alert": 0.06, "latitude": 0, "longitude": 0}
        result = create_synthetic_hazard_curve(1.0, hc_a, hc_b)
        assert abs(result['annual_hazard_rate_alert'] - 0.06) < 1e-6


# ---------------------------------------------------------------------------
# Integration: _find_nearest_gauges with polyline
# ---------------------------------------------------------------------------

class TestFindNearestGaugesWithPolyline:

    def _make_flood_mixin(self):
        from port.src.property.ts.flood import FloodMixin
        mixin = FloodMixin()
        mixin._storm_to_sequence = {}
        return mixin

    def test_returns_two_real_plus_synthetic(self):
        mixin = self._make_flood_mixin()
        lookup = dict(GAUGE_LOOKUP)
        prop_lat, prop_lon = 51.455, -0.40

        result = mixin._find_nearest_gauges(
            prop_lat, prop_lon, lookup,
            gauge_polyline=POLYLINE)

        assert len(result) == 3
        synth_entries = [r for r in result if r.get('is_synthetic')]
        assert len(synth_entries) == 1
        real_entries = [r for r in result if not r.get('is_synthetic')]
        assert len(real_entries) == 2

    def test_synthetic_gauge_is_closest(self):
        """Synthetic gauge (perpendicular to river) should be closer than flanking stations."""
        mixin = self._make_flood_mixin()
        lookup = dict(GAUGE_LOOKUP)
        # Property offset perpendicular from river, between gauges A and B
        prop_lat, prop_lon = 51.44, -0.40

        result = mixin._find_nearest_gauges(
            prop_lat, prop_lon, lookup,
            gauge_polyline=POLYLINE)

        synth = [r for r in result if r.get('is_synthetic')][0]
        reals = [r for r in result if not r.get('is_synthetic')]

        # Synthetic (perpendicular) distance should be less than
        # haversine to either flanking station
        for real in reals:
            assert synth['distance_m'] < real['distance_m']

    def test_fallback_without_polyline(self):
        """Without polyline, falls back to original 3-nearest haversine."""
        mixin = self._make_flood_mixin()
        lookup = dict(GAUGE_LOOKUP)

        result = mixin._find_nearest_gauges(51.455, -0.40, lookup)

        assert len(result) == 3
        synth_entries = [r for r in result if r.get('is_synthetic')]
        assert len(synth_entries) == 0

    def test_injects_synthetic_into_gauge_lookup(self):
        """Synthetic gauge should be added to gauge_lookup for downstream use."""
        mixin = self._make_flood_mixin()
        lookup = dict(GAUGE_LOOKUP)
        original_count = len(lookup)

        mixin._find_nearest_gauges(
            51.455, -0.40, lookup, gauge_polyline=POLYLINE)

        assert len(lookup) == original_count + 1
        synth_ids = [k for k in lookup if k.startswith(SYNTH_PREFIX)]
        assert len(synth_ids) == 1
