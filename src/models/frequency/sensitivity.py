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

import math

from .annualise import annual_exceedance_probability
from .rate_process import ConstantRate, rate_process_for, term_exceedance_probability


def rate_sensitivity(
    lambda_per_year: float,
    p_event: float,
    factors: Sequence[float],
) -> Dict:
    """Quantify how a PRS spread responds to the arrival rate λ.

    λ is a linear multiplier on the annual exceedance, so this is the model's
    single most material sensitivity: the spread `1 - exp(-λ·p)` moves with λ,
    and because `λ·p` is small at realistic conditionals the response is close to
    proportional — an X% error in λ is roughly an X% error in the spread.

    Reports, for each multiplicative *factor* on λ, the repriced annual
    probability and spread against the base, plus the analytic derivative
    `∂P/∂λ = p·exp(-λ·p)` so the response is stated in closed form, not only
    sampled.

    Args:
        lambda_per_year: the base arrival rate.
        p_event: the per-event conditional exceedance probability.
        factors: multiplicative shocks to λ (e.g. 0.8, 1.0, 1.2).

    Returns:
        A dict with the base point, the closed-form derivative, and a row per
        factor carrying the shocked rate, probability, spread (bps) and relative
        change.
    """
    base = annual_exceedance_probability(lambda_per_year, p_event)
    derivative = max(0.0, p_event) * math.exp(
        -max(0.0, lambda_per_year) * max(0.0, p_event))

    rows = []
    for factor in factors:
        shocked = lambda_per_year * factor
        probability = annual_exceedance_probability(shocked, p_event)
        rows.append({
            "factor": factor,
            "lambda_per_year": shocked,
            "annual_probability": probability,
            "spread_bps": probability * 10000.0,
            "relative_change": (probability / base - 1.0) if base > 0 else 0.0,
        })

    return {
        "lambda_per_year": lambda_per_year,
        "p_event": p_event,
        "base_probability": base,
        "base_spread_bps": base * 10000.0,
        "d_prob_d_lambda": derivative,
        "rows": rows,
    }


def distributional_sensitivity(
    mean_count: float,
    alphas: Sequence[float],
) -> Dict:
    """Quantify how the spread responds to the count *distribution*, not its mean.

    Holds the mean annual flood count fixed and swaps the Poisson for a Negative
    Binomial of increasing over-dispersion `alpha`. `P(at least one) = 1 -
    exp(-mean)` under Poisson; `1 - (r/(r+mean))^r` with `r = 1/alpha` under
    NegBin. This isolates the effect of the *distributional form* — the thing the
    Stage 2 dispersion test guards — from the effect of the rate.

    At the low mean counts realistic here the occurrence probability is governed
    by the mean, so the form is a second-order effect; the table makes that
    explicit rather than assumed.

    Args:
        mean_count: the mean annual flood count, `λ·p`.
        alphas: over-dispersion parameters; ``0`` (or negative) is the Poisson
            limit, larger values are more clustered.

    Returns:
        A dict with the Poisson baseline and a row per alpha carrying the
        family, the exceedance probability, the spread (bps), and its change
        relative to the Poisson.
    """
    mean = max(0.0, mean_count)
    poisson = 1.0 - math.exp(-mean)

    rows = []
    for alpha in alphas:
        if alpha <= 0.0:
            probability, family = poisson, "poisson"
        else:
            r = 1.0 / alpha
            probability = 1.0 - (r / (r + mean)) ** r if mean > 0 else 0.0
            family = "negbin"
        rows.append({
            "alpha": alpha,
            "family": family,
            "prob_at_least_one": probability,
            "spread_bps": probability * 10000.0,
            "relative_to_poisson": (probability / poisson - 1.0) if poisson > 0 else 0.0,
        })

    return {
        "mean_count": mean,
        "poisson_probability": poisson,
        "poisson_spread_bps": poisson * 10000.0,
        "rows": rows,
    }


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
