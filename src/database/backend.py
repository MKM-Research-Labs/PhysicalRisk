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

"""Backend selection — the single place the active storage backend is chosen.

``configure_backend`` is the one line that flips files → PostgreSQL; no caller changes.
"""

from __future__ import annotations

from .base import Repository

_active: Repository | None = None


def configure_backend(repo: Repository | None) -> None:
    """Bind the active backend. Called once at app/CLI startup. Pass ``None`` to unbind."""
    global _active
    _active = repo


def active_backend() -> Repository:
    """Return the bound backend, or raise if startup never configured one."""
    if _active is None:
        raise RuntimeError(
            "database backend not configured — call configure_backend(...) at startup"
        )
    return _active


def backend_configured() -> bool:
    """True if a backend is already bound. Lets an entry point bind a default only
    when a caller (a test fixture, the web app) hasn't already chosen one."""
    return _active is not None
