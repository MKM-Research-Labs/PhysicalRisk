# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for generate_stress_storms — trigger_summary fields and
intensity category derivation.
"""

import json
import pytest

from tests.port.gauge.conftest import make_gauge_file, make_response


# ---------------------------------------------------------------------------
# trigger_summary
# ---------------------------------------------------------------------------

class TestTriggerSummary:

    @pytest.fixture
    def single_storm_data(self, tmp_path):
        """Two gauges: one severe, one alert-only."""
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, warning=True, severe=True, peak=3.0)],
        )))
        (gaugets / "GAUGE-00000002.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000002",
            [make_response(sid, alert=True, warning=False, severe=False, peak=2.0)],
        )))
        out = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out)
        data = json.loads((out / "_index.json").read_text())
        return data["storms"][0]

    def test_trigger_summary_present(self, single_storm_data):
        assert "trigger_summary" in single_storm_data

    def test_gauges_alert_count(self, single_storm_data):
        assert single_storm_data["trigger_summary"]["gauges_alert"] == 2

    def test_gauges_warning_count(self, single_storm_data):
        assert single_storm_data["trigger_summary"]["gauges_warning"] == 1

    def test_gauges_severe_count(self, single_storm_data):
        assert single_storm_data["trigger_summary"]["gauges_severe"] == 1

    def test_gauges_impacted_matches_alert(self, single_storm_data):
        ts = single_storm_data["trigger_summary"]
        assert ts["gauges_impacted"] == ts["gauges_alert"]

    def test_max_trigger_is_severe(self, single_storm_data):
        assert single_storm_data["trigger_summary"]["max_trigger"] == "severe"

    def test_max_trigger_is_warning_when_no_severe(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, warning=True, severe=False, peak=2.0)],
        )))
        out = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out)
        data = json.loads((out / "_index.json").read_text())
        assert data["storms"][0]["trigger_summary"]["max_trigger"] == "warning"

    def test_max_trigger_is_alert_when_alert_only(self, tmp_path):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        (gaugets / "GAUGE-00000001.json").write_text(json.dumps(make_gauge_file(
            "GAUGE-00000001",
            [make_response(sid, alert=True, warning=False, severe=False, peak=2.0)],
        )))
        out = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out)
        data = json.loads((out / "_index.json").read_text())
        assert data["storms"][0]["trigger_summary"]["max_trigger"] == "alert"


# ---------------------------------------------------------------------------
# Intensity category derivation
# ---------------------------------------------------------------------------

class TestIntensityCategoryDerivation:

    def _run(self, tmp_path, *, n_severe=0, n_warning=0, n_alert=0):
        from port.src.gauge.stress_storms import generate_stress_storms
        gaugets = tmp_path / "gaugets"
        gaugets.mkdir()
        sid = "STORM-aabbccdd"
        for i in range(max(n_severe, n_warning, n_alert, 1)):
            sev = i < n_severe
            warn = i < n_warning or sev
            ale = i < n_alert or warn or sev or True
            gf = gaugets / f"GAUGE-{i:08d}.json"
            gf.write_text(json.dumps(make_gauge_file(
                f"GAUGE-{i:08d}",
                [make_response(sid, alert=ale, warning=warn, severe=sev, peak=2.0 + i * 0.1)],
            )))
        out = tmp_path / "stress_storms"
        generate_stress_storms(gaugets, out)
        data = json.loads((out / "_index.json").read_text())
        return data["storms"][0]["intensity_category"]

    def test_catastrophic_10_severe(self, tmp_path):
        assert self._run(tmp_path, n_severe=10) == "catastrophic"

    def test_extreme_6_severe(self, tmp_path):
        assert self._run(tmp_path, n_severe=6) == "extreme"

    def test_severe_3_severe(self, tmp_path):
        assert self._run(tmp_path, n_severe=3) == "severe"

    def test_moderate_1_severe(self, tmp_path):
        assert self._run(tmp_path, n_severe=1) == "moderate"

    def test_baseline_alert_only(self, tmp_path):
        assert self._run(tmp_path, n_severe=0, n_warning=0) == "baseline"
