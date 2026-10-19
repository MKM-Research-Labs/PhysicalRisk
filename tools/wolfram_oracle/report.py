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

"""The evidence a run files in ModelRisk: one PDF and two CSVs.

ModelRisk takes pdf/csv/txt uploads, not JSON, and files them under the
"Benchmark Test" document category. The PDF says what was found; the CSVs carry
every number behind it. The PDF states plainly whether Wolfram has run — until
it has, the closed-form results rest on one reference implementation, not two.
"""

import csv
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config.models import (
    ORACLE_FIT_LL_TOL,
    ORACLE_MODEL_ID,
    ORACLE_MODEL_NAME,
    ORACLE_OPERATING_MAX_T,
    ORACLE_REL_TOL,
)
from tools.wolfram_oracle.return_levels import worst


def _flat(row, skip=()):
    out = {}
    for k, v in row.items():
        if k in skip:
            continue
        if isinstance(v, dict):
            for T, d in v.items():
                for kk, vv in d.items():
                    out[f"x_{T}_{kk}"] = vv
        elif isinstance(v, (list, tuple)):
            for name, vv in zip(("xi", "loc", "scale"), v):
                out[f"{k.removesuffix('_xi_loc_scale')}_{name}"] = vv
        else:
            out[k] = v
    return out


def write_csv(path, rows, skip=()):
    flat = [_flat(r, skip) for r in rows]
    fields = list(dict.fromkeys(k for r in flat for k in r))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(flat)


def findings(rl_rows, fit_rows, wolfram_version):
    """The verdicts, each as (check, result, outcome)."""
    lv, ex = worst(rl_rows, "level_rel_err"), worst(rl_rows, "exc_rel_err")
    ok = max(lv["level_rel_err"], ex["exc_rel_err"]) <= ORACLE_REL_TOL
    out = [("Closed-form return levels and exceedance, T <= "
            f"{ORACLE_OPERATING_MAX_T:,} (tolerance {ORACLE_REL_TOL:.0e})",
            f"worst level {lv['level_rel_err']:.1e} ({lv['id']}); "
            f"worst exceedance {ex['exc_rel_err']:.1e} ({ex['id']})",
            "PASS" if ok else "FAIL")]
    if wolfram_version:
        ref = max(max(r["level_wolfram_vs_ref"], r["exc_wolfram_vs_ref"]) for r in rl_rows)
        mod = max(max(r["level_model_vs_wolfram"], r["exc_model_vs_wolfram"])
                  for r in rl_rows if r["T"] <= ORACLE_OPERATING_MAX_T)
        out.append(("Wolfram confirms the reference", f"{wolfram_version}: reference within "
                    f"{ref:.1e}; model within {mod:.1e} of Wolfram",
                    "PASS" if mod <= ORACLE_REL_TOL else "FAIL"))
    else:
        out.append(("Wolfram confirms the reference", "Not run. The closed forms rest on one "
                    "reference implementation (mpmath) until it is.", "PENDING"))
    gain = max(r["ll_gain_indep"] for r in fit_rows)
    gain_w = max((r["ll_gain_wolfram"] for r in fit_rows if "ll_gain_wolfram" in r), default=None)
    detail = f"largest log-likelihood gain found by the independent fit: {gain:.1e}"
    if gain_w is not None:
        detail += f"; by Wolfram: {gain_w:.1e}"
    out.append(("Maximum-likelihood fit reaches the maximum", detail,
                "PASS" if max(gain, gain_w or gain) <= ORACLE_FIT_LL_TOL else "FAIL"))
    truthful = [r for r in fit_rows if r["truth_xi_loc_scale"] and r["family"] == "gev"]
    if truthful:
        ratios = [r["levels"][1000]["model"] / r["levels"][1000]["truth"] for r in truthful]
        out.append(("Sampling uncertainty in the 1-in-1000 level (synthetic, known truth)",
                    f"fitted / true level ranges {min(ratios):.2f}x to {max(ratios):.2f}x "
                    "across samples", "FINDING"))
    return out


LIMITATIONS = [
    "This is a benchmark of the implementation, not independent validation: it shows the "
    "model computes what its formulae say, not that the formulae suit the data.",
    "The fit section uses seeded synthetic samples unless a gauge export was supplied; see "
    "'Data' above.",
    "GEVFitter fits the GEV to every storm's peak level. The GEV is the limiting law for "
    "block maxima (e.g. annual maxima); the per-storm choice is a methodology question this "
    "benchmark does not answer.",
    "Parameter uncertainty is the dominant tail risk at the sample sizes tested; return levels "
    "carry no confidence interval in the model today.",
]


def _table(data, widths=None):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def write_pdf(path, prov, data_source, rl_rows, fit_rows, wolfram_version, trap):
    st = getSampleStyleSheet()
    p = lambda s, style="BodyText": Paragraph(s, st[style])  # noqa: E731
    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4),
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm,
                            title=f"Benchmark Test - {ORACLE_MODEL_NAME}")
    meta = [["Model", f"{ORACLE_MODEL_ID} {ORACLE_MODEL_NAME}"],
            ["Generated", date.today().isoformat()],
            ["Code under test", f"{prov['file']} sha256 {prov['sha256'][:16]}... "
                                f"commit {prov['last_commit'][:12]}"
                                + (" (UNCOMMITTED CHANGES)" if prov["uncommitted_changes"] else "")],
            ["Numerics", ", ".join(f"{k} {v}" for k, v in prov["packages"].items())],
            ["Wolfram", wolfram_version or "not run"],
            ["Data", data_source]]
    story = [p(f"Benchmark Test: {ORACLE_MODEL_NAME} ({ORACLE_MODEL_ID})", "Title"),
             _table(meta, [40 * mm, 220 * mm]), Spacer(0, 5 * mm), p("Findings", "Heading2"),
             _table([["Check", "Result", "Outcome"]] +
                    [[p(a), p(b), c] for a, b, c in findings(rl_rows, fit_rows, wolfram_version)],
                    [80 * mm, 160 * mm, 22 * mm]),
             p(f"Sign convention: the 1-in-1000 level for xi = 0.2 is {trap['correct (c = -xi)']:.2f}; "
               f"passed to scipy unflipped it would be {trap['unflipped (c = +xi)']:.2f}. "
               "GEVFitter flips it correctly.")]
    head = ["Case", "T", "Reference level", "Level err", "P(X > x_T)", "Exceed. err"]
    if wolfram_version:
        head += ["Model vs Wolfram (level)", "Model vs Wolfram (exc.)"]
    body = []
    for r in rl_rows:
        line = [r["case"], f"{r['T']:,}", r["level_ref"][:20], f"{r['level_rel_err']:.1e}",
                f"{float(r['exc_ref']):.2e}", f"{r['exc_rel_err']:.1e}"]
        if wolfram_version:
            line += [f"{r['level_model_vs_wolfram']:.1e}", f"{r['exc_model_vs_wolfram']:.1e}"]
        body.append(line)
    story += [p("Return levels and exceedance", "Heading2"), _table([head] + body)]
    head = ["Series", "Fit", "n", "xi model", "xi indep.", "xi true", "LL gain",
            "x_100 model", "x_100 true", "x_1000 model", "x_1000 true"]
    if wolfram_version:
        head += ["xi Wolfram", "LL gain Wolfram"]
    body = []
    for r in fit_rows:
        lv, t = r["levels"], r["truth_xi_loc_scale"]
        line = [r["series"], r["family"], r["n"], f"{r['model_xi_loc_scale'][0]:.4f}",
                f"{r['indep_xi_loc_scale'][0]:.4f}", f"{t[0]:.2f}" if t else "-",
                f"{r['ll_gain_indep']:.1e}", f"{lv[100]['model']:.3f}",
                f"{lv[100]['truth']:.3f}" if t else "-", f"{lv[1000]['model']:.3f}",
                f"{lv[1000]['truth']:.3f}" if t else "-"]
        if wolfram_version:
            line += [f"{r['wolfram_xi_loc_scale'][0]:.4f}", f"{r['ll_gain_wolfram']:.1e}"]
        body.append(line)
    story += [p("Maximum-likelihood fit", "Heading2"), _table([head] + body),
              p("Limitations", "Heading2")] + [p(f"&bull; {s}") for s in LIMITATIONS]
    doc.build(story)
