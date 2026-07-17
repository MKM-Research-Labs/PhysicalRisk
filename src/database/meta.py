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
