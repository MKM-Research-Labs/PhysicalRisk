# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.winddamage.event — per-event composer."""

import json

import pytest

from config.damage import DEFAULT_WIND_THRESHOLD_KPH
from models.winddamage.event import (
    build_event_damage,
    run_event,
    run_event_directory,
)
from models.winddamage.extraction import EventWindts


# -- Fixtures (synthetic, no I/O dependence) --------------------------------


def _property(prop_id: str, *, threshold_kph=None, bri_wind=None, bri_composite=None):
    """Build a minimum property record with the fields the model needs."""
    record = {
        "PropertyHeader": {"Header": {"PropertyID": prop_id}},
        "ProtectionMeasures": {
            "HazardProfile": {},
            "RiskAssessment": {"GoverningBodyRatings": {}},
        },
    }
    if threshold_kph is not None:
        record["ProtectionMeasures"]["HazardProfile"]["WindThresholdKph"] = threshold_kph
    ratings = record["ProtectionMeasures"]["RiskAssessment"]["GoverningBodyRatings"]
    if bri_wind is not None:
        ratings["BRIWindScore"] = bri_wind
    if bri_composite is not None:
        ratings["BRIScore"] = bri_composite
    return record


def _windts(peaks_by_property, **kwargs):
    return EventWindts(
        event_id=kwargs.get("event_id", "EVT-0001"),
        scenario_family=kwargs.get("scenario_family", "moderate"),
        horizon_hours=kwargs.get("horizon_hours", 168.0),
        dt_hours=kwargs.get("dt_hours", 1.0),
        peaks_by_property=peaks_by_property,
    )


def _windts_series(peaks_by_property, series_by_property, **kwargs):
    """A windts summary that also carries per-property sustained-wind series."""
    return EventWindts(
        event_id=kwargs.get("event_id", "EVT-0001"),
        scenario_family=kwargs.get("scenario_family", "moderate"),
        horizon_hours=kwargs.get("horizon_hours", 168.0),
        dt_hours=kwargs.get("dt_hours", 1.0),
        peaks_by_property=peaks_by_property,
        series_by_property=series_by_property,
    )


def _flat_series(peak, hours):
    """A series holding `peak` for `hours` whole hours (sustained plateau)."""
    times = [float(h) for h in range(hours + 1)]
    sustained = [float(peak)] * (hours + 1)
    return times, sustained


# -- build_event_damage in memory -------------------------------------------


class TestBuildEventDamage:

    def test_one_property_one_event(self):
        windts = _windts({"PROP-a": 35.0})
        props = [_property("PROP-a", threshold_kph=100.0)]
        payload = build_event_damage(windts, props)
        assert payload["event_id"] == "EVT-0001"
        assert payload["scenario_family"] == "moderate"
        assert len(payload["damages"]) == 1
        d = payload["damages"][0]
        assert d["property_id"] == "PROP-a"
        assert d["peak_sustained_ms"] == 35.0
        # threshold_ms = 100 / 3.6 ~ 27.78
        assert 27.5 < d["threshold_ms"] < 28.0
        # No BRI scores -> v_50_eff = threshold_ms
        assert d["v_50_eff_ms"] == d["threshold_ms"]
        assert 0.0 <= d["damage_ratio"] <= 1.0

    def test_property_not_in_windts_omitted(self):
        windts = _windts({"PROP-a": 35.0})
        props = [
            _property("PROP-a", threshold_kph=100.0),
            _property("PROP-b", threshold_kph=100.0),   # not in this event
        ]
        payload = build_event_damage(windts, props)
        ids = [d["property_id"] for d in payload["damages"]]
        assert ids == ["PROP-a"]

    def test_missing_threshold_uses_default(self):
        windts = _windts({"PROP-a": 35.0})
        props = [_property("PROP-a")]   # no threshold field
        payload = build_event_damage(windts, props)
        d = payload["damages"][0]
        assert d["threshold_ms"] == DEFAULT_WIND_THRESHOLD_KPH / 3.6

    def test_bri_scores_shift_v50(self):
        # Hardened property — high BRI scores — should see a v_50_eff
        # above the raw threshold.
        windts = _windts({"PROP-a": 35.0})
        props = [_property("PROP-a", threshold_kph=100.0,
                           bri_wind=0.85, bri_composite=0.80)]
        payload = build_event_damage(windts, props)
        d = payload["damages"][0]
        assert d["v_50_eff_ms"] > d["threshold_ms"]
        # And damage is lower than the no-BRI baseline at the same peak.
        baseline = build_event_damage(
            windts, [_property("PROP-a", threshold_kph=100.0)],
        )["damages"][0]["damage_ratio"]
        assert d["damage_ratio"] < baseline

    def test_low_bri_increases_damage(self):
        windts = _windts({"PROP-a": 35.0})
        props_vuln = [_property("PROP-a", threshold_kph=100.0,
                                bri_wind=0.10, bri_composite=0.15)]
        props_base = [_property("PROP-a", threshold_kph=100.0)]
        d_vuln = build_event_damage(windts, props_vuln)["damages"][0]
        d_base = build_event_damage(windts, props_base)["damages"][0]
        assert d_vuln["damage_ratio"] > d_base["damage_ratio"]

    def test_records_without_id_are_skipped(self):
        windts = _windts({"PROP-a": 35.0})
        props = [
            _property("PROP-a", threshold_kph=100.0),
            {"NoHeader": "junk"},   # unrecognisable record
        ]
        payload = build_event_damage(windts, props)
        assert len(payload["damages"]) == 1


# -- run_event: disk round-trip ---------------------------------------------


class TestRunEvent:

    def test_writes_json_to_output_path(self, tmp_path):
        # Stage a windts file on disk so load_event_peaks reads it.
        windts_path = tmp_path / "EVT-0001.json"
        windts_path.write_text(json.dumps({
            "event_id": "EVT-0001",
            "scenario_family": "severe",
            "horizon_hours": 168.0,
            "dt_hours": 1.0,
            "property_windts": [{"point_id": "PROP-a", "peak_sustained_ms": 40.0}],
        }))

        out_path = tmp_path / "damage" / "EVT-0001.json"
        props = [_property("PROP-a", threshold_kph=100.0, bri_wind=0.55, bri_composite=0.50)]

        payload = run_event(windts_path, props, out_path)
        assert out_path.exists()

        on_disk = json.loads(out_path.read_text())
        assert on_disk == payload
        assert on_disk["scenario_family"] == "severe"
        assert len(on_disk["damages"]) == 1

    def test_run_event_directory_writes_one_file_per_input(self, tmp_path):
        windts_dir = tmp_path / "windts"
        damage_dir = tmp_path / "damage"
        windts_dir.mkdir()

        for i, peak in enumerate([32.0, 45.0, 18.0]):
            (windts_dir / f"EVT-{i:04d}.json").write_text(json.dumps({
                "event_id": f"EVT-{i:04d}",
                "scenario_family": "baseline",
                "horizon_hours": 168.0,
                "dt_hours": 1.0,
                "property_windts": [{"point_id": "PROP-a", "peak_sustained_ms": peak}],
            }))

        props = [_property("PROP-a", threshold_kph=100.0)]
        written = run_event_directory(windts_dir, damage_dir, props)
        assert [p.name for p in written] == ["EVT-0000.json", "EVT-0001.json", "EVT-0002.json"]
        for p in written:
            assert p.exists()


# -- Persistence (duration-of-load) wiring ----------------------------------


class TestPersistenceInComposer:

    def test_no_series_falls_back_to_peak_only(self):
        # Legacy peak-only windts: no series -> saturated bound, persistence 1.0.
        from models.winddamage.vulnerability import bri_peak_damage
        windts = _windts({"PROP-a": 40.0})
        props = [_property("PROP-a", threshold_kph=100.0)]
        d = build_event_damage(windts, props)["damages"][0]
        assert d["duration_above_hours"] is None
        assert d["persistence_factor"] == 1.0
        thr = DEFAULT_WIND_THRESHOLD_KPH / 3.6
        assert d["damage_ratio"] == pytest.approx(bri_peak_damage(40.0, thr), abs=1e-12)

    def test_series_adds_duration_and_persistence_fields(self):
        windts = _windts_series({"PROP-a": 40.0}, {"PROP-a": _flat_series(40.0, 6)})
        d = build_event_damage(windts, [_property("PROP-a", threshold_kph=100.0)])["damages"][0]
        # 40 m/s held for 6 h, all above v_50 (~27.8) -> ~6 h above threshold.
        assert d["duration_above_hours"] == pytest.approx(6.0, abs=1e-9)
        assert 0.45 <= d["persistence_factor"] < 1.0

    def test_brief_gust_less_than_sustained(self):
        # The headline requirement, end-to-end through the composer.
        brief = _windts_series({"PROP-a": 45.0}, {"PROP-a": _flat_series(45.0, 1)})
        long = _windts_series({"PROP-a": 45.0}, {"PROP-a": _flat_series(45.0, 24)})
        prop = [_property("PROP-a", threshold_kph=100.0)]
        d_brief = build_event_damage(brief, prop)["damages"][0]["damage_ratio"]
        d_long = build_event_damage(long, prop)["damages"][0]["damage_ratio"]
        assert d_brief < d_long

    def test_duration_measured_above_v50_eff(self):
        # A hardened property (higher v_50_eff) spends less time above its
        # threshold for the same wind series, so less persistence accrues.
        series = {"PROP-a": _flat_series(40.0, 6)}
        soft = _windts_series({"PROP-a": 40.0}, series)
        hard = _windts_series({"PROP-a": 40.0}, series)
        d_soft = build_event_damage(
            soft, [_property("PROP-a", threshold_kph=100.0)],
        )["damages"][0]
        d_hard = build_event_damage(
            hard, [_property("PROP-a", threshold_kph=130.0,
                             bri_wind=0.90, bri_composite=0.85)],
        )["damages"][0]
        # Hardened threshold sits above 40 m/s -> 0 h above -> gust floor.
        assert d_hard["duration_above_hours"] < d_soft["duration_above_hours"]
        assert d_hard["damage_ratio"] < d_soft["damage_ratio"]

    def test_run_event_round_trip_includes_persistence(self, tmp_path):
        # A real windts file with the sustained series round-trips with the
        # new fields populated.
        windts_path = tmp_path / "EVT-0007.json"
        times, sustained = _flat_series(42.0, 5)
        windts_path.write_text(json.dumps({
            "event_id": "EVT-0007",
            "scenario_family": "severe",
            "horizon_hours": 168.0,
            "dt_hours": 1.0,
            "property_windts": [{
                "point_id": "PROP-a",
                "peak_sustained_ms": 42.0,
                "time_hours": times,
                "sustained_ms": sustained,
            }],
        }))
        out_path = tmp_path / "damage" / "EVT-0007.json"
        payload = run_event(windts_path, [_property("PROP-a", threshold_kph=100.0)], out_path)
        d = payload["damages"][0]
        assert d["duration_above_hours"] == pytest.approx(5.0, abs=1e-9)
        assert 0.45 <= d["persistence_factor"] < 1.0
        assert json.loads(out_path.read_text()) == payload
