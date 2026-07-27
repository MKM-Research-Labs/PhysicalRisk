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
Hazard curve builder — orchestrates gauge responses, GEV fitting,
and term structure computation into complete hazard curves.
"""

import logging
from datetime import datetime
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)

from config.frequency import (
    catchment_annual_growth,
    catchment_lambda,
    config_hash,
    load_frequency_config,
)

from models.floodrisk.depth_damage import scalar_depth_damage
from models.frequency import (
    annual_exceedance_probability,
    annual_hazard_by_year,
    compact_loss_block,
    loss_metrics,
    peak_level_losses,
    rate_process_for,
    shared_draws,
)
from models.frequency.datastructures import ProvenanceClass
from models.frequency.events import build_catalogue

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
        verbose: bool = True,
        catchment: str = ""
    ):
        """Build hazard curves from storms and gauges.

        Args:
            gauges: flat gauge dicts.
            storms: storm dicts carrying their parent event tag.
            force_gumbel: fit Gumbel rather than GEV.
            verbose: log progress.
            catchment: catchment whose event arrival rate annualises the
                per-event conditionals. Empty uses the default seed rate.
        """
        self.gauges = gauges
        self.storms = storms
        self.verbose = verbose
        self.catchment = catchment

        self.response_model = GaugeResponseModel(gauges)
        self.gev_fitter = GEVFitter(force_gumbel)

    def log(self, message: str):
        if self.verbose:
            logger.info(message)

    def build(self) -> Dict[str, GaugeHazardCurve]:
        """Build hazard curves for all gauges."""
        self.log(f"Computing gauge responses for {len(self.storms)} storms...")
        responses = self.response_model.compute_all_responses(self.storms)

        # Regroup the per-storm responses onto hours-clause events. The physics
        # is untouched — each storm was still routed individually — but an event
        # is the unit that arrives at a rate, and the catalogue carries the
        # population weights that stop a stress-weighted storm set being read as
        # a fair sample of the events a year contains.
        catalogue = build_catalogue(responses, self.storms)
        lambda_per_year = catchment_lambda(self.catchment)
        self.log(
            f"Event catalogue: {catalogue.n_storms} storms -> {catalogue.n_events} "
            f"events; lambda = {lambda_per_year}/yr"
        )

        # Loss-weighted view (MKM-EF-001 Stage 6c, additive). Drawn once for the
        # whole catchment so every gauge is scored against the same simulated
        # storms, which keeps their annual losses correlated. The lambda is
        # a config seed rather than a fitted rate, so the loss table is stamped
        # generator-derived.
        freq_config = load_frequency_config(self.catchment or None)
        loss_config_hash = config_hash(freq_config)
        loss_return_periods = freq_config.rate.return_periods_years
        loss_draws = shared_draws(catalogue, lambda_per_year, freq_config.simulation)

        # Arrival-rate process for the multi-year term structure (Stage 6h).
        # Stationary by default — an empty growth registry gives a ConstantRate,
        # so the term structure is unchanged unless a catchment carries a trend.
        rate_process = rate_process_for(
            lambda_per_year, catchment_annual_growth(self.catchment))

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

            # Per-EVENT conditional exceedance, weighted onto the event
            # population (MKM-EF-001). This is an honest conditional; it is not
            # an annual probability and is no longer labelled as one.
            p_event_alert = catalogue.conditional_probability(gauge_id, alert)
            p_event_warning = catalogue.conditional_probability(gauge_id, warning)
            p_event_severe = catalogue.conditional_probability(gauge_id, severe)

            # Annualise: P(at least one in a year) = 1 - exp(-lambda * p).
            prob_alert = annual_exceedance_probability(lambda_per_year, p_event_alert)
            prob_warning = annual_exceedance_probability(lambda_per_year, p_event_warning)
            prob_severe = annual_exceedance_probability(lambda_per_year, p_event_severe)

            # The pre-frequency metric, kept alongside for parallel-run
            # comparison until the switchover is signed off.
            legacy_severe = self.gev_fitter.exceedance_probability(
                severe, shape, loc, scale)

            # Raw catalogue count, for the basis leg. Not weighted and not
            # annualised: it is compared against a property's raw flood-event
            # count over the same catalogue, so it has to be on that basis.
            severe_event_count = int(
                catalogue.flood_flags(gauge_id, severe).sum())

            # Per-event loss vector for this gauge. A gauge carries no asset
            # value, so the loss quantum is the depth-damage ratio at unit
            # exposure, keyed off depth above the severe trigger — a severity
            # index in [0, 1], not a currency amount. The property and
            # commercial legs multiply their own value into the same shape.
            gauge_losses = peak_level_losses(
                catalogue, gauge_id,
                lambda level: scalar_depth_damage(level - severe))
            metrics = loss_metrics(
                catalogue, gauge_losses, lambda_per_year,
                freq_config.simulation, gauge_id, self.catchment,
                ProvenanceClass.GENERATOR_DERIVED.value, loss_return_periods,
                config_hash=loss_config_hash, draws=loss_draws)
            loss_block = compact_loss_block(metrics, "unit_exposure_damage_ratio")

            # Term structures. The per-year hazards compound the arrival-rate
            # process over the tenor (Stage 6h); under the default stationary
            # process every year is identical and this is the prior behaviour.
            term_structure_alert = compute_term_structure(
                annual_hazard_by_year(rate_process, p_event_alert, 5))
            term_structure_warning = compute_term_structure(
                annual_hazard_by_year(rate_process, p_event_warning, 5))
            term_structure_severe = compute_term_structure(
                annual_hazard_by_year(rate_process, p_event_severe, 5))

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
                simulation_timestamp=datetime.now().isoformat(),
                num_events_simulated=catalogue.n_events,
                lambda_per_year=lambda_per_year,
                event_exceedance_prob_alert=p_event_alert,
                event_exceedance_prob_warning=p_event_warning,
                event_exceedance_prob_severe=p_event_severe,
                implied_return_period_severe_years=(
                    catalogue.implied_return_period_years(
                        gauge_id, severe, lambda_per_year)),
                legacy_annual_flood_prob_severe=legacy_severe,
                severe_event_count=severe_event_count,
                loss_metrics=loss_block,
            )

            hazard_curves[gauge_id] = hazard_curve

            if (i + 1) % 10 == 0:
                self.log(f"Processed {i + 1}/{len(self.gauges)} gauges")

        self.log(f"Built hazard curves for {len(hazard_curves)} gauges")
        return hazard_curves, responses
