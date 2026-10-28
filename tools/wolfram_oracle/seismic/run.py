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

"""Run the SEIS-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle seis001 [--out DIR] [--no-live] [--no-pdf]
"""

import argparse
from pathlib import Path

import mpmath as mp

from config import config
from config.models import (
    ORACLE_REFERENCE_DPS,
    ORACLE_SEIS_CSV,
    ORACLE_SEIS_DOC,
    ORACLE_SEIS_OUT_DIR,
    ORACLE_SEIS_SOURCES,
    ORACLE_SEIS_WL,
)
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._model import provenance
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle._wl import rel_err, wl_number
from tools.wolfram_oracle.seismic import cases, claims, exact
from tools.wolfram_oracle.seismic.latex import write_tables


def wolfram_error(exact_by, wl):
    """Worst disagreement between Wolfram's P(DS >= i) and the reference's."""
    ids, worst = cases.asset_ids(exact_by), 0.0
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for key, (_, ex, *_) in exact_by.items():
            for got, ds in zip(wl_number(wl[ids[key]]), exact.DS):
                worst = max(worst, float(rel_err(got, ex["p"][ds]) if ex["p"][ds] else abs(got)))
    return worst


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle seis001")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_SEIS_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    m = cases.load()
    rows, exact_by = cases.run(m)
    version, results, mode = wolfram(out, [(ORACLE_SEIS_WL, cases.wl_items(exact_by, m))], not args.no_live)
    werr = wolfram_error(exact_by, results[0]) if version else None

    write_csv(out / ORACLE_SEIS_CSV, rows)
    c = claims.assess(rows, m)
    write_tables(out, [provenance(s) for s in ORACLE_SEIS_SOURCES], rows, version, mode, c, werr)
    return finish(out, ORACLE_SEIS_DOC, version, mode, args.no_pdf)
