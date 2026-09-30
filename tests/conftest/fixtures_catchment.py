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

"""Fixture for tests that are about the thames catchment specifically.

``phys.py test --<catchment>`` pins the whole suite to one catchment. Most tests
follow whatever is active, but some assert thames facts -- UK use classes,
"On Thames River" wording, London coordinates -- and those are only true under
thames. They take this fixture so they keep testing thames whichever catchment
the run is pinned to, instead of failing under every other one.
"""

import pytest

from config import config

THAMES = "thames"


@pytest.fixture
def thames_catchment():
    """Activate thames for the test, restoring the run's catchment afterwards."""
    with config.use_catchment(THAMES):
        yield THAMES
