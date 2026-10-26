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

"""Run the EF-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle ef001 [--out DIR] [--no-live] [--no-pdf]
"""

import argparse
from pathlib import Path

import mpmath as mp

from config import config
from config.models import (
    ORACLE_EF_CSV,
    ORACLE_EF_DOC,
    ORACLE_EF_OUT_DIR,
    ORACLE_EF_SOURCES,
    ORACLE_EF_TERM_SOURCE,
    ORACLE_EF_WL,
    ORACLE_REFERENCE_DPS,
)
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._model import provenance
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle._wl import rel_err, wl_number
from tools.wolfram_oracle.frequency import cases, claims
from tools.wolfram_oracle.frequency.latex import write_tables


def _add_wolfram(rows, wl):
    with mp.workdps(ORACLE_REFERENCE_DPS):
        for r in rows:
            w = wl_number(wl[r["id"]])
            if r["group"] == "nb_ll":
                r["wolfram_ll_gain"] = float(w - mp.mpf(r["ref"]))
            else:
                r["wolfram"] = mp.nstr(w, 30)
                r["wolfram_vs_ref"] = rel_err(w, r["ref"])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle ef001")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_EF_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    m = cases.load()
    rows = cases.annualisation(m) + cases.term(m) + cases.compound(m) + cases.families(m)
    items = cases.wl_items(rows) + claims.wl_claim_items()
    version, results, mode = wolfram(out, [(ORACLE_EF_WL, items)], not args.no_live)
    wl = results[0] if version else None
    if version:
        _add_wolfram(rows, wl)

    write_csv(out / ORACLE_EF_CSV, [{k: v for k, v in r.items() if k not in ("w", "loss", "counts")}
                                    for r in rows])
    provs = [provenance(s) for s in list(ORACLE_EF_SOURCES.values()) + [ORACLE_EF_TERM_SOURCE]]
    write_tables(out, provs, rows, version, mode, wl)
    return finish(out, ORACLE_EF_DOC, version, mode, args.no_pdf)
