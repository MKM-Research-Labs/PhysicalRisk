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

"""Synthetic Credit block for generated counterparties (MKM-XV-001).

Generated counterparties have no market CDS quotes, so each gets a flat curve
from its rating (``config.xva.RATING_CDS_SPREADS``), marked Source
"RatingProxy" so no screen or model mistakes it for market data. Derived from
the existing ``_platform.CreditRating``, so the generator's random draws do
not change.
"""

from datetime import date
from typing import Any, Dict

from config.xva import RATING_CDS_SPREADS, UNKNOWN_COUNTERPARTY_RATING, XvaConfig

PROXY_TENORS = (1.0, 3.0, 5.0, 7.0)


def with_credit_curve(record: Dict[str, Any]) -> Dict[str, Any]:
    """Attach a rating-proxy ``Credit`` block to a generated record and return it."""
    root = record["CounterpartySet"]
    rating = root.get("_platform", {}).get("CreditRating")
    spread = RATING_CDS_SPREADS.get(rating, RATING_CDS_SPREADS[UNKNOWN_COUNTERPARTY_RATING])
    root["Credit"] = {
        "CdsSpreads": [{"TenorYears": t, "SpreadBps": round(spread * 1e4, 1)}
                       for t in PROXY_TENORS],
        "Recovery": XvaConfig().counterparty_recovery,
        "Source": "RatingProxy",
        "AsOf": date.today().isoformat(),
    }
    return record
