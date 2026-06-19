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

    @abstractmethod
    def iter_keys(self, artifact: str, catchment: str,
                  *, mode: str = DEFAULT_MODE) -> Iterator[str]:
        """Yield the keys of a keyed artifact (replaces directory ``glob``)."""

    @abstractmethod
    def exists(self, artifact: str, catchment: str, key: str | None = None,
               *, mode: str = DEFAULT_MODE) -> bool:
        """True if the record is present."""

    @abstractmethod
    def catchments(self) -> list[str]:
        """List catchments that hold any data."""

    def ping(self) -> bool:
        """Backend health check. Override where a real connection exists."""
        return True
