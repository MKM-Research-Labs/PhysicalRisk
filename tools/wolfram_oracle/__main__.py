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

"""Run one model's Wolfram oracle benchmark and write its evidence.

    python -m tools.wolfram_oracle gh001 [--gauges FILE] [--out DIR] [--no-live] [--no-pdf]
    python -m tools.wolfram_oracle pr001 [--out DIR] [--no-live] [--no-pdf]
    python -m tools.wolfram_oracle si001 [--out DIR] [--no-live] [--no-pdf]
    python -m tools.wolfram_oracle de001 [--out DIR] [--no-live] [--no-pdf]
    python -m tools.wolfram_oracle ef001 [--out DIR] [--no-live] [--no-pdf]
    python -m tools.wolfram_oracle mp001 [--out DIR] [--no-live] [--no-pdf]
    python -m tools.wolfram_oracle seis001 [--out DIR] [--no-live] [--no-pdf]
    python -m tools.wolfram_oracle fire001 [--out DIR] [--no-live] [--no-pdf]

With an activated Wolfram Engine and ``wolframclient`` installed, one run
evaluates every oracle in a live kernel. Without them it writes ``.wl`` scripts
instead; run them with ``wolframscript -file`` and run this again to fold their
output in. Every run rewrites the generated ``evidence_tables_*.tex`` and the
CSVs, then builds the model's PDF with its directory's Makefile.
"""

import importlib
import sys

# Model key -> the module whose main() runs that benchmark.
BENCHMARKS = {
    "gh001": "tools.wolfram_oracle.gev.run",
    "pr001": "tools.wolfram_oracle.prs.run",
    "si001": "tools.wolfram_oracle.intensity.run",
    "de001": "tools.wolfram_oracle.delta.run",
    "ef001": "tools.wolfram_oracle.frequency.run",
    "mp001": "tools.wolfram_oracle.mortgage.run",
    "seis001": "tools.wolfram_oracle.seismic.run",
    "fire001": "tools.wolfram_oracle.fire.run",
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in BENCHMARKS:
        print(f"usage: python -m tools.wolfram_oracle {{{','.join(BENCHMARKS)}}} [options]",
              file=sys.stderr)
        return 2
    return importlib.import_module(BENCHMARKS[argv[0]]).main(argv[1:])


if __name__ == "__main__":
    sys.exit(main())
