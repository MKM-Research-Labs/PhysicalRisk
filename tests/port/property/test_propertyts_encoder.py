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
Tests for DateTimeEncoder, _depth_to_damage, and _process_property early exits.
"""

import json
from datetime import datetime

import numpy as np
import pytest

from .conftest import make_prop, make_gauge_lookup, make_generator


# ===========================================================================
# DateTimeEncoder — numpy type branches (lines 59-67)
# ===========================================================================

class TestDateTimeEncoderPropertyts:

    def test_datetime_encoding(self):
        """Line 59-60: datetime -> isoformat."""
        from port.src.property.propertyts import DateTimeEncoder
        result = json.dumps(datetime(2024, 6, 1), cls=DateTimeEncoder)
        assert "2024-06-01" in result

    def test_numpy_integer(self):
        """Line 61-62: np.integer -> int."""
        from port.src.property.propertyts import DateTimeEncoder
        result = json.dumps(np.int64(99), cls=DateTimeEncoder)
        assert result == "99"

    def test_numpy_floating(self):
        """Line 63-64: np.floating -> float."""
        from port.src.property.propertyts import DateTimeEncoder
        result = json.dumps(np.float64(2.71), cls=DateTimeEncoder)
        assert "2.71" in result

    def test_numpy_ndarray(self):
        """Line 65-66: np.ndarray -> list."""
        from port.src.property.propertyts import DateTimeEncoder
        result = json.loads(json.dumps(np.array([10, 20]), cls=DateTimeEncoder))
        assert result == [10, 20]

    def test_unknown_raises(self):
        """Line 67: super().default() -> TypeError for unknown."""
        from port.src.property.propertyts import DateTimeEncoder
        with pytest.raises(TypeError):
            json.dumps(object(), cls=DateTimeEncoder)


# ===========================================================================
# _depth_to_damage static method (line 502)
# ===========================================================================

class TestDepthToDamage:

    def test_zero_depth_returns_zero(self, tmp_path):
        """0m depth -> 0 damage."""
        gen = make_generator(tmp_path)
        assert gen._depth_to_damage(0.0) == 0.0

    def test_positive_depth_returns_positive(self, tmp_path):
        """Positive depth -> positive damage ratio."""
        gen = make_generator(tmp_path)
        result = gen._depth_to_damage(1.0)
        assert 0.0 < result <= 1.0

    def test_deep_flood_near_max_damage(self, tmp_path):
        """Deep flood -> damage ratio approaches 1."""
        gen = make_generator(tmp_path)
        result = gen._depth_to_damage(3.0)
        assert result > 0.5


# ===========================================================================
# _process_property — early exits (lines 282-288)
# ===========================================================================

class TestProcessPropertyEarlyExits:

    def test_missing_prop_id_returns_none(self, tmp_path):
        """Line 283: empty prop_id -> None."""
        gen = make_generator(tmp_path)
        prop = make_prop(prop_id="")
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        result = gen._process_property(prop, make_gauge_lookup(), {}, pts_dir)
        assert result is None

    def test_zero_lat_returns_none(self, tmp_path):
        """Line 283: prop_lat == 0 -> None."""
        gen = make_generator(tmp_path)
        prop = make_prop(lat=0)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        result = gen._process_property(prop, make_gauge_lookup(), {}, pts_dir)
        assert result is None

    def test_empty_gauge_lookup_returns_none(self, tmp_path):
        """Line 288: empty gauge_lookup -> no nearest -> None."""
        gen = make_generator(tmp_path)
        pts_dir = tmp_path / "propertyts"
        pts_dir.mkdir()
        result = gen._process_property(make_prop(), {}, {}, pts_dir)
        assert result is None
