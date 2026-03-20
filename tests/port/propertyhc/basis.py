# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for basis waterfall calculation and edge cases."""

import json

import pytest

from port.src.property.propertyhc import (
    COMPOSITION_BASIS_BPS,
    DISTANCE_MAX_BPS,
    ELEVATION_MAX_BENEFIT_BPS,
    MODEL_UNCERTAINTY_BPS,
    TERRAIN_BASIS_BPS,
    PropertyHazardCurveGenerator,
)


class TestBasisWaterfall:
    """Test the 5-component basis waterfall calculation."""

    def _make_pdata(self, **overrides):
        pdata = {
            "elevation_m": 4.0,
            "flood_zone": "Zone 1",
            "property_type": "Detached",
            "construction_year": 2005,
        }
        pdata.update(overrides)
        return pdata

    def _make_gauges(self, distances_m=None, gauge_elevs=None):
        if distances_m is None:
            distances_m = [1000]
        if gauge_elevs is None:
            gauge_elevs = [3.5]
        return [
            {"gauge_id": f"G-{i}", "distance_m": d, "gauge_elevation_m": e}
            for i, (d, e) in enumerate(zip(distances_m, gauge_elevs))
        ]

    def test_model_uncertainty_is_fixed(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        result = gen._compute_basis_waterfall(self._make_pdata(), self._make_gauges())
        assert result["model_uncertainty_bp"] == MODEL_UNCERTAINTY_BPS

    def test_distance_basis_scales_linearly(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        result = gen._compute_basis_waterfall(
            self._make_pdata(), self._make_gauges(distances_m=[2000]))
        assert result["distance_bp"] == pytest.approx(1.0, abs=0.1)

    def test_distance_basis_capped(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        result = gen._compute_basis_waterfall(
            self._make_pdata(), self._make_gauges(distances_m=[20000]))
        assert result["distance_bp"] == DISTANCE_MAX_BPS

    def test_elevation_above_gauge_reduces_spread(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        result = gen._compute_basis_waterfall(
            self._make_pdata(elevation_m=8.5), self._make_gauges(gauge_elevs=[3.5]))
        assert result["elevation_bp"] == pytest.approx(-1.0, abs=0.1)

    def test_elevation_below_gauge_no_benefit(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        result = gen._compute_basis_waterfall(
            self._make_pdata(elevation_m=2.0), self._make_gauges(gauge_elevs=[3.5]))
        assert result["elevation_bp"] == 0.0

    def test_elevation_capped_at_3bp(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        result = gen._compute_basis_waterfall(
            self._make_pdata(elevation_m=33.5), self._make_gauges(gauge_elevs=[3.5]))
        assert result["elevation_bp"] == -ELEVATION_MAX_BENEFIT_BPS

    def test_terrain_zone3_high_risk(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        result = gen._compute_basis_waterfall(
            self._make_pdata(flood_zone="Zone 3a"), self._make_gauges())
        assert result["terrain_bp"] == TERRAIN_BASIS_BPS["Zone 3a"]

    def test_terrain_zone1_low_risk(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        result = gen._compute_basis_waterfall(
            self._make_pdata(flood_zone="Zone 1"), self._make_gauges())
        assert result["terrain_bp"] == 0.0

    def test_composition_flat_penalty(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        result = gen._compute_basis_waterfall(
            self._make_pdata(property_type="Flat", construction_year=2005),
            self._make_gauges())
        assert result["composition_bp"] == COMPOSITION_BASIS_BPS["Flat"]

    def test_composition_pre2000_penalty(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        result = gen._compute_basis_waterfall(
            self._make_pdata(property_type="Detached", construction_year=1990),
            self._make_gauges())
        assert result["composition_bp"] == 1.0

    def test_total_basis_sums_components(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        pdata = self._make_pdata(
            elevation_m=5.5, flood_zone="Zone 2",
            property_type="Flat", construction_year=1990
        )
        result = gen._compute_basis_waterfall(
            pdata, self._make_gauges(distances_m=[4000], gauge_elevs=[3.5]))

        expected_total = (
            result["model_uncertainty_bp"] + result["distance_bp"] +
            result["elevation_bp"] + result["terrain_bp"] + result["composition_bp"]
        )
        assert result["total_basis_bp"] == pytest.approx(expected_total, abs=0.1)

    def test_basis_waterfall_in_generated_output(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        bw1 = data["property_hazard_curves"]["PROP-001"]["basis_waterfall"]
        assert bw1["model_uncertainty_bp"] == 2.0
        assert bw1["terrain_bp"] == 2.0
        assert bw1["flood_zone"] == "Zone 2"
        assert bw1["property_type"] == "Semi-detached"
        assert bw1["construction_year"] == 1995
        assert bw1["composition_bp"] == 1.0

        bw3 = data["property_hazard_curves"]["PROP-003"]["basis_waterfall"]
        assert bw3["terrain_bp"] == 3.0
        assert bw3["composition_bp"] == 3.0


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
