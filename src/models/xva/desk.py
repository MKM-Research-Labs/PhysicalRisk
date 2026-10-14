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

"""The XVA model on the Trading Desk's book (WP4).

Turns the desk's enriched trades (``DeltaEngine.enrich_trade``), its market
state and the counterparty CDM into netting sets, runs the Monte Carlo engine
on each, and returns per-trade and per-netting-set figures, a valuation KPI
and an audit record. Deliberately outside ``enrich_trade``: an XVA run costs
about a second per netting set, and ``enrich_trade`` runs on every blotter
request, curve edit and stress run. The desk calls this on demand, at EOD,
and for a quote, and the blotter reads the stored result.

Hazard: one curve per gauge, because trades on one gauge share one trigger.
``term_structure_curve`` bootstraps it from the desk's tenor-bucket hazards so
that each standard tenor reprices at the front office's fair spread (plan §16).
The front office still values each trade flat at its own bucket over a
whole-year remaining tenor; the KPI reports what gap remains.
"""

from dataclasses import replace
from datetime import date, datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple, Union

from config.xva import (
    DEFAULT_PARTY_CAPITAL,
    PARTY_TYPE_CAPITAL,
    STATUS,
    VALUATION_KPI_TOLERANCE_BPS,
    XvaConfig,
)

from . import monte_carlo
from .capital import CounterpartyProfile
from .counterparty_credit import credit_of, hazard_curve
from .counterparty_credit import summary as credit_summary
from .curves import HazardCurve, ZeroCurve, bootstrap_cds, cds_par_spread
from .inputs import PrsTrade
from .netting import NettingSet, close_out_netting_from_cdm, csa_from_cdm
from .valuation import legs, value

UNASSIGNED = "UNASSIGNED"
# (gauge, trigger) -> an annual trigger probability (flat) or a hazard curve.
HazardLookup = Callable[[str, str], Union[float, HazardCurve]]


def zero_curve(market_state: Dict) -> ZeroCurve:
    """The desk's yield curve (D-13), with its flat rate as the fallback."""
    return ZeroCurve(market_state.get("yield_curve") or None,
                     market_state.get("risk_free_rate", 0.03))


def remaining_quarters(maturity: str, today: date) -> float:
    days = (date.fromisoformat(str(maturity)[:10]) - today).days
    return max(1, round(days / 365.25 * 4)) / 4.0


def term_structure_curve(tenor_probs: Dict[int, float], zero: ZeroCurve) -> Tuple[HazardCurve, bool]:
    """One gauge's hazard curve from its tenor-bucket annual probabilities.

    The front office prices a T-year PRS flat at that bucket's probability.
    Bootstrapping a piecewise-constant hazard to those fair spreads (pricer
    convention, recovery 0, unfloored) gives a single curve on which every
    standard tenor reprices exactly. Returns ``(curve, fell_back)``: a curve
    that cannot be bootstrapped (a forward hazard would be negative) falls back
    to flat at the longest bucket, and says so.
    """
    tenors = sorted(t for t, p in tenor_probs.items() if p > 0)
    if not tenors:
        return HazardCurve.flat(0.0), False
    probs = [tenor_probs[t] for t in tenors]
    if len(set(probs)) == 1:
        return HazardCurve.from_annual_probability(probs[0]), False
    spreads = [cds_par_spread(HazardCurve.from_annual_probability(p), zero, t, 0.0)
               for t, p in zip(tenors, probs)]
    try:
        return bootstrap_cds(tenors, spreads, 0.0, zero), False
    except ValueError:
        return HazardCurve.from_annual_probability(probs[-1]), True


def trade_from_enriched(e: Dict, hazard_for: HazardLookup, today: date) -> Optional[PrsTrade]:
    """A ``PrsTrade`` from an enriched blotter row; None if closed or matured."""
    if not e.get("notional") or not e.get("maturity"):
        return None
    if date.fromisoformat(str(e["maturity"])[:10]) <= today:
        return None
    h = hazard_for(e["gauge_id"], e.get("trigger", "severe"))
    trigger = h if isinstance(h, HazardCurve) else HazardCurve.from_annual_probability(h)
    return PrsTrade(float(e["notional"]), float(e["trade_spread_bps"]) / 1e4,
                    remaining_quarters(e["maturity"], today), bool(e["is_payer"]),
                    trigger, e["gauge_id"])


def counterparty_terms(record: Optional[Dict], zero: ZeroCurve, cfg: XvaConfig):
    """(hazard curve, capital profile, CSA, close-out netting, netting set id, rating).

    The hazard curve is bootstrapped from the record's own CDS spreads, or from
    the rating proxy when it has none (``counterparty_credit``).
    """
    root = (record or {}).get("CounterpartySet", {})
    platform = root.get("_platform", {})
    view = credit_of(record, cfg)
    rating = view.rating
    exposure_class, sector = PARTY_TYPE_CAPITAL.get(platform.get("PartyType"), DEFAULT_PARTY_CAPITAL)
    sets = (root.get("CreditSupport") or {}).get("NettingSets") or [None]
    ns = sets[0]
    party = root.get("Party", {}).get("PartyID", UNASSIGNED)
    ns_id = (ns or {}).get("NettingSetID") or f"NS-{party}"
    hazard = hazard_curve(view, zero)
    return (hazard, CounterpartyProfile(rating, exposure_class, sector),
            csa_from_cdm(ns), close_out_netting_from_cdm(ns), ns_id, rating)


def _kpi(e: Dict, trade: PrsTrade, zero: ZeroCurve) -> Dict:
    engine_v = value(trade, zero, 0.0)
    gap_bps = abs(engine_v - float(e.get("mtm") or 0.0)) / trade.notional * 1e4
    return {"fo_mtm": float(e.get("mtm") or 0.0), "engine_value": engine_v,
            "gap_bps_notional": gap_bps, "breach": gap_bps > VALUATION_KPI_TOLERANCE_BPS}


def _netting_set_result(ns_id, cpty, rating, csa, out, trades, rows):
    booked, kva = out["booked"], out["kva"]
    alloc = out["allocation"]
    total_notional = sum(t.notional for t in trades)
    per_trade = []
    for i, (t, e) in enumerate(zip(trades, rows)):
        share = t.notional / total_notional
        per_trade.append({"swap_id": e["swap_id"], "netting_set_id": ns_id,
                          "cva": alloc["contributions"][i], "fva": alloc["fva_contributions"][i],
                          "kva": kva["total"]["value"] * share})
        per_trade[-1]["xva"] = per_trade[-1]["cva"] + per_trade[-1]["fva"]
    return {
        "netting_set_id": ns_id, "counterparty_id": cpty, "rating": rating,
        "csa": {"variation_margin": csa.variation_margin, "threshold": csa.threshold,
                "im_received": csa.im_received},
        "n_trades": len(trades), "booked": booked, "dva_disclosed": out["dva_disclosed"],
        "kva": {k: kva[k] for k in ("total", "ccr", "cva", "rrao", "today")},
        "allocation_residual": {"cva": alloc["residual"], "fva": alloc["fva_residual"]},
    }, per_trade


def _netting_sets(enriched, counterparties, hazard_for, zero, cfg, today):
    groups: Dict[str, Dict] = {}
    for e in enriched:
        trade = trade_from_enriched(e, hazard_for, today)
        if trade is None:
            continue
        cpty = e.get("counterparty_id") or UNASSIGNED
        g = groups.setdefault(cpty, {"trades": [], "rows": []})
        g["trades"].append(trade)
        g["rows"].append(e)
    for cpty, g in groups.items():
        hazard, profile, csa, netting, ns_id, rating = counterparty_terms(
            counterparties.get(cpty), zero, cfg)
        yield cpty, g, NettingSet(g["trades"], hazard, csa, netting), profile, ns_id, rating


def run_book(enriched: List[Dict], counterparties: Dict[str, Dict], market_state: Dict,
             hazard_for: HazardLookup, cfg: Optional[XvaConfig] = None,
             today: Optional[date] = None) -> Dict:
    """XVA, KVA and the valuation KPI for every open gauge PRS on the desk."""
    cfg, today = cfg or XvaConfig(), today or date.today()
    zero = zero_curve(market_state)
    sets, trades = [], []
    for cpty, g, nset, profile, ns_id, rating in _netting_sets(
            enriched, counterparties, hazard_for, zero, cfg, today):
        out = monte_carlo.run(nset, zero, cfg, counterparty=profile)
        summary, per_trade = _netting_set_result(ns_id, cpty, rating, nset.csa, out,
                                                 g["trades"], g["rows"])
        summary["credit"] = credit_summary(credit_of(counterparties.get(cpty), cfg))
        for row, t, e in zip(per_trade, g["trades"], g["rows"]):
            row["kpi"] = _kpi(e, t, zero)
        sets.append(summary)
        trades += per_trade
    return {
        "as_of": today.isoformat(),
        "netting_sets": sets,
        "trades": trades,
        "summary": {
            "xva_total": sum(s["booked"]["total"]["value"] for s in sets),
            "kva_total": sum(s["kva"]["total"]["value"] for s in sets),
            "kva_included_in_booked": False,
            "n_netting_sets": len(sets), "n_trades": len(trades),
            "kpi_breaches": sum(t["kpi"]["breach"] for t in trades),
        },
        "audit": {"run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "model_id": "MKM-XV-001", "engine": "monte_carlo", "status": STATUS,
                  "config_sha256": cfg.fingerprint(), "seed": cfg.seed, "n_paths": cfg.n_paths},
    }


def quote(new_trade: Dict, enriched: List[Dict], counterparties: Dict[str, Dict],
          market_state: Dict, hazard_for: HazardLookup, cfg: Optional[XvaConfig] = None,
          today: Optional[date] = None) -> Dict:
    """Incremental XVA and KVA of a proposed trade against its netting set.

    Both runs share the seed, so the difference is taken on common random
    numbers (Green §3: incremental CVA by one simulation over old and new).
    ``new_trade`` is an enriched-style row: gauge_id, trigger, notional,
    trade_spread_bps, is_payer, maturity, counterparty_id.
    """
    cfg, today = cfg or XvaConfig(), today or date.today()
    zero = zero_curve(market_state)
    cpty = new_trade.get("counterparty_id") or UNASSIGNED
    trade = trade_from_enriched(new_trade, hazard_for, today)
    if trade is None:
        raise ValueError("the proposed trade has no notional or has already matured")
    existing = [t for t in (trade_from_enriched(e, hazard_for, today) for e in enriched
                            if (e.get("counterparty_id") or UNASSIGNED) == cpty) if t is not None]
    hazard, profile, csa, netting, ns_id, rating = counterparty_terms(
        counterparties.get(cpty), zero, cfg)

    def totals(trades):
        if not trades:
            return {"xva": 0.0, "kva": 0.0}
        out = monte_carlo.run(NettingSet(trades, hazard, csa, netting), zero, cfg,
                              counterparty=profile)
        return {"xva": out["booked"]["total"]["value"], "kva": out["kva"]["total"]["value"]}

    before, after = totals(existing), totals(existing + [trade])
    d_xva, d_kva = after["xva"] - before["xva"], after["kva"] - before["kva"]
    annuity = legs(trade, zero, 0.0)["annuity"]
    to_bps = 1e4 / (trade.notional * annuity * trade.direction)
    return {
        "netting_set_id": ns_id, "counterparty_rating": rating,
        "incremental_xva": d_xva, "incremental_kva": d_kva,
        "xva_spread_bps": d_xva * to_bps,
        "kva_spread_bps": d_kva * to_bps,
        "note": "Spread adjustments are first order, U / (direction N A). KVA is shown, "
                "not booked, until the regulatory paper is answered (D-16).",
        "audit": {"config_sha256": cfg.fingerprint(), "seed": cfg.seed, "n_paths": cfg.n_paths,
                  "status": STATUS},
    }


def with_paths(cfg: XvaConfig, n_paths: Optional[int]) -> XvaConfig:
    return replace(cfg, n_paths=int(n_paths)) if n_paths else cfg
