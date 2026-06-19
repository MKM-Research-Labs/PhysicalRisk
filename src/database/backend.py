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
