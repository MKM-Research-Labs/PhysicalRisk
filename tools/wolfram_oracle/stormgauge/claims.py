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
"""SG-001's model document, tested as stated (``storm_gauge.pdf`` v1.3).

Tables 4-7 are judged as printed: Tables 4 and 5 against the code, rounded as their
generator rounds; Tables 6 and 7, written by hand, to the places they print. The
statements about behaviour -- the calibration targets, the lag between peaks, what
doubling tau_decay does, the durations, and which inputs matter -- are judged by
running the code, which the checks show computes the document's equations. Where the
code goes is judged by searching the tree for anything that imports it.
"""

import dataclasses
import subprocess
import time

import mpmath as mp

from config import config
from config.models import (
    ORACLE_SG_DECAY,
    ORACLE_SG_GAMMA,
    ORACLE_SG_GAMMA_SHIFT,
    ORACLE_SG_GAMMA_STATED,
    ORACLE_SG_LAG,
    ORACLE_SG_LAG_TOL_H,
    ORACLE_SG_PACKAGE,
    ORACLE_SG_PRINTED_GAUSS,
    ORACLE_SG_PRINTED_T4,
    ORACLE_SG_PRINTED_T5,
    ORACLE_SG_PRINTED_T6,
    ORACLE_SG_PRINTED_T7,
    ORACLE_SG_T4,
    ORACLE_SG_T5,
    ORACLE_SG_T7_GAMMAS,
    ORACLE_SG_TARGET_TOL,
    ORACLE_SG_TARGETS,
    ORACLE_SG_TIMING,
)
from tools.wolfram_oracle.stormgauge import cases
from tools.wolfram_oracle.stormgauge import reference as ref

STAGES = (("alert", "flood_alert"), ("warning", "flood_warning"), ("severe", "severe_warning"))


def printed(v, places):
    """A value as the sensitivity generator printed it: rounded, then formatted by size."""
    v = round(float(v), places)
    return f"{v:.2f}" if abs(v) >= 1 else f"{v:.4f}"


def to_places(v, text):
    """``v`` written to as many places as the hand-written ``text``."""
    return f"{float(v):.{len(text.split('.')[1]) if '.' in text else 0}f}"


def _matched(got, want):
    return {"matched": sum(a == b for a, b in zip(got, want)), "of": len(want)}


def tables(m):
    model, kern = m["model"].StormGaugeModel(), m["data"].DecayKernel
    t4 = [printed(model.compute_decay(d, ORACLE_SG_T4["footprint"], kern(k), ORACLE_SG_T4["param"]), 4)
          for d in ORACLE_SG_T4["distances"] for k in ref.KERNELS]
    g = m["data"].GaugeConfig(gauge_id="T", gauge_name="T", latitude=51.5, longitude=-0.1, **ORACLE_SG_T5["gauge"])
    rows = [[printed(m["model"].StormGaugeModel(intensity_to_level_scale=s).intensity_to_level(i, g), 3)
             for i in ORACLE_SG_T5["intensities"]] for s in ORACLE_SG_T5["scales"]]
    t6 = [model.compute_decay(1.0, 1.0, kern(k), 0.5) for k in ref.KERNELS]
    with mp.workdps(50):
        t7 = [mp.mpf("0.5") ** mp.mpf(x) for x in ORACLE_SG_T7_GAMMAS]
        gauss = [100 * mp.exp(-mp.mpf(n) ** 2 / 2) for n in (1, 2)]
    out = {
        "t4": _matched(t4, [c for row in ORACLE_SG_PRINTED_T4 for c in row]),
        "t5": _matched([c for row in rows for c in row], list(ORACLE_SG_PRINTED_T5) * len(rows)),
        "t6": _matched([to_places(v, p) for v, p in zip(t6, ORACLE_SG_PRINTED_T6)], ORACLE_SG_PRINTED_T6),
        "t7": _matched([to_places(v, p) for v, p in zip(t7, ORACLE_SG_PRINTED_T7)], ORACLE_SG_PRINTED_T7),
        "gauss": _matched([to_places(v, p) for v, p in zip(gauss, ORACLE_SG_PRINTED_GAUSS)], ORACLE_SG_PRINTED_GAUSS),
    }
    for v in out.values():
        v["met"] = v["matched"] == v["of"]
    return out


def gamma_shift(intensity):
    """s6.2: the change in (I/100)^gamma when gamma moves by -25% and +25%."""
    with mp.workdps(50):
        x, g = mp.mpf(intensity) / 100, mp.mpf(ORACLE_SG_GAMMA)
        return [float(x ** (g * (1 + s)) / x ** g - 1) for s in (-ORACLE_SG_GAMMA_SHIFT, ORACLE_SG_GAMMA_SHIFT)]


def steady_targets():
    """s3.5: the intensity whose Eq. 13 target holds the level at each stage (Table 2's gauge)."""
    g = cases.gauge()
    with mp.workdps(50):
        rng = ref.high(g) - mp.mpf(g["base_level"])
        out = {k: float(100 * ((mp.mpf(g[s]) - mp.mpf(g["base_level"])) / rng) ** (1 / mp.mpf(ORACLE_SG_GAMMA)))
               for k, s in STAGES}
        out["high"] = float(100 * ((ref.high(g) - mp.mpf(g["base_level"])) / rng) ** (1 / mp.mpf(ORACLE_SG_GAMMA)))
    return out


def _run(m, s, g=None, **kw):
    return m["model"].StormGaugeModel(**kw).compute_response(s, cases.config(m, g or cases.gauge()))


def storm_targets(m):
    """The least peak intensity at which a default storm crossing the gauge reaches each stage."""
    g = cases.gauge()
    out = {}
    for key, stage in STAGES:
        if _run(m, cases.storm(m, 100.0)).peak_level < g[stage]:
            out[key] = None
            continue
        lo, hi = 0.0, 100.0
        while hi - lo > 1e-3:
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if _run(m, cases.storm(m, mid)).peak_level >= g[stage] else (mid, hi)
        out[key] = hi
    return out


def _targets_met(steady):
    t, tol = ORACLE_SG_TARGETS, ORACLE_SG_TARGET_TOL
    return (steady["alert"] is not None and abs(steady["alert"] - t["alert"]) <= tol
            and steady["warning"] is not None and t["warning"][0] - tol <= steady["warning"] <= t["warning"][1] + tol
            and steady["severe"] is not None and abs(steady["severe"] - t["severe"]) <= tol
            and abs(steady["high"] - t["high"]) <= tol)


def lag_gaps(m):
    """s3.7, s7.1: hours from peak intensity to peak level, wherever the gauge feels the storm."""
    gaps = []
    for s in cases.storms(m):
        for g in cases.gauges():
            r = _run(m, s, g)
            if r.peak_intensity > 1:
                gaps.append(r.peak_time_hours - r.peak_intensity_time_hours)
    return min(gaps), max(gaps)


def sensitivities(m):
    """s6.3 on a default storm crossing the gauge at peak 100: doubling tau_decay, doubling
    tau_lag, and what the simulation stops short of -- the same storm run on to 72 h."""
    s = cases.storm(m, 100.0)
    base = _run(m, s)
    slow = _run(m, s, response_decay_hours=2 * ORACLE_SG_DECAY)
    late = _run(m, s, response_lag_hours=2 * ORACLE_SG_LAG)
    longer = _run(m, dataclasses.replace(s, duration_hours=72.0))
    g = cases.gauge()
    rise = base.peak_level - g["base_level"]
    end = base.level_timeseries[-1]["level"] - g["base_level"]
    return {"dur": base.duration_above_alert, "dur_slow": slow.duration_above_alert,
            "peak_change": slow.peak_level / base.peak_level - 1,
            "lag_peak_change": late.peak_level / base.peak_level - 1,
            "lag_shift": late.peak_time_hours - base.peak_time_hours,
            "end_rise": end, "end_share": end / rise, "dur_72": longer.duration_above_alert,
            "acc": base.accumulation, "acc_72": longer.accumulation}


def unread_inputs(m):
    """Table 5's scale and Table 1's speed: does changing either change any response?"""
    s, g = cases.storm(m, 80.0), cases.gauge(0.1)
    base = _run(m, s, g).to_dict()
    scaled = _run(m, s, g, intensity_to_level_scale=10.0).to_dict()
    fast = _run(m, dataclasses.replace(s, speed_kmh=300.0), g).to_dict()
    return {"scale": base == scaled, "speed": base == fast}


def timing(m):
    """Q3: a 48-hour storm with 25 track points over 25 gauges, best of five."""
    t = ORACLE_SG_TIMING
    s = cases.storm(m, 80.0, duration=t["hours"])
    gs = [cases.config(m, cases.gauge(0.02 * i)) for i in range(t["gauges"])]
    model = m["model"].StormGaugeModel()
    best = float("inf")
    for _ in range(5):
        t0 = time.perf_counter()
        model.compute_all_responses(s, gs)
        best = min(best, time.perf_counter() - t0)
    return {"all_ms": 1000 * best, "per_gauge_ms": 1000 * best / t["gauges"]}


def importers():
    """Every file outside the package (and the models package's docstring) importing it."""
    out = subprocess.run(["git", "grep", "-lE", r"^\s*(from|import)\s+\S*stormgauge", "--", "src", "tools", "scripts"],
                         capture_output=True, text=True, cwd=config.get_project_root()).stdout.split()
    return [f for f in out if not f.startswith(ORACLE_SG_PACKAGE)]


def assess(m):
    """Each claim as a dict with its figures and ``met``."""
    steady, in_storm = steady_targets(), storm_targets(m)
    shift50 = gamma_shift(50)
    mid = [x for i in (40, 50, 60) for x in gamma_shift(i)]
    lo, hi = ORACLE_SG_GAMMA_STATED
    gaps, sens, unread, t = lag_gaps(m), sensitivities(m), unread_inputs(m), timing(m)
    imp = importers()
    return {
        **tables(m),
        "gamma": {"at50": shift50, "range": (min(abs(x) for x in mid), max(abs(x) for x in mid)),
                  "met": all(lo - 0.005 <= abs(x) <= hi + 0.005 for x in shift50)},
        "steady": {**steady, "met": _targets_met(steady)},
        "storm": {**in_storm, "met": _targets_met({**in_storm, "high": steady["high"]})},
        "lag": {"gaps": gaps, "met": all(abs(x - ORACLE_SG_LAG) <= ORACLE_SG_LAG_TOL_H for x in gaps)},
        "decay": {**{k: sens[k] for k in ("dur", "dur_slow", "peak_change")},
                  "met": 1.5 <= sens["dur_slow"] / sens["dur"] <= 2.5 and abs(sens["peak_change"]) < 0.05},
        "lagpeak": {"change": sens["lag_peak_change"], "shift": sens["lag_shift"],
                    "met": abs(sens["lag_peak_change"]) < 0.01},
        "duration": {**{k: sens[k] for k in ("dur", "dur_72", "end_rise", "end_share", "acc", "acc_72")},
                     "met": sens["dur"] == sens["dur_72"] and sens["acc"] == sens["acc_72"]},
        "unread": {**unread, "met": not (unread["scale"] or unread["speed"])},
        "timing": {**t, "met": t["per_gauge_ms"] < ORACLE_SG_TIMING["per_gauge_ms"]
                   and t["all_ms"] < ORACLE_SG_TIMING["all_ms"]},
        "lineage": {"importers": imp, "met": bool(imp)},
    }
