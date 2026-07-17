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

"""Autouse fixture binding the data backend for every test.

As callers migrate onto the ``database`` package (coding rule R6), they need a
backend configured. This binds the config-wired file backend before each test
(resolving the same real paths ``create_app`` uses, so read-path tests work) —
but **with writes to the real ``data/`` tree refused** (``_WriteGuardedFileRepository``).
A test that needs to write must bind a scratch backend (``tmp_catchment`` /
``memory_catchment``) or monkeypatch ``config`` paths to a tmp dir first; otherwise
the guard raises rather than letting a migrated writer silently clobber real
portfolio data on the shared SSD. Tests that need a different backend (e.g. the
database suite) override this and may reset to ``None``; the fixture re-binds for
the next test.
"""

import pytest


@pytest.fixture(autouse=True)
def _database_file_backend():
    from db_helpers import pg_test_isolation, test_backend, use_guarded_file_backend
    if test_backend() == "pg":
        # WP4.2: run the test against Postgres in a rolled-back transaction.
        with pg_test_isolation():
            yield
    else:
        use_guarded_file_backend()
        yield
