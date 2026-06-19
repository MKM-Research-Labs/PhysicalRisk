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

"""FileRepository — today's backend.

Reads/writes the existing ``data/input/<catchment>/...`` JSON tree, exactly as the
codebase does now. This module (with the rest of the ``database`` package) is the
ONLY place ``json.load`` / ``json.dump`` / ``glob`` against catchment data is allowed
to live; the data-access audit (migration task 0.8) enforces that.

Path note: this composes paths *beneath* a config-provided ``input_root`` only; all
name literals come from ``config.data_layout``. ``database`` is added to the
path-definition audit's sanctioned packages alongside ``config``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Iterator

from config.data_layout import DEFAULT_MODE

from . import artifacts
from ._serialize import dumps
from .base import Repository


class FileRepository(Repository):
    """Catchment data stored as JSON files under a per-catchment directory.

    Pass ``input_root`` for the simple ``input_root/<catchment>/`` layout, or a
    ``dir_resolver`` callable ``catchment -> Path`` to map each catchment to its
    directory (used by the config binding so the active catchment honours the e2e
    ``MKM_CATCHMENT_INPUT_OVERRIDE``). ``input_root`` also drives :meth:`catchments`.
    """

    def __init__(self, input_root: str | Path | None = None, *,
                 dir_resolver: Callable[[str], Path] | None = None):
        self.root = Path(input_root) if input_root is not None else None
        if dir_resolver is None:
            if self.root is None:
                raise ValueError("FileRepository needs input_root or dir_resolver")
            dir_resolver = lambda catchment: self.root / catchment
        self._dir_resolver = dir_resolver

    # -- internal path resolution (private to this module) ---------------------
    def _catchment_dir(self, catchment: str) -> Path:
        return self._dir_resolver(catchment)

    def _file(self, artifact: str, catchment: str, key: str | None, mode: str) -> Path:
        sp = artifacts.spec(artifact)
        base = self._catchment_dir(catchment)
        if sp.kind == artifacts.DOCUMENT:
            return base / sp.location(mode)
        if key is None:
            raise ValueError(f"artifact {artifact!r} is keyed; a key is required")
        return base / sp.location(mode) / artifacts.filename(sp, key)

    def _dir(self, artifact: str, catchment: str, mode: str) -> Path:
        sp = artifacts.spec(artifact)
        return self._catchment_dir(catchment) / sp.location(mode)

    # -- Repository interface --------------------------------------------------
    def load(self, artifact, catchment, key=None, *, mode=DEFAULT_MODE) -> Any:
        sp = artifacts.spec(artifact)
        p = self._file(artifact, catchment, key, mode)
        if sp.kind == artifacts.BLOB:
            return p.read_bytes()
        return json.loads(p.read_text())

    def save(self, artifact, catchment, payload, key=None, *, mode=DEFAULT_MODE) -> None:
        sp = artifacts.spec(artifact)
        p = self._file(artifact, catchment, key, mode)
        p.parent.mkdir(parents=True, exist_ok=True)
        if sp.kind == artifacts.BLOB:
            p.write_bytes(payload)
        else:
            p.write_text(dumps(payload))

    def delete(self, artifact, catchment, key=None, *, mode=DEFAULT_MODE) -> None:
        self._file(artifact, catchment, key, mode).unlink(missing_ok=True)

    def iter_keys(self, artifact, catchment, *, mode=DEFAULT_MODE) -> Iterator[str]:
        sp = artifacts.spec(artifact)
        d = self._dir(artifact, catchment, mode)
        if not d.exists():
            return
        for f in sorted(d.glob(f"*{artifacts.glob_ext(sp)}")):
            if f.name.startswith("_"):           # skip _index.json and similar
                continue
            yield artifacts.key_of(sp, f.name)

    def exists(self, artifact, catchment, key=None, *, mode=DEFAULT_MODE) -> bool:
        return self._file(artifact, catchment, key, mode).exists()

    def has_collection(self, artifact, catchment, *, mode=DEFAULT_MODE) -> bool:
        return self._dir(artifact, catchment, mode).exists()

    def catchments(self) -> list[str]:
        if self.root is None or not self.root.exists():
            return []
        return sorted(p.name for p in self.root.iterdir() if p.is_dir())
