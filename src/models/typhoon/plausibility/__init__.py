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
Plausibility scoring — simulation-mode soft likelihoods.

Implements the simulation-mode plausibility framework from spec p.6:
when no real observations are available, the Bayesian update degenerates
to a soft-constraint score that penalises unphysical or off-regime
behaviour.

Each component produces a multiplier in (0, 1]; the composer
plausibility_score returns their product. Components are split by
concern so each can evolve independently:

  - heading_jump.py        sharp Δψ penalty
  - speed_jump.py          large |Δu| penalty
  - basin_boundary.py      smooth bbox-exit penalty
  - regime_consistency.py  off-regime speed/heading penalty
  - score.py               composer + ParticleFilter adapter

Phase 1 defaults in PlausibilityWeights are deliberately loose so the
particle ensemble retains breadth of peak winds — the priority for this
phase.
"""

from models.typhoon.plausibility.basin_boundary import basin_boundary_score
from models.typhoon.plausibility.heading_jump import heading_jump_score
from models.typhoon.plausibility.regime_consistency import regime_consistency_score
from models.typhoon.plausibility.score import (
    make_particle_plausibility,
    plausibility_score,
)
from models.typhoon.plausibility.speed_jump import speed_jump_score


__all__ = [
    # components
    "heading_jump_score",
    "speed_jump_score",
    "basin_boundary_score",
    "regime_consistency_score",
    # composer + adapter
    "plausibility_score",
    "make_particle_plausibility",
]
