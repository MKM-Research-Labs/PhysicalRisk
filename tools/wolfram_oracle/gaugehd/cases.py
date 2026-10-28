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

"""The gauges, the model's replications, and what Wolfram is asked.

Each gauge is generated ORACLE_GHD_REPLICATIONS times with seeds 1..n through the
model's own generate_synthetic_timeseries; each statistic's mean over them is judged
against its exact expectation in standard errors of that mean.
"""

import importlib
from datetime import datetime

import mpmath as mp
import numpy as np

from config.models import (
    ORACLE_GHD_HISTORICAL_HIGH,
    ORACLE_GHD_MODULE,
    ORACLE_GHD_N3,
    ORACLE_GHD_REGIMES,
    ORACLE_GHD_REPLICATIONS,
    ORACLE_GHD_SPRING_NEAP,
    ORACLE_GHD_TABLE1,
    ORACLE_GHD_THRESHOLDS,
    ORACLE_GHD_YEARS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import wl_exact
from tools.wolfram_oracle.gaugehd import exact

STATS = ("days_FloodAlert", "days_FloodWarning", "days_SevereFloodWarning", "mean",
         "jan_minus_mean", "jul_minus_mean")
# Closed-form spot checks for Wolfram: (day of year, age in days) at mu0 = 0.4 FloodAlert.
WL_POINTS = ((15, 1), (15, 3), (105, 2), (197, 1), (197, 8), (300, 20))


def load():
    return importlib.import_module(ORACLE_GHD_MODULE)


def gauges():
    return [(f"{reg}/n3={n3}", reg, n3) for reg in ORACLE_GHD_REGIMES for n3 in ORACLE_GHD_N3]


def gauge_data(regime, n3):
    return {"FloodGauge": {"FloodStages": dict(ORACLE_GHD_THRESHOLDS),
                           "SensorStats": {"HistoricalHighLevel": ORACLE_GHD_HISTORICAL_HIGH,
                                           "FrequencyExceedLevel3": n3},
                           "SensorDetails": {"GaugeInformation": {"TidalInfluence": regime}}}}


def statistics(obs):
    """The statistics of one generated series (levels as reported, to the millimetre)."""
    lv = np.array([o["level_meters"] for o in obs])
    months = np.array([int(o["date"][5:7]) for o in obs])
    out = {f"days_{k}": float((lv >= h).sum()) for k, h in ORACLE_GHD_THRESHOLDS.items()}
    out["mean"] = float(lv.mean())
    out["jan_minus_mean"] = float(lv[months == 1].mean() - lv.mean())
    out["jul_minus_mean"] = float(lv[months == 7].mean() - lv.mean())
    x = lv - lv.mean()
    out["lag1"] = float((x[:-1] * x[1:]).sum() / (x * x).sum())
    return out


def run(syn):
    rows, calendars = [], {}
    for gid, regime, n3 in gauges():
        reps = [syn.generate_synthetic_timeseries(gauge_data(regime, n3), ORACLE_GHD_YEARS, seed=s)
                for s in range(1, ORACLE_GHD_REPLICATIONS + 1)]
        dates = [r[0]["date"] for r in reps]
        if len(set(dates)) != 1:                            # the series ends at datetime.now()
            raise RuntimeError("the replications span midnight; re-run")
        cal = [datetime.strptime(o["date"], "%Y-%m-%d") for o in reps[0]]
        doy = [d.timetuple().tm_yday for d in cal]
        calendars[gid] = doy
        ex = exact.expected(regime, n3, doy, [d.month for d in cal], ORACLE_GHD_YEARS)
        sample = [statistics(r) for r in reps]
        row = {"id": gid, "regime": regime, "n3": n3, "n_days": len(doy), "start": dates[0],
               "floods_exact": float(ex["floods"]), "mu0_mean": float(ex["mu0"]),
               "lag1_flood_free": float(exact.lag1_flood_free(regime, doy)),
               "lag1_model": float(np.mean([s["lag1"] for s in sample]))}
        for k in STATS:
            vals = np.array([s[k] for s in sample])
            se = vals.std(ddof=1) / np.sqrt(len(vals))
            row[f"{k}_exact"], row[f"{k}_model"], row[f"{k}_se"] = float(ex[k]), float(vals.mean()), float(se)
            row[f"{k}_z"] = float((vals.mean() - ex[k]) / se) if se > 0 else 0.0
        rows.append(row)
    return rows, calendars


def wl_items():
    """Wolfram integrates the normal tail over the two uniforms symbolically, from the
    exact inputs, at points where the reference uses its own closed form. Exactly, not
    by NIntegrate: 30 digits of a 1e-33 tail defeat its adaptive rule."""
    d, items = ORACLE_WOLFRAM_DIGITS, []
    alert = ORACLE_GHD_THRESHOLDS["FloodAlert"]
    mu0 = 0.4 * alert
    for gid, regime, n3 in gauges()[::2]:
        sd, a_s, a_t, phi = ORACLE_GHD_TABLE1[regime]
        for doy, k in WL_POINTS:
            s_k = sd * mu0 * (1 - phi ** (2 * k)) ** 0.5
            seas = mu0 + a_s * mu0 * float(np.cos(2 * np.pi * (doy - 15) / 365))
            env = 0.6 + 0.4 * float(np.cos(2 * np.pi * (doy % ORACLE_GHD_SPRING_NEAP) / ORACLE_GHD_SPRING_NEAP))
            r1, r2 = ORACLE_GHD_THRESHOLDS["FloodAlert"] - mu0, ORACLE_GHD_THRESHOLDS["FloodWarning"] - mu0
            args = [f"({wl_exact(x)})" for x in (alert - 0.0005, seas, phi ** k, s_k, a_t * mu0 * env, r1, r2)]
            h, c, f, s, b, lo, hi = args
            items.append((f"tail/{gid}/{doy}/{k}",
                          f"N[Integrate[(1/2) Erfc[({h} - {c} - {f} r - {b} v)/({s} Sqrt[2])], "
                          f"{{r, {lo}, {hi}}}, {{v, -1, 1}}]/(2 ({hi} - {lo})), {d}]"))
    return items


def reference_points():
    """The reference's closed form at the same points, keyed as wl_items."""
    out, alert = {}, ORACLE_GHD_THRESHOLDS["FloodAlert"]
    mu0 = 0.4 * alert
    for gid, regime, n3 in gauges()[::2]:
        sd, a_s, a_t, phi = ORACLE_GHD_TABLE1[regime]
        for doy, k in WL_POINTS:
            s_k = sd * mu0 * (1 - phi ** (2 * k)) ** 0.5
            seas = mu0 + a_s * mu0 * float(np.cos(2 * np.pi * (doy - 15) / 365))
            env = 0.6 + 0.4 * float(np.cos(2 * np.pi * (doy % ORACLE_GHD_SPRING_NEAP) / ORACLE_GHD_SPRING_NEAP))
            out[f"tail/{gid}/{doy}/{k}"] = float(exact.tail_uniforms(
                (alert - 0.0005 - seas) / s_k, phi ** k / s_k, alert - mu0,
                ORACLE_GHD_THRESHOLDS["FloodWarning"] - mu0, a_t * mu0 * env / s_k))
    return out
