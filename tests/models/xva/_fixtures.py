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

"""Ready-made trades and markets for the XVA tests.

A 5-year GBP 10m gauge PRS on a 2% annual trigger probability, priced on the
book's default yield curve or a flat 3% curve, against a flat counterparty
hazard. Every case returns the inputs the reference implementation needs too.
"""

import math
from dataclasses import replace

from config.port import DEFAULT_YIELD_CURVE
from config.xva import XvaConfig
from models.xva import HazardCurve, Market, PrsTrade, ZeroCurve

from ._reference import Ref

NOTIONAL = 10_000_000.0
TRIGGER_PROB = 0.02
LAMBDA_C = 0.02
TENOR = 5


def case(*, buyer=True, spread=0.0180, curve=None, lam_c=LAMBDA_C, lam_e=None,
         tenor=TENOR, **cfg_overrides):
    """(trade, market, cfg, reference) for one PRS."""
    cfg = replace(XvaConfig(), **cfg_overrides)
    lam_e = -math.log(1.0 - TRIGGER_PROB) if lam_e is None else lam_e
    zero = ZeroCurve(curve, 0.03)
    trade = PrsTrade(NOTIONAL, spread, tenor, buyer, HazardCurve.flat(lam_e))
    market = Market(zero, HazardCurve.flat(lam_c), HazardCurve.flat(cfg.own_hazard))
    ref = Ref(notional=NOTIONAL, spread=spread, tenor=tenor, buyer=buyer, lam_e=lam_e,
              lam_c=lam_c, lam_b=cfg.own_hazard, rec_c=cfg.counterparty_recovery,
              rec_b=cfg.own_recovery, s_f=cfg.own_funding_spread,
              lag=cfg.settlement_years, curve=curve)
    return trade, market, cfg, ref


HUMPED = DEFAULT_YIELD_CURVE
