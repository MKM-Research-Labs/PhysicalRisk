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

"""Run the SP-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle sp001 [--out DIR] [--no-live] [--no-pdf]
"""

import argparse
from pathlib import Path

import mpmath as mp

from config import config
from config.models import (
    ORACLE_REFERENCE_DPS,
    ORACLE_SP_CSV,
    ORACLE_SP_DOC,
    ORACLE_SP_OUT_DIR,
    ORACLE_SP_SOURCES,
    ORACLE_SP_WL,
)
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._model import provenance
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle.spatial import cases, claims
from tools.wolfram_oracle.spatial import wolfram as oracle
from tools.wolfram_oracle.spatial.latex import write_tables


def evaluate(sp):
    """Every code-against-reference result, and the claims."""
    with mp.workdps(ORACLE_REFERENCE_DPS):
        det, proj, tree = cases.deterministic(sp), cases.projection(sp), cases.tree(sp)
    return {"det": det, "proj": proj, "tree": tree}, claims.assess(sp, proj, tree, det)


def rows_for_csv(r):
    rows = [{"check": k, "value": v} for k, v in r["det"].items()]
    rows += [{"check": f"projection_{k}", "value": v} for k, v in r["proj"].items() if k != "table4"]
    rows += [{"check": f"table4_{km}km", "value": f"{pct}% {m} m"} for km, pct, m in r["proj"]["table4"]]
    return rows + [{"check": f"tree_{k}", "value": v} for k, v in r["tree"].items() if k != "distances_m"]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle sp001")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_SP_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    sp = cases.load()
    r, c = evaluate(sp)
    items = [(i, e) for i, e, _ in oracle.items()]
    version, results, mode = wolfram(out, [(ORACLE_SP_WL, items)], not args.no_live)
    r["wolfram"] = oracle.judge(sp, results[0]) if version else None

    write_csv(out / ORACLE_SP_CSV, rows_for_csv(r))
    write_tables(out, [provenance(s) for s in ORACLE_SP_SOURCES], r, version, mode, c)
    return finish(out, ORACLE_SP_DOC, version, mode, args.no_pdf)
