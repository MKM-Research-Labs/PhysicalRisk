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

"""InMemoryRepository — a dict-backed backend.

Stands in for the future PostgresRepository in tests and demos (no DB to install),
and proves the seam: the same caller code runs unchanged against this and the file
backend. The real ``pg_repo.py`` (migration WP1) keeps the same interface, with all
SQL confined to its private ``_engine``/``_queries`` modules.
"""

from __future__ import annotations

from typing import Any, Iterator

from config.data_layout import DEFAULT_MODE

from .base import Repository


class InMemoryRepository(Repository):
    """Volatile store keyed by ``(artifact, mode, catchment, key)``."""

    def __init__(self):
        self._store: dict[tuple, Any] = {}

    def load(self, artifact, catchment, key=None, *, mode=DEFAULT_MODE) -> Any:
        return self._store[(artifact, mode, catchment, key)]

    def save(self, artifact, catchment, payload, key=None, *, mode=DEFAULT_MODE) -> None:
        self._store[(artifact, mode, catchment, key)] = payload

    def delete(self, artifact, catchment, key=None, *, mode=DEFAULT_MODE) -> None:
        self._store.pop((artifact, mode, catchment, key), None)

    def iter_keys(self, artifact, catchment, *, mode=DEFAULT_MODE) -> Iterator[str]:
        for (a, m, c, k) in sorted(self._store, key=lambda t: tuple(str(x) for x in t)):
            if a == artifact and m == mode and c == catchment and k is not None:
                yield k

    def exists(self, artifact, catchment, key=None, *, mode=DEFAULT_MODE) -> bool:
        return (artifact, mode, catchment, key) in self._store

    def has_collection(self, artifact, catchment, *, mode=DEFAULT_MODE) -> bool:
        return any(a == artifact and m == mode and c == catchment and k is not None
                   for (a, m, c, k) in self._store)

    def catchments(self) -> list[str]:
        return sorted({c for (_a, _m, c, _k) in self._store})
