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

"""Regulatory capital of a PRS netting set in every Monte Carlo state (WP3).

Green §13.4: SA-CCR EAD and BA-CVA are computed as a payout in each state, then
the KVA integral (13.25) is taken over the expected capital profile. The
formulas are the shared ones in ``models.capital.counterparty`` (D-07).

How a PRS enters SA-CCR is the regulatory paper's question Q2, so it is a
setting, not a choice made here:

- ``commodity_other``: hedging set "other", one commodity type per gauge,
  adjusted notional = the payout notional, delta +1 for the protection buyer
  (long the flood index), supervisory factor 18%;
- ``credit_single_name``: one entity per gauge, adjusted notional = notional x
  supervisory duration, delta -1 for the protection buyer (short credit, as
  for a CDS), supervisory factor by a reference rating.

A trade that has triggered is a pending payment, not a derivative: it enters
V and so the replacement cost, but carries no add-on. Capital held is RWA x
the bank's capital ratio, the same ratio MKM-CR-001 uses (D-06); the RRAO
(Q3) is off unless switched on.
"""

from dataclasses import dataclass
from typing import Dict

import numpy as np

from config.counterparty_capital import (
    BASEL_MINIMUM_RATIO,
    RRAO_EXOTIC_RATE,
    SACCR_COMMODITY_CORRELATION,
    SACCR_COMMODITY_SF,
    SACCR_CREDIT_SF,
    SACCR_CREDIT_SINGLE_NAME_CORRELATION,
)
from models.capital.counterparty import (
    aggregate_addon,
    ba_cva_maturity,
    ba_cva_reduced,
    ba_cva_risk_weight,
    commodity_addon,
    ead,
    letter_grade,
    maturity_factor_margined,
    maturity_factor_unmargined,
    sa_risk_weight,
    scva,
    supervisory_duration,
)

from .netting import NettingSet


@dataclass(frozen=True)
class CounterpartyProfile:
    """What capital needs to know about the counterparty."""
    rating: str
    exposure_class: str = "corporate"          # CRE20: corporate or bank
    sector: str = "financials"                 # MAR50 Table 1 (insurers are financials)


def _addon(nset: NettingSet, alive, remaining, mf, asset_class: str, reference_rating: str):
    """Aggregate SA-CCR add-on per state.

    ``alive`` is one (paths, nodes) mask per trade; ``remaining`` and ``mf`` are
    one (nodes,) row per trade, so nothing is broadcast to trades x paths x
    nodes.
    """
    by_gauge: Dict[str, np.ndarray] = {}
    for i, trade in enumerate(nset.trades):
        if asset_class == "commodity_other":
            size = trade.direction * trade.notional * mf[i]
        else:
            size = -trade.direction * trade.notional * supervisory_duration(0.0, remaining[i]) * mf[i]
        eff = np.where(alive[i], size, 0.0)
        by_gauge[trade.gauge_id] = by_gauge.get(trade.gauge_id, 0.0) + eff
    if asset_class == "commodity_other":
        return commodity_addon({"other": by_gauge}, {"other": SACCR_COMMODITY_SF["other"]},
                               SACCR_COMMODITY_CORRELATION)
    sf = SACCR_CREDIT_SF[letter_grade(reference_rating)]
    return aggregate_addon([sf * v for v in by_gauge.values()],
                           SACCR_CREDIT_SINGLE_NAME_CORRELATION)


def capital(nset: NettingSet, profile: CounterpartyProfile, *, nodes: np.ndarray,
            alive, net: np.ndarray, collateral: np.ndarray, asset_class: str,
            reference_rating: str, rrao: bool, capital_ratio: float) -> Dict[str, np.ndarray]:
    """Capital held per state, split by charge; ``alive`` is one mask per trade."""
    csa = nset.csa
    remaining = [np.maximum(t.tenor_years - nodes, 0.0) for t in nset.trades]
    addon_u = _addon(nset, alive, remaining, [maturity_factor_unmargined(r) for r in remaining],
                     asset_class, reference_rating)
    nica = csa.im_received - csa.im_posted
    if csa.variation_margin:
        mf_m = maturity_factor_margined(csa.mpor_days)
        addon_m = _addon(nset, alive, remaining, [np.full(nodes.shape, mf_m)] * len(remaining),
                         asset_class, reference_rating)
        exposure = ead(net, collateral + nica, addon_m, margined=True, threshold=csa.threshold,
                       mta=csa.minimum_transfer, nica=nica, unmargined_addon=addon_u)
    else:
        exposure = ead(net, nica, addon_u)
    any_alive = np.logical_or.reduce(alive)
    exposure = np.where(any_alive | (net != 0), exposure, 0.0)

    scale = capital_ratio / BASEL_MINIMUM_RATIO          # RWA x ratio = K_basel x scale
    k_ccr = capital_ratio * sa_risk_weight(profile.rating, profile.exposure_class) * exposure
    live_notional = sum(np.where(a, t.notional, 0.0) for a, t in zip(alive, nset.trades))
    weighted = sum(np.where(a, t.notional * r, 0.0) for a, t, r in zip(alive, nset.trades, remaining))
    m_ns = ba_cva_maturity([np.divide(weighted, live_notional, out=np.zeros_like(weighted),
                                      where=live_notional > 0)], [live_notional])
    s = scva(ba_cva_risk_weight(profile.sector, profile.rating), exposure, m_ns)
    k_cva = scale * ba_cva_reduced({"counterparty": s})
    k_rrao = scale * RRAO_EXOTIC_RATE * live_notional if rrao else np.zeros_like(exposure)
    return {"ead": exposure, "ccr": k_ccr, "cva": k_cva,
            "rrao": np.broadcast_to(np.asarray(k_rrao, float), exposure.shape)}
