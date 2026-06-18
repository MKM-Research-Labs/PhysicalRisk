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

"""Fixtures for temporary data directories and basic sample portfolio files."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from data import (
    SAMPLE_GAUGE, SAMPLE_GAUGE_2, SAMPLE_GAUGE_INACTIVE,
    SAMPLE_MORTGAGE, SAMPLE_MORTGAGE_2, SAMPLE_MORTGAGE_DELINQUENT,
    SAMPLE_PROPERTY, SAMPLE_PROPERTY_2, SAMPLE_PROPERTY_TX,
    SAMPLE_STORM, SAMPLE_TIMESERIES,
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data files."""
    temp_dir = tempfile.mkdtemp(prefix="prs_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_property_file(temp_data_dir):
    """Create a sample property portfolio file."""
    data = {"properties": [SAMPLE_PROPERTY, SAMPLE_PROPERTY_2, SAMPLE_PROPERTY_TX]}
    filepath = temp_data_dir / "property.json"
    with open(filepath, 'w') as f:
        json.dump(data, f)
    return filepath


@pytest.fixture
def sample_mortgage_file(temp_data_dir):
    """Create a sample mortgage portfolio file."""
    data = {"loans": [SAMPLE_MORTGAGE, SAMPLE_MORTGAGE_2, SAMPLE_MORTGAGE_DELINQUENT]}
    filepath = temp_data_dir / "loan.json"
    with open(filepath, 'w') as f:
        json.dump(data, f)
    return filepath


@pytest.fixture
def sample_gauge_file(temp_data_dir):
    """Create a sample gauge portfolio file."""
    data = {"floodGauges": [SAMPLE_GAUGE, SAMPLE_GAUGE_2, SAMPLE_GAUGE_INACTIVE]}
    filepath = temp_data_dir / "gauge.json"
    with open(filepath, 'w') as f:
        json.dump(data, f)
    return filepath


@pytest.fixture
def sample_timeseries_file(temp_data_dir):
    """Create sample per-gauge timeseries files in gaugets/ directory."""
    gaugets_dir = temp_data_dir / "gaugets"
    gaugets_dir.mkdir(parents=True, exist_ok=True)

    gauge_readings = {}
    for timestep in SAMPLE_TIMESERIES:
        for reading in timestep.get('readings', []):
            gid = reading.get('gaugeId')
            if gid:
                if gid not in gauge_readings:
                    gauge_readings[gid] = []
                gauge_readings[gid].append({
                    'timestamp': timestep.get('timestamp'),
                    'hour': timestep.get('hour'),
                    **reading
                })

    for gauge_id, readings in gauge_readings.items():
        gauge_file = gaugets_dir / f"{gauge_id}.json"
        gauge_data = {
            "gauge_id": gauge_id,
            "metadata": {"catchment": "test"},
            "flood_simulation": {
                "simulation_hours": len(readings),
                "num_timesteps": len(readings),
                "readings": readings,
            },
        }
        with open(gauge_file, 'w') as f:
            json.dump(gauge_data, f)

    return gaugets_dir


@pytest.fixture
def sample_storm_file(temp_data_dir):
    """Create a sample storm events file."""
    data = {"storms": [SAMPLE_STORM]}
    filepath = temp_data_dir / "storm_events.json"
    with open(filepath, 'w') as f:
        json.dump(data, f)
    return filepath


@pytest.fixture
def populated_data_dir(
    temp_data_dir,
    sample_property_file,
    sample_mortgage_file,
    sample_gauge_file,
    sample_timeseries_file,
    sample_storm_file
):
    """Create a fully populated test data directory."""
    return temp_data_dir
