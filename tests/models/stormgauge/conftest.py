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

"""Shared fixtures for stormgauge forward model tests."""

from datetime import datetime

import pytest

from models.stormgauge.data_structures import (
    DecayKernel,
    GaugeConfig,
    Storm,
    TrackPoint,
)
from models.stormgauge.forward_model import StormGaugeModel


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
