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

"""Top-level genesis samplers composing the peak-wind and initial-state samplers."""

from typing import List

import numpy as np

from config.typhoon import CatchmentTyphoonConfig, ScenarioFamily
from models.typhoon.data_structures import TyphoonState
from models.typhoon.genesis._peakwind import sample_peak_wind
from models.typhoon.genesis._samplers import (
    sample_genesis_location,
    sample_initial_heading,
    sample_initial_size,
    sample_initial_speed,
    sample_regime,
    sample_scenario_family,
)


# ===========================================================================
# Top-level genesis samplers
# ===========================================================================


def sample_genesis(
    config: CatchmentTyphoonConfig,
    scenario: ScenarioFamily,
    rng: np.random.Generator,
    v_max_override: float = None,
) -> TyphoonState:
    """Sample one genesis state under the given scenario family.

    Args:
        config: catchment configuration
        scenario: scenario family selecting the peak-wind distribution
        rng: random generator (caller-owned for reproducibility)
        v_max_override: if not None, use this peak wind (m/s) instead of
            drawing from the scenario's peak-wind distribution. Set by the
            storm->wind coupling (coupling_spec.md §4) so the event's genesis
            intensity is fixed by the paired storm's severity; location,
            heading, speed, size and regime are still sampled from ``rng``.

    Returns:
        TyphoonState at t = 0.
    """
    prior = config.genesis_prior

    lon, lat = sample_genesis_location(prior, rng)
    heading_deg = sample_initial_heading(prior, rng)
    speed_kmh = sample_initial_speed(prior, rng)
    if v_max_override is not None:
        v_max_ms = float(v_max_override)
    else:
        v_max_ms = sample_peak_wind(config.peak_wind[scenario], rng)
    r_max_km, r_outer_km = sample_initial_size(v_max_ms, config.size, rng)
    regime = sample_regime(prior.regime_weights, rng)
    land_flag = bool(config.land_mask(lon, lat))

    return TyphoonState(
        longitude=lon,
        latitude=lat,
        translation_speed_kmh=speed_kmh,
        heading_deg=heading_deg,
        v_max_ms=v_max_ms,
        r_max_km=r_max_km,
        r_outer_km=r_outer_km,
        regime=regime,
        land_flag=land_flag,
        time_hours=0.0,
    )


def sample_genesis_ensemble(
    config: CatchmentTyphoonConfig,
    n: int,
    rng: np.random.Generator,
) -> List[TyphoonState]:
    """Sample n genesis states with scenarios drawn from the prior mix.

    Args:
        config: catchment configuration
        n: number of genesis states to draw
        rng: random generator

    Returns:
        List of n TyphoonState instances at t = 0.
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    mix = config.genesis_prior.scenario_mix
    states: List[TyphoonState] = []
    for _ in range(n):
        scenario = sample_scenario_family(mix, rng)
        states.append(sample_genesis(config, scenario, rng))
    return states
