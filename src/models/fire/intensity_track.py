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
Model B — intensity track for the fire model.

Advances the latent building-scale fire intensity I_t one 15-minute step at a
time. Growth each step is the compartmentation-driven base rate, damped by the
asset's aggregate passive effectiveness, and further reduced once active
suppression bites.

The point of no return (PNR) is the controllability race made concrete: the
first step where intensity exceeds the critical threshold i_crit *before*
suppression has bitten. At that step the fire becomes uncontrollable and the
PNR latch is set; the containment march then switches to the absorbing
point-of-no-return matrix. Once latched, PNR stays set.

Dynamics knobs come from ProgressionConfig (loaded from fire_matrices.json);
the per-asset values come from the ResponseProfile (Model C). This module is
deterministic — randomness lives in the chain march (Model D).
"""

from config.fire import ProgressionConfig
from models.fire.data_structures import IntensityTrack, ResponseProfile

__all__ = [
    "initial_intensity_track",
    "effective_growth",
    "advance_intensity",
]


def initial_intensity_track() -> IntensityTrack:
    """The intensity track at ignition (step 0): zero intensity, nothing active."""
    return IntensityTrack(
        step=0,
        intensity=0.0,
        suppression_active=False,
        point_of_no_return=False,
        point_of_no_return_step=None,
    )


def effective_growth(
    profile: ResponseProfile,
    cfg: ProgressionConfig,
    suppression_active: bool,
) -> float:
    """Intensity added this step given the asset profile and suppression state.

    Base compartmentation growth is damped by passive effectiveness, then scaled
    by the suppression multiplier once suppression is active:

        growth = growth_per_step * (1 - passive_damp_weight * passive_eff)
        if suppression_active: growth *= suppression_growth_multiplier
    """
    damp = cfg.intensity_dynamics["passive_damp_weight"]
    growth = profile.growth_per_step * (1.0 - damp * profile.passive_effectiveness)
    growth = max(growth, 0.0)
    if suppression_active:
        growth *= profile.suppression_growth_multiplier
    return growth


def advance_intensity(
    track: IntensityTrack,
    profile: ResponseProfile,
    cfg: ProgressionConfig,
) -> IntensityTrack:
    """Advance the intensity track by one 15-minute step.

    Determines whether suppression has bitten by this step, grows the intensity
    (capped at the structure's combustibility-implied ceiling), and latches the
    point of no return when suppression has not yet bitten and either intensity
    crosses i_crit, or suppression is structurally unreachable AND the structure
    is combustible (a tall combustible building with no internal sprinklers —
    uncontrollable from ignition). A non-combustible frame above the fire-service
    reach is contained by its own structure: its intensity ceiling sits below
    i_crit, so the race never crosses and the unreachable latch does not fire.
    """
    next_step = track.step + 1
    suppression_active = next_step >= profile.suppression_active_step

    growth = effective_growth(profile, cfg, suppression_active)
    intensity = min(track.intensity + growth, profile.intensity_ceiling)

    point_of_no_return = track.point_of_no_return
    pnr_step = track.point_of_no_return_step
    unreachable_latch = (
        not profile.suppression_reachable and profile.structure_combustible
    )
    crossed = intensity > profile.i_crit or unreachable_latch
    if not point_of_no_return and crossed and not suppression_active:
        point_of_no_return = True
        pnr_step = next_step

    return IntensityTrack(
        step=next_step,
        intensity=intensity,
        suppression_active=suppression_active,
        point_of_no_return=point_of_no_return,
        point_of_no_return_step=pnr_step,
    )
