# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
    """Binary damage-onset wind trigger: peak_sustained_ms >= threshold_ms."""

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
