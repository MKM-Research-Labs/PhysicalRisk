"""Tests for synthetic gauge priority in nearest gauge selection."""

import pytest

from port.src.property.ts.flood.nearest import NearestGaugeMixin


class FakeGen(NearestGaugeMixin):
    pass


def _make_gauge_lookup():
    """Build a gauge lookup with 1 synthetic + 3 real gauges at known positions."""
    return {
        'SYNTH-001': {
            'gauge_id': 'SYNTH-001',
            'lat': 51.500, 'lon': -0.100,
            'elevation': 5.0, 'alert_level': 4.0,
            'warning_level': 5.5, 'severe_level': 7.0,
        },
        'GAUGE-AAA': {
            'gauge_id': 'GAUGE-AAA',
            'lat': 51.501, 'lon': -0.100,  # very close
            'elevation': 5.5, 'alert_level': 4.0,
            'warning_level': 5.5, 'severe_level': 7.0,
        },
        'GAUGE-BBB': {
            'gauge_id': 'GAUGE-BBB',
            'lat': 51.505, 'lon': -0.100,  # medium distance
            'elevation': 6.0, 'alert_level': 4.0,
            'warning_level': 5.5, 'severe_level': 7.0,
        },
        'GAUGE-CCC': {
            'gauge_id': 'GAUGE-CCC',
            'lat': 51.510, 'lon': -0.100,  # far
            'elevation': 7.0, 'alert_level': 4.0,
            'warning_level': 5.5, 'severe_level': 7.0,
        },
    }


class TestSyntheticAlwaysFirst:
    """Synthetic gauge must always be at position [0]."""

    def test_synthetic_at_position_zero(self):
        gen = FakeGen()
        lookup = _make_gauge_lookup()
        # Property near GAUGE-AAA (closer than SYNTH-001)
        result = gen._find_nearest_gauges(51.501, -0.100, lookup, n=3)
        assert result[0]['gauge_id'] == 'SYNTH-001'

    def test_synthetic_first_even_when_far(self):
        gen = FakeGen()
        lookup = _make_gauge_lookup()
        # Move synthetic far away
        lookup['SYNTH-001']['lat'] = 51.520
        result = gen._find_nearest_gauges(51.501, -0.100, lookup, n=3)
        assert result[0]['gauge_id'] == 'SYNTH-001'

    def test_real_gauges_sorted_by_distance_after_synthetic(self):
        gen = FakeGen()
        lookup = _make_gauge_lookup()
        result = gen._find_nearest_gauges(51.501, -0.100, lookup, n=3)
        # Position [0] is synthetic
        assert result[0]['gauge_id'].startswith('SYNTH')
        # Positions [1], [2] are real, sorted by distance
        assert not result[1]['gauge_id'].startswith('SYNTH')
        assert not result[2]['gauge_id'].startswith('SYNTH')
        assert result[1]['distance_m'] <= result[2]['distance_m']

    def test_no_synthetic_falls_back_to_distance_order(self):
        gen = FakeGen()
        lookup = _make_gauge_lookup()
        del lookup['SYNTH-001']
        result = gen._find_nearest_gauges(51.501, -0.100, lookup, n=3)
        # All real, sorted by distance
        for r in result:
            assert not r['gauge_id'].startswith('SYNTH')
        assert result[0]['distance_m'] <= result[1]['distance_m'] <= result[2]['distance_m']

    def test_three_gauges_returned(self):
        gen = FakeGen()
        lookup = _make_gauge_lookup()
        result = gen._find_nearest_gauges(51.501, -0.100, lookup, n=3)
        assert len(result) == 3

    def test_synthetic_gauge_info_preserved(self):
        gen = FakeGen()
        lookup = _make_gauge_lookup()
        result = gen._find_nearest_gauges(51.501, -0.100, lookup, n=3)
        synth = result[0]
        assert synth['gauge_info']['elevation'] == 5.0
        assert synth['gauge_info']['severe_level'] == 7.0
