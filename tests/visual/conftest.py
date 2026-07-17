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

# JS/CSS factory bodies were migrated out of the .py shells into the central
# src/static tree (returned via js_static()/css_static()). Source-text contract
# tests still want to see that JS, so when a shell references a static asset we
# fold the asset's contents back in. This keeps the "JS lives on disk, not in
# Python" rule while letting substring assertions stay pointed at the .py.
_STATIC_REF_RE = re.compile(r"(js|css)_static\(\s*['\"]([^'\"]+)['\"]")


def _augment_with_static(src: str, repo: str) -> str:
    extra = []
    for kind, name in _STATIC_REF_RE.findall(src):
        asset = os.path.join(repo, 'src', 'static', kind, name)
        if os.path.exists(asset):
            with open(asset) as f:
                extra.append(f.read())
    return src + ('\n' + '\n'.join(extra) if extra else '')


def iife_src_file(rel: str) -> str:
    with open(os.path.join(_IIFE_REPO, rel)) as f:
        src = f.read()
    return _augment_with_static(src, _IIFE_REPO)


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
