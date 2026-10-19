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

"""Run the GH-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle gh001 [--gauges FILE] [--out DIR] [--no-live] [--no-pdf]

Writes ``evidence_tables_*.tex`` and the CSVs into ``docs/models/gev_hazard_benchmark``
and builds ``MKM-GH-001_wolfram_benchmark.pdf`` there.
"""

import argparse
from pathlib import Path

from config import config
from config.models import (
    ORACLE_FIT_SEED,
    ORACLE_GEV_DOC,
    ORACLE_GEV_FIT_CSV,
    ORACLE_GEV_FIT_WL,
    ORACLE_GEV_OUT_DIR,
    ORACLE_GEV_RETURN_LEVELS_CSV,
    ORACLE_GEV_RETURN_LEVELS_WL,
)
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle.gev import fit, return_levels
from tools.wolfram_oracle.gev._code import gev_provenance, load_gev_fitter
from tools.wolfram_oracle.gev.latex import write_tables


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle gh001")
    ap.add_argument("--gauges", help="JSON: gauge id -> peak levels or gauge record")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_GEV_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    gev_fitter = load_gev_fitter()
    rl_rows = return_levels.run(gev_fitter)
    if args.gauges:
        series, source = fit.load_gauges(args.gauges), f"gauge export {Path(args.gauges).name}"
    else:
        series = fit.synthetic_series()
        source = f"synthetic samples from known parameters, seed {ORACLE_FIT_SEED}"
    fit_rows = fit.run(gev_fitter, series)

    version, results, mode = wolfram(out, [
        (ORACLE_GEV_RETURN_LEVELS_WL, return_levels.wl_items(rl_rows)),
        (ORACLE_GEV_FIT_WL, fit.wl_items(fit_rows))], not args.no_live)
    if version:
        return_levels.add_wolfram(rl_rows, results[0])
        fit.add_wolfram(fit_rows, results[1])

    write_csv(out / ORACLE_GEV_RETURN_LEVELS_CSV, rl_rows)
    write_csv(out / ORACLE_GEV_FIT_CSV, fit_rows, skip=("x",))
    write_tables(out, gev_provenance(), source, rl_rows, fit_rows, version, mode,
                 return_levels.sign_trap())
    return finish(out, ORACLE_GEV_DOC, version, mode, args.no_pdf)
