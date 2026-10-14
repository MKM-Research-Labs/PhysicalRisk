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

"""XVA on trade commit (MKM-XV-001): rerun the new trade's netting set.

Called as the commit response is built, after the trade is saved. It merges
the netting set into the stored XVA run, so the blotter shows the new trade's
XVA at once. Gauge PRS only; a failure is logged and never blocks the commit.
"""

import logging

logger = logging.getLogger(__name__)


def _refresh_xva(cdm_record):
    """The new trade's XVA and KVA after rerunning its netting set, or None."""
    import config.xva as xva_config
    if not xva_config.XVA_ON_TRADE_COMMIT:
        return None
    try:
        from models.xva import service
        header = cdm_record["PhysicalSwap"]["Header"]
        run = service.refresh_netting_set(header.get("CounterParty"))
        row = next((t for t in run["trades"] if t["swap_id"] == header["SwapID"]), None)
        return {"xva": row["xva"], "kva": row["kva"]} if row else None
    except Exception as exc:  # noqa: BLE001 -- XVA must never block a booking
        logger.error("XVA refresh after commit failed: %s", exc, exc_info=True)
        return None
