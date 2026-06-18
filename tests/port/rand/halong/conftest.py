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

"""Shared fixtures for halong random-module smoke tests."""

import pytest


@pytest.fixture
def gauge_metadata():
    """Realistic halong gauge metadata for the random generators."""
    return {
        "gauge_id": "GAUGE-halong-001",
        "historical_high_level": 7.2,
        "historical_high_date": "2024-09-12",
        "flood_alert": 4.32,
        "flood_warning": 5.76,
        "severe_flood_warning": 6.84,
        "install_date": "2014-03-01",
        "location": {
            "lat": 20.95, "lon": 107.05, "elevation": 4.2,
            "name": "Bai Chay", "area": "Halong Bay",
        },
        "catchment_name": "Halong",
        "index": 0,
    }


@pytest.fixture
def property_location():
    """Halong property location dict."""
    return {
        "lat": 20.95, "lon": 107.05, "elevation": 8.0,
        "area_name": "Bai Chay", "value_factor": 1.0,
        "property_type": "Detached", "streets_data": {},
    }


@pytest.fixture
def gauges_for_timeseries():
    """A small lookup-style gauge list for gaugets_random tests."""
    return [
        {
            "GaugeID": f"GAUGE-h{i:03d}",
            "GaugeName": f"Halong Test {i}",
            "Latitude": 20.95 + i * 0.01,
            "Longitude": 107.05 + i * 0.01,
            "Elevation": 4.0 + i * 0.5,
            "FloodAlert": 3.0 + i * 0.1,
            "FloodWarning": 4.0 + i * 0.1,
            "SevereFloodWarning": 5.0 + i * 0.1,
        }
        for i in range(3)
    ]
