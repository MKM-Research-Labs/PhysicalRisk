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
Tests for models.stormgauge.forward_model — StormGaugeModel (part 1).

Haversine distance, decay kernels, nearest-track-point search.
"""

import math

import pytest

from models.stormgauge.data_structures import DecayKernel, TrackPoint


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
        decay = model.compute_decay(50, 100, DecayKernel.LINEAR, 2.0)
        assert decay == pytest.approx(0.75, abs=0.001)

    def test_linear_beyond_cutoff_is_zero(self, model):
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
