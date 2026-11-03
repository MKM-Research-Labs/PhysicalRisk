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
"""LaTeX for the MKM-DD-001 benchmark document, generated from a run."""

from datetime import date

from config.models import (
    ORACLE_DD_CODE_TOL,
    ORACLE_DD_MC_DRAWS,
    ORACLE_DD_TABLE_PREFIX,
    ORACLE_DD_WOLFRAM_TOL,
    ORACLE_DD_Z_LIMIT,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files
from tools.wolfram_oracle.depthdamage.claims import UNREAD

HYDRO_TOL = 1e-4           # the code reports the hydrograph to 4 decimal places
METRE_TOL = 1e-6
COEFF_TOL = 5e-9           # DD_POLY_COEFFS is printed to 8 places
_FAMILIES = (("Eq.~1, the depth-damage curve", "damage"), ("Eq.~3, Manning's velocity", "manning"),
             ("Eq.~4, the ground slope", "slope"), ("Eq.~5, the travel time", "travel"),
             ("Eq.~6, the retention", "attenuation"), ("\\S3.4.2, IDW", "idw"))


def _n(x):
    """A whole number with LaTeX thousands separators."""
    return f"{x:,.0f}".replace(",", "{,}")


def findings(r):
    det = r["det"]
    out = [(f"{label}: code against the reference, worst relative error", sci(det[k]), sci(ORACLE_DD_CODE_TOL),
            det[k] <= ORACLE_DD_CODE_TOL) for label, k in _FAMILIES]
    out += [
        ("Eq.~5: no velocity gives an infinite travel time", "yes" if det["travel_inf"] else "no", "", det["travel_inf"]),
        ("Eq.~8, the haversine: code against the reference, worst error (m)", sci(det["haversine_m"]),
         sci(METRE_TOL), det["haversine_m"] <= METRE_TOL),
        ("Eq.~9, the correlation matrix: worst relative error", sci(r["corr_err"]), sci(ORACLE_DD_CODE_TOL),
         r["corr_err"] <= ORACLE_DD_CODE_TOL),
        ("Eq.~7, the property hydrograph: worst error (m)", sci(r["hydro_err"]), sci(HYDRO_TOL),
         r["hydro_err"] <= HYDRO_TOL),
        (f"Eqs.~10--11: Monte Carlo mean loss ({_n(ORACLE_DD_MC_DRAWS)} draws) against the exact, $|z|$",
         f"{abs(r['mc']['z']):.2f}", f"{ORACLE_DD_Z_LIMIT:g}", abs(r["mc"]["z"]) <= ORACLE_DD_Z_LIMIT),
        ("\\S3.5: the code's ES$_{99}$ against its own draws", sci(r["mc"]["es99_err"]), sci(ORACLE_DD_CODE_TOL),
         r["mc"]["es99_err"] <= ORACLE_DD_CODE_TOL),
    ]
    if r["wolfram"] is None:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_DD_WOLFRAM_TOL), None))
    else:
        worst, gap, _ = r["wolfram"]
        out += [("Wolfram agrees with the reference", sci(worst), sci(ORACLE_DD_WOLFRAM_TOL), worst <= ORACLE_DD_WOLFRAM_TOL),
                ("\\S3.1: the degree-5 curve is the exact least-squares fit to Table~1", sci(gap), sci(COEFF_TOL),
                 gap <= COEFF_TOL)]
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "met" if met else "\\textbf{not met}"


def _of(c):
    return f"{c['matched']} of {c['of']} figures reproduced"


def _claims_table(c, ew):
    ew_text = f"; on WGS84, 0.1$^\\circ$ east--west is {_n(ew)}\\,m, not 11{{,}}100" if ew else ""
    rows = [
        ("Table~4", "the depth-damage curve at 13 depths", _of(c["t4"]), _met(c["t4"]["met"])),
        ("Table~5", "Manning's velocity", _of(c["t5"]), _met(c["t5"]["met"])),
        ("Table~6", "retention by distance and length", _of(c["t6"]), _met(c["t6"]["met"])),
        ("Table~7", "expected loss after a $\\pm$10\\% curve shift, by damage ratio",
         _of(c["t7"]) + " from Eq.~11", _met(c["t7"]["met"])),
        ("Table~8", "velocity and travel time by roughness", _of(c["t8"]), _met(c["t8"]["met"])),
        ("\\S3.3.4, Table~2", f"retention length $\\ell={_n(c['ell']['doc'])}$\\,m",
         f"the code's default is {_n(c['ell']['code'])}\\,m", _met(c["ell"]["met"])),
        ("\\S3.3.4, \\S6.3", "94, 82, 61\\% retained at 0.6, 2, 5\\,km; 0.37, 0.67, 0.82 at 2\\,km",
         "as printed", _met(c["quotes"]["met"])),
        ("\\S3.3.5", "retention is applied once, by the caller, not in the hydrograph",
         f"the code's hydrograph is Eq.~7 without it, to {sci(c['once']['err'])}\\,m", _met(c["once"]["met"])),
        ("\\S3.1, \\S3.2", "the property-type factors and 25\\,km radius are unread",
         ", ".join(f"\\texttt{{{esc(k)}}}" for k in c["unread"]["unread"]) + " never read in \\texttt{src}",
         _met(c["unread"]["met"])),
        ("\\S3.4.3, \\S8(7)", "1$^\\circ\\approx$111\\,km overstates east--west distance by 61\\% at 51.5$^\\circ$N",
         f"{100 * c['deg']['error']:.1f}\\%{ew_text}", _met(c["deg"]["met"])),
        ("\\S3.4.3", "the correlation matrix is positive definite",
         f"smallest eigenvalue {c['psd']['min_eig']:.3f}", _met(c["psd"]["met"])),
        ("\\S3.5", "shocks drawn by SVD", "NumPy's legacy draws equal the SVD factor's exactly",
         _met(c["svd"]["met"])),
        ("\\S3.5", "HHI $=1/N$ for an equal portfolio", f"{c['hhi']['value']:.4f} for $N=40$", _met(c["hhi"]["met"])),
        ("Q3", "800\\,MB for 10{,}000 properties", f"{_n(c['memory']['bytes'] / 1e6)}\\,MB", _met(c["memory"]["met"])),
        ("\\S3.1", "degree-5 curve: $R^2$ 0.999244, RMSE 0.009368, largest error 0.020388, increasing",
         f"{c['poly']['r2']:.6f}, {c['poly']['rmse']:.6f}, {c['poly']['max_err']:.6f}; least slope "
         f"{c['poly']['slope_min']:.3f}", _met(c["poly"]["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{22mm}p{50mm}p{64mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows)


def macros(provs, r, version, mode, c):
    checks = findings(r)
    failed = sum(ok is False for *_, ok in checks)
    worst = r["wolfram"][0] if r["wolfram"] else None
    claims = [v for v in c.values()]
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
        "bmCodeErr": sci(max(r["det"][k] for _, k in _FAMILIES)), "bmZ": f"{abs(r['mc']['z']):.2f}",
        "bmClaims": str(len(claims)), "bmClaimsMet": str(sum(bool(v["met"]) for v in claims)),
        "bmFigures": str(sum(c[k]["of"] for k in ("t4", "t5", "t6", "t7", "t8"))),
    })


def write_tables(out, provs, r, version, mode, c):
    ew = r["wolfram"][2] if r["wolfram"] else None
    return write_files(out, ORACLE_DD_TABLE_PREFIX, {
        "macros": macros(provs, r, version, mode, c),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{92mm}p{16mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(r))),
        "claims": GENERATED + _claims_table(c, ew),
    })
