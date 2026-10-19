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

"""Run the PR-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle pr001 [--out DIR] [--no-live] [--no-pdf]

Writes ``evidence_tables_*.tex`` and ``spreads.csv`` into
``docs/models/prs_pricing_benchmark`` and builds
``MKM-PR-001_wolfram_benchmark.pdf`` there.
"""

import argparse
from pathlib import Path

from config import config
from config.models import (
    ORACLE_PRS_DOC,
    ORACLE_PRS_OUT_DIR,
    ORACLE_PRS_SOURCE,
    ORACLE_PRS_SPREADS_CSV,
    ORACLE_PRS_SPREADS_WL,
)
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._model import load_module, provenance
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle.prs import spread
from tools.wolfram_oracle.prs.latex import write_tables


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle pr001")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_PRS_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    pricing = load_module(ORACLE_PRS_SOURCE)
    rows = spread.run(pricing)
    rules = spread.rules(pricing)
    version, results, mode = wolfram(
        out, [(ORACLE_PRS_SPREADS_WL, spread.wl_items(rows))], not args.no_live)
    if version:
        spread.add_wolfram(rows, results[0])

    write_csv(out / ORACLE_PRS_SPREADS_CSV, rows)
    write_tables(out, provenance(ORACLE_PRS_SOURCE), rows, rules, version, mode)
    return finish(out, ORACLE_PRS_DOC, version, mode, args.no_pdf)
