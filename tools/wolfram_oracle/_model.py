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

"""Load the code under test from its file, and the provenance that names it.

A model's package cannot simply be imported: ``src.models.hazard``'s
``__init__`` pulls in the builder and io, and through them the database seam,
which touches the data directory on import. A benchmark of closed-form methods
has no business needing the data store, so each source file is loaded on its
own, inside a stand-in package whose path is the file's real directory — a
relative import such as ``from .data_structures import`` still resolves to the
real module.
"""

import hashlib
import importlib.metadata
import importlib.util
import subprocess
import sys
import types

from config import config


def load_module(relpath):
    """The module at ``relpath`` (from the project root), and nothing around it."""
    path = config.get_project_root() / relpath
    pkg_name = "_oracle_" + "_".join(path.parent.relative_to(config.get_project_root()).parts)
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(path.parent)]
        sys.modules[pkg_name] = pkg
    spec = importlib.util.spec_from_file_location(f"{pkg_name}.{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _git(*args):
    root = str(config.get_project_root())
    return subprocess.run(["git", "-C", root, *args],
                          capture_output=True, text=True).stdout.strip()


def provenance(relpath):
    """Which code, and which numerics, the evidence was produced against."""
    src = config.get_project_root() / relpath
    return {
        "file": relpath,
        "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "last_commit": _git("log", "-1", "--format=%H", "--", str(src)),
        "uncommitted_changes": bool(_git("status", "--porcelain", "--", str(src))),
        "packages": {p: importlib.metadata.version(p) for p in ("numpy", "scipy", "mpmath")},
    }
