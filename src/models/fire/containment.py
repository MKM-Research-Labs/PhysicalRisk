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
Model D — containment, loss and resilience credit for the fire model.

Marches one fire through the 8-state Bayesian chain in 15-minute steps. At each
step the latent intensity track (Model B) advances and the active transition
matrix is chosen from the asset's controllability (Model C): a controllable
asset uses AA_controllable, a weak asset uses weak_controllable, and once the
point of no return latches every transient state switches to the absorbing
point_of_no_return matrix (its S5/Contained column is zero, so containment is no
longer reachable). The chain is sampled until it reaches an absorbing state
(S5/S6/S7) or the step budget runs out.

The end-to-end orchestrator ties Model A (initiation) to this stage: for each of
n_sim draws it decides fire/no-fire, marches every instantiated fire, and
aggregates the outcomes into the resilience-credit currency
(loss_frequency over all draws; containment_rate conditional on a fire).

Randomness flows through a single caller-owned numpy.random.Generator, matching
the typhoon model and Stage 1 convention.
"""

from typing import List

import numpy as np

from config.fire import FireModelConfig, FireState, ProgressionConfig
from models.fire.data_structures import (
    AssetFireFeatures,
    AssetFireResult,
    ContainmentOutcome,
    ResponseProfile,
)
from models.fire.initiation import asset_lambda, simulate_asset_initiation
from models.fire.intensity_track import advance_intensity, initial_intensity_track
from models.fire.response_effectiveness import derive_response_profile

__all__ = [
    "TERMINAL_STATES",
    "select_transition_matrix",
    "sample_next_state",
    "simulate_fire_containment",
    "simulate_asset_fire",
    "simulate_portfolio_fire",
]


# The absorbing states that end a fire's march.
TERMINAL_STATES = frozenset({
    FireState.S5_CONTAINED,
    FireState.S6_PARTIAL_LOSS,
    FireState.S7_TOTAL_LOSS,
})


def select_transition_matrix(
    profile: ResponseProfile,
    point_of_no_return: bool,
    cfg: ProgressionConfig,
) -> List[List[float]]:
    """Pick the active 8x8 transition matrix for the current step.

    Once the point of no return has latched the absorbing point_of_no_return
    matrix is used. Otherwise a hard switch on the controllability score selects
    AA_controllable (controllable) or weak_controllable (weak).
    """
    matrices = cfg.transition_matrices
    if point_of_no_return:
        return matrices["point_of_no_return"]
    threshold = cfg.controllability["switch_threshold"]
    if profile.controllability >= threshold:
        return matrices["AA_controllable"]
    return matrices["weak_controllable"]


def sample_next_state(
    state: FireState,
    matrix: List[List[float]],
    rng: np.random.Generator,
) -> FireState:
    """Sample the next state from the row of ``matrix`` for the current state.

    Row probabilities are renormalised defensively so small calibration drift in
    a matrix row does not error out at sample time.
    """
    row = np.array(matrix[state.value], dtype=float)
    total = row.sum()
    if total <= 0.0:
        raise ValueError(f"Transition row for {state.name} sums to zero")
    row = row / total
    idx = int(rng.choice(len(row), p=row))
    return FireState(idx)


def simulate_fire_containment(
    profile: ResponseProfile,
    config: FireModelConfig,
    rng: np.random.Generator,
) -> ContainmentOutcome:
    """March one fire from ignition to a terminal state.

    Steps the intensity track and samples the chain (starting at S0) under the
    per-step matrix until an absorbing state is reached or max_steps is hit.
    """
    prog = config.progression
    state = FireState.S0_EXPOSURE_OR_IGNITION
    track = initial_intensity_track()
    peak_intensity = track.intensity
    steps = 0

    for _ in range(config.run.max_steps):
        track = advance_intensity(track, profile, prog)
        peak_intensity = max(peak_intensity, track.intensity)
        matrix = select_transition_matrix(profile, track.point_of_no_return, prog)
        state = sample_next_state(state, matrix, rng)
        steps += 1
        if state in TERMINAL_STATES:
            break

    return ContainmentOutcome(
        terminal_state=state,
        steps=steps,
        reached_point_of_no_return=track.point_of_no_return,
        point_of_no_return_step=track.point_of_no_return_step,
        peak_intensity=peak_intensity,
    )


def simulate_asset_fire(
    features: AssetFireFeatures,
    config: FireModelConfig,
    rng: np.random.Generator,
) -> AssetFireResult:
    """Run the full fire model for one asset (initiation + containment + credit).

    Model A decides which of the n_sim draws ignite; every ignited draw is
    marched through the containment chain. Outcomes aggregate into the
    resilience-credit currency.
    """
    profile = derive_response_profile(features, config.progression)
    initiation = simulate_asset_initiation(features, config, rng)

    outcomes: List[ContainmentOutcome] = []
    n_contained = n_partial = n_total = n_pnr = 0
    for draw in initiation.draws:
        if not draw.fire:
            continue
        outcome = simulate_fire_containment(profile, config, rng)
        outcomes.append(outcome)
        if outcome.contained:
            n_contained += 1
        elif outcome.partial_loss:
            n_partial += 1
        elif outcome.total_loss:
            n_total += 1
        if outcome.reached_point_of_no_return:
            n_pnr += 1

    n_sim = config.run.n_sim
    n_fires = initiation.n_fires
    return AssetFireResult(
        asset_id=features.asset_id,
        lambda_annual=asset_lambda(features, config.initiation),
        n_sim=n_sim,
        n_fires=n_fires,
        n_contained=n_contained,
        n_partial=n_partial,
        n_total=n_total,
        n_point_of_no_return=n_pnr,
        loss_frequency=(n_partial + n_total) / n_sim if n_sim else 0.0,
        partial_loss_frequency=n_partial / n_sim if n_sim else 0.0,
        total_loss_frequency=n_total / n_sim if n_sim else 0.0,
        containment_rate=n_contained / n_fires if n_fires else 0.0,
        outcomes=outcomes,
    )


def simulate_portfolio_fire(
    features: List[AssetFireFeatures],
    config: FireModelConfig,
    rng: np.random.Generator,
) -> List[AssetFireResult]:
    """Run the full fire model for every asset in a portfolio.

    Assets share the single caller-owned Generator, so the whole portfolio run
    is reproducible from one seed.
    """
    return [simulate_asset_fire(f, config, rng) for f in features]
