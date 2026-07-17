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

"""Fixtures for data loader instances."""

import pytest


@pytest.fixture
def property_loader(populated_data_dir):
    """Create a PropertyLoader with test data."""
    from loaders.property_loader import PropertyLoader
    return PropertyLoader(data_dir=populated_data_dir)


@pytest.fixture
def rloan_loader(populated_data_dir):
    """Create a RLoanLoader with test data."""
    from loaders.rloan_loader import RLoanLoader
    return RLoanLoader(data_dir=populated_data_dir)


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
