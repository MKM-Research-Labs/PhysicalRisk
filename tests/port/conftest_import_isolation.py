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

"""Shared helpers for import-isolation tests (used by test_import_isolation_part*.py)."""

import sys


def _simulate_no_quantlib(monkeypatch):
    """
    Block 'QuantLib' in sys.modules so any `import QuantLib` raises ImportError.

    Python treats sys.modules[name] = None as a "blocked" import -- it raises
    ImportError immediately rather than searching for the package.
    """
    for key in list(sys.modules.keys()):
        if key == "QuantLib" or key.startswith("QuantLib."):
            monkeypatch.delitem(sys.modules, key, raising=False)
    monkeypatch.setitem(sys.modules, "QuantLib", None)


def _drop_port_src_cache(monkeypatch):
    """Remove all port.src.* entries from sys.modules so they reimport fresh."""
    for key in list(sys.modules.keys()):
        if key == "port.src" or key.startswith("port.src."):
            monkeypatch.delitem(sys.modules, key, raising=False)
