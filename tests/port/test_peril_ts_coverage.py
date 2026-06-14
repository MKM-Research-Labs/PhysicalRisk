# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage tests for port.src.peril.peril_ts — caching, malformed-input
fallbacks, the unknown-mode guard and the missing-base-ts error path."""

import json
import logging

import pytest

from port.src.peril.peril_ts import PerilTimeseriesGenerator


def _write(path, obj):
    path.write_text(json.dumps(obj))


class TestPerilTimeseriesCoverage:
    def test_log_emits_when_verbose(self, tmp_path, caplog):
        gen = PerilTimeseriesGenerator(output_dir=tmp_path, verbose=True)
        with caplog.at_level(logging.INFO):
            gen.log("hello peril")
        assert "hello peril" in caplog.text  # line 96

    def test_wind_damage_index_caches_and_skips_bad_file(self, tmp_path):
        dmg = tmp_path / "typhoon" / "damage"
        dmg.mkdir(parents=True)
        (dmg / "EVT-00001.json").write_text("{ this is not valid json")  # 118,119
        gen = PerilTimeseriesGenerator(output_dir=tmp_path)
        first = gen._wind_damage_index()
        assert first == {}
        assert gen._wind_damage_index() is first  # cache hit -> line 110

    def test_seq_to_event_map_caches_and_swallows_bad_file(self, tmp_path):
        (tmp_path / "storm_sequences.json").write_text("{ not json")  # line 150
        gen = PerilTimeseriesGenerator(output_dir=tmp_path)
        first = gen._seq_to_event_map()
        assert first == {}
        assert gen._seq_to_event_map() is first  # cache hit -> line 138

    def test_peril_flag_unknown_mode_raises(self, tmp_path):
        gen = PerilTimeseriesGenerator(output_dir=tmp_path)
        with pytest.raises(ValueError):
            gen._peril_flag("nope", True, True)  # line 172

    def test_generate_raises_when_base_ts_missing(self, tmp_path):
        # A non-empty wind damage index keeps generate() past its early
        # "no typhoon damage" return so the missing flood-spine dir raises.
        dmg = tmp_path / "typhoon" / "damage"
        dmg.mkdir(parents=True)
        _write(dmg / "EVT-00001.json", {"damages": [
            {"property_id": "PROP-1", "peak_sustained_ms": 60.0,
             "threshold_ms": 50.0, "v_50_eff_ms": 50.0}]})
        gen = PerilTimeseriesGenerator(output_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            gen.generate()  # line 190 — normal flood ts dir absent
