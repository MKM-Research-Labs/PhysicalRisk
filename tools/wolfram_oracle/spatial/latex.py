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

"""LaTeX for the MKM-SP-001 benchmark document, generated from a run."""

from datetime import date

from config.models import (
    ORACLE_SP_CODE_TOL,
    ORACLE_SP_METRE_TOL,
    ORACLE_SP_NEAREST_TOL,
    ORACLE_SP_TABLE_PREFIX,
    ORACLE_SP_WOLFRAM_TOL,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files
from tools.wolfram_oracle.spatial.claims import RETAINED, ellipsoid

_FAMILIES = (("Eq.~2, IDW from distances, seven powers", "idw"),
             ("\\S3.2, IDW from coordinates: WSE as depth plus elevation, Eq.~1's distance", "wse"),
             ("Eq.~3, the correlation at 111\\,km a degree", "corr_degrees"))


def findings(r):
    det, proj, tree = r["det"], r["proj"], r["tree"]
    out = [("Eq.~1, the haversine: code against the reference, worst error (m)", sci(det["haversine_m"]),
            sci(ORACLE_SP_METRE_TOL), det["haversine_m"] <= ORACLE_SP_METRE_TOL)]
    out += [(f"{label}: worst relative error", sci(det[k]), sci(ORACLE_SP_CODE_TOL), det[k] <= ORACLE_SP_CODE_TOL)
            for label, k in _FAMILIES]
    out += [
        (f"\\S3.3, the index over {tree['queries']} queries: nearest gauges that differ from Eq.~1's",
         str(tree["wrong"]), "0", tree["wrong"] == 0),
        ("\\S3.3, the index's distance: worst relative error", sci(tree["distance_err"]), sci(ORACLE_SP_NEAREST_TOL),
         tree["distance_err"] <= ORACLE_SP_NEAREST_TOL),
        (f"\\S3.5, the polyline projection picks the reference's segment ({proj['polyline_points']} points): "
         "segments that differ", str(proj["polyline_segments_off"]), "0", proj["polyline_segments_off"] == 0),
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
    ix, lin = c["index"], c["lineage"]
    retained = sorted({f for k in RETAINED for f in lin["users"][k]})
    rows = [
        ("Table~2", "WSE by IDW power", _of(c["t1"]), _met(c["t1"]["met"])),
        ("Table~3", "WSE by distance of the first gauge", _of(c["t2"]), _met(c["t2"]["met"])),
        ("Table~4", "WSE by number of gauges", _of(c["t3"]), _met(c["t3"]["met"])),
        ("Table~5", "the projection's worst error by distance from the line", _of(c["t4"]), _met(c["t4"]["met"])),
        ("\\S3.2", "both interpolation paths take the power and the threshold",
         "both do" if c["configurable"]["met"] else "one does not", _met(c["configurable"]["met"])),
        ("\\S3.2", "with no gauges, the interpolation returns 0", "both paths do" if c["empty"]["met"]
         else "not so", _met(c["empty"]["met"])),
        ("\\S3.3, \\S4.2", "the index returns the nearest gauge by Eq.~1, and its distance",
         f"{ix['queries'] - ix['wrong']} of {ix['queries']} queries; distance to {sci(ix['distance_err'])}; "
         f"the gauge {ix['distances_m'][1]:.0f}\\,m away over one {ix['distances_m'][0]:.0f}\\,m away",
         _met(ix["met"] and c["outputs"]["met"])),
        ("\\S3.4", "the correlation converts degrees at 111\\,km, overstating east--west separation by "
         "61\\% at 51.5$^\\circ$N", f"exact to {sci(c['correlation']['err'])}; {c['correlation']['ew']:.1f}\\%",
         _met(c["correlation"]["met"])),
        ("\\S5", "the sphere errs by up to 0.32\\% against WGS84 for UK pairs under 100\\,km",
         "Wolfram not run" if sphere["met"] is None else f"worst {sphere['worst']:+.2f}\\%", _met(sphere["met"])),
        ("\\S2.2, Table~1", "nothing calls the interpolation, the index or the correlation; the haversine and "
         "projection serve the gauge, property and seismic code",
         ("called by " + _files(retained)) if not lin["met"] else f"so: {', '.join(lin['areas'])}", _met(lin["met"])),
        ("Q4", "the unit tests query the index", "they do" if c["unit_tests"]["met"] else "they do not",
         _met(c["unit_tests"]["met"])),
        ("Q5", "nothing validates the interpolation against observations",
         "no code calls it" if c["validation"]["met"] else "called by " + _files(c["validation"]["callers"]),
         _met(c["validation"]["met"])),
        ("Q7", "nothing compares it with kriging", "kriging appears nowhere in the repository"
         if c["kriging"]["met"] else _files(c["kriging"]["files"]), _met(c["kriging"]["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{20mm}p{56mm}p{60mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows)


def _mets(c, sphere):
    return [v["met"] for k, v in c.items() if k != "outputs"] + [sphere["met"]]


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
        "bmHavErr": sci(r["det"]["haversine_m"]),
        "bmTreeWrong": str(c["index"]["wrong"]), "bmTreeQueries": str(c["index"]["queries"]),
        "bmClaims": str(len(mets)), "bmClaimsMet": str(sum(m is True for m in mets)),
        "bmClaimsFailed": str(sum(m is False for m in mets)),
        "bmFigures": str(sum(c[k]["of"] for k in ("t1", "t2", "t3", "t4"))),
    })


def write_tables(out, provs, r, version, mode, c):
    sphere = ellipsoid(r["wolfram"][1] if r["wolfram"] else None)
    return write_files(out, ORACLE_SP_TABLE_PREFIX, {
        "macros": macros(provs, r, version, mode, c, sphere),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{96mm}p{16mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(r))),
        "claims": GENERATED + _claims_table(c, sphere),
    })
