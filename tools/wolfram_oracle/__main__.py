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

    python -m tools.wolfram_oracle [--gauges FILE] [--out DIR] [--no-live] [--no-pdf]

With an activated Wolfram Engine and ``wolframclient`` installed, one run
evaluates every oracle and fit in a live kernel. Without them it writes the
``.wl`` scripts instead; run them with ``wolframscript -file`` and run this again
to fold their output in. Wolfram output produced for different inputs is
ignored rather than trusted.

Every run rewrites the generated ``evidence_tables_*.tex`` and the CSVs, then
builds ``MKM-GH-001_wolfram_benchmark.pdf`` from the hand-written document with
the directory's Makefile (``--no-pdf`` skips that step).
"""

import argparse
import subprocess
import sys
from pathlib import Path

from config import config
from config.models import (
    ORACLE_FIT_SEED,
    ORACLE_GEV_DOC,
    ORACLE_GEV_FIT_CSV,
    ORACLE_GEV_FIT_WL,
    ORACLE_GEV_OUT_DIR,
    ORACLE_GEV_RETURN_LEVELS_CSV,
    ORACLE_GEV_RETURN_LEVELS_WL,
    ORACLE_WOLFRAM_KERNEL,
    ORACLE_WOLFRAM_STARTUP_TIMEOUT,
    ORACLE_WOLFRAM_SUFFIX,
)
from tools.wolfram_oracle import fit, return_levels
from tools.wolfram_oracle._model import load_gev_fitter, provenance
from tools.wolfram_oracle._wl import evaluate_live, load_wolfram, save_wolfram, write_wl
from tools.wolfram_oracle.latex import write_tables
from tools.wolfram_oracle._csv import write_csv


def _from_file(out, wl_name, items):
    """Write the .wl; return (version, results) from its matching wolframscript output."""
    wl_path = out / wl_name
    result = wl_path.with_name(wl_path.stem + ORACLE_WOLFRAM_SUFFIX)
    write_wl(wl_path, items, result.name)
    version, values = load_wolfram(result)
    if values is not None and set(values) != {i for i, _ in items}:
        print(f"Ignoring {result.name}: it was produced for different inputs. "
              f"Re-run wolframscript -file {wl_path}", file=sys.stderr)
        return None, None
    return version, values


def _wolfram(out, groups, live):
    """Wolfram's answers for each ``(wl_name, items)`` group: (version, [results], mode).

    One live session covers every group — the kernel takes over half a minute to
    start — and its answers are saved exactly as a wolframscript run would save
    them. Without a kernel, each group falls back to its .wl output file.
    """
    files = [_from_file(out, name, items) for name, items in groups]
    if live:
        version, values = evaluate_live([it for _, items in groups for it in items],
                                        ORACLE_WOLFRAM_KERNEL, ORACLE_WOLFRAM_STARTUP_TIMEOUT)
        if values is not None:
            split = [{i: values[i] for i, _ in items} for _, items in groups]
            for (name, _), part in zip(groups, split):
                save_wolfram(out / (Path(name).stem + ORACLE_WOLFRAM_SUFFIX), version, part)
            return version, split, "live kernel session (wolframclient)"
    if all(values is not None for _, values in files):
        return files[0][0], [values for _, values in files], "wolframscript file"
    return None, None, None


def build_pdf(out):
    """Build the document with its Makefile, then clear the LaTeX intermediates.

    False if that is not possible here (no Makefile, or the build failed — its
    .log is then left in place to read).
    """
    if not (out / "Makefile").exists():
        return False
    if subprocess.run(["make", "-C", str(out)], capture_output=True).returncode != 0:
        return False
    subprocess.run(["make", "-C", str(out), "clean"], capture_output=True)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.wolfram_oracle")
    ap.add_argument("--gauges", help="JSON: gauge id -> peak levels or gauge record")
    ap.add_argument("--out", help="output directory (default: the configured one)")
    ap.add_argument("--no-live", action="store_true", help="do not start a Wolfram kernel")
    ap.add_argument("--no-pdf", action="store_true", help="write the tables, skip the build")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else config.get_project_root() / ORACLE_GEV_OUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    gev_fitter = load_gev_fitter()
    rl_rows = return_levels.run(gev_fitter)
    if args.gauges:
        series, source = fit.load_gauges(args.gauges), f"gauge export {Path(args.gauges).name}"
    else:
        series = fit.synthetic_series()
        source = f"synthetic samples from known parameters, seed {ORACLE_FIT_SEED}"
    fit_rows = fit.run(gev_fitter, series)

    live = not args.no_live
    version, results, mode = _wolfram(out, [
        (ORACLE_GEV_RETURN_LEVELS_WL, return_levels.wl_items(rl_rows)),
        (ORACLE_GEV_FIT_WL, fit.wl_items(fit_rows))], live)
    if version:
        return_levels.add_wolfram(rl_rows, results[0])
        fit.add_wolfram(fit_rows, results[1])

    write_csv(out / ORACLE_GEV_RETURN_LEVELS_CSV, rl_rows)
    write_csv(out / ORACLE_GEV_FIT_CSV, fit_rows, skip=("x",))
    write_tables(out, provenance(), source, rl_rows, fit_rows, version, mode,
                 return_levels.sign_trap())
    print(f"Wolfram: {version + ' via ' + mode if version else 'not run'}")
    if not args.no_pdf:
        built = build_pdf(out)
        print(f"{'Built' if built else 'Could not build'} {out / (ORACLE_GEV_DOC + '.pdf')}")
        if not built:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
