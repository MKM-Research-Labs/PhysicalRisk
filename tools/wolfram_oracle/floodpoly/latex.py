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
    ORACLE_FPO_EARLY_RISE,
    ORACLE_FPO_ENVELOPE_TOL,
    ORACLE_FPO_FINE_LEVELS,
    ORACLE_FPO_LATE_HOUR,
    ORACLE_FPO_NEAR,
    ORACLE_FPO_TABLE_PREFIX,
    ORACLE_FPO_WOLFRAM_TOL,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files

_TOL = sci(ORACLE_FPO_CODE_TOL)


def _code(label, x):
    return (label, sci(x), _TOL, x <= ORACLE_FPO_CODE_TOL)


def findings(r):
    c = r["code"]
    yes = lambda ok: "yes" if ok else "no"
    out = [_code("Eq.~3: \\texttt{p\\_flood\\_poly} against the reference, worst relative error", c["poly"]),
           ("A threshold at or below zero gives zero", yes(c["zero_threshold"]), "", c["zero_threshold"]),
           ("\\texttt{p\\_flood\\_series} is \\texttt{p\\_flood\\_poly} hour by hour", sci(c["series"]), "0",
            c["series"] == 0),
           _code("\\texttt{p\\_flood\\_simple} is $\\min(1, w/s)$", c["simple"]),
           _code("The model as \\texttt{stress.sensitivity} evaluates it", c["copy"]),
           _code("Its closed-form $\\partial P/\\partial h$, held hours included", c["slope"]),
           ("The server sends the screen the document's coefficients and envelope", yes(c["served"]), "", c["served"]),
           ("The screen carries no coefficients of its own", yes(not c["js_own_coefficients"]), "",
            not c["js_own_coefficients"])]
    if c["js"] is None:
        out.append(("The screen's JavaScript, run under node, against the reference", "not run", _TOL, None))
    else:
        out.append(_code("The screen's JavaScript, run under node, against the reference", c["js"]))
    if r["wolfram"] is None:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_FPO_WOLFRAM_TOL), None))
    else:
        out.append(("Wolfram agrees with the reference (table cells, slopes, minima at their points)",
                    sci(r["wolfram"][0]), sci(ORACLE_FPO_WOLFRAM_TOL), r["wolfram"][0] <= ORACLE_FPO_WOLFRAM_TOL))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "pending" if met is None else ("met" if met else "\\textbf{not met}")


def _range(xs, fmt="{:.3f}"):
    return f"{fmt.format(min(xs))} to {fmt.format(max(xs))}"


def _minima(r):
    if r["wolfram"] is None:
        return None, None
    m = r["wolfram"][1]
    return min(v for k, v in m.items() if k.startswith("free/")), min(v for k, v in m.items() if k.startswith("env/"))


def claim_rows(c, r):
    free, env = _minima(r)
    g, e, f = c["grid"], c["envelope"], c["fit"]
    wolfram = ("not run" if free is None else
               f"smallest $\\partial z/\\partial h$ at any whole hour where it runs free {free:.4f}; "
               f"along the envelope {env:.4f}")
    return [
        ("\\S4.3, Table~2", "the ten terms and coefficients", "the code's, to the printed six decimals",
         _met(c["coeffs"]["met"])),
        ("\\S3.3, Table~1", "the earliest hour any storm reached each level",
         f"the code's knots; recomputed from the catalogue, every knot within {e['worst']:.2f} h "
         f"(limit {ORACLE_FPO_ENVELOPE_TOL}); first level at hour~0 {e['first']:.3f}", _met(e["met"] and e["config"])),
        ("\\S7.1, Table~4", "$P$ by level and hour, held cells marked",
         f"{g['matched']} of {g['of']} cells reproduced by the code; the {g['n_held']} held cells marked as the code holds them"
         if g["held"] else f"{g['matched']} of {g['of']} cells; the held cells differ", _met(g["met"])),
        ("\\S3.2", "$P=1$ at or above severe; constant below the floor",
         "so at every hour", _met(c["step"]["met"])),
        ("\\S3.2", "below the floor, effectively zero", f"at most {c['floor']['value']:.4f}",
         _met(c["floor"]["met"])),
        ("\\S3.4", "rising water never lowers $P$ (the code)",
         f"over {ORACLE_FPO_FINE_LEVELS:,} levels at each of 168 hours, the largest fall is {c['monotone']['drop']:.1e}".replace(",", "{,}"),
         _met(c["monotone"]["met"])),
        ("\\S3.4", "rising water never lowers $P$ (Wolfram, between the fit's grid levels)", wolfram,
         _met(None if free is None else min(free, env) >= 0)),
        ("\\S3.2", f"from hour~{ORACLE_FPO_LATE_HOUR} on $P$ never rises with the hour; "
         f"before it, by at most {ORACLE_FPO_EARLY_RISE}",
         f"largest rise from hour~{ORACLE_FPO_LATE_HOUR} {c['in_time']['late']:.1e}; before it {c['in_time']['early']:.3f}",
         _met(c["in_time"]["met"])),
        ("\\S3.1", "$t\\approx-5.12$ at hour~0", f"{c['t0']['value']:.4f}", _met(c["t0"]["met"])),
        ("\\S5, Table~3", "accuracy on the held-out storms, by gauge",
         f"{f['matched']} of {f['of']} rows reproduced with the document's model, on "
         f"{f['states'][0]:,} fitted and {f['states'][1]:,} held-out states".replace(",", "{,}"), _met(f["met"])),
        ("\\S2.3", "the scenario holds $P=1$ once severe is reached",
         "so the route does" if c["latch"]["met"] else "the route does not", _met(c["latch"]["met"])),
    ]


def _claims_table(c, r):
    return tab("The model document's claims, tested", "tab:bm-claims", "p{20mm}p{44mm}p{72mm}l",
               "Claim & Stated & Benchmark finds & Outcome", claim_rows(c, r))


def _gauge_table(gauges):
    body = [(esc(g["gauge"]), f"{g['near']['n']:,}".replace(",", "{,}"), f"{g['near']['gbm']:.3f}",
             f"{g['near']['poly']:.3f}", f"{g['near']['mae']:.3f}", f"{g['near']['p95']:.3f}",
             f"{100 * g['near']['over']:.0f}\\%", f"{g['below']['mae']:.4f}") for g in gauges]
    return tab(f"The model against each gauge's GBM on every real storm state, near severe "
               f"($w/s\\ge{ORACLE_FPO_NEAR}$) and below it", "tab:bm-gauges", "lrrrrrrr",
               "Gauge & States & GBM & Poly & Mean $|d|$ & 95\\% & $>0.1$ & All below", body)


def macros(provs, r, version, mode, c):
    checks = findings(r)
    failed = sum(ok is False for *_, ok in checks)
    rows = claim_rows(c, r)
    near = [g["near"] for g in r["gauges"]]
    free, env = _minima(r)
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeCommit": f"\\texttt{{{provs[0]['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(version) if version else "not run",
        "bmWolframVia": f" via {mode}" if version else "",
        "bmWolframConfirms": (f"Wolfram, from the exact coefficients and knots, agrees with the reference to "
                              f"{sci(r['wolfram'][0])}." if version else "Wolfram has not been run."),
        "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail") + ("" if version else "; Wolfram pending"),
        "bmClaims": str(len(rows)), "bmClaimsMet": str(sum(row[3] == "met" for row in rows)),
        "bmGauges": str(len(r["gauges"])), "bmNearMae": _range([g["mae"] for g in near]),
        "bmNearOver": _range([100 * g["over"] for g in near], "{:.0f}"),
        "bmNearBias": _range([g["bias"] for g in near], "{:+.3f}"),
        "bmBelowMae": _range([g["below"]["mae"] for g in r["gauges"]], "{:.4f}"),
        "bmGridMatched": str(c["grid"]["matched"]), "bmGridCells": str(c["grid"]["of"]),
        "bmHeld": str(c["grid"]["n_held"]), "bmDrop": f"{c['monotone']['drop']:.1e}",
        "bmEnvWorst": f"{c['envelope']['worst']:.2f}",
        "bmMinFree": "not run" if free is None else f"{free:.4f}",
        "bmMinEnv": "not run" if env is None else f"{env:.4f}",
    })


def write_tables(out, provs, r, version, mode, c):
    return write_files(out, ORACLE_FPO_TABLE_PREFIX, {
        "macros": macros(provs, r, version, mode, c),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{92mm}p{16mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(r))),
        "claims": GENERATED + _claims_table(c, r),
        "gauges": GENERATED + _gauge_table(r["gauges"]),
    })
