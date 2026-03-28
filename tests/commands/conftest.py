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

"""Shared fixtures for model_risk report tests."""

import pytest

from tests.commands.model_risk_helpers_part1 import (
    _make_model, _make_bcbs, _make_raci, _make_role, _make_principle,
)
from tests.commands.model_risk_helpers_part2 import (
    _full_data, SAMPLE_JUNIT_EMPTY, SAMPLE_VQ, SAMPLE_REMEDIATION,
    SAMPLE_ASSUMPTIONS, SAMPLE_TEST_COVERAGE, SAMPLE_RISK_RATING,
)


@pytest.fixture
def mr_pkg():
    """Import the model_risk package."""
    from docs.models import model_risk
    return model_risk


@pytest.fixture
def data_mod():
    """Import the data module."""
    from docs.models.model_risk import data
    return data


@pytest.fixture
def styles_mod():
    """Import the styles module."""
    from docs.models.model_risk import styles
    return styles


@pytest.fixture
def sections_mod():
    """Import the sections package."""
    from docs.models.model_risk import sections
    return sections


@pytest.fixture
def sample_data():
    """Build a full sample data dict."""
    return _full_data()


@pytest.fixture
def empty_data():
    """Minimal data — no models, meetings, etc."""
    return _full_data(
        models=[],
        meetings=[],
        bcbs=_make_bcbs(),
        raci=_make_raci(),
        audit_log=[],
        junit=SAMPLE_JUNIT_EMPTY,
        coverage_pct=None,
        audit_files=[],
        sensitivity_generators=[],
    )


# ---------------------------------------------------------------------------
# Shared fixtures for data lineage report tests
# ---------------------------------------------------------------------------

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
