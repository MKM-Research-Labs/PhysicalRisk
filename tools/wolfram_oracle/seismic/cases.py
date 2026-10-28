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

"""The cells of SEIS-001's sensitivity tables: the model's Monte Carlo, the exact
credit, and what Wolfram is asked.

Every cell is rebuilt as the document's generator built it -- its fault, baseline
and placement -- and run at its draw count and seed, so the model's figures can be
compared with the printed ones, and both with the exact credit in standard errors.
"""

import importlib

import mpmath as mp
import numpy as np

from config.models import (
    ORACLE_REFERENCE_DPS,
    ORACLE_SEIS_BASELINE,
    ORACLE_SEIS_FAULT,
    ORACLE_SEIS_FAULT_LAT,
    ORACLE_SEIS_FAULT_LON,
    ORACLE_SEIS_KM_PER_DEG,
    ORACLE_SEIS_N_SIM,
    ORACLE_SEIS_PACKAGE,
    ORACLE_SEIS_PRODUCTION_N_SIM,
    ORACLE_SEIS_SEED,
    ORACLE_SEIS_TABLES,
    ORACLE_SEIS_WOLFRAM_GOAL,
    ORACLE_WOLFRAM_DIGITS,
)
from config.seismic import SeismicRunConfig, load_seismic_config
from tools.wolfram_oracle._wl import rel_err, wl_precise
from tools.wolfram_oracle.seismic import exact

METRICS = ("pga", "no_collapse", "loss", "spread")
UNIT = {"pga": 1.0, "no_collapse": 100.0, "loss": 100.0, "spread": 10_000.0}


def load():
    return {"damage": importlib.import_module(f"{ORACLE_SEIS_PACKAGE}.damage"),
            "gm": importlib.import_module(f"{ORACLE_SEIS_PACKAGE}.groundmotion"),
            "resp": importlib.import_module(f"{ORACLE_SEIS_PACKAGE}.responseeffectiveness"),
            "occ": importlib.import_module(f"{ORACLE_SEIS_PACKAGE}.occurrence"),
            "features": importlib.import_module(f"{ORACLE_SEIS_PACKAGE}.datastructures").AssetSeismicFeatures,
            "config": load_seismic_config(run=SeismicRunConfig(n_sim=ORACLE_SEIS_N_SIM))}


def cells():
    out = []
    for number, _, rows in ORACLE_SEIS_TABLES:
        for label, over, printed in rows:
            out.append((f"T{number}/{label}", number, label, {**ORACLE_SEIS_BASELINE, **over}, printed))
    return out


def features(m, feat):
    f = {k: v for k, v in feat.items() if k not in ("r_jb_km", "measures")}
    return m["features"](**f, latitude=ORACLE_SEIS_FAULT_LAT - feat["r_jb_km"] / ORACLE_SEIS_KM_PER_DEG,
                         longitude=ORACLE_SEIS_FAULT_LON, measures=frozenset(feat["measures"]))


def fmt(v):
    """The generator's number format (docs/models/sensitivities latex_table)."""
    return f"{v:.1f}" if abs(v) >= 10 else (f"{v:.2f}" if abs(v) >= 1 else f"{v:.4f}")


def asset_key(feat):
    return tuple(sorted((k, tuple(v) if isinstance(v, (list, tuple)) else v) for k, v in feat.items()))


def asset_ids(exact_by):
    return {key: f"asset/{i}" for i, key in enumerate(exact_by)}


def _se(metric, ex, n):
    """Standard error of the model's estimate at n draws, as a fraction (pga: in g)."""
    q = ex["q"]
    if metric == "no_collapse":
        p = ex["no_collapse"]
        return mp.sqrt(p * (1 - p) / (n * q))
    if metric == "spread":
        p = ex["spread"]
        return mp.sqrt(p * (1 - p) / n)
    if metric == "loss":
        return mp.sqrt((ex["loss_second"] - ex["loss"] ** 2) / n)
    return 1 / (2 * ex["pga_density"] * mp.sqrt(n * q))      # a sample median


def _z(est, exact_v, se):
    if se == 0:
        return 0.0 if abs(est - exact_v) < 1e-15 else float("inf")
    return float((mp.mpf(est) - exact_v) / se)


def _checks(m, feat, f, ex, res):
    """Model C, the GMPE median, lambda and R_JB in the code, against the reference."""
    cfg = m["config"]
    prof = m["resp"].derive_response_profile(f, cfg)
    medians, beta = m["damage"].adjusted_medians(f.construction_type, prof.theta_mult, cfg.fragility)
    err = max(rel_err(medians[d], ex["thetas"][d]) for d in exact.DS)
    ev = ex["ev"]
    for mag in (5.0, 6.0, 7.0):
        err = max(err, rel_err(m["gm"].gmpe_median_pga(mag, float(ev["r_jb"]), float(ev["vs30"]), ev["gmpe"]),
                               mp.exp(exact.ln_median(mp.mpf(mag), ev["r_jb"], ev["vs30"], ev["gmpe"]))))
    err = max(err, rel_err(res.lambda_annual, ev["lam"]))
    rjb = max((rel_err(o, ev["r_jb"]) for o in _event_rjb(m, f)), default=0.0)
    return err, rjb


def _event_rjb(m, f):
    fault = m["occ"].parse_fault_trace([list(v) for v in ORACLE_SEIS_FAULT])
    occ = m["occ"].simulate_asset_occurrence(f, m["config"], fault, np.random.default_rng(ORACLE_SEIS_SEED), 2_000)
    return [e.r_jb_km for e in occ.events]


def run(m):
    cfg = m["config"]
    fault = m["occ"].parse_fault_trace([list(v) for v in ORACLE_SEIS_FAULT])
    exact_by, rows = {}, []
    for cid, number, label, feat, printed in cells():
        f = features(m, feat)
        res = m["damage"].simulate_asset_seismic(f, cfg, fault, np.random.default_rng(ORACLE_SEIS_SEED))
        key = asset_key(feat)
        with mp.workdps(ORACLE_REFERENCE_DPS):
            if key not in exact_by:
                ex = exact.credit(feat, cfg, ORACLE_SEIS_KM_PER_DEG, with_median="pga" in printed)
                exact_by[key] = (feat, ex, *_checks(m, feat, f, ex, res))
            feat_, ex, chk, rjb_err = exact_by[key]
            if "pga" in printed and "pga" not in ex:  # pragma: no cover - Table 3 meets every PGA asset first
                ex.update(dict(zip(("pga", "pga_density"), exact.median_pga(ex["ev"]))))
            pgas = sorted(o.pga_g for o in res.outcomes)
            model = {"pga": pgas[len(pgas) // 2] if pgas else 0.0, "no_collapse": res.no_collapse_rate,
                     "loss": res.loss_frequency, "spread": res.seismic_spread_bps / 10_000}
            row = {"id": cid, "table": number, "label": label, "asset": asset_ids(exact_by)[key],
                   "lam": float(ex["ev"]["lam"]), "r_jb": float(ex["ev"]["r_jb"]),
                   "check_rel_err": chk, "rjb_rel_err": rjb_err, "n_events": res.n_events,
                   "p_ds3": float(ex["p"]["DS3"])}
            for k in METRICS:
                if k == "pga" and "pga" not in ex:
                    continue
                se = _se(k, ex, ORACLE_SEIS_N_SIM)
                row[f"{k}_exact"] = float(ex[k] * UNIT[k])
                row[f"{k}_model"] = model[k] * UNIT[k]
                row[f"{k}_z"] = _z(model[k], ex[k], se)
                row[f"{k}_se"] = float(se * UNIT[k])
                if k in printed:
                    row[f"{k}_printed"] = printed[k]
                    row[f"{k}_printed_z"] = _z(printed[k] / UNIT[k], ex[k], se)
                    row[f"{k}_reproduced"] = fmt(model[k] * UNIT[k]) == fmt(printed[k])
            row["spread_se_production"] = float(_se("spread", ex, ORACLE_SEIS_PRODUCTION_N_SIM) * 10_000)
            rows.append(row)
    return rows, exact_by


def wl_items(exact_by, m):
    """Per asset, Wolfram's {P(DS>=1), P(DS>=2), P(DS>=3)} by NIntegrate over magnitude."""
    d, g = ORACLE_WOLFRAM_DIGITS, ORACLE_SEIS_WOLFRAM_GOAL
    items, ids = [], asset_ids(exact_by)
    for key, (feat, ex, *_) in exact_by.items():
        ev, gm = ex["ev"], ex["ev"]["gmpe"]
        c = {k: wl_precise(gm.get(k, 0.0)) for k in ("c0", "c1", "c2", "c3", "c4", "c5", "mref", "vref", "h_km")}
        r = f"{mp.nstr(ev['r_jb'], 45, min_fixed=-mp.inf, max_fixed=mp.inf)}`{2 * d}"
        lnmu = (f"({c['c0']} + {c['c1']} (m - {c['mref']}) + {c['c2']} (m - {c['mref']})^2 + "
                f"({c['c3']} + {c['c5']} (m - {c['mref']})) Log[Sqrt[{r}^2 + {c['h_km']}^2]] + "
                f"{c['c4']} Log[{wl_precise(float(ev['vs30']))}/{c['vref']}] + Log[{wl_precise(float(ev['fa']))}])")
        b, lo, hi = (wl_precise(float(ev[k])) for k in ("b", "m_min", "m_max"))
        dens = f"{b} Log[10] 10^(-{b} (m - {lo}))/(1 - 10^(-{b} ({hi} - {lo})))"
        s = f"Sqrt[{wl_precise(float(ev['sigma']))}^2 + {wl_precise(float(ex['beta']))}^2]"
        parts = [f"NIntegrate[CDF[NormalDistribution[0, 1], ({lnmu} - Log[{_wl_mp(ex['thetas'][ds], d)}])/{s}] {dens}, "
                 f"{{m, {lo}, {hi}}}, WorkingPrecision -> {g + 20}, PrecisionGoal -> {g}]" for ds in exact.DS]
        items.append((ids[key], f"N[{{{', '.join(parts)}}}, {d}]"))
    return items


def _wl_mp(x, d):
    return f"{mp.nstr(x, 45, min_fixed=-mp.inf, max_fixed=mp.inf)}`{2 * d}"
