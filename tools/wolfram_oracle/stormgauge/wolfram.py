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
"""What Wolfram computes for SG-001, independently of the reference.

The great-circle distance as R times the angle between the two points' unit vectors
(not the haversine); the kernels and the power law from exact inputs; and the whole
response -- track, distance, kernel, Eq. 13, the lag, Eq. 16's rise and fall and the
recession -- written again in the Wolfram Language for three storms. Then the true distance between the UK
pairs on the WGS84 ellipsoid, by GeoDistance, for the document's 0.3% claim (s8(5)).
"""

import mpmath as mp

from config.models import (
    ORACLE_REFERENCE_DPS,
    ORACLE_SG_EARTH_R_KM,
    ORACLE_SG_RECESSION,
    ORACLE_SG_UK_PAIRS,
    ORACLE_WOLFRAM_DIGITS,
)
from tools.wolfram_oracle._wl import rel_err, wl_exact, wl_number, wl_precise
from tools.wolfram_oracle.stormgauge import cases
from tools.wolfram_oracle.stormgauge import reference as ref

_D = ORACLE_WOLFRAM_DIGITS
_KERNEL = {"gaussian": "Exp[-x^2/(2 p^2)]", "exponential": "Exp[-x/p]", "linear": "Max[0, 1 - x/p]"}


def _unit(lat, lon):
    p, l = (f"({wl_precise(x)}) Pi/180" for x in (lat, lon))
    return f"{{Cos[{p}] Cos[{l}], Cos[{p}] Sin[{l}], Sin[{p}]}}"


def _sphere(lon1, lat1, lon2, lat2):
    return f"N[{ORACLE_SG_EARTH_R_KM} VectorAngle[{_unit(lat1, lon1)}, {_unit(lat2, lon2)}], {_D}]"


def _response(track, duration, g, footprint, kind, param, dt, lag, rise, decay):
    """The response in the Wolfram Language: {peak level, accumulation, last level}."""
    w = wl_precise
    pts = "{" + ", ".join("{" + ", ".join(w(v) for v in (t, lon, lat, i)) + "}" for lon, lat, t, i in track) + "}"
    high = g["historical_high"] if g["historical_high"] is not None else None
    hi = w(high) if high is not None else f"(11/10) {w(g['severe_warning'])}"
    dt_, lag_, ris, dec = (wl_exact(x) for x in (dt, lag, rise, decay))
    return (
        f"N[Module[{{tr = {pts}, n, k, at, ints, tg, lv, up, dn, rng}},"
        f" at[t0_] := Module[{{tt = Clip[t0, {{tr[[1, 1]], tr[[-1, 1]]}}], j, a, pt, x, p = {w(param)}}},"
        f"   j = Max[1, Min[Length[tr] - 1, LengthWhile[tr[[All, 1]], # <= tt &]]];"
        f"   a = (tt - tr[[j, 1]])/(tr[[j + 1, 1]] - tr[[j, 1]]);"
        f"   pt = tr[[j]] + a (tr[[j + 1]] - tr[[j]]);"
        f"   x = {ORACLE_SG_EARTH_R_KM} VectorAngle[{_unit(g['latitude'], g['longitude'])},"
        f"     {{Cos[pt[[3]] Pi/180] Cos[pt[[2]] Pi/180], Cos[pt[[3]] Pi/180] Sin[pt[[2]] Pi/180], Sin[pt[[3]] Pi/180]}}]/{w(footprint)};"
        f"   If[t0 > {w(duration)}, 0, pt[[4]] If[x <= 0, 1, {_KERNEL[kind]}]]];"
        f" n = Floor[({w(duration)} + {ORACLE_SG_RECESSION} ({dec}))/({dt_})] + 1; k = Floor[({lag_})/({dt_})];"
        f" ints = Table[at[i ({dt_})], {{i, 0, n - 1}}];"
        f" rng = {hi} - {w(g['base_level'])};"
        f" tg = Table[With[{{v = ints[[Max[1, i - k]]]}}, If[v <= 0, 0, (v/100)^(4/5) rng {w(g['sensitivity'])}]], {{i, 1, n}}];"
        f" up = Min[1, ({dt_})/({ris})]; dn = Min[1, ({dt_})/({dec})];"
        f" lv = {w(g['base_level'])} + Rest[FoldList[#1 + (#2 - #1) If[#2 > #1, up, dn] &, 0, tg]];"
        f" {{Max[lv], ({dt_}) Total[Max[0, # - {w(g['flood_alert'])}] & /@ lv], Last[lv]}}], {_D}]")


def _ref_response(track, duration, g, footprint, kind, param, dt, lag, rise, decay):
    times, ints, levels = ref.response(track, duration, g, footprint, kind, param, dt, lag, rise, decay)
    st = ref.statistics(times, ints, levels, g, dt)
    return [st["peak_level"], st["accumulation"], levels[-1]]


def response_cases(m):
    """Three storms: the default crossing, an exponential beta storm off the track, the irregular one."""
    s1 = cases.storm(m, 100.0)
    s2 = cases.storm(m, 80.0, kernel="exponential", profile="beta")
    s3 = cases.irregular(m, 23.7)
    gs = cases.gauges()
    return [(s1, gs[0], (0.5, 2.0, 1.0, 12.0)), (s2, gs[2], (0.25, 2.0, 1.0, 12.0)), (s3, gs[-1], (1.0, 3.3, 0.5, 6.0))]


def items(m):
    """(id, expression, reference) for every numerical oracle; the reference is None
    where Wolfram's answer is itself the finding."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        return _items(m)


def _items(m):
    out = [(f"sphere/{i}", _sphere(*p), ref.haversine(*p)) for i, p in enumerate(cases.POINTS)]
    for d in (0.5, 3, 20, 40, 80, 200):
        for kind in ref.KERNELS:
            out.append((f"kernel/{kind}/{d}", f"N[With[{{x = {wl_precise(d)}/40, p = 1/2}}, {_KERNEL[kind]}], {_D}]",
                        ref.kernel(d, 40.0, kind, 0.5)))
    g = cases.gauge()
    for i in (0.5, 20, 38.7, 50, 100):
        out.append((f"power/{i}", f"N[({wl_precise(i)}/100)^(4/5) ((11/10) {wl_precise(g['severe_warning'])} - "
                                  f"{wl_precise(g['base_level'])}), {_D}]", ref.contribution(i, g)))
    for j, (s, gg, setting) in enumerate(response_cases(m)):
        args = (cases.track(s), s.duration_hours, gg, s.footprint_km, s.decay_kernel.value, s.decay_parameter,
                *setting)
        out.append((f"response/{j}", _response(*args), _ref_response(*args)))
    for i, (a, b, c, d) in enumerate(ORACLE_SG_UK_PAIRS):
        out.append((f"wgs84/{i}", f"N[QuantityMagnitude[GeoDistance[GeoPosition[{{{wl_precise(a)}, {wl_precise(b)}}}], "
                                  f"GeoPosition[{{{wl_precise(c)}, {wl_precise(d)}}}]], \"Kilometers\"], {_D}]", None))
    return out


def _err(got, want):
    if isinstance(want, list):
        return max(rel_err(a, b) for a, b in zip(got, want))
    return rel_err(got, want)


def judge(m, results):
    """Wolfram's worst disagreement with the reference, and the sphere's error against
    WGS84 for each UK pair (per cent)."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        its = items(m)
        worst = max(_err(wl_number(results[i]), r) for i, _, r in its if r is not None)
        pct = [100 * float(ref.haversine(b, a, d, c) / wl_number(results[f"wgs84/{i}"]) - 1)
               for i, (a, b, c, d) in enumerate(ORACLE_SG_UK_PAIRS)]
    return float(worst), pct
