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

"""``build_hazard_curves`` — the main hazard-curve build entry point."""

import logging
from typing import Dict

import numpy as np

import database
from ..builder import HazardCurveBuilder
from models.frequency.events import count_events

from ._load import load_gauges, load_storms_from_sequences
from ._save import save_gauge_storm_responses, save_hazard_curves

logger = logging.getLogger(__name__)


def build_hazard_curves(
    catchment_id: str,
    distribution: str = 'gev',
    verbose: bool = True
) -> Dict:
    """
    Build hazard curves from storm sequences and gauge data.

    Reads the ``storm_sequences`` and gauge portfolio for ``catchment_id`` through
    the database seam, and persists the hazard curves + per-gauge storm responses
    the same way.

    Args:
        catchment_id: Catchment identifier
        distribution: 'gev' or 'gumbel'
        verbose: Print progress

    Returns:
        Dictionary with results
    """
    sequences_data = database.get_storm_sequences(catchment_id)
    if sequences_data is None:
        raise FileNotFoundError(
            f"Storm sequences not found for catchment {catchment_id}. "
            "Run 'python phys.py port --stressm' first."
        )

    storms = load_storms_from_sequences(sequences_data)
    # An event is the hours-clause window a sequence occupies; a storm is one
    # burst inside it. Both are reported: num_storms is what existing consumers
    # read, num_events is the unit that carries an arrival rate.
    num_events = count_events(storms)
    if verbose:
        logger.info("Loaded %d individual storms from %d events",
                    len(storms), num_events)

    gauge_portfolio = database.get_gauge_portfolio(catchment_id)
    if gauge_portfolio is None:
        raise FileNotFoundError(
            f"Gauge portfolio not found for catchment {catchment_id}. "
            "Run 'python port.py --gauges' first."
        )

    gauges = load_gauges(gauge_portfolio)
    if verbose:
        logger.info("Loaded %d gauges", len(gauges))

    builder = HazardCurveBuilder(
        gauges=gauges,
        storms=storms,
        force_gumbel=(distribution == 'gumbel'),
        verbose=verbose,
        catchment=catchment_id
    )

    hazard_curves, responses = builder.build()

    metadata = {
        'num_storms': len(storms),
        'num_events': num_events,
        'distribution': distribution
    }
    save_hazard_curves(hazard_curves, catchment_id, metadata)

    if verbose:
        logger.info("Saved hazard curves for catchment %s", catchment_id)

    # Merge gauge storm responses into the per-gauge timeseries records.
    save_gauge_storm_responses(responses, catchment_id)

    if verbose:
        total_responses = sum(len(r) for r in responses.values())
        logger.info("Saved %d gauge storm responses", total_responses)

    avg_alert = np.mean([c.annual_flood_prob_alert for c in hazard_curves.values()])
    avg_warning = np.mean([c.annual_flood_prob_warning for c in hazard_curves.values()])
    avg_severe = np.mean([c.annual_flood_prob_severe for c in hazard_curves.values()])

    if verbose:
        logger.info("Average annual flood probabilities: Alert=%.2f%%, Warning=%.2f%%, Severe=%.2f%%",
                    avg_alert * 100, avg_warning * 100, avg_severe * 100)

    return {
        'hazard_curves': hazard_curves,
        'summary': {
            'num_gauges': len(hazard_curves),
            'num_storms': len(storms),
            'num_events': num_events,
            'avg_annual_prob_alert': avg_alert,
            'avg_annual_prob_warning': avg_warning,
            'avg_annual_prob_severe': avg_severe
        }
    }
