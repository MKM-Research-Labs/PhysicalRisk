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

"""Shared fixtures for CDM schema tests."""

import pytest

from port.cdm import (
    FloodGaugeCDM,
    LoanCDM,
    PhysicalRiskSwapCDM,
    ResidentialAssetCDM,
    StormEventCDM,
    StormTimeSeriesCDM,
)


@pytest.fixture
def gauge_cdm():
    return FloodGaugeCDM()


@pytest.fixture
def property_cdm():
    return ResidentialAssetCDM()


@pytest.fixture
def mortgage_cdm():
    return LoanCDM()


@pytest.fixture
def storm_cdm():
    return StormEventCDM()


@pytest.fixture
def stormts_cdm():
    return StormTimeSeriesCDM()


@pytest.fixture
def prs_cdm():
    return PhysicalRiskSwapCDM()
