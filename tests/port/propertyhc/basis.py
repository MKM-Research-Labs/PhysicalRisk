# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for spread decomposition (replaces old basis waterfall tests)."""

import json

import pytest

from port.src.property.propertyhc import PropertyHazardCurveGenerator


class TestSpreadDecomposition:
    """Test the data-driven spread decomposition."""

    def test_decomposition_attached_after_post_processing(self, output_dir):
        """After attach_spread_decomposition, propertyhc.json has decomposition."""
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        # Generate shd and she variants
        shd_gen = PropertyHazardCurveGenerator(output_dir, verbose=False, mode="shd")
        she_gen = PropertyHazardCurveGenerator(output_dir, verbose=False, mode="she")

        # Create propertytsd and propertytse dirs (copy from propertyts)
        import shutil
        pts_dir = output_dir / "propertyts"
        for variant in ["propertytsd", "propertytse"]:
            dest = output_dir / variant
            if not dest.exists():
                shutil.copytree(pts_dir, dest)

        shd_gen.generate()
        she_gen.generate()

        # Now attach decomposition
        gen.attach_spread_decomposition()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        for prop_id, pc in data["property_hazard_curves"].items():
            assert "spread_decomposition" in pc, f"{prop_id} missing decomposition"
            sd = pc["spread_decomposition"]
            assert "gauge_spread_bps" in sd
            assert "property_spread_bps" in sd
            assert "shd_spread_bps" in sd
            assert "she_spread_bps" in sd
            assert "distance_first" in sd
            assert "elevation_first" in sd

    def test_decomposition_paths_sum_correctly(self, output_dir):
        """Both decomposition paths should arrive at the property spread."""
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        import shutil
        pts_dir = output_dir / "propertyts"
        for variant in ["propertytsd", "propertytse"]:
            dest = output_dir / variant
            if not dest.exists():
                shutil.copytree(pts_dir, dest)

        PropertyHazardCurveGenerator(output_dir, verbose=False, mode="shd").generate()
        PropertyHazardCurveGenerator(output_dir, verbose=False, mode="she").generate()
        gen.attach_spread_decomposition()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        for prop_id, pc in data["property_hazard_curves"].items():
            sd = pc["spread_decomposition"]
            gauge = sd["gauge_spread_bps"]
            prop = sd["property_spread_bps"]

            # Path 1: gauge + distance_effect + elevation_effect = property
            df = sd["distance_first"]
            path1 = gauge + df["distance_effect_bps"] + df["elevation_effect_bps"]
            assert abs(path1 - prop) < 0.1, f"{prop_id}: distance-first path {path1} != {prop}"

            # Path 2: gauge + elevation_effect + distance_effect = property
            ef = sd["elevation_first"]
            path2 = gauge + ef["elevation_effect_bps"] + ef["distance_effect_bps"]
            assert abs(path2 - prop) < 0.1, f"{prop_id}: elevation-first path {path2} != {prop}"

    def test_decomposition_without_synthetic_files(self, output_dir):
        """Without shd/she files, decomposition still works (zeros)."""
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        # Don't generate shd/she — attach_spread_decomposition should handle gracefully
        n = gen.attach_spread_decomposition()
        assert n > 0

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        for prop_id, pc in data["property_hazard_curves"].items():
            sd = pc["spread_decomposition"]
            # shd and she spreads should be 0 (files not found)
            assert sd["shd_spread_bps"] == 0.0
            assert sd["she_spread_bps"] == 0.0


class TestEdgeCases:
    """Test edge cases."""

    def test_no_propertyts_dir(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        with pytest.raises(FileNotFoundError):
            gen.generate()

    def test_empty_propertyts_dir(self, tmp_path):
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        with open(tmp_path / "gaugehc.json", "w") as f:
            json.dump({"hazard_curves": {}}, f)

        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        stats = gen.generate()
        assert stats["total_properties"] == 0
        assert stats["properties_with_gev"] == 0

    def test_no_gauge_hazard_curves(self, output_dir):
        """Generator should still work without gauge hazard curves (empty basis)."""
        (output_dir / "gaugehc.json").unlink()
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        stats = gen.generate()
        assert stats["properties_with_gev"] == 2
        assert stats["properties_with_floor"] == 1

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        nearest = data["property_hazard_curves"]["PROP-001"]["nearest_gauges"]
        assert len(nearest) == 0
