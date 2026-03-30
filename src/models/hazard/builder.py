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
Hazard curve builder — orchestrates gauge responses, GEV fitting,
and term structure computation into complete hazard curves.
"""

import logging
from datetime import datetime
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)

from .data_structures import GaugeHazardCurve, HazardCurvePoint
from .gev import GEVFitter, compute_term_structure
from .response_model import GaugeResponseModel


class HazardCurveBuilder:
    """Builds hazard curves from storm scenarios and gauge responses."""

    STANDARD_THRESHOLDS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
    RETURN_PERIODS = [2, 5, 10, 20, 50, 100]

    def __init__(
        self,
        gauges: List[Dict],
        storms: List[Dict],
        force_gumbel: bool = False,
        verbose: bool = True
    ):
        self.gauges = gauges
        self.storms = storms
        self.verbose = verbose

        self.response_model = GaugeResponseModel(gauges)
        self.gev_fitter = GEVFitter(force_gumbel)

    def log(self, message: str):
        if self.verbose:
            logger.info(message)

    def build(self) -> Dict[str, GaugeHazardCurve]:
        """Build hazard curves for all gauges."""
        self.log(f"Computing gauge responses for {len(self.storms)} storms...")
        responses = self.response_model.compute_all_responses(self.storms)

        self.log(f"Fitting GEV distributions for {len(self.gauges)} gauges...")
        hazard_curves = {}

        for i, gauge in enumerate(self.gauges):
            gauge_id = gauge['gauge_id']
            gauge_responses = responses[gauge_id]

            # Extract peak levels
            peak_levels = np.array([r.peak_level_m for r in gauge_responses])

            # Fit GEV
            shape, loc, scale = self.gev_fitter.fit(peak_levels)

            # Build curve points
            curve_points = []
            for threshold in self.STANDARD_THRESHOLDS:
                abs_threshold = loc + threshold
                exc_prob = self.gev_fitter.exceedance_probability(abs_threshold, shape, loc, scale)
                # Cap at 100yr return period (1% annual probability)
                if 0 < exc_prob < 0.01:
                    exc_prob = 0.01
                return_period = 1.0 / exc_prob if exc_prob > 1e-10 else 9999

                curve_points.append(HazardCurvePoint(
                    threshold_m=abs_threshold,
                    annual_exceedance_prob=exc_prob,
                    return_period_years=return_period
                ))

            # Return period levels
            return_period_levels = {}
            for rp in self.RETURN_PERIODS:
                level = self.gev_fitter.return_level(rp, shape, loc, scale)
                return_period_levels[f"{rp}yr"] = level

            # Flood probabilities
            gauge_chars = self.response_model.gauge_chars[gauge_id]
            alert = gauge_chars['flood_alert']
            warning = gauge_chars['flood_warning']
            severe = gauge_chars['severe_warning']

            prob_alert = self.gev_fitter.exceedance_probability(alert, shape, loc, scale)
            prob_warning = self.gev_fitter.exceedance_probability(warning, shape, loc, scale)
            prob_severe = self.gev_fitter.exceedance_probability(severe, shape, loc, scale)

            # Term structures
            term_structure_alert = compute_term_structure(prob_alert)
            term_structure_warning = compute_term_structure(prob_warning)
            term_structure_severe = compute_term_structure(prob_severe)

            # Get coordinates
            lat = gauge.get('gauge_latitude') or gauge.get('latitude') or 0.0
            lon = gauge.get('gauge_longitude') or gauge.get('longitude') or 0.0

            hazard_curve = GaugeHazardCurve(
                gauge_id=gauge_id,
                gauge_name=gauge.get('gauge_name') or f"Gauge {gauge_id}",
                latitude=lat,
                longitude=lon,
                elevation_m=0.0,
                flood_alert_m=alert,
                flood_warning_m=warning,
                severe_flood_warning_m=severe,
                gev_location=loc,
                gev_scale=scale,
                gev_shape=shape,
                curve_points=curve_points,
                return_period_levels=return_period_levels,
                annual_flood_prob_alert=prob_alert,
                annual_flood_prob_warning=prob_warning,
                annual_flood_prob_severe=prob_severe,
                annual_hazard_rate_alert=prob_alert,
                annual_hazard_rate_warning=prob_warning,
                annual_hazard_rate_severe=prob_severe,
                term_structure_alert=term_structure_alert,
                term_structure_warning=term_structure_warning,
                term_structure_severe=term_structure_severe,
                num_storms_simulated=len(self.storms),
                simulation_timestamp=datetime.now().isoformat()
            )

            hazard_curves[gauge_id] = hazard_curve

            if (i + 1) % 10 == 0:
                self.log(f"Processed {i + 1}/{len(self.gauges)} gauges")

        self.log(f"Built hazard curves for {len(hazard_curves)} gauges")
        return hazard_curves, responses
