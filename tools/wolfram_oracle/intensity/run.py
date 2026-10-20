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

"""Run the SI-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle si001 [--out DIR] [--no-live] [--no-pdf]

Writes ``evidence_tables_*.tex`` and ``intensity.csv`` into
``docs/models/storm_intensity_benchmark`` and builds
``MKM-SI-001_wolfram_benchmark.pdf`` there.
"""

import argparse
import importlib
from pathlib import Path

import mpmath as mp

from config import config
from config.models import (
    ORACLE_SI_CSV,
    ORACLE_SI_DOC,
    ORACLE_SI_OUT_DIR,
    ORACLE_SI_PACKAGE,
    ORACLE_SI_SOURCES,
    ORACLE_SI_WL,
)
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._model import provenance
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle._wl import rel_err, wl_number
from tools.wolfram_oracle.intensity import claims, distribution
from tools.wolfram_oracle.intensity.latex import write_tables


def _moment_error(scenarios, results):
    """Worst relative gap between Wolfram's and the reference's E[Q] and E[Q^2]."""
    worst = 0.0
    for s in scenarios:
        m2 = mp.mpf(s["sd"]) ** 2 + mp.mpf(s["mean"]) ** 2
        worst = max(worst, rel_err(wl_number(results[f"{s['scenario']}/m1"]), s["mean"]),
                    rel_err(wl_number(results[f"{s['scenario']}/m2"]), m2))
    return worst


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle si001")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_SI_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    package = importlib.import_module(ORACLE_SI_PACKAGE)
    dist_cls, families = package.IntensityDistribution, package.SCENARIO_FAMILIES
    rows, ack_rows = distribution.run(dist_cls, families), distribution.acklam(dist_cls)
    scenarios = claims.by_scenario(dist_cls, families)
    items = distribution.wl_items(rows, ack_rows, families) + claims.wl_moment_items(families)
    version, results, mode = wolfram(out, [(ORACLE_SI_WL, items)], not args.no_live)
    moment_err = None
    if version:
        distribution.add_wolfram(rows, ack_rows, results[0])
        moment_err = _moment_error(scenarios, results[0])

    write_csv(out / ORACLE_SI_CSV, rows + ack_rows)
    write_tables(out, [provenance(s) for s in ORACLE_SI_SOURCES], rows, ack_rows,
                 claims.assess(scenarios, ack_rows), scenarios, families, version, mode, moment_err)
    return finish(out, ORACLE_SI_DOC, version, mode, args.no_pdf)
