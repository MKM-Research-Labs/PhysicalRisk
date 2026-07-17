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

"""Low-level JSON document I/O — directory + filename, for the legacy loader layer.

The artifact-based functions (``get_property`` etc.) are the preferred API. These
directory/filename helpers exist only so the path-based loaders under ``src/loaders/``
read through the ``database`` package rather than calling ``json``/``glob`` themselves
(coding rule R6 — single point of file I/O). They support the loaders' need for
custom-filename construction.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


def read_json_document(directory, filename) -> Any:
    """Parse ``directory/filename``. Returns ``None`` if the file is absent; raises
    ``json.JSONDecodeError`` on a corrupt file (the caller decides tolerance)."""
    path = Path(directory) / filename
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def iter_document_names(directory, suffix: str = ".json") -> Iterator[str]:
    """Yield filenames (sorted) ending in ``suffix`` directly under ``directory``,
    skipping ``_``-prefixed index files. Empty when the directory is absent."""
    d = Path(directory)
    if not d.exists():
        return
    for p in sorted(d.glob(f"*{suffix}")):
        if not p.name.startswith("_"):
            yield p.name
