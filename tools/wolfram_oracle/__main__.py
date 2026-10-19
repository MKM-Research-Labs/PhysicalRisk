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

    python -m tools.wolfram_oracle [--gauges FILE] [--out DIR]
    wolframscript -file docs/models/benchmark/gev_hazard/return_levels.wl
    wolframscript -file docs/models/benchmark/gev_hazard/fit.wl
    python -m tools.wolfram_oracle [--gauges FILE]   # again: now Wolfram is in the report

Each run re-reads whatever Wolfram output sits beside the .wl files, so the
second run folds it into the PDF and CSVs. Wolfram output older than the inputs
would be silently wrong, so it is only used when its ids match this run's.
The PDF and both CSVs are what get filed in ModelRisk as a Benchmark Test.
"""

import argparse
import sys
from pathlib import Path

from config import config
from config.models import (
    ORACLE_GEV_FIT_CSV,
    ORACLE_GEV_FIT_WL,
    ORACLE_GEV_OUT_DIR,
    ORACLE_GEV_REPORT_PDF,
    ORACLE_GEV_RETURN_LEVELS_CSV,
    ORACLE_GEV_RETURN_LEVELS_WL,
    ORACLE_FIT_SEED,
    ORACLE_WOLFRAM_SUFFIX,
)
from tools.wolfram_oracle import fit, return_levels
from tools.wolfram_oracle._model import load_gev_fitter, provenance
from tools.wolfram_oracle._wl import load_wolfram, write_wl
from tools.wolfram_oracle.report import write_csv, write_pdf


def _wolfram(out, wl_name, items):
    """Write the .wl; return (version, results) if a matching Wolfram run exists."""
    wl_path = out / wl_name
    result = wl_path.with_name(wl_path.stem + ORACLE_WOLFRAM_SUFFIX)
    write_wl(wl_path, items, result.name)
    version, values = load_wolfram(result)
    if values is not None and set(values) != {i for i, _ in items}:
        print(f"Ignoring {result.name}: it was produced for different inputs. "
              f"Re-run wolframscript -file {wl_path}", file=sys.stderr)
        return None, None
    return version, values


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle")
    ap.add_argument("--gauges", help="JSON: gauge id -> peak levels or gauge record")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_GEV_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    gev_fitter = load_gev_fitter()
    rl_rows = return_levels.run(gev_fitter)
    if args.gauges:
        series, source = fit.load_gauges(args.gauges), f"gauge export {args.gauges}"
    else:
        series = fit.synthetic_series()
        source = f"synthetic samples from known parameters, seed {ORACLE_FIT_SEED}"
    fit_rows = fit.run(gev_fitter, series)

    v1, wl_rl = _wolfram(out, ORACLE_GEV_RETURN_LEVELS_WL, return_levels.wl_items(rl_rows))
    v2, wl_fit = _wolfram(out, ORACLE_GEV_FIT_WL, fit.wl_items(fit_rows))
    version = v1 if (wl_rl and wl_fit) else None
    if version:
        return_levels.add_wolfram(rl_rows, wl_rl)
        fit.add_wolfram(fit_rows, wl_fit)

    write_csv(out / ORACLE_GEV_RETURN_LEVELS_CSV, rl_rows)
    write_csv(out / ORACLE_GEV_FIT_CSV, fit_rows, skip=("x",))
    pdf = out / ORACLE_GEV_REPORT_PDF
    write_pdf(pdf, provenance(), source, rl_rows, fit_rows, version, return_levels.sign_trap())
    print(f"Wrote {pdf}\nWolfram: {version or 'not run — see the .wl files in ' + str(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
