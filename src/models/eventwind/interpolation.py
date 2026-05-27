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

"""Linear interpolation of a typhoon state between two stored hours.

Continuous fields (position, speed, wind, size, time) are linearly
interpolated. Heading uses circular interpolation via signed_compass_delta
to handle the 0/360 seam. Discrete fields (regime, land_flag) take the
nearest neighbour.

Queries before the first state return the first state; queries after the
last state return the last state. Both are clamped, not extrapolated.
"""

from typing import List

from models.typhoon.data_structures import TyphoonState
from models.typhoon.transitions.compass import signed_compass_delta


__all__ = ["interpolate_state_at_hour"]


def _lerp_state(a: TyphoonState, b: TyphoonState, t: float) -> TyphoonState:
    """Linear interpolation between two states. t in [0, 1]."""
    # Circular heading interpolation along the short arc.
    delta_heading = signed_compass_delta(b.heading_deg, a.heading_deg)
    new_heading = (a.heading_deg + delta_heading * t) % 360.0

    return TyphoonState(
        longitude=a.longitude + t * (b.longitude - a.longitude),
        latitude=a.latitude + t * (b.latitude - a.latitude),
        translation_speed_kmh=a.translation_speed_kmh
            + t * (b.translation_speed_kmh - a.translation_speed_kmh),
        heading_deg=new_heading,
        v_max_ms=a.v_max_ms + t * (b.v_max_ms - a.v_max_ms),
        r_max_km=a.r_max_km + t * (b.r_max_km - a.r_max_km),
        r_outer_km=a.r_outer_km + t * (b.r_outer_km - a.r_outer_km),
        regime=a.regime if t < 0.5 else b.regime,
        land_flag=a.land_flag if t < 0.5 else b.land_flag,
        time_hours=a.time_hours + t * (b.time_hours - a.time_hours),
    )


def interpolate_state_at_hour(states: List[TyphoonState], hour: float) -> TyphoonState:
    """Return the state at the requested hour, linearly interpolated.

    Args:
        states: time-ordered TyphoonState list (output of the pipeline)
        hour: target hour since genesis

    Returns:
        TyphoonState at the requested hour. Clamped to first / last state
        outside the trajectory's time range.
    """
    if not states:
        raise ValueError("Cannot interpolate empty state list")

    if hour <= states[0].time_hours:
        return states[0]
    if hour >= states[-1].time_hours:
        return states[-1]

    # Binary search would be faster for long trajectories; linear scan is
    # fine for the 168-state hourly trajectories the pipeline produces.
    for i in range(len(states) - 1):
        a, b = states[i], states[i + 1]
        if a.time_hours <= hour <= b.time_hours:
            span = b.time_hours - a.time_hours
            if span <= 0:
                # Duplicate timestamps — return the earlier state.
                return a
            t = (hour - a.time_hours) / span
            return _lerp_state(a, b, t)

    # Should be unreachable given the bounds checks above.
    return states[-1]
