# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
(coding rule R6 — single point of file I/O). They retain the loaders' need for
arbitrary filenames (``file_overrides``, custom-filename construction).
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
