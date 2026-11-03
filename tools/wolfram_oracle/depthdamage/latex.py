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
    ORACLE_DD_PRINTED_T8,
    ORACLE_DD_PRINTED_T9,
    ORACLE_DD_TABLE_PREFIX,
    ORACLE_DD_TABLE9,
    ORACLE_DD_WOLFRAM_TOL,
    ORACLE_DD_Z_LIMIT,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files

# Checks: (label, result key, limit, how the result prints).
HYDRO_TOL = 1e-4           # the code reports the hydrograph to 4 decimal places
METRE_TOL = 1e-6
COEFF_TOL = 5e-9           # DD_POLY_COEFFS is printed to 8 places
_FAMILIES = (("Eq.~1, the depth-damage curve", "damage"), ("Eq.~11, Manning's velocity", "manning"),
             ("Eq.~12, the ground slope", "slope"), ("Eq.~13, the travel time", "travel"),
             ("Eq.~14, the attenuation", "attenuation"), ("Eq.~8, IDW", "idw"))


def findings(r):
    det = r["det"]
    out = [(f"{label}: code against the reference, worst relative error", sci(det[k]), sci(ORACLE_DD_CODE_TOL),
            det[k] <= ORACLE_DD_CODE_TOL) for label, k in _FAMILIES]
    out += [
        ("Eq.~13: no velocity gives an infinite travel time", "yes" if det["travel_inf"] else "no", "", det["travel_inf"]),
        ("Eq.~7, the haversine: code against the reference, worst error (m)", sci(det["haversine_m"]),
         sci(METRE_TOL), det["haversine_m"] <= METRE_TOL),
        ("Eq.~10, the correlation matrix: worst relative error", sci(r["corr_err"]), sci(ORACLE_DD_CODE_TOL),
         r["corr_err"] <= ORACLE_DD_CODE_TOL),
        ("Eqs.~15--17, the hydrograph without $a$: worst error (m)", sci(r["hydro_err"]), sci(HYDRO_TOL),
         r["hydro_err"] <= HYDRO_TOL),
        (f"Eq.~18--19: Monte Carlo mean loss ({_n(ORACLE_DD_MC_DRAWS)} draws) against the exact, $|z|$",
         f"{abs(r['mc']['z']):.2f}", f"{ORACLE_DD_Z_LIMIT:g}", abs(r["mc"]["z"]) <= ORACLE_DD_Z_LIMIT),
        ("Eq.~21: the code's ES$_{99}$ against its own draws", sci(r["mc"]["es99_err"]), sci(ORACLE_DD_CODE_TOL),
         r["mc"]["es99_err"] <= ORACLE_DD_CODE_TOL),
    ]
    if r["wolfram"] is None:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_DD_WOLFRAM_TOL), None))
    else:
        worst, gap, _ = r["wolfram"]
        out += [("Wolfram agrees with the reference", sci(worst), sci(ORACLE_DD_WOLFRAM_TOL), worst <= ORACLE_DD_WOLFRAM_TOL),
                ("The code's degree-5 curve is the exact least-squares fit to Table~1", sci(gap), sci(COEFF_TOL),
                 gap <= COEFF_TOL)]
    return out


def _n(x):
    """A whole number with LaTeX thousands separators."""
    return f"{x:,.0f}".replace(",", "{,}")


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "finding" if met is None else ("met" if met else "\\textbf{not met}")


def _claims_table(c, ew):
    t9, t8 = c["t9"], c["t8"]
    ew_m = _n(ew) if ew else ""
    ew_text = f"; on WGS84, 0.1$^\\circ$ is {ew_m}\\,m, not 11{{,}}100" if ew else ""
    rows = [
        ("Table~5", "depth-damage curve, 13 depths", f"{c['t5']['matched']} of {c['t5']['of']} figures reproduced",
         _met(c["t5"]["met"])),
        ("Table~6", "Manning's velocity", f"{c['t6']['matched']} of {c['t6']['of']}", _met(c["t6"]["met"])),
        ("Table~7", "attenuation", f"{c['t7']['matched']} of {c['t7']['of']}", _met(c["t7"]["met"])),
        ("\\S3.3.4, Table~10", "$e^{-1}\\approx0.37$, $e^{-3}\\approx0.05$; 0.14, 0.37, 0.67", "as printed",
         _met(c["s334"]["met"] and c["t10"]["met"])),
        ("Table~9", "velocity " + "/".join(f"{v:.2f}" for v in ORACLE_DD_PRINTED_T9["velocity"]) + " m/s at "
         f"$d={ORACLE_DD_TABLE9['depth']:g}$, $S={ORACLE_DD_TABLE9['slope']:g}$",
         "Eq.~11 gives " + "/".join(f"{v:.2f}" for v in t9["eq11"]) + "; the travel times imply "
         f"{_n(min(t9['implied_m']))}--{_n(max(t9['implied_m']))}\\,m at the printed speeds",
         _met(t9["met"])),
        ("Table~8, \\S1, Q9", f"a $\\pm$10\\% curve shift moves expected loss {ORACLE_DD_PRINTED_T8['el'][0]:.2f}$\\times$"
         f"/{ORACLE_DD_PRINTED_T8['el'][1]:.2f}$\\times$, tail risk $\\pm$8\\%",
         f"exactly 1.10$\\times$ wherever the clip does not bind (to {c['t8']['single'][1]:.3f} at "
         f"$\\delta=0.6$, {c['t8']['single'][2]:.3f} at 0.9); {t8['el'][0]:.3f}/{t8['el'][1]:.3f} and VaR$_{{99}}$ "
         f"+{100 * t8['var99']:.1f}\\% on the benchmark portfolio: a property of the portfolio, not the model",
         _met(t8["met"])),
        ("\\S8(8)", "1$^\\circ\\approx$111\\,km is about 2\\% out east--west at 51.5$^\\circ$N",
         f"{100 * c['s8']['error']:.1f}\\% ($1/\\cos 51.5^\\circ - 1$){ew_text}", _met(c["s8"]["met"])),
        ("\\S3.3.4, Table~2", f"attenuation length $\\ell={_n(c['ell']['doc'])}$\\,m",
         f"the code's default is {_n(c['ell']['code'])}\\,m, its docstring says 3{{,}}000",
         _met(c["ell"]["met"])),
        ("Eqs.~2, 4--6", "property-type factor; depth from the Thames point with linear decay",
         "not in the code: " + ", ".join(f"\\texttt{{{esc(k)}}}" for k in c["eq2"]["unused"]) + " are never read",
         _met(c["eq2"]["met"])),
        ("Eq.~15", "the hydrograph scales by the attenuation $a$",
         f"the code does not (the caller does); applied as written, peak depth falls by up to "
         f"{c['eq15']['depth_gap']:.1f}\\,m", _met(c["eq15"]["met"])),
        ("\\S3.2.4, \\S5.4", "the correlation matrix is positive definite",
         f"smallest eigenvalue {c['psd']['min_eig']:.3f}", _met(c["psd"]["met"])),
        ("\\S7.4, \\S9.3", "correlated shocks by Cholesky", "NumPy's \\texttt{multivariate\\_normal} factorises by SVD",
         _met(c["cholesky"]["met"])),
        ("\\S3.4.3", "HHI $=1/N$ for an equal portfolio", f"{c['hhi']['value']:.4f} for $N=40$", _met(c["hhi"]["met"])),
        ("\\S9.3", "about 800\\,MB for 10{,}000 properties", f"{_n(c['memory']['bytes'] / 1e6)}\\,MB",
         _met(c["memory"]["met"])),
        ("config", "the undocumented degree-5 curve: $R^2$ 0.999244, RMSE 0.009368, max error 0.020388, monotone",
         f"{c['poly']['r2']:.6f}, {c['poly']['rmse']:.6f}, {c['poly']['max_err']:.6f}; least slope "
         f"{c['poly']['slope_min']:.3f}", _met(c["poly"]["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{22mm}p{44mm}p{70mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows)


def macros(provs, r, version, mode, c):
    checks = findings(r)
    failed = sum(ok is False for *_, ok in checks)
    worst = r["wolfram"][0] if r["wolfram"] else None
    code_worst = max(r["det"][k] for _, k in _FAMILIES)
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
        "bmCodeErr": sci(code_worst), "bmZ": f"{abs(r['mc']['z']):.2f}",
        "bmVelocity": "/".join(f"{v:.2f}" for v in c["t9"]["eq11"]),
        "bmShift": f"{c['t8']['el'][0]:.3f}", "bmDegErr": f"{100 * c['s8']['error']:.0f}",
        "bmEll": _n(c["ell"]["code"]), "bmDepthGap": f"{c['eq15']['depth_gap']:.1f}",
    })


def write_tables(out, provs, r, version, mode, c):
    ew = r["wolfram"][2] if r["wolfram"] else None
    return write_files(out, ORACLE_DD_TABLE_PREFIX, {
        "macros": macros(provs, r, version, mode, c),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{92mm}p{16mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(r))),
        "claims": GENERATED + _claims_table(c, ew),
    })
