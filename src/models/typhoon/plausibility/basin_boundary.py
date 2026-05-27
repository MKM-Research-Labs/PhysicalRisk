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

"""Basin-boundary plausibility — smooth penalty for tracks leaving the basin.

For a track at (lon, lat), compute the signed distance outside the
basin bbox (zero when inside, positive when outside). Apply a Gaussian
penalty on the Euclidean distance in degrees:

    out_lon = max(0, lon_min - lon, lon - lon_max)
    out_lat = max(0, lat_min - lat, lat - lat_max)
    score   = exp(-weight * (out_lon^2 + out_lat^2))

Inside the bbox: score = 1.0. Outside: degrades smoothly with the
squared overshoot in degrees. The bbox is treated as the genesis prior
bbox; future phases can pass a wider expanded basin if needed.
"""

import math
from typing import Tuple

from models.typhoon.data_structures import TyphoonState


__all__ = ["basin_boundary_score"]


def basin_boundary_score(
    state: TyphoonState,
    bbox: Tuple[float, float, float, float],
    weight: float,
) -> float:
    """Return a multiplier in (0, 1] penalising tracks outside the basin bbox.

    Args:
        state: current state
        bbox: (lon_min, lat_min, lon_max, lat_max)
        weight: penalty strength; 0 disables
    """
    if weight <= 0.0:
        return 1.0
    lon_min, lat_min, lon_max, lat_max = bbox
    out_lon = max(0.0, lon_min - state.longitude, state.longitude - lon_max)
    out_lat = max(0.0, lat_min - state.latitude, state.latitude - lat_max)
    out_sq = out_lon * out_lon + out_lat * out_lat
    return math.exp(-weight * out_sq)
