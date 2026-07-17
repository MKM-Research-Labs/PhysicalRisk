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

"""Tests for models.typhoon.pipeline.ensemble — top-level simulator. (part 1 of 2)"""

import json

import numpy as np
import pytest

from models.typhoon.pipeline import (
    TyphoonEventEnsemble,
    simulate_typhoon_events,
    write_ensemble_json,
)


class TestSimulateTyphoonEvents:

    def test_returns_typhoon_event_ensemble(self, minimal_config):
        ensemble = simulate_typhoon_events(
            config=minimal_config,
            n_events=3,
            n_particles=8,
            rng=np.random.default_rng(0),
            horizon_hours=6.0,
        )
        assert isinstance(ensemble, TyphoonEventEnsemble)
        assert ensemble.catchment_id == minimal_config.catchment_id
        assert ensemble.n_events == 3
        assert ensemble.n_particles == 8

    def test_every_property_present_in_results(self, minimal_config):
        ensemble = simulate_typhoon_events(
            config=minimal_config, n_events=2, n_particles=5,
            rng=np.random.default_rng(0), horizon_hours=4.0,
        )
        configured_ids = {p.property_id for p in minimal_config.property_points}
        result_ids = {p.property_id for p in ensemble.properties}
        assert result_ids == configured_ids

    def test_realization_count_matches_events_x_particles(self, minimal_config):
        ensemble = simulate_typhoon_events(
            config=minimal_config, n_events=3, n_particles=7,
            rng=np.random.default_rng(0), horizon_hours=4.0,
        )
        for p in ensemble.properties:
            assert p.n_realizations == 21

    def test_zero_events_produces_empty_summaries(self, minimal_config):
        ensemble = simulate_typhoon_events(
            config=minimal_config, n_events=0, n_particles=5,
            rng=np.random.default_rng(0), horizon_hours=4.0,
        )
        assert ensemble.n_events == 0
        for p in ensemble.properties:
            assert p.n_realizations == 0

    def test_negative_n_events_rejected(self, minimal_config):
        with pytest.raises(ValueError):
            simulate_typhoon_events(
                config=minimal_config, n_events=-1, n_particles=5,
                rng=np.random.default_rng(0), horizon_hours=4.0,
            )

    def test_non_positive_n_particles_rejected(self, minimal_config):
        with pytest.raises(ValueError):
            simulate_typhoon_events(
                config=minimal_config, n_events=2, n_particles=0,
                rng=np.random.default_rng(0), horizon_hours=4.0,
            )

    def test_metadata_records_run_parameters(self, minimal_config):
        ensemble = simulate_typhoon_events(
            config=minimal_config, n_events=2, n_particles=4,
            rng=np.random.default_rng(0), horizon_hours=4.0,
            use_plausibility=False,
        )
        assert ensemble.metadata["use_plausibility"] is False
        assert ensemble.metadata["n_property_points"] == len(minimal_config.property_points)
        assert ensemble.metadata["n_realizations_per_property"] == 8
        assert ensemble.metadata["elapsed_seconds"] >= 0.0


class TestWriteEnsembleJson:

    def test_disk_roundtrip(self, minimal_config, tmp_path):
        ensemble = simulate_typhoon_events(
            config=minimal_config, n_events=2, n_particles=5,
            rng=np.random.default_rng(0), horizon_hours=4.0,
        )
        out = tmp_path / "typhoon" / "ensemble.json"
        write_ensemble_json(ensemble, out)
        assert out.exists()

        with out.open() as f:
            payload = json.load(f)
        restored = TyphoonEventEnsemble.from_dict(payload)
        assert restored.n_events == ensemble.n_events
        assert len(restored.properties) == len(ensemble.properties)

    def test_creates_parent_directories(self, minimal_config, tmp_path):
        ensemble = simulate_typhoon_events(
            config=minimal_config, n_events=1, n_particles=3,
            rng=np.random.default_rng(0), horizon_hours=2.0,
        )
        out = tmp_path / "a" / "b" / "c" / "ensemble.json"
        write_ensemble_json(ensemble, out)
        assert out.exists()


class TestEventTrajectoryOutput:

    def test_events_output_dir_writes_per_event_files(self, minimal_config, tmp_path):
        events_dir = tmp_path / "events"
        simulate_typhoon_events(
            config=minimal_config, n_events=4, n_particles=5,
            rng=np.random.default_rng(0), horizon_hours=4.0,
            events_output_dir=events_dir,
        )
        files = sorted(events_dir.glob("EVT-*.json"))
        assert len(files) == 4
        # Files numbered 0000..0003.
        assert files[0].name == "EVT-0000.json"
        assert files[-1].name == "EVT-0003.json"

    def test_each_event_file_has_summary_and_states(self, minimal_config, tmp_path):
        import json
        events_dir = tmp_path / "events"
        simulate_typhoon_events(
            config=minimal_config, n_events=2, n_particles=4,
            rng=np.random.default_rng(0), horizon_hours=4.0,
            events_output_dir=events_dir,
        )
        with (events_dir / "EVT-0000.json").open() as f:
            payload = json.load(f)
        assert "states" in payload
        assert len(payload["states"]) >= 1
        assert "summary" in payload
        assert payload["summary"]["event_idx"] == 0
        assert payload["summary"]["peak_v_max_ms"] > 0.0

    def test_no_events_dir_no_per_event_files_written(self, minimal_config, tmp_path):
        # When events_output_dir is None, nothing extra is written.
        simulate_typhoon_events(
            config=minimal_config, n_events=2, n_particles=4,
            rng=np.random.default_rng(0), horizon_hours=4.0,
        )
        assert not any(tmp_path.glob("EVT-*.json"))


class TestEventIdSlaving:
    """Stage 2 — caller-supplied event_ids slave the count and name artefacts.

    When the typhoon stage couples to a storm event set it passes the shared
    1:1 keys (e.g. EVT-00001) so the count follows the storm sequences and the
    per-event files carry the join key used downstream (Stage 4).
    """

    def test_event_ids_slave_the_count(self, minimal_config):
        # n_events is ignored when event_ids is supplied.
        ensemble = simulate_typhoon_events(
            config=minimal_config, n_events=999, n_particles=3,
            rng=np.random.default_rng(0), horizon_hours=2.0,
            event_ids=["EVT-00000", "EVT-00001", "EVT-00002"],
        )
        assert ensemble.n_events == 3

    def test_event_ids_name_trajectory_and_windts_files(self, minimal_config, tmp_path):
        events_dir = tmp_path / "events"
        windts_dir = tmp_path / "windts"
        ids = ["EVT-00007", "EVT-00042"]
        simulate_typhoon_events(
            config=minimal_config, n_events=2, n_particles=4,
            rng=np.random.default_rng(0), horizon_hours=4.0,
            events_output_dir=events_dir, windts_output_dir=windts_dir,
            event_ids=ids,
        )
        for d in (events_dir, windts_dir):
            names = sorted(p.name for p in d.glob("EVT-*.json"))
            assert names == ["EVT-00007.json", "EVT-00042.json"]

    def test_windts_payload_carries_supplied_event_id(self, minimal_config, tmp_path):
        windts_dir = tmp_path / "windts"
        simulate_typhoon_events(
            config=minimal_config, n_events=1, n_particles=3,
            rng=np.random.default_rng(0), horizon_hours=2.0,
            windts_output_dir=windts_dir, event_ids=["EVT-01234"],
        )
        with (windts_dir / "EVT-01234.json").open() as f:
            payload = json.load(f)
        assert payload["event_id"] == "EVT-01234"

    def test_none_event_ids_keeps_index_naming(self, minimal_config, tmp_path):
        # Backward-compatible fallback: index naming when event_ids is None.
        events_dir = tmp_path / "events"
        simulate_typhoon_events(
            config=minimal_config, n_events=2, n_particles=3,
            rng=np.random.default_rng(0), horizon_hours=2.0,
            events_output_dir=events_dir,
        )
        names = sorted(p.name for p in events_dir.glob("EVT-*.json"))
        assert names == ["EVT-0000.json", "EVT-0001.json"]
