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

"""FloodGaugeCDM class — CDM implementation for flood gauge data."""

from typing import Dict, List

from ..base import BaseCDM
from .schema import GAUGE_SCHEMA
from .validate import validate_gauge
from .mapping import create_gauge_mapping, get_required_fields, get_nrfa_fields


class FloodGaugeCDM(BaseCDM):
    """
    Flood Gauge Common Data Model (CDM) implementation.

    Provides a standardized schema and data transformation methods
    for flood gauge data with multi-catchment support and historical
    data integration.
    """

    def __init__(self):
        """Initialize the Flood Gauge CDM with schema definition."""
        self._schema = GAUGE_SCHEMA

    @property
    def schema(self) -> Dict:
        """Return the CDM schema."""
        return self._schema

    def validate(self, gauge_data: dict) -> Dict[str, List[str]]:
        """Validate flood gauge data against the CDM schema."""
        return validate_gauge(gauge_data)

    def create_mapping(self, gauge: dict) -> dict:
        """Create a flat dictionary from nested CDM structure."""
        return create_gauge_mapping(gauge)

    def get_required_fields(self) -> List[str]:
        """Return list of required fields."""
        return get_required_fields()

    def get_nrfa_fields(self) -> List[str]:
        """Return list of NRFA metadata fields."""
        return get_nrfa_fields()
