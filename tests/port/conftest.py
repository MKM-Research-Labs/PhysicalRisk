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
Pytest configuration and fixtures for port package tests.
"""


import pytest

from config import config

# =============================================================================
# Session-scoped fixtures (existing)
# =============================================================================

@pytest.fixture(scope="session")
def catchment():
    """Return current catchment from config."""
    return config.CATCHMENT


@pytest.fixture(scope="session")
def input_dir():
    """Return input directory from config."""
    return config.get_input_dir()


@pytest.fixture(scope="session")
def gauge_portfolio_path(input_dir):
    """Return path to gauge portfolio JSON."""
    return input_dir / "gauge.json"


@pytest.fixture(scope="session")
def property_portfolio_path(input_dir):
    """Return path to property portfolio JSON."""
    return input_dir / "property.json"


@pytest.fixture(scope="session")
def mortgage_portfolio_path(input_dir):
    """Return path to residential loan portfolio JSON."""
    return input_dir / "loan.json"


@pytest.fixture(scope="session")
def gaugets_path(input_dir):
    """Return path to gauge timeseries directory."""
    return input_dir / "gaugets"


@pytest.fixture(scope="session")
def storm_timeseries_path(input_dir):
    """Return path to storm timeseries JSON."""
    return input_dir / "storm_timeseries.json"


# =============================================================================
# Random module fixtures
# =============================================================================

@pytest.fixture
def thames_gauge_random():
    """Load thames gauge random module."""
    from port.rand.thames import gauge_random
    return gauge_random


@pytest.fixture
def thames_property_random():
    """Load thames property random module."""
    from port.rand.thames import property_random
    return property_random


@pytest.fixture
def thames_mortgage_random():
    """Load thames mortgage random module."""
    from port.rand.thames import mortgage_random
    return mortgage_random


@pytest.fixture
def thames_params():
    """Load thames catchment params."""
    import catch.thames as params
    return params


# =============================================================================
# Sample data fixtures
# =============================================================================

@pytest.fixture
def sample_gauge_location():
    """A minimal gauge location dict for testing."""
    return {
        "lat": 51.5, "lon": -0.1, "elevation": 7.5,
        "name": "TestArea", "distance_to_river": 0,
        "distance_to_thames": 100,
    }


@pytest.fixture
def sample_property_location():
    """A minimal property location dict for testing."""
    return {
        "lat": 51.5, "lon": -0.1, "elevation": 7.5,
        "area_name": "Chelsea", "value_factor": 1.5,
        "property_type": "Semi-detached",
        "streets_data": {},
    }


# =============================================================================
# Generator fixtures (function-scoped, use tmp_path)
# =============================================================================

@pytest.fixture
def small_gauge_portfolio(tmp_path):
    """Generate a small gauge portfolio (5 gauges) in tmp_path, return result dict."""
    from port.src.gauge import GaugePortfolioGenerator
    gen = GaugePortfolioGenerator(output_dir=tmp_path, verbose=False)
    return gen.generate(count=5)


@pytest.fixture
def small_property_portfolio(tmp_path):
    """Generate a small property portfolio (5 properties) in tmp_path, return result dict."""
    from port.src.property import PropertyPortfolioGenerator
    gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
    return gen.generate(count=5)


@pytest.fixture
def synthetic_flat_gauges():
    """Minimal flat gauge dicts for hazard testing (no file I/O needed)."""
    return [
        {
            "gauge_id": f"GAUGE-TEST{i:04d}",
            "gauge_name": f"Test Gauge {i}",
            "gauge_latitude": 51.5 + i * 0.01,
            "gauge_longitude": -0.1 + i * 0.01,
            "elevation": 7.0 + i,
            "flood_alert": 3.0 + i * 0.1,
            "flood_warning": 4.0 + i * 0.1,
            "severe_flood_warning": 5.0 + i * 0.1,
        }
        for i in range(5)
    ]


@pytest.fixture
def synthetic_storm_dicts():
    """Minimal storm dicts for hazard testing (derived from storm_multi sequences)."""
    from port.src.storm_multi.generators.batch_generator import generate_event_set
    sequences = generate_event_set(count=100, catchment_id="thames", seed=42)
    storms = []
    for seq in sequences:
        for s in seq.storms:
            storms.append({
                "storm_id": s.storm_id,
                "effective_precipitation_mm": s.precipitation_mm,
                "duration_hours": s.duration_hours,
                "intensity_factor": s.intensity_factor,
                "intensity_category": s.intensity_category,
                "peak_position": s.peak_position,
            })
    return storms


# =============================================================================
# Marker configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "cdm_mapping: marks test as CDM mapping validation test"
    )
    config.addinivalue_line(
        "markers", "requires_portfolio: marks test as requiring generated portfolio files"
    )
    config.addinivalue_line(
        "markers", "generator: marks test as portfolio generator test"
    )
    config.addinivalue_line(
        "markers", "random_values: marks test as random value generator test"
    )

