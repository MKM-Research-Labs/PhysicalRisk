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
Tests for PropertyHazardCurveGenerator helper methods:
  - _get_gauge_severe_count
  - _load_gauge_hazard_curves
  - _get_prs_pricer
  - _json_default
"""

from datetime import datetime
from unittest.mock import patch

import numpy as np
import pytest

from port.src.property.propertyhc import (
    PropertyHazardCurveGenerator,
)

from .conftest import write_gauge_hc


# ===========================================================================
# _get_gauge_severe_count
# ===========================================================================

class TestGetGaugeSevereCount:

    def test_returns_severe_event_count(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gauge_hc = {"severe_event_count": 7}
        assert gen._get_gauge_severe_count(gauge_hc) == 7

    def test_missing_key_defaults_to_zero(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gauge_hc = {}
        assert gen._get_gauge_severe_count(gauge_hc) == 0

    def test_zero_count_returns_zero(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gauge_hc = {"severe_event_count": 0}
        assert gen._get_gauge_severe_count(gauge_hc) == 0

    def test_large_count_returned(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gauge_hc = {"severe_event_count": 150}
        assert gen._get_gauge_severe_count(gauge_hc) == 150

    def test_ignores_other_keys(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gauge_hc = {"annual_hazard_rate_alert": 0.05, "severe_event_count": 3}
        assert gen._get_gauge_severe_count(gauge_hc) == 3


# ===========================================================================
# _load_gauge_hazard_curves
# ===========================================================================

class TestLoadGaugeHazardCurves:

    def test_missing_gaugehc_returns_empty_and_default_storms(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        curves, n_storms = gen._load_gauge_hazard_curves()
        assert curves == {}
        assert n_storms == 1000

    def test_present_gaugehc_returns_curves(self, tmp_path):
        write_gauge_hc(tmp_path, num_storms=500)
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        curves, n_storms = gen._load_gauge_hazard_curves()
        assert "GAUGE-001" in curves
        assert n_storms == 500

    def test_present_gaugehc_returns_num_storms(self, tmp_path):
        write_gauge_hc(tmp_path, num_storms=250)
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        _, n_storms = gen._load_gauge_hazard_curves()
        assert n_storms == 250


# ===========================================================================
# _get_prs_pricer
# ===========================================================================

class TestGetPrsPricer:

    def test_returns_none_when_quantlib_unavailable(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        with patch.dict("sys.modules", {"models.prs.prshc": None}):
            with patch("builtins.__import__", side_effect=ImportError):
                result = gen._get_prs_pricer()
        assert result is None


# ===========================================================================
# _json_default
# ===========================================================================

class TestJsonDefault:

    def test_numpy_int_encoded(self):
        result = PropertyHazardCurveGenerator._json_default(np.int64(42))
        assert result == 42
        assert isinstance(result, int)

    def test_numpy_float_encoded(self):
        result = PropertyHazardCurveGenerator._json_default(np.float64(3.14))
        assert abs(result - 3.14) < 1e-6

    def test_numpy_ndarray_encoded_as_list(self):
        result = PropertyHazardCurveGenerator._json_default(np.array([1, 2, 3]))
        assert result == [1, 2, 3]

    def test_datetime_encoded_as_isoformat(self):
        dt = datetime(2024, 1, 15)
        result = PropertyHazardCurveGenerator._json_default(dt)
        assert "2024-01-15" in result

    def test_unknown_type_raises_type_error(self):
        with pytest.raises(TypeError):
            PropertyHazardCurveGenerator._json_default(object())

    def test_numpy_int32_encoded(self):
        result = PropertyHazardCurveGenerator._json_default(np.int32(7))
        assert result == 7

    def test_numpy_float32_encoded(self):
        result = PropertyHazardCurveGenerator._json_default(np.float32(1.5))
        assert abs(result - 1.5) < 0.01
