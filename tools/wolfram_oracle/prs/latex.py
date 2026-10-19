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

"""LaTeX for the MKM-PR-001 benchmark document, generated from a run.

The document (``MKM-PR-001_wolfram_benchmark.tex``) is hand-written on the house
template; every figure it quotes from a run comes through here as a macro or an
``evidence_tables_*`` file it inputs, so the PDF and the CSV always agree.
"""

from datetime import date

from config.models import (
    MIN_PRS_SPREAD_BPS,
    ORACLE_PRS_TABLE_PREFIX,
    ORACLE_PRS_CLAIM_DISC_SPLIT,
    ORACLE_PRS_REL_TOL,
    ORACLE_PRS_TABLE_TENOR,
)
from tools.wolfram_oracle._latex import (
    GENERATED,
    esc,
    longtab,
    macros as as_macros,
    outcome,
    sci,
    tab,
    write_files,
)
from tools.wolfram_oracle.prs.claims import assess, by_probability


def _met(met):
    return "finding" if met is None else ("met" if met else "\\textbf{not met}")


def findings(rows, rules, wolfram_version):
    """The computational checks, each as (check, result, tolerance, outcome)."""
    worst = max(r["rel_err"] for r in rows)
    out = [("Fair spread, all cases (Eqs.~1--8)", sci(worst), sci(ORACLE_PRS_REL_TOL),
            outcome(worst <= ORACLE_PRS_REL_TOL))]
    if wolfram_version:
        ref = max(r["wolfram_vs_ref"] for r in rows)
        mod = max(r["model_vs_wolfram"] for r in rows)
        out += [("Wolfram agrees with the reference", sci(ref), sci(ORACLE_PRS_REL_TOL),
                 outcome(ref <= ORACLE_PRS_REL_TOL)),
                ("Model agrees with Wolfram", sci(mod), sci(ORACLE_PRS_REL_TOL),
                 outcome(mod <= ORACLE_PRS_REL_TOL))]
    else:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_PRS_REL_TOL),
                    "\\textbf{pending}"))
    out += [(esc(name), esc(detail), "--", outcome(ok)) for name, ok, detail in rules]
    return out


def _claims_table(claims):
    disc, curve, basis = claims
    split = f"{ORACLE_PRS_CLAIM_DISC_SPLIT:.2f}"
    rows = [
        ("s8.3 Quarterly vs continuous time",
         f"up to {disc['limit']:.0f} bp, only above $p={split}$",
         f"{disc['low']:.1f} bp ($p\\le{split}$); {disc['high']:.1f} bp above", _met(disc["met"])),
        ("s8.4 Flat vs book curve, 5y", f"$<{curve['limit']:.0f}$ bp",
         f"{curve['worst']:.1f} bp; over 1 bp from $p={curve['first_over']}$"
         if curve["first_over"] else f"{curve['worst']:.2f} bp", _met(curve["met"])),
        ("s3.3 Basis: gauge leg $p\\times10^4$ vs Eq.~7", "not stated",
         f"up to {basis['worst']:.0f} bp; over 1 bp from $p={basis['first_over']}$",
         _met(basis["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{45mm}p{35mm}p{55mm}l",
               "Claim & Document says & Benchmark finds & Outcome", rows)


def _worked(rows):
    body = [(f"{t['p']:g}", f"{t['quarterly']:.2f}", f"{t['continuous']:.2f}",
             f"{t['disc_minus_cont_bp']:+.2f}", f"{100 * t['disc_rel']:+.2f}\\%",
             f"{t['flat_minus_book_bp']:+.2f}", f"{t['gauge_leg']:.1f}",
             f"{t['basis_artefact_bp']:+.2f}") for t in by_probability(rows)]
    return tab(f"Worked figures at {ORACLE_PRS_TABLE_TENOR} years, $R=0$, in bp",
               "tab:bm-worked", "rrrrrrrr",
               "$p$ & Quarterly & Continuous & $\\Delta$ & Rel. & Flat$-$book & "
               "$p\\times10^4$ & Basis artefact", body)


def _spreads(rows, wolfram_version):
    book = [r for r in rows if r["curve"] == "book" and r["R"] == 0.0]
    head = "$T$ & $p$ & Reference spread (bp) & Model rel.\\ err"
    spec = "rrrr"
    if wolfram_version:
        head += " & Model vs W."
        spec += "r"
    body = []
    for r in book:
        row = [str(r["T"]), f"{r['p']:g}", r["ref"][:16] + (" (floor)" if r["floored"] else ""),
               sci(r["rel_err"])]
        if wolfram_version:
            row.append(sci(r["model_vs_wolfram"]))
        body.append(row)
    return longtab("Fair spread on the book curve, $R=0$: model against reference. The full "
                   "grid (both curves, both recoveries) is in \\texttt{spreads.csv}",
                   "tab:bm-spreads", spec, head, body)


def macros(prov, rows, rules, wolfram_version, wolfram_mode):
    checks = findings(rows, rules, wolfram_version)
    failed = sum("FAIL" in c[3] for c in checks)
    claims = assess(rows)
    if wolfram_version:
        agree = max(r["wolfram_vs_ref"] for r in rows)
        confirmed = (f"Wolfram and the 50-digit reference agree to {sci(agree)}, so the "
                     "reference is confirmed by a second, independent implementation.")
    else:
        confirmed = "Wolfram has not been run, so the reference rests on one implementation."
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeFile": f"\\texttt{{{esc(prov['file'])}}}",
        "bmCodeSha": f"\\texttt{{{prov['sha256'][:16]}}}",
        "bmCodeCommit": f"\\texttt{{{prov['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if prov["uncommitted_changes"] else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in prov["packages"].items()),
        "bmWolfram": esc(wolfram_version) if wolfram_version else "not run",
        "bmWolframVia": f" via {wolfram_mode}" if wolfram_version else "",
        "bmWolframConfirms": confirmed,
        "bmCases": str(len(rows)),
        "bmWorst": sci(max(r["rel_err"] for r in rows)),
        "bmTol": sci(ORACLE_PRS_REL_TOL),
        "bmFloor": f"{MIN_PRS_SPREAD_BPS:g}",
        "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail")
                     + ("" if wolfram_version else "; Wolfram pending"),
        "bmDiscLow": f"{claims[0]['low']:.1f}",
        "bmDiscHigh": f"{claims[0]['high']:.0f}",
        "bmCurveWorst": f"{claims[1]['worst']:.1f}",
        "bmCurveOver": f"{claims[1]['first_over']}" if claims[1]["first_over"] else "--",
        "bmBasisOver": f"{claims[2]['first_over']}" if claims[2]["first_over"] else "--",
    })


def write_tables(out, prov, rows, rules, wolfram_version, wolfram_mode):
    """Write every generated .tex the document inputs; return their paths."""
    return write_files(out, ORACLE_PRS_TABLE_PREFIX, {
        "macros": macros(prov, rows, rules, wolfram_version, wolfram_mode),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{70mm}p{50mm}rl",
                                    "Check & Result & Tolerance & Outcome",
                                    findings(rows, rules, wolfram_version)),
        "claims": GENERATED + _claims_table(assess(rows)),
        "worked": GENERATED + _worked(rows),
        "spreads": GENERATED + _spreads(rows, wolfram_version),
    })
