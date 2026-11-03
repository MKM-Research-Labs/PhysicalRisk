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

"""Run the GHD-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle ghd001 [--out DIR] [--no-live] [--no-pdf]
"""

import argparse
from pathlib import Path

import mpmath as mp

from config import config
from config.models import ORACLE_GHD_CSV, ORACLE_GHD_DOC, ORACLE_GHD_OUT_DIR, ORACLE_GHD_SOURCES, ORACLE_GHD_WL
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._model import provenance
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle._wl import rel_err, wl_number
from tools.wolfram_oracle.gaugehd import cases, claims
from tools.wolfram_oracle.gaugehd.latex import write_tables


def wolfram_error(wl):
    ref = cases.reference_points()
    return max(float(rel_err(wl_number(wl[k]), mp.mpf(v))) for k, v in ref.items())


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle ghd001")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_GHD_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    rows, _ = cases.run(cases.load())
    version, results, mode = wolfram(out, [(ORACLE_GHD_WL, cases.wl_items())], not args.no_live)
    werr = wolfram_error(results[0]) if version else None

    write_csv(out / ORACLE_GHD_CSV, rows)
    c = claims.assess(rows)
    write_tables(out, [provenance(s) for s in ORACLE_GHD_SOURCES], rows, version, mode, c, werr)
    return finish(out, ORACLE_GHD_DOC, version, mode, args.no_pdf)
