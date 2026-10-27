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

"""LaTeX for the MKM-MP-001 benchmark document, generated from a run."""

from datetime import date

from config.models import ORACLE_MP_REL_TOL, ORACLE_MP_TABLE_PREFIX
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files
from tools.wolfram_oracle.mortgage.claims import assess

_GROUPS = (("payment", "Monthly payment (Eq.~1)"), ("spread", "Credit spread (Eqs.~6--13)"),
           ("pv_cf", "PV of expected cashflows (Eqs.~19, 22)"),
           ("pv_el", "PV of expected losses (Eqs.~20, 23)"), ("fv", "Fair value (Eq.~24)"))


def _gbp(x):
    return f"{x:,.0f}".replace(",", "{,}")


def findings(rows, version):
    out = [(f"{label}: model vs document", sci(max(r[f"{g}_rel_err"] for r in rows)),
            sci(ORACLE_MP_REL_TOL), max(r[f"{g}_rel_err"] for r in rows) <= ORACLE_MP_REL_TOL)
           for g, label in _GROUPS]
    if version:
        ref = max(max(r["wolfram_fv_vs_ref"], r["wolfram_path_vs_ref"]) for r in rows)
        out.append(("Wolfram agrees with the reference (fair value and pathwise value)", sci(ref),
                    sci(ORACLE_MP_REL_TOL), ref <= ORACLE_MP_REL_TOL))
    else:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_MP_REL_TOL), None))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "finding" if met is None else ("met" if met else "\\textbf{not met}")


def _claims_table(c):
    dc, rec, t7, pay, zero, bound, par, disc = c
    rows = [
        ("\\S1, Eqs.~19, 24", "fair value is the PV of expected cashflows net of expected losses",
         f"the loss is deducted twice: fair value understated by up to {100 * dc['worst']:.1f}\\% of par",
         _met(dc["met"])),
        ("Eq.~19 recovery", "$B_{i-1}-\\mathrm{LGD}_i$",
         f"exceeds the recoverable value by a month's principal; up to {100 * rec['worst']:.2f}\\% of par",
         _met(rec["met"])),
        ("\\S6, Table~7", "spread and value by flood category",
         "reproduced to the figures quoted" + ("; no loss given default at the baseline" if t7["lgd_free"] else ""),
         _met(t7["met"])),
        ("\\S6.1", "$+100$\\,bp raises the 25-year payment 6--8\\%",
         f"{100 * pay['low']:.1f}--{100 * pay['high']:.1f}\\% over rates of 2--9\\%", _met(pay["met"])),
        ("\\S3.2.4", "zero income gives a 15\\% spread",
         f"income is floored at GBP~1 first; the spread is {100 * zero['got']:.2f}\\%", _met(zero["met"])),
        ("\\S7.2.2", "$\\sum_i \\mathrm{EL}_i\\le B_0$", f"at most {100 * bound['worst']:.1f}\\% of $B_0$",
         _met(bound["met"])),
        ("\\S5.3, \\S7.2.1", "at the contractual rate the payments are worth par",
         "identity proved symbolically" if par["identity"] else "identity not run", _met(par["met"])),
        ("\\S3.8", "discount at the contractual rate",
         f"production discounts at the risk-free rate; fair value moves up to {100 * disc['worst']:.0f}\\%",
         _met(disc["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{26mm}p{48mm}p{62mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows)


def _double_table(rows):
    pick = [r for r in rows if r["discount_rate"] is None and r["interest_rate"] == 0.06
            and r["original_maturity"] == 25 and r["current_term"] == 25 and r["recovery_haircut"] > 0
            and r["loan_amount"] >= 240_000]
    body = [(f"{r['loan_amount'] / r['property_value']:.2f}", f"{r['recovery_haircut']:.2f}",
             _gbp(r["gross_annual_income"]), f"{100 * float(r['spread_ref']):.2f}",
             _gbp(float(r["fv_ref"])), _gbp(float(r["pathwise"])),
             _gbp(float(r["pv_el_ref"])), f"{100 * r['double_count']:.1f}\\%") for r in pick]
    return tab("The document's fair value against the pathwise value: GBP~300k property, 6\\% coupon, "
               "25 years, discounted at the coupon", "tab:bm-double", "rrrrrrrr",
               "LTV & $\\delta$ & Income & $s$ (\\%) & Eq.~24 & Pathwise & Twice-counted & of par", body)


def macros(provs, rows, version, mode, c):
    checks = findings(rows, version)
    failed = sum(ok is False for *_, ok in checks)
    dc = c[0]
    agree = sci(max(max(r["wolfram_fv_vs_ref"], r["wolfram_path_vs_ref"]) for r in rows)) if version else None
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeCommit": f"\\texttt{{{provs[0]['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(version) if version else "not run",
        "bmWolframVia": f" via {mode}" if version else "",
        "bmWolframConfirms": (f"Wolfram and the 50-digit reference agree to {agree} on both values."
                              if version else "Wolfram has not been run."),
        "bmCases": str(len(rows)), "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail") + ("" if version else "; Wolfram pending"),
        "bmCodeErr": sci(max(r["fv_rel_err"] for r in rows)),
        "bmDoubleWorst": f"{100 * dc['worst']:.1f}", "bmDoubleShare": f"{100 * dc['share']:.0f}",
        "bmWorstLoan": _gbp(dc["loan"]), "bmWorstFv": _gbp(dc["fv"]), "bmWorstPath": _gbp(dc["pathwise"]),
        "bmExcess": f"{100 * c[1]['worst']:.2f}",
        "bmPayLow": f"{100 * c[3]['low']:.1f}", "bmPayHigh": f"{100 * c[3]['high']:.1f}",
        "bmZeroIncome": f"{100 * c[4]['got']:.2f}", "bmDiscount": f"{100 * c[7]['worst']:.0f}",
    })


def write_tables(out, provs, rows, version, mode, pricer, wl):
    c = assess(rows, pricer, wl)
    return write_files(out, ORACLE_MP_TABLE_PREFIX, {
        "macros": macros(provs, rows, version, mode, c),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{88mm}p{22mm}rl",
                                    "Check & Result & Tolerance & Outcome", _render(findings(rows, version))),
        "claims": GENERATED + _claims_table(c),
        "double": GENERATED + _double_table(rows),
    })
