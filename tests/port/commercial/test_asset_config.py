# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for the shared AssetTypeConfig and the two configured instances."""

import pytest

from port.utils.asset_config import (
    AssetTypeConfig,
    COMMERCIAL_CONFIG,
    RESIDENTIAL_CONFIG,
)


class TestAssetTypeConfigDataclass:

    def test_residential_config_values(self):
        c = RESIDENTIAL_CONFIG
        assert c.portfolio_filename == "property.json"
        assert c.portfolio_key == "properties"
        assert c.root_section_key == "PropertyHeader"
        assert c.attributes_key == "PropertyAttributes"
        assert c.id_prefix == "PROP-"
        assert c.id_glob == "PROP-*.json"
        assert c.label == "Property"

    def test_commercial_config_values(self):
        c = COMMERCIAL_CONFIG
        assert c.portfolio_filename == "commercial.json"
        assert c.portfolio_key == "commercial_assets"
        assert c.root_section_key == "CommercialAsset"
        assert c.attributes_key == "CommercialAttributes"
        assert c.id_prefix == "CPROP-"
        assert c.id_glob == "CPROP-*.json"
        assert c.label == "Commercial"

    def test_residential_ts_dirs(self):
        assert RESIDENTIAL_CONFIG.ts_dirs == {
            "normal": "propertyts",
            "shd": "propertytsd",
            "she": "propertytse",
            "bri": "propertytsb",
        }

    def test_commercial_ts_dirs(self):
        assert COMMERCIAL_CONFIG.ts_dirs == {
            "normal": "commercialts",
            "shd": "commercialtsd",
            "she": "commercialtse",
            "bri": "commercialtsb",
        }

    def test_residential_hc_files(self):
        assert RESIDENTIAL_CONFIG.hc_files == {
            "normal": "propertyhc.json",
            "shd": "propertyshd.json",
            "she": "propertyshe.json",
            "bri": "propertybri.json",
        }

    def test_commercial_hc_files(self):
        assert COMMERCIAL_CONFIG.hc_files == {
            "normal": "commercialhc.json",
            "shd": "commercialshd.json",
            "she": "commercialshe.json",
            "bri": "commercialbri.json",
        }

    def test_no_naming_collision_between_configs(self):
        """The two configs must never reference the same output directory or
        file — that would let one asset class trample the other."""
        assert set(RESIDENTIAL_CONFIG.ts_dirs.values()).isdisjoint(
            set(COMMERCIAL_CONFIG.ts_dirs.values()))
        assert set(RESIDENTIAL_CONFIG.hc_files.values()).isdisjoint(
            set(COMMERCIAL_CONFIG.hc_files.values()))
        assert RESIDENTIAL_CONFIG.portfolio_filename != COMMERCIAL_CONFIG.portfolio_filename
        assert RESIDENTIAL_CONFIG.id_prefix != COMMERCIAL_CONFIG.id_prefix

    def test_config_is_frozen(self):
        with pytest.raises((AttributeError, Exception)):
            RESIDENTIAL_CONFIG.portfolio_filename = "other.json"  # type: ignore
