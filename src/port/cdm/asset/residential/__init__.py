# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Residential asset CDM package.

Sub-modules
-----------
schema     — PROPERTY_SCHEMA dict + DEFAULT_ELEVATION constant
cdm        — ResidentialAssetCDM class
validator  — validate() and get_required_fields() functions
mapping    — create_mapping() function (nested CDM -> flat snake_case)
bri        — apply_bri_rating() helper
contents   — CONTENTS_SCHEMA (asset.residential-specific extension)
"""

from .cdm import ResidentialAssetCDM  # noqa: F401
from .schema import DEFAULT_ELEVATION, PROPERTY_SCHEMA  # noqa: F401

__all__ = ["ResidentialAssetCDM", "PROPERTY_SCHEMA", "DEFAULT_ELEVATION"]
