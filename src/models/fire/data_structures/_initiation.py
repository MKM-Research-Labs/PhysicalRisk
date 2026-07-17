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

"""Stage-1 fire initiation output structures."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from config.fire import InitiationClass


# ===========================================================================
# Stage-1 outputs
# ===========================================================================


@dataclass
class IgnitionDraw:
    """One Poisson draw for one asset.

    Attributes:
        draw_index: index of the draw within the asset's n_sim ensemble.
        count: Poisson count N_i for this draw.
        fire: True when count >= 1 (a fire instantiates).
        initiation_class: assigned entry-point class when fire is True, else None.
    """
    draw_index: int
    count: int
    fire: bool
    initiation_class: Optional[InitiationClass] = None


@dataclass
class AssetInitiationResult:
    """Per-asset summary of the Stage-1 initiation simulation.

    Attributes:
        asset_id: the asset this result is for.
        lambda_annual: effective annual ignition rate lambda_i.
        lambda_effective: rate scaled to the run horizon (lambda_i * horizon_years).
        n_sim: number of draws taken.
        n_fires: number of draws with a fire (count >= 1).
        fire_probability: n_fires / n_sim — empirical P(at least one ignition).
        class_counts: count of instantiated fires by InitiationClass.
        draws: the per-draw IgnitionDraw records.
    """
    asset_id: str
    lambda_annual: float
    lambda_effective: float
    n_sim: int
    n_fires: int
    fire_probability: float
    class_counts: Dict[InitiationClass, int] = field(default_factory=dict)
    draws: List[IgnitionDraw] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serialisable summary (omits per-draw detail)."""
        return {
            "asset_id": self.asset_id,
            "lambda_annual": self.lambda_annual,
            "lambda_effective": self.lambda_effective,
            "n_sim": self.n_sim,
            "n_fires": self.n_fires,
            "fire_probability": self.fire_probability,
            "class_counts": {k.value: v for k, v in self.class_counts.items()},
        }
