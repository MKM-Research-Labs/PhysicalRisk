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

"""Shared fixtures for typhoon model tests.

All geography in this file is deliberately neutral — a 10x10 deg box
anchored at (0, 0). The bbox is chosen so it visually maps to no real
cyclone basin, reinforcing that the model is catchment-agnostic. Real
catchment data (Halong, etc.) lives only under data/catch/<id>/ and
tests/catch/<id>/.
"""

from datetime import datetime

import pytest

from config.typhoon import (
    CatchmentTyphoonConfig,
    GenesisPrior,
    IntensityParams,
    MotionParams,
    PeakWindParams,
    PlausibilityWeights,
    PropertyPoint,
    RegimeClass,
    ScenarioFamily,
    SizeParams,
    WindFieldParams,
)
from models.typhoon.data_structures import (
    TyphoonParticle,
    TyphoonState,
    TyphoonTrajectory,
    WindFieldOutput,
)


# ---------------------------------------------------------------------------
# Canonical neutral coordinates used throughout the typhoon model tests.
# Any test fixture that needs a position should pull from here so the test
# suite stays free of region-suggestive literals.
# ---------------------------------------------------------------------------

TEST_BBOX = (0.0, 0.0, 10.0, 10.0)                    # neutral genesis bbox
TEST_BBOX_INTERIOR_LON = 5.0                          # midpoint, "open water" by default mask
TEST_BBOX_INTERIOR_LAT = 5.0
TEST_BBOX_LAND_LON = 1.0                              # west side, "over land" by default mask
TEST_LAND_THRESHOLD_LON = 2.0                         # mask boundary: lon < threshold is land


def _default_land_mask(longitude: float, latitude: float) -> bool:
    """Neutral test land mask — land on the west side of the test bbox."""
    return longitude < TEST_LAND_THRESHOLD_LON


# ---------------------------------------------------------------------------
# Sample state / particle / trajectory fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_state():
    """A canonical mid-event state, over water, moving west."""
    return TyphoonState(
        longitude=TEST_BBOX_INTERIOR_LON,
        latitude=TEST_BBOX_INTERIOR_LAT,
        translation_speed_kmh=18.0,
        heading_deg=270.0,
        v_max_ms=40.0,
        r_max_km=35.0,
        r_outer_km=150.0,
        regime=RegimeClass.STRAIGHT_WESTWARD,
        land_flag=False,
        time_hours=24.0,
    )


@pytest.fixture
def landfall_state():
    """A state with the storm over land, decaying."""
    return TyphoonState(
        longitude=TEST_BBOX_LAND_LON,
        latitude=TEST_BBOX_INTERIOR_LAT,
        translation_speed_kmh=12.0,
        heading_deg=280.0,
        v_max_ms=25.0,
        r_max_km=40.0,
        r_outer_km=160.0,
        regime=RegimeClass.LANDFALL_DECAY,
        land_flag=True,
        time_hours=72.0,
    )


@pytest.fixture
def sample_particle(sample_state):
    return TyphoonParticle(
        state=sample_state,
        weight=0.001,
        particle_id=42,
        parent_id=7,
    )


@pytest.fixture
def sample_trajectory(sample_state, landfall_state):
    return TyphoonTrajectory(
        event_id="EVT-0001",
        particle_id=42,
        scenario_family=ScenarioFamily.SEVERE,
        genesis_time=datetime(2026, 9, 1, 0, 0, 0),
        states=[sample_state, landfall_state],
    )


# ---------------------------------------------------------------------------
# Minimal CatchmentTyphoonConfig fixture — built from model defaults only
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_config():
    """A self-contained config built from model defaults — exercises the
    parameter dataclass shape without referencing any catchment file.

    Geography is deliberately neutral (see module docstring).
    """
    return CatchmentTyphoonConfig(
        catchment_id="test",
        genesis_prior=GenesisPrior(
            bbox=TEST_BBOX,
            heading_mean_deg=270.0,
            heading_kappa=5.0,
            speed_shape=4.0,
            speed_scale=4.0,
            regime_weights={r: 0.2 for r in RegimeClass},
            scenario_mix={s: 0.2 for s in ScenarioFamily},
        ),
        peak_wind={
            s: PeakWindParams(mu_ms=35.0, sigma_ms=12.0, v_threshold_ms=50.0, alpha=2.0)
            for s in ScenarioFamily
        },
        motion=MotionParams(
            mean_speed_kmh={r: 15.0 for r in RegimeClass},
            sigma_speed_kmh={r: 4.0 for r in RegimeClass},
            mean_heading_deg={r: 270.0 for r in RegimeClass},
            sigma_heading_deg={r: 20.0 for r in RegimeClass},
        ),
        intensity=IntensityParams(),
        size=SizeParams(),
        wind_field=WindFieldParams(),
        plausibility=PlausibilityWeights(),
        land_mask=_default_land_mask,
        property_points=[
            PropertyPoint(
                property_id="P1",
                longitude=TEST_BBOX_INTERIOR_LON,
                latitude=TEST_BBOX_INTERIOR_LAT,
            ),
        ],
    )


@pytest.fixture
def sample_wind_output():
    return WindFieldOutput(
        point_id="P1",
        longitude=TEST_BBOX_INTERIOR_LON,
        latitude=TEST_BBOX_INTERIOR_LAT,
        time_hours=[0.0, 1.0, 2.0, 3.0],
        sustained_ms=[5.0, 12.0, 22.0, 14.0],
        peak_sustained_ms=22.0,
        time_of_peak_hours=2.0,
        distance_at_peak_km=80.0,
        azimuth_at_peak_deg=125.0,
        duration_above_ms={17.5: 1.0, 25.0: 0.0},
    )
