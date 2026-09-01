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

"""Shared fixtures for data lineage report tests.

The model_risk fixtures that used to live here went with the governance
report generator; the data-lineage ones below serve tests that remain.
"""

import pytest


@pytest.fixture
def dl_mod():
    from tests.commands.data_lineage_helpers import get_dl_mod
    return get_dl_mod()


@pytest.fixture
def sample_data_consistent(dl_mod):
    from tests.commands.data_lineage_helpers import make_sample_data_consistent
    return make_sample_data_consistent()


@pytest.fixture
def sample_data_issues(sample_data_consistent):
    from tests.commands.data_lineage_helpers import make_sample_data_issues
    return make_sample_data_issues(sample_data_consistent)
