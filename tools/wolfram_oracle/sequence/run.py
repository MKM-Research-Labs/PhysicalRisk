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

"""Run the SS-001 benchmark and write its evidence.

    python -m tools.wolfram_oracle ss001 [--out DIR] [--no-live] [--no-pdf]
"""

import argparse
from pathlib import Path

import mpmath as mp
from tools.wolfram_oracle._csv import write_csv
from tools.wolfram_oracle._model import provenance
from tools.wolfram_oracle._run import finish, wolfram
from tools.wolfram_oracle.sequence import cases, claims, evidence
from tools.wolfram_oracle.sequence import reference as ref
from tools.wolfram_oracle.sequence import wolfram as oracle
from tools.wolfram_oracle.sequence.latex import write_tables

from config import config
from config.models import (
    ORACLE_REFERENCE_DPS,
    ORACLE_SS_CSV,
    ORACLE_SS_DOC,
    ORACLE_SS_OUT_DIR,
    ORACLE_SS_SOURCES,
    ORACLE_SS_WEIGHTS,
    ORACLE_SS_WL,
)


def evaluate(code):
    """Every code-against-reference result, and the claims."""
    exact = ref.batch(ORACLE_SS_WEIGHTS)
    with mp.workdps(ORACLE_REFERENCE_DPS):
        rp = cases.replay(code)
    mc = cases.monte_carlo(code, rp["batch"], exact)
    r = {"replay": rp, "mc": mc, "validator": cases.validator(code, rp["batch"] + rp["forced"]), "exact": exact,
         "season": len({q.sequence_start[:7] for q in rp["batch"]})}
    return r, claims.assess(code, rp, mc, exact), evidence.assess(code)


def rows_for_csv(r, c):
    rows = [{"check": f"replay_{k}", "value": r["replay"][k]} for k in ("sequences", "structure_off", "worst")]
    rows += [{"check": f"exact_type_{t}", "value": float(p)} for t, p in r["exact"]["types"].items()]
    rows += [{"check": f"exact_count_{n}", "value": float(p)} for n, p in r["exact"]["counts"].items()]
    rows += [{"check": f"exact_{k}", "value": float(r["exact"][k])} for k in ("cap_share", "zero_share", "compressed_share")]
    rows += [{"check": f"mc_{k}", "value": r["mc"][k]} for k in ("z_types", "z_counts", "z_zero", "multi", "zero")]
    rows += [{"check": f"seed{k}_{t}", "value": n} for k, p in enumerate(r["mc"]["per_seed"]) for t, n in p.items()]
    return rows + [{"check": f"validator_{k}", "value": v} for k, v in r["validator"].items()]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle ss001")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_SS_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    code = cases.load()
    r, c, e = evaluate(code)
    items = [(i, x) for i, x, _ in oracle.items()]
    version, results, mode = wolfram(out, [(ORACLE_SS_WL, items)], not args.no_live)
    r["wolfram"] = oracle.judge(results[0]) if version else None

    write_csv(out / ORACLE_SS_CSV, rows_for_csv(r, c))
    write_tables(out, [provenance(s) for s in ORACLE_SS_SOURCES], r, version, mode, c, e)
    return finish(out, ORACLE_SS_DOC, version, mode, args.no_pdf)
