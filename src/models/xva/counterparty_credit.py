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

"""A counterparty's credit curve, read from its CDM record (MKM-XV-001).

One place both the XVA desk and the PRS pricer read a counterparty's default
risk from, so the spread a trader sees is the spread the model uses. The
record's ``Credit`` block (par CDS spreads by tenor, recovery, source) is
used when present. Without it the rating proxy (``config.xva.RATING_CDS_SPREADS``)
stands in, flat, and the view says so: ``derived`` is True and the source
is RatingProxy.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from config.xva import RATING_CDS_SPREADS, UNKNOWN_COUNTERPARTY_RATING, XvaConfig

from .curves import HazardCurve, ZeroCurve, bootstrap_cds

PROXY_TENOR_YEARS = 5.0


@dataclass(frozen=True)
class CreditView:
    points: Tuple[Tuple[float, float], ...]   # (tenor years, spread bps), increasing
    recovery: float
    source: str                              # "Market" or "RatingProxy"
    derived: bool                            # True: no Credit block, proxied from the rating
    rating: str
    as_of: Optional[str] = None

    def spread_bps(self, tenor: float = PROXY_TENOR_YEARS) -> float:
        """Spread at a tenor, linear between quotes and flat outside them."""
        t, s = zip(*self.points)
        return float(np.interp(tenor, t, s))


def credit_of(record: Optional[Dict], cfg: Optional[XvaConfig] = None) -> CreditView:
    cfg = cfg or XvaConfig()
    root = (record or {}).get("CounterpartySet", {})
    rating = root.get("_platform", {}).get("CreditRating")
    if rating not in RATING_CDS_SPREADS:
        rating = UNKNOWN_COUNTERPARTY_RATING
    credit = root.get("Credit")
    if credit and credit.get("CdsSpreads"):
        points = tuple((float(p["TenorYears"]), float(p["SpreadBps"]))
                       for p in credit["CdsSpreads"])
        return CreditView(points, float(credit.get("Recovery", cfg.counterparty_recovery)),
                          credit.get("Source", "Market"), False, rating, credit.get("AsOf"))
    proxy = RATING_CDS_SPREADS[rating] * 1e4
    return CreditView(((PROXY_TENOR_YEARS, proxy),), cfg.counterparty_recovery,
                      "RatingProxy", True, rating)


def hazard_curve(view: CreditView, zero: ZeroCurve) -> HazardCurve:
    """Bootstrap the hazard curve that reprices every quoted spread.

    A curve that cannot be bootstrapped (a negative forward hazard) falls back
    to flat at the longest quote rather than failing the run.
    """
    tenors = [t for t, _ in view.points]
    spreads = [s / 1e4 for _, s in view.points]
    try:
        return bootstrap_cds(tenors, spreads, view.recovery, zero)
    except ValueError:
        return bootstrap_cds([tenors[-1]], [spreads[-1]], view.recovery, zero)


def summary(view: CreditView) -> Dict:
    """What a screen shows: the 5y spread, recovery, source and whether derived."""
    return {"cds_5y_bps": round(view.spread_bps(), 1), "recovery": view.recovery,
            "credit_source": view.source, "credit_derived": view.derived,
            "credit_as_of": view.as_of}
