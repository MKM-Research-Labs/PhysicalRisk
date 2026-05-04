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
Pytest configuration for MKM Research Labs PRS Platform.

Submodules are in tests/conftest/:
  collection.py       — pytest_collect_file hook and non-prefixed dir registry
  data.py             — SAMPLE_* test data constants
  fixtures_files_basic.py    — temp dir and basic portfolio file fixtures
  fixtures_files_advanced.py — advanced data dir fixtures (propertyts, hazard curves, storms)
  fixtures_loaders.py — data loader fixtures
  fixtures_flask.py   — Flask app and test client fixtures
  helpers.py          — assertion helpers and file utilities
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
_TESTS_DIR = Path(__file__).parent

# project root, src/, and the conftest/ submodule directory are all importable
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(_TESTS_DIR / "conftest"))

# Re-export everything so pytest discovers fixtures and hooks in this namespace.
from collection import pytest_collect_file, _NON_PREFIXED_DIRS  # noqa: F401, E402

from data import (  # noqa: F401, E402
    SAMPLE_PROPERTY, SAMPLE_PROPERTY_2, SAMPLE_PROPERTY_TX,
    SAMPLE_MORTGAGE, SAMPLE_MORTGAGE_2, SAMPLE_MORTGAGE_DELINQUENT,
    SAMPLE_GAUGE, SAMPLE_GAUGE_2, SAMPLE_GAUGE_INACTIVE,
    SAMPLE_TIMESERIES, SAMPLE_STORM,
)

from fixtures_files_basic import (  # noqa: F401, E402
    temp_data_dir,
    sample_property_file,
    sample_mortgage_file,
    sample_gauge_file,
    sample_timeseries_file,
    sample_storm_file,
    populated_data_dir,
)

from fixtures_files_advanced import (  # noqa: F401, E402
    sample_propertyts_dir,
    sample_propertyhc_file,
    sample_gaugehc_file,
    sample_storms_file,
    fully_populated_data_dir,
)

from fixtures_loaders import (  # noqa: F401, E402
    property_loader,
    mortgage_loader,
    gauge_loader,
    timeseries_loader,
    storm_loader,
    loader_registry,
)

from fixtures_flask import (  # noqa: F401, E402
    flask_app,
    full_flask_app,
    full_client,
    client,
)

from fixtures_admin import (  # noqa: F401, E402
    TEST_ADMIN_PW,
    AuthenticatedTestClient,
    _test_admin_credential,
)

from helpers import (  # noqa: F401, E402
    create_test_file,
    assert_valid_property,
    assert_valid_gauge,
    assert_valid_mortgage,
)
