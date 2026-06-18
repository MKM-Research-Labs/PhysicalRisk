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

"""Model B ground-motion output types."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class GroundMotionSample:
    """The site ground motion for one instantiated earthquake (Model B).

    Attributes:
        draw_index: the Monte Carlo draw this sample belongs to (aligned with
            the originating :class:`EarthquakeEvent`).
        pga_g: sampled site peak ground acceleration (g).
        median_pga_g: the GMPE median PGA (g) before the aleatory residual
            (already includes any soft-soil amplification factor).
        epsilon: the standard-normal residual draw used for this sample.
    """
    draw_index: int
    pga_g: float
    median_pga_g: float
    epsilon: float


@dataclass
class GroundMotionResult:
    """Per-asset summary of Model B ground-motion sampling.

    Attributes:
        asset_id: stable identifier for the asset.
        regime: tectonic regime whose GMPE was used.
        vs30_mps: effective V_S30 (m/s) applied in the GMPE.
        site_class: Eurocode 8 site class (A-E).
        amplification_factor: soft-soil F_a applied to the GMPE median (1.0 when
            not gated; 1.30 for class D/E with GS02 absent).
        sigma_total: GMPE total log-standard deviation used for the residual.
        samples: per-event ground-motion samples (aligned with the events).
    """
    asset_id: str
    regime: str
    vs30_mps: float
    site_class: str
    amplification_factor: float
    sigma_total: float
    samples: List[GroundMotionSample] = field(default_factory=list)

    @property
    def median_pga_g(self) -> Optional[float]:
        """Median of the sampled site PGAs, or None when no events occurred."""
        if not self.samples:
            return None
        vals = sorted(s.pga_g for s in self.samples)
        n = len(vals)
        mid = n // 2
        return vals[mid] if n % 2 else 0.5 * (vals[mid - 1] + vals[mid])
