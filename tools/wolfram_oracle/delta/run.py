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

"""Run the DE-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle de001 [--out DIR] [--no-live] [--no-pdf]

Writes ``evidence_tables_*.tex`` and ``delta.csv`` into
``docs/models/delta_engine_benchmark`` and builds
``MKM-DE-001_wolfram_benchmark.pdf`` there.
"""

import argparse
import importlib
from pathlib import Path

import mpmath as mp

from config import config
from config.models import (
    ORACLE_DE_CLAIM_HAND,
    ORACLE_DE_CLAIM_YIELD_SHIFT,
    ORACLE_DE_CSV,
    ORACLE_DE_DOC,
    ORACLE_DE_FLAT_RATE,
    ORACLE_DE_OUT_DIR,
    ORACLE_DE_PACKAGE,
    ORACLE_DE_SOURCES,
    ORACLE_DE_TABLE_TENOR,
    ORACLE_DE_WL,
    ORACLE_REFERENCE_DPS,
)
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._model import provenance
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle._wl import rel_err, wl_number
from tools.wolfram_oracle.delta import claims, sensitivity
from tools.wolfram_oracle.delta.latex import write_tables


def _claim_error(results):
    """Worst gap between Wolfram and the reference on the claims' own figures."""
    h, t, r, _ = ORACLE_DE_CLAIM_HAND
    ref = {"claim/hand_annuity": sensitivity.legs(h, t, None, shift=r - ORACLE_DE_FLAT_RATE)[1],
           "claim/fs01_base": sensitivity.fs01(0.02, ORACLE_DE_TABLE_TENOR, None, notional=1),
           "claim/fs01_shifted": sensitivity.fs01(0.02, ORACLE_DE_TABLE_TENOR, None,
                                                  shift=ORACLE_DE_CLAIM_YIELD_SHIFT, notional=1)}
    with mp.workdps(ORACLE_REFERENCE_DPS):
        return max(rel_err(wl_number(results[k]), v) for k, v in ref.items())


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle de001")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_DE_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    pricer = importlib.import_module(ORACLE_DE_PACKAGE)
    rows = sensitivity.run(pricer)
    items = sensitivity.wl_items(rows) + claims.wl_claim_items()
    version, results, mode = wolfram(out, [(ORACLE_DE_WL, items)], not args.no_live)
    claim_err = None
    if version:
        sensitivity.add_wolfram(rows, results[0])
        claim_err = _claim_error(results[0])

    write_csv(out / ORACLE_DE_CSV, rows)
    write_tables(out, [provenance(s) for s in ORACLE_DE_SOURCES], rows, version, mode, claim_err)
    return finish(out, ORACLE_DE_DOC, version, mode, args.no_pdf)
