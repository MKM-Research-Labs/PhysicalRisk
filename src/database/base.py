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

"""The storage-agnostic Repository contract.

Every backend (files today, PostgreSQL tomorrow) implements this interface.
Callers never see SQL, paths, connections, json, or globs — only these methods,
wrapped by the intent-named public functions in ``database/__init__.py``.

Vocabulary
----------
* ``artifact`` — a logical record type, e.g. ``'property'``, ``'gauge'``,
  ``'prs_trade'``. The full set is defined in ``artifacts.py``.
* ``catchment`` — ``'thames'`` / ``'halong'`` / ``'mekong'``. First-class here so a
  single store can hold every catchment (the migration goal).
* ``key`` — the entity id for per-entity ("keyed") artifacts, e.g. a property id.
  ``None`` for whole-document artifacts.
* ``mode`` — scenario variant for hazard curves / timeseries: ``flood`` (default),
  ``shd``, ``she``, ``bri``, ``win``, ``faw``, ``fow``, ``bow``, ``baw``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterator

from config.data_layout import DEFAULT_MODE


class Repository(ABC):
    """Contract implemented by every storage backend."""

    @abstractmethod
    def load(self, artifact: str, catchment: str, key: str | None = None,
             *, mode: str = DEFAULT_MODE) -> Any:
        """Return one record. Raises ``FileNotFoundError``/``KeyError`` if absent
        (the public API translates that to ``None``)."""

    @abstractmethod
    def save(self, artifact: str, catchment: str, payload: Any,
             key: str | None = None, *, mode: str = DEFAULT_MODE) -> None:
        """Create or replace one record."""

    @abstractmethod
    def delete(self, artifact: str, catchment: str, key: str | None = None,
               *, mode: str = DEFAULT_MODE) -> None:
        """Remove one record. No-op if it does not exist."""

    def clear(self, artifact: str, catchment: str,
              *, mode: str = DEFAULT_MODE) -> None:
        """Remove every record of a keyed artifact's collection.

        Default implementation deletes each enumerated key; since ``iter_keys``
        skips ``_``-prefixed entries (e.g. ``_index``), those are left for the
        caller to overwrite rather than cleared. Backends may override with a
        single bulk delete."""
        for key in list(self.iter_keys(artifact, catchment, mode=mode)):
            self.delete(artifact, catchment, key, mode=mode)

    @abstractmethod
    def iter_keys(self, artifact: str, catchment: str,
                  *, mode: str = DEFAULT_MODE) -> Iterator[str]:
        """Yield the keys of a keyed artifact (replaces directory ``glob``)."""

    @abstractmethod
    def exists(self, artifact: str, catchment: str, key: str | None = None,
               *, mode: str = DEFAULT_MODE) -> bool:
        """True if the record is present."""

    @abstractmethod
    def has_collection(self, artifact: str, catchment: str,
                       *, mode: str = DEFAULT_MODE) -> bool:
        """True if a keyed-artifact collection exists, even when empty (distinguishes
        a not-yet-generated collection from a generated-but-empty one)."""

    @abstractmethod
    def catchments(self) -> list[str]:
        """List catchments that hold any data."""

    def ping(self) -> bool:
        """Backend health check. Override where a real connection exists."""
        return True
