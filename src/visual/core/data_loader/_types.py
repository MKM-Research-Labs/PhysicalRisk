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

"""Data containers for the visualization data loader."""

from dataclasses import dataclass
from typing import Any, Dict, List, NamedTuple, Optional


@dataclass
class LoadedData:
    """Container for all loaded visualization data."""
    gauge_data: Optional[Dict[str, Any]] = None
    property_data: Optional[Dict[str, Any]] = None
    rloan_data: Optional[Dict[str, Any]] = None
    commercial_data: Optional[Dict[str, Any]] = None
    commercial_loan_data: Optional[Dict[str, Any]] = None
    hazard_data: Optional[Dict[str, Any]] = None
    property_hazard_data: Optional[Dict[str, Any]] = None
    storm_data: Optional[Dict[str, Any]] = None
    counterparty_data: Optional[Dict[str, Any]] = None

    # Directory-based data counts
    gaugets_count: int = 0
    gaugehd_count: int = 0
    propertyts_count: int = 0

    # Processed lookups
    rloan_lookup: Optional[Dict[str, Dict]] = None
    commercial_loan_lookup: Optional[Dict[str, Dict]] = None
    gauge_flood_info: Optional[Dict[str, Dict]] = None
    property_flood_info: Optional[Dict[str, Dict]] = None


class DataValidationResult(NamedTuple):
    """Result of data validation."""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    summary: Dict[str, Any]
