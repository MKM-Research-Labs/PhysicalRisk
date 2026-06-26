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

from config import config

# The static tree is owned by the config package (``src/static``); resolve it
# through the accessor so callers at any nesting depth load the same place.
_STATIC_DIR = config.get_static_dir()


def _strip_inlined_header(text: str) -> str:
    """Drop the leading ``//`` license/comment block from JS that is inlined
    into the page.

    Every source ``.js`` carries the canonical copyright header as a block of
    ``//`` lines (enforced by the copyright-header audit). That is harmless
    inside a real ``<script>``, but several fragments are injected as raw HTML
    whose own ``<script>`` lives lower in the file — there a leading ``//``
    block is not a comment, it renders as visible text at the top of the page.
    Stripping it at inline time keeps the on-disk header (still audited) while
    keeping the rendered page clean. Only the leading run of blank / ``//``
    lines is removed; the first line of real content (code or a ``<script>``
    tag) is preserved verbatim, indentation included.
    """
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines) and (not lines[i].strip()
                              or lines[i].lstrip().startswith("//")):
        i += 1
    return "".join(lines[i:])


@lru_cache(maxsize=None)
def js_sibling(module_file: str) -> str:
    """Read the ``.js`` file sitting next to *module_file*.

    Pass ``__file__`` from the calling module; the companion file shares the
    module's stem with a ``.js`` suffix (``phc_hazard.py`` → ``phc_hazard.js``).
    The leading license header is stripped (see :func:`_strip_inlined_header`).
    """
    return _strip_inlined_header(
        Path(module_file).with_suffix(".js").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def js_static(name: str) -> str:
    """Read a JavaScript fragment from ``src/static/js/<name>``.

    *name* is the bare filename (e.g. ``"phc-hazard.js"``). The path is
    resolved relative to this module, so it is independent of the calling
    module's location in the package tree. The leading license header is
    stripped (see :func:`_strip_inlined_header`).
    """
    return _strip_inlined_header(
        (_STATIC_DIR / "js" / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def css_static(name: str) -> str:
    """Read a CSS fragment from ``src/static/css/<name>``.

    *name* is the bare filename (e.g. ``"training-ui.css"``).
    """
    return (_STATIC_DIR / "css" / name).read_text(encoding="utf-8")
