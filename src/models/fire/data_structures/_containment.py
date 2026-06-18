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

"""Stage-2 fire structures: response, intensity track, containment, credit."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config.fire import FireState


# ===========================================================================
# Stage-2 structures — response effectiveness (Model C)
# ===========================================================================


@dataclass
class ResponseProfile:
    """Per-asset response characteristics derived from the resilience fields.

    Computed once per asset (deterministic given the features) and reused for
    every fire that asset instantiates. It is the bridge from CDM resilience
    levels to the dynamics the intensity track and the chain march consume.

    Attributes:
        detection_steps: expected 15-min steps from ignition to detection.
        suppression_bite_steps: expected steps from detection until active
            suppression takes effect (already scaled by the height penalty).
        growth_per_step: base intensity added per step (compartmentation-driven).
        suppression_growth_multiplier: factor applied to growth once suppression
            is active (< 1 = suppression is reducing the spread).
        i_crit: critical intensity threshold for the point of no return.
        passive_effectiveness: aggregate passive (structural) defence in [0,1].
        response_effectiveness: aggregate active response in [0,1].
        height_penalty: >= 1 multiplier on suppression difficulty (storeys).
        controllability: aggregate score in [0,1] selecting the pre-PNR matrix.
        suppression_reachable: False when the building is above the fire-service
            reach height with no adequate internal sprinklers — suppression can
            never engage, so the fire is uncontrollable from ignition. The PNR
            gate then latches immediately ONLY when the structure is combustible
            (see structure_combustible); a non-combustible frame is contained by
            its own structure even when suppression cannot reach.
        combustibility: structural-frame combustibility in [0,1] derived from
            ConstructionType (0 = non-combustible reinforced concrete; 1 =
            timber frame).
        intensity_ceiling: cap on the latent intensity track I_t implied by the
            structure's combustibility. A non-combustible frame plateaus below
            even the worst i_crit, so it cannot cross the point of no return via
            the intensity race. Defaults to +inf (no cap) for profiles built
            without a construction type, preserving the pre-construction race.
        structure_combustible: whether combustibility clears the combustible
            threshold; gates the unreachable-suppression auto-PNR latch. Defaults
            True so a profile built without a construction type behaves as before.
    """
    detection_steps: float
    suppression_bite_steps: float
    growth_per_step: float
    suppression_growth_multiplier: float
    i_crit: float
    passive_effectiveness: float
    response_effectiveness: float
    height_penalty: float
    controllability: float
    suppression_reachable: bool = True
    combustibility: float = 1.0
    intensity_ceiling: float = float("inf")
    structure_combustible: bool = True

    @property
    def suppression_active_step(self) -> float:
        """First step index at which active suppression has bitten."""
        return self.detection_steps + self.suppression_bite_steps


# ===========================================================================
# Stage-2 structures — intensity track (Model B)
# ===========================================================================


@dataclass
class IntensityTrack:
    """Latent building-scale fire intensity I_t at one step of the march.

    The point of no return latches True the first step intensity exceeds i_crit
    while suppression has not yet bitten; once latched it stays True (the fire
    has become uncontrollable).

    Attributes:
        step: the 15-min step index this track describes (0 = ignition).
        intensity: latent intensity I_t.
        suppression_active: whether active suppression has bitten by this step.
        point_of_no_return: True once the fire became uncontrollable.
        point_of_no_return_step: the step PNR latched, or None.
    """
    step: int
    intensity: float
    suppression_active: bool
    point_of_no_return: bool
    point_of_no_return_step: Optional[int] = None


# ===========================================================================
# Stage-2 structures — containment & credit (Model D)
# ===========================================================================


@dataclass
class ContainmentOutcome:
    """Terminal outcome of marching one fire through the 8-state chain.

    Attributes:
        terminal_state: the absorbing state reached (S5/S6/S7), or the last
            state if max_steps was hit without absorption.
        steps: number of 15-min steps taken to reach the terminal state.
        reached_point_of_no_return: whether the PNR gate fired during the march.
        point_of_no_return_step: the step PNR latched, or None.
        peak_intensity: highest intensity I_t reached during the march.
    """
    terminal_state: FireState
    steps: int
    reached_point_of_no_return: bool
    point_of_no_return_step: Optional[int]
    peak_intensity: float

    @property
    def contained(self) -> bool:
        return self.terminal_state == FireState.S5_CONTAINED

    @property
    def partial_loss(self) -> bool:
        return self.terminal_state == FireState.S6_PARTIAL_LOSS

    @property
    def total_loss(self) -> bool:
        return self.terminal_state == FireState.S7_TOTAL_LOSS

    @property
    def any_loss(self) -> bool:
        return self.partial_loss or self.total_loss


@dataclass
class AssetFireResult:
    """End-to-end per-asset fire result (initiation + containment + credit).

    The credit currency mirrors the storm Monte Carlo engine: loss_frequency is
    the unconditional annual probability of a fire loss (over all n_sim draws,
    most of which never ignite), while containment_rate is conditional on a fire
    occurring.

    Attributes:
        asset_id: the asset this result is for.
        lambda_annual: annual ignition rate lambda_i (Model A).
        n_sim: number of Monte Carlo draws.
        n_fires: draws that instantiated a fire.
        n_contained / n_partial / n_total: terminal-state tallies over fires.
        n_point_of_no_return: fires that crossed the PNR gate.
        loss_frequency: (n_partial + n_total) / n_sim — annual, unconditional.
        partial_loss_frequency / total_loss_frequency: split of loss_frequency.
        containment_rate: n_contained / n_fires — conditional on ignition.
        outcomes: the per-fire ContainmentOutcome records.
    """
    asset_id: str
    lambda_annual: float
    n_sim: int
    n_fires: int
    n_contained: int
    n_partial: int
    n_total: int
    n_point_of_no_return: int
    loss_frequency: float
    partial_loss_frequency: float
    total_loss_frequency: float
    containment_rate: float
    outcomes: List[ContainmentOutcome] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serialisable summary (omits per-fire detail)."""
        return {
            "asset_id": self.asset_id,
            "lambda_annual": self.lambda_annual,
            "n_sim": self.n_sim,
            "n_fires": self.n_fires,
            "n_contained": self.n_contained,
            "n_partial": self.n_partial,
            "n_total": self.n_total,
            "n_point_of_no_return": self.n_point_of_no_return,
            "loss_frequency": self.loss_frequency,
            "partial_loss_frequency": self.partial_loss_frequency,
            "total_loss_frequency": self.total_loss_frequency,
            "containment_rate": self.containment_rate,
        }
