# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Unit tests for Thames gauge random value generators.
"""

import re

import pytest


@pytest.mark.random_values
class TestGenerateGaugeMetadata:

    def test_returns_dict_with_required_keys(self, thames_gauge_random, sample_gauge_location):
        meta = thames_gauge_random.generate_gauge_metadata(0, sample_gauge_location, "Thames")
        required_keys = [
            "gauge_id", "historical_high_level", "flood_alert",
            "flood_warning", "severe_flood_warning", "install_date", "location",
        ]
        for key in required_keys:
            assert key in meta, f"Missing key: {key}"

    def test_gauge_id_format(self, thames_gauge_random, sample_gauge_location):
        meta = thames_gauge_random.generate_gauge_metadata(0, sample_gauge_location)
        assert re.match(r"^GAUGE-[a-f0-9]{8}$", meta["gauge_id"])

    def test_flood_stage_ordering(self, thames_gauge_random, sample_gauge_location):
        for _ in range(10):
            meta = thames_gauge_random.generate_gauge_metadata(0, sample_gauge_location)
            assert meta["flood_alert"] < meta["flood_warning"]
            assert meta["flood_warning"] < meta["severe_flood_warning"]
            assert meta["severe_flood_warning"] <= meta["historical_high_level"]

    def test_historical_high_level_range(self, thames_gauge_random, sample_gauge_location):
        for _ in range(10):
            meta = thames_gauge_random.generate_gauge_metadata(0, sample_gauge_location)
            assert 5.0 <= meta["historical_high_level"] <= 8.0

    def test_install_date_format(self, thames_gauge_random, sample_gauge_location):
        meta = thames_gauge_random.generate_gauge_metadata(0, sample_gauge_location)
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", meta["install_date"])

    def test_catchment_name_stored(self, thames_gauge_random, sample_gauge_location):
        meta = thames_gauge_random.generate_gauge_metadata(0, sample_gauge_location, "Thames")
        assert meta["catchment_name"] == "Thames"


@pytest.mark.random_values
class TestGenerateFieldValue:

    def _make_metadata(self, thames_gauge_random, sample_gauge_location):
        return thames_gauge_random.generate_gauge_metadata(0, sample_gauge_location, "Thames")

    def test_text_field_returns_string(self, thames_gauge_random, sample_gauge_location):
        meta = self._make_metadata(thames_gauge_random, sample_gauge_location)
        val = thames_gauge_random.generate_field_value(
            "GaugeOwner", {"type": "text"}, 0, meta
        )
        assert isinstance(val, str)
        assert len(val) > 0

    def test_decimal_field_returns_float(self, thames_gauge_random, sample_gauge_location):
        meta = self._make_metadata(thames_gauge_random, sample_gauge_location)
        val = thames_gauge_random.generate_field_value(
            "FloodAlert", {"type": "decimal"}, 0, meta
        )
        assert isinstance(val, (int, float))

    def test_menu_field_returns_valid_option(self, thames_gauge_random, sample_gauge_location):
        meta = self._make_metadata(thames_gauge_random, sample_gauge_location)
        options = ["Fully operational", "Maintenance required", "Temporarily offline"]
        val = thames_gauge_random.generate_field_value(
            "OperationalStatus", {"type": "menu", "options": options}, 0, meta
        )
        assert isinstance(val, str)

    def test_date_field_returns_date_string(self, thames_gauge_random, sample_gauge_location):
        meta = self._make_metadata(thames_gauge_random, sample_gauge_location)
        val = thames_gauge_random.generate_field_value(
            "InstallDate", {"type": "date"}, 0, meta
        )
        assert isinstance(val, str)
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", val)

    def test_gauge_name_includes_area(self, thames_gauge_random, sample_gauge_location):
        meta = self._make_metadata(thames_gauge_random, sample_gauge_location)
        val = thames_gauge_random.generate_field_value(
            "GaugeName", {"type": "text"}, 0, meta
        )
        assert "TestArea" in val


@pytest.mark.random_values
class TestFloodRiskAssessment:

    def test_close_to_thames_high_risk(self, thames_gauge_random):
        location = {"distance_to_thames": 50}
        for _ in range(10):
            result = thames_gauge_random.generate_flood_risk_assessment(location)
            assert result["FloodRiskScore"] >= 7
            assert result["FloodRiskCategory"] in ["High", "Very High"]

    def test_far_from_thames_lower_risk(self, thames_gauge_random):
        location = {"distance_to_thames": 500}
        for _ in range(10):
            result = thames_gauge_random.generate_flood_risk_assessment(location)
            assert result["FloodRiskScore"] <= 6
            assert result["FloodRiskCategory"] in ["Low", "Medium"]
