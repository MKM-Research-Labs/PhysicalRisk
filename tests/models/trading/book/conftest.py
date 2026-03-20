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

"""Shared fixtures for book generator tests."""

import json

import pytest

from port.src.book import THAMES_CENTRAL_AREAS


@pytest.fixture
def sample_gaugehc(tmp_path):
    """Create a minimal gaugehc.json for testing."""
    gaugehc = {
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
    }
    path = tmp_path / "gaugehc.json"
    with open(path, "w") as f:
        json.dump(gaugehc, f)
    return path


@pytest.fixture
def sample_counterparties(tmp_path):
    """Create a minimal counterparty.json for testing."""
    ctpy = {
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
    }
    path = tmp_path / "counterparty.json"
    with open(path, "w") as f:
        json.dump(ctpy, f)
    return path


@pytest.fixture
def thames_central_gaugehc(tmp_path):
    """Create gaugehc.json with the Thames Central gauges."""
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
    path = tmp_path / "gaugehc.json"
    with open(path, "w") as f:
        json.dump(gaugehc, f)
    return path
