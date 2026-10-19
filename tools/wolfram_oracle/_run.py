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

"""What every benchmark run does around its model: reach Wolfram, build the PDF.

One live session covers all of a run's expressions (the kernel takes over half
a minute to start); without a kernel each group falls back to its ``.wl``
script's output. The document is built by its directory's Makefile.
"""

import subprocess
import sys
from pathlib import Path

from config.models import (
    ORACLE_WOLFRAM_KERNEL,
    ORACLE_WOLFRAM_STARTUP_TIMEOUT,
    ORACLE_WOLFRAM_SUFFIX,
)
from tools.wolfram_oracle._wl import evaluate_live, load_wolfram, save_wolfram, write_wl


def from_file(out, wl_name, items):
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


def wolfram(out, groups, live):
    """Wolfram's answers for each ``(wl_name, items)`` group: (version, [results], mode).

    A live run's answers are saved exactly as a wolframscript run would save them.
    """
    files = [from_file(out, name, items) for name, items in groups]
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


def finish(out, doc, version, mode, no_pdf):
    """Report the Wolfram route and build the document; the exit code."""
    print(f"Wolfram: {version + ' via ' + mode if version else 'not run'}")
    if no_pdf:
        return 0
    built = build_pdf(out)
    print(f"{'Built' if built else 'Could not build'} {out / (doc + '.pdf')}")
    return 0 if built else 1
