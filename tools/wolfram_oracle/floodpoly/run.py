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
"""Run the FPO-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle fpo001 [--out DIR] [--no-live] [--no-pdf]

The GBM comparison reads the storm catalogue and the classifiers from the data
store; from a worktree, point MKM_DATA_ROOT at it.
"""

import argparse
from pathlib import Path

from config import config
from config.models import (
    ORACLE_FPO_CSV,
    ORACLE_FPO_DOC,
    ORACLE_FPO_OUT_DIR,
    ORACLE_FPO_SCENARIO,
    ORACLE_FPO_SOURCES,
    ORACLE_FPO_WL,
)
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._model import provenance
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle.floodpoly import cases, claims, gbm
from tools.wolfram_oracle.floodpoly import wolfram as oracle
from tools.wolfram_oracle.floodpoly.latex import write_tables


def evaluate(m):
    """The code checks, the GBM comparison and the claims."""
    gauges, top = gbm.compare(claims.predict)
    held = gbm.heldout(claims.predict)
    scenario = (config.get_project_root() / ORACLE_FPO_SCENARIO).read_text()
    c = claims.assess(m["poly"], top, held, scenario)
    return {"code": cases.run(m), "gauges": gauges, "held": held}, c


def rows_for_csv(r):
    return [{"gauge": g["gauge"], "band": band, **g[band]} for g in r["gauges"] for band in ("below", "near")]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle fpo001")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_FPO_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    r, c = evaluate(cases.load())
    version, results, mode = wolfram(out, [(ORACLE_FPO_WL, [(i, e) for i, e, _ in oracle.items()])], not args.no_live)
    r["wolfram"] = oracle.judge(results[0]) if version else None

    write_csv(out / ORACLE_FPO_CSV, rows_for_csv(r))
    write_tables(out, [provenance(s) for s in ORACLE_FPO_SOURCES], r, version, mode, c)
    return finish(out, ORACLE_FPO_DOC, version, mode, args.no_pdf)
