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

"""Production binding — wire the file backend to the real ``config`` paths.

The app/CLI calls :func:`use_file_backend` once at startup. The resolver honours the
active catchment's resolved input dir (so the e2e ``MKM_CATCHMENT_INPUT_OVERRIDE``
keeps working) and composes ``data/input/<catchment>`` for any other catchment.
No behaviour change: the resulting paths match what the codebase reads today.
"""

from __future__ import annotations

from pathlib import Path

from config import config

from .backend import configure_backend
from .file_repo import FileRepository


def _input_root() -> Path:
    """The ``data/input`` directory that contains every catchment."""
    return config.get_input_root()


def _resolve_catchment_dir(catchment: str) -> Path:
    """Directory holding ``catchment``'s data. The active catchment uses
    ``config.get_input_dir()`` (which already applies any e2e override)."""
    if catchment == config.catchment_id:
        return config.get_input_dir()
    return _input_root() / catchment


def from_config() -> FileRepository:
    """Build a FileRepository wired to the real config paths."""
    return FileRepository(input_root=_input_root(), dir_resolver=_resolve_catchment_dir)


def use_file_backend() -> FileRepository:
    """Bind the file backend as the active repository and return it."""
    repo = from_config()
    configure_backend(repo)
    return repo


def use_configured_backend():
    """Bind the backend selected by ``config.database.get_repo_backend()`` —
    the WP2.1 read-source switch. ``'file'`` (default) keeps today's behaviour;
    ``'pg'`` binds the PostgreSQL backend. The pg import is lazy so the file path
    never pulls SQLAlchemy in.
    """
    from config.database import get_repo_backend

    if get_repo_backend() == "pg":
        from ._pg.pg_repo import PostgresRepository

        repo = PostgresRepository()
        configure_backend(repo)
        return repo
    return use_file_backend()
