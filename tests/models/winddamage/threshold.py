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

"""Tests for models.winddamage.threshold — WindThresholdKph → v_50 (m/s)."""

import pytest

from config.damage import DEFAULT_WIND_THRESHOLD_KPH
from models.winddamage.threshold import (
    KMH_TO_MS,
    is_prs_wind,
    kph_to_ms,
    resolve_threshold_ms,
)


def _record(**overrides):
    base = {
        "PropertyHeader": {"Header": {"PropertyID": "PROP-test"}},
        "ProtectionMeasures": {
            "HazardProfile": {"WindThresholdKph": 120.0},
        },
    }
    base.update(overrides)
    return base


class TestKphToMs:

    def test_kmh_to_ms_factor(self):
        assert KMH_TO_MS == pytest.approx(1.0 / 3.6, abs=1e-12)

    def test_100_kph_is_27_78_ms(self):
        # 100 kph = 27.7777... m/s
        assert kph_to_ms(100.0) == pytest.approx(100.0 / 3.6, abs=1e-9)

    def test_zero_kph(self):
        assert kph_to_ms(0.0) == 0.0


class TestResolveThresholdMs:

    def test_uses_cdm_field_when_present(self):
        v_50 = resolve_threshold_ms(_record())
        assert v_50 == pytest.approx(120.0 / 3.6, abs=1e-9)

    def test_falls_back_to_default_when_missing(self):
        rec = _record()
        rec["ProtectionMeasures"]["HazardProfile"].pop("WindThresholdKph")
        v_50 = resolve_threshold_ms(rec)
        assert v_50 == pytest.approx(DEFAULT_WIND_THRESHOLD_KPH / 3.6, abs=1e-9)

    def test_falls_back_when_field_value_invalid(self):
        rec = _record()
        rec["ProtectionMeasures"]["HazardProfile"]["WindThresholdKph"] = "nope"
        v_50 = resolve_threshold_ms(rec)
        assert v_50 == pytest.approx(DEFAULT_WIND_THRESHOLD_KPH / 3.6, abs=1e-9)

    def test_empty_record_uses_default(self):
        v_50 = resolve_threshold_ms({})
        assert v_50 == pytest.approx(DEFAULT_WIND_THRESHOLD_KPH / 3.6, abs=1e-9)

    def test_returns_float_in_meters_per_second(self):
        v_50 = resolve_threshold_ms(_record())
        # 120 kph -> 33.33 m/s; type must be float, units must be reasonable.
        assert isinstance(v_50, float)
        assert 25.0 < v_50 < 45.0


class TestIsPrsWind:
    """Binary damage-onset wind trigger: peak_sustained_ms >= v_50_eff_ms.

    The BRI-adjusted ``v_50_eff_ms`` is the preferred exceedance level; the
    raw ``threshold_ms`` is only used as a fallback for legacy damage rows
    written before ``v_50_eff_ms`` existed.
    """

    def test_peak_above_threshold_triggers(self):
        assert is_prs_wind({"peak_sustained_ms": 55.0, "threshold_ms": 30.0}) is True

    def test_peak_equal_threshold_triggers(self):
        # Boundary is inclusive (>=).
        assert is_prs_wind({"peak_sustained_ms": 30.0, "threshold_ms": 30.0}) is True

    def test_peak_below_threshold_does_not_trigger(self):
        assert is_prs_wind({"peak_sustained_ms": 20.0, "threshold_ms": 30.0}) is False

    def test_high_bri_threshold_suppresses_trigger(self):
        # Same wind, resilient building (higher BRI-adjusted threshold) -> no fire;
        # low-BRI building (lower threshold) -> fires. Encodes the user's point.
        wind = 45.0
        assert is_prs_wind({"peak_sustained_ms": wind, "threshold_ms": 60.0}) is False
        assert is_prs_wind({"peak_sustained_ms": wind, "threshold_ms": 35.0}) is True

    def test_missing_peak_returns_false(self):
        assert is_prs_wind({"threshold_ms": 30.0}) is False

    def test_missing_threshold_returns_false(self):
        assert is_prs_wind({"peak_sustained_ms": 55.0}) is False

    def test_empty_row_returns_false(self):
        assert is_prs_wind({}) is False

    def test_non_numeric_values_return_false(self):
        assert is_prs_wind({"peak_sustained_ms": "fast", "threshold_ms": 30.0}) is False

    # --- v_50_eff_ms (BRI-adjusted) is the preferred exceedance level ---

    def test_v50_eff_is_preferred_over_raw_threshold(self):
        # Resilient building: raw threshold would fire, but the higher
        # BRI-adjusted v_50_eff suppresses it. The effective level wins.
        row = {"peak_sustained_ms": 32.0, "threshold_ms": 30.0, "v_50_eff_ms": 40.0}
        assert is_prs_wind(row) is False

    def test_v50_eff_fires_when_raw_threshold_would_not(self):
        # Vulnerable building: BRI shifts the curve left (lower v_50_eff),
        # so a wind below the raw threshold still triggers.
        row = {"peak_sustained_ms": 25.0, "threshold_ms": 30.0, "v_50_eff_ms": 20.0}
        assert is_prs_wind(row) is True

    def test_v50_eff_boundary_is_inclusive(self):
        row = {"peak_sustained_ms": 22.7, "threshold_ms": 27.78, "v_50_eff_ms": 22.7}
        assert is_prs_wind(row) is True

    def test_falls_back_to_threshold_when_v50_eff_absent(self):
        # Legacy rows without v_50_eff_ms keep working off threshold_ms.
        assert is_prs_wind({"peak_sustained_ms": 35.0, "threshold_ms": 30.0}) is True
        assert is_prs_wind({"peak_sustained_ms": 25.0, "threshold_ms": 30.0}) is False

    def test_non_numeric_v50_eff_returns_false(self):
        row = {"peak_sustained_ms": 55.0, "v_50_eff_ms": "fast", "threshold_ms": 30.0}
        assert is_prs_wind(row) is False
