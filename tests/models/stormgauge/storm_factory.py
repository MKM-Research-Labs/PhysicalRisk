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
Tests for models.stormgauge.storm_factory.

Covers: create_storm (default params, auto ID, all intensity profiles,
custom track), and load_gauges_from_portfolio.
"""

import json
import math
from datetime import datetime

import pytest

from models.stormgauge.data_structures import (
    DecayKernel,
    IntensityProfile,
    Storm,
    TrackPoint,
)
from models.stormgauge.storm_factory import create_storm


# Placeholder track coords for tests that don't care about geography.
# `create_storm` requires track_start/track_end since they were dethamesed;
# tests in this file exercise creation semantics, not regional behaviour,
# so they use arbitrary non-catchment-specific coords through this wrapper.
def _storm(**kw):
    kw.setdefault("track_start", (0.0, 0.0))
    kw.setdefault("track_end", (2.0, 0.0))
    return create_storm(**kw)


# ===========================================================================
# create_storm
# ===========================================================================

class TestCreateStorm:

    def test_returns_storm_object(self):
        storm = _storm()
        assert isinstance(storm, Storm)

    def test_auto_generated_id_starts_with_storm(self):
        storm = _storm()
        assert storm.storm_id.startswith("STORM-")

    def test_explicit_id_preserved(self):
        storm = _storm(storm_id="MY-STORM-001")
        assert storm.storm_id == "MY-STORM-001"

    def test_explicit_name(self):
        storm = _storm(name="Ciara")
        assert storm.name == "Ciara"

    def test_explicit_start_time(self):
        t = datetime(2025, 1, 15, 12, 0, 0)
        storm = _storm(start_time=t)
        assert storm.start_time == t

    def test_default_start_time_is_recent(self):
        before = datetime.now()
        storm = _storm()
        after = datetime.now()
        assert before <= storm.start_time <= after

    def test_peak_intensity_stored(self):
        storm = _storm(peak_intensity=75.0)
        assert storm.peak_intensity == pytest.approx(75.0)

    def test_footprint_km_stored(self):
        storm = _storm(footprint_km=60.0)
        assert storm.footprint_km == pytest.approx(60.0)

    def test_duration_hours_stored(self):
        storm = _storm(duration_hours=36.0)
        assert storm.duration_hours == pytest.approx(36.0)

    def test_num_track_points(self):
        storm = _storm(num_track_points=10)
        assert len(storm.track) == 10

    def test_default_num_track_points(self):
        storm = _storm()
        assert len(storm.track) == 25

    def test_track_points_are_trackpoint_instances(self):
        storm = _storm()
        for tp in storm.track:
            assert isinstance(tp, TrackPoint)

    def test_track_longitude_moves_from_start_to_end(self):
        # Demonstrates passing explicit track coords; uses the raw
        # factory directly rather than the placeholder-coords helper.
        storm = create_storm(
            track_start=(0.0, 0.0),
            track_end=(2.0, 0.0),
        )
        lons = [tp.longitude for tp in storm.track]
        assert lons[0] < lons[-1]  # west to east

    def test_track_time_increases(self):
        storm = _storm()
        times = [tp.time_hours for tp in storm.track]
        assert all(times[i] <= times[i + 1] for i in range(len(times) - 1))

    def test_track_start_time_is_zero(self):
        storm = _storm()
        assert storm.track[0].time_hours == pytest.approx(0.0)

    def test_track_end_time_equals_duration(self):
        storm = _storm(duration_hours=24.0)
        assert storm.track[-1].time_hours == pytest.approx(24.0)

    def test_speed_is_positive(self):
        storm = _storm()
        assert storm.speed_kmh > 0

    def test_decay_kernel_stored(self):
        storm = _storm(decay_kernel=DecayKernel.EXPONENTIAL)
        assert storm.decay_kernel == DecayKernel.EXPONENTIAL

    def test_decay_parameter_stored(self):
        storm = _storm(decay_parameter=1.2)
        assert storm.decay_parameter == pytest.approx(1.2)


# ===========================================================================
# Intensity profiles
# ===========================================================================

class TestIntensityProfiles:

    def _max_intensity(self, profile):
        storm = _storm(peak_intensity=60.0, intensity_profile=profile)
        return max(tp.intensity for tp in storm.track)

    def _min_start_end(self, profile):
        storm = _storm(peak_intensity=60.0, intensity_profile=profile)
        return storm.track[0].intensity, storm.track[-1].intensity

    def test_triangular_profile_peak_near_midpoint(self):
        storm = _storm(
            peak_intensity=60.0,
            intensity_profile=IntensityProfile.TRIANGULAR,
            num_track_points=25,
        )
        intensities = [tp.intensity for tp in storm.track]
        peak_idx = intensities.index(max(intensities))
        # Peak should be close to the middle (index 12 for 25 points)
        assert 8 <= peak_idx <= 16

    def test_triangular_max_equals_peak_intensity(self):
        storm = _storm(peak_intensity=80.0, intensity_profile=IntensityProfile.TRIANGULAR)
        assert max(tp.intensity for tp in storm.track) == pytest.approx(80.0, abs=5.0)

    def test_gaussian_profile_peak_near_midpoint(self):
        storm = _storm(
            peak_intensity=60.0,
            intensity_profile=IntensityProfile.GAUSSIAN,
            num_track_points=25,
        )
        intensities = [tp.intensity for tp in storm.track]
        peak_idx = intensities.index(max(intensities))
        assert 8 <= peak_idx <= 16

    def test_beta_profile_creates_storm(self):
        storm = _storm(intensity_profile=IntensityProfile.BETA)
        assert storm is not None
        assert len(storm.track) > 0

    def test_all_profiles_produce_valid_storm(self):
        for profile in IntensityProfile:
            storm = _storm(intensity_profile=profile)
            assert isinstance(storm, Storm)
            assert len(storm.track) > 0


# ===========================================================================
# load_gauges_from_portfolio
# ===========================================================================

class TestLoadGaugesFromPortfolio:

    def test_empty_portfolio_returns_empty_list(self, tmp_path):
        from models.stormgauge.storm_factory import load_gauges_from_portfolio
        data = {"flood_gauges": []}
        p = tmp_path / "gauge.json"
        p.write_text(json.dumps(data))
        result = load_gauges_from_portfolio(p)
        assert result == []

    def test_loads_gauge_from_portfolio(self, tmp_path):
        from models.stormgauge.storm_factory import load_gauges_from_portfolio
        from models.stormgauge.data_structures import GaugeConfig
        data = {
            "flood_gauges": [
                {
                    "FloodGauge": {
                        "Header": {
                            "GaugeID": "GAUGE-001",
                            "GaugeName": "Test Gauge",
                        },
                        "SensorDetails": {
                            "GaugeInformation": {
                                "GaugeLatitude": 51.5,
                                "GaugeLongitude": -0.1,
                                "GroundLevelMeters": 3.0,
                            }
                        },
                        "FloodStage": {
                            "UK": {
                                "FloodAlert": 4.0,
                                "FloodWarning": 4.5,
                                "SevereFloodWarning": 5.0,
                            }
                        },
                    }
                }
            ]
        }
        p = tmp_path / "gauge.json"
        p.write_text(json.dumps(data))
        result = load_gauges_from_portfolio(p)
        assert len(result) == 1
        assert isinstance(result[0], GaugeConfig)
        assert result[0].gauge_id == "GAUGE-001"
