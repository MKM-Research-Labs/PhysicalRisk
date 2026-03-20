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
  - _map_threshold_to_gauge_trigger
  - _get_gauge_prs_spreads
  - _load_gauge_hazard_curves
  - _get_prs_pricer
  - _json_default
"""

from datetime import datetime
from unittest.mock import patch

import numpy as np
import pytest

from port.src.property.propertyhc import (
    TENORS,
    PropertyHazardCurveGenerator,
)

from .conftest import write_gauge_hc


# ===========================================================================
# _map_threshold_to_gauge_trigger
# ===========================================================================

class TestMapThresholdToGaugeTrigger:

    def test_any_flood_maps_to_alert(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        assert gen._map_threshold_to_gauge_trigger("any_flood") == "alert"

    def test_moderate_maps_to_warning(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        assert gen._map_threshold_to_gauge_trigger("moderate") == "warning"

    def test_severe_maps_to_severe(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        assert gen._map_threshold_to_gauge_trigger("severe") == "severe"

    def test_unknown_key_returns_warning(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        assert gen._map_threshold_to_gauge_trigger("nonexistent") == "warning"


# ===========================================================================
# _get_gauge_prs_spreads
# ===========================================================================

class TestGetGaugePrsSpreads:

    def test_zero_rate_returns_all_zeros(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gauge_hc = {"annual_hazard_rate_alert": 0.0}
        result = gen._get_gauge_prs_spreads(gauge_hc, "alert", price_prs_func=None)
        assert result == [0.0] * len(TENORS)

    def test_negative_rate_returns_all_zeros(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gauge_hc = {"annual_hazard_rate_alert": -0.01}
        result = gen._get_gauge_prs_spreads(gauge_hc, "alert", price_prs_func=None)
        assert result == [0.0] * len(TENORS)

    def test_positive_rate_returns_positive_spreads(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gauge_hc = {"annual_hazard_rate_warning": 0.02}
        result = gen._get_gauge_prs_spreads(gauge_hc, "warning", price_prs_func=None)
        assert len(result) == len(TENORS)
        assert all(s > 0 for s in result)

    def test_missing_key_defaults_to_zero_rate(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gauge_hc = {}  # key not present, defaults to 0
        result = gen._get_gauge_prs_spreads(gauge_hc, "alert", price_prs_func=None)
        assert result == [0.0] * len(TENORS)

    def test_spread_list_has_one_entry_per_tenor(self, tmp_path):
        gen = PropertyHazardCurveGenerator(tmp_path, verbose=False)
        gauge_hc = {"annual_hazard_rate_severe": 0.01}
        result = gen._get_gauge_prs_spreads(gauge_hc, "severe", price_prs_func=None)
        assert len(result) == len(TENORS)


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
