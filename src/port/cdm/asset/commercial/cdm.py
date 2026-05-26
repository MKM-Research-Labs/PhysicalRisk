# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""CommercialAssetCDM — CDM implementation for commercial asset data."""

from typing import Dict, List

from ...base import BaseCDM
from .schema import COMMERCIAL_SCHEMA, DEFAULT_ELEVATION
from .validator import get_required_fields, validate


class CommercialAssetCDM(BaseCDM):
    """Commercial Asset Common Data Model (CDM) implementation.

    Scope: office, retail, hotel, leisure, healthcare, multi-family, mixed-use.
    Industrial / warehouse / manufacturing live in asset/industrial/.
    """

    DEFAULT_ELEVATION = DEFAULT_ELEVATION

    def __init__(self):
        self._schema = COMMERCIAL_SCHEMA

    @property
    def schema(self) -> Dict:
        return self._schema

    def validate(self, commercial_data: dict) -> Dict[str, List[str]]:
        return validate(commercial_data)

    def create_mapping(self, asset: dict) -> dict:
        """Stub flat mapping — full mapping helpers TBD on a later pass."""
        ca = asset.get("CommercialAsset", {})
        header = ca.get("Header", {})
        attrs = ca.get("CommercialAttributes", {})
        location = ca.get("Location", {})
        return {k: v for k, v in {
            "property_id": header.get("PropertyID"),
            "catchment_id": header.get("CatchmentID"),
            "commercial_type": attrs.get("CommercialType"),
            "use_class_uko": attrs.get("UseClassUKO"),
            "property_area_sqm": attrs.get("PropertyAreaSqm"),
            "net_internal_area_sqm": attrs.get("NetInternalAreaSqm"),
            "latitude": location.get("LatitudeDegrees"),
            "longitude": location.get("LongitudeDegrees"),
        }.items() if v is not None}

    def get_required_fields(self) -> List[str]:
        return get_required_fields()
