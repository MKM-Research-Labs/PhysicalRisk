# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Shared helpers for layer modules."""


def get_properties_list(property_data):
    """Extract properties list from property data in various input shapes.

    Shared by PropertyLayer and MortgageLayer.
    """
    if isinstance(property_data, dict):
        properties = property_data.get('items') or property_data.get('properties') or []
        if not properties and 'PropertyHeader' in property_data:
            properties = [property_data]
        elif not properties:
            properties = property_data.get('portfolio', [])
    elif isinstance(property_data, list):
        properties = property_data
    else:
        properties = []
    return properties
