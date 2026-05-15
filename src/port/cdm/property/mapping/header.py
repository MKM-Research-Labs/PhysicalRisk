# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flatten PropertyHeader (Header, Valuation, Attributes, Construction, Location)."""


def flatten_header(prop: dict) -> dict:
    """Return flat snake_case keys for PropertyHeader intrinsic-fact sections."""
    ph = prop.get("PropertyHeader", {})
    header = ph.get("Header", {})
    valuation = ph.get("Valuation", {})
    attrs = ph.get("PropertyAttributes", {})
    construction = ph.get("Construction", {})
    location = ph.get("Location", {})

    return {
        "property_id":      header.get("PropertyID"),
        "catchment_id":     header.get("CatchmentID"),
        "uprn":             header.get("UPRN"),
        "property_type":    header.get("propertyType", "residential"),
        "property_status":  header.get("propertyStatus", "active"),

        "value":             valuation.get("PropertyValue"),
        "valuation_date":    valuation.get("ValuationDate"),
        "valuation_method":  valuation.get("ValuationMethod"),

        "occupancy_type":     attrs.get("OccupancyType"),
        "property_area_sqm":  attrs.get("PropertyAreaSqm"),
        "property_resi":      attrs.get("PropertyResi"),
        "number_storeys":     attrs.get("NumberOfStoreys"),
        "construction_year":  attrs.get("ConstructionYear"),
        "property_period":    attrs.get("PropertyPeriod"),
        "council_tax_band":   attrs.get("CouncilTaxBand"),
        "number_bedrooms":    attrs.get("NumberBedrooms"),
        "number_bathrooms":   attrs.get("NumberBathrooms"),
        "property_condition": attrs.get("PropertyCondition"),

        "construction_type":  construction.get("ConstructionType"),
        "foundation_type":    construction.get("FoundationType"),
        "floor_level_metres": construction.get("FloorLevelMeters"),
        "basement_present":   construction.get("BasementPresent"),

        "building_number": location.get("BuildingNumber"),
        "street_name":     location.get("StreetName"),
        "town_city":       location.get("TownCity"),
        "county":          location.get("County"),
        "postcode":        location.get("Postcode"),
        "local_authority": location.get("LocalAuthority"),
        "country":         location.get("Country"),
        "region":          location.get("Region"),
        "urban_rural":     location.get("UrbanRuralClassification"),
        "latitude":        location.get("LatitudeDegrees"),
        "longitude":       location.get("LongitudeDegrees"),
    }
