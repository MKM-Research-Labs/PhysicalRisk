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

"""Water-level simulation and flood-alert classification."""

import math
from typing import Any, Dict

from config.port import GAUGETS_SIM_PARAMS as DEFAULT_PARAMS


def calculate_water_level(
    hour: int,
    gauge_index: int,
    base_level: float,
    params: Dict[str, Any] = None
) -> float:
    """
    Calculate water level for a given hour and gauge.

    Simulates a flood wave that peaks at different times for different gauges
    (downstream propagation effect).

    Args:
        hour: Current simulation hour
        gauge_index: Index of the gauge (affects peak timing)
        base_level: Base water level (typically alert level - 1.0)
        params: Simulation parameters (uses defaults if None)

    Returns:
        Simulated water level in meters
    """
    if params is None:
        params = DEFAULT_PARAMS

    peak_hour_base = params.get('peak_hour_base', params.get('peak_hour_min', 36))
    peak_hour_stagger = params.get('peak_hour_stagger', 2)
    simulation_hours = params.get('simulation_hours', 168)
    base_amplitude = params.get('base_amplitude', 0.5)
    peak_amplitude = params.get('peak_amplitude', 2.0)

    # Peak time varies by gauge (simulating wave propagation downstream)
    peak_hour = peak_hour_base + (gauge_index * peak_hour_stagger)

    # Calculate amplitude based on flood wave shape
    if hour < peak_hour - 12:
        # Rising phase
        progress = hour / max(1, peak_hour - 12)
        amplitude = base_amplitude + (progress * (peak_amplitude - base_amplitude))
    elif hour < peak_hour + 12:
        # Peak phase
        progress = abs(hour - peak_hour) / 12
        amplitude = peak_amplitude - (progress * 0.5)
    else:
        # Recession phase
        remaining = simulation_hours - peak_hour - 12
        if remaining > 0:
            progress = (hour - peak_hour - 12) / remaining
            amplitude = (peak_amplitude - 0.5) * (1 - progress)
        else:
            amplitude = base_amplitude

    # Add sinusoidal variation for natural fluctuations
    variation = math.sin((hour + gauge_index) * 0.3) * 0.2

    # Calculate final water level
    water_level = base_level + amplitude + variation

    return round(water_level, 2)


def determine_alert_status(
    water_level: float,
    alert_level: float,
    warning_level: float,
    severe_level: float
) -> str:
    """
    Determine flood alert status based on water level.

    Args:
        water_level: Current water level in meters
        alert_level: Flood alert threshold
        warning_level: Flood warning threshold
        severe_level: Severe flood warning threshold

    Returns:
        Alert status string
    """
    if water_level >= severe_level:
        return "Severe Flood Warning"
    elif water_level >= warning_level:
        return "Flood Warning"
    elif water_level >= alert_level:
        return "Flood Alert"
    else:
        return "Normal"
