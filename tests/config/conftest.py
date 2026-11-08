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

"""Fixtures for the config tests.

``apply_storm_control`` patches ``config.port``, ``config.models`` and the ``config``
package in place, and the storm sequence generator reads those on every draw. A test
that applies a control file must not leave its values behind for the tests after it,
so every storm-control attribute is put back after each test here.
"""

import sys

import pytest

import config.models as cm
import config.port as cp
from config.storm_control._mappings import _CONFIG_MODELS_KEYS, _CONFIG_PORT_KEYS

_MISSING = object()


@pytest.fixture(autouse=True)
def _restore_storm_control_targets():
    pkg = sys.modules["config"]
    targets = [(m, a) for m, keys in ((cp, _CONFIG_PORT_KEYS), (cm, _CONFIG_MODELS_KEYS), (pkg, _CONFIG_PORT_KEYS),
                                      (pkg, _CONFIG_MODELS_KEYS)) for a in keys.values()]
    saved = [(m, a, getattr(m, a, _MISSING)) for m, a in targets]
    yield
    for m, a, v in saved:
        if v is _MISSING:
            if hasattr(m, a):
                delattr(m, a)
        else:
            setattr(m, a, v)
