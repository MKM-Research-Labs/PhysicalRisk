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

"""LaTeX for the MKM-EF-001 benchmark document, generated from a run."""

from datetime import date

from config.models import (
    ORACLE_EF_LL_TOL,
    ORACLE_EF_OPERATING_MIN_X,
    ORACLE_EF_PVALUE_TOL,
    ORACLE_EF_REL_TOL,
    ORACLE_EF_TABLE_PREFIX,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files
from tools.wolfram_oracle.frequency.claims import assess, operating

_GROUPS = (
    ("annual", f"Annual probability $1-e^{{-\\lambda p}}$, $\\lambda p\\ge{ORACLE_EF_OPERATING_MIN_X:g}$", ORACLE_EF_REL_TOL),
    ("rate", "Aggregate rate $\\lambda p$", ORACLE_EF_REL_TOL),
    ("term", "Tenor probability $1-e^{-p\\sum\\lambda_y}$", ORACLE_EF_REL_TOL),
    ("aal", "Compound-Poisson average annual loss", ORACLE_EF_REL_TOL),
    ("aal_se", "Its standard error over $n$ years", ORACLE_EF_REL_TOL),
    ("disp_stat", "Dispersion statistic $(n-1)s^2/\\bar x$", ORACLE_EF_REL_TOL),
    ("p_over", "Over-dispersion $p$-value ($\\chi^2$ survival)", ORACLE_EF_PVALUE_TOL),
    ("p_under", "Under-dispersion $p$-value ($\\chi^2$ CDF)", ORACLE_EF_PVALUE_TOL),
    ("pois_ll", "Poisson log-likelihood", ORACLE_EF_REL_TOL),
    ("nb_ll", "Negative Binomial log-likelihood at its maximum", ORACLE_EF_LL_TOL),
)


def _worst(rows, group, key="rel_err"):
    return max((r[key] for r in rows if r["group"] == group and key in r), default=0.0)


def findings(rows, version):
    judged = operating(rows)
    out = [(label + ": model vs reference", sci(_worst(judged, g)), sci(tol), _worst(judged, g) <= tol)
           for g, label, tol in _GROUPS]
    if version:
        ref = max(r["wolfram_vs_ref"] for r in rows if "wolfram_vs_ref" in r)
        gain = max(r["wolfram_ll_gain"] for r in rows if "wolfram_ll_gain" in r)
        out += [("Wolfram agrees with the reference (closed forms, $\\chi^2$, Poisson)", sci(ref),
                 sci(ORACLE_EF_REL_TOL), ref <= ORACLE_EF_REL_TOL),
                ("Wolfram's own Negative Binomial maximum finds no higher likelihood",
                 sci(max(gain, 0.0)), sci(ORACLE_EF_LL_TOL), gain <= ORACLE_EF_LL_TOL)]
    else:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_EF_REL_TOL), None))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "finding" if met is None else ("met" if met else "\\textbf{not met}")


def _claims_table(c):
    eq4, z, samp, term, prec, nb = c
    scaled = ", ".join(f"{100 * s:.2f}\\%" for _, _, s in samp["scaled"])
    rows = [
        ("\\S5.9 closed form", "$E[(1-p)^N]=e^{-\\lambda p}$; aggregate $\\ge$ occurrence",
         ("identity confirmed symbolically; " if eq4["identity"] else "identity not run; ")
         + ("aggregate $\\ge$ occurrence in every case" if eq4["aggregate_ge_occurrence"] else "violated"),
         _met(eq4["met"])),
        ("\\S5.9 gate statistic", f"mean $|z|=\\sqrt{{2/\\pi}}={z['stated']}$", f"${z['exact']:.6f}$",
         _met(z["met"])),
        ("\\S7.2 sampling error", "5, 1.6, 0.5, 0.16\\% at $10^3$..$10^6$ years",
         f"$1/\\sqrt n$ from the first gives {scaled}", _met(samp["met"])),
        ("Term structure (annualise, gev)", "annual probability used as the per-year hazard",
         f"tenor probability understated by {100 * -term['low']:.2f}--{100 * -term['high']:.1f}\\%",
         _met(term["met"])),
        ("Annualisation precision", "$1-\\exp(-x)$",
         f"{sci(prec['worst'])} relative below $\\lambda p={prec['below']:g}$; $-\\mathrm{{expm1}}(-x)$ is exact",
         _met(prec["met"])),
        ("Negative Binomial search", "bounded scalar search on $\\alpha$",
         f"log-likelihood within {sci(nb['worst'])} of the maximum", _met(nb["met"])),
    ]
    return tab("The model document's claims, and the code's own conventions, tested", "tab:bm-claims",
               "p{36mm}p{44mm}p{56mm}l", "Claim & Stated & Benchmark finds & Outcome", rows)


def _term_table(rows):
    body = [(r["id"].split("/")[1].split(",")[0], f"{r['lam']:g}", f"{r['p']:g}", str(r["T"]),
             f"{float(r['ref']):.6f}", f"{float(r['convention']):.6f}", f"{100 * r['convention_gap']:+.2f}\\%")
            for r in rows if r["group"] == "term" and r["T"] in (1, 10)]
    return tab("The multi-year exceedance probability: exact against the per-year-hazard convention",
               "tab:bm-term", "lrrrrrr", "Rate & $\\lambda_0$ & $p$ & $T$ & Exact & Convention & Gap", body)


def macros(provs, rows, version, mode, wl):
    checks = findings(rows, version)
    failed = sum(ok is False for *_, ok in checks)
    c = assess(rows, wl)
    agree = (sci(max(r["wolfram_vs_ref"] for r in rows if "wolfram_vs_ref" in r)) if version else None)
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeCommit": f"\\texttt{{{provs[0]['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(version) if version else "not run",
        "bmWolframVia": f" via {mode}" if version else "",
        "bmWolframConfirms": (f"Wolfram and the 50-digit reference agree to {agree}, so the reference is "
                              "confirmed by a second, independent implementation." if version else
                              "Wolfram has not been run, so the reference rests on one implementation."),
        "bmCases": str(len(rows)), "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail") + ("" if version else "; Wolfram pending"),
        "bmTermLow": f"{100 * -c[3]['low']:.2f}", "bmTermHigh": f"{100 * -c[3]['high']:.1f}",
        "bmPrecision": sci(c[4]["worst"]), "bmPrecisionBelow": f"{c[4]['below']:g}",
        "bmNbGap": sci(c[5]["worst"]), "bmImpliedP": f"{c[2]['implied_p']:.2f}",
        "bmOperating": f"{ORACLE_EF_OPERATING_MIN_X:g}",
    })


def write_tables(out, provs, rows, version, mode, wl):
    return write_files(out, ORACLE_EF_TABLE_PREFIX, {
        "macros": macros(provs, rows, version, mode, wl),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{88mm}p{22mm}rl",
                                    "Check & Result & Tolerance & Outcome", _render(findings(rows, version))),
        "claims": GENERATED + _claims_table(assess(rows, wl)),
        "term": GENERATED + _term_table(rows),
    })
