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
"""SG-001's code against its document, case by case.

Each family calls the production function and the 50-digit reference with the same
inputs; the largest relative error (absolute where the answer is zero, metres for
distances and levels) is the family's result; a value too small for a double is judged
absolutely, since the code can only return 0. The response family also counts the
statistics that are not equal outright: the times of the peaks and the durations,
which are whole numbers of steps.
"""

import importlib
import sys
from datetime import datetime

import mpmath as mp

from config.models import (
    ORACLE_SG_ALERT,
    ORACLE_SG_DURATIONS,
    ORACLE_SG_GAUGE,
    ORACLE_SG_MODULES,
    ORACLE_SG_OFFSETS_DEG,
    ORACLE_SG_PEAKS,
    ORACLE_SG_SETTINGS,
    ORACLE_SG_STAGES,
    ORACLE_SG_TRACK,
    ORACLE_SG_UK_PAIRS,
)
from tools.wolfram_oracle._wl import rel_err
from tools.wolfram_oracle.stormgauge import reference as ref

START = datetime(2026, 1, 1)
# (lon1, lat1, lon2, lat2): the UK pairs, a metre apart, one degree, and across the dateline.
POINTS = tuple((b, a, d, c) for a, b, c, d in ORACLE_SG_UK_PAIRS) + (
    (-0.1, 51.5, -0.1, 51.50001), (-1.0, 51.4, -1.0, 52.4), (179.9, 51.5, -179.9, 51.5))
# A track that starts late, ends early and turns: (lon, lat, t, I).
IRREGULAR = ((-0.9, 51.3, 2.0, 10.0), (-0.6, 51.45, 5.0, 45.0), (-0.45, 51.5, 5.5, 70.0),
             (-0.2, 51.6, 11.0, 95.0), (0.3, 51.55, 20.0, 15.0))


def load():
    return {k: importlib.import_module(m) for k, m in ORACLE_SG_MODULES.items()}


def gauge(offset=0.0, alert=ORACLE_SG_ALERT, high=None, sensitivity=1.0):
    """A gauge with Table 2's default stages, ``offset`` degrees north of the track."""
    s = ORACLE_SG_STAGES
    return {"gauge_id": f"G{offset}", "gauge_name": "gauge", "longitude": ORACLE_SG_GAUGE[0],
            "latitude": ORACLE_SG_GAUGE[1] + offset, "base_level": s["base"] * alert,
            "flood_alert": alert, "flood_warning": s["warning"] * alert,
            "severe_warning": s["severe"] * alert, "historical_high": high, "sensitivity": sensitivity}


def gauges():
    return [gauge(o) for o in ORACLE_SG_OFFSETS_DEG] + [gauge(0.05, 3.2, 7.5, 1.3)]


def config(m, g):
    return m["data"].GaugeConfig(**g)


def storm(m, peak=100.0, kernel="gaussian", profile="triangular", duration=24.0, param=0.5):
    d = m["data"]
    return m["factory"].create_storm(ORACLE_SG_TRACK[0], ORACLE_SG_TRACK[1], storm_id="S", start_time=START,
                                     peak_intensity=peak, duration_hours=duration,
                                     decay_kernel=d.DecayKernel(kernel), decay_parameter=param,
                                     intensity_profile=d.IntensityProfile(profile))


def irregular(m, duration=24.0):
    d = m["data"]
    return d.Storm(storm_id="IRR", name="irregular", start_time=START, duration_hours=duration,
                   track=[d.TrackPoint(*p) for p in IRREGULAR], peak_intensity=95.0, footprint_km=55.0,
                   decay_kernel=d.DecayKernel.EXPONENTIAL, decay_parameter=0.7)


def storms(m, duration=24.0):
    out = [storm(m, peak=p, duration=duration) for p in ORACLE_SG_PEAKS]
    out += [storm(m, kernel=k, profile=p, duration=duration, param=0.8 if k == "linear" else 0.5)
            for k in ref.KERNELS for p in ("triangular", "gaussian", "beta") if (k, p) != ("gaussian", "triangular")]
    return out + [irregular(m, duration)]


def track(s):
    return [(p.longitude, p.latitude, p.time_hours, p.intensity) for p in s.track]


def _err(a, b):
    """Relative error; absolute where the answer underflows a double, which rounds it to 0."""
    return float(abs(mp.mpf(a) - b)) if abs(b) < sys.float_info.min else rel_err(a, b)


def _worst(pairs):
    return max(_err(a, b) for a, b in pairs)


def deterministic(m):
    """Each closed-form family's worst error, code against reference."""
    model = m["model"].StormGaugeModel()
    kern = m["data"].DecayKernel
    dists = (-5, 0, 1e-9, 3, 20, 40, 80, 200, 1000)
    grid = [(d, f, k, p) for d in dists for f in (40.0, 100.0) for k in ref.KERNELS for p in (0.25, 0.5, 1.0)]
    times = (-1.0, 0.0, 0.3, 1.0, 11.99, 12.0, 12.01, 23.9, 24.0, 30.0)
    gs = gauges()
    out = {
        "haversine_m": max(float(abs(model.haversine_km(*p) - ref.haversine(*p))) * 1000 for p in POINTS),
        "kernel": _worst((model.compute_decay(d, f, kern(k), p), ref.kernel(d, f, k, p)) for d, f, k, p in grid),
        "intensity": _worst((model.compute_intensity_at_gauge(t, g["longitude"], g["latitude"], s),
                             ref.intensity_at(track(s), t, g["longitude"], g["latitude"], s.footprint_km,
                                              s.decay_kernel.value, s.decay_parameter, s.duration_hours))
                            for s in storms(m) for g in gs for t in times),
        "level": _worst((model.intensity_to_level(i, config(m, g)), ref.contribution(i, g))
                        for i in (-5, 0, 1e-6, 0.5, 20, 38.7, 50, 99.9, 100, 120) for g in gs),
    }
    return out


def _compare(m, s, g, dt, lag, rise, decay):
    r = m["model"].StormGaugeModel(time_resolution_hours=dt, response_lag_hours=lag, response_rise_hours=rise,
                                   response_decay_hours=decay).compute_response(s, config(m, g))
    times, ints, levels = ref.response(track(s), s.duration_hours, g, s.footprint_km, s.decay_kernel.value,
                                       s.decay_parameter, dt, lag, rise, decay)
    st = ref.statistics(times, ints, levels, g, dt)
    lv = max(float(abs(p["level"] - w)) for p, w in zip(r.level_timeseries, levels))
    stats = max(rel_err(r.peak_level, st["peak_level"]), rel_err(r.accumulation, st["accumulation"]),
                rel_err(r.peak_intensity, st["peak_intensity"]))
    exact = [(r.peak_time_hours, st["peak_time"]), (r.peak_intensity_time_hours, st["peak_intensity_time"]),
             (r.duration_above_alert, st["duration_alert"]), (r.duration_above_warning, st["duration_warning"]),
             (r.duration_above_severe, st["duration_severe"]), (len(r.level_timeseries), len(levels))]
    return lv, stats, sum(mp.mpf(a) != mp.mpf(b) for a, b in exact)


def responses(m):
    """Eqs. 14-18 over every storm, gauge, setting and duration: the worst level error
    (m), the worst statistic, and how many exact statistics differ."""
    lv = stats = 0.0
    off = cases = 0
    for duration in ORACLE_SG_DURATIONS:
        for s in storms(m, duration):
            for g in gauges():
                for setting in ORACLE_SG_SETTINGS:
                    a, b, c = _compare(m, s, g, *setting)
                    lv, stats, off, cases = max(lv, a), max(stats, b), off + c, cases + 1
    return {"level_m": lv, "stats": stats, "mismatches": off, "cases": cases}
