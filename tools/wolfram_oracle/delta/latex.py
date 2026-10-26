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

"""LaTeX for the MKM-DE-001 benchmark document, generated from a run.

The document (``MKM-DE-001_wolfram_benchmark.tex``) is hand-written on the house
template; every figure it quotes from a run comes through here as a macro or an
``evidence_tables_*`` file it inputs, so the PDF and the CSV always agree.
"""

from datetime import date

from config.models import (
    ORACLE_DE_ANNUITY_TOL,
    ORACLE_DE_CLAIM_MOVE,
    ORACLE_DE_CLAIM_YIELD_SHIFT,
    ORACLE_DE_NOTIONAL,
    ORACLE_DE_RATES,
    ORACLE_DE_ROUNDING,
    ORACLE_DE_TABLE_PREFIX,
    ORACLE_DE_TABLE_TENOR,
    ORACLE_DE_TENORS,
    ORACLE_DE_TRADE_SPREAD_BPS,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files
from tools.wolfram_oracle.delta.claims import assess, by_rate

_ROUNDED = (("delta_spread_bps", "Spread change $\\Delta s$ (bp, to $10^{-4}$)"),
            ("dv01_gbp", "FS01 (GBP, to the penny)"),
            ("risky_annuity", "Risky annuity as returned (to $10^{-6}$)"),
            ("mtm", "Mark-to-market (GBP, to the penny)"))


def findings(rows, wolfram_version, claim_err):
    """Checks as (check, result, tolerance, ok) -- ok None for a check not judged."""
    ann = max(r["annuity_rel_err"] for r in rows)
    out = [("Risky annuity, unrounded (s3.1)", sci(ann), sci(ORACLE_DE_ANNUITY_TOL),
            ann <= ORACLE_DE_ANNUITY_TOL)]
    for key, label in _ROUNDED:
        worst, half = max(r[f"{key}_err"] for r in rows), ORACLE_DE_ROUNDING[key] / 2
        out.append((label + ": model vs reference", sci(worst), sci(half), worst <= half))
    if wolfram_version:
        ref = max(max(r["wolfram_annuity_vs_ref"], r["wolfram_ds_vs_ref"], r["wolfram_gradient_vs_ref"])
                  for r in rows)
        out.append(("Wolfram agrees with the reference: annuity, $\\Delta s$, gradient",
                    sci(ref), sci(ORACLE_DE_ANNUITY_TOL), ref <= ORACLE_DE_ANNUITY_TOL))
        out.append(("Wolfram agrees with the reference: claims (annuity, FS01)", sci(claim_err),
                    sci(ORACLE_DE_ANNUITY_TOL), claim_err <= ORACLE_DE_ANNUITY_TOL))
    else:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_DE_ANNUITY_TOL), None))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "finding" if met is None else ("met" if met else "\\textbf{not met}")


def _claims_table(c):
    fd, lin, ten, yld, hand, cvx, floor, basis = c
    rows = [
        ("s6 item 5: 1\\,bp bump error", "$<0.01$\\,bp vs analytical gradient",
         f"{sci(fd['worst'])}\\,bp at most", _met(fd["met"])),
        ("s6 item 1: FS01 against $h$", "``scales approximately linearly'', 50--500\\,bp",
         f"FS01(500)/FS01(50) $= {lin['ratio']:.2f}$, not 10", _met(lin["met"])),
        ("s6 item 2: tenor", f"5Y $\\approx {ten['stated']}\\times$ 1Y", f"${ten['ratio']:.2f}\\times$",
         _met(ten["met"])),
        ("s6 item 3: yields $+100$\\,bp", "FS01 changes 3--5\\%",
         f"FS01 {yld['sign']} {100 * yld['low']:.1f}--{100 * yld['high']:.1f}\\%", _met(yld["met"])),
        ("s7.2 hand calculation", f"$A\\approx{hand['stated']}$", f"$A={hand['exact']:.6f}$",
         _met(hand["met"])),
        ("s8 item 1: 50\\,bp move", "FS01$\\times\\Delta h$ differs from revaluation",
         f"by {100 * cvx['rel']:.2f}\\%", _met(cvx["met"])),
        ("Spread floor (2\\,bp)", "not stated",
         f"at $h={floor['h']:g}$: $\\Delta s={floor['model']}$\\,bp vs gradient {floor['gradient']:.3f}\\,bp",
         _met(floor["met"])),
        ("s3.5 basis delta", "$\\approx$ gauge delta",
         "identical in every case: the basis argument is unused" if basis["identical"] else "differs",
         _met(basis["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{38mm}p{40mm}p{56mm}l",
               "Claim & Document says & Benchmark finds & Outcome", rows)


def _fs01_table(rows):
    head = "$h$ & " + " & ".join(f"{t}Y" for t in ORACLE_DE_TENORS)
    body = [[f"{r[0]:g}"] + [f"{v:,.0f}".replace(",", "{,}") for v in r[1:]] for r in by_rate(rows)]
    return tab(f"FS01 in GBP from the engine, flat 3\\% curve, $R=0$, notional "
               f"{ORACLE_DE_NOTIONAL:,}".replace(",", "{,}") + ". Down a column it barely moves: "
               "FS01 is set by the annuity, not the hazard rate", "tab:bm-fs01",
               "r" * (len(ORACLE_DE_TENORS) + 1), head, body)


def macros(provs, rows, wolfram_version, wolfram_mode, claim_err):
    checks = findings(rows, wolfram_version, claim_err)
    failed = sum(ok is False for *_, ok in checks)
    c = assess(rows)
    mtm = max(r["mtm_err"] for r in rows)
    confirmed = ("Wolfram and the 50-digit reference agree to "
                 f"{sci(max(max(r['wolfram_annuity_vs_ref'], r['wolfram_ds_vs_ref'], r['wolfram_gradient_vs_ref']) for r in rows))}"
                 ", so the reference is confirmed by a second, independent implementation."
                 if wolfram_version else
                 "Wolfram has not been run, so the reference rests on one implementation.")
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeFiles": ",\\\\ ".join(f"\\texttt{{{esc(p['file'])}}}" for p in provs),
        "bmCodeCommit": f"\\texttt{{{provs[0]['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(wolfram_version) if wolfram_version else "not run",
        "bmWolframVia": f" via {wolfram_mode}" if wolfram_version else "",
        "bmWolframConfirms": confirmed,
        "bmCases": str(len(rows)),
        "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail")
                     + ("" if wolfram_version else "; Wolfram pending"),
        "bmAnnuity": sci(max(r["annuity_rel_err"] for r in rows)),
        "bmMtm": f"{mtm:.2f}", "bmMtmLow": f"{max(r['mtm_err'] for r in rows if r['h'] <= 0.05):.2f}",
        "bmNotional": f"{ORACLE_DE_NOTIONAL:,}".replace(",", "{,}"),
        "bmTradeSpread": f"{ORACLE_DE_TRADE_SPREAD_BPS:g}",
        "bmFd": sci(c[0]["worst"]), "bmLinear": f"{c[1]['ratio']:.2f}",
        "bmTenor": f"{c[2]['ratio']:.2f}",
        "bmYieldLow": f"{100 * c[3]['low']:.1f}", "bmYieldHigh": f"{100 * c[3]['high']:.1f}",
        "bmHand": f"{c[4]['exact']:.6f}", "bmHandStated": f"{c[4]['stated']}",
        "bmConvexity": f"{100 * c[5]['rel']:.2f}", "bmMove": f"{ORACLE_DE_CLAIM_MOVE * 1e4:g}",
        "bmFloorH": f"{c[6]['h']:g}", "bmFloorModel": f"{c[6]['model']}",
        "bmFloorGrad": f"{c[6]['gradient']:.3f}",
        "bmYieldShift": f"{ORACLE_DE_CLAIM_YIELD_SHIFT * 1e4:g}",
        "bmTableTenor": str(ORACLE_DE_TABLE_TENOR),
        "bmRates": f"{min(ORACLE_DE_RATES):g}--{max(ORACLE_DE_RATES):g}",
    })


def write_tables(out, provs, rows, wolfram_version, wolfram_mode, claim_err):
    return write_files(out, ORACLE_DE_TABLE_PREFIX, {
        "macros": macros(provs, rows, wolfram_version, wolfram_mode, claim_err),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{82mm}p{24mm}rl",
                                    "Check & Result & Tolerance & Outcome",
                                    _render(findings(rows, wolfram_version, claim_err))),
        "claims": GENERATED + _claims_table(assess(rows)),
        "fs01": GENERATED + _fs01_table(rows),
    })
