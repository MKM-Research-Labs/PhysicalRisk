# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for generate_stress_storms — metadata enrichment from storms.json,
sorting order, and naming conventions.
"""

import json
import pytest

from tests.port.gauge.conftest import make_gauge_file, make_response


# ---------------------------------------------------------------------------
# Metadata enrichment from storms.json
# ---------------------------------------------------------------------------

class TestMetadataEnrichment:

    def test_duration_from_storms_json(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        storms_json = tmp_path / "storms.json"
        storms_json.write_text(json.dumps({
            "storms": [{"storm_id": sid, "duration_hours": 72, "peak_position": 0.3,
                        "effective_precipitation_mm": 45.0}]
        }))
        out = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out, storms_json_path=storms_json)
        data = json.loads((out / "_index.json").read_text())
        storm = data["storms"][0]
        assert storm["duration_hours"] == 72
        assert storm["peak_position"] == pytest.approx(0.3)
        assert storm["effective_precipitation_mm"] == pytest.approx(45.0)

    def test_fallback_to_config_defaults(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        from config.port import STRESS_STORM_DEFAULT_DURATION_HOURS, STRESS_STORM_DEFAULT_PEAK_POSITION
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        out = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out)  # no storms_json
        data = json.loads((out / "_index.json").read_text())
        storm = data["storms"][0]
        assert storm["duration_hours"] == STRESS_STORM_DEFAULT_DURATION_HOURS
        assert storm["peak_position"] == pytest.approx(STRESS_STORM_DEFAULT_PEAK_POSITION)

    def test_missing_storms_json_does_not_crash(self, tmp_path):
        """Passing a non-existent storms_json_path must not crash."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        out = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out, storms_json_path=tmp_path / "nonexistent.json")
        assert out.exists() and (out / "_index.json").exists()


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

class TestSorting:
    """Storms must be sorted: gauges_severe DESC -> gauges_warning DESC -> max peak DESC."""

    @pytest.fixture
    def sorted_storms(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()

        # Storm A: 0 severe, 1 warning, peak=2.5
        # Storm B: 2 severe, 2 warning, peak=3.0  <- should be first
        # Storm C: 0 severe, 0 warning, peak=5.0  <- alert only, should be last

        for gid_n, (sid, alert, warn, sev, peak) in enumerate([
            ("STORM-aaaaaaaa", True,  False, False, 2.5),  # storm A
            ("STORM-bbbbbbbb", True,  True,  True,  3.0),  # storm B gauge 1
            ("STORM-cccccccc", True,  False, False, 5.0),  # storm C
        ]):
            gf = gaugets / f"GAUGE-0000000{gid_n}.json"
            responses = [make_response(sid, alert=alert, warning=warn, severe=sev, peak=peak)]
            if sid == "STORM-aaaaaaaa":
                responses.append(make_response("STORM-aaaaaaaa", alert=True, warning=True, peak=2.5))
            gf.write_text(json.dumps(make_gauge_file(f"GAUGE-0000000{gid_n}", responses)))

        # Second gauge for storm B (severe)
        gf2 = gaugets / "GAUGE-00000003.json"
        gf2.write_text(json.dumps(make_gauge_file(
            "GAUGE-00000003",
            [make_response("STORM-bbbbbbbb", alert=True, warning=True, severe=True, peak=2.8)],
        )))

        out = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out)
        return json.loads((out / "_index.json").read_text())["storms"]

    def test_most_severe_is_first(self, sorted_storms):
        """STORM-bbbbbbbb (2 severe) must rank before all others."""
        assert sorted_storms[0]["storm_id"] == "STORM-bbbbbbbb", (
            f"Expected STORM-bbbbbbbb first, got {sorted_storms[0]['storm_id']}"
        )

    def test_alert_only_is_last(self, sorted_storms):
        """STORM-cccccccc (alert-only, no warning/severe) must be last."""
        assert sorted_storms[-1]["storm_id"] == "STORM-cccccccc", (
            f"Expected STORM-cccccccc last, got {sorted_storms[-1]['storm_id']}"
        )

    def test_sort_is_descending_by_severe(self, sorted_storms):
        """gauges_severe must be non-increasing."""
        severe_counts = [s["trigger_summary"]["gauges_severe"] for s in sorted_storms]
        assert severe_counts == sorted(severe_counts, reverse=True), (
            f"Storms not sorted by gauges_severe DESC: {severe_counts}"
        )


# ---------------------------------------------------------------------------
# Greek naming convention
# ---------------------------------------------------------------------------

class TestNaming:

    def test_first_storm_gets_greek_name(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        out = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out)
        data = json.loads((out / "_index.json").read_text())
        name = data["storms"][0]["name"]
        assert name  # non-empty
        assert name[0].isupper(), f"Expected name to start with capital, got: {name!r}"

    def test_name_from_storms_json_takes_priority(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, peak=2.0)],
        )))
        storms_json = tmp_path / "storms.json"
        storms_json.write_text(json.dumps({
            "storms": [{"storm_id": sid, "name": "CustomStormName",
                        "duration_hours": 168, "peak_position": 0.5,
                        "effective_precipitation_mm": 0}]
        }))
        out = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out, storms_json_path=storms_json)
        data = json.loads((out / "_index.json").read_text())
        assert data["storms"][0]["name"] == "CustomStormName"
