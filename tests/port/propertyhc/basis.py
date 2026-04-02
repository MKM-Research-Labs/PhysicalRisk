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
            assert abs(path1 - prop) < 0.1, (
                f"{prop_id}: distance-first path {path1} != {prop}")

            # Path 2: gauge + elevation_effect + distance_effect = property
            ef = sd["elevation_first"]
            path2 = gauge + ef["elevation_effect_bps"] + ef["distance_effect_bps"]
            assert abs(path2 - prop) < 0.1, (
                f"{prop_id}: elevation-first path {path2} != {prop}")

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

    def test_decomposition_values_nonzero_with_synthetic_files(self, output_dir):
        """With shd/she files present, decomposition values must be non-zero.

        This is the regression guard for the all-zeros bug: if shd/she variants
        are generated, property_spread, gauge_spread, and at least one effect
        per path must be non-zero for properties that have flood data.
        """
        import shutil

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

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
            # Property spread must be non-zero (properties have flood events)
            assert sd["property_spread_bps"] != 0.0, (
                f"{prop_id}: property_spread_bps is zero"
            )
            assert sd["shd_spread_bps"] != 0.0, (
                f"{prop_id}: shd_spread_bps is zero"
            )
            assert sd["she_spread_bps"] != 0.0, (
                f"{prop_id}: she_spread_bps is zero"
            )

    def test_decomposition_effects_not_all_zero(self, output_dir):
        """At least one effect per path must be non-zero when gauge != property.

        Guards against the UI showing 0.0 for all effects even when the
        property spread differs from the gauge spread.
        """
        import shutil

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

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
            prop_ = sd["property_spread_bps"]

            if abs(prop_ - gauge) < 0.01:
                continue

            df = sd["distance_first"]
            assert df["distance_effect_bps"] != 0.0 or df["elevation_effect_bps"] != 0.0, (
                f"{prop_id}: distance-first effects are both zero but "
                f"gauge={gauge} != property={prop_}"
            )

            ef = sd["elevation_first"]
            assert ef["elevation_effect_bps"] != 0.0 or ef["distance_effect_bps"] != 0.0, (
                f"{prop_id}: elevation-first effects are both zero but "
                f"gauge={gauge} != property={prop_}"
            )

    def test_get_5yr_spread_returns_zero_for_empty(self):
        """_get_5yr_spread must return 0.0 for empty/missing data."""
        assert PropertyHazardCurveGenerator._get_5yr_spread({}) == 0.0
        assert PropertyHazardCurveGenerator._get_5yr_spread(
            {"term_structure": {}}
        ) == 0.0
        assert PropertyHazardCurveGenerator._get_5yr_spread(
            {"term_structure": {"any_flood": {"prs_spread_bps": [1, 2, 3]}}}
        ) == 0.0  # only 3 values, need index 4

    def test_get_5yr_spread_returns_correct_value(self):
        """_get_5yr_spread must return index 4 when available."""
        spreads = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        pc = {"term_structure": {"any_flood": {"prs_spread_bps": spreads}}}
        assert PropertyHazardCurveGenerator._get_5yr_spread(pc) == 50.0

    def test_get_5yr_spread_with_threshold(self):
        """_get_5yr_spread must work with specified threshold."""
        pc = {"term_structure": {
            "severe": {"prs_spread_bps": [0, 0, 0, 0, 20.0]},
        }}
        assert PropertyHazardCurveGenerator._get_5yr_spread(pc, 'severe') == 20.0
        # Default is any_flood
        assert PropertyHazardCurveGenerator._get_5yr_spread(pc, 'any_flood') == 0.0


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
