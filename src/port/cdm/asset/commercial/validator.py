# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Commercial asset CDM validation logic."""

from typing import Dict, List


def validate(commercial_data: dict) -> Dict[str, List[str]]:
    """Validate a commercial asset record against the CDM schema."""
    errors: Dict[str, List[str]] = {}

    try:
        header = commercial_data.get("CommercialAsset", {}).get("Header", {})
        header_errors: List[str] = []
        if not header.get("PropertyID"):
            header_errors.append("Missing required field: PropertyID")
        if not header.get("CatchmentID"):
            header_errors.append("Missing recommended field: CatchmentID")
        if header_errors:
            errors["Header"] = header_errors

        attrs = commercial_data.get("CommercialAsset", {}).get("CommercialAttributes", {})
        attr_errors: List[str] = []
        if not attrs.get("CommercialType"):
            attr_errors.append("Missing required field: CommercialType")
        if attr_errors:
            errors["CommercialAttributes"] = attr_errors

        location = commercial_data.get("CommercialAsset", {}).get("Location", {})
        loc_errors: List[str] = []
        if not location.get("LatitudeDegrees"):
            loc_errors.append("Missing required field: LatitudeDegrees")
        if not location.get("LongitudeDegrees"):
            loc_errors.append("Missing required field: LongitudeDegrees")
        if loc_errors:
            errors["Location"] = loc_errors

        return errors

    except Exception as exc:
        return {"validation_error": [str(exc)]}


def get_required_fields() -> List[str]:
    return [
        "CommercialAsset.Header.PropertyID",
        "CommercialAsset.Header.CatchmentID",
        "CommercialAsset.CommercialAttributes.CommercialType",
        "CommercialAsset.Location.LatitudeDegrees",
        "CommercialAsset.Location.LongitudeDegrees",
    ]
