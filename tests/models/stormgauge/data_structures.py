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
Tests for models.stormgauge.data_structures — enums and dataclasses.

Covers: IntensityProfile, DecayKernel enums,
Storm.to_dict, GaugeConfig.from_gauge_portfolio, GaugeResponse.to_dict.
"""

from datetime import datetime

import pytest

from models.stormgauge.data_structures import (
    DecayKernel,
    GaugeConfig,
    GaugeResponse,
    IntensityProfile,
    Storm,
    TrackPoint,
)


# ===========================================================================
# IntensityProfile enum
# ===========================================================================

class TestIntensityProfile:

    def test_triangular_value(self):
        assert IntensityProfile.TRIANGULAR.value == "triangular"

    def test_beta_value(self):
        assert IntensityProfile.BETA.value == "beta"

    def test_gaussian_value(self):
        assert IntensityProfile.GAUSSIAN.value == "gaussian"


# ===========================================================================
# DecayKernel enum
# ===========================================================================

class TestDecayKernel:

    def test_gaussian_value(self):
        assert DecayKernel.GAUSSIAN.value == "gaussian"

    def test_exponential_value(self):
        assert DecayKernel.EXPONENTIAL.value == "exponential"

    def test_linear_value(self):
        assert DecayKernel.LINEAR.value == "linear"


# ===========================================================================
# Storm.to_dict
# ===========================================================================

class TestStormToDict:

    def _make_storm(self):
        return Storm(
            storm_id="STORM-0001",
            name="Test Storm",
            start_time=datetime(2026, 1, 1, 0, 0),
            duration_hours=48.0,
            track=[
                TrackPoint(-0.5, 51.0, 0.0, 50.0),
                TrackPoint(-0.3, 51.1, 24.0, 80.0),
            ],
            peak_intensity=80.0,
            footprint_km=200.0,
        )

    def test_returns_dict(self):
        storm = self._make_storm()
        d = storm.to_dict()
        assert isinstance(d, dict)

    def test_has_storm_id(self):
        storm = self._make_storm()
        assert storm.to_dict()["storm_id"] == "STORM-0001"

    def test_has_track(self):
        storm = self._make_storm()
        d = storm.to_dict()
        assert "track" in d
        assert len(d["track"]) == 2

    def test_track_has_coords(self):
        storm = self._make_storm()
        d = storm.to_dict()
        point = d["track"][0]
        assert "longitude" in point
        assert "latitude" in point
        assert "time_hours" in point
        assert "intensity" in point

    def test_decay_kernel_serialised_as_string(self):
        storm = self._make_storm()
        d = storm.to_dict()
        assert isinstance(d["decay_kernel"], str)
        assert d["decay_kernel"] == "gaussian"

    def test_intensity_profile_serialised_as_string(self):
        storm = self._make_storm()
        d = storm.to_dict()
        assert isinstance(d["intensity_profile"], str)
        assert d["intensity_profile"] == "triangular"

    def test_custom_kernel(self):
        storm = self._make_storm()
        storm.decay_kernel = DecayKernel.EXPONENTIAL
        d = storm.to_dict()
        assert d["decay_kernel"] == "exponential"


# ===========================================================================
# GaugeConfig.from_gauge_portfolio
# ===========================================================================

class TestGaugeConfigFromPortfolio:

    def _make_gauge_data(self, gauge_id="GAUGE-001"):
        return {
            "FloodGauge": {
                "Header": {"GaugeID": gauge_id, "GaugeName": "Test Gauge"},
                "Location": {"GaugeLatitude": 51.5, "GaugeLongitude": -0.1},
                "FloodStages": {
                    "FloodAlert": 4.0,
                    "FloodWarning": 4.5,
                    "SevereFloodWarning": 5.0,
                    "HistoricalHighLevel": 6.0,
                },
            }
        }

    def test_creates_gauge_config(self):
        gc = GaugeConfig.from_gauge_portfolio(self._make_gauge_data())
        assert isinstance(gc, GaugeConfig)

    def test_gauge_id_set(self):
        gc = GaugeConfig.from_gauge_portfolio(self._make_gauge_data("GAUGE-099"))
        assert gc.gauge_id == "GAUGE-099"

    def test_flood_alert_set(self):
        gc = GaugeConfig.from_gauge_portfolio(self._make_gauge_data())
        assert gc.flood_alert == 4.0

    def test_base_level_calculated(self):
        gc = GaugeConfig.from_gauge_portfolio(self._make_gauge_data())
        # base_level = flood_alert * 0.35 = 4.0 * 0.35 = 1.4
        assert abs(gc.base_level - 1.4) < 0.01

    def test_historical_high_set(self):
        gc = GaugeConfig.from_gauge_portfolio(self._make_gauge_data())
        assert gc.historical_high == 6.0

    def test_defaults_when_no_flood_stages(self):
        gauge_data = {
            "FloodGauge": {
                "Header": {"GaugeID": "G1"},
                "Location": {},
                "FloodStages": {},
            }
        }
        gc = GaugeConfig.from_gauge_portfolio(gauge_data)
        assert gc.flood_alert == 4.0  # default

    def test_flat_gauge_data(self):
        """Handles case where FloodGauge key is missing (flat data)."""
        flat = {
            "Header": {"GaugeID": "G2", "GaugeName": "Flat"},
            "Location": {"GaugeLatitude": 51.0, "GaugeLongitude": 0.0},
            "FloodStages": {"FloodAlert": 3.5},
        }
        gc = GaugeConfig.from_gauge_portfolio(flat)
        assert gc.flood_alert == 3.5


# ===========================================================================
# GaugeResponse.to_dict
# ===========================================================================

class TestGaugeResponseToDict:

    def _make_response(self):
        return GaugeResponse(
            gauge_id="GAUGE-001",
            storm_id="STORM-001",
            flooded=True,
            peak_level=5.2,
            peak_exceedance=0.7,
            peak_time_hours=18.0,
            peak_intensity=75.0,
            peak_intensity_time_hours=12.0,
            duration_above_alert=6.0,
            duration_above_warning=3.0,
            duration_above_severe=0.5,
            accumulation=4.5,
            intensity_timeseries=[
                {"time_hours": 0.0, "intensity": 30.0},
                {"time_hours": 6.0, "intensity": 75.0},
            ],
            level_timeseries=[
                {"time_hours": 0.0, "level": 3.5},
                {"time_hours": 18.0, "level": 5.2},
            ],
        )

    def test_returns_dict(self):
        r = self._make_response()
        d = r.to_dict()
        assert isinstance(d, dict)

    def test_has_required_keys(self):
        r = self._make_response()
        d = r.to_dict()
        assert "gauge_id" in d
        assert "storm_id" in d
        assert "flooded" in d
        assert "peak_level" in d

    def test_includes_timeseries_by_default(self):
        r = self._make_response()
        d = r.to_dict(include_timeseries=True)
        assert "intensity_timeseries" in d
        assert "level_timeseries" in d
        assert len(d["intensity_timeseries"]) == 2

    def test_excludes_timeseries_when_requested(self):
        r = self._make_response()
        d = r.to_dict(include_timeseries=False)
        assert "intensity_timeseries" not in d
        assert "level_timeseries" not in d

    def test_values_rounded(self):
        r = self._make_response()
        d = r.to_dict()
        assert d["peak_level"] == 5.2
        assert d["accumulation"] == 4.5

    def test_flooded_is_bool(self):
        r = self._make_response()
        d = r.to_dict()
        assert isinstance(d["flooded"], bool)
        assert d["flooded"] is True
