# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage smoke tests for port.rand.halong.gauge.*

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

    def test_unknown_field_with_options_picks_by_index(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_menu_value
        v = generate_menu_value("Unknown", {"options": ["a", "b", "c"]}, 4, gauge_metadata)
        assert v == "b"  # 4 % 3 = 1

    def test_unknown_field_no_options_returns_empty(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_field_generators import generate_menu_value
        v = generate_menu_value("Unknown", {}, 0, gauge_metadata)
        assert v == ""


# ---------------------------------------------------------------------------
# gauge_random — generate_gauge_metadata + generate_field_value dispatch
# ---------------------------------------------------------------------------

class TestGenerateGaugeMetadata:
    def test_generates_complete_metadata(self):
        from port.rand.halong.gauge.gauge_random import generate_gauge_metadata
        loc = {"lat": 20.95, "lon": 107.05, "elevation": 4.2, "name": "Bai Chay"}
        meta = generate_gauge_metadata(0, loc, catchment_name="Halong")
        # ID is deterministic for fixed location
        assert meta["gauge_id"].startswith("GAUGE-")
        assert meta["catchment_name"] == "Halong"
        # Levels respect ordering
        assert meta["flood_alert"] < meta["flood_warning"] < meta["severe_flood_warning"]
        assert meta["historical_high_level"] > 0
        # ID is stable for the same location/index
        meta2 = generate_gauge_metadata(0, loc, catchment_name="Halong")
        assert meta["gauge_id"] == meta2["gauge_id"]


class TestGenerateFloodRiskAssessment:
    """generate_flood_risk_assessment: risk dispatch on distance_to_thames threshold."""

    def test_close_to_thames_returns_high_risk(self):
        from port.rand.halong.gauge.gauge_random import generate_flood_risk_assessment
        loc = {"distance_to_thames": 10}
        result = generate_flood_risk_assessment(loc, distance_threshold=100)
        assert 7 <= result["FloodRiskScore"] <= 10
        assert result["FloodRiskCategory"] in {"High", "Very High"}
        assert "LastAssessmentDate" in result

    def test_far_from_thames_returns_low_risk(self):
        from port.rand.halong.gauge.gauge_random import generate_flood_risk_assessment
        loc = {"distance_to_thames": 500}
        result = generate_flood_risk_assessment(loc, distance_threshold=100)
        assert 2 <= result["FloodRiskScore"] <= 6
        assert result["FloodRiskCategory"] in {"Low", "Medium"}


class TestGenerateFieldValueDispatch:
    """generate_field_value dispatches on field_def['type']."""

    @pytest.mark.parametrize("ftype,field,validate", [
        ("text", "GaugeOwner", lambda v: isinstance(v, str) and v),
        ("decimal", "FloodAlert", lambda v: isinstance(v, float)),
        ("integer", "FrequencyExceedLevel3", lambda v: isinstance(v, int)),
        ("date", "InstallationDate", lambda v: isinstance(v, str) and "-" in v),
        ("menu", "GaugeType", lambda v: isinstance(v, str)),
    ])
    def test_dispatch_by_type(self, ftype, field, validate, gauge_metadata):
        from port.rand.halong.gauge.gauge_random import generate_field_value
        v = generate_field_value(field, {"type": ftype}, 0, gauge_metadata)
        assert validate(v), f"{ftype} dispatch returned {v!r}"

    def test_non_dict_field_def_returns_string(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_random import generate_field_value
        assert generate_field_value("X", "literal", 0, gauge_metadata) == "literal"
        assert generate_field_value("X", 42, 0, gauge_metadata) == ""

    def test_unknown_type_returns_empty(self, gauge_metadata):
        from port.rand.halong.gauge.gauge_random import generate_field_value
        assert generate_field_value("X", {"type": "mystery_type"}, 0, gauge_metadata) == ""


# ---------------------------------------------------------------------------
# gaugets_random — exercise time-series generation
# ---------------------------------------------------------------------------

class TestGaugetsRandom:
    """gaugets_random simulates a per-hour flood-wave reading for each gauge."""

    def test_calculate_water_level_returns_float(self):
        from port.rand.halong.gauge.gaugets_random import calculate_water_level
        # signature: (hour, gauge_index, base_level, params=None)
        v = calculate_water_level(hour=12, gauge_index=0, base_level=3.0)
        assert isinstance(v, float)
        assert v >= 0

    @pytest.mark.parametrize("hour", [0, 24, 48, 72, 168])
    def test_calculate_water_level_phases(self, hour):
        """All three flood-wave phases (rise / peak / recession) covered."""
        from port.rand.halong.gauge.gaugets_random import calculate_water_level
        v = calculate_water_level(hour=hour, gauge_index=0, base_level=3.0,
                                  params={"peak_hour_base": 36, "simulation_hours": 168,
                                          "base_amplitude": 0.5, "peak_amplitude": 2.0,
                                          "peak_hour_stagger": 2})
        assert isinstance(v, float)

    def test_determine_alert_status_thresholds(self):
        from port.rand.halong.gauge.gaugets_random import determine_alert_status
        # signature: (water_level, alert, warning, severe)
        assert determine_alert_status(2.0, 3.0, 4.0, 5.0) == "Normal"
        assert determine_alert_status(3.5, 3.0, 4.0, 5.0) == "Flood Alert"
        assert determine_alert_status(4.5, 3.0, 4.0, 5.0) == "Flood Warning"
        assert determine_alert_status(5.5, 3.0, 4.0, 5.0) == "Severe Flood Warning"

    def test_generate_gauge_reading_shape(self):
        from datetime import datetime
        from port.rand.halong.gauge.gaugets_random import generate_gauge_reading
        gauge = {
            "FloodGauge": {
                "Header": {"GaugeID": "GAUGE-h001"},
                "FloodStages": {"FloodAlert": 3.0, "FloodWarning": 4.0,
                                "SevereFloodWarning": 5.0},
            }
        }
        # signature: (hour, gauge_index, gauge_data, timestamp, params=None)
        reading = generate_gauge_reading(12, 0, gauge, datetime(2026, 1, 1, 12, 0))
        assert reading["gaugeId"] == "GAUGE-h001"
        assert "waterLevel" in reading
        assert reading["alertStatus"] in {
            "Normal", "Flood Alert", "Flood Warning", "Severe Flood Warning",
        }

    def test_generate_timestep_readings_handles_errors(self):
        from datetime import datetime
        from port.rand.halong.gauge.gaugets_random import generate_timestep_readings
        # One valid gauge and one malformed → covers the except branch
        gauges = [
            {"FloodGauge": {"Header": {"GaugeID": "G1"},
                            "FloodStages": {"FloodAlert": 3, "FloodWarning": 4,
                                            "SevereFloodWarning": 5}}},
            None,  # triggers exception in inner loop
        ]
        result = generate_timestep_readings(0, gauges, datetime(2026, 1, 1))
        assert "readings" in result

    def test_generate_time_series_alias(self):
        from port.rand.halong.gauge.gaugets_random import generate_time_series
        gauges = [
            {"FloodGauge": {"Header": {"GaugeID": "G1"},
                            "FloodStages": {"FloodAlert": 3, "FloodWarning": 4,
                                            "SevereFloodWarning": 5}}},
        ]
        # generate_time_series is an alias for generate_flood_simulation;
        # constrain hours to keep the test snappy.
        result = generate_time_series(gauges, params={
            "peak_hour_base": 4, "peak_hour_stagger": 1,
            "simulation_hours": 8, "base_amplitude": 0.5, "peak_amplitude": 2.0,
        })
        assert isinstance(result, list) and len(result) >= 1

    def test_generate_flood_simulation_uses_defaults(self):
        from port.rand.halong.gauge.gaugets_random import generate_flood_simulation
        gauges = [
            {"FloodGauge": {"Header": {"GaugeID": "G1"},
                            "FloodStages": {"FloodAlert": 3, "FloodWarning": 4,
                                            "SevereFloodWarning": 5}}},
        ]
        # Force start_time str path
        result = generate_flood_simulation(gauges, params={
            "peak_hour_base": 4, "peak_hour_stagger": 1,
            "simulation_hours": 6, "base_amplitude": 0.5, "peak_amplitude": 2.0,
            "simulation_start_date": "2026-01-01T00:00:00",
        })
        assert len(result) >= 1
