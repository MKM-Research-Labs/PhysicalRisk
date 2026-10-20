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

"""LaTeX for the MKM-SI-001 benchmark document, generated from a run.

The document (``MKM-SI-001_wolfram_benchmark.tex``) is hand-written on the house
template; every figure it quotes from a run comes through here as a macro or an
``evidence_tables_*`` file it inputs, so the PDF and the CSV always agree.
"""

from datetime import date

from config.models import (
    ORACLE_SI_EXC_TOL,
    ORACLE_SI_INV_TOL,
    ORACLE_SI_RETURN_PERIODS,
    ORACLE_SI_STORMS_PER_YEAR,
    ORACLE_SI_TABLE_PREFIX,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files

_KINDS = (("exc", "Exceedance $S(x)$ (Eq.~3.4)", ORACLE_SI_EXC_TOL),
          ("inv", "Quantile $S^{-1}(p)$, clamped (s3.5)", ORACLE_SI_INV_TOL),
          ("rp", "Return-period intensity (s3.6)", ORACLE_SI_INV_TOL))


def _worst(rows, kind, key="rel_err"):
    return max(r[key] for r in rows if r["kind"] == kind)


def findings(rows, ack_rows, wolfram_version, moment_err):
    out = [(f"{label}: model vs reference", sci(_worst(rows, k)), sci(tol),
            outcome(_worst(rows, k) <= tol)) for k, label, tol in _KINDS]
    if wolfram_version:
        ref = max(r["wolfram_vs_ref"] for r in rows + ack_rows)
        out += [("Wolfram agrees with the reference (all cases)", sci(ref), sci(ORACLE_SI_EXC_TOL),
                 outcome(ref <= ORACLE_SI_EXC_TOL)),
                ("Acklam $\\Phi^{-1}$ against Wolfram's exact InverseCDF, absolute",
                 sci(max(r["abs_err_vs_wolfram"] for r in ack_rows)), "see claims", "--"),
                ("Moments $E[Q]$, $E[Q^2]$: Wolfram NIntegrate vs reference", sci(moment_err),
                 sci(ORACLE_SI_INV_TOL), outcome(moment_err <= ORACLE_SI_INV_TOL))]
    else:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_SI_EXC_TOL),
                    "\\textbf{pending}"))
    return out


def _met(met):
    return "finding" if met is None else ("met" if met else "\\textbf{not met}")


def _claims_table(claims):
    cont, pdf, ack, mass, rp, jit = claims
    rows = [
        ("s3.4 $S$ continuous at $u$", "continuous (proved)", f"jump {sci(cont['worst'])}", _met(cont["met"])),
        ("Code docstring: PDF continuous at $u$", "``calibrated so the PDF is continuous''",
         f"$f(u^+)/f(u^-)$ from {pdf['low']:.2f} to {pdf['high']:.2f}", _met(pdf["met"])),
        ("s3.5, s5.3 Acklam $\\Phi^{-1}$", f"{sci(ack['limit'], 2)} absolute, full domain",
         f"{sci(ack['worst'])} absolute; {sci(ack['relative'])} relative", _met(ack["met"])),
        ("s8.4 Mass put on the clamp", "``slight''",
         f"up to {100 * mass['worst']:.1f}\\% at $I_{{\\max}}$ ({esc(mass['at'])})", _met(mass["met"])),
        ("s3.6 Return periods", "$S^{-1}(1/T\\lambda)$",
         f"equal to $I_{{\\max}}$ for every $T$ above {rp['worst']:.2f} to {rp['high']:.2f}\\,y, "
         "by scenario", _met(rp["met"])),
        ("s5.4, s8.5 Jitter on the moments", "``not material''",
         f"{100 * jit['worst']:.2f}\\% at most", _met(jit["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{42mm}p{36mm}p{56mm}l",
               "Claim & Document says & Benchmark finds & Outcome", rows)


def _scenarios(scenarios):
    body = [(esc(s["scenario"]), f"{s['p_tail']:.3f}", f"{100 * s['mass_min']:.2f}\\%",
             f"{100 * s['mass_max']:.1f}\\%", f"{s['cap_T']:.2f}", f"{s['pdf_ratio']:.2f}",
             f"{s['mean']:.2f}", f"{s['sd']:.2f}", f"{100 * s['jitter_sd_rel']:+.2f}\\%")
            for s in scenarios]
    return tab("Each scenario family, exactly: tail probability, the mass the clamp puts on each "
               "bound, the return period from which every intensity is $I_{\\max}$, the density "
               "jump at $u$, and the moments of the sampled intensity", "tab:bm-scenarios",
               "lrrrrrrrr", "Scenario & $p_{\\text{tail}}$ & at $I_{\\min}$ & at $I_{\\max}$ & "
               "cap from $T$ (y) & $f(u^+)/f(u^-)$ & Mean & SD & Jitter on SD", body)


def _return_periods(rows, families):
    body = []
    for name, p in families.items():
        cells = []
        for t in ORACLE_SI_RETURN_PERIODS:
            r = next(x for x in rows if x["scenario"] == name and x["kind"] == "rp" and x["arg"] == t)
            cells.append("\\textbf{cap}" if r["capped"] else f"{float(r['ref']):.2f}")
        body.append([esc(name)] + cells)
    head = "Scenario & " + " & ".join(f"$T={t}$" for t in ORACLE_SI_RETURN_PERIODS)
    return tab(f"Return-period intensity, $\\lambda={ORACLE_SI_STORMS_PER_YEAR}$ storms a year "
               "(reference; the model agrees to the figures in Table~\\ref{tab:bm-checks}). "
               "``cap'' means $I_{\\max}$", "tab:bm-rp", "l" + "r" * len(ORACLE_SI_RETURN_PERIODS),
               head, body)


def macros(provs, rows, ack_rows, claims, scenarios, wolfram_version, wolfram_mode, moment_err):
    checks = findings(rows, ack_rows, wolfram_version, moment_err)
    failed = sum("FAIL" in c[3] for c in checks)
    by = {s["scenario"]: s for s in scenarios}
    if wolfram_version:
        agree = max(r["wolfram_vs_ref"] for r in rows + ack_rows)
        confirmed = (f"Wolfram and the 50-digit reference agree to {sci(agree)}, so the "
                     "reference is confirmed by a second, independent implementation.")
    else:
        confirmed = "Wolfram has not been run, so the reference rests on one implementation."
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeFiles": ",\\\\ ".join(f"\\texttt{{{esc(p['file'])}}}" for p in provs),
        "bmCodeCommit": f"\\texttt{{{provs[0]['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(wolfram_version) if wolfram_version else "not run",
        "bmWolframVia": f" via {wolfram_mode}" if wolfram_version else "",
        "bmWolframConfirms": confirmed,
        "bmCases": str(len(rows) + len(ack_rows)),
        "bmExcWorst": sci(_worst(rows, "exc")), "bmInvWorst": sci(_worst(rows, "inv")),
        "bmRpWorst": sci(_worst(rows, "rp")),
        "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail")
                     + ("" if wolfram_version else "; Wolfram pending"),
        "bmAcklamAbs": sci(claims[2]["worst"]), "bmAcklamRel": sci(claims[2]["relative"]),
        "bmMassMaxLow": f"{100 * min(s['mass_max'] for s in scenarios):.1f}",
        "bmMassMaxHigh": f"{100 * max(s['mass_max'] for s in scenarios):.1f}",
        "bmCapHistorical": f"{by['historical']['cap_T']:.1f}" if "historical" in by else "--",
        "bmCapBaseline": f"{by['baseline']['cap_T']:.2f}" if "baseline" in by else "--",
        "bmPdfLow": f"{claims[1]['low']:.2f}", "bmPdfHigh": f"{claims[1]['high']:.2f}",
        "bmJitter": f"{100 * claims[5]['worst']:.2f}",
    })


def write_tables(out, provs, rows, ack_rows, claims, scenarios, families,
                 wolfram_version, wolfram_mode, moment_err):
    return write_files(out, ORACLE_SI_TABLE_PREFIX, {
        "macros": macros(provs, rows, ack_rows, claims, scenarios, wolfram_version, wolfram_mode,
                         moment_err),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{78mm}p{28mm}rl",
                                    "Check & Result & Tolerance & Outcome",
                                    findings(rows, ack_rows, wolfram_version, moment_err)),
        "claims": GENERATED + _claims_table(claims),
        "scenarios": GENERATED + _scenarios(scenarios),
        "return_periods": GENERATED + _return_periods(rows, families),
    })
