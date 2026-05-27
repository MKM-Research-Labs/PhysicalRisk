# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.winddamage.threshold — WindThresholdKph → v_50 (m/s)."""

import pytest

from config.damage import DEFAULT_WIND_THRESHOLD_KPH
from models.winddamage.threshold import KMH_TO_MS, kph_to_ms, resolve_threshold_ms


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
