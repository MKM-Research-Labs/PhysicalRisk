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

"""Pytest configuration for services tests."""

import pytest

import database
from db_helpers import tmp_catchment


@pytest.fixture(autouse=True)
def _services_catchment(temp_data_dir):
    """Bind an isolated catchment rooted at the test's ``temp_data_dir``.

    The entity loaders read their portfolio through the database seam (ignoring the
    ``data_dir`` they are constructed with), so binding the seam to ``temp_data_dir``
    makes them read exactly the JSON files these tests write there — restoring the
    pre-migration behaviour where a test's own files drove the loader. Tests that seed
    through ``populated_data_dir`` bind their own (nested) catchment on top of this."""
    with tmp_catchment(temp_data_dir):
        yield
