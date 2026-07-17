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
QuantLib credit curve pricing — converts hazard points to credit curves
for CDS pricing of Physical Risk Swaps.
"""

import numpy as np
import QuantLib as ql


def hazard_points_to_credit_curve(hazard_points, years, evaluation_date, day_count=None):
    """
    Convert hazard points (conditional default probabilities) to QuantLib credit curve.

    Parameters:
        hazard_points: list of conditional default probabilities [h1, h2, h3, h4, h5]
        years: list of years corresponding to hazard points [1, 2, 3, 4, 5]
        evaluation_date: QuantLib Date object for evaluation
        day_count: QuantLib DayCounter (defaults to Actual365Fixed)

    Returns:
        QuantLib credit curve object
    """
    if day_count is None:
        day_count = ql.Actual365Fixed()

    # Convert hazard points to survival probabilities
    survival_probs = []
    current_survival = 1.0

    for hazard in hazard_points:
        current_survival = current_survival * (1 - hazard)
        survival_probs.append(current_survival)

    # Create dates for the curve
    dates = [evaluation_date]
    for year in years:
        dates.append(evaluation_date + ql.Period(year, ql.Years))

    # Survival probabilities including initial 1.0
    curve_survival_probs = [1.0] + survival_probs

    # Create QuantLib SurvivalProbabilityCurve
    credit_curve = ql.SurvivalProbabilityCurve(
        dates,
        curve_survival_probs,
        day_count,
        ql.TARGET()
    )

    credit_curve.enableExtrapolation()
    return credit_curve


def create_cds_pricing_engines(credit_curve, recovery_rate, risk_free_curve):
    """
    Create different CDS pricing engines using the credit curve.

    Returns:
        Dictionary of pricing engines
    """
    credit_handle = ql.DefaultProbabilityTermStructureHandle(credit_curve)
    risk_free_handle = ql.YieldTermStructureHandle(risk_free_curve)

    engines = {
        'ISDA': ql.IsdaCdsEngine(credit_handle, recovery_rate, risk_free_handle),
        'Integral': ql.IntegralCdsEngine(ql.Period('1d'), credit_handle, recovery_rate, risk_free_handle),
        'Midpoint': ql.MidPointCdsEngine(credit_handle, recovery_rate, risk_free_handle)
    }

    return engines


def create_hazard_rate_curve_approach(hazard_points, years, evaluation_date):
    """
    Alternative approach using HazardRateCurve directly.

    Converts conditional default probabilities to instantaneous hazard rates
    under piecewise constant assumption.
    """
    survival_probs = []
    current_survival = 1.0

    for hazard in hazard_points:
        current_survival = current_survival * (1 - hazard)
        survival_probs.append(current_survival)

    # Calculate cumulative hazard rates: H(t) = -ln(S(t))
    cumulative_hazards = [-np.log(sp) for sp in survival_probs]

    # Calculate instantaneous hazard rates for piecewise constant assumption
    instantaneous_hazards = []
    prev_cum_hazard = 0
    for cum_hazard in cumulative_hazards:
        inst_hazard = cum_hazard - prev_cum_hazard
        instantaneous_hazards.append(inst_hazard)
        prev_cum_hazard = cum_hazard

    dates = [evaluation_date + ql.Period(year, ql.Years) for year in years]

    hazard_curve = ql.HazardRateCurve(dates, instantaneous_hazards, ql.Actual365Fixed())
    hazard_curve.enableExtrapolation()

    return hazard_curve
