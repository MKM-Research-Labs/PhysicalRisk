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
    return config.get_project_root() / "data" / "input"


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
