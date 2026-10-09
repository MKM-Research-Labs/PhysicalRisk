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

"""LaTeX tables for the MKM-XV-001 model document, from the evidence JSON.

Every figure the document quotes from a run comes through here, so the PDF
and ``validation_evidence.json`` always agree.
"""

from pathlib import Path


def _gbp(x: float) -> str:
    return f"{x:,.0f}".replace(",", "{,}").replace("-", "$-$")


def _esc(text: str) -> str:
    """Escape the LaTeX specials that appear in labels (a bare % starts a comment)."""
    for ch in ("&", "%", "$", "#", "_", "{", "}"):
        text = text.replace(ch, "\\" + ch)
    return text


def _sci(x: float) -> str:
    if x == 0:
        return "0"
    mant, exp = f"{x:.1e}".split("e")
    return f"${mant}\\times10^{{{int(exp)}}}$"


def _tab(caption: str, label: str, spec: str, header: str, rows) -> str:
    body = "\n".join(" & ".join(r) + r" \\" for r in rows)
    return (f"\\begin{{table}}[H]\\centering\\small\n\\caption{{{caption}}}\\label{{{label}}}\n"
            f"\\begin{{tabular}}{{{spec}}}\n\\toprule\n{header} \\\\\n\\midrule\n{body}\n"
            f"\\bottomrule\n\\end{{tabular}}\n\\end{{table}}\n")


def _checks(ev) -> str:
    c = ev["checks"]
    tl = c["time_rule_error"]["relative_error"]
    rows = [
        ("Pricer reconciliation (fair spread, annuity)",
         _sci(max(c["pricer_reconciliation"]["max_rel_fair_spread"],
                  c["pricer_reconciliation"]["max_rel_annuity"])), r"$<10^{-12}$"),
        ("Independent re-implementation, all terms",
         _sci(c["reference_agreement"]["max_rel_difference"]), r"$<10^{-8}$"),
        ("Monte Carlo against analytic, max $|z|$",
         f"{c['mc_reconciliation']['max_abs_z']:.2f}", "$<3$"),
        ("Time rule error at 26 cells / quarter", _sci(abs(tl["26"])), r"$<5\times10^{-4}$"),
        ("CIR++ fit to the market curve", _sci(c["cir"]["cir_pp_max_rel_fit_error"]),
         r"$<10^{-12}$"),
        ("BCBS 279 Example 2 / 3 EAD",
         f"{c['basel_examples']['example_2']['ead']:.0f} / {c['basel_examples']['example_3']['ead']:.0f}",
         "381 / 5{,}406"),
    ]
    out = [(name, fig, tol, "pass" if ok else "\\textbf{FAIL}")
           for (name, fig, tol), ok in zip(rows, [c[k]["pass"] for k in (
               "pricer_reconciliation", "reference_agreement", "mc_reconciliation",
               "time_rule_error", "cir", "basel_examples")])]
    return _tab("Benchmark checks", "tab:ev-checks", "lrrl",
                "Check & Result & Tolerance & Outcome", out)


def _analytic(ev) -> str:
    rows = [(r["rating"], r["bank"], _gbp(r["cva"]), _gbp(r["fva"]), _gbp(r["booked"]),
             _gbp(r["dva"]), _gbp(r["semi_total"]), f"{r['xva_spread_bps']:+.2f}")
            for r in ev["results"]["analytic"]["rows"]]
    return _tab("Analytic engine: GBP 10m, 5y, 2\\% trigger, at the fair spread", "tab:ev-analytic",
                "llrrrrrr", "Ctpy & Bank & CVA & FVA & Booked & DVA & Semi-rep & bp", rows)


def _mc_recon(ev) -> str:
    rows = [(r["bank"], r["view"].replace("_", "-"), r["term"].upper(), _gbp(r["mc"]),
             f"{r['se']:,.1f}", _gbp(r["analytic"]), f"${r['z']:+.2f}$")
            for r in ev["checks"]["mc_reconciliation"]["rows"]]
    return _tab("Monte Carlo ($\\sigma=0$) against the analytic engine", "tab:ev-mc-recon",
                "lllrrrr", "Bank & View & Term & MC & SE & Analytic & $z$", rows)


def _mc(ev) -> str:
    rows = [(_esc(r["case"]), f"{_gbp(r['cva'])} $\\pm$ {r['cva_se']:,.0f}", _gbp(r["fva"]),
             _gbp(r["booked"])) for r in ev["results"]["monte_carlo"]["rows"]]
    return _tab("Monte Carlo engine, BBB-proxy counterparty", "tab:ev-mc", "lrrr",
                "Case & CVA $\\pm$ SE & FVA & Booked", rows)


def _capital(ev) -> str:
    rows = [(_esc(r["case"]), _gbp(r["ead_today"]), _gbp(r["capital_today"]),
             f"{_gbp(r['kva'])} $\\pm$ {r['kva_se']:,.0f}", f"{r['kva_bps']:.2f}")
            for r in ev["results"]["capital"]["rows"]]
    return _tab("Capital and KVA, bank buys protection; bp is $|$KVA$|/(NA)$ of running spread",
                "tab:ev-capital", "lrrrr",
                "Treatment & EAD today & Capital today & KVA $\\pm$ SE & bp", rows)


def _sensitivities(ev) -> str:
    rows = ev["sensitivities"]["rows"]
    by = {(r["bank"], r["case"]): r for r in rows}
    cases = [r["case"] for r in rows if r["bank"] == "buys"]
    out = [(_esc(case), _gbp(by[("buys", case)]["xva"]), _gbp(by[("buys", case)]["kva"]),
            _gbp(by[("sells", case)]["xva"]), _gbp(by[("sells", case)]["kva"])) for case in cases]
    return _tab("Sensitivities: booked XVA and KVA (GBP)", "tab:ev-sens", "lrrrr",
                "Case & Buys XVA & Buys KVA & Sells XVA & Sells KVA", out)


def write_tables(ev, directory: Path) -> None:
    """Write the macros and the four table groups the document inputs."""
    a = ev["audit"]
    macros = (f"\\newcommand{{\\evCommit}}{{\\texttt{{{a['git_commit'][:12]}}}}}\n"
              f"\\newcommand{{\\evGenerated}}{{{a['generated_utc']}}}\n"
              f"\\newcommand{{\\evPaths}}{{{a['n_paths']:,}}}\n".replace(",", "{,}")
              + f"\\newcommand{{\\evConfig}}{{\\texttt{{{a['config_sha256'][:12]}}}}}\n"
              + f"\\newcommand{{\\evFair}}{{{ev['results']['analytic']['fair_spread_bps']:.2f}}}\n"
              + f"\\newcommand{{\\evAllPass}}{{{'all pass' if ev['all_pass'] else 'NOT ALL PASS'}}}\n")
    files = {
        "evidence_tables_macros.tex": macros,
        "evidence_tables_checks.tex": _checks(ev),
        "evidence_tables_mc_recon.tex": _mc_recon(ev),
        "evidence_tables_results.tex": _analytic(ev) + _mc(ev) + _capital(ev),
        "evidence_tables_sens.tex": _sensitivities(ev),
    }
    directory.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        (directory / name).write_text(
            "% Generated by docs/xva/validation_evidence.py -- do not edit.\n" + body)
