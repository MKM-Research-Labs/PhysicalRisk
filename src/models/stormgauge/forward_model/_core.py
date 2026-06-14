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
Storm gauge forward model.

Computes gauge water level responses given storm parameters by mapping storm
characteristics (track, intensity, footprint) to a water-level timeseries at
each gauge location. Geometry/intensity and response simulation live in mixins.
"""

from ._intensity import _IntensityMixin
from ._response import _ResponseMixin


class StormGaugeModel(_IntensityMixin, _ResponseMixin):
    """
    Forward model: Storm parameters -> Gauge water level responses.

    The model computes water level at each gauge based on:
    1. Storm track proximity (distance from gauge to nearest track point)
    2. Storm intensity at that track point
    3. Spatial decay based on distance and footprint
    4. Gauge-specific transfer function (intensity -> water level)

    Parameters:
        intensity_to_level_scale: Multiplier from intensity to water level contribution
        time_resolution_hours: Time step for simulation
        response_lag_hours: Lag between storm passage and peak gauge response
        response_decay_hours: How quickly gauge level returns to normal after storm
    """

    def __init__(
        self,
        intensity_to_level_scale: float = 0.1,
        time_resolution_hours: float = 0.5,
        response_lag_hours: float = 2.0,
        response_decay_hours: float = 12.0,
    ):
        self.intensity_to_level_scale = intensity_to_level_scale
        self.time_resolution_hours = time_resolution_hours
        self.response_lag_hours = response_lag_hours
        self.response_decay_hours = response_decay_hours
