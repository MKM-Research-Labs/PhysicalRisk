# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""PropertyCDM class — CDM implementation for property data."""

from typing import Dict, List

from ..base import BaseCDM
from .mapping import create_mapping
from .schema import DEFAULT_ELEVATION, PROPERTY_SCHEMA
from .validator import get_required_fields, validate


class PropertyCDM(BaseCDM):
    """
    Property Common Data Model (CDM) implementation.

    Provides a standardized schema and data transformation methods
    for property data with comprehensive attributes.

    Sub-module responsibilities
    ---------------------------
    schema.py    — canonical schema dict and DEFAULT_ELEVATION
    validator.py — validate() and get_required_fields()
    mapping.py   — create_mapping() (nested CDM -> flat snake_case dict)
    """

    DEFAULT_ELEVATION = DEFAULT_ELEVATION

    def __init__(self):
        """Initialize the Property CDM with schema definition."""
        self._schema = PROPERTY_SCHEMA

    @property
    def schema(self) -> Dict:
        """Return the CDM schema."""
        return self._schema

    def validate(self, property_data: dict) -> Dict[str, List[str]]:
        """
        Validate property data against the CDM schema.

        Args:
            property_data: Property data to validate.

        Returns:
            Dictionary of validation errors by section.  Empty = valid.
        """
        return validate(property_data)

    def create_mapping(self, prop: dict) -> dict:
        """
        Flatten a nested CDM record into a snake_case dict.

        Args:
            prop: Nested property data in CDM format.

        Returns:
            Flat dict with snake_case keys; None values are omitted.
        """
        return create_mapping(prop, default_elevation=self.DEFAULT_ELEVATION)

    def get_required_fields(self) -> List[str]:
        """Return list of dotted-path required field names."""
        return get_required_fields()
