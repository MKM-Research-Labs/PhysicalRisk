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
