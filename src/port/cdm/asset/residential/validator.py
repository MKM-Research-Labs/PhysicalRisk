# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Residential asset CDM validation logic.

Provides validate() and get_required_fields() as module-level functions so they
can be used standalone or delegated to by ResidentialAssetCDM.
"""

from typing import Dict, List


def validate(property_data: dict) -> Dict[str, List[str]]:
    """
    Validate property data against the residential asset CDM schema.

    Args:
        property_data: Property data to validate.

    Returns:
        Dictionary of validation errors keyed by section name.
        Empty dict means the record is valid.
    """
    errors: Dict[str, List[str]] = {}

    try:
        header = property_data.get("PropertyHeader", {}).get("Header", {})
        header_errors: List[str] = []

        if not header.get("PropertyID"):
            header_errors.append("Missing required field: PropertyID")
        if not header.get("CatchmentID"):
            header_errors.append("Missing recommended field: CatchmentID")

        if header_errors:
            errors["Header"] = header_errors

        location = property_data.get("PropertyHeader", {}).get("Location", {})
        location_errors: List[str] = []

        if not location.get("LatitudeDegrees"):
            location_errors.append("Missing required field: LatitudeDegrees")
        if not location.get("LongitudeDegrees"):
            location_errors.append("Missing required field: LongitudeDegrees")

        if location_errors:
            errors["Location"] = location_errors

        return errors

    except Exception as exc:
        return {"validation_error": [str(exc)]}


def get_required_fields() -> List[str]:
    """Return the list of dotted-path required field names."""
    return [
        "PropertyHeader.Header.PropertyID",
        "PropertyHeader.Header.CatchmentID",
        "PropertyHeader.Location.LatitudeDegrees",
        "PropertyHeader.Location.LongitudeDegrees",
    ]
