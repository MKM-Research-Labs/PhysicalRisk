# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Tests for synthetic hazard curve generation:
  - propertyshd (mode="shd"): reads from propertytsd/, writes propertyshd.json
  - propertyshe (mode="she"): reads from propertytse/, writes propertyshe.json
"""

import json

import pytest

from port.src.property.propertyhc import PropertyHazardCurveGenerator

from .conftest import write_gauge_hc, write_property_ts


@pytest.fixture
def shd_output_dir(tmp_path):
    """Output dir with propertytsd/ timeseries + gaugehc for shd hazard curves."""
    pts_dir = tmp_path / "propertytsd"
    pts_dir.mkdir(parents=True)
    write_gauge_hc(tmp_path)
    return tmp_path, pts_dir


@pytest.fixture
def she_output_dir(tmp_path):
    """Output dir with propertytse/ timeseries + gaugehc for she hazard curves."""
    pts_dir = tmp_path / "propertytse"
    pts_dir.mkdir(parents=True)
    write_gauge_hc(tmp_path)
    return tmp_path, pts_dir


class TestPropertyShdGenerate:

    def test_shd_output_file_is_propertyshd_json(self, shd_output_dir):
        output_dir, pts_dir = shd_output_dir
        write_property_ts(pts_dir, "PROP-shd1", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False, mode="shd")
        gen.generate()
        assert (output_dir / "propertyshd.json").exists()
        assert not (output_dir / "propertyhc.json").exists()

    def test_shd_has_term_structure(self, shd_output_dir):
        output_dir, pts_dir = shd_output_dir
        write_property_ts(pts_dir, "PROP-shd2", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False, mode="shd")
        gen.generate()
        with open(output_dir / "propertyshd.json") as f:
            data = json.load(f)
        pc = data["property_hazard_curves"]["PROP-shd2"]
        assert "term_structure" in pc
        assert "any_flood" in pc["term_structure"]

    def test_shd_reads_from_propertytsd(self, tmp_path):
        """shd mode should look for propertytsd/ not propertyts/."""
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False, mode="shd")
        with pytest.raises(FileNotFoundError, match="propertytsd"):
            gen.generate()


class TestPropertySheGenerate:

    def test_she_output_file_is_propertyshe_json(self, she_output_dir):
        output_dir, pts_dir = she_output_dir
        write_property_ts(pts_dir, "PROP-she1", n_floods=5)
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False, mode="she")
        gen.generate()
        assert (output_dir / "propertyshe.json").exists()

    def test_she_has_term_structure(self, she_output_dir):
        output_dir, pts_dir = she_output_dir
        write_property_ts(pts_dir, "PROP-she2", n_floods=5,
                          nearest_gauges=[{"gauge_id": "GAUGE-001", "distance_m": 0, "gauge_elevation_m": 3.5}])
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False, mode="she")
        gen.generate()
        with open(output_dir / "propertyshe.json") as f:
            data = json.load(f)
        pc = data["property_hazard_curves"]["PROP-she2"]
        assert "term_structure" in pc
        assert "any_flood" in pc["term_structure"]

    def test_she_reads_from_propertytse(self, tmp_path):
        """she mode should look for propertytse/ not propertyts/."""
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False, mode="she")
        with pytest.raises(FileNotFoundError, match="propertytse"):
            gen.generate()
