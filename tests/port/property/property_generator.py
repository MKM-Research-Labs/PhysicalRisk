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

"""
Unit tests for PropertyPortfolioGenerator end-to-end.
"""

import json
import re

import pytest

from port.src.property import PropertyPortfolioGenerator


@pytest.mark.generator
class TestPropertyGeneratorOutput:

    def test_generate_returns_expected_keys(self, tmp_path):
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        assert "data" in result
        assert "file_path" in result
        assert "processing_stats" in result

    def test_generate_correct_count(self, tmp_path):
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        assert len(result["data"]["properties"]) == 5

    def test_property_ids_unique(self, tmp_path):
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=10)
        ids = result["data"]["property_ids"]
        assert len(ids) == len(set(ids))

    def test_property_id_format(self, tmp_path):
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        for pid in result["data"]["property_ids"]:
            assert re.match(r"^PROP-[a-f0-9]{8}$", pid)


@pytest.mark.generator
class TestPropertyGeneratorFile:

    def test_output_file_exists(self, tmp_path):
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        assert result["file_path"].exists()

    def test_output_file_is_valid_json(self, tmp_path):
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        with open(result["file_path"]) as f:
            data = json.load(f)
        assert isinstance(data, dict)


@pytest.mark.generator
class TestPropertyGeneratorDataQuality:

    def test_coordinates_in_thames_range(self, tmp_path):
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=10)
        for loc in result["data"]["locations"]:
            assert 51.0 <= loc["lat"] <= 52.0
            assert -1.0 <= loc["lon"] <= 1.0

    def test_processing_stats(self, tmp_path):
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen.generate(count=5)
        stats = result["processing_stats"]
        assert stats["successful_properties"] == 5
        assert stats["failed_properties"] == 0


# ===========================================================================
# property_utils — generate_past_date, generate_owner_name, generate_grid_reference
# ===========================================================================

class TestPropertyUtils:
    """Tests for uncovered utility functions in property_utils.py."""

    def test_generate_past_date_format(self):
        """Lines 43-45: generate_past_date returns YYYY-MM-DD string."""
        from port.rand.thames.property.property_utils import generate_past_date
        result = generate_past_date()
        assert isinstance(result, str)
        parts = result.split("-")
        assert len(parts) == 3  # YYYY-MM-DD

    def test_generate_past_date_range(self):
        """Custom days_range is respected (result is a past date)."""
        from port.rand.thames.property.property_utils import generate_past_date
        from datetime import datetime, timedelta
        result = generate_past_date(days_range=(10, 20))
        dt = datetime.strptime(result, "%Y-%m-%d")
        assert dt < datetime.now()

    def test_generate_owner_name_two_words(self):
        """Lines 50-52: generate_owner_name returns 'Firstname Lastname'."""
        from port.rand.thames.property.property_utils import generate_owner_name
        name = generate_owner_name()
        parts = name.split(" ")
        assert len(parts) == 2
        assert all(p[0].isupper() for p in parts)

    def test_generate_grid_reference_format(self):
        """Lines 73-75: generate_grid_reference returns a non-empty string."""
        from port.rand.thames.property.property_utils import generate_grid_reference
        ref = generate_grid_reference(51.5, -0.1)
        assert isinstance(ref, str)
        assert len(ref) > 4


# ===========================================================================
# DateTimeEncoder — numpy type handling (lines 60-68)
# ===========================================================================

class TestDateTimeEncoder:

    def test_datetime_to_isoformat(self):
        """Line 60-61: datetime → isoformat string."""
        import json
        from datetime import datetime
        from port.src.property.main import DateTimeEncoder
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = json.dumps(dt, cls=DateTimeEncoder)
        assert "2024-01-01" in result

    def test_numpy_integer(self):
        """Lines 62-63: np.integer → int."""
        import json
        import numpy as np
        from port.src.property.main import DateTimeEncoder
        result = json.dumps(np.int64(42), cls=DateTimeEncoder)
        assert result == "42"

    def test_numpy_floating(self):
        """Lines 64-65: np.floating → float."""
        import json
        import numpy as np
        from port.src.property.main import DateTimeEncoder
        result = json.dumps(np.float64(3.14), cls=DateTimeEncoder)
        assert "3.14" in result

    def test_numpy_ndarray(self):
        """Lines 66-67: np.ndarray → list."""
        import json
        import numpy as np
        from port.src.property.main import DateTimeEncoder
        result = json.loads(json.dumps(np.array([1, 2, 3]), cls=DateTimeEncoder))
        assert result == [1, 2, 3]

    def test_unknown_type_raises(self):
        """Line 68: super().default() raises TypeError for unknown type."""
        import json
        from port.src.property.main import DateTimeEncoder
        with pytest.raises(TypeError):
            json.dumps(object(), cls=DateTimeEncoder)


# ===========================================================================
# _generate_locations_fallback (lines 499-518)
# ===========================================================================

class TestGenerateLocationsFallback:

    def _make_minimal_params(self, tmp_path, has_gauge_points=True):
        """Build a minimal params object (no GAUGE_POINTS or < 3 points)."""
        from unittest.mock import MagicMock
        params = MagicMock()
        params.AREAS = ["Chelsea", "Fulham"]
        params.AREA_VALUE_FACTORS = {"Chelsea": 1.2, "Fulham": 1.0}
        params.STREETS = {}
        params.CENTER_LAT = 51.5
        params.CENTER_LON = -0.1
        if has_gauge_points:
            params.GAUGE_POINTS = None  # forces fallback
        else:
            del params.GAUGE_POINTS  # GAUGEPOINTS also absent
        params.GAUGEPOINTS = None
        params.get_elevation = MagicMock(return_value=5.0)
        return params

    def test_fallback_returns_correct_count(self, tmp_path):
        """Lines 499-518: fallback generates right number of locations."""
        from port.src.property.main import PropertyPortfolioGenerator
        params = self._make_minimal_params(tmp_path)
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False,
                                          catchment_params=params)
        locs = gen._generate_locations_fallback(5, params.AREAS,
                                                 params.AREA_VALUE_FACTORS, {})
        assert len(locs) == 5

    def test_fallback_location_has_required_keys(self, tmp_path):
        """Lines 510-517: each fallback location has lat/lon/name/elevation."""
        from port.src.property.main import PropertyPortfolioGenerator
        params = self._make_minimal_params(tmp_path)
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False,
                                          catchment_params=params)
        locs = gen._generate_locations_fallback(3, params.AREAS,
                                                 params.AREA_VALUE_FACTORS, {})
        for loc in locs:
            assert "lat" in loc
            assert "lon" in loc
            assert "name" in loc
            assert "elevation" in loc

    def test_fallback_with_get_elevation(self, tmp_path):
        """Lines 505-506: uses params.get_elevation if available."""
        from unittest.mock import MagicMock
        from port.src.property.main import PropertyPortfolioGenerator
        params = MagicMock()
        params.AREAS = ["Area1"]
        params.AREA_VALUE_FACTORS = {}
        params.STREETS = {}
        params.CENTER_LAT = 51.5
        params.CENTER_LON = -0.1
        params.GAUGE_POINTS = None
        params.GAUGEPOINTS = None
        params.get_elevation = MagicMock(return_value=10.0)
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False,
                                          catchment_params=params)
        locs = gen._generate_locations_fallback(2, params.AREAS, {}, {})
        assert all(loc["elevation"] == 10.0 for loc in locs)


# ===========================================================================
# generate_properties convenience function (lines 608-612)
# ===========================================================================

class TestGeneratePropertiesFunction:

    def test_generate_properties_basic(self, tmp_path):
        """Lines 608-612: generate_properties returns result dict."""
        from port.src.property.main import generate_properties
        result = generate_properties(count=3, output_dir=tmp_path)
        assert isinstance(result, dict)
        assert "data" in result
        assert len(result["data"]["properties"]) == 3

    def test_generate_properties_output_file_created(self, tmp_path):
        """Lines 610-612: generate_properties creates output file."""
        from port.src.property.main import generate_properties
        result = generate_properties(count=2, output_dir=tmp_path)
        assert result["file_path"].exists()


# ===========================================================================
# _build_section edge cases (lines 540-552)
# ===========================================================================

class TestBuildSection:

    def test_non_dict_schema_returns_empty(self, tmp_path):
        """Line 541: non-dict schema → returns {}."""
        from port.src.property.main import PropertyPortfolioGenerator
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        result = gen._build_section("not_a_dict", 0, {})
        assert result == {}

    def test_skips_type_field(self, tmp_path):
        """Line 544-545: 'type'/'options'/'description' fields are skipped."""
        from port.src.property.main import PropertyPortfolioGenerator
        gen = PropertyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        schema = {"type": "string", "options": ["a", "b"]}
        result = gen._build_section(schema, 0, {})
        assert "type" not in result
        assert "options" not in result
