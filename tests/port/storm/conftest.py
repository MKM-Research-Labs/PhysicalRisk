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

"""Shared fixtures for spatial correlation tests."""

import numpy as np
import pytest

from port.src.storm_multi.models.spatial_correlation import (
    SpatialCorrelationModel,
)
from port.src.storm_multi.generators.batch_generator import generate_event_set
import sys as _sys
import pathlib as _pl
_DATA_DIR = str(_pl.Path(__file__).parents[3] / "data")
if _DATA_DIR not in _sys.path:
    _sys.path.insert(0, _DATA_DIR)
from catch.thames import GAUGE_POINTS as THAMES_GAUGE_POINTS  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic gauge locations (5 gauges along a 50km transect)
# ---------------------------------------------------------------------------

SYNTHETIC_LOCATIONS = [
    (51.45, -0.30),
    (51.46, -0.20),
    (51.47, -0.10),
    (51.48,  0.00),
    (51.49,  0.10),
]

THAMES_GAUGE_PATH = "data/input/thames/gauge.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def small_model():
    """5-gauge synthetic model with default parameters."""
    return SpatialCorrelationModel(SYNTHETIC_LOCATIONS)


@pytest.fixture(scope="module")
def thames_model():
    """Full 52-gauge Thames model built from thames.GAUGE_POINTS (source of truth)."""
    locations = [(lat, lon) for lat, lon, _ in THAMES_GAUGE_POINTS]
    return SpatialCorrelationModel(locations)


@pytest.fixture(scope="module")
def rng():
    return np.random.RandomState(42)


@pytest.fixture(scope="module")
def small_batch():
    return generate_event_set(count=50, seed=99)


# ---------------------------------------------------------------------------
# Fixtures for sequence_response_hydro tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def default_gauge():
    from port.src.storm_multi.models.sequence_response import SequenceGaugeParams
    return SequenceGaugeParams.default_thames()


@pytest.fixture(scope="module")
def doublet_batch():
    """200 forced-doublet sequences for compounding validation."""
    return generate_event_set(count=200, force_sequence_type="doublet", seed=42)


@pytest.fixture(scope="module")
def severe_batch():
    """200 severe sequences (natural type mix)."""
    return generate_event_set(
        count=200,
        intensity_weights={"severe": 1.0},
        seed=7,
    )
