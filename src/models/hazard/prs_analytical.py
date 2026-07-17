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
Analytical PRS (Physical Risk Swap) pricing without QuantLib dependency.

Implements quarterly CDS-equivalent pricing per PRS Property Pricing Spec Section 6.1.

Functions:
    compute_prs_spread: Fair spread from hazard rate, tenor, recovery
"""

import math
from typing import Dict, List, Optional

from config.models import (
    MIN_PRS_SPREAD_BPS,
    RECOVERY_RATES,
)


def interpolate_yield_rate(yield_curve: dict, t: float,
                           fallback: float = 0.04) -> float:
    """
    Interpolate yield rate at time t (years) from curve points.

    Args:
        yield_curve: Dict mapping tenor (str keys like '1','2') to rate
        t: Time in years (can be fractional, e.g. 0.25)
        fallback: Rate to use if curve is empty

    Returns:
        Interpolated continuous yield rate
    """
    if not yield_curve:
        return fallback
    keys = sorted(int(k) for k in yield_curve.keys())
    if not keys:
        return fallback
    if t <= keys[0]:
        return yield_curve[str(keys[0])]
    if t >= keys[-1]:
        return yield_curve[str(keys[-1])]
    for i in range(len(keys) - 1):
        if keys[i] <= t <= keys[i + 1]:
            t0, t1 = keys[i], keys[i + 1]
            r0, r1 = yield_curve[str(t0)], yield_curve[str(t1)]
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
    return yield_curve[str(keys[-1])]


def compute_prs_spread(
    annual_hazard_rate: float,
    tenor: int,
    recovery: float = 0.0,
    risk_free_rate: float = 0.03,
    min_spread_bps: float = MIN_PRS_SPREAD_BPS,
    yield_curve: Optional[dict] = None,
) -> float:
    """
    Compute PRS fair spread in basis points using quarterly CDS-equivalent pricing.

    Implements Spec Section 6.1:
        - Converts annual probability to continuous hazard rate (Eq. 7)
        - Computes risky annuity: sum of dt * S(t) * DF(t)
        - Computes protection leg PV: (1-R) * sum of (S(t-1) - S(t)) * DF(t)
        - Fair spread = protection_pv / annuity

    Args:
        annual_hazard_rate: Annual default/flood probability (0-1)
        tenor: Maturity in years
        recovery: Recovery rate (0-1), trigger-dependent per Spec Table 5
        risk_free_rate: Risk-free discount rate (continuous)
        min_spread_bps: Floor spread in basis points

    Returns:
        Fair spread in basis points
    """
    if annual_hazard_rate <= 0:
        return 0.0

    # Convert annual probability to continuous hazard rate (Spec Eq. 7)
    hazard_lambda = -math.log(1.0 - min(annual_hazard_rate, 0.999))

    dt = 0.25  # Quarterly periods (Spec Section 6.1)
    n_periods = tenor * 4

    # Risky annuity: sum of dt * S(t) * DF(t)
    annuity = 0.0
    for i in range(1, n_periods + 1):
        t = i * dt
        survival = math.exp(-hazard_lambda * t)
        rf = interpolate_yield_rate(yield_curve, t, risk_free_rate) if yield_curve else risk_free_rate
        discount = math.exp(-rf * t)
        annuity += dt * survival * discount

    if annuity <= 0:
        return annual_hazard_rate * 10000  # Fallback

    # Protection leg PV: (1-R) * sum of (S(t-1) - S(t)) * DF(t)
    protection_pv = 0.0
    for i in range(1, n_periods + 1):
        t = i * dt
        t_prev = (i - 1) * dt
        surv_prev = math.exp(-hazard_lambda * t_prev)
        surv_curr = math.exp(-hazard_lambda * t)
        default_prob = surv_prev - surv_curr
        t_mid = t - dt / 2
        rf = interpolate_yield_rate(yield_curve, t_mid, risk_free_rate) if yield_curve else risk_free_rate
        discount = math.exp(-rf * t_mid)
        protection_pv += (1.0 - recovery) * default_prob * discount

    fair_spread = protection_pv / annuity if annuity > 0 else 0.0
    spread_bps = fair_spread * 10000  # Convert to bps
    return max(spread_bps, min_spread_bps)
