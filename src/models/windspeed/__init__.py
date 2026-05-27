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
Wind-at-point query model — given a stored typhoon event, return the
sustained wind at any (hour, longitude, latitude).

Submodules:
    interpolation.py  linear state interpolation at arbitrary hour
    loader.py         EVT-*.json -> TyphoonTrajectory
    query.py          windspeed() function + WindSpeedModel class (with cache)
    timeseries.py     windspeed_series() — convenience for multi-hour queries

Catchment-agnostic — the model consumes WindFieldParams + a land mask
(typically pulled from CatchmentTyphoonConfig.wind_field / .land_mask).
"""

from models.windspeed.interpolation import interpolate_state_at_hour
from models.windspeed.loader import load_event
from models.windspeed.query import WindSpeedModel, windspeed
from models.windspeed.timeseries import windspeed_series


__all__ = [
    "interpolate_state_at_hour",
    "load_event",
    "windspeed",
    "WindSpeedModel",
    "windspeed_series",
]
