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
"""LaTeX for the MKM-SP-001 benchmark document, generated from a run."""

from datetime import date

from config.models import (
    ORACLE_SP_CODE_TOL,
    ORACLE_SP_METRE_TOL,
    ORACLE_SP_SUFFICIENT_PCT,
    ORACLE_SP_TABLE_PREFIX,
    ORACLE_SP_WOLFRAM_TOL,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files
from tools.wolfram_oracle.spatial.claims import ellipsoid

_FAMILIES = (("Eq.~1, IDW from distances, seven powers", "idw"),
             ("\\S3.1, IDW from coordinates: WSE as depth plus elevation, Eq.~2's distance", "wse"),
             ("The correlation, against the 111\\,km-a-degree convention it follows", "corr_degrees"))


def findings(r):
    det, proj = r["det"], r["proj"]
    out = [("Eq.~2, the haversine: code against the reference, worst error (m)", sci(det["haversine_m"]),
            sci(ORACLE_SP_METRE_TOL), det["haversine_m"] <= ORACLE_SP_METRE_TOL)]
    out += [(f"{label}: worst relative error", sci(det[k]), sci(ORACLE_SP_CODE_TOL), det[k] <= ORACLE_SP_CODE_TOL)
            for label, k in _FAMILIES]
    out += [
        ("Eq.~3, the correlation as the document states it: worst relative error", sci(det["corr_doc"]),
         sci(ORACLE_SP_CODE_TOL), det["corr_doc"] <= ORACLE_SP_CODE_TOL),
        (f"The polyline projection picks the reference's segment ({proj['polyline_points']} points): segments that differ",
         str(proj["polyline_segments_off"]), "0", proj["polyline_segments_off"] == 0),
    ]
    if r["wolfram"] is None:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_SP_WOLFRAM_TOL), None))
    else:
        out.append(("Wolfram agrees with the reference", sci(r["wolfram"][0]), sci(ORACLE_SP_WOLFRAM_TOL),
                    r["wolfram"][0] <= ORACLE_SP_WOLFRAM_TOL))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "\\textbf{pending}" if met is None else ("met" if met else "\\textbf{not met}")


def _of(c):
    return f"{c['matched']} of {c['of']} figures reproduced"


def _files(fs):
    return ", ".join(f"\\texttt{{{esc(f)}}}" for f in fs)


def _claims_table(c, sphere):
    tr, fe, lin = c["tree"], c["flat_earth"], c["lineage"]["users"]
    # src/models/<area>/... or src/port/src/<area>/...
    shared = sorted({f.split("/")[3] if f.startswith("src/port/src/") else f.split("/")[2]
                     for k in ("haversine_distance", "nearest_point_on_polyline", "nearest_point_on_segment")
                     for f in lin[k]})
    pending = sphere["worst"] is None
    rows = [
        ("Table~1", "WSE by IDW power", _of(c["t1"]), _met(c["t1"]["met"])),
        ("Table~2", "WSE by distance of the nearest gauge", _of(c["t2"]), _met(c["t2"]["met"])),
        ("Table~2", "the gauge varied is the nearest", f"in {c['t2_label']['nearest']} of {c['t2_label']['of']} rows; "
         "at 5{,}000 and 10{,}000\\,m the 2{,}000\\,m gauge is nearer", _met(c["t2_label"]["met"])),
        ("Table~3", "WSE by number of gauges", _of(c["t3"]), _met(c["t3"]["met"])),
        ("\\S3.1, \\S4.1", "the power and the 1\\,m threshold are inputs",
         "fixed at 2 and 1\\,m where gauges are given by coordinates; inputs only where they are given "
         "by distance", _met(c["configurable"]["met"])),
        ("\\S3.3", "the KDTree answers nearest-neighbour queries",
         f"it measures degrees of latitude and longitude alike, and names the wrong gauge in {tr['wrong']} of "
         f"{tr['queries']} queries, up to {100 * tr['worst_excess']:.0f}\\% farther; in the case built for it, "
         f"the gauge {tr['distances_m'][0]:.0f}\\,m away over one {tr['distances_m'][1]:.0f}\\,m away",
         _met(tr["met"])),
        ("\\S3.4, Eq.~3", "correlation decays with the distance $d$ of Eq.~1",
         f"the code converts Euclidean degrees at 111\\,km a degree; up to {100 * c['correlation']['err']:.0f}\\% off "
         "Eq.~3 east--west", _met(c["correlation"]["met"])),
        ("\\S4.2", "it returns the nearest gauge's distance and identity",
         "no function returns a gauge", _met(c["outputs"]["met"])),
        ("\\S5.1(2)", f"the haversine is sufficient below 100\\,km (judged: within {ORACLE_SP_SUFFICIENT_PCT}\\% of WGS84)",
         "Wolfram not run" if pending else f"worst {sphere['worst']:+.2f}\\%", _met(sphere["sufficient"])),
        ("Q2", "the haversine is exact for the Earth's geometry",
         "Wolfram not run" if pending else f"a sphere: {sphere['worst']:+.2f}\\% from WGS84", _met(sphere["exact"])),
        ("\\S5.2(3)", f"the flat-Earth projection errs beyond {fe['km']}\\,km",
         f"worst {100 * fe['near']:.4f}\\% within {fe['km']}\\,km; {100 * fe['far']:.3f}\\% "
         f"({fe['far_m']:.0f}\\,m) at 200\\,km", _met(fe["met"])),
        ("\\S1, \\S2.1, Q1", "it maps gauge readings to properties by IDW, its exclusive use",
         "nothing in \\texttt{src} or \\texttt{scripts} calls the interpolation, the index or the correlation; "
         f"the haversine and projection serve the {', '.join(esc(s) for s in shared)} code", _met(c["lineage"]["met"])),
        ("Q4", "unit tests verify KDTree correctness", "no test queries the tree", _met(c["unit_tests"]["met"])),
        ("Q5", "outcomes are validated against held-out gauge readings",
         "no code calls the interpolation to compare it with anything", _met(c["validation"]["met"])),
        ("Q7", "IDW is compared against kriging and nearest-neighbour baselines",
         "kriging appears nowhere in the repository" if not c["kriging"]["files"] else _files(c["kriging"]["files"]),
         _met(c["kriging"]["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{20mm}p{50mm}p{66mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows)


def _mets(c, sphere):
    keys = ("t1", "t2", "t2_label", "t3", "configurable", "tree", "correlation", "outputs", "flat_earth",
            "lineage", "unit_tests", "validation", "kriging")
    return [c[k]["met"] for k in keys] + [sphere["sufficient"], sphere["exact"]]


def macros(provs, r, version, mode, c, sphere):
    checks = findings(r)
    failed = sum(ok is False for *_, ok in checks)
    worst = r["wolfram"][0] if r["wolfram"] else None
    mets = _mets(c, sphere)
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
        "bmCorrErr": f"{100 * r['det']['corr_doc']:.0f}\\%",
        "bmTreeWrong": str(c["tree"]["wrong"]), "bmTreeQueries": str(c["tree"]["queries"]),
        "bmClaims": str(len(mets)), "bmClaimsMet": str(sum(m is True for m in mets)),
        "bmClaimsFailed": str(sum(m is False for m in mets)),
        "bmFigures": str(sum(c[k]["of"] for k in ("t1", "t2", "t3"))),
    })


def write_tables(out, provs, r, version, mode, c):
    sphere = ellipsoid(r["wolfram"][1] if r["wolfram"] else None)
    return write_files(out, ORACLE_SP_TABLE_PREFIX, {
        "macros": macros(provs, r, version, mode, c, sphere),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{96mm}p{16mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(r))),
        "claims": GENERATED + _claims_table(c, sphere),
    })
