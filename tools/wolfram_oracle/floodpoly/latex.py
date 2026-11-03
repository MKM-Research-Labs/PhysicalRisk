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
"""LaTeX for the MKM-FPO-001 benchmark document, generated from a run."""

from datetime import date

from config.models import (
    ORACLE_FPO_CODE_TOL,
    ORACLE_FPO_NEAR,
    ORACLE_FPO_PRINTED_FIT,
    ORACLE_FPO_TABLE_PREFIX,
    ORACLE_FPO_WOLFRAM_TOL,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files


def findings(r):
    c = r["code"]
    out = [("Eqs.~1--4: \\texttt{p\\_flood\\_poly} against the reference, worst relative error", sci(c["poly"]),
            sci(ORACLE_FPO_CODE_TOL), c["poly"] <= ORACLE_FPO_CODE_TOL),
           ("A threshold at or below zero gives zero", "yes" if c["zero_threshold"] else "no", "", c["zero_threshold"]),
           ("\\texttt{p\\_flood\\_series} is \\texttt{p\\_flood\\_poly} hour by hour", sci(c["series"]), "0",
            c["series"] == 0),
           ("\\S5.2: \\texttt{p\\_flood\\_simple} is $\\min(1, w/s)$", sci(c["simple"]), sci(ORACLE_FPO_CODE_TOL),
            c["simple"] <= ORACLE_FPO_CODE_TOL),
           ("The copy in \\texttt{stress.sensitivity}, worst relative error", sci(c["copy"]), sci(ORACLE_FPO_CODE_TOL),
            c["copy"] <= ORACLE_FPO_CODE_TOL),
           ("Its closed-form $\\partial P/\\partial h$, worst relative error", sci(c["slope"]), sci(ORACLE_FPO_CODE_TOL),
            c["slope"] <= ORACLE_FPO_CODE_TOL),
           ("The port stress screen's JavaScript coefficients are the document's", "yes" if c["js"] else "no", "",
            c["js"])]
    if r["wolfram"] is None:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_FPO_WOLFRAM_TOL), None))
    else:
        out.append(("Wolfram agrees with the reference (Table~1 cells, $P=\\tfrac12$ levels, slopes)",
                    sci(r["wolfram"][0]), sci(ORACLE_FPO_WOLFRAM_TOL), r["wolfram"][0] <= ORACLE_FPO_WOLFRAM_TOL))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "finding" if met is None else ("met" if met else "\\textbf{not met}")


def _range(xs, fmt="{:.3f}"):
    return f"{fmt.format(min(xs))} to {fmt.format(max(xs))}"


def _claims_table(c, half):
    fit = c["fit"]
    rows = [
        ("\\S8, Table~1", "$P$ by level and hour, $s=6.58$\\,m",
         f"{c['t1']['matched']} of {c['t1']['of']} cells reproduced by the code", _met(c["t1"]["met"])),
        ("\\S8, Table~2", "GBM and polynomial at six points",
         f"polynomial column {c['t2']['matched']} of 6; GBM column {c['t2']['gbm_matched']} of 6 (rate of rise zero)",
         _met(c["t2"]["met"])),
        ("\\S8", "at the severe level, 0.42 at hour~0 rising to 0.97 at hour~167",
         f"{c['at_severe']['code'][0]:.2f} at hour~0, {c['at_severe']['code'][1]:.2f} at hour~167", _met(c["at_severe"]["met"])),
        ("\\S8", "$|\\text{poly}-\\text{GBM}|<0.05$ across the surface",
         f"near severe, 95th percentile up to {c['delta']['near_p95']:.2f}; above 0.05 in up to "
         f"{100 * c['delta']['share']:.0f}\\% of states", _met(c["delta"]["met"])),
        ("\\S4.2", f"$R^2$ {ORACLE_FPO_PRINTED_FIT['r2']}, MAE {ORACLE_FPO_PRINTED_FIT['mae']}, "
         f"RMSE {ORACLE_FPO_PRINTED_FIT['rmse']} against the GBM",
         f"{fit['r2']:.4f}, {fit['mae']:.4f}, {fit['rmse']:.4f} on all {fit['n']:,} real states".replace(",", "{,}"),
         _met(fit["met"])),
        ("\\S9.1", "a cubic kernel reaches $R^2\\approx0.97$",
         "not computed" if c["cubic"]["r2"] is None else f"{c['cubic']['r2']:.4f} on the same states",
         _met(c["cubic"]["met"])),
        ("\\S4.2", "mildly conservative: over-predicts near severe",
         f"bias near severe {_range(c['conservative']['bias'], '{:+.3f}')} across gauges", _met(c["conservative"]["met"])),
        ("\\S3.2", "$t\\approx-5.1$ at hour~0", f"{c['t0']['value']:.4f}", _met(c["t0"]["met"])),
        ("---", "rising water raises $P$",
         "at hour~24, $P$ passes $\\tfrac12$ at " + " and ".join(f"{100 * x:.0f}\\%" for x in half.get(24, []))
         + " of severe: it falls as the water rises between them", _met(None)),
        ("\\S5", "the scenario uses $P$ as given",
         "the stress route latches $P=1$ once the level reaches severe; undocumented", _met(c["latch"]["met"])),
        ("\\S5.2", "\\texttt{p\\_flood\\_simple} for portfolio stress",
         "$\\min(1,w/s)$ is a ratio, not a probability, and it sets portfolio stress P\\&L", _met(c["simple"]["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{18mm}p{46mm}p{72mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows)


def _gauge_table(gauges):
    body = [(esc(g["gauge"]), f"{g['near']['n']:,}".replace(",", "{,}"), f"{g['near']['gbm']:.3f}",
             f"{g['near']['poly']:.3f}", f"{g['near']['mae']:.3f}", f"{g['near']['p95']:.3f}",
             f"{100 * g['near']['over']:.0f}\\%", f"{g['below']['mae']:.4f}") for g in gauges]
    return tab(f"The polynomial against each gauge's GBM on real storm states, near severe "
               f"($w/s\\ge{ORACLE_FPO_NEAR}$) and below it", "tab:bm-gauges", "lrrrrrrr",
               "Gauge & States & GBM & Poly & Mean $|d|$ & 95\\% & $>0.1$ & All below", body)


def macros(provs, r, version, mode, c):
    checks = findings(r)
    failed = sum(ok is False for *_, ok in checks)
    near = [g["near"] for g in r["gauges"]]
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeCommit": f"\\texttt{{{provs[0]['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(version) if version else "not run",
        "bmWolframVia": f" via {mode}" if version else "",
        "bmWolframConfirms": (f"Wolfram, from the exact coefficients, agrees with the reference to {sci(r['wolfram'][0])}."
                              if version else "Wolfram has not been run."),
        "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail") + ("" if version else "; Wolfram pending"),
        "bmGauges": str(len(r["gauges"])), "bmNearMae": _range([g["mae"] for g in near]),
        "bmNearOver": _range([100 * g["over"] for g in near], "{:.0f}"),
        "bmNearBias": _range([g["bias"] for g in near], "{:+.3f}"),
        "bmBelowMae": _range([g["below"]["mae"] for g in r["gauges"]], "{:.4f}"),
        "bmTableOne": str(c["t1"]["matched"]),
        "bmFitRsq": f"{c['fit']['r2']:.3f}", "bmFitMae": f"{c['fit']['mae']:.4f}",
    })


def write_tables(out, provs, r, version, mode, c):
    half = r["wolfram"][1] if r["wolfram"] else {}
    return write_files(out, ORACLE_FPO_TABLE_PREFIX, {
        "macros": macros(provs, r, version, mode, c),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{92mm}p{16mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(r))),
        "claims": GENERATED + _claims_table(c, half),
        "gauges": GENERATED + _gauge_table(r["gauges"]),
    })
