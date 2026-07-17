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

"""
DEMO — the single data-access utility (repository) pattern.

Run it:  python docs/database/repository_demo.py

The point this demonstrates:
  * The whole .py codebase talks to ONE package and just calls a function that
    says WHAT it wants ("get this property", "commit this trade").
  * That package is the ONLY place that knows whether the data lives in JSON
    files or in PostgreSQL. No caller contains SQL, paths, json.load, or glob.
  * Migrating the database = swap ONE line (which backend is active). Not a
    single caller changes. We prove it below by running the SAME caller code
    against a file backend and then a database backend and getting identical
    output.

In the real project this single file becomes the `src/repository/` package:
    src/repository/__init__.py   <- PUBLIC API  (sections 4 + 5 below)
    src/repository/base.py       <- Repository protocol            (section 1)
    src/repository/file_repo.py  <- FileRepository                 (section 2)
    src/repository/pg_repo.py    <- PostgresRepository (+ _engine/_queries) (section 3)
Everything with a leading underscore is private; callers import only the public API.
"""

from __future__ import annotations

import json
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterator


# ════════════════════════════════════════════════════════════════════════════
# SECTION 1 — base.py : the interface every backend implements
# ════════════════════════════════════════════════════════════════════════════
class Repository(ABC):
    """Storage-agnostic contract. 'artifact' = logical record type (e.g.
    'property', 'gauge', 'prs_trade'); 'key' = entity id for per-entity data."""

    @abstractmethod
    def load(self, artifact: str, catchment: str, key: str | None = None) -> Any: ...

    @abstractmethod
    def save(self, artifact: str, catchment: str, payload: Any, key: str | None = None) -> None: ...

    @abstractmethod
    def iter_keys(self, artifact: str, catchment: str) -> Iterator[str]: ...


# which artifacts are stored one-file/row-per-entity (keyed) vs as one document
_KEYED = {"stress_storm", "prs_trade"}


# ════════════════════════════════════════════════════════════════════════════
# SECTION 2 — file_repo.py : TODAY's backend (wraps the existing JSON tree)
# ════════════════════════════════════════════════════════════════════════════
class FileRepository(Repository):
    """Reads/writes data/input/<catchment>/... exactly like the code does now.
    This is the ONLY place json.load / json.dump / glob is allowed to live."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def _path(self, artifact, catchment, key):
        base = self.root / catchment
        if artifact in _KEYED:
            return base / artifact / f"{key}.json"
        return base / f"{artifact}.json"

    def load(self, artifact, catchment, key=None):
        return json.loads(self._path(artifact, catchment, key).read_text())

    def save(self, artifact, catchment, payload, key=None):
        p = self._path(artifact, catchment, key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, indent=2))

    def iter_keys(self, artifact, catchment):
        d = self.root / catchment / artifact
        if not d.exists():
            return
        for f in sorted(d.glob("*.json")):
            yield f.stem


# ════════════════════════════════════════════════════════════════════════════
# SECTION 3 — pg_repo.py : TOMORROW's backend (PostgreSQL)
# ════════════════════════════════════════════════════════════════════════════
# For a runnable demo with no database to install, this uses an in-memory dict
# as a stand-in for Postgres. In the real pg_repo.py the bodies below are the
# ONLY place SQL exists — e.g. load() would be:
#
#     with self._engine.connect() as cx:                       # _engine.py
#         row = cx.execute(SELECT_ONE, {"c": catchment,        # _queries.py
#                                       "k": key}).fetchone()
#     return row.payload
#
# Same Repository interface => callers never know it changed.
class PostgresRepository(Repository):
    """Stands in for the real Postgres-backed repo. Note: identical interface."""

    def __init__(self):
        self._db: dict[tuple, Any] = {}          # pretend tables, keyed by (artifact, catchment, key)

    def load(self, artifact, catchment, key=None):
        return self._db[(artifact, catchment, key)]

    def save(self, artifact, catchment, payload, key=None):
        self._db[(artifact, catchment, key)] = payload

    def iter_keys(self, artifact, catchment):
        for (a, c, k) in sorted(self._db):
            if a == artifact and c == catchment and k is not None:
                yield k


# ════════════════════════════════════════════════════════════════════════════
# SECTION 4 — __init__.py : backend selection (THE one line that migrates the DB)
# ════════════════════════════════════════════════════════════════════════════
_active: Repository | None = None

def configure_backend(repo: Repository) -> None:
    """Called once at startup. Swapping file->postgres happens HERE and nowhere else."""
    global _active
    _active = repo

def _repo() -> Repository:
    if _active is None:
        raise RuntimeError("call configure_backend() first")
    return _active


# ════════════════════════════════════════════════════════════════════════════
# SECTION 5 — __init__.py : the PUBLIC API the rest of the codebase calls
# ════════════════════════════════════════════════════════════════════════════
# These are the "just call a function saying what you want" entry points.
# Intent-named, typed, return plain dicts/lists. No SQL, no paths, no escape hatch.

def list_gauges(catchment: str) -> list[dict]:
    return _repo().load("gauge", catchment)

def save_gauges(catchment: str, gauges: list[dict]) -> None:
    _repo().save("gauge", catchment, gauges)

def get_property(catchment: str, property_id: str) -> dict | None:
    props = _repo().load("property", catchment)
    return next((p for p in props if p["id"] == property_id), None)

def save_properties(catchment: str, properties: list[dict]) -> None:
    _repo().save("property", catchment, properties)

def list_stress_storms(catchment: str) -> list[dict]:
    return [_repo().load("stress_storm", catchment, k)
            for k in _repo().iter_keys("stress_storm", catchment)]

def add_stress_storm(catchment: str, storm: dict) -> None:
    _repo().save("stress_storm", catchment, storm, key=storm["id"])

# Mutating action — in production this carries the permission gate, e.g.
#   @require("Func003", "create")        # Trade PRS / Create
def commit_prs_trade(catchment: str, trade: dict) -> None:
    _repo().save("prs_trade", catchment, trade, key=trade["swap_id"])

def list_prs_trades(catchment: str) -> list[dict]:
    return [_repo().load("prs_trade", catchment, k)
            for k in _repo().iter_keys("prs_trade", catchment)]


# ════════════════════════════════════════════════════════════════════════════
# A CALLER — e.g. a Flask route or a report builder. Notice: NO json, NO SQL,
# NO paths, NO idea what the backend is. This code is IDENTICAL forever.
# ════════════════════════════════════════════════════════════════════════════
def build_portfolio_summary(catchment: str) -> dict:
    gauges = list_gauges(catchment)
    storms = list_stress_storms(catchment)
    prop = get_property(catchment, "PROP-002")
    trades = list_prs_trades(catchment)
    return {
        "catchment": catchment,
        "gauges": len(gauges),
        "stress_storms": len(storms),
        "looked_up_property": prop["address"] if prop else None,
        "open_trades": len(trades),
    }


# ════════════════════════════════════════════════════════════════════════════
# DEMO: seed some data, run the caller on TWO backends, show identical results.
# ════════════════════════════════════════════════════════════════════════════
def _seed(catchment: str) -> None:
    """Uses ONLY the public API — same code path that the port generators use."""
    save_gauges(catchment, [{"id": "GAUGE-1"}, {"id": "GAUGE-2"}, {"id": "GAUGE-3"}])
    save_properties(catchment, [
        {"id": "PROP-001", "address": "1 Mill Lane"},
        {"id": "PROP-002", "address": "2 River View"},
    ])
    add_stress_storm(catchment, {"id": "STORM-A", "severity": "severe"})
    add_stress_storm(catchment, {"id": "STORM-B", "severity": "moderate"})
    commit_prs_trade(catchment, {"swap_id": "PRS-100", "notional": 5_000_000})


def main() -> None:
    catchment = "thames"

    print("── Backend 1: FileRepository (today's JSON files) ─────────────")
    with tempfile.TemporaryDirectory() as tmp:
        configure_backend(FileRepository(Path(tmp)))   # <<< the one migration line
        _seed(catchment)
        file_result = build_portfolio_summary(catchment)
        print(json.dumps(file_result, indent=2))
        # show that real files were actually written:
        written = sorted(p.relative_to(tmp).as_posix() for p in Path(tmp).rglob("*.json"))
        print("  files on disk:", written)

    print("\n── Backend 2: PostgresRepository (tomorrow's DB) ──────────────")
    configure_backend(PostgresRepository())            # <<< the ONLY thing that changed
    _seed(catchment)
    db_result = build_portfolio_summary(catchment)
    print(json.dumps(db_result, indent=2))

    print("\n── Proof: the caller produced identical output on both ────────")
    print("  identical:", file_result == db_result)
    print("  build_portfolio_summary() and every public function above were")
    print("  UNCHANGED. Only configure_backend(...) differed.")


if __name__ == "__main__":
    main()
