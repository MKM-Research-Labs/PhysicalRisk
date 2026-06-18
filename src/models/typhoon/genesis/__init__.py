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
Genesis prior sampling for the typhoon model.

Implements the t=0 sampler that produces a TyphoonState from a
CatchmentTyphoonConfig. Each genesis sample consists of:

- Position uniform in the basin bbox
- Initial heading from a von Mises around the climatological mean
- Initial translation speed from a Gamma(shape, scale)
- Initial peak wind V_max from a hybrid truncated-normal + Pareto tail
  (spec eq. 14, per ScenarioFamily)
- Initial size (R_max, R_outer) from log-space regression on V_max
- Regime drawn from the categorical regime mixture
- Land flag evaluated via the catchment-supplied land_mask

The Pareto tail is the principal mechanism for generating rare extreme
storms; the scenario family controls how fat that tail is. Phase 1 of the
typhoon model prioritises *breadth* of the peak-wind distribution, so all
samplers route through this module.

All randomness flows through a single numpy.random.Generator passed in by
the caller. Callers that need reproducibility seed their own Generator.
"""

from models.typhoon.genesis._peakwind import (
    coupled_genesis_wind,
    coupling_floor,
    derive_scenario_family,
    mixture_peak_wind_exceedance,
    mixture_peak_wind_inverse,
    peak_wind_exceedance,
    peak_wind_inverse_exceedance,
    sample_peak_wind,
)
from models.typhoon.genesis._samplers import (
    _categorical,
    sample_genesis_location,
    sample_initial_heading,
    sample_initial_size,
    sample_initial_speed,
    sample_regime,
    sample_scenario_family,
)
from models.typhoon.genesis._top import (
    sample_genesis,
    sample_genesis_ensemble,
)

__all__ = [
    "peak_wind_exceedance",
    "peak_wind_inverse_exceedance",
    "sample_peak_wind",
    "mixture_peak_wind_exceedance",
    "mixture_peak_wind_inverse",
    "coupling_floor",
    "coupled_genesis_wind",
    "derive_scenario_family",
    "sample_genesis_location",
    "sample_initial_heading",
    "sample_initial_speed",
    "sample_initial_size",
    "sample_regime",
    "sample_scenario_family",
    "sample_genesis",
    "sample_genesis_ensemble",
]
