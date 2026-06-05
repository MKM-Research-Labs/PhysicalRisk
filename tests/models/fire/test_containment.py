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

"""Tests for Model D — containment & resilience credit (containment.py).

Verifies the chain march and the end-to-end orchestrator:
- the active matrix is selected from controllability, and switches to the
  absorbing point_of_no_return matrix once PNR latches
- sample_next_state renormalises rows and returns a valid state
- one fire marches to an absorbing terminal state (or the step budget)
- the per-asset run aggregates into the resilience-credit currency and the
  tallies are internally consistent
- a strong asset contains far more often / loses far less than a weak one
- a portfolio run is reproducible from a single seed
"""

import numpy as np
import pytest

from config.fire import FireModelConfig, FireRunConfig, FireState, load_fire_config
from models.fire.containment import (
    TERMINAL_STATES,
    sample_next_state,
    select_transition_matrix,
    simulate_asset_fire,
    simulate_fire_containment,
    simulate_portfolio_fire,
)
from models.fire.data_structures import AssetFireFeatures
from models.fire.response_effectiveness import derive_response_profile


def _rng(seed=20260605):
    return np.random.default_rng(seed)


@pytest.fixture
def config():
    return load_fire_config()


@pytest.fixture
def prog(config):
    return config.progression


def _strong(**overrides):
    base = dict(
        asset_id="STRONG",
        commercial_type="Office",
        occupancy_status="Fully occupied",
        property_condition="Excellent",
        automatic_detection_level="Verified",
        suppression_systems_level="Verified",
        emergency_procedures_level="Verified",
        structural_fire_resistance_level="Verified",
        compartments_level="Verified",
        fire_stopping_level="Verified",
        external_materials_level="Verified",
        access_route_level="Verified",
        business_continuity_level="Verified",
        number_of_storeys=2,
    )
    base.update(overrides)
    return AssetFireFeatures(**base)


def _weak(**overrides):
    base = dict(
        asset_id="WEAK",
        commercial_type="MixedUse",
        occupancy_status="Vacant",
        property_condition="Very poor",
        number_of_storeys=20,
    )
    base.update(overrides)
    return AssetFireFeatures(**base)


# ===========================================================================
# Matrix selection
# ===========================================================================


def test_pnr_selects_absorbing_matrix(config, prog):
    profile = derive_response_profile(_strong(), prog)
    chosen = select_transition_matrix(profile, point_of_no_return=True, cfg=prog)
    assert chosen is prog.transition_matrices["point_of_no_return"]


def test_controllability_switches_pre_pnr_matrix(prog):
    strong = derive_response_profile(_strong(), prog)
    weak = derive_response_profile(_weak(), prog)
    threshold = prog.controllability["switch_threshold"]
    assert strong.controllability >= threshold
    assert weak.controllability < threshold
    assert select_transition_matrix(strong, False, prog) is (
        prog.transition_matrices["AA_controllable"]
    )
    assert select_transition_matrix(weak, False, prog) is (
        prog.transition_matrices["weak_controllable"]
    )


# ===========================================================================
# State sampling
# ===========================================================================


def test_sample_next_state_returns_valid_state(prog):
    matrix = prog.transition_matrices["AA_controllable"]
    nxt = sample_next_state(FireState.S0_EXPOSURE_OR_IGNITION, matrix, _rng())
    assert isinstance(nxt, FireState)


def test_sample_next_state_renormalises_unnormalised_row():
    # A row that does not sum to 1 is renormalised rather than erroring.
    matrix = [[0.0] * 8 for _ in range(8)]
    matrix[0][6] = 2.0   # only S6 reachable, weight 2.0
    nxt = sample_next_state(FireState.S0_EXPOSURE_OR_IGNITION, matrix, _rng())
    assert nxt == FireState.S6_PARTIAL_LOSS


def test_sample_next_state_zero_row_raises():
    matrix = [[0.0] * 8 for _ in range(8)]
    with pytest.raises(ValueError):
        sample_next_state(FireState.S0_EXPOSURE_OR_IGNITION, matrix, _rng())


# ===========================================================================
# Single-fire march
# ===========================================================================


def test_single_fire_reaches_terminal_state(config, prog):
    profile = derive_response_profile(_strong(), prog)
    outcome = simulate_fire_containment(profile, config, _rng())
    assert outcome.terminal_state in TERMINAL_STATES or outcome.steps == config.run.max_steps
    assert outcome.steps >= 1
    assert outcome.peak_intensity >= 0.0


def test_single_fire_is_reproducible(config, prog):
    profile = derive_response_profile(_weak(), prog)
    a = simulate_fire_containment(profile, config, _rng(7))
    b = simulate_fire_containment(profile, config, _rng(7))
    assert a.terminal_state == b.terminal_state
    assert a.steps == b.steps
    assert a.peak_intensity == pytest.approx(b.peak_intensity)


# ===========================================================================
# Asset-level aggregation
# ===========================================================================


def _big(config, n_sim):
    run = FireRunConfig(n_sim=n_sim)
    return FireModelConfig(run=run, initiation=config.initiation,
                           progression=config.progression)


def test_asset_result_tallies_are_consistent(config):
    big = _big(config, 5000)
    result = simulate_asset_fire(_weak(), big, _rng(1))
    assert result.n_contained + result.n_partial + result.n_total <= result.n_fires
    assert 0 <= result.n_point_of_no_return <= result.n_fires
    assert result.loss_frequency == pytest.approx(
        (result.n_partial + result.n_total) / result.n_sim
    )
    assert result.partial_loss_frequency == pytest.approx(
        result.n_partial / result.n_sim
    )
    assert result.total_loss_frequency == pytest.approx(
        result.n_total / result.n_sim
    )
    if result.n_fires:
        assert result.containment_rate == pytest.approx(
            result.n_contained / result.n_fires
        )


def test_strong_asset_outperforms_weak_asset(config):
    big = _big(config, 8000)
    strong = simulate_asset_fire(_strong(), big, _rng(3))
    weak = simulate_asset_fire(_weak(), big, _rng(3))
    assert strong.containment_rate > weak.containment_rate
    assert strong.loss_frequency < weak.loss_frequency


def test_weak_asset_exercises_point_of_no_return(config):
    # The weak asset must actually cross the PNR gate at least once, otherwise
    # the absorbing matrix is dead code under the seed config.
    big = _big(config, 8000)
    weak = simulate_asset_fire(_weak(), big, _rng(11))
    assert weak.n_point_of_no_return > 0


def test_asset_result_to_dict_round_trips(config):
    result = simulate_asset_fire(_strong(), config, _rng())
    d = result.to_dict()
    assert d["asset_id"] == "STRONG"
    assert d["n_sim"] == config.run.n_sim
    assert "loss_frequency" in d and "containment_rate" in d


# ===========================================================================
# Portfolio
# ===========================================================================


def test_portfolio_runs_every_asset_reproducibly(config):
    portfolio = [_strong(), _weak()]
    a = simulate_portfolio_fire(portfolio, config, _rng(99))
    b = simulate_portfolio_fire(portfolio, config, _rng(99))
    assert [r.asset_id for r in a] == ["STRONG", "WEAK"]
    assert [r.n_fires for r in a] == [r.n_fires for r in b]
    assert [r.n_contained for r in a] == [r.n_contained for r in b]
