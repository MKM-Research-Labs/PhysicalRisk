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

"""The Monte Carlo XVA engine (WP2): a netting set of gauge PRS trades.

Adds to the analytic engine: a stochastic hazard factor (CIR++, D-15),
correlated triggers from the event catalogue, close-out netting, variation
margin with a margin period of risk, initial margin, a wrong-way-risk stress
(D-05) and Euler allocation. Each adjustment is estimated path by path, so
every figure carries its standard error (D-08). With sigma = 0, one trade, no
collateral and beta = 0 it must reproduce the analytic engine within 3
standard errors (plan §5, WP2).
"""

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, Optional

import numpy as np

from config.xva import STATUS, XvaConfig

from . import events as ev
from .capital import CounterpartyProfile, capital
from .cir import CirFactor
from .curves import HazardCurve, ZeroCurve
from .inputs import Market
from .integrals import kernel
from .netting import NettingSet
from .paths import (alive_value, factor_paths, grid, lookup, simulation_times, trade_values,
                    triggers_for)


def _exposures(values: np.ndarray, lagged: Optional[np.ndarray], nset: NettingSet):
    """Netted exposures at the nodes; values is (trades, paths, nodes)."""
    csa = nset.csa
    if not nset.close_out_netting:
        pos = np.maximum(values, 0.0).sum(axis=0)
        neg = np.minimum(values, 0.0).sum(axis=0)
        return {"epe": pos, "ene": neg, "fca": pos, "ee": values.sum(axis=0),
                "net": values.sum(axis=0), "collateral": np.zeros_like(pos)}
    net = values.sum(axis=0)
    held = csa.variation_margin_held(lagged) if lagged is not None else np.zeros_like(net)
    uncollateralised = net - held
    return {
        "epe": np.maximum(uncollateralised - csa.im_received, 0.0),   # Green 10.31
        "ene": np.minimum(uncollateralised + csa.im_posted, 0.0),
        "fca": np.maximum(uncollateralised + csa.im_posted, 0.0),     # 10.28
        "ee": uncollateralised,                                        # funded: V - X (9.30)
        "net": net, "collateral": held,
    }


def wwr_weights(triggered_count: np.ndarray, beta: float) -> np.ndarray:
    """Normalised path weights exp(beta Z) / E[exp(beta Z)] at each node.

    Z is the number of the netting set's gauges triggered so far: the
    counterparty's own flood losses. Normalising node by node leaves each
    period's default probability unchanged (Green 7.17 admissibility).
    """
    if beta == 0.0:
        return np.ones_like(triggered_count, dtype=float)
    raw = np.exp(beta * triggered_count)
    return raw / raw.mean(axis=0, keepdims=True)


def _estimate(per_path: np.ndarray) -> Dict[str, float]:
    return {"value": float(per_path.mean()),
            "se": float(per_path.std(ddof=1) / np.sqrt(per_path.size))}


def run(nset: NettingSet, zero: ZeroCurve, cfg: Optional[XvaConfig] = None,
        model: Optional[ev.TriggerModel] = None, own: Optional[HazardCurve] = None,
        counterparty: Optional[CounterpartyProfile] = None) -> Dict:
    """XVA of a netting set; with ``counterparty`` given, also capital and KVA."""
    cfg = cfg or XvaConfig()
    model = model or ev.TriggerModel.independent()
    own = own or HazardCurve.flat(cfg.own_hazard)
    lag = cfg.settlement_years
    factor = CirFactor(cfg.hazard_mean_reversion, cfg.hazard_vol)
    triggers = triggers_for(nset, factor)

    nodes, widths = grid(nset, lag, cfg.cells_per_quarter)
    vm = nset.csa.variation_margin
    lagged_at = np.maximum(nodes - nset.csa.mpor_years, 0.0)
    times = simulation_times(nodes, lagged_at if vm else np.zeros(0), nset.horizon + lag)
    rng = np.random.default_rng(cfg.seed)
    y, clock = factor_paths(factor, times, cfg.n_paths, rng)
    paths = ev.simulate(model, triggers, times, clock, rng)

    values = np.stack([trade_values(t, triggers[t.gauge_id], zero, nodes,
                                    lookup(times, y, nodes), paths.first_trigger[t.gauge_id], lag)
                       for t in nset.trades])
    lagged = None
    if vm:
        lagged = sum(trade_values(t, triggers[t.gauge_id], zero, lagged_at,
                                  lookup(times, y, lagged_at), paths.first_trigger[t.gauge_id], lag)
                     for t in nset.trades)
    exp = _exposures(values, lagged, nset)
    hit = sum((paths.first_trigger[g][:, None] <= nodes[None, :]).astype(float)
              for g in nset.gauges)
    weights = wwr_weights(hit, cfg.wwr_beta)

    market = Market(zero, nset.counterparty, own)
    lam_c, lam_b = nset.counterparty.hazard(nodes), own.hazard(nodes)
    lgd_c, lgd_b = 1.0 - cfg.counterparty_recovery, 1.0 - cfg.own_recovery
    k = {s: kernel(s, market, cfg, nodes) * widths for s in ("one_bond", "semi_replication")}

    def term(strategy, rate, exposure):
        return -(exposure * (rate * k[strategy])).sum(axis=1)

    cva_ob = term("one_bond", lgd_c * lam_c, exp["epe"] * weights)
    per_path = {
        "one_bond": {"cva": cva_ob,
                     "fva": term("one_bond", np.full_like(nodes, cfg.own_funding_spread), exp["ee"])},
        "semi_replication": {
            "cva": term("semi_replication", lgd_c * lam_c, exp["epe"] * weights),
            "dva": term("semi_replication", lgd_b * lam_b, exp["ene"]),
            "fca": term("semi_replication", lgd_b * lam_b, exp["fca"])},
    }
    views = {}
    for view, terms in per_path.items():
        views[view] = {name: _estimate(p) for name, p in terms.items()}
        views[view]["total"] = _estimate(sum(terms.values()))

    result = {
        "views": views,
        "booked_strategy": cfg.funding_strategy,
        "booked": views[cfg.funding_strategy],
        "dva_disclosed": views["semi_replication"]["dva"],
        "allocation": _euler_cva(values, exp, weights, lgd_c * lam_c * k[cfg.funding_strategy],
                                 views[cfg.funding_strategy]["cva"]["value"]),
        "profiles": {"t": nodes.tolist(),
                     **{key: exp[key].mean(axis=0).tolist() for key in ("epe", "ene", "ee")},
                     "collateral": exp["collateral"].mean(axis=0).tolist()},
        "trigger_probability": {g: float(np.mean(paths.first_trigger[g] <= nset.horizon))
                                for g in nset.gauges},
        "audit": _audit(nset, cfg),
    }
    if counterparty is not None:
        alive = np.stack([(paths.first_trigger[t.gauge_id][:, None] > nodes[None, :])
                          & (nodes[None, :] < t.tenor_years) for t in nset.trades])
        result["kva"] = _kva(nset, cfg, counterparty, nodes, alive, exp, market,
                             k[cfg.funding_strategy], zero, triggers)
    return result


def _capital_args(cfg: XvaConfig) -> Dict:
    return {"asset_class": cfg.saccr_asset_class, "reference_rating": cfg.credit_reference_rating,
            "rrao": cfg.rrao, "capital_ratio": cfg.capital_ratio}


def _kva(nset, cfg, counterparty, nodes, alive, exp, market, weighted_kernel, zero, triggers):
    """KVA = -int (gamma_K - phi r) D E[K] ds per charge (13.25), with capital today.

    Reported beside the booked XVA, not inside it, until the regulatory paper
    is answered (D-16).
    """
    held = capital(nset, counterparty, nodes=nodes, alive=alive, net=exp["net"],
                   collateral=exp["collateral"], **_capital_args(cfg))
    rate = cfg.cost_of_capital - cfg.capital_funding_fraction * zero.forward_rate(nodes)
    per_path = {c: -(held[c] * (rate * weighted_kernel)).sum(axis=1) for c in ("ccr", "cva", "rrao")}
    out = {c: _estimate(p) for c, p in per_path.items()}
    out["total"] = _estimate(sum(per_path.values()))

    v0 = np.array([[sum(float(alive_value(t, triggers[t.gauge_id], zero, 0.0, np.ones(1))[0])
                        for t in nset.trades)]])
    today = capital(nset, counterparty, nodes=np.zeros(1), alive=np.ones((len(nset.trades), 1, 1), bool),
                    net=v0, collateral=nset.csa.variation_margin_held(v0), **_capital_args(cfg))
    out["today"] = {c: float(v[0, 0]) for c, v in today.items()}
    out["profiles"] = {c: held[c].mean(axis=0).tolist() for c in ("ead", "ccr", "cva", "rrao")}
    out["included_in_booked"] = False
    return out


def _euler_cva(values, exp, weights, rate_kernel, total) -> Dict[str, object]:
    """Trade contributions to CVA: E[V_i 1{exposure > 0}] (Green 3.84-3.93).

    Exact for an uncollateralised netted set, where EPE is homogeneous of
    degree one in the trade weights. Thresholds, IM and per-trade (unnetted)
    close-out break homogeneity; the residual is reported, not hidden.
    """
    indicator = (exp["epe"] > 0).astype(float) * weights
    contributions = [-float(((v * indicator) * rate_kernel).sum(axis=1).mean()) for v in values]
    return {"contributions": contributions, "residual": total - sum(contributions)}


def _audit(nset: NettingSet, cfg: XvaConfig) -> Dict:
    return {
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine": "monte_carlo",
        "config_sha256": cfg.fingerprint(),
        "seed": cfg.seed,
        "n_paths": cfg.n_paths,
        "status": STATUS,
        "config": asdict(cfg),
        "netting_set": {"n_trades": len(nset.trades), "csa": asdict(nset.csa),
                        "close_out_netting": nset.close_out_netting},
    }
