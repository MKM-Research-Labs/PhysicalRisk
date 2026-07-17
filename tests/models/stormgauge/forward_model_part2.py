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
Tests for models.stormgauge.forward_model — StormGaugeModel (part 2).

Intensity at gauge, intensity-to-level mapping, full compute_response,
multi-gauge batch.
"""

from datetime import datetime

import pytest

from models.stormgauge.data_structures import (
    DecayKernel,
    GaugeConfig,
    Storm,
    TrackPoint,
)


# ===========================================================================
# Intensity at gauge
# ===========================================================================

class TestComputeIntensityAtGauge:

    def test_empty_track_returns_zero(self, model):
        storm = Storm(
            storm_id="S0", name="Empty", start_time=datetime(2025, 1, 1),
            duration_hours=10, track=[], peak_intensity=50, footprint_km=50,
        )
        result = model.compute_intensity_at_gauge(5.0, -0.1, 51.5, storm)
        assert result == 0.0

    def test_at_peak_time_is_nonzero(self, model, simple_storm, gauge):
        intensity = model.compute_intensity_at_gauge(12.0, gauge.longitude, gauge.latitude, simple_storm)
        assert intensity > 0

    def test_far_from_track_is_lower(self, model, simple_storm):
        near = model.compute_intensity_at_gauge(12.0, -0.22, 51.49, simple_storm)
        far = model.compute_intensity_at_gauge(12.0, 5.0, 55.0, simple_storm)
        assert near > far

    def test_before_start_uses_first_point(self, model, simple_storm, gauge):
        intensity = model.compute_intensity_at_gauge(-1.0, gauge.longitude, gauge.latitude, simple_storm)
        assert intensity >= 0

    def test_after_end_uses_last_point(self, model, simple_storm, gauge):
        intensity = model.compute_intensity_at_gauge(30.0, gauge.longitude, gauge.latitude, simple_storm)
        assert intensity >= 0


# ===========================================================================
# Intensity to level mapping
# ===========================================================================

class TestIntensityToLevel:

    def test_zero_intensity_returns_zero(self, model, gauge):
        assert model.intensity_to_level(0.0, gauge) == 0.0

    def test_negative_intensity_returns_zero(self, model, gauge):
        assert model.intensity_to_level(-10.0, gauge) == 0.0

    def test_positive_intensity_positive_level(self, model, gauge):
        assert model.intensity_to_level(50.0, gauge) > 0.0

    def test_monotone_increasing(self, model, gauge):
        levels = [model.intensity_to_level(i, gauge) for i in [10, 30, 50, 70, 90]]
        assert all(levels[i] < levels[i + 1] for i in range(len(levels) - 1))

    def test_uses_historical_high_when_set(self, model):
        g_with = GaugeConfig("G1", "T", 51.5, -0.1, 1.0, 3.0, 4.0, 5.0, historical_high=8.0)
        g_without = GaugeConfig("G2", "T", 51.5, -0.1, 1.0, 3.0, 4.0, 5.0, historical_high=None)
        lv_with = model.intensity_to_level(50, g_with)
        lv_without = model.intensity_to_level(50, g_without)
        assert lv_with != lv_without

    def test_sensitivity_scales_output(self, model):
        g1 = GaugeConfig("G1", "T", 51.5, -0.1, 1.0, 3.0, 4.0, 5.0, sensitivity=1.0)
        g2 = GaugeConfig("G2", "T", 51.5, -0.1, 1.0, 3.0, 4.0, 5.0, sensitivity=2.0)
        assert model.intensity_to_level(50, g2) == pytest.approx(
            model.intensity_to_level(50, g1) * 2, rel=1e-6)


# ===========================================================================
# Full response simulation
# ===========================================================================

class TestComputeResponse:

    def test_response_ids_match(self, model, simple_storm, gauge):
        resp = model.compute_response(simple_storm, gauge)
        assert resp.gauge_id == gauge.gauge_id
        assert resp.storm_id == simple_storm.storm_id

    def test_timeseries_length(self, model, simple_storm, gauge):
        resp = model.compute_response(simple_storm, gauge)
        expected_steps = int(simple_storm.duration_hours / model.time_resolution_hours) + 1
        assert len(resp.level_timeseries) == expected_steps
        assert len(resp.intensity_timeseries) == expected_steps

    def test_peak_level_at_least_base(self, model, simple_storm, gauge):
        resp = model.compute_response(simple_storm, gauge)
        assert resp.peak_level >= gauge.base_level

    def test_peak_level_is_max_of_series(self, model, simple_storm, gauge):
        resp = model.compute_response(simple_storm, gauge)
        levels = [p['level'] for p in resp.level_timeseries]
        assert resp.peak_level == pytest.approx(max(levels))

    def test_flooded_flag_correct(self, model, simple_storm, gauge):
        resp = model.compute_response(simple_storm, gauge)
        assert resp.flooded == (resp.peak_level >= gauge.flood_alert)

    def test_duration_nonnegative(self, model, simple_storm, gauge):
        resp = model.compute_response(simple_storm, gauge)
        assert resp.duration_above_alert >= 0
        assert resp.duration_above_warning >= 0
        assert resp.duration_above_severe >= 0

    def test_accumulation_nonnegative(self, model, simple_storm, gauge):
        resp = model.compute_response(simple_storm, gauge)
        assert resp.accumulation >= 0

    def test_high_intensity_storm_floods(self, model, gauge):
        intense = Storm(
            storm_id="S-BIG",
            name="Big Storm",
            start_time=datetime(2025, 1, 1),
            duration_hours=12.0,
            track=[
                TrackPoint(gauge.longitude, gauge.latitude, 0.0, 100.0),
                TrackPoint(gauge.longitude, gauge.latitude, 12.0, 100.0),
            ],
            peak_intensity=100.0,
            footprint_km=100.0,
            decay_kernel=DecayKernel.GAUSSIAN,
            decay_parameter=2.0,
        )
        resp = model.compute_response(intense, gauge)
        assert resp.peak_level > gauge.base_level

    def test_to_dict_roundtrip(self, model, simple_storm, gauge):
        resp = model.compute_response(simple_storm, gauge)
        d = resp.to_dict()
        assert d['gauge_id'] == gauge.gauge_id
        assert 'level_timeseries' in d
        assert 'peak_level' in d

    def test_to_dict_without_timeseries(self, model, simple_storm, gauge):
        resp = model.compute_response(simple_storm, gauge)
        d = resp.to_dict(include_timeseries=False)
        assert 'level_timeseries' not in d


# ===========================================================================
# Multi-gauge batch
# ===========================================================================

class TestComputeAllResponses:

    def test_returns_one_response_per_gauge(self, model, simple_storm, gauge):
        gauge2 = GaugeConfig("G2", "Far Gauge", 52.0, 1.0, 1.0, 3.0, 4.0, 5.0)
        responses = model.compute_all_responses(simple_storm, [gauge, gauge2])
        assert len(responses) == 2

    def test_gauge_ids_match(self, model, simple_storm, gauge):
        gauge2 = GaugeConfig("G2", "Far Gauge", 52.0, 1.0, 1.0, 3.0, 4.0, 5.0)
        responses = model.compute_all_responses(simple_storm, [gauge, gauge2])
        assert {r.gauge_id for r in responses} == {gauge.gauge_id, gauge2.gauge_id}

    def test_near_gauge_higher_response(self, model, simple_storm, gauge):
        far_gauge = GaugeConfig("G-FAR", "Far Away", 55.0, 5.0, 1.0, 3.0, 4.0, 5.0)
        responses = model.compute_all_responses(simple_storm, [gauge, far_gauge])
        near_resp = next(r for r in responses if r.gauge_id == gauge.gauge_id)
        far_resp = next(r for r in responses if r.gauge_id == far_gauge.gauge_id)
        assert near_resp.peak_level >= far_resp.peak_level
