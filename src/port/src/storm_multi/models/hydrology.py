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

"""
Simplified catchment hydrology model for Storm Generator v2.0.

Implements the antecedent condition state equations from spec Section 5.3.
Converts hourly precipitation (mm) into quickflow (mm/h) via a three-store
model: soil moisture, groundwater, and direct runoff.

State equations (all per hour):
    soil_moisture[h] = soil_moisture[h-1] * (1 - drainage_coeff)
                       + precip[h] * infiltration_coeff

    groundwater[h]   = groundwater[h-1] * (1 - baseflow_coeff)
                       + soil_moisture[h] * percolation_coeff

    quickflow[h]     = precip[h] * (1 - infiltration_coeff)
                       + alpha * soil_moisture[h]
                       + beta  * groundwater[h]
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class HydrologyParams:
    """Parameters for the catchment hydrology model.

    Defaults are calibrated for a Thames-like lowland catchment with
    clay-dominated soils and relatively low permeability (spec Table 3).
    """
    # Fraction of precipitation absorbed by soil (vs direct overland flow)
    infiltration_coeff: float = 0.70

    # Hourly fraction of soil moisture that drains (time constant ~50h)
    drainage_coeff: float = 0.02

    # Hourly fraction of soil moisture that percolates to groundwater
    # (kept small to prevent GW store dominating multi-day drainage)
    percolation_coeff: float = 0.01

    # Hourly fraction of groundwater that leaves as baseflow (time constant ~50h)
    # Upper end of spec range (0.005-0.02) to ensure recovery within 168h window
    baseflow_coeff: float = 0.02

    # Contribution of soil moisture to quickflow (antecedent wetness effect)
    # Calibrated so SM drives compounding without overwhelming drainage
    alpha: float = 0.05

    # Contribution of groundwater to quickflow
    # Kept low to prevent slow GW release sustaining high levels indefinitely
    beta: float = 0.05


@dataclass
class HydrologicalState:
    """Catchment state at a single timestep."""
    soil_moisture: float = 0.0   # mm of water stored in soil
    groundwater: float = 0.0     # mm of water in groundwater store


class HydrologyModel:
    """Hourly catchment hydrology model.

    Maintains soil moisture and groundwater state between calls. The
    compounding effect arises because Storm 2 starts with elevated state
    (wet soil from Storm 1), producing higher quickflow per unit of
    precipitation even before additional precipitation accumulates.

    Usage:
        model = HydrologyModel()
        state = HydrologicalState()
        for h in range(168):
            state, qf = model.step(state, precip[h])
    """

    def __init__(self, params: Optional[HydrologyParams] = None):
        self.params = params or HydrologyParams()

    def step(
        self,
        state: HydrologicalState,
        precip_mm: float,
    ) -> Tuple[HydrologicalState, float]:
        """Advance state by one hour.

        Args:
            state: Current catchment state (soil moisture, groundwater).
            precip_mm: Precipitation falling this hour (mm).

        Returns:
            (new_state, quickflow_mm) where quickflow is the runoff
            generated this hour (mm), which feeds the river routing.
        """
        p = self.params
        precip_mm = max(0.0, precip_mm)

        # Update soil moisture (infiltration - drainage)
        new_sm = (
            state.soil_moisture * (1.0 - p.drainage_coeff)
            + precip_mm * p.infiltration_coeff
        )

        # Update groundwater (percolation from soil - baseflow)
        new_gw = (
            state.groundwater * (1.0 - p.baseflow_coeff)
            + new_sm * p.percolation_coeff
        )

        # Quickflow: direct runoff + soil moisture contribution + groundwater
        quickflow = (
            precip_mm * (1.0 - p.infiltration_coeff)
            + p.alpha * new_sm
            + p.beta * new_gw
        )

        return HydrologicalState(soil_moisture=new_sm, groundwater=new_gw), quickflow

    def run_series(
        self,
        precip_series: np.ndarray,
        initial_state: Optional[HydrologicalState] = None,
    ) -> Tuple[np.ndarray, List[HydrologicalState]]:
        """Run the model over a full precipitation series.

        Args:
            precip_series: Array of hourly precipitation values (mm), shape (N,).
            initial_state: Starting state. Defaults to dry conditions.

        Returns:
            (quickflow_series, states) where quickflow_series is shape (N,)
            and states is a list of N HydrologicalState objects.
        """
        state = initial_state or HydrologicalState()
        n = len(precip_series)
        quickflow = np.zeros(n)
        states = []

        for h in range(n):
            state, qf = self.step(state, float(precip_series[h]))
            quickflow[h] = qf
            states.append(state)

        return quickflow, states
