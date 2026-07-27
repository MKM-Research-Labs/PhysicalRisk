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

"""What-if sensitivity for the deferred rate reprices (MKM-EF-001, Stage 6j).

Stages 6h and 6i left two reprices switched off behind empty registries — a
non-stationary climate trend and decoupled wind — because turning either on
moves a priced quantity and so is a model-risk decision resting on real data.
This module is the evidence that decision needs: it quantifies what a trend
*would* do, without changing anything priced.

It is pure and data-free. It composes the rate-process building blocks already
built (``rate_process_for``, ``term_exceedance_probability``) over a grid of
candidate growths and reports each one's multi-year exceedance probability
against the stationary baseline. Nothing here is wired into pricing; it is a
diagnostic a validation report or the MRC calls, not a production path.
"""

from typing import Dict, Sequence

from .annualise import annual_exceedance_probability
from .rate_process import ConstantRate, rate_process_for, term_exceedance_probability


def trend_sensitivity(
    lambda_per_year: float,
    p_event: float,
    tenor_years: int,
    growth_grid: Sequence[float],
) -> Dict:
    """Quantify what a climate trend would do to a multi-year exceedance.

    For each growth in *growth_grid*, the probability of at least one exceedance
    over the tenor, compared against the stationary (zero-growth) baseline that
    is priced today. The delta is exactly the reprice that seeding that growth
    into ``CATCHMENT_ANNUAL_GROWTH`` would cause.

    Args:
        lambda_per_year: the base (tenor-start) arrival rate.
        p_event: the per-event conditional exceedance probability.
        tenor_years: the contract tenor.
        growth_grid: candidate annual growths to evaluate; ``0.0`` is the
            stationary baseline whether or not it appears in the grid.

    Returns:
        A dict with the inputs, the stationary baseline probability, and a row
        per growth carrying its exceedance probability, its absolute delta from
        the baseline, and its relative change.
    """
    baseline = term_exceedance_probability(
        ConstantRate(lambda_per_year), p_event, tenor_years)

    rows = []
    for growth in growth_grid:
        process = rate_process_for(lambda_per_year, growth)
        probability = term_exceedance_probability(process, p_event, tenor_years)
        rows.append({
            "annual_growth": growth,
            "term_exceedance_probability": probability,
            "delta_vs_stationary": probability - baseline,
            "relative_change": (probability / baseline - 1.0) if baseline > 0 else 0.0,
            "final_year_annual_probability": annual_exceedance_probability(
                process.rate_at(max(0, tenor_years - 1)), p_event),
        })

    return {
        "lambda_per_year": lambda_per_year,
        "p_event": p_event,
        "tenor_years": tenor_years,
        "stationary_probability": baseline,
        "rows": rows,
    }
