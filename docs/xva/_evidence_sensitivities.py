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

"""The sensitivity runs of the MKM-XV-001 validation evidence (plan §6).

Split from ``validation_evidence.py`` to keep both under the 300-line rule.
Each case changes one input from the base trade (GBP 10m, 5y, 2% trigger, at
the fair spread, BBB-proxy counterparty) and records booked XVA and KVA for the
bank buying and selling protection.
"""

from dataclasses import replace

from models.xva import HazardCurve, build_market, monte_carlo
from models.xva.netting import NettingSet

SENSITIVITIES = [
    ("counterparty hazard x0.5", lambda c: c, {"cp_scale": 0.5}),
    ("counterparty hazard x2", lambda c: c, {"cp_scale": 2.0}),
    ("R_C 20%", lambda c: replace(c, counterparty_recovery=0.2), {}),
    ("R_C 60%", lambda c: replace(c, counterparty_recovery=0.6), {}),
    ("s_F 0bp", lambda c: replace(c, own_funding_spread=0.0), {}),
    ("s_F 150bp", lambda c: replace(c, own_funding_spread=0.015), {}),
    ("sigma 0", lambda c: replace(c, hazard_vol=0.0), {}),
    ("sigma 0.6", lambda c: replace(c, hazard_vol=0.6), {}),
    ("kappa 0.25", lambda c: replace(c, hazard_mean_reversion=0.25), {}),
    ("kappa 1.0", lambda c: replace(c, hazard_mean_reversion=1.0), {}),
    ("WWR beta 1", lambda c: replace(c, wwr_beta=1.0), {}),
    ("settlement 0d", lambda c: replace(c, settlement_days=0), {}),
    ("settlement 20d", lambda c: replace(c, settlement_days=20), {}),
    ("credit-analogy SA-CCR", lambda c: replace(c, saccr_asset_class="credit_single_name"), {}),
    ("RRAO on", lambda c: replace(c, rrao=True), {}),
    ("gamma_K 8%", lambda c: replace(c, cost_of_capital=0.08), {}),
    ("gamma_K 15%", lambda c: replace(c, cost_of_capital=0.15), {}),
    ("phi = 1", lambda c: replace(c, capital_funding_fraction=1.0), {}),
]


def sensitivities(cfg, zero, trade, profile):
    base_cp = build_market(zero, cfg, rating="BBB").counterparty
    rows = []
    for buyer in (True, False):
        def run(c, cp_scale=1.0):
            cp = HazardCurve(base_cp.knots, base_cp.rates * cp_scale)
            out = monte_carlo.run(NettingSet([trade(buyer)], cp), zero, c, counterparty=profile)
            return out["booked"]["total"]["value"], out["kva"]["total"]["value"]
        base_xva, base_kva = run(cfg)
        rows.append({"bank": "buys" if buyer else "sells", "case": "base",
                     "xva": base_xva, "kva": base_kva})
        for label, change, kw in SENSITIVITIES:
            x, k = run(change(cfg), **kw)
            rows.append({"bank": "buys" if buyer else "sells", "case": label, "xva": x, "kva": k})
    return {"rows": rows}
