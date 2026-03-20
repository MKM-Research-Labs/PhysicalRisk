# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

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
