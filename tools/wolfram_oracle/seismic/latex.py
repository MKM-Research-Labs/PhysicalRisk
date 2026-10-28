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

"""LaTeX for the MKM-SEIS-001 benchmark document, generated from a run."""

from datetime import date

from config.models import (
    ORACLE_SEIS_N_SIM,
    ORACLE_SEIS_PRODUCTION_N_SIM,
    ORACLE_SEIS_REL_TOL,
    ORACLE_SEIS_SEED,
    ORACLE_SEIS_TABLE_PREFIX,
    ORACLE_SEIS_WOLFRAM_TOL,
    ORACLE_SEIS_Z_LIMIT,
)
from tools.wolfram_oracle._latex import GENERATED, esc, longtab, macros as as_macros, outcome, sci, tab, write_files
from tools.wolfram_oracle.seismic.cases import METRICS

_LABEL = {"pga": "Median PGA", "no_collapse": "No-collapse rate", "loss": "Loss frequency",
          "spread": "Seismic spread"}


def _n(x):
    return f"{x:,}".replace(",", "{,}")


def findings(rows, wolfram_err):
    chk = max(r["check_rel_err"] for r in rows)
    rjb = max(r["rjb_rel_err"] for r in rows)
    out = [("Model C medians, GMPE median and $\\lambda_i$ against the reference", sci(chk),
            sci(ORACLE_SEIS_REL_TOL), chk <= ORACLE_SEIS_REL_TOL),
           ("Every event's $R_{JB}$ is the asset's offset (the generator's geometry)", sci(rjb),
            sci(ORACLE_SEIS_REL_TOL), rjb <= ORACLE_SEIS_REL_TOL)]
    for k in METRICS:
        z = max(abs(r[f"{k}_z"]) for r in rows if f"{k}_z" in r)
        out.append((f"{_LABEL[k]}: model's Monte Carlo against the exact credit, worst $|z|$",
                    f"{z:.2f}", f"{ORACLE_SEIS_Z_LIMIT:g}", z <= ORACLE_SEIS_Z_LIMIT))
    if wolfram_err is None:
        out.append(("Wolfram agrees with the reference", "not run", sci(ORACLE_SEIS_WOLFRAM_TOL), None))
    else:
        out.append(("Wolfram's integrals over magnitude agree with the reference", sci(wolfram_err),
                    sci(ORACLE_SEIS_WOLFRAM_TOL), wolfram_err <= ORACLE_SEIS_WOLFRAM_TOL))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "finding" if met is None else ("met" if met else "\\textbf{not met}")


def _claims_table(c):
    rep, vs, gates, rev, stab, prod, t18, gmpe = c
    rows = [
        ("\\S7, Tables 3--10", "the tables come from the running model",
         f"the code reproduces {rep['reproduced']} of {rep['of']} printed figures at the generator's seed",
         _met(rep["met"])),
        ("\\S7, Tables 3--10", "the figures are the model's credit",
         f"every printed figure within {vs['worst_z']:.2f} standard errors of the exact value", _met(vs["met"])),
        ("Table 2", "six acceptance gates pass",
         f"all hold on the exact credit, without the harness's 0.7\\,bp tolerance; the floor is {gates['floor_bps']:.4f}\\,bp",
         _met(gates["met"])),
        ("\\S7", "monotone in distance, zone, soil and resilience",
         f"{len(rev['reversals'])} adjacent printed pairs run against the exact order; all are sampling noise",
         _met(rev["met"])),
        ("\\S9.6", "stability is adequate at 20{,}000 draws",
         f"a {stab['exact']:.2f}\\,bp spread carries a {stab['se']:.2f}\\,bp standard error "
         f"({100 * stab['worst_rel_se']:.0f}\\%)", _met(stab["met"])),
        ("Table 18", "mean loss 0.01, 0.10, 0.35 (DS0--DS2), truncated lognormal",
         "the figures are medians of lognormals clipped at 1: means "
         + ", ".join(f"{v:.4f}" for v in t18["exact"].values()), _met(t18["met"])),
        ("\\S3.3, App.~B", "a Boore--Atkinson-style GMPE",
         "the coded form, with magnitude-dependent spreading $(c_3+c_5(M-m_{\\mathrm{ref}}))\\ln R$, "
         "is not stated", _met(gmpe["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{24mm}p{44mm}p{68mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows)


def _f(x, k):
    if x is None:
        return "--"
    return f"{x:.4f}" if k == "pga" else (f"{x:.1f}" if k == "no_collapse" else
                                          (f"{x:.4f}" if k == "loss" else f"{x:.2f}"))


def _cells_table(rows):
    body = []
    for r in rows:
        zmax = max(abs(r[f"{k}_printed_z"]) for k in METRICS if f"{k}_printed_z" in r)
        cells = [str(r["table"]), esc(r["label"])]
        for k in METRICS[1:]:
            cells += [_f(r.get(f"{k}_printed"), k), _f(r[f"{k}_exact"], k) if f"{k}_printed" in r else "--"]
        body.append((*cells, f"{zmax:.2f}"))
    return longtab("Every printed cell against the exact credit: no-collapse (\\%), loss frequency (\\%), "
                   f"spread (bp), printed then exact; $|z|$ in standard errors at {_n(ORACLE_SEIS_N_SIM)} draws",
                   "tab:bm-cells", "rlrrrrrrr",
                   "T & Cell & \\multicolumn{2}{c}{No-collapse} & \\multicolumn{2}{c}{Loss} & "
                   "\\multicolumn{2}{c}{Spread} & $|z|$", body)


def _pga_table(rows):
    body = [(esc(r["label"]), f"{r['r_jb']:.3f}", f"{r['pga_printed']:.4f}", f"{r['pga_exact']:.4f}",
             f"{abs(r['pga_printed_z']):.2f}") for r in rows if "pga_printed" in r]
    return tab("Table 3's median PGA: printed against the exact median of the event PGA", "tab:bm-pga",
               "lrrrr", "Cell & $R_{JB}$ (km) & Printed (g) & Exact (g) & $|z|$", body)


def _noise_table(rows):
    live = sorted((r for r in rows if r["spread_exact"] >= 1.0), key=lambda r: -r["spread_exact"])[:8]
    body = [(esc(r["id"]), f"{r['spread_exact']:.2f}", f"{r['spread_se']:.2f}",
             f"{r['spread_se_production']:.2f}") for r in live]
    return tab(f"The largest spreads and their standard errors at {_n(ORACLE_SEIS_N_SIM)} draws "
               f"(the tables) and {_n(ORACLE_SEIS_PRODUCTION_N_SIM)} (production)", "tab:bm-noise", "lrrr",
               "Cell & Exact (bp) & Std error, tables (bp) & Std error, production (bp)", body)


def macros(provs, rows, version, mode, c, wolfram_err):
    checks = findings(rows, wolfram_err)
    failed = sum(ok is False for *_, ok in checks)
    stab, prod, t18 = c[4], c[5], c[6]
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeCommit": f"\\texttt{{{provs[0]['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(version) if version else "not run",
        "bmWolframVia": f" via {mode}" if version else "",
        "bmWolframConfirms": (f"Wolfram's integrals agree with the 50-digit reference to {sci(wolfram_err)}."
                              if version else "Wolfram has not been run."),
        "bmCells": str(len(rows)), "bmAssets": str(len({r['asset'] for r in rows})),
        "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail") + ("" if version else "; Wolfram pending"),
        "bmCheckErr": sci(max(r["check_rel_err"] for r in rows)),
        "bmReproduced": str(c[0]["reproduced"]), "bmPrinted": str(c[0]["of"]),
        "bmWorstZ": f"{c[1]['worst_z']:.2f}", "bmFloor": f"{c[2]['floor_bps']:.4f}",
        "bmReversals": str(len(c[3]["reversals"])),
        "bmStableAt": esc(stab["at"]), "bmStableExact": f"{stab['exact']:.2f}",
        "bmStableSE": f"{stab['se']:.2f}", "bmStableRel": f"{100 * stab['worst_rel_se']:.0f}",
        "bmProdAt": esc(prod["at"]), "bmProdExact": f"{prod['exact']:.1f}", "bmProdSE": f"{prod['se']:.1f}",
        "bmMeanTwo": f"{t18['exact']['DS2']:.3f}",
        "bmNSim": _n(ORACLE_SEIS_N_SIM), "bmSeed": str(ORACLE_SEIS_SEED),
        "bmProductionN": _n(ORACLE_SEIS_PRODUCTION_N_SIM),
    })


def write_tables(out, provs, rows, version, mode, c, wolfram_err):
    return write_files(out, ORACLE_SEIS_TABLE_PREFIX, {
        "macros": macros(provs, rows, version, mode, c, wolfram_err),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{88mm}p{18mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(rows, wolfram_err))),
        "claims": GENERATED + _claims_table(c),
        "noise": GENERATED + _noise_table(rows),
        "pga": GENERATED + _pga_table(rows),
        "cells": GENERATED + _cells_table(rows),
    })
