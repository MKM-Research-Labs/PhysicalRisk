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

"""Helpers for loading JavaScript/CSS fragments from disk.

JavaScript and CSS belong in ``.js``/``.css`` files, not embedded as Python
strings. The preferred home is the central ``src/static`` tree, loaded via
:func:`js_static` / :func:`css_static`. :func:`js_sibling` remains for any
module that still keeps a companion ``foo.py`` → ``foo.js`` next to itself.
"""

from functools import lru_cache
from pathlib import Path

# ``_jsbundle.py`` lives at ``src/visual/interactivity/`` so the static tree is
# three directories up. Resolve once, relative to this file, so callers at any
# nesting depth load the same place without fragile ``parent.parent`` chains.
_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@lru_cache(maxsize=None)
def js_sibling(module_file: str) -> str:
    """Read the ``.js`` file sitting next to *module_file*.

    Pass ``__file__`` from the calling module; the companion file shares the
    module's stem with a ``.js`` suffix (``phc_hazard.py`` → ``phc_hazard.js``).
    """
    return Path(module_file).with_suffix(".js").read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def js_static(name: str) -> str:
    """Read a JavaScript fragment from ``src/static/js/<name>``.

    *name* is the bare filename (e.g. ``"phc-hazard.js"``). The path is
    resolved relative to this module, so it is independent of the calling
    module's location in the package tree.
    """
    return (_STATIC_DIR / "js" / name).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def css_static(name: str) -> str:
    """Read a CSS fragment from ``src/static/css/<name>``.

    *name* is the bare filename (e.g. ``"training-ui.css"``).
    """
    return (_STATIC_DIR / "css" / name).read_text(encoding="utf-8")
