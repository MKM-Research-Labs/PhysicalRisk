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

"""Helpers for loading JavaScript fragments from companion ``.js`` files.

JavaScript belongs in ``.js`` files, not embedded as Python strings. A panel
module keeps its JS in a sibling file (``foo.py`` → ``foo.js``) and calls
:func:`js_sibling` from its ``get_js()`` so the fragment is read from disk.
"""

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=None)
def js_sibling(module_file: str) -> str:
    """Read the ``.js`` file sitting next to *module_file*.

    Pass ``__file__`` from the calling module; the companion file shares the
    module's stem with a ``.js`` suffix (``phc_hazard.py`` → ``phc_hazard.js``).
    """
    return Path(module_file).with_suffix(".js").read_text(encoding="utf-8")
