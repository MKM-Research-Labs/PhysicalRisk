# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Direct coverage for financial_basis loader helpers — the defensive
exception branches that swallow malformed JSON (lines 120-121, 140-141).

Catchment-agnostic: every file is synthesised inside tmp_path and
config paths are monkeypatched, so no real data/ is touched.
"""

from routes.propertyts import financial_basis as fb


class TestLoadGaugeThresholds:

    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fb.config, "get_input_dir", lambda: tmp_path)
        assert fb._load_gauge_thresholds() == {}

    def test_valid_file_parsed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fb.config, "get_input_dir", lambda: tmp_path)
        (tmp_path / "gaugehc.json").write_text(
            '{"hazard_curves": {"G1": {"gauge_name": "One", '
            '"flood_alert_m": 1.0, "elevation_m": 5}}}')
        out = fb._load_gauge_thresholds()
        assert out["G1"]["gauge_name"] == "One"
        assert out["G1"]["alert_m"] == 1.0

    def test_malformed_file_swallowed(self, tmp_path, monkeypatch):
        """Lines 120-121: corrupt gaugehc.json → warning + empty dict."""
        monkeypatch.setattr(fb.config, "get_input_dir", lambda: tmp_path)
        (tmp_path / "gaugehc.json").write_text("{not valid json")
        assert fb._load_gauge_thresholds() == {}


class TestLoadStormGaugePeaks:

    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fb.config, "get_input_path",
                            lambda name: tmp_path / name)
        assert fb._load_storm_gauge_peaks("STORM-X") == {}

    def test_valid_file_parsed(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fb.config, "get_input_path",
                            lambda name: tmp_path / name)
        sdir = tmp_path / "stress_storms"
        sdir.mkdir()
        (sdir / "STORM-1.json").write_text(
            '{"gauge_responses": [{"gauge_id": "G1", "peak_level_m": 2.5, '
            '"exceeded_severe": true}]}')
        out = fb._load_storm_gauge_peaks("STORM-1")
        assert out["G1"]["peak_level_m"] == 2.5
        assert out["G1"]["exceeded_severe"] is True

    def test_malformed_file_swallowed(self, tmp_path, monkeypatch):
        """Lines 140-141: corrupt storm file → warning + empty dict."""
        monkeypatch.setattr(fb.config, "get_input_path",
                            lambda name: tmp_path / name)
        sdir = tmp_path / "stress_storms"
        sdir.mkdir()
        (sdir / "STORM-1.json").write_text("{bad json")
        assert fb._load_storm_gauge_peaks("STORM-1") == {}
