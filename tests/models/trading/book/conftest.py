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

"""Shared fixtures for book generator tests.

The gauge book generators read gauge hazard curves and counterparties through
the ``database`` seam (no longer from loose ``gaugehc.json`` / ``counterparty
.json`` files). These fixtures therefore seed the seam for the active catchment
rather than writing JSON to ``tmp_path``. ``_book_backend`` binds a single
scratch backend (file under the default test backend, Postgres under
``MKM_TEST_BACKEND=pg``) that both the gaugehc and counterparty fixtures save
into and that stays bound for the test body, so the generator — defaulting to
``catchment_id='thames'`` — reads the seeded data back. The fixtures return the
catchment id; tests request them for their seeding side-effect."""

import pytest
from db_helpers import tmp_catchment

import database
from port.src.book import THAMES_CENTRAL_AREAS

_CATCHMENT = "thames"


@pytest.fixture
def _book_backend(tmp_path):
    """Bind one scratch backend for the test so gaugehc + counterparty co-seed."""
    with tmp_catchment(tmp_path, _CATCHMENT) as repo:
        yield repo


@pytest.fixture
def sample_gaugehc(_book_backend):
    """Seed a minimal gauge hazard-curve set through the seam; return the catchment."""
    database.save_gauge_hazard_curves(_CATCHMENT, {
        "metadata": {"catchment": "test"},
        "hazard_curves": {
            "GAUGE-001": {
                "gauge_id": "GAUGE-001",
                "gauge_name": "Test Gauge 1",
                "annual_hazard_rate_alert": 0.04,
                "annual_hazard_rate_warning": 0.025,
                "annual_hazard_rate_severe": 0.01,
            },
            "GAUGE-002": {
                "gauge_id": "GAUGE-002",
                "gauge_name": "Test Gauge 2",
                "annual_hazard_rate_alert": 0.035,
                "annual_hazard_rate_warning": 0.022,
                "annual_hazard_rate_severe": 0.012,
            },
            "GAUGE-003": {
                "gauge_id": "GAUGE-003",
                "gauge_name": "Test Gauge 3",
                "annual_hazard_rate_alert": 0.038,
                "annual_hazard_rate_warning": 0.027,
                "annual_hazard_rate_severe": 0.015,
            },
        },
    })
    return _CATCHMENT


@pytest.fixture
def sample_counterparties(_book_backend):
    """Seed a minimal counterparty set through the seam; return the catchment."""
    database.save_counterparties(_CATCHMENT, {
        "counterparties": [
            {
                "CounterpartySet": {
                    "Party": {"PartyID": "CTPY-001", "PartyName": "Test Bank A"},
                    "_platform": {"ShortName": "TestA", "CreditRating": "A+"},
                }
            },
            {
                "CounterpartySet": {
                    "Party": {"PartyID": "CTPY-002", "PartyName": "Test Bank B"},
                    "_platform": {"ShortName": "TestB", "CreditRating": "AA"},
                }
            },
        ],
    })
    return _CATCHMENT


@pytest.fixture
def thames_central_gaugehc(_book_backend):
    """Seed gauge hazard curves named for the Thames Central gauges via the seam."""
    from port.src.book import _AREA_TO_GAUGE_NAME

    gaugehc = {"metadata": {"catchment": "thames"}, "hazard_curves": {}}
    for i, area in enumerate(THAMES_CENTRAL_AREAS):
        gauge_id = f"GAUGE-test{i:04d}"
        gauge_name_target = _AREA_TO_GAUGE_NAME.get(area, area)
        gaugehc["hazard_curves"][gauge_id] = {
            "gauge_id": gauge_id,
            "gauge_name": f"Thames {gauge_name_target}",
            "latitude": 51.48,
            "longitude": -0.25 + i * 0.02,
            "annual_hazard_rate_severe": 0.015,
            "annual_hazard_rate_warning": 0.025,
            "annual_hazard_rate_alert": 0.04,
        }
    database.save_gauge_hazard_curves(_CATCHMENT, gaugehc)
    return _CATCHMENT
