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
"""LaTeX for the MKM-SG-001 benchmark document, generated from a run."""

from datetime import date

from config.models import (
    ORACLE_SG_CODE_TOL,
    ORACLE_SG_ELLIPSOID_PCT,
    ORACLE_SG_METRE_TOL,
    ORACLE_SG_TABLE_PREFIX,
    ORACLE_SG_WOLFRAM_TOL,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files

_FAMILIES = (("Eqs.~7--10, the decay kernels", "kernel"),
             ("Eqs.~3--6 and 11, the intensity at the gauge", "intensity"),
             ("Eqs.~12--13, the intensity-to-level power law", "level"))


def findings(r):
    det, resp = r["det"], r["resp"]
    out = [("Eqs.~1--2, the haversine: code against the reference, worst error (m)", sci(det["haversine_m"]),
            sci(ORACLE_SG_METRE_TOL), det["haversine_m"] <= ORACLE_SG_METRE_TOL)]
    out += [(f"{label}: code against the reference, worst relative error", sci(det[k]), sci(ORACLE_SG_CODE_TOL),
             det[k] <= ORACLE_SG_CODE_TOL) for label, k in _FAMILIES]
    out += [
        (f"Eqs.~14--16, the response over {resp['cases']} runs: worst level error (m)", sci(resp["level_m"]),
         sci(ORACLE_SG_METRE_TOL), resp["level_m"] <= ORACLE_SG_METRE_TOL),
        ("\\S3.7, peak level, peak intensity and accumulation (Eq.~18): worst relative error",
         sci(resp["stats"]), sci(ORACLE_SG_CODE_TOL), resp["stats"] <= ORACLE_SG_CODE_TOL),
        ("\\S3.7, peak times and durations (Eq.~17): statistics that differ", str(resp["mismatches"]), "0",
         resp["mismatches"] == 0),
    ]
    if r["wolfram"] is None:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_SG_WOLFRAM_TOL), None))
    else:
        out.append(("Wolfram agrees with the reference", sci(r["wolfram"][0]), sci(ORACLE_SG_WOLFRAM_TOL),
                    r["wolfram"][0] <= ORACLE_SG_WOLFRAM_TOL))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "\\textbf{pending}" if met is None else ("met" if met else "\\textbf{not met}")


def _of(c):
    return f"{c['matched']} of {c['of']} figures reproduced"


def _pct(x, sign=True):
    return f"{100 * x:+.1f}\\%" if sign else f"{100 * x:.1f}\\%"


def _at(x):
    return "never, even at 100" if x is None else f"{x:.1f}"


def _wgs84(pct):
    if pct is None:
        return "Wolfram not run", None
    worst = max(abs(p) for p in pct)
    return (f"{min(pct):+.2f}\\% to {max(pct):+.2f}\\% against \\texttt{{GeoDistance}} on WGS84",
            worst < ORACLE_SG_ELLIPSOID_PCT)


def _claims_table(c, pct):
    st, sm, d, du = c["steady"], c["storm"], c["decay"], c["duration"]
    g50, (glo, ghi) = c["gamma"]["at50"], c["gamma"]["range"]
    wtext, wmet = _wgs84(pct)
    imp = c["lineage"]["importers"]
    rows = [
        ("\\S3.3.1", "Gaussian: 60.7\\% of on-track intensity at $\\tilde d=\\sigma$, 13.5\\% at $2\\sigma$",
         "as printed", _met(c["gauss"]["met"])),
        ("Table~4", "decay by kernel and distance", _of(c["t4"]), _met(c["t4"]["met"])),
        ("Table~5", "contribution by intensity and scale factor", _of(c["t5"]), _met(c["t5"]["met"])),
        ("Table~6", "$k(1.0)$ for each kernel", _of(c["t6"]), _met(c["t6"]["met"])),
        ("Table~7", "$(1/2)^\\gamma$ for four exponents", _of(c["t7"]), _met(c["t7"]["met"])),
        ("Tables~1, 5", "the scale factor and the storm's speed are model inputs",
         "changing either changes nothing; Table~5's six rows are identical"
         if c["unread"]["scale"] and c["unread"]["speed"] else
         f"scale {'unread' if c['unread']['scale'] else 'read'}, speed {'unread' if c['unread']['speed'] else 'read'}",
         _met(c["unread"]["met"])),
        ("\\S6.2", "$\\pm$25\\% in $\\gamma$ moves a mid-range contribution by 20--25\\%",
         f"{_pct(g50[0])} and {_pct(g50[1])} at $I=50$; {_pct(glo, False)}--{_pct(ghi, False)} over $I=40$--60",
         _met(c["gamma"]["met"])),
        ("\\S3.5", "the level reaches alert at $I\\approx40$, warning at 60--70, severe at 85+, the high at 100",
         f"Eq.~13's target does: at {st['alert']:.1f}, {st['warning']:.1f}, {st['severe']:.1f} and {st['high']:.0f}",
         _met(st["met"])),
        ("\\S3.5", "\\ldots and so does a storm of that intensity",
         f"a default storm crossing the gauge reaches alert at peak {_at(sm['alert'])}, warning at "
         f"{_at(sm['warning'])}, severe {_at(sm['severe'])}", _met(sm["met"])),
        ("\\S3.7, \\S7.1", "peak level follows peak intensity by about $\\tau_{\\mathrm{lag}}=2$\\,h",
         f"by {c['lag']['gaps'][0]:.1f} to {c['lag']['gaps'][1]:.1f}\\,h", _met(c["lag"]["met"])),
        ("\\S6.3", "doubling $\\tau_{\\mathrm{decay}}$ roughly doubles the time above alert; peak barely moves",
         f"{d['dur']:.1f}\\,h becomes {d['dur_slow']:.1f}\\,h; the peak moves {_pct(d['peak_change'])}",
         _met(d["met"])),
        ("\\S6.3", "a longer $\\tau_{\\mathrm{lag}}$ moves the timing, not the peak",
         f"doubled, the peak moves {_pct(c['lagpeak']['change'])} and {c['lagpeak']['shift']:+.1f}\\,h",
         _met(c["lagpeak"]["met"])),
        ("\\S3.7", "durations are the total time above each stage",
         f"the run stops at the storm's end, the level still {du['end_rise']:.2f}\\,m up "
         f"({_pct(du['end_share'], False)} of its rise); run on, {du['dur']:.1f}\\,h above alert becomes "
         f"{du['dur_72']:.1f}\\,h", _met(du["met"])),
        ("\\S8(5)", "the sphere is within 0.3\\% of the ellipsoid at UK scale", wtext, _met(wmet)),
        ("Q3", "under 10\\,ms a gauge; 25 gauges under 250\\,ms",
         f"{c['timing']['per_gauge_ms']:.1f}\\,ms; {c['timing']['all_ms']:.0f}\\,ms", _met(c["timing"]["met"])),
        ("\\S2.2, Q5, Q6", "its responses fill \\texttt{gaugets/} and feed the hazard curves, MKM-PF-001 and MKM-TS-001",
         ("imported by " + ", ".join(f"\\texttt{{{esc(f)}}}" for f in imp)) if imp
         else "nothing in \\texttt{src}, \\texttt{tools} or \\texttt{scripts} imports it",
         _met(c["lineage"]["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{20mm}p{52mm}p{64mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows), wmet


def macros(provs, r, version, mode, c, wmet):
    checks = findings(r)
    failed = sum(ok is False for *_, ok in checks)
    worst = r["wolfram"][0] if r["wolfram"] else None
    mets = [v["met"] for v in c.values()] + [wmet]
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeCommit": f"\\texttt{{{provs[0]['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(version) if version else "not run",
        "bmWolframVia": f" via {mode}" if version else "",
        "bmWolframConfirms": (f"Wolfram, computing each independently, agrees with the reference to {sci(worst)}."
                              if version else "Wolfram has not been run."),
        "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail") + ("" if version else "; Wolfram pending"),
        "bmCodeErr": sci(max(r["det"][k] for _, k in _FAMILIES)),
        "bmLevelErr": sci(max(r["resp"]["level_m"], r["det"]["haversine_m"])),
        "bmRuns": str(r["resp"]["cases"]),
        "bmClaims": str(len(mets)), "bmClaimsMet": str(sum(m is True for m in mets)),
        "bmFigures": str(sum(c[k]["of"] for k in ("t4", "t5", "t6", "t7"))),
    })


def write_tables(out, provs, r, version, mode, c):
    claims, wmet = _claims_table(c, r["wolfram"][1] if r["wolfram"] else None)
    return write_files(out, ORACLE_SG_TABLE_PREFIX, {
        "macros": macros(provs, r, version, mode, c, wmet),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{96mm}p{16mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(r))),
        "claims": GENERATED + claims,
    })
