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
Compound gauge response model for Storm Generator v2.0 sequences.

Computes a continuous 168-hour river level hydrograph for a full
StormSequence, capturing the compounding effect where Storm 2 peaks
higher than Storm 1 due to antecedent soil moisture and groundwater.

Spec Section 5 requirements:
- Continuous 168h hydrograph
- River level partially drains during gap (does NOT return to baseline
  for short gaps; groundwater remains elevated for all gap lengths)
- Storm 2 peak > Storm 1 peak in >= 60% of doublet sequences
- Drainage window (hours 156-168) precipitation-free
- Validation: Storm 2 peak >= Storm 1 peak in >= 60% of doublets
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from config.port import EVENT_WINDOW_HOURS

from ..core.data_structures import StormSequence
from .hydrology import HydrologicalState, HydrologyModel, HydrologyParams

# EVENT_WINDOW_HOURS imported from config/port.py


@dataclass
class SequenceGaugeParams:
    """Gauge parameters needed for hydraulic routing.

    Decoupled from GaugeConfig so this module has no dependency on
    the stormgauge forward model. Use from_gauge_config() to convert.
    """
    gauge_id: str
    base_level: float           # Normal water level (m)
    flood_alert: float          # Flood alert threshold (m)
    flood_warning: float        # Flood warning threshold (m)
    severe_warning: float       # Severe warning threshold (m)

    # Hydraulic routing parameters
    sensitivity: float = 1.0            # Gauge response multiplier
    quickflow_to_level_scale: float = 0.50  # mm/h quickflow → m level rise
    response_lag_hours: int = 2         # Hours before quickflow reaches gauge
    response_decay_hours: float = 24.0  # Hydraulic time constant (hours)
    rise_factor: float = 3.0            # Channel rises this much faster than it falls

    @classmethod
    def from_gauge_config(cls, gauge_config) -> "SequenceGaugeParams":
        """Construct from a stormgauge GaugeConfig object."""
        return cls(
            gauge_id=gauge_config.gauge_id,
            base_level=gauge_config.base_level,
            flood_alert=gauge_config.flood_alert,
            flood_warning=gauge_config.flood_warning,
            severe_warning=gauge_config.severe_warning,
            sensitivity=gauge_config.sensitivity,
        )

    @classmethod
    def default_thames(cls, gauge_id: str = "GAUGE-DEFAULT") -> "SequenceGaugeParams":
        """Typical Thames gauge parameters for testing."""
        flood_alert = 4.0
        return cls(
            gauge_id=gauge_id,
            base_level=flood_alert * 0.35,       # 1.4m
            flood_alert=flood_alert,
            flood_warning=flood_alert * 1.33,    # 5.32m
            severe_warning=flood_alert * 1.58,   # 6.32m
        )


def _make_precip_series(
    sequence: StormSequence,
    n_hours: int = EVENT_WINDOW_HOURS,
) -> np.ndarray:
    """Convert a StormSequence into an hourly precipitation series (mm/h).

    Uses a triangular intensity profile within each storm, with peak at
    storm.peak_position * duration_hours. Total precipitation per storm
    equals storm.precipitation_mm exactly (within floating-point rounding).

    Args:
        sequence: StormSequence with 1-5 storms.
        n_hours: Length of output series (default 168).

    Returns:
        np.ndarray of shape (n_hours,) with precipitation in mm/h.
    """
    precip = np.zeros(n_hours)

    for storm in sequence.storms:
        start_h = int(round(storm.start_time_hours))
        duration_h = int(round(storm.duration_hours))
        end_h = min(start_h + duration_h, n_hours)

        if duration_h <= 0 or start_h >= n_hours:
            continue

        # Build triangular weight profile over the storm hours
        peak_pos = max(0.01, min(0.99, storm.peak_position))  # clamp from edges
        peak_h = int(round(peak_pos * duration_h))
        peak_h = max(0, min(duration_h - 1, peak_h))

        weights = np.zeros(duration_h)
        for i in range(duration_h):
            if i <= peak_h and peak_h > 0:
                weights[i] = i / peak_h
            elif i > peak_h and (duration_h - 1 - peak_h) > 0:
                weights[i] = (duration_h - 1 - i) / (duration_h - 1 - peak_h)
            else:
                weights[i] = 1.0  # uniform fallback

        weight_sum = weights.sum()
        if weight_sum > 0:
            weights /= weight_sum

        # Distribute precipitation into the output array
        available = min(duration_h, n_hours - start_h)
        precip[start_h:start_h + available] += weights[:available] * storm.precipitation_mm

    return precip


def _route_quickflow_to_level(
    quickflow_series: np.ndarray,
    params: SequenceGaugeParams,
) -> np.ndarray:
    """Route quickflow to river level using a first-order lag filter.

    Mirrors the asymmetric rise/fall approach in StormGaugeModel.compute_response():
    the channel rises `rise_factor` times faster than it falls, which is
    physically realistic — rivers respond quickly to runoff but recede slowly.

    Args:
        quickflow_series: Hourly quickflow in mm/h, shape (N,).
        params: Gauge parameters including routing coefficients.

    Returns:
        np.ndarray of river levels (m), shape (N,).
    """
    n = len(quickflow_series)
    levels = np.zeros(n)
    scale = params.quickflow_to_level_scale * params.sensitivity
    lag = params.response_lag_hours
    decay_rate = 1.0 / params.response_decay_hours  # per hour

    current_excess = 0.0  # m above base level

    for h in range(n):
        # Lagged quickflow input
        lag_h = max(0, h - lag)
        qf_input = quickflow_series[lag_h]
        target_excess = qf_input * scale

        # Asymmetric rise/fall: rises rise_factor × faster than it decays
        if target_excess > current_excess:
            rate = min(1.0, decay_rate * params.rise_factor)
            current_excess += (target_excess - current_excess) * rate
        else:
            current_excess += (target_excess - current_excess) * decay_rate

        current_excess = max(0.0, current_excess)
        levels[h] = params.base_level + current_excess

    return levels


def compute_sequence_gauge_response(
    sequence: StormSequence,
    gauge_params: SequenceGaugeParams,
    hydro_params: Optional[HydrologyParams] = None,
    initial_state: Optional[HydrologicalState] = None,
    precip_series: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Compute a 168-hour river level hydrograph for a StormSequence.

    For each of 168 hours:
    1. Determine precipitation from the sequence (triangular profile per storm)
    2. Update soil moisture + groundwater via HydrologyModel
    3. Compute quickflow (direct runoff + antecedent wetness contributions)
    4. Route quickflow to river level via first-order lag filter

    Compounding effect: Storm 2 starts with elevated soil moisture and
    groundwater from Storm 1, producing higher quickflow → higher peak.

    Args:
        sequence: A StormSequence (1-5 storms within 168h window).
        gauge_params: Gauge geometry and routing parameters.
        hydro_params: Hydrology model parameters. Defaults calibrated for Thames.
        initial_state: Starting soil moisture / groundwater. Defaults to dry.
        precip_series: Optional pre-computed precipitation array of shape (168,).
            When provided (e.g. spatially-adjusted per-gauge precip), it is used
            instead of calling _make_precip_series(sequence).

    Returns:
        np.ndarray of shape (168,) containing hourly river levels in metres.
        All values are >= gauge_params.base_level.
    """
    if precip_series is None:
        precip_series = _make_precip_series(sequence)
    model = HydrologyModel(params=hydro_params)
    quickflow, _ = model.run_series(precip_series, initial_state=initial_state)
    levels = _route_quickflow_to_level(quickflow, gauge_params)
    return levels


def compute_storm_peaks(
    sequence: StormSequence,
    gauge_params: SequenceGaugeParams,
    hydro_params: Optional[HydrologyParams] = None,
) -> List[Tuple[int, float]]:
    """Return the peak river level within each storm's active window.

    Useful for the compounding validation criterion: Storm 2 peak > Storm 1 peak.

    Args:
        sequence: StormSequence.
        gauge_params: Gauge parameters.
        hydro_params: Hydrology parameters.

    Returns:
        List of (storm_index, peak_level_m) in storm order.
    """
    levels = compute_sequence_gauge_response(sequence, gauge_params, hydro_params)

    peaks = []
    for storm in sequence.storms:
        start_h = int(round(storm.start_time_hours))
        end_h = min(start_h + int(round(storm.duration_hours)) + gauge_params.response_lag_hours + 6, EVENT_WINDOW_HOURS)
        start_h = max(0, start_h)
        end_h = min(end_h, EVENT_WINDOW_HOURS)
        if start_h < end_h:
            peak = float(np.max(levels[start_h:end_h]))
        else:
            peak = float(gauge_params.base_level)
        peaks.append((storm.storm_index, peak))

    return peaks
