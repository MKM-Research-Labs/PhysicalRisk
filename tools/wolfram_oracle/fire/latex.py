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

"""LaTeX for the MKM-FIRE-001 benchmark document, generated from a run."""

from datetime import date

from config.models import (
    ORACLE_FIRE_N_SIM,
    ORACLE_FIRE_PRODUCTION_N_SIM,
    ORACLE_FIRE_REL_TOL,
    ORACLE_FIRE_SEED,
    ORACLE_FIRE_TABLE_PREFIX,
    ORACLE_FIRE_Z_LIMIT,
)
from tools.wolfram_oracle._latex import GENERATED, esc, longtab, macros as as_macros, outcome, sci, tab, write_files
from tools.wolfram_oracle.fire.cases import METRICS

_LABEL = {"containment": "Containment rate", "loss": "Loss frequency", "spread_bps": "Fire spread"}


def findings(rows, wolfram_err):
    z = {k: max(abs(r[f"{k}_z"]) for r in rows) for k in METRICS}
    prof = max(r["profile_rel_err"] for r in rows)
    out = [("Model C: response profile against the documented formulae (s3.2)", sci(prof),
            sci(ORACLE_FIRE_REL_TOL), prof <= ORACLE_FIRE_REL_TOL and all(r["flags_ok"] for r in rows))]
    out += [(f"{_LABEL[k]}: model's Monte Carlo against the exact credit, worst $|z|$",
             f"{z[k]:.2f}", f"{ORACLE_FIRE_Z_LIMIT:g}", z[k] <= ORACLE_FIRE_Z_LIMIT) for k in METRICS]
    unresolved = max(r["unresolved"] for r in rows)
    out.append(("Fires unresolved at the 200-step budget", sci(unresolved), sci(ORACLE_FIRE_REL_TOL),
                unresolved <= ORACLE_FIRE_REL_TOL))
    if wolfram_err is None:
        out.append(("Wolfram agrees with the exact reference", "not run", sci(ORACLE_FIRE_REL_TOL), None))
    else:
        out.append(("Wolfram agrees with the exact reference (outcome probabilities, $q$)",
                    sci(wolfram_err), sci(ORACLE_FIRE_REL_TOL), wolfram_err <= ORACLE_FIRE_REL_TOL))
    return out


def _render(checks):
    return [(a, b, c, "\\textbf{pending}" if ok is None else outcome(ok)) for a, b, c, ok in checks]


def _met(met):
    return "finding" if met is None else ("met" if met else "\\textbf{not met}")


def _claims_table(c):
    rep, vs, absorb, grow, resid, tall, cliff, t13, race, s6, timing, noise = c
    rows = [
        ("\\S7, Tables 1--12", "the tables come from the running model",
         f"the code reproduces {rep['reproduced']} of {rep['of']} printed figures at the generator's seed",
         _met(rep["met"])),
        ("\\S7, Tables 1--12", "the figures are the model's credit",
         f"every printed figure within {vs['worst_z']:.2f} standard errors of the exact value", _met(vs["met"])),
        ("\\S7.1", "the chain absorbs in $\\approx3$ steps", f"{absorb['exact']:.2f} steps (baseline)", _met(absorb["met"])),
        ("\\S7.1", "intensity climbs $\\approx0.8$ a step", f"{grow['exact']:.4f} (baseline)", _met(grow["met"])),
        ("Table 12", "non-combustible residual is sub-bp", f"at most {resid['exact']:.3f}\\,bp", _met(resid["met"])),
        ("Table 12, \\S8", "single-digit bps in very tall non-combustible assets",
         f"{tall['exact']:.4f}\\,bp at {tall['storeys']} storeys: height does not enter an unreachable race",
         _met(tall["met"])),
        ("Table 2", "the reach cliff is 203\\,bp", f"exactly {cliff['exact']:.1f}\\,bp; 203 is a draw ($z={cliff['z']:.2f}$)",
         _met(cliff["met"])),
        ("Table 13", "construction levers", f"{t13['reproduced']} of {t13['of']} reproduced from the formulae",
         _met(t13["met"])),
        ("FIRE-L3", "the chain absorbs before the race is lost",
         f"no suppression: race lost in {100 * race['race_lost']:.1f}\\% of fires, recorded in {100 * race['recorded']:.2f}\\%",
         _met(race["met"])),
        ("\\S3.5", "$S_6$ is absorbing", "the march stops at $S_6$, but every matrix carries an unused "
         f"$S_6\\to S_7$ row ({', '.join(f'{v:g}' for v in s6['escalation'].values())})", _met(s6["met"])),
        ("\\S3.3", "suppression is active from step $\\lceil\\tau_{\\mathrm{supp}}\\rceil$",
         "the code, and the config's own definition, use $\\lceil\\tau_{\\mathrm{det}}+\\tau_{\\mathrm{supp}}\\rceil$",
         _met(timing["met"])),
        ("Tables 4, 5, 9", f"containment {noise['printed_low']:.1f}--{noise['printed_high']:.1f}\\% by condition, type, occupancy",
         f"exactly {noise['exact_low']:.1f}\\% for all: these inputs move only the ignition rate", _met(noise["met"])),
    ]
    return tab("The model document's claims, tested", "tab:bm-claims", "p{24mm}p{44mm}p{68mm}l",
               "Claim & Stated & Benchmark finds & Outcome", rows)


def _f(x, k):
    return "--" if x is None else (f"{x:.1f}" if k != "loss" else f"{x:.3f}")


def _cells_table(rows):
    body = []
    for r in rows:
        zmax = max(abs(r[f"{k}_printed_z"]) for k in METRICS if f"{k}_printed_z" in r)
        body.append((str(r["table"]), esc(r["label"]),
                     *[_f(r.get(f"{k}_printed"), k) for k in METRICS],
                     *[_f(r[f"{k}_exact"], k) for k in METRICS], f"{zmax:.2f}"))
    return longtab("Every printed cell against the exact credit: containment (\\%), loss frequency "
                   "(\\%), fire spread (bp); $|z|$ is the worst printed figure in standard errors at "
                   f"{ORACLE_FIRE_N_SIM:,} draws".replace(",", "{,}"), "tab:bm-cells", "rlrrrrrrr",
                   "T & Cell & \\multicolumn{3}{c}{Printed} & \\multicolumn{3}{c}{Exact} & $|z|$", body)


def _production_table(rows):
    pick = ("T1/Not assessed", "T3/Partial", "T2/12 storeys", "T12/Timber frame")
    body = [(esc(r["id"]), f"{r['spread_bps_exact']:.2f}", f"{r['spread_bps_model']:.1f}",
             f"{r['spread_se_production']:.1f}")
            for r in rows if r["id"] in pick]
    return tab(f"The fire spread and its sampling error at the production draw count ({ORACLE_FIRE_PRODUCTION_N_SIM:,})"
               .replace(",", "{,}"), "tab:bm-production", "lrrr",
               "Cell & Exact (bp) & Model at 20k (bp) & Std error at production (bp)", body)


def macros(provs, rows, version, mode, c, wolfram_err):
    checks = findings(rows, wolfram_err)
    failed = sum(ok is False for *_, ok in checks)
    cliff = c[6]
    return as_macros({
        "bmGenerated": date.today().isoformat(),
        "bmCodeCommit": f"\\texttt{{{provs[0]['last_commit'][:12]}}}",
        "bmCodeDirty": " (with uncommitted changes)" if any(p["uncommitted_changes"] for p in provs) else "",
        "bmNumerics": ", ".join(f"{k} {v}" for k, v in provs[0]["packages"].items()),
        "bmWolfram": esc(version) if version else "not run",
        "bmWolframVia": f" via {mode}" if version else "",
        "bmWolframConfirms": (f"Wolfram and the 50-digit reference agree to {sci(wolfram_err)}."
                              if version else "Wolfram has not been run."),
        "bmCells": str(len(rows)), "bmAssets": str(len({r['asset'] for r in rows})),
        "bmChecks": str(len(checks)),
        "bmOutcome": ("all pass" if not failed else f"{failed} fail") + ("" if version else "; Wolfram pending"),
        "bmProfile": sci(max(r["profile_rel_err"] for r in rows)),
        "bmReproduced": str(c[0]["reproduced"]), "bmPrinted": str(c[0]["of"]),
        "bmWorstZ": f"{c[1]['worst_z']:.2f}", "bmAbsorb": f"{c[2]['exact']:.2f}",
        "bmGrowth": f"{c[3]['exact']:.3f}", "bmResidual": f"{c[4]['exact']:.3f}",
        "bmTall": f"{c[5]['exact']:.4f}",
        "bmCliff": f"{cliff['exact']:.1f}", "bmCliffSE": f"{cliff['production_se']:.0f}",
        "bmNoiseLow": f"{c[11]['printed_low']:.1f}", "bmNoiseHigh": f"{c[11]['printed_high']:.1f}",
        "bmNoiseExact": f"{c[11]['exact_low']:.1f}",
        "bmRaceLost": f"{100 * c[8]['race_lost']:.0f}", "bmRaceRecorded": f"{100 * c[8]['recorded']:.1f}",
        "bmNSim": f"{ORACLE_FIRE_N_SIM:,}".replace(",", "{,}"), "bmSeed": str(ORACLE_FIRE_SEED),
        "bmProductionN": f"{ORACLE_FIRE_PRODUCTION_N_SIM:,}".replace(",", "{,}"),
    })


def write_tables(out, provs, rows, version, mode, c, wolfram_err):
    return write_files(out, ORACLE_FIRE_TABLE_PREFIX, {
        "macros": macros(provs, rows, version, mode, c, wolfram_err),
        "findings": GENERATED + tab("Benchmark checks", "tab:bm-checks", "p{88mm}p{18mm}rl",
                                    "Check & Result & Limit & Outcome", _render(findings(rows, wolfram_err))),
        "claims": GENERATED + _claims_table(c),
        "cells": GENERATED + _cells_table(rows),
        "production": GENERATED + _production_table(rows),
    })
