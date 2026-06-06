# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for DateTimeEncoder and _extract_property_info."""

import json
from datetime import datetime

import numpy as np
import pytest

from port.src.mortgage import DateTimeEncoder, MortgagePortfolioGenerator
from tests.port.mortgage.conftest import make_generator


# ===========================================================================
# DateTimeEncoder
# ===========================================================================

class TestDateTimeEncoder:
    """All type-dispatch branches of the custom JSON encoder."""

    def test_datetime_encoded_as_isoformat(self):
        dt = datetime(2024, 6, 15, 9, 30, 0)
        result = json.dumps({"ts": dt}, cls=DateTimeEncoder)
        assert "2024-06-15" in result

    def test_numpy_int64_encoded_as_int(self):
        result = json.loads(json.dumps(np.int64(99), cls=DateTimeEncoder))
        assert result == 99
        assert isinstance(result, int)

    def test_numpy_float64_encoded_as_float(self):
        result = json.loads(json.dumps(np.float64(3.14), cls=DateTimeEncoder))
        assert abs(result - 3.14) < 1e-6

    def test_numpy_ndarray_encoded_as_list(self):
        result = json.loads(json.dumps(np.array([1, 2, 3]), cls=DateTimeEncoder))
        assert result == [1, 2, 3]

    def test_numpy_int32_encoded(self):
        result = json.loads(json.dumps(np.int32(7), cls=DateTimeEncoder))
        assert result == 7

    def test_numpy_float32_encoded(self):
        result = json.loads(json.dumps(np.float32(1.5), cls=DateTimeEncoder))
        assert abs(result - 1.5) < 0.01

    def test_unknown_type_raises_type_error(self):
        with pytest.raises(TypeError):
            json.dumps(object(), cls=DateTimeEncoder)

    def test_nested_numpy_in_dict(self):
        data = {"a": np.int64(1), "b": np.float64(2.5), "c": np.array([10, 20])}
        result = json.loads(json.dumps(data, cls=DateTimeEncoder))
        assert result["a"] == 1
        assert abs(result["b"] - 2.5) < 1e-6
        assert result["c"] == [10, 20]


# ===========================================================================
# _extract_property_info
# ===========================================================================

class TestExtractPropertyInfo:
    """Extraction of structured fields from a property record dict."""

    def _full_record(self, **overrides):
        record = {
            "PropertyHeader": {
                "Header": {"PropertyID": "PROP-aabbccdd"},
                "PropertyAttributes": {
                    "PropertyResi": "Semi-detached",
                    "ConstructionYear": 1998,
                    "PropertyCondition": "Good",
                },
                "Valuation": {"PropertyValue": 550000},
                "Location": {
                    "PostCode": "TW9 1AA",
                    "LatitudeDegrees": 51.45,
                    "LongitudeDegrees": -0.30,
                },
                "RiskAssessment": {"OverallFloodRisk": "Medium"},
            }
        }
        record.update(overrides)
        return record

    def test_property_id_extracted_from_header(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen._extract_property_info(self._full_record())["property_id"] == "PROP-aabbccdd"

    def test_property_value_extracted(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen._extract_property_info(self._full_record())["property_value"] == 550000

    def test_property_type_extracted(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen._extract_property_info(self._full_record())["property_type"] == "Semi-detached"

    def test_construction_year_extracted(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen._extract_property_info(self._full_record())["construction_year"] == 1998

    def test_flood_risk_extracted(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen._extract_property_info(self._full_record())["flood_risk"] == "Medium"

    def test_postcode_extracted(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen._extract_property_info(self._full_record())["postcode"] == "TW9 1AA"

    def test_lat_lon_extracted(self, tmp_path):
        gen = make_generator(tmp_path)
        info = gen._extract_property_info(self._full_record())
        assert abs(info["latitude"] - 51.45) < 0.001
        assert abs(info["longitude"] + 0.30) < 0.001

    def test_missing_header_defaults_property_id(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen._extract_property_info({"PropertyHeader": {}})["property_id"] == ""

    def test_missing_valuation_defaults_property_value(self, tmp_path):
        gen = make_generator(tmp_path)
        record = {"PropertyHeader": {"Header": {"PropertyID": "X"}}}
        assert gen._extract_property_info(record)["property_value"] == 500000

    def test_missing_risk_assessment_defaults_flood_risk(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen._extract_property_info({"PropertyHeader": {"Header": {}}})["flood_risk"] == "Low"

    def test_missing_property_header_returns_defaults(self, tmp_path):
        gen = make_generator(tmp_path)
        info = gen._extract_property_info({})
        assert info["property_id"] == ""
        assert info["property_value"] == 500000
        assert info["property_type"] == "Flat"

    def test_missing_attrs_default_construction_year(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen._extract_property_info({"PropertyHeader": {"Header": {}}})["construction_year"] == 1990

    def test_missing_location_defaults_to_catchment_centre(self, tmp_path):
        """Missing coords fall back to the active catchment centre, not a
        hardcoded London point."""
        from config.visual import get_map_center
        center_lat, center_lon = get_map_center()
        gen = make_generator(tmp_path)
        info = gen._extract_property_info({"PropertyHeader": {"Header": {}}})
        assert info["postcode"] == ""
        assert abs(info["latitude"] - center_lat) < 0.01
        assert abs(info["longitude"] - center_lon) < 0.01
