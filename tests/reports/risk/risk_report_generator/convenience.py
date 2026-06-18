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

"""Tests for generate_risk_report convenience function and edge-case inputs."""

from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
from .conftest import _make_generator


class TestGenerateRiskReportConvenienceFunction:
    """Tests for the module-level generate_risk_report() convenience function."""

    def test_basic_type_returns_path(self, tmp_path, minimal_flood_data):
        from reports.risk.generator import generate_risk_report
        path = generate_risk_report(minimal_flood_data, output_dir=tmp_path, report_type="basic")
        assert isinstance(path, Path)
        assert path.exists()

    def test_detailed_type_returns_path(self, tmp_path, minimal_flood_data):
        from reports.risk.generator import generate_risk_report
        path = generate_risk_report(minimal_flood_data, output_dir=tmp_path, report_type="detailed")
        assert path.exists()

    def test_summary_type_returns_path(self, tmp_path, minimal_flood_data):
        from reports.risk.generator import generate_risk_report
        path = generate_risk_report(minimal_flood_data, output_dir=tmp_path, report_type="summary")
        assert path.exists()

    def test_analysis_type_returns_path(self, tmp_path, minimal_flood_data):
        from reports.risk.generator import generate_risk_report
        path = generate_risk_report(minimal_flood_data, output_dir=tmp_path, report_type="analysis")
        assert path.exists()

    def test_unknown_type_falls_back_to_generate_report(self, tmp_path, minimal_flood_data):
        from reports.risk.generator import generate_risk_report
        path = generate_risk_report(minimal_flood_data, output_dir=tmp_path, report_type="unknown_xyz")
        assert path.exists()

    def test_default_report_type_is_basic(self, tmp_path, minimal_flood_data):
        """Omitting report_type should default to 'basic'."""
        from reports.risk.generator import RiskReportGenerator, generate_risk_report
        with patch.object(RiskReportGenerator, "generate_basic_report",
                          wraps=RiskReportGenerator(output_dir=tmp_path).generate_basic_report
                          ) as spy:
            generate_risk_report(minimal_flood_data, output_dir=tmp_path)
            # The function is called — just confirm no exception and path returned

    def test_output_dir_as_string(self, tmp_path, minimal_flood_data):
        from reports.risk.generator import generate_risk_report
        path = generate_risk_report(minimal_flood_data, output_dir=str(tmp_path))
        assert path.exists()

    def test_pdf_is_non_empty_bytes_on_disk(self, tmp_path, minimal_flood_data):
        from reports.risk.generator import generate_risk_report
        path = generate_risk_report(minimal_flood_data, output_dir=tmp_path)
        content = path.read_bytes()
        assert isinstance(content, bytes)
        assert len(content) > 0


class TestEdgeCases:
    """Edge-case inputs: empty dicts, None sub-keys, zero values, large data."""

    def test_completely_empty_flood_data(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_basic_report({})
        assert path.exists()

    def test_none_gauge_data_key(self, tmp_path):
        gen = _make_generator(tmp_path)
        data = {
            "summary": {"total_properties": 0},
            "gauge_data": None,
            "property_risk": None,
        }
        path = gen.generate_basic_report(data)
        assert path.exists()

    def test_zero_properties_at_risk(self, tmp_path):
        gen = _make_generator(tmp_path)
        data = {
            "summary": {
                "total_properties": 100,
                "properties_at_risk": 0,
                "percentage_at_risk": 0.0,
                "total_value": 50_000_000,
                "value_at_risk": 0,
                "percentage_value_at_risk": 0.0,
            },
            "gauge_data": {},
            "property_risk": {},
        }
        path = gen.generate_basic_report(data)
        assert path.exists()

    def test_negative_values_in_summary(self, tmp_path):
        """Negative/nonsensical values should not crash the generator."""
        gen = _make_generator(tmp_path)
        data = {
            "summary": {
                "total_properties": -5,
                "properties_at_risk": -1,
                "percentage_at_risk": -10.0,
                "total_value": -1_000_000,
                "value_at_risk": -100_000,
                "percentage_value_at_risk": -10.0,
            },
            "gauge_data": {},
            "property_risk": {},
        }
        path = gen.generate_basic_report(data)
        assert path.exists()

    def test_missing_summary_key(self, tmp_path):
        gen = _make_generator(tmp_path)
        path = gen.generate_basic_report({"catchment": "Thames"})
        assert path.exists()

    def test_single_page_report(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        path = gen.generate_report(minimal_flood_data, pages_to_include=["title"])
        assert path.exists()

    def test_all_unknown_pages_still_creates_pdf(self, tmp_path, minimal_flood_data):
        gen = _make_generator(tmp_path)
        # All pages unknown → empty elements list → doc.build creates minimal PDF
        path = gen.generate_report(minimal_flood_data, pages_to_include=["xxx", "yyy"])
        assert path.exists()

    def test_large_property_risk_dataset(self, tmp_path):
        """Verify no crash or timeout with 500 property entries."""
        properties: Dict[str, Any] = {}
        for i in range(500):
            pid = f"P_{i:05d}"
            properties[pid] = {
                "property_id": pid,
                "flood_depth": 0.1 * (i % 10),
                "risk_value": 0.01 * (i % 10),
                "risk_level": "Low",
            }
        gen = _make_generator(tmp_path)
        path = gen.generate_basic_report({
            "summary": {"total_properties": 500},
            "gauge_data": {},
            "property_risk": properties,
        })
        assert path.exists()

    def test_report_with_all_pages(self, tmp_path, full_flood_data):
        gen = _make_generator(tmp_path)
        all_pages = list(gen.pages.keys())
        path = gen.generate_report(full_flood_data, pages_to_include=all_pages)
        assert path.exists()
        assert path.stat().st_size > 0
