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

"""Risk-free value of a PRS at a future date, on the pricer's conventions.

V(t) is the value to the bank at t given no trigger by t. It is the pricer's
protection-minus-premium leg restricted to the periods still running, with
survival and discounting conditioned on t, so at t = 0 it reproduces
``compute_prs_spread`` / ``compute_mark_to_market`` exactly. Inside a period
the protection still to run is discounted at the midpoint of what remains,
which equals the pricer's mid-period on a period boundary and keeps V
continuous between payment dates. V jumps at each premium date, by the
premium just paid: the saw-tooth Green warns the time grid must resolve.

After a trigger at u the bank holds a claim (buyer) or obligation (seller) of
the notional, settled at u + settlement lag. The pricer itself discounts the
payout at mid-period and ignores the lag; the lag enters only the exposure.
"""

from typing import Dict

import numpy as np

from .curves import ZeroCurve
from .inputs import PrsTrade

QUARTER = 0.25


def premium_dates(trade: PrsTrade) -> np.ndarray:
    n = int(round(trade.tenor_years / QUARTER))
    return QUARTER * np.arange(1, n + 1)


def legs(trade: PrsTrade, zero: ZeroCurve, t: float) -> Dict[str, float]:
    """Per-unit-notional protection leg and risky annuity at t, given no trigger."""
    dates = premium_dates(trade)
    live = dates > t
    if not np.any(live):
        return {"protection": 0.0, "annuity": 0.0}
    ends = dates[live]
    starts = np.maximum(ends - QUARTER, t)
    s_t = float(trade.trigger.survival(t))
    df_t = float(zero.df(t))
    surv_end = trade.trigger.survival(ends) / s_t
    surv_start = trade.trigger.survival(starts) / s_t
    mids = 0.5 * (starts + ends)
    protection = float(np.sum((surv_start - surv_end) * zero.df(mids))) / df_t
    annuity = float(np.sum(QUARTER * surv_end * zero.df(ends))) / df_t
    return {"protection": protection, "annuity": annuity}


def value(trade: PrsTrade, zero: ZeroCurve, t: float) -> float:
    """V(t) to the bank, given no trigger by t; zero at and after maturity."""
    leg = legs(trade, zero, t)
    return trade.direction * trade.notional * (leg["protection"] - trade.spread * leg["annuity"])


def fair_spread(trade: PrsTrade, zero: ZeroCurve) -> float:
    """Unfloored par spread at t = 0 (the pricer floors its quote at 2bp)."""
    leg = legs(trade, zero, 0.0)
    return leg["protection"] / leg["annuity"]


def pending_payout(trade: PrsTrade, zero: ZeroCurve, u, t, lag: float):
    """Value at t of the payout triggered at u <= t, settling at u + lag."""
    return trade.direction * trade.notional * zero.df(np.asarray(u) + lag) / zero.df(t)
