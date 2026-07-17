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

"""Public API — lifecycle & meta."""

from __future__ import annotations

from .backend import active_backend


def catchments() -> list[str]:
    return active_backend().catchments()


def ping() -> bool:
    return active_backend().ping()


def postgres_reachable() -> bool:
    """True if the Postgres service answers, regardless of which backend is bound.

    ``ping`` asks the *active* backend, so it says nothing about Postgres while
    the file backend is bound. Callers that need to know whether the service
    itself is up (the test preflight) ask this instead.
    """
    from ._pg.engine import reachable

    return reachable()


def object_store_reachable() -> bool:
    """True if the blob-tier object store answers. See :func:`postgres_reachable`."""
    from ._pg._objectstore import reachable

    return reachable()
