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

"""Tests for PropertyHazardCurveGenerator main generation flow."""

import json

from port.src.property.propertyhc import (
    DEPTH_THRESHOLDS,
    MIN_PRS_SPREAD_BPS,
    TENORS,
    PropertyHazardCurveGenerator,
)


class TestPropertyHazardCurveGenerator:
    """Test the main generator."""

    def test_generate_produces_output(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        output_path = output_dir / "propertyhc.json"
        assert output_path.exists()

        with open(output_path) as f:
            data = json.load(f)

        assert "metadata" in data
        assert "property_hazard_curves" in data
        assert data["metadata"]["catchment_id"] == "thames"

    def test_properties_with_gev(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        stats = gen.generate()

        assert stats["properties_with_gev"] == 2
        assert stats["properties_with_floor"] == 1
        assert stats["properties_skipped"] == 0

    def test_output_structure(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        curves = data["property_hazard_curves"]
        assert "PROP-001" in curves
        assert "PROP-002" in curves
        assert "PROP-003" in curves

        prop1 = curves["PROP-001"]
        assert prop1["property_id"] == "PROP-001"
        assert prop1["flood_count"] == 5
        assert prop1["has_gev"] is True
        assert prop1["pricing_method"] == "gev"
        assert "gev_params" in prop1
        assert "depth_thresholds" in prop1
        assert "term_structure" in prop1
        assert "nearest_gauges" in prop1
        assert "summary" in prop1

        prop2 = curves["PROP-002"]
        assert prop2["has_gev"] is False
        assert prop2["pricing_method"] == "floor"
        assert prop2["min_spread_bps"] == MIN_PRS_SPREAD_BPS
        assert prop2["gev_params"] is None

    def test_gev_params_structure(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        gev = data["property_hazard_curves"]["PROP-001"]["gev_params"]
        assert "shape" in gev
        assert "loc" in gev
        assert "scale" in gev
        assert gev["scale"] > 0

    def test_depth_thresholds(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        thresholds = data["property_hazard_curves"]["PROP-001"]["depth_thresholds"]
        assert "any_flood" in thresholds
        assert "moderate" in thresholds
        assert "severe" in thresholds

        assert thresholds["any_flood"]["annual_probability"] >= thresholds["moderate"]["annual_probability"]
        assert thresholds["moderate"]["annual_probability"] >= thresholds["severe"]["annual_probability"]
        assert thresholds["any_flood"]["annual_probability"] <= 0.06

    def test_term_structure(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        ts = data["property_hazard_curves"]["PROP-001"]["term_structure"]
        assert ts["tenors"] == TENORS

        for threshold_name in DEPTH_THRESHOLDS:
            assert threshold_name in ts
            assert "survival" in ts[threshold_name]
            assert "prs_spread_bps" in ts[threshold_name]
            assert len(ts[threshold_name]["survival"]) == len(TENORS)

    def test_survival_decreases_with_tenor(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        ts = data["property_hazard_curves"]["PROP-001"]["term_structure"]
        survival = ts["any_flood"]["survival"]

        for i in range(1, len(survival)):
            assert survival[i] <= survival[i - 1]

    def test_basis_calculation(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        nearest = data["property_hazard_curves"]["PROP-001"]["nearest_gauges"]
        assert len(nearest) > 0

        ng0 = nearest[0]
        assert ng0["gauge_id"] == "GAUGE-001"
        assert "basis_bps" in ng0
        assert "event_basis" in ng0
        assert "flood_transmission_rate" in ng0

        assert ng0["event_basis"] == 15
        assert ng0["flood_transmission_rate"] == 0.25

    def test_high_transmission_rate(self, output_dir):
        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gen.generate()

        with open(output_dir / "propertyhc.json") as f:
            data = json.load(f)

        prop3 = data["property_hazard_curves"]["PROP-003"]
        assert prop3["summary"]["flood_transmission_rate"] == 1.0
