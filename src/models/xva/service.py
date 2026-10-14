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

"""Running XVA on the desk's book, outside any one caller (MKM-XV-001).

The trading routes (on demand, at EOD), the PRS trade-commit route and the
port pipeline all run XVA through here, so the inputs are assembled one way:
the open book revalued by the delta engine, the counterparty CDM, the market
state, and each gauge's term-structure hazard curve (plan §16).

``refresh_netting_set`` reruns one counterparty's netting set and merges it into
the stored run: what a newly committed trade needs, in seconds rather than the
minute a whole book takes. With no stored run yet, the stored run holds only
that netting set and is marked partial until the next full run.
"""

from datetime import datetime, timezone
from typing import Dict, Optional

import database
from config import config
from config.xva import XvaConfig

from . import desk


def book_inputs():
    """(enriched open trades, counterparties by PartyID, market state, hazard lookup)."""
    from models.trading.delta_engine import DeltaEngine
    from models.trading.market_state import MarketStateManager
    from models.trading.open_trades import load_open_trades

    market_mgr = MarketStateManager()
    state = market_mgr.load()
    enriched = [t for t in DeltaEngine(market_mgr).revalue_all(load_open_trades(), state)
                if t.get("trade_status", "Open").lower() != "closed"]
    counterparties = {
        r.get("CounterpartySet", {}).get("Party", {}).get("PartyID"): r
        for r in database.list_counterparties(config.catchment_id)
    }
    zero = desk.zero_curve(state)
    curves: Dict = {}
    fallbacks = []

    def hazard_for(gauge_id, trigger):
        """The gauge's term-structure curve, bootstrapped once per call (§16)."""
        key = (gauge_id, trigger)
        if key not in curves:
            buckets = state.get("hazard_term_structure", {}).get(gauge_id, {}).get(trigger, {})
            if buckets:
                probs = {int(t): market_mgr.get_hazard_rate_for_tenor(state, gauge_id, trigger, int(t))
                         for t in buckets}
                curves[key], fell_back = desk.term_structure_curve(probs, zero)
                if fell_back:
                    fallbacks.append(gauge_id)
            else:
                curves[key] = market_mgr.get_gauge_rate(state, gauge_id, trigger)
        return curves[key]

    hazard_for.fallbacks = fallbacks
    return enriched, counterparties, state, hazard_for


def run_and_save(n_paths: Optional[int] = None, inputs=None) -> Dict:
    """Run XVA on the whole open book and store it as the latest run."""
    enriched, counterparties, state, hazard_for = inputs or book_inputs()
    result = desk.run_book(enriched, counterparties, state, hazard_for,
                           desk.with_paths(XvaConfig(), n_paths))
    result["audit"]["hazard_curve_fallbacks"] = sorted(set(hazard_for.fallbacks))
    result["audit"]["scope"] = "book"
    database.save_xva_run(config.catchment_id, result)
    return result


def refresh_netting_set(counterparty_id: Optional[str], n_paths: Optional[int] = None,
                        inputs=None) -> Dict:
    """Rerun one counterparty's netting set and merge it into the stored run."""
    enriched, counterparties, state, hazard_for = inputs or book_inputs()
    cpty = counterparty_id or desk.UNASSIGNED
    mine = [e for e in enriched if (e.get("counterparty_id") or desk.UNASSIGNED) == cpty]
    part = desk.run_book(mine, counterparties, state, hazard_for,
                         desk.with_paths(XvaConfig(), n_paths))
    stored = database.get_xva_run(config.catchment_id)
    if not stored:
        merged = part
        merged["audit"]["scope"] = "partial"
    else:
        merged = stored
        replaced = {s["netting_set_id"] for s in stored["netting_sets"] if s["counterparty_id"] == cpty}
        merged["netting_sets"] = ([s for s in stored["netting_sets"] if s["counterparty_id"] != cpty]
                                  + part["netting_sets"])
        merged["trades"] = ([t for t in stored["trades"] if t["netting_set_id"] not in replaced]
                            + part["trades"])
        merged["summary"] = _summary(merged)
        merged["audit"]["refreshed"] = {
            "counterparty_id": cpty,
            "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    database.save_xva_run(config.catchment_id, merged)
    return merged


def _summary(run: Dict) -> Dict:
    sets, trades = run["netting_sets"], run["trades"]
    return {
        "xva_total": sum(s["booked"]["total"]["value"] for s in sets),
        "kva_total": sum(s["kva"]["total"]["value"] for s in sets),
        "kva_included_in_booked": False,
        "n_netting_sets": len(sets), "n_trades": len(trades),
        "kpi_breaches": sum(t["kpi"]["breach"] for t in trades),
    }
