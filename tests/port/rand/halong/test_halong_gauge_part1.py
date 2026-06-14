# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage smoke tests for port.rand.halong.gauge.* (part 1)

The halong rand subpackage is largely a parallel copy of thames; these
tests exercise the halong-specific module bindings so the coverage tool
sees them as covered. They are NOT a substitute for the thames tests
that already verify behaviour — they're a regression net so changes to
halong specifically don't go silently uncovered.
"""

import random

import pytest


# ---------------------------------------------------------------------------
# Imports — exercise module-load paths
# ---------------------------------------------------------------------------

def test_import_gauge_subpackage():
    """The halong.gauge subpackage imports cleanly (covers __init__.py)."""
    from port.rand.halong import gauge as halong_gauge
    assert halong_gauge is not None


def test_import_gauge_random_module():
    from port.rand.halong.gauge import gauge_random
    assert hasattr(gauge_random, "generate_gauge_metadata")


def test_import_gaugets_random_module():
    from port.rand.halong.gauge import gaugets_random
    assert hasattr(gaugets_random, "generate_time_series")


def test_import_gauge_field_generators_module():
    from port.rand.halong.gauge import gauge_field_generators as gfg
    # Module-level constant list is populated
    assert isinstance(gfg.GAUGE_TYPES, list) and gfg.GAUGE_TYPES


# ---------------------------------------------------------------------------
# gauge_field_generators — exercise every field-name branch
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _seeded():
    """Seed the RNG so dispatched random.choice calls produce stable values."""
    random.seed(20260527)


class TestGenerateTextValue:
    @pytest.mark.parametrize("field", [
        "GaugeID", "GaugeOwner", "ManufacturerName",
        "DecisionBody", "DataCurator", "GaugeName",
    ])
    def test_known_field_returns_str(self, field, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_text_value
        v = generate_text_value(field, {}, 0, gauge_metadata)
        assert isinstance(v, str) and v

    def test_gauge_name_with_short_name(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_text_value
        v = generate_text_value("GaugeName", {}, 0, gauge_metadata)
        assert "Bai Chay" in v
        assert "Halong" in v

    def test_gauge_name_without_short_name_falls_back_to_area(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_text_value
        meta = dict(gauge_metadata)
        meta["location"] = dict(gauge_metadata["location"])
        meta["location"]["name"] = ""
        v = generate_text_value("GaugeName", {}, 3, meta)
        assert "Gauge 4" in v  # index+1
        assert "Halong" in v

    def test_unknown_field_returns_default_text(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_text_value
        v = generate_text_value("UnknownXyz", {}, 7, gauge_metadata)
        assert v == "Text-UnknownXyz-7"


class TestGenerateDecimalValue:
    @pytest.mark.parametrize("field,expected", [
        ("HistoricalHighLevel", 7.2),
        ("FloodAlert", 4.32),
        ("FloodWarning", 5.76),
        ("SevereFloodWarning", 6.84),
        # Flash / tsunami thresholds are fixed offsets above severe (6.84)
        ("FlashMinor", 9.84),
        ("FlashMajor", 11.84),
        ("TsunamiMinor", 11.84),
        ("TsunamiMajor", 16.84),
        ("GaugeLatitude", 20.95),
        ("GaugeLongitude", 107.05),
        ("elevation", 4.2),
        ("GroundLevelMeters", 4.2),
    ])
    def test_known_field(self, field, expected, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_decimal_value
        v = generate_decimal_value(field, {}, 0, gauge_metadata)
        assert v == expected

    def test_unknown_field_returns_float_in_range(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_decimal_value
        v = generate_decimal_value("Mystery", {}, 0, gauge_metadata)
        assert isinstance(v, float) and 0 <= v <= 10


class TestGenerateIntegerValue:
    def test_frequency_exceed_level3_in_range(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_integer_value
        for _ in range(20):
            v = generate_integer_value("FrequencyExceedLevel3", {}, 0, gauge_metadata)
            assert 0 <= v <= 10

    def test_unknown_field_returns_int_in_default_range(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_integer_value
        for _ in range(10):
            v = generate_integer_value("MysteryInt", {}, 0, gauge_metadata)
            assert 1 <= v <= 10


class TestGenerateDateValue:
    @pytest.mark.parametrize("field", [
        "HistoricalHighDate", "InstallationDate",
        "LastInspectionDate", "LastDateLevelExceedLevel3",
        "RandomEventDate",
    ])
    def test_returns_iso_date(self, field, gauge_metadata):
        from datetime import datetime
        from port.rand.halong.gauge.gauge_field_generators import generate_date_value
        s = generate_date_value(field, {}, 0, gauge_metadata)
        # Parseable as YYYY-MM-DD
        datetime.strptime(s, "%Y-%m-%d")


class TestGenerateMenuValue:
    @pytest.mark.parametrize("field", [
        "DataSourceType", "GaugeType", "MaintenanceSchedule",
        "OperationalStatus", "CertificationStatus",
        "MeasurementFrequency", "MeasurementMethod",
        "DataTransmission", "DataAccessMethod",
    ])
    def test_known_field_returns_str(self, field, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_menu_value
        v = generate_menu_value(field, {}, 0, gauge_metadata)
        assert isinstance(v, str) and v

    def test_tidal_branches(self, gauge_metadata):
        """TidalInfluence dispatches on longitude — exercise all three branches."""
        from port.rand.halong.gauge.gauge_field_generators import generate_menu_value
        for lon, expected_keyword in [(0.0, "Tidal"), (-0.3, "Partially"), (-0.5, "Non-tidal")]:
            meta = dict(gauge_metadata)
            meta["location"] = dict(gauge_metadata["location"])
            meta["location"]["lon"] = lon
            v = generate_menu_value("TidalInfluence", {}, 0, meta)
            assert expected_keyword in v

    def test_tidal_influence_missing_lon_returns_non_tidal(self, gauge_metadata):
        """No longitude in metadata → can't place along the span → Non-tidal."""
        from port.rand.halong.gauge.gauge_field_generators import generate_menu_value
        meta = dict(gauge_metadata)
        meta["location"] = dict(gauge_metadata["location"])
        meta["location"]["lon"] = None
        assert generate_menu_value("TidalInfluence", {}, 0, meta) == "Non-tidal"

    def test_tidal_influence_bounds_error_returns_non_tidal(self, gauge_metadata, monkeypatch):
        """If get_catchment_bounds() raises, fall back safely to Non-tidal."""
        from port.rand.halong.gauge import gauge_field_generators as gfg

        def _boom():
            raise RuntimeError("no catchment bounds available")

        monkeypatch.setattr(gfg, "get_catchment_bounds", _boom)
        assert gfg.generate_menu_value("TidalInfluence", {}, 0, gauge_metadata) == "Non-tidal"

    def test_unknown_field_with_options_picks_by_index(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_menu_value
        v = generate_menu_value("Unknown", {"options": ["a", "b", "c"]}, 4, gauge_metadata)
        assert v == "b"  # 4 % 3 = 1

    def test_unknown_field_no_options_returns_empty(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_menu_value
        v = generate_menu_value("Unknown", {}, 0, gauge_metadata)
        assert v == ""
