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
Gauge response model — translates storm intensity into water levels.

The normal water level is derived from the gauge's flood thresholds,
NOT from elevation (which is only relevant for property flood risk).

Uses CDM field names from FloodGaugeCDM.create_mapping():
- gauge_id, gauge_name, catchment_id
- flood_alert, flood_warning, severe_flood_warning
"""

from typing import Dict, List

import hashlib

import numpy as np

from config.frequency import GAUGE_RESPONSE_SEED

from .data_structures import GaugeResponse


class GaugeResponseModel:
    """Models gauge response to storm scenarios."""

    def __init__(self, gauges: List[Dict], seed: int = GAUGE_RESPONSE_SEED):
        """
        Initialize the response model.

        Args:
            gauges: List of gauge dictionaries (flattened via CDM)
            seed: Run seed for the character and noise draws. Defaults to the
                configured value; pass a different one to explore the response
                model's own uncertainty deliberately rather than by accident.
        """
        self.gauges = gauges
        self.seed = seed
        self._calculate_gauge_characteristics()

    def _rng(self, *parts: str) -> np.random.Generator:
        """Return a generator seeded from the run seed and the given labels.

        Deriving the stream from the identifiers rather than drawing from one
        global sequence keeps a gauge's character stable when an unrelated
        gauge is added to or removed from the portfolio, and keeps a storm's
        noise stable when the storm set is re-ordered. Without that, a curve
        would move for reasons that have nothing to do with its own inputs.
        """
        label = "|".join((str(self.seed),) + parts)
        digest = hashlib.sha256(label.encode("utf-8")).digest()
        return np.random.default_rng(int.from_bytes(digest[:8], "big"))

    def _calculate_gauge_characteristics(self):
        """Calculate response characteristics for each gauge."""
        self.gauge_chars = {}

        for gauge in self.gauges:
            gauge_id = gauge['gauge_id']

            # Get flood thresholds from CDM
            flood_alert = gauge.get('flood_alert') or 3.0
            flood_warning = gauge.get('flood_warning') or 4.0
            severe_warning = gauge.get('severe_flood_warning') or 5.0

            # Normal water level is BELOW alert threshold
            # Typically 50-70% of alert level
            rng = self._rng("char", gauge_id)
            normal_level = flood_alert * rng.uniform(0.5, 0.7)

            # Response coefficient determines how much storm intensity
            # translates to water level rise. Calibrated so that:
            # - Most storms cause minor rises (stay below alert)
            # - Moderate storms may reach alert/warning
            # - Severe storms may reach severe warning
            #
            # The coefficient is scaled relative to the gap between
            # normal level and severe warning
            level_range = severe_warning - normal_level
            base_response = level_range * 0.015
            response_coef = base_response * rng.uniform(0.8, 1.2)

            self.gauge_chars[gauge_id] = {
                'response_coef': response_coef,
                'normal_level': normal_level,
                'flood_alert': flood_alert,
                'flood_warning': flood_warning,
                'severe_warning': severe_warning,
                'gauge_data': gauge
            }

    def compute_response(self, gauge_id: str, storm: Dict) -> GaugeResponse:
        """Compute gauge response to a storm."""
        chars = self.gauge_chars[gauge_id]

        base_level = chars['normal_level']

        # Calculate level change from storm
        precip_factor = storm['effective_precipitation_mm'] / 35.0
        duration_factor = min(2.0, storm['duration_hours'] / 24.0)

        level_change = (
            precip_factor *
            duration_factor *
            chars['response_coef'] *
            storm['intensity_factor']
        )

        # Add noise, drawn per (gauge, storm) so it is stable under re-ordering
        # of the storm set.
        level_change *= self._rng("noise", gauge_id, storm['storm_id']).uniform(0.85, 1.15)

        peak_level = base_level + level_change

        return GaugeResponse(
            gauge_id=gauge_id,
            storm_id=storm['storm_id'],
            base_level_m=base_level,
            level_change_m=level_change,
            peak_level_m=peak_level,
            exceeded_alert=peak_level >= chars['flood_alert'],
            exceeded_warning=peak_level >= chars['flood_warning'],
            exceeded_severe=peak_level >= chars['severe_warning']
        )

    def compute_all_responses(self, storms: List[Dict]) -> Dict[str, List[GaugeResponse]]:
        """Compute responses for all gauges across all storms."""
        responses = {g['gauge_id']: [] for g in self.gauges}

        for storm in storms:
            for gauge in self.gauges:
                response = self.compute_response(gauge['gauge_id'], storm)
                responses[gauge['gauge_id']].append(response)

        return responses
