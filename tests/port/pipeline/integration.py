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

"""Tests for dependency chains and end-to-end pipeline output integrity."""

import json

import pytest

from tests.port.pipeline.conftest import N_GAUGES, N_PROPERTIES


class TestDependencyChains:
    """Verify outputs from earlier steps are consumed by later steps."""

    def test_mortgage_reads_property(self, pipeline_dir):
        with open(pipeline_dir / "property.json") as f:
            prop_ids = {
                p["PropertyHeader"]["Header"]["PropertyID"]
                for p in json.load(f)["properties"]
            }
        with open(pipeline_dir / "loan.json") as f:
            for m in json.load(f)["loans"]:
                mid = m.get("RLoan", {}).get("Header", {}).get("PropertyID", "")
                assert mid in prop_ids

    def test_gaugets_reads_gauge(self, pipeline_dir):
        with open(pipeline_dir / "gauge.json") as f:
            gauge_ids = {
                g["FloodGauge"]["Header"]["GaugeID"]
                for g in json.load(f)["flood_gauges"]
            }
        for gf in (pipeline_dir / "gaugets").glob("GAUGE-*.json"):
            with open(gf) as f:
                data = json.load(f)
            gid = data.get("gauge_id", gf.stem)
            assert gid in gauge_ids

    def test_hazard_reads_gauge_and_storms(self, pipeline_dir):
        with open(pipeline_dir / "gauge.json") as f:
            gauge_ids = {
                g["FloodGauge"]["Header"]["GaugeID"]
                for g in json.load(f)["flood_gauges"]
            }
        with open(pipeline_dir / "gaugehc.json") as f:
            hc_curves = json.load(f).get("hazard_curves", {})
        assert len(hc_curves) > 0
        for gid in hc_curves:
            assert gid in gauge_ids

    def test_propertyts_uses_nearest_gauges(self, pipeline_dir):
        with open(pipeline_dir / "gauge.json") as f:
            gauge_ids = {
                g["FloodGauge"]["Header"]["GaugeID"]
                for g in json.load(f)["flood_gauges"]
            }
        prop_files = list((pipeline_dir / "propertyts").glob("PROP-*.json"))
        if not prop_files:
            pytest.skip("No per-property files to check")
        for pf in prop_files[:3]:
            with open(pf) as f:
                data = json.load(f)
            for ng in data.get("nearest_gauges", []):
                assert ng["gauge_id"] in gauge_ids

    def test_propertyhc_references_properties(self, pipeline_dir):
        phc_path = pipeline_dir / "propertyhc.json"
        if not phc_path.exists():
            pytest.skip("propertyhc.json not generated")
        with open(pipeline_dir / "property.json") as f:
            prop_ids = {
                p["PropertyHeader"]["Header"]["PropertyID"]
                for p in json.load(f)["properties"]
            }
        with open(phc_path) as f:
            for pid in json.load(f).get("property_hazard_curves", {}):
                assert pid in prop_ids

    def test_gaugehd_references_gauges(self, pipeline_dir):
        with open(pipeline_dir / "gauge.json") as f:
            gauge_ids = {
                g["FloodGauge"]["Header"]["GaugeID"]
                for g in json.load(f)["flood_gauges"]
            }
        for hf in (pipeline_dir / "gaugehd").glob("gauge_*_hd.json"):
            with open(hf) as f:
                data = json.load(f)
            gid = data.get("gauge_metadata", {}).get("gauge_id", "")
            assert gid in gauge_ids


class TestEndToEndPipeline:
    """Verify the full pipeline produces all expected output artifacts."""

    def test_full_pipeline_generates_all_outputs(self, pipeline_dir):
        for name in ["gauge.json", "property.json", "loan.json",
                     "storm_sequences.json", "counterparty.json", "gaugehc.json"]:
            assert (pipeline_dir / name).exists()
        assert (pipeline_dir / "gaugets").is_dir()
        assert (pipeline_dir / "gaugehd").is_dir()
        assert (pipeline_dir / "propertyts").is_dir()
        assert (pipeline_dir / "propertyts" / "portfolio_flood_summary.json").exists()

    def test_pipeline_output_file_integrity(self, pipeline_dir):
        checks = {
            "gauge.json": "flood_gauges",
            "property.json": "properties",
            "loan.json": "loans",
            "storm_sequences.json": "sequences",
            "counterparty.json": "counterparties",
            "gaugehc.json": "hazard_curves",
        }
        for filename, expected_key in checks.items():
            with open(pipeline_dir / filename) as f:
                data = json.load(f)
            assert expected_key in data

    def test_gauge_count_propagates(self, pipeline_dir):
        with open(pipeline_dir / "gauge.json") as f:
            n = len(json.load(f)["flood_gauges"])
        assert n == N_GAUGES
        assert len(list((pipeline_dir / "gaugets").glob("GAUGE-*.json"))) >= n
        assert len(list((pipeline_dir / "gaugehd").glob("gauge_*_hd.json"))) == n
        with open(pipeline_dir / "gaugehc.json") as f:
            assert len(json.load(f)["hazard_curves"]) == n

    def test_property_count_propagates(self, pipeline_dir):
        with open(pipeline_dir / "property.json") as f:
            n = len(json.load(f)["properties"])
        assert n == N_PROPERTIES
        with open(pipeline_dir / "propertyts" / "portfolio_flood_summary.json") as f:
            assert json.load(f)["summary"]["total_properties"] == n
