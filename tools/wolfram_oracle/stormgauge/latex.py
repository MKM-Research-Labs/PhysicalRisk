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
    ORACLE_SG_METRE_TOL,
    ORACLE_SG_TABLE_PREFIX,
    ORACLE_SG_WOLFRAM_TOL,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files
from tools.wolfram_oracle.stormgauge.claims import ellipsoid

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
        (f"Eqs.~14--16, the response and its recession over {resp['cases']} runs: worst level error (m)", sci(resp["level_m"]),
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


def _pct(x):
    return f"{100 * x:+.1f}\\%"


def _bands(b):
    return ", ".join("never" if b[k] is None else f"{b[k]:.1f}" for k in ("alert", "warning", "severe"))


def _claims_table(c, sphere):
    st, sm, g = c["steady"], c["storm"], c["gamma"]
    sph = (f"{sphere['east_west']:+.2f}\\% east--west, {sphere['north_south']:+.2f}\\% north--south"
           if sphere["met"] is not None else "Wolfram not run")
    imp = c["lineage"]["importers"]
    rows = [
        ("\\S3.3.1", "Gaussian: 60.7\\% of on-track intensity at $\\tilde d=\\sigma$, 13.5\\% at $2\\sigma$",
         "as printed", _met(c["gauss"]["met"])),
        ("Table~4", "decay by kernel and distance", _of(c["t4"]), _met(c["t4"]["met"])),
        ("Table~5", "the target by intensity and gauge sensitivity", _of(c["t5"]), _met(c["t5"]["met"])),
        ("Table~6", "$k(1.0)$ for each kernel", _of(c["t6"]), _met(c["t6"]["met"])),
        ("Table~7", "$(1/2)^\\gamma$ for four exponents", _of(c["t7"]), _met(c["t7"]["met"])),
        ("Table~8", "a default storm by peak and gauge: peaks, lag, durations, accumulation", _of(c["t8"]),
         _met(c["t8"]["met"])),
        ("Table~9", "the time constants on the peak-100 storm", _of(c["t9"]), _met(c["t9"]["met"])),
        ("\\S6.2", "$\\pm$25\\% in $\\gamma$: +14.9\\% and $-$12.9\\% at $I=50$; 10--20\\% over $I=40$--60",
         f"{_pct(g['at50'][0])} and {_pct(g['at50'][1])}; {100 * g['range'][0]:.1f}--{100 * g['range'][1]:.1f}\\%",
         _met(g["met"])),
        ("\\S3.5", "the target reaches alert, warning, severe at $I=38.7$, 64.7, 86.0; the high at 100",
         f"{_bands(st)}; {st['high']:.1f}", _met(st["met"])),
        ("\\S3.5", "a default storm crossing the gauge reaches them at peaks 40.9, 68.3, 90.7",
         _bands(sm), _met(sm["met"])),
        ("\\S3.6, \\S6.3", "peak level follows peak intensity by 2.5\\,h in every case of Table~8",
         ", ".join(f"{x}\\,h" for x in c["lag"]["gaps"]), _met(c["lag"]["met"])),
        ("\\S3.6", "the run ends with the gauge back within 1\\% of its rise",
         f"worst {100 * c['recession']['worst']:.2f}\\% over every storm and gauge", _met(c["recession"]["met"])),
        ("\\S4.1", "the storm's speed is not read", "changing it changes no response" if c["speed"]["met"]
         else "it changes the response", _met(c["speed"]["met"])),
        ("\\S8(5)", "the sphere errs by 0.32\\% east--west and 0.06\\% north--south in the UK",
         sph, _met(sphere["met"])),
        ("Q3", "0.3\\,ms a gauge and 8\\,ms for 25 (to within a factor of 3)",
         f"{c['timing']['per_gauge_ms']:.2f}\\,ms; {c['timing']['all_ms']:.1f}\\,ms", _met(c["timing"]["met"])),
        ("\\S2.2, Q5, Q6", "nothing in the platform imports the model",
         ("imported by " + ", ".join(f"\\texttt{{{esc(f)}}}" for f in imp)) if imp
         else "nothing in \\texttt{src}, \\texttt{tools} or \\texttt{scripts} does", _met(c["lineage"]["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{20mm}p{56mm}p{60mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows)


def macros(provs, r, version, mode, c, sphere):
    checks = findings(r)
    failed = sum(ok is False for *_, ok in checks)
    worst = r["wolfram"][0] if r["wolfram"] else None
    mets = [v["met"] for v in c.values()] + [sphere["met"]]
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
        "bmLevelErr": sci(r["resp"]["level_m"]),
        "bmRuns": str(r["resp"]["cases"]),
        "bmClaims": str(len(mets)), "bmClaimsMet": str(sum(m is True for m in mets)),
        "bmFigures": str(sum(c[k]["of"] for k in ("gauss", "t4", "t5", "t6", "t7", "t8", "t9"))),
    })


def write_tables(out, provs, r, version, mode, c):
    sphere = ellipsoid(r["wolfram"][1] if r["wolfram"] else None)
    return write_files(out, ORACLE_SG_TABLE_PREFIX, {
        "macros": macros(provs, r, version, mode, c, sphere),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{96mm}p{16mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(r))),
        "claims": GENERATED + _claims_table(c, sphere),
    })
