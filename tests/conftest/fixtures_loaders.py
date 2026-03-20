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

"""Fixtures for data loader instances."""

import pytest


@pytest.fixture
def property_loader(populated_data_dir):
    """Create a PropertyLoader with test data."""
    from loaders.property_loader import PropertyLoader
    return PropertyLoader(data_dir=populated_data_dir)


@pytest.fixture
def mortgage_loader(populated_data_dir):
    """Create a MortgageLoader with test data."""
    from loaders.mortgage_loader import MortgageLoader
    return MortgageLoader(data_dir=populated_data_dir)


@pytest.fixture
def gauge_loader(populated_data_dir):
    """Create a GaugeLoader with test data."""
    from loaders.gauge_loader import GaugeLoader
    return GaugeLoader(data_dir=populated_data_dir)


@pytest.fixture
def timeseries_loader(populated_data_dir):
    """Create a TimeseriesLoader with test data."""
    from loaders.timeseries_loader import TimeseriesLoader
    return TimeseriesLoader(data_dir=populated_data_dir)


@pytest.fixture
def storm_loader(populated_data_dir):
    """Create a StormLoader with test data."""
    from loaders.storm_loader import StormLoader
    return StormLoader(data_dir=populated_data_dir)


@pytest.fixture
def loader_registry(populated_data_dir):
    """Create a LoaderRegistry with test data."""
    from loaders.loader_registry import LoaderRegistry
    return LoaderRegistry(data_dir=populated_data_dir)
