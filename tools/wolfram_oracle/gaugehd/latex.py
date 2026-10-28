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

"""LaTeX for the MKM-GHD-001 benchmark document, generated from a run."""

from datetime import date

from config.models import (
    ORACLE_GHD_REPLICATIONS,
    ORACLE_GHD_TABLE_PREFIX,
    ORACLE_GHD_WOLFRAM_TOL,
    ORACLE_GHD_Z_LIMIT,
)
from tools.wolfram_oracle._latex import GENERATED, esc, macros as as_macros, outcome, sci, tab, write_files
from tools.wolfram_oracle.gaugehd.cases import STATS

_LABEL = {"days_FloodAlert": "Days at or above FloodAlert", "days_FloodWarning": "Days at or above FloodWarning",
          "days_SevereFloodWarning": "Days at or above SevereFloodWarning", "mean": "Mean level",
          "jan_minus_mean": "January mean less the annual mean", "jul_minus_mean": "July mean less the annual mean"}


def findings(rows, wolfram_err):
    out = []
    for k in STATS:
        z = max(abs(r[f"{k}_z"]) for r in rows)
        out.append((f"{_LABEL[k]}: model against the exact expectation, worst $|z|$", f"{z:.2f}",
                    f"{ORACLE_GHD_Z_LIMIT:g}", z <= ORACLE_GHD_Z_LIMIT))
    if wolfram_err is None:
        out.append(("Wolfram agrees with the closed forms", "not run", sci(ORACLE_GHD_WOLFRAM_TOL), None))
    else:
        out.append(("Wolfram's exact integrals agree with the closed forms", sci(wolfram_err),
                    sci(ORACLE_GHD_WOLFRAM_TOL), wolfram_err <= ORACLE_GHD_WOLFRAM_TOL))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "finding" if met is None else ("met" if met else "\\textbf{not met}")


def _claims_table(c):
    lag1, alert, spikes, seas, sev, rep, lag7, phase, below = c
    rows = [
        ("\\S7.1(1)", "lag-1 autocorrelation $\\approx0.85$ (non-tidal)",
         f"{lag1['flood_free']:.3f} without floods; the model gives {lag1['model'][0]:.3f} and {lag1['model'][1]:.3f}: "
         "the seasonal cycle dominates", _met(lag1["met"])),
        ("\\S7.1(3)", "days above FloodAlert $\\approx 6\\max(n_3,1)$",
         f"{alert['exact'][0]:.1f} and {alert['exact'][1]:.1f} for $n_3=0, 8$, against 6 and 48", _met(alert["met"])),
        ("\\S8.4", "single-day flood spikes",
         "days above FloodAlert per flood: " + ", ".join(f"{v:.2f}" for v in spikes["per_event"].values())
         + " (non-tidal, partial, tidal)", _met(spikes["met"])),
        ("\\S5.6", "January, July means $\\approx\\pm A_s$",
         f"{seas['low']:.3f}--{seas['high']:.3f} of $A_s$", _met(seas["met"])),
        ("\\S4.5", "reproduces the observed severe frequency",
         f"$n_3$ counts 5 years but is spread over {sev['factor'] * 5:.0f}: {sev['observed_per_5y']} observed "
         f"per 5 years become {sev['model_per_5y']:.1f}", _met(sev["met"])),
        ("\\S5.4, \\S7.3", "byte-identical regeneration",
         f"one gauge id seeds {rep['seeds'][0]} in one process and {rep['seeds'][1]} in another; "
         "the series also ends at the run date", _met(rep["met"])),
        ("\\S6.1", "lag-7 autocorrelations 0.32, 0.028",
         ", ".join(f"{v:.4f}" for _, _, v in lag7["values"]), _met(lag7["met"])),
        ("\\S7.2", "mean levels below FloodAlert", f"at most {below['worst']:.3f}\\,m", _met(below["met"])),
        ("\\S3.5", "a 14.8-day spring--neap cycle",
         f"its phase is the day of the year, so it jumps {phase['jump_days']:.1f} days each 1 January",
         _met(phase["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{20mm}p{42mm}p{74mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows)


def _gauge_table(rows):
    body = []
    for r in rows:
        body.append((esc(r["id"]), f"{r['floods_exact']:.1f}",
                     *[f"{r[f'{k}_exact']:.2f} / {r[f'{k}_model']:.2f}" for k in STATS[:3]],
                     f"{r['mean_exact']:.3f} / {r['mean_model']:.3f}"))
    return tab(f"Exact expectation / model mean over {ORACLE_GHD_REPLICATIONS} series, per 50-year series",
               "tab:bm-gauges", "lrrrrr",
               "Gauge & Floods & Days $\\ge$ alert & $\\ge$ warning & $\\ge$ severe & Mean level (m)", body)


def macros(provs, rows, version, mode, c, wolfram_err):
    checks = findings(rows, wolfram_err)
    failed = sum(ok is False for *_, ok in checks)
    nt = {r["id"]: r for r in rows}["Non-tidal/n3=0"]
    z = max(abs(r[f"{k}_z"]) for r in rows for k in STATS)
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeCommit": f"\\texttt{{{provs[0]['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(version) if version else "not run",
        "bmWolframVia": f" via {mode}" if version else "",
        "bmWolframConfirms": (f"Wolfram's exact integrals agree with the reference's double-precision closed forms to {sci(wolfram_err)}."
                              if version else "Wolfram has not been run."),
        "bmChecks": str(len(checks)), "bmOutcome": ("all pass" if not failed else f"{failed} fail")
        + ("" if version else "; Wolfram pending"),
        "bmReps": str(ORACLE_GHD_REPLICATIONS), "bmWorstZ": f"{z:.2f}", "bmDays": f"{nt['n_days']:,}".replace(",", "{,}"),
        "bmLagExact": f"{c[0]['flood_free']:.3f}", "bmLagModel": f"{c[0]['model'][0]:.3f}",
        "bmAlertZero": f"{c[1]['exact'][0]:.1f}", "bmAlertEight": f"{c[1]['exact'][1]:.1f}",
        "bmPerEvent": f"{c[2]['per_event']['Non-tidal']:.1f}",
        "bmSeedOne": str(c[5]["seeds"][0]), "bmSeedTwo": str(c[5]["seeds"][1]),
        "bmJump": f"{c[7]['jump_days']:.1f}",
    })


def write_tables(out, provs, rows, version, mode, c, wolfram_err):
    return write_files(out, ORACLE_GHD_TABLE_PREFIX, {
        "macros": macros(provs, rows, version, mode, c, wolfram_err),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{88mm}p{18mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(rows, wolfram_err))),
        "claims": GENERATED + _claims_table(c),
        "gauges": GENERATED + _gauge_table(rows),
    })
