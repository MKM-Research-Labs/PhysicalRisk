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

"""The code under test — GH-001's GEVFitter — and the provenance that names it.

``src.models.hazard`` cannot simply be imported: its ``__init__`` pulls in the
builder and io, and through them the database seam, which touches the data
directory on import. A benchmark of four closed-form methods has no business
needing the data store, so ``gev.py`` is loaded on its own, inside a stand-in
package whose path is the real hazard directory — its relative
``from .data_structures import`` still resolves to the real module.
"""

import hashlib
import importlib.metadata
import importlib.util
import subprocess
import sys
import types

from config import config

_PKG = "_gh001_hazard"


def hazard_dir():
    return config.get_project_root() / "src" / "models" / "hazard"


def load_gev_fitter():
    """GH-001's GEVFitter class, from its file and nothing else."""
    pkg = types.ModuleType(_PKG)
    pkg.__path__ = [str(hazard_dir())]
    sys.modules.setdefault(_PKG, pkg)
    spec = importlib.util.spec_from_file_location(f"{_PKG}.gev", hazard_dir() / "gev.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.GEVFitter


def _git(*args):
    root = str(config.get_project_root())
    return subprocess.run(["git", "-C", root, *args],
                          capture_output=True, text=True).stdout.strip()


def provenance():
    """Which code, and which numerics, the evidence was produced against."""
    src = hazard_dir() / "gev.py"
    return {
        "file": "src/models/hazard/gev.py",
        "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "last_commit": _git("log", "-1", "--format=%H", "--", str(src)),
        "uncommitted_changes": bool(_git("status", "--porcelain", "--", str(src))),
        "packages": {p: importlib.metadata.version(p) for p in ("numpy", "scipy", "mpmath")},
    }
