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

"""ETL: load a catchment's file-backed artifacts into Postgres (JSON→Postgres WP1.5).

Reads each tier-1 artifact through the file repository and writes it through
``PostgresRepository`` — both sides of the same ``Repository`` interface, so the
ETL is pure repo calls (no direct SQL or file I/O of its own). Idempotent:
collection artifacts replace, keyed artifacts upsert, so a re-run reconciles.
Returns a ``{artifact: record_count}`` report for reconciliation against the
files.
"""

from ..config_binding import from_config
from .pg_repo import (
    _BLOBS,
    _COLLECTIONS,
    _DOCUMENTS,
    _KEYED,
    _KEYED_DOCS,
    PostgresRepository,
    modes_for,
)


def import_catchment(catchment, *, file_repo=None, pg=None) -> dict:
    """Load every mapped artifact for ``catchment`` from files into Postgres.

    ``file_repo`` / ``pg`` are injectable for tests; by default reads via the
    config-bound file backend and writes via a fresh ``PostgresRepository``.
    Document counts are the number of scenario-mode variants imported.
    """
    file_repo = file_repo if file_repo is not None else from_config()
    pg = pg if pg is not None else PostgresRepository()
    counts: dict = {}

    for artifact, spec in _COLLECTIONS.items():
        if not file_repo.exists(artifact, catchment):
            continue
        doc = file_repo.load(artifact, catchment)
        pg.save(artifact, catchment, doc)
        counts[artifact] = len(doc.get(spec[2]) or [])

    for artifact in _KEYED:
        n = 0
        for key in file_repo.iter_keys(artifact, catchment):
            pg.save(artifact, catchment, file_repo.load(artifact, catchment, key), key=key)
            n += 1
        counts[artifact] = n

    for artifact in sorted(_DOCUMENTS):
        n = 0
        for mode in modes_for(artifact):
            if not file_repo.exists(artifact, catchment, mode=mode):
                continue
            pg.save(artifact, catchment, file_repo.load(artifact, catchment, mode=mode), mode=mode)
            n += 1
        counts[artifact] = n

    for artifact in sorted(_KEYED_DOCS):
        n = 0
        for mode in modes_for(artifact):
            for key in file_repo.iter_keys(artifact, catchment, mode=mode):
                record = file_repo.load(artifact, catchment, key, mode=mode)
                pg.save(artifact, catchment, record, key=key, mode=mode)
                n += 1
        counts[artifact] = n

    for artifact in sorted(_BLOBS):
        n = 0
        for mode in modes_for(artifact):
            for key in file_repo.iter_keys(artifact, catchment, mode=mode):
                blob = file_repo.load(artifact, catchment, key, mode=mode)  # bytes
                pg.save(artifact, catchment, blob, key=key, mode=mode)
                n += 1
        counts[artifact] = n

    return counts
