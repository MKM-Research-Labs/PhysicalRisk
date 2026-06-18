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
Configuration schema for the Building Seismic-Resilience Credit Model
(MKM-SEIS-001).

Defines the *shape* of the calibration knobs the seismic model expects and the
loader that hydrates them from two seed-matrices files:

- ``config/seismicmatrices.json`` — occurrence scalars, fragility medians,
  loss-given-damage-state, recovery and post-earthquake-fire seeds, and the
  BRI geoseismic measure modifiers (Appendices A2, D, E).
- ``config/seismic_zones.json``  — zone hazard rates, Gutenberg-Richter
  coefficients, GMPE selection, V_S30 site-class proxies and total sigma
  (Appendices A1, C).

Architecture (governance-separated component models):
- Model A — Occurrence (Poisson) + fault-geometry spatial draw -> R_JB
- Model B — Ground Motion Intensity (GMPE) -> site PGA
- Model C — Seismic Response Effectiveness (BRI measure -> modifier mapping)
- Model D — Damage State, Loss & Resilience Credit (lognormal fragility chain)

All numeric values live in the two JSON files and are engineering-judgement
SEEDS (placeholders), not calibrated values. This package never embeds the
numbers; it only describes their structure and loads them.
"""

from config.seismic._enums import DamageState, SoilClass
from config.seismic._loader import (
    DEFAULT_MATRICES_PATH,
    DEFAULT_ZONES_PATH,
    load_seismic_config,
)
from config.seismic._schema import (
    FragilityConfig,
    GroundMotionConfig,
    OccurrenceConfig,
    ResponseConfig,
    SeismicModelConfig,
    SeismicRunConfig,
)

__all__ = [
    "DamageState",
    "SoilClass",
    "SeismicRunConfig",
    "OccurrenceConfig",
    "GroundMotionConfig",
    "ResponseConfig",
    "FragilityConfig",
    "SeismicModelConfig",
    "load_seismic_config",
    "DEFAULT_MATRICES_PATH",
    "DEFAULT_ZONES_PATH",
]
