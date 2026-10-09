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

"""
MKM-XV-001 validation evidence
==============================

Re-runs every benchmark, reconciliation and sensitivity the model document
quotes, and writes them to ``validation_evidence.json`` with an audit block
(git commit, config hash, seeds, path counts). ``_evidence_latex.py`` turns
the JSON into the tables ``docs/models/prs_xva`` inputs, so the document's
numbers are this script's numbers and cannot drift from the code.

Run from the repository root:

    python docs/xva/validation_evidence.py            # full: 10,000 paths
    python docs/xva/validation_evidence.py --quick    # structure check, 1,000 paths

Each check returns its figures and a ``pass`` flag against the tolerance the
project plan set for it (§6, and the exit criteria of WP1-WP3).
"""

import argparse
import json
import math
import subprocess
import sys
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

import numpy as np  # noqa: E402

from config.port import DEFAULT_YIELD_CURVE  # noqa: E402
from config.xva import STATUS, XvaConfig  # noqa: E402
from models.capital import counterparty as cc  # noqa: E402
from models.hazard.prs_analytical import compute_prs_spread  # noqa: E402
from models.trading.delta_engine.pricer import compute_risky_annuity  # noqa: E402
from models.xva import (HazardCurve, Market, PrsTrade, ZeroCurve, analytic,  # noqa: E402
                        build_market, monte_carlo)
from models.xva.capital import CounterpartyProfile  # noqa: E402
from models.xva.cir import CirFactor, ShiftedTrigger  # noqa: E402
from models.xva.netting import Csa, NettingSet  # noqa: E402
from models.xva.valuation import fair_spread, legs  # noqa: E402
from tests.models.xva._reference import Ref  # noqa: E402

ZERO = ZeroCurve(DEFAULT_YIELD_CURVE)
NOTIONAL, TENOR, P_TRIGGER = 10_000_000.0, 5, 0.02
LAM_E = HazardCurve.from_annual_probability(P_TRIGGER)
PROFILE = CounterpartyProfile("BBB", "corporate", "financials")


def _trade(buyer: bool, spread=None, gauge="G1") -> PrsTrade:
    t = PrsTrade(NOTIONAL, 0.01, TENOR, buyer, LAM_E, gauge)
    return replace(t, spread=fair_spread(t, ZERO) if spread is None else spread)


def _rel(a, b):
    return abs(a - b) / max(abs(b), 1e-300)


# --- WP1: the analytic engine -------------------------------------------------

def pricer_reconciliation():
    worst_spread = worst_annuity = 0.0
    for p in (0.005, 0.02, 0.08):
        for tenor in (1, 2, 3, 5):
            t = PrsTrade(NOTIONAL, 0.01, tenor, True, HazardCurve.from_annual_probability(p))
            worst_spread = max(worst_spread, _rel(
                fair_spread(t, ZERO) * 1e4, compute_prs_spread(p, tenor, 0.0, yield_curve=DEFAULT_YIELD_CURVE)))
            worst_annuity = max(worst_annuity, _rel(
                legs(t, ZERO, 0.0)["annuity"], compute_risky_annuity(p, tenor, yield_curve=DEFAULT_YIELD_CURVE)))
    return {"max_rel_fair_spread": worst_spread, "max_rel_annuity": worst_annuity,
            "tolerance": 1e-12, "pass": max(worst_spread, worst_annuity) < 1e-12}


def reference_agreement(cfg):
    rows, worst = [], 0.0
    for curve, label in ((None, "flat 3%"), (DEFAULT_YIELD_CURVE, "humped")):
        for buyer in (True, False):
            zero = ZeroCurve(curve, 0.03)
            lam_e = -math.log(1 - P_TRIGGER)
            t = PrsTrade(NOTIONAL, 0.018, TENOR, buyer, HazardCurve.flat(lam_e))
            m = Market(zero, HazardCurve.flat(0.02), HazardCurve.flat(cfg.own_hazard))
            eng = analytic.xva(t, m, cfg)
            ref = Ref(notional=NOTIONAL, spread=0.018, tenor=TENOR, buyer=buyer, lam_e=lam_e,
                      lam_c=0.02, lam_b=cfg.own_hazard, rec_c=cfg.counterparty_recovery,
                      rec_b=cfg.own_recovery, s_f=cfg.own_funding_spread,
                      lag=cfg.settlement_years, curve=curve)
            for view, expected in (("one_bond", ref.one_bond()),
                                   ("semi_replication", ref.semi_replication())):
                for term, v in expected.items():
                    worst = max(worst, _rel(eng[view][term], v))
            rows.append({"curve": label, "bank": "buys" if buyer else "sells",
                         "cva": eng["one_bond"]["cva"], "fva": eng["one_bond"]["fva"]})
    return {"cases": rows, "max_rel_difference": worst, "tolerance": 1e-8, "pass": worst < 1e-8}


def analytic_results(cfg):
    rows = []
    for rating in ("A", "BBB", "BB"):
        m = build_market(ZERO, cfg, rating=rating)
        for buyer in (True, False):
            r = analytic.run(_trade(buyer), m, cfg)
            ob, sr = r["views"]["one_bond"], r["views"]["semi_replication"]
            rows.append({"rating": rating, "bank": "buys" if buyer else "sells",
                         "cva": ob["cva"], "fva": ob["fva"], "booked": ob["total"],
                         "dva": sr["dva"], "semi_total": sr["total"],
                         "xva_spread_bps": r["xva_spread_bps"]})
    return {"fair_spread_bps": fair_spread(_trade(True), ZERO) * 1e4, "rows": rows}


# --- WP2: the Monte Carlo engine ------------------------------------------------

def mc_reconciliation(cfg):
    det = replace(cfg, hazard_vol=0.0)
    lam_c = HazardCurve.flat(0.02)
    worst, rows = 0.0, []
    for buyer in (True, False):
        t = replace(_trade(buyer, 0.018))
        out = monte_carlo.run(NettingSet([t], lam_c), ZERO, det)
        exact = analytic.xva(t, Market(ZERO, lam_c, HazardCurve.flat(det.own_hazard)), det)
        for view in ("one_bond", "semi_replication"):
            for term, est in out["views"][view].items():
                z = (est["value"] - exact[view][term]) / est["se"] if est["se"] else 0.0
                worst = max(worst, abs(z))
                rows.append({"bank": "buys" if buyer else "sells", "view": view, "term": term,
                             "mc": est["value"], "se": est["se"], "analytic": exact[view][term],
                             "z": z})
    return {"rows": rows, "max_abs_z": worst, "tolerance_se": 3.0, "pass": worst < 3.0}


def time_rule_error(cfg):
    from models.xva.exposure_analytic import profiles
    from models.xva.integrals import kernel
    from models.xva.paths import grid
    det = replace(cfg, hazard_vol=0.0)
    t = _trade(True, 0.018)
    lam_c = HazardCurve.flat(0.02)
    m = Market(ZERO, lam_c, HazardCurve.flat(det.own_hazard))
    exact = analytic.xva(t, m, det)["semi_replication"]["dva"]
    errors = {}
    for cells in (13, 26, 52):
        nodes, widths = grid(NettingSet([t], lam_c), det.settlement_years, cells)
        ene = profiles(t, ZERO, nodes, det.settlement_years, 24)["ene"]
        rate = (1 - det.own_recovery) * det.own_hazard
        errors[str(cells)] = float(-np.sum(widths * rate * kernel("semi_replication", m, det, nodes) * ene)
                              / exact - 1)
    return {"relative_error": errors, "ratio_26_to_52": errors["26"] / errors["52"],
            "pass": abs(errors["26"]) < 5e-4}


def cir_checks():
    lam = -math.log(1 - P_TRIGGER)
    fit = max(float(np.max(np.abs(ShiftedTrigger(CirFactor(0.5, s), HazardCurve.flat(lam))
                                  .survival(0.0, np.linspace(0, 10, 41), 1.0)
                                  / np.exp(-lam * np.linspace(0, 10, 41)) - 1)))
              for s in (0.0, 0.3, 0.8))
    gaps = {s: abs(CirFactor(0.5, s).bond(4.0, lam)[0] - CirFactor(0.5, 0.0).bond(4.0, lam)[0])
            for s in (1e-2, 1e-4, 1e-6)}
    return {"cir_pp_max_rel_fit_error": fit, "small_vol_gap": {str(k): v for k, v in gaps.items()},
            "pass": fit < 1e-12 and gaps[1e-6] < 1e-12}


def mc_results(cfg):
    cp = build_market(ZERO, cfg, rating="BBB").counterparty
    buy, sell = _trade(True), _trade(False)
    cases = [
        ("buys, sigma 0", NettingSet([buy], cp), replace(cfg, hazard_vol=0.0)),
        ("buys, sigma 0.3", NettingSet([buy], cp), cfg),
        ("buys, WWR beta 3", NettingSet([buy], cp), replace(cfg, wwr_beta=3.0)),
        ("buys, VM", NettingSet([buy], cp, Csa(True)), cfg),
        ("buys, VM + IM = notional", NettingSet([buy], cp, Csa(True, im_received=NOTIONAL)), cfg),
        ("sells, sigma 0.3", NettingSet([sell], cp), cfg),
        ("sells, WWR beta 3", NettingSet([sell], cp), replace(cfg, wwr_beta=3.0)),
        ("sells, VM", NettingSet([sell], cp, Csa(True)), cfg),
    ]
    rows = []
    for label, nset, c in cases:
        b = monte_carlo.run(nset, ZERO, c)["booked"]
        rows.append({"case": label, "cva": b["cva"]["value"], "cva_se": b["cva"]["se"],
                     "fva": b["fva"]["value"], "booked": b["total"]["value"]})
    return {"rows": rows}


# --- WP3: capital -----------------------------------------------------------

def basel_examples():
    sd = cc.supervisory_duration(0.0, np.array([3.0, 6.0, 5.0]))
    addons = np.array([0.0038, -0.0054, 0.0038]) * 10_000 * sd
    credit_addon = float(cc.aggregate_addon(list(addons), [0.5, 0.5, 0.8]))
    ex2 = float(cc.ead(-20.0, 0.0, credit_addon))
    mf = cc.maturity_factor_unmargined(np.array([0.75, 2.0, 5.0]))
    com = cc.commodity_addon({"energy": {"crude": 10_000 * mf[0] - 20_000 * mf[1]},
                              "metals": {"silver": 10_000 * mf[2]}},
                             {"energy": 0.18, "metals": 0.18}, 0.4)
    ex3 = float(cc.ead(20.0, 0.0, com))
    return {"example_2": {"addon": credit_addon, "ead": ex2, "printed_ead": 381},
            "example_3": {"addon": float(com), "ead": ex3, "printed_ead": 5_406},
            "pass": round(ex2) == 381 and round(ex3) == 5_406 and round(credit_addon) == 282}


def capital_results(cfg):
    cp = build_market(ZERO, cfg, rating="BBB").counterparty
    annuity = legs(_trade(True), ZERO, 0.0)["annuity"]
    rows = []
    for label, c, csa in (("commodity other", cfg, Csa()),
                          ("credit analogy (ref. B)", replace(cfg, saccr_asset_class="credit_single_name"), Csa()),
                          ("commodity + RRAO", replace(cfg, rrao=True), Csa()),
                          ("commodity, VM", cfg, Csa(True))):
        k = monte_carlo.run(NettingSet([_trade(True)], cp, csa), ZERO, c, counterparty=PROFILE)["kva"]
        rows.append({"case": label, "ead_today": k["today"]["ead"],
                     "capital_today": k["today"]["ccr"] + k["today"]["cva"] + k["today"]["rrao"],
                     "kva": k["total"]["value"], "kva_se": k["total"]["se"],
                     "kva_bps": abs(k["total"]["value"]) / (NOTIONAL * annuity) * 1e4})
    return {"rows": rows}


# --- Sensitivities (§6) ------------------------------------------------------

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


def sensitivities(cfg):
    base_cp = build_market(ZERO, cfg, rating="BBB").counterparty
    rows = []
    for buyer in (True, False):
        def run(c, cp_scale=1.0):
            cp = HazardCurve(base_cp.knots, base_cp.rates * cp_scale)
            out = monte_carlo.run(NettingSet([_trade(buyer)], cp), ZERO, c, counterparty=PROFILE)
            return out["booked"]["total"]["value"], out["kva"]["total"]["value"]
        base_xva, base_kva = run(cfg)
        rows.append({"bank": "buys" if buyer else "sells", "case": "base",
                     "xva": base_xva, "kva": base_kva})
        for label, change, kw in SENSITIVITIES:
            x, k = run(change(cfg), **kw)
            rows.append({"bank": "buys" if buyer else "sells", "case": label, "xva": x, "kva": k})
    return {"rows": rows}


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run(quick: bool = False) -> dict:
    cfg = XvaConfig(n_paths=1_000) if quick else XvaConfig()
    checks = {
        "pricer_reconciliation": pricer_reconciliation(),
        "reference_agreement": reference_agreement(cfg),
        "mc_reconciliation": mc_reconciliation(cfg),
        "time_rule_error": time_rule_error(cfg),
        "cir": cir_checks(),
        "basel_examples": basel_examples(),
    }
    return {
        "model_id": "MKM-XV-001",
        "checks": checks,
        "all_pass": all(c["pass"] for c in checks.values()),
        "results": {"analytic": analytic_results(cfg), "monte_carlo": mc_results(cfg),
                    "capital": capital_results(cfg)},
        "sensitivities": sensitivities(cfg),
        "audit": {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "git_commit": _commit(), "config_sha256": cfg.fingerprint(),
                  "seed": cfg.seed, "n_paths": cfg.n_paths, "quick": quick,
                  "status": STATUS, "config": asdict(cfg)},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quick", action="store_true", help="1,000 paths; structure only")
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("validation_evidence.json"))
    args = parser.parse_args(argv)
    evidence = run(args.quick)
    args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True, default=float) + "\n")
    from _evidence_latex import write_tables
    write_tables(evidence, ROOT / "docs/models/prs_xva")
    for name, check in evidence["checks"].items():
        print(f"{'PASS' if check['pass'] else 'FAIL'}  {name}")
    return 0 if evidence["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
