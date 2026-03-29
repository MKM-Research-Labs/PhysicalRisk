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

"""
Visual test configuration.
"""

import pytest

# Remaining legacy files that have not yet been rewritten
collect_ignore = [
    "verify_popups_package.py",
]

import os
import re
import subprocess
import sys


# ---------------------------------------------------------------------------
# Cross-IIFE contract test helpers
# ---------------------------------------------------------------------------

_IIFE_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_IIFE_SRC = os.path.join(_IIFE_REPO, 'src')


def iife_src_file(rel: str) -> str:
    with open(os.path.join(_IIFE_REPO, rel)) as f:
        return f.read()


def iife_has_node() -> bool:
    try:
        return subprocess.run(['node', '--version'], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def iife_node_check(js: str, label: str) -> None:
    """Assert JS is syntactically valid via node --check."""
    import pytest
    if not iife_has_node():
        pytest.skip('node not available')
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as f:
        f.write(js)
        path = f.name
    try:
        result = subprocess.run(['node', '--check', path], capture_output=True, text=True)
        assert result.returncode == 0, (
            f'node --check failed for {label}:\n{result.stderr[:800]}'
        )
    finally:
        os.unlink(path)


STARTUP_CACHE_VARS = [
    '_tdPreBlotter', '_tdPreMarket', '_tdPreGauges', '_tdPreStressStorms',
    '_tdPrePortStorms', '_tdPreEodHistory', '_tdPreYieldCurve', '_tdPreGovDocs',
    '_preStorms', '_preGovAudit', '_preGovBib',
    '_tdPreloadDone',
]
