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
"""SG-001's model document, tested as stated (``storm_gauge_v2.0.pdf``).

Every printed table is judged figure by figure. Tables 4, 5, 8 and 9 were generated
from the code, so the code's value is rounded and formatted as their generator did.
Tables 6 and 7 were written by hand, and are judged to the places they print. The
statements -- the calibration bands, the lag, the recession, the unread speed, the
sphere's error, the timings -- are judged by running the code, which the checks show
computes the document's equations. Where the code goes is judged by searching the tree
for anything that imports it.
"""

import dataclasses
import subprocess
import time

import mpmath as mp

from config import config
from config.models import (
    ORACLE_SG_ELLIPSOID_STATED,
    ORACLE_SG_GAMMA,
    ORACLE_SG_GAMMA_STATED,
    ORACLE_SG_LAG_STATED_H,
    ORACLE_SG_PACKAGE,
    ORACLE_SG_PRINTED_GAUSS,
    ORACLE_SG_PRINTED_T4,
    ORACLE_SG_PRINTED_T5,
    ORACLE_SG_PRINTED_T6,
    ORACLE_SG_PRINTED_T7,
    ORACLE_SG_PRINTED_T8,
    ORACLE_SG_PRINTED_T9,
    ORACLE_SG_STEADY_STATED,
    ORACLE_SG_STORM_STATED,
    ORACLE_SG_T4,
    ORACLE_SG_T5,
    ORACLE_SG_T5_SENSITIVITIES,
    ORACLE_SG_T7_GAMMAS,
    ORACLE_SG_TIMING,
)
from tools.wolfram_oracle.stormgauge import cases
from tools.wolfram_oracle.stormgauge import reference as ref

STAGES = (("alert", "flood_alert"), ("warning", "flood_warning"), ("severe", "severe_warning"))
CONSTANTS = {"lag": "response_lag_hours", "rise": "response_rise_hours", "decay": "response_decay_hours"}


def printed(v, places):
    """A value as the sensitivity generator printed it: rounded, then formatted by size."""
    v = round(float(v), places)
    return f"{v:.2f}" if abs(v) >= 1 else f"{v:.4f}"


def to_places(v, text):
    """``v`` written to as many places as the hand-written ``text``."""
    return f"{float(v):.{len(text.split('.')[1]) if '.' in text else 0}f}"


def _matched(got, want):
    got, want = list(got), list(want)
    return {"matched": sum(a == b for a, b in zip(got, want)), "of": len(want), "met": got == want}


def _flat(rows):
    return [c for row in rows for c in row]


def _run(m, s, g=None, **kw):
    return m["model"].StormGaugeModel(**kw).compute_response(s, cases.config(m, g or cases.gauge()))


def _row(r):
    """A response as Tables 8 and 9 print it."""
    lag = r.peak_time_hours - r.peak_intensity_time_hours
    return {"I": f"{r.peak_intensity:.1f}", "L": f"{r.peak_level:.2f}", "lag": f"{lag:.1f}",
            "Da": f"{r.duration_above_alert:.1f}", "Dw": f"{r.duration_above_warning:.1f}",
            "Ds": f"{r.duration_above_severe:.1f}", "A": f"{r.accumulation:.2f}"}


def tables(m):
    model, kern, data = m["model"].StormGaugeModel(), m["data"].DecayKernel, m["data"]
    t4 = [printed(model.compute_decay(d, ORACLE_SG_T4["footprint"], kern(k), ORACLE_SG_T4["param"]), 4)
          for d in ORACLE_SG_T4["distances"] for k in ref.KERNELS]
    t5 = [printed(model.intensity_to_level(i, data.GaugeConfig(gauge_id="T", gauge_name="T", latitude=51.5,
                                                                longitude=-0.1, sensitivity=s, **ORACLE_SG_T5["gauge"])), 3)
          for s in ORACLE_SG_T5_SENSITIVITIES for i in ORACLE_SG_T5["intensities"]]
    t6 = [model.compute_decay(1.0, 1.0, kern(k), 0.5) for k in ref.KERNELS]
    with mp.workdps(50):
        t7 = [mp.mpf("0.5") ** mp.mpf(x) for x in ORACLE_SG_T7_GAMMAS]
        gauss = [100 * mp.exp(-mp.mpf(n) ** 2 / 2) for n in (1, 2)]
    t8 = [tuple(_row(_run(m, cases.storm(m, float(pk)), cases.gauge(off))).values())
          for (pk, off), _ in ORACLE_SG_PRINTED_T8]
    s100 = cases.storm(m, 100.0)
    t9 = [(lambda x: (x["L"], x["lag"], x["Da"], x["A"]))(_row(_run(m, s100, **{CONSTANTS[c]: float(h)})))
          for (c, h), _ in ORACLE_SG_PRINTED_T9]
    return {
        "gauss": _matched([to_places(v, p) for v, p in zip(gauss, ORACLE_SG_PRINTED_GAUSS)], ORACLE_SG_PRINTED_GAUSS),
        "t4": _matched(t4, _flat(ORACLE_SG_PRINTED_T4)),
        "t5": _matched(t5, _flat(ORACLE_SG_PRINTED_T5)),
        "t6": _matched([to_places(v, p) for v, p in zip(t6, ORACLE_SG_PRINTED_T6)], ORACLE_SG_PRINTED_T6),
        "t7": _matched([to_places(v, p) for v, p in zip(t7, ORACLE_SG_PRINTED_T7)], ORACLE_SG_PRINTED_T7),
        "t8": _matched(_flat(t8), _flat(v for _, v in ORACLE_SG_PRINTED_T8)),
        "t9": _matched(_flat(t9), _flat(v for _, v in ORACLE_SG_PRINTED_T9)),
    }


def gamma_shift(intensity):
    """s6.2: the change in (I/100)^gamma when gamma moves by -25% and +25%."""
    with mp.workdps(50):
        x, g = mp.mpf(intensity) / 100, mp.mpf(ORACLE_SG_GAMMA)
        return [float(x ** (g * (1 + s)) / x ** g - 1) for s in (-0.25, 0.25)]


def steady_targets():
    """s3.5: the intensity whose Eq. 13 target holds the level at each stage (Table 2's gauge)."""
    g = cases.gauge()
    with mp.workdps(50):
        base = mp.mpf(g["base_level"])
        rng = ref.high(g) - base
        level = {**{k: mp.mpf(g[s]) for k, s in STAGES}, "high": ref.high(g)}
        return {k: float(100 * ((v - base) / rng) ** (1 / mp.mpf(ORACLE_SG_GAMMA))) for k, v in level.items()}


def storm_targets(m):
    """The least peak intensity at which a default storm crossing the gauge reaches each stage."""
    g = cases.gauge()
    out = {}
    for key, stage in STAGES:
        if _run(m, cases.storm(m, 100.0)).peak_level < g[stage]:
            out[key] = None
            continue
        lo, hi = 0.0, 100.0
        while hi - lo > 1e-6:
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if _run(m, cases.storm(m, mid)).peak_level >= g[stage] else (mid, hi)
        out[key] = hi
    return out


def _bands(got, stated):
    return all(got.get(k) is not None and round(got[k], 1) == v for k, v in stated.items())


def recession(m):
    """s3.6: every run ends with the gauge within 1% of its rise from base."""
    worst = 0.0
    for s in cases.storms(m):
        for g in cases.gauges():
            r = _run(m, s, g)
            rise = r.peak_level - g["base_level"]
            if rise > 0:
                worst = max(worst, (r.level_timeseries[-1]["level"] - g["base_level"]) / rise)
    return worst


def speed_unread(m):
    """s4.1: changing the storm's speed changes no response."""
    s, g = cases.storm(m, 80.0), cases.gauge(0.1)
    return _run(m, s, g).to_dict() == _run(m, dataclasses.replace(s, speed_kmh=300.0), g).to_dict()


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
    """Every file outside the package that imports it."""
    out = subprocess.run(["git", "grep", "-lE", r"^\s*(from|import)\s+\S*stormgauge", "--", "src", "tools", "scripts"],
                         capture_output=True, text=True, cwd=config.get_project_root()).stdout.split()
    return [f for f in out if not f.startswith(ORACLE_SG_PACKAGE)]


def ellipsoid(pct):
    """s8(5): the sphere's worst error east-west, and north-south, against WGS84 (per cent)."""
    if pct is None:
        return {"east_west": None, "north_south": None, "met": None}
    ew, ns = max(pct, key=abs), pct[1]
    return {"east_west": ew, "north_south": ns,
            "met": round(abs(ew), 2) == ORACLE_SG_ELLIPSOID_STATED["east_west"]
            and round(abs(ns), 2) == ORACLE_SG_ELLIPSOID_STATED["north_south"]}


def assess(m):
    """Each claim as a dict with its figures and ``met``; the sphere's waits for Wolfram."""
    steady, in_storm = steady_targets(), storm_targets(m)
    g50 = gamma_shift(50)
    mid = [abs(x) for i in (40, 50, 60) for x in gamma_shift(i)]
    gaps = {_row(_run(m, cases.storm(m, float(pk)), cases.gauge(off)))["lag"] for (pk, off), _ in ORACLE_SG_PRINTED_T8}
    t, imp, tail = timing(m), importers(), recession(m)
    f = ORACLE_SG_TIMING["factor"]
    return {
        **tables(m),
        "gamma": {"at50": g50, "range": (min(mid), max(mid)),
                  "met": [round(100 * x, 1) for x in g50] == list(ORACLE_SG_GAMMA_STATED["at50"])
                  and (round(100 * min(mid)), round(100 * max(mid))) == ORACLE_SG_GAMMA_STATED["range"]},
        "steady": {**steady, "met": _bands(steady, ORACLE_SG_STEADY_STATED)},
        "storm": {**in_storm, "met": _bands(in_storm, ORACLE_SG_STORM_STATED)},
        "lag": {"gaps": sorted(gaps), "met": gaps == {f"{ORACLE_SG_LAG_STATED_H:.1f}"}},
        "recession": {"worst": tail, "met": tail < 0.01},
        "speed": {"met": speed_unread(m)},
        "timing": {**t, "met": t["per_gauge_ms"] <= f * ORACLE_SG_TIMING["per_gauge_ms"]
                   and t["all_ms"] <= f * ORACLE_SG_TIMING["all_ms"]},
        "lineage": {"importers": imp, "met": not imp},
    }
