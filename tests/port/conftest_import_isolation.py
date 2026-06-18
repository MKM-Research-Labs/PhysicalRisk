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

"""Shared helpers for import-isolation tests (used by test_import_isolation_part*.py)."""

import sys


def _simulate_no_quantlib(monkeypatch):
    """
    Block 'QuantLib' in sys.modules so any `import QuantLib` raises ImportError.

    Python treats sys.modules[name] = None as a "blocked" import -- it raises
    ImportError immediately rather than searching for the package.
    """
    for key in list(sys.modules.keys()):
        if key == "QuantLib" or key.startswith("QuantLib."):
            monkeypatch.delitem(sys.modules, key, raising=False)
    monkeypatch.setitem(sys.modules, "QuantLib", None)


def _drop_port_src_cache(monkeypatch):
    """Remove all port.src.* entries from sys.modules so they reimport fresh."""
    for key in list(sys.modules.keys()):
        if key == "port.src" or key.startswith("port.src."):
            monkeypatch.delitem(sys.modules, key, raising=False)
