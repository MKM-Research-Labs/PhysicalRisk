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

"""Run the MP-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle mp001 [--out DIR] [--no-live] [--no-pdf]
"""

import argparse
import importlib
from pathlib import Path

import mpmath as mp

from config import config
from config.models import (
    ORACLE_MP_CSV,
    ORACLE_MP_DOC,
    ORACLE_MP_OUT_DIR,
    ORACLE_MP_PACKAGE,
    ORACLE_MP_SOURCES,
    ORACLE_MP_WL,
    ORACLE_REFERENCE_DPS,
)
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._model import provenance
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle._wl import rel_err, wl_number
from tools.wolfram_oracle.mortgage import cases, claims
from tools.wolfram_oracle.mortgage.latex import write_tables


def _add_wolfram(rows, wl):
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for r in rows:
            r["wolfram_fv"] = wl[f"{r['id']}/fv"]
            r["wolfram_fv_vs_ref"] = rel_err(wl_number(wl[f"{r['id']}/fv"]), r["fv_ref"])
            r["wolfram_path_vs_ref"] = rel_err(wl_number(wl[f"{r['id']}/path"]), r["pathwise"])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle mp001")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_MP_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    pricer = importlib.import_module(ORACLE_MP_PACKAGE)
    rows = cases.run(pricer)
    lookup = {cases.case_id(k): k for k in cases.loans()}
    items = cases.wl_items(rows, lookup) + claims.wl_claim_items()
    version, results, mode = wolfram(out, [(ORACLE_MP_WL, items)], not args.no_live)
    wl = results[0] if version else None
    if version:
        _add_wolfram(rows, wl)

    write_csv(out / ORACLE_MP_CSV, rows)
    write_tables(out, [provenance(s) for s in ORACLE_MP_SOURCES], rows, version, mode, pricer, wl)
    return finish(out, ORACLE_MP_DOC, version, mode, args.no_pdf)
