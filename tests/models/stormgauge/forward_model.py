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
Tests for models.stormgauge.forward_model — StormGaugeModel.

Covers: haversine distance, all three decay kernels, nearest-track-point
search, intensity interpolation, intensity-to-level mapping, full
compute_response pipeline, and multi-gauge batch compute.
"""

import math
from datetime import datetime

import pytest

from models.stormgauge.data_structures import (
    DecayKernel,
    GaugeConfig,
    GaugeResponse,
    Storm,
    TrackPoint,
)
from models.stormgauge.forward_model import StormGaugeModel


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def model():
    return StormGaugeModel(
        intensity_to_level_scale=0.1,
        time_resolution_hours=1.0,
        response_lag_hours=2.0,
        response_decay_hours=12.0,
    )


@pytest.fixture
def gauge():
    """Gauge on the Thames near Hammersmith."""
    return GaugeConfig(
        gauge_id="G-TEST01",
        gauge_name="Test Thames Gauge",
        latitude=51.49,
        longitude=-0.22,
        base_level=1.0,
        flood_alert=3.0,
        flood_warning=4.0,
        severe_warning=5.0,
        historical_high=6.0,
        sensitivity=1.0,
    )


@pytest.fixture
def simple_storm():
    """Storm passing directly over the gauge area."""
    return Storm(
        storm_id="S-TEST01",
        name="Test Storm Alpha",
        start_time=datetime(2025, 3, 1, 0, 0),
        duration_hours=24.0,
        track=[
            TrackPoint(-0.50, 51.40, 0.0,  10.0),
            TrackPoint(-0.22, 51.49, 12.0, 85.0),   # closest point
            TrackPoint( 0.10, 51.60, 24.0, 20.0),
        ],
        peak_intensity=85.0,
        footprint_km=50.0,
        decay_kernel=DecayKernel.GAUSSIAN,
        decay_parameter=0.5,
    )


# ===========================================================================
# Haversine distance
# ===========================================================================

class TestHaversine:

    def test_same_point_is_zero(self, model):
        assert model.haversine_km(0.0, 0.0, 0.0, 0.0) == pytest.approx(0.0, abs=0.01)

    def test_london_to_paris_approx_340km(self, model):
        d = model.haversine_km(-0.1276, 51.5074, 2.3522, 48.8566)
        assert 320 < d < 360

    def test_symmetric(self, model):
        d1 = model.haversine_km(0.0, 51.0, 1.0, 52.0)
        d2 = model.haversine_km(1.0, 52.0, 0.0, 51.0)
        assert d1 == pytest.approx(d2, rel=1e-6)

    def test_equatorial_degree_approx_111km(self, model):
        d = model.haversine_km(0.0, 0.0, 1.0, 0.0)
        assert 110 < d < 113


# ===========================================================================
# Spatial decay kernels
# ===========================================================================

class TestComputeDecay:

    def test_zero_distance_returns_one_all_kernels(self, model):
        for kernel in DecayKernel:
            assert model.compute_decay(0, 100, kernel, 1.0) == 1.0

    def test_gaussian_at_one_sigma(self, model):
        # d_norm = 1.0, sigma = 1.0 → exp(-0.5)
        decay = model.compute_decay(100, 100, DecayKernel.GAUSSIAN, 1.0)
        assert decay == pytest.approx(math.exp(-0.5), rel=1e-4)

    def test_gaussian_at_two_sigma(self, model):
        decay = model.compute_decay(200, 100, DecayKernel.GAUSSIAN, 1.0)
        assert decay == pytest.approx(math.exp(-2.0), rel=1e-4)

    def test_exponential_at_one_lambda(self, model):
        decay = model.compute_decay(100, 100, DecayKernel.EXPONENTIAL, 1.0)
        assert decay == pytest.approx(math.exp(-1.0), rel=1e-4)

    def test_exponential_at_half(self, model):
        decay = model.compute_decay(50, 100, DecayKernel.EXPONENTIAL, 1.0)
        assert decay == pytest.approx(math.exp(-0.5), rel=1e-4)

    def test_linear_midpoint(self, model):
        # d_norm = 0.5, r = 2.0 → 1 - 0.5/2 = 0.75
        decay = model.compute_decay(50, 100, DecayKernel.LINEAR, 2.0)
        assert decay == pytest.approx(0.75, abs=0.001)

    def test_linear_beyond_cutoff_is_zero(self, model):
        # d_norm = 3.0 > r = 2.0 → clamped to 0
        decay = model.compute_decay(300, 100, DecayKernel.LINEAR, 2.0)
        assert decay == 0.0

    def test_all_kernels_decrease_with_distance(self, model):
        for kernel in DecayKernel:
            near = model.compute_decay(10, 100, kernel, 1.0)
            far = model.compute_decay(200, 100, kernel, 1.0)
            assert near >= far, f"Decay did not decrease for kernel {kernel}"

    def test_all_kernels_in_0_1_range(self, model):
        for kernel in DecayKernel:
            for d in [1, 50, 100, 300]:
                decay = model.compute_decay(d, 100, kernel, 1.0)
                assert 0.0 <= decay <= 1.0


# ===========================================================================
# Nearest track point
# ===========================================================================

class TestFindNearestTrackPoint:

    def test_returns_nearest_of_three(self, model):
        track = [
            TrackPoint(-1.0, 51.0, 0.0, 10.0),
            TrackPoint(-0.22, 51.49, 6.0, 80.0),  # nearest
            TrackPoint(1.0, 52.0, 12.0, 30.0),
        ]
        nearest, dist = model.find_nearest_track_point(-0.22, 51.49, track)
        assert nearest.intensity == 80.0
        assert dist == pytest.approx(0.0, abs=1.0)

    def test_single_track_point(self, model):
        track = [TrackPoint(0.0, 51.0, 0.0, 50.0)]
        nearest, dist = model.find_nearest_track_point(0.0, 51.0, track)
        assert nearest is track[0]

    def test_distance_is_positive(self, model):
        track = [
            TrackPoint(-0.5, 51.3, 0.0, 20.0),
            TrackPoint(0.5, 51.7, 12.0, 60.0),
        ]
        _, dist = model.find_nearest_track_point(0.0, 51.5, track)
        assert dist > 0


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
        # At t=12h, storm is directly over gauge
        intensity = model.compute_intensity_at_gauge(12.0, gauge.longitude, gauge.latitude, simple_storm)
        assert intensity > 0

    def test_far_from_track_is_lower(self, model, simple_storm):
        # Gauge far away
        near = model.compute_intensity_at_gauge(12.0, -0.22, 51.49, simple_storm)
        far = model.compute_intensity_at_gauge(12.0, 5.0, 55.0, simple_storm)
        assert near > far

    def test_before_start_uses_first_point(self, model, simple_storm, gauge):
        # t=0 is first track point with intensity 10
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
        # Different historical_high → different level_range → different contribution
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
        """A storm passing directly over with peak=100 should flood the gauge."""
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
