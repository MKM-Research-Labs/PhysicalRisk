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

"""Model C response-effectiveness profile type."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class SeismicResponseProfile:
    """Deterministic modifiers derived from an asset's BRI geoseismic measures.

    Model C introduces no randomness; this profile is computed once per asset
    and consumed by Model D.

    Attributes:
        asset_id: stable identifier for the asset.
        theta_mult: per-damage-state fragility median multiplier, keyed
            "DS1"/"DS2"/"DS3". A multiplier > 1.0 raises the median PGA at that
            threshold (more resilient -> rarer damage).
        rating: derived BRI geoseismic rating ("AA"/"A"/"B"/"NR").
        r_acc: recovery acceleration factor (effective T_rec = T_rec / r_acc).
        p_pef_by_ds: post-GS15 post-earthquake-fire probability per damage state.
        gs02_present: whether GS02 is installed (the soft-soil F_a gate; the
            amplification itself is applied in Model B from the same flag).
    """
    asset_id: str
    theta_mult: Dict[str, float]
    rating: str
    r_acc: float
    p_pef_by_ds: Dict[str, float]
    gs02_present: bool
