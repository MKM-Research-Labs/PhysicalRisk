# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Asset-type configuration for the property / commercial timeseries + hazard-curve
generators.

The flood propagation, IDW interpolation, depth-damage, and PRS pricing logic
is identical between residential and commercial assets. What differs is the
input JSON shape and the output filenames:

                        residential                commercial
  portfolio_filename    property.json              commercial.json
  portfolio_key         properties                 commercial_assets
  root_section_key      PropertyHeader             CommercialAsset
  attributes_key        PropertyAttributes         CommercialAttributes
  id_prefix             PROP-                      CPROP-
  ts_dirs.normal        propertyts                 commercialts
  ts_dirs.shd           propertytsd                commercialtsd
  ts_dirs.she           propertytse                commercialtse
  ts_dirs.bri           propertytsb                commercialtsb
  ts_dirs.win           propertytsw                commercialtsw
  ts_dirs.faw           propertytsfaw              commercialtsfaw
  ts_dirs.fow           propertytsfow              commercialtsfow
  hc_files.normal       propertyhc.json            commercialhc.json
  hc_files.shd          propertyshd.json           commercialshd.json
  hc_files.she          propertyshe.json           commercialshe.json
  hc_files.bri          propertybri.json           commercialbri.json
  hc_files.win          propertywin.json           commercialwin.json
  hc_files.faw          propertyfaw.json           commercialfaw.json
  hc_files.fow          propertyfow.json           commercialfow.json
  type_field            PropertyResi               CommercialType
  type_default          Detached                   Office

The TS + HC generator classes read an ``ASSET_CONFIG`` class attribute. The
residential generators set it to ``RESIDENTIAL_CONFIG``; the commercial
subclasses override only that attribute.
"""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class AssetTypeConfig:
    """Per-asset-type knobs for the ts/hc generators."""

    # Input portfolio
    portfolio_filename: str       # e.g. "property.json" / "commercial.json"
    portfolio_key: str            # JSON key holding the records list

    # Record shape
    root_section_key: str         # "PropertyHeader" / "CommercialAsset"
    attributes_key: str           # "PropertyAttributes" / "CommercialAttributes"
    type_field: str               # field name inside attributes that holds the asset-type label
    type_default: str             # fallback label when the field is absent

    # Output naming
    id_prefix: str                # "PROP-" / "CPROP-" — used for output filenames + glob
    ts_dirs: Mapping[str, str]    # mode → ts output directory name
    hc_files: Mapping[str, str]   # mode → hc output JSON filename
    label: str                    # human-readable label for log lines

    @property
    def id_glob(self) -> str:
        """Glob pattern matching the per-asset JSON files in the ts output dirs."""
        return f"{self.id_prefix}*.json"


RESIDENTIAL_CONFIG = AssetTypeConfig(
    portfolio_filename="property.json",
    portfolio_key="properties",
    root_section_key="PropertyHeader",
    attributes_key="PropertyAttributes",
    type_field="PropertyResi",
    type_default="Detached",
    id_prefix="PROP-",
    ts_dirs={
        "normal": "propertyts",
        "shd": "propertytsd",
        "she": "propertytse",
        "bri": "propertytsb",
        "win": "propertytsw",
        "faw": "propertytsfaw",
        "fow": "propertytsfow",
    },
    hc_files={
        "normal": "propertyhc.json",
        "shd": "propertyshd.json",
        "she": "propertyshe.json",
        "bri": "propertybri.json",
        "win": "propertywin.json",
        "faw": "propertyfaw.json",
        "fow": "propertyfow.json",
    },
    label="Property",
)


COMMERCIAL_CONFIG = AssetTypeConfig(
    portfolio_filename="commercial.json",
    portfolio_key="commercial_assets",
    root_section_key="CommercialAsset",
    attributes_key="CommercialAttributes",
    type_field="CommercialType",
    type_default="Office",
    id_prefix="CPROP-",
    ts_dirs={
        "normal": "commercialts",
        "shd": "commercialtsd",
        "she": "commercialtse",
        "bri": "commercialtsb",
        "win": "commercialtsw",
        "faw": "commercialtsfaw",
        "fow": "commercialtsfow",
    },
    hc_files={
        "normal": "commercialhc.json",
        "shd": "commercialshd.json",
        "she": "commercialshe.json",
        "bri": "commercialbri.json",
        "win": "commercialwin.json",
        "faw": "commercialfaw.json",
        "fow": "commercialfow.json",
    },
    label="Commercial",
)


__all__ = ["AssetTypeConfig", "RESIDENTIAL_CONFIG", "COMMERCIAL_CONFIG"]
