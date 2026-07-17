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

"""
Common Data Model (CDM) definitions.

This package contains standardized data models for all entity types
used in the PRS platform. Each CDM provides schema definitions,
validation methods, and data transformation utilities.

All CDMs include CatchmentID for multi-catchment support.

Usage:
    from port.cdm import ResidentialAssetCDM, FloodGaugeCDM, LoanCDM

    # Validate property data
    cdm = ResidentialAssetCDM()
    errors = cdm.validate(property_data)

    # Create flat mapping from nested CDM structure
    flat_data = cdm.create_mapping(nested_data)
"""

from .asset.commercial.cdm import CommercialAssetCDM
from .asset.loan import LoanCDM
from .asset.residential.cdm import ResidentialAssetCDM
from .base import BaseCDM
from .ctpy import CounterpartyCDM
from .gauge import FloodGaugeCDM
from .oed_export import cdm_to_oed_row, cdm_to_oed_rows, export_oed_csv
from .prs import PhysicalRiskSwapCDM
from .storm import StormEventCDM, TCEventCDM
from .stormts import StormTimeSeriesCDM, TCEventTSCDM

__all__ = [
    # Base class
    'BaseCDM',

    # Asset CDMs
    'ResidentialAssetCDM',
    'CommercialAssetCDM',
    'LoanCDM',

    # Other entity CDMs
    'FloodGaugeCDM',
    'StormEventCDM',
    'StormTimeSeriesCDM',
    'PhysicalRiskSwapCDM',
    'CounterpartyCDM',

    # Backwards compatibility aliases
    'TCEventCDM',
    'TCEventTSCDM',

    # OED export
    'cdm_to_oed_row',
    'cdm_to_oed_rows',
    'export_oed_csv',
]
