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

from dataclasses import replace
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
    "controllability_blend_weight",
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


def controllability_blend_weight(
    profile: ResponseProfile,
    cfg: ProgressionConfig,
) -> float:
    """Map controllability to a pre-PNR matrix blend weight in [0, 1].

    A fire is controllable if EITHER it can be actively suppressed OR it is
    passively contained by a non-combustible structure, so the weight is the
    larger of two contributions:

    * Active: w_active = clamp((controllability - blend_floor) /
      (blend_ceiling - blend_floor)) — the (well-graded) suppression/passive/
      response score remapped over the band the portfolio actually spans.
    * Structural: w_structural = clamp(structural_containment_weight *
      (1 - combustibility)) — a non-combustible frame (combustibility ~0)
      contains the fire floor-by-floor even when active suppression cannot reach
      it (a tall, unsprinklered concrete building), so it earns a high blend
      weight on its own; a combustible frame earns none.

    w = 1 is pure AA_controllable; w = 0 is pure weak_controllable.
    """
    block = cfg.controllability
    floor = block["blend_floor"]
    ceiling = block["blend_ceiling"]
    if ceiling <= floor:
        w_active = 1.0 if profile.controllability >= ceiling else 0.0
    else:
        w_active = (profile.controllability - floor) / (ceiling - floor)
        w_active = min(max(w_active, 0.0), 1.0)

    structural_weight = cfg.construction.get("structural_containment_weight", 0.0)
    w_structural = structural_weight * (1.0 - profile.combustibility)
    w_structural = min(max(w_structural, 0.0), 1.0)

    return max(w_active, w_structural)


def select_transition_matrix(
    profile: ResponseProfile,
    point_of_no_return: bool,
    cfg: ProgressionConfig,
) -> List[List[float]]:
    """Pick the active 8x8 transition matrix for the current step.

    Once the point of no return has latched the absorbing point_of_no_return
    matrix is used. Otherwise the pre-PNR matrix is a controllability-weighted
    blend of weak_controllable and AA_controllable: M = w*AA + (1-w)*weak, with
    w from controllability_blend_weight. Blending (rather than a hard switch)
    turns the continuous controllability score into a continuous containment
    response, so suppression, passive and response defences all grade the credit.
    """
    matrices = cfg.transition_matrices
    if point_of_no_return:
        return matrices["point_of_no_return"]
    w = controllability_blend_weight(profile, cfg)
    aa = matrices["AA_controllable"]
    weak = matrices["weak_controllable"]
    return [
        [w * a + (1.0 - w) * k for a, k in zip(aa_row, weak_row)]
        for aa_row, weak_row in zip(aa, weak)
    ]


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


def _jitter_profile_for_fire(
    profile: ResponseProfile,
    prog: ProgressionConfig,
    rng: np.random.Generator,
) -> ResponseProfile:
    """Draw this fire's race realisation from the asset's mean profile.

    The intensity race is otherwise deterministic per asset, which would force
    every fire of an asset to share one point-of-no-return verdict (so spread
    could only be 0 or the full ignition rate). Drawing per-fire lognormal jitter
    on the suppression-bite time and the per-step growth makes the PNR verdict a
    Bernoulli outcome per fire, so the conflagration probability grades smoothly.
    A reachable asset still suppresses on average; an unlucky draw (late bite /
    fast growth) can lose the race. sigma = 0 recovers the deterministic race.
    """
    jitter = prog.race_jitter
    timing_sigma = jitter.get("timing_sigma", 0.0)
    growth_sigma = jitter.get("growth_sigma", 0.0)
    ceiling_sigma = jitter.get("ceiling_sigma", 0.0)
    bite = profile.suppression_bite_steps
    growth = profile.growth_per_step
    ceiling = profile.intensity_ceiling
    if timing_sigma > 0.0:
        bite *= float(rng.lognormal(0.0, timing_sigma))
    if growth_sigma > 0.0:
        growth *= float(rng.lognormal(0.0, growth_sigma))
    # Jitter the fuel cap so a non-combustible structure with no suppression has
    # a small residual chance an unlucky fire's ceiling exceeds i_crit (the
    # "eventually it will catch" tail). Skips an infinite ceiling (combustible
    # frames are uncapped, so jitter is a no-op there).
    if ceiling_sigma > 0.0 and ceiling != float("inf"):
        ceiling *= float(rng.lognormal(0.0, ceiling_sigma))
    return replace(
        profile, suppression_bite_steps=bite, growth_per_step=growth,
        intensity_ceiling=ceiling,
    )


def simulate_fire_containment(
    profile: ResponseProfile,
    config: FireModelConfig,
    rng: np.random.Generator,
) -> ContainmentOutcome:
    """March one fire from ignition to a terminal state.

    Draws this fire's race realisation (per-fire jitter on bite time and growth),
    then steps the intensity track and samples the chain (starting at S0) under
    the per-step matrix until an absorbing state is reached or max_steps is hit.
    """
    prog = config.progression
    profile = _jitter_profile_for_fire(profile, prog, rng)
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
