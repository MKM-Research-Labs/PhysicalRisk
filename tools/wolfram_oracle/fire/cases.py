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

"""The cells of FIRE-001's sensitivity tables: the model's Monte Carlo, the exact
credit, and what Wolfram is asked.

Every cell is rebuilt as the document's generator built it -- the baseline asset
with one or two inputs varied, run at the generator's draw count and seed -- so the
model's figures can be compared with the printed ones, and both with the exact
credit in sampling standard errors.
"""

import importlib

import mpmath as mp
import numpy as np

from config.fire import FireRunConfig, load_fire_config
from config.models import (
    ORACLE_FIRE_BASELINE,
    ORACLE_FIRE_LEVELS,
    ORACLE_FIRE_N_SIM,
    ORACLE_FIRE_PACKAGE,
    ORACLE_FIRE_PRODUCTION_N_SIM,
    ORACLE_FIRE_SEED,
    ORACLE_FIRE_TABLES,
    ORACLE_REFERENCE_DPS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import rel_err, wl_list, wl_precise
from tools.wolfram_oracle.fire import exact

METRICS = ("containment", "loss", "spread_bps")
_SCALE = {"containment": 100.0, "loss": 100.0, "spread_bps": 10_000.0}   # display units


def load():
    pkg = importlib.import_module(ORACLE_FIRE_PACKAGE)
    return {"containment": importlib.import_module(f"{ORACLE_FIRE_PACKAGE}.containment"),
            "initiation": importlib.import_module(f"{ORACLE_FIRE_PACKAGE}.initiation"),
            "features": pkg.data_structures.AssetFireFeatures,
            "config": load_fire_config(run=FireRunConfig(n_sim=ORACLE_FIRE_N_SIM))}


def cells():
    """(id, table, label, features, printed figures) for every printed cell."""
    out = []
    for number, _, base, rows in ORACLE_FIRE_TABLES:
        for label, over, *printed in rows:
            feat = {**ORACLE_FIRE_BASELINE, "construction_type": None, **base, **over}
            out.append((f"T{number}/{label}", number, label, feat, dict(zip(METRICS, printed))))
    return out


def asset_key(feat):
    return tuple(sorted(feat.items(), key=lambda kv: kv[0]))


def _se(metric, p, q, n):
    """Sampling standard error of the model's estimate, as a probability: the
    containment rate is conditional on a fire, so it rests on n q draws."""
    count = n * q if metric == "containment" else n
    return mp.sqrt(p * (1 - p) / count) if count > 0 else mp.mpf(0)


def asset_ids(exact_by):
    """A stable id per distinct asset, in the order the tables first meet it."""
    return {key: f"asset/{i}" for i, key in enumerate(exact_by)}


def _z(est, exact_v, se):
    if se == 0:
        return 0.0 if abs(est - exact_v) < 1e-15 else float("inf")
    return float((mp.mpf(est) - exact_v) / se)


def printed_match(model, printed):
    """True if the model's figure rounds to the printed one (3 significant figures)."""
    if printed == 0:
        return model == 0
    unit = 10 ** (mp.floor(mp.log10(abs(printed))) - 2)
    return abs(model - printed) <= unit / 2 + 1e-12


def run(m):
    """Every cell: model at the generator's seed, exact credit, z-scores."""
    cfg, prog = m["config"], m["config"].progression
    exact_by, rows = {}, []
    for cid, number, label, feat, printed in cells():
        f = m["features"](**feat)
        res = m["containment"].simulate_asset_fire(f, cfg, np.random.default_rng(ORACLE_FIRE_SEED))
        lam = m["initiation"].asset_lambda(f, cfg.initiation)
        key = asset_key(feat)
        with mp.workdps(ORACLE_REFERENCE_DPS):
            if key not in exact_by:
                ref = exact.profile(feat, prog, ORACLE_FIRE_LEVELS)
                code = m["containment"].derive_response_profile(f, prog)
                prof_err = max(rel_err(getattr(code, k), v) for k, v in ref.items()
                               if hasattr(code, k) and not isinstance(v, bool))
                flags_ok = all(getattr(code, k) == ref[k] for k in ("suppression_reachable",
                                                                     "structure_combustible"))
                w_err = rel_err(m["containment"].controllability_blend_weight(code, prog),
                                ref["blend_weight"]) if ref["blend_weight"] else 0.0
                exact_by[key] = (ref, exact.credit(ref, prog.transition_matrices, prog.race_jitter,
                                                   cfg.run.max_steps, lam, cfg.run.horizon_years),
                                 max(prof_err, w_err), flags_ok, lam)
            ref, ex, prof_err, flags_ok, lam = exact_by[key]
            model = {"containment": res.containment_rate, "loss": res.loss_frequency,
                     "spread_bps": res.n_point_of_no_return / res.n_sim}
            exact_p = {"containment": ex["contained"], "loss": ex["loss"], "spread_bps": ex["q"] * ex["pnr"]}
            row = {"id": cid, "table": number, "label": label, "asset": asset_ids(exact_by)[key],
                   "lam": lam, "profile_rel_err": prof_err, "flags_ok": flags_ok,
                   "n_fires": res.n_fires, "pnr_step": float(ex["p_pnr_step"]),
                   "pnr_recorded": float(ex["pnr"]), "unresolved": float(ex["unresolved"]),
                   "mean_steps": float(ex["mean_steps"]), "growth": float(ref["growth"])}
            for k in METRICS:
                p, unit = exact_p[k], _SCALE[k]
                se = _se(k, p, ex["q"], ORACLE_FIRE_N_SIM)
                row[f"{k}_exact"] = float(p * unit)
                row[f"{k}_model"] = model[k] * unit
                row[f"{k}_z"] = _z(model[k], p, se)
                if printed[k] is not None:
                    row[f"{k}_printed"] = printed[k]
                    row[f"{k}_printed_z"] = _z(printed[k] / unit, p, se)
                    row[f"{k}_reproduced"] = printed_match(model[k] * unit, printed[k])
            row["spread_se_production"] = float(
                _se("spread_bps", exact_p["spread_bps"], ex["q"], ORACLE_FIRE_PRODUCTION_N_SIM) * 10_000)
            rows.append(row)
    return rows, exact_by


def _wl_mp(x):
    s = mp.nstr(x, 45, min_fixed=-mp.inf, max_fixed=mp.inf) if x else "0"
    return f"{s}`{2 * ORACLE_WOLFRAM_DIGITS}" if x else "0"      # precision-marked


def wl_items(exact_by, m):
    """Per distinct asset, Wolfram's exact {contained, partial, total, PNR recorded, q}."""
    prog, cfg = m["config"].progression, m["config"]
    mats = {k: "{" + ", ".join(wl_list(r, wl_precise) for r in v) + "}"
            for k, v in prog.transition_matrices.items() if not k.startswith("_")}
    j = prog.race_jitter
    items = []
    ids = asset_ids(exact_by)
    for key, (ref, _, _, _, lam) in exact_by.items():
        auto = "True" if (not ref["suppression_reachable"] and ref["structure_combustible"]) else "False"
        # Lognormal tails as Erfc survival functions, never 1 - CDF, which at working
        # precision rounds a 1e-140 tail to zero; a CDF difference is taken from
        # whichever tail avoids cancellation.
        law = (f"If[{auto}, Join[{{1}}, ConstantArray[0, T - 1]], Table[If[t == 1, sf[zg[ic]], "
               f"bt[zg[ic/t], zg[ic/(t - 1)]]] If[t <= det, 1, sf[Log[(t - det)/bite]/st]] "
               f"sf[Log[ic/cap]/sc], {{t, 1, T}}]]")
        body = (
            f"g0 = {_wl_mp(ref['growth'])}; ic = {_wl_mp(ref['i_crit'])}; det = {_wl_mp(ref['detection_steps'])}; "
            f"bite = {_wl_mp(ref['suppression_bite_steps'])}; cap = {_wl_mp(ref['intensity_ceiling'])}; "
            f"w = {_wl_mp(ref['blend_weight'])}; sg = {wl_precise(j['growth_sigma'])}; "
            f"st = {wl_precise(j['timing_sigma'])}; sc = {wl_precise(j['ceiling_sigma'])}; "
            f"T = {cfg.run.max_steps}; sf = Function[x, Erfc[x/Sqrt[2]]/2]; "
            f"bt = Function[{{a, b}}, If[a > 0, sf[a] - sf[b], sf[-b] - sf[-a]]]; "
            f"zg = Function[x, Log[x/g0]/sg]; "
            f"ab = Function[mm, ReplacePart[mm, {{6 -> UnitVector[8, 6], 7 -> UnitVector[8, 7], 8 -> UnitVector[8, 8]}}]]; "
            f"pre = ab[w {mats['AA_controllable']} + (1 - w) {mats['weak_controllable']}]; "
            f"pn = ab[{mats['point_of_no_return']}]; law = {law}; "
            f"u = FoldList[#1 . pre &, UnitVector[8, 1], Range[T]]; "
            f"res = Sum[law[[k]] u[[k]] . MatrixPower[pn, T - k + 1], {{k, 1, T}}] + (1 - Total[law]) u[[T + 1]]; "
            f"rec = Sum[law[[k]] (1 - Total[u[[k]][[6 ;; 8]]]), {{k, 1, T}}]; "
            f"q = 1 - Exp[-{wl_precise(lam)} {wl_precise(cfg.run.horizon_years)}]")
        items.append((ids[key],
                      f"Module[{{g0, ic, det, bite, cap, w, sg, st, sc, T, sf, bt, zg, ab, pre, pn, law, u, res, rec, q}}, "
                      f"{body}; N[{{res[[6]], res[[7]], res[[8]], rec, q}}, {ORACLE_WOLFRAM_DIGITS}]]"))
    return items
