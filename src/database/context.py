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

"""Run/request-scoped catchment identity.

The writers (port generators, trading engines) need to know *which catchment* a run is
producing so they can call ``save_*(catchment, …)``. Historically that identity was
carried by an injected ``output_dir`` (or the mutable global ``config.catchment_id``).
This module replaces both with a :class:`~contextvars.ContextVar`, so concurrent
requests / parallel runs each get their own catchment without clobbering a shared
global (the WP2.4 race fix).

Usage::

    with catchment_context("halong"):
        generate_gauges()          # every save_*/get_* inside sees "halong"

When no context is bound, :func:`active_catchment` falls back to ``config.catchment_id``
— so single-catchment runs behave exactly as before and callers need no change until
they are migrated.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

# ``None`` means "no run-scoped catchment bound" → fall back to config's active catchment.
_active: ContextVar[str | None] = ContextVar("active_catchment", default=None)


def active_catchment() -> str:
    """The catchment for the current run/request.

    Returns the context-bound catchment when one is active, otherwise the process-wide
    ``config.catchment_id``. ``config`` is imported lazily so ``import database`` stays
    lightweight and free of an import cycle.
    """
    current = _active.get()
    if current is not None:
        return current
    from config import config

    return config.catchment_id


@contextmanager
def catchment_context(catchment: str) -> Iterator[str]:
    """Bind ``catchment`` as the active catchment for the duration of the block.

    Nestable and restores the previous value on exit (including on exception), so a
    nested context cannot leak into the enclosing one.
    """
    token = _active.set(catchment)
    try:
        yield catchment
    finally:
        _active.reset(token)
