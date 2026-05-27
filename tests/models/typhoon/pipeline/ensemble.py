# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for models.typhoon.pipeline.ensemble — top-level simulator."""

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


class TestWindtsOutput:
    """Per-property wind timeseries written during the pipeline run, for
    downstream consumers (flood model, BRI scoring, visualisation)."""

    def test_writes_one_file_per_event(self, minimal_config, tmp_path):
        windts_dir = tmp_path / "windts"
        simulate_typhoon_events(
            config=minimal_config, n_events=3, n_particles=5,
            rng=np.random.default_rng(0), horizon_hours=4.0,
            windts_output_dir=windts_dir,
        )
        files = sorted(windts_dir.glob("EVT-*.json"))
        assert len(files) == 3
        assert files[0].name == "EVT-0000.json"

    def test_windts_payload_shape(self, minimal_config, tmp_path):
        import json
        windts_dir = tmp_path / "windts"
        simulate_typhoon_events(
            config=minimal_config, n_events=1, n_particles=4,
            rng=np.random.default_rng(0), horizon_hours=4.0,
            windts_output_dir=windts_dir,
        )
        with (windts_dir / "EVT-0000.json").open() as f:
            payload = json.load(f)
        assert payload["event_id"] == "EVT-0000"
        assert payload["horizon_hours"] == 4.0
        assert payload["dt_hours"] == 1.0
        assert "property_windts" in payload
        # One WindFieldOutput per configured property point.
        assert len(payload["property_windts"]) == len(minimal_config.property_points)
        first = payload["property_windts"][0]
        assert "point_id" in first
        assert "sustained_ms" in first
        assert "time_hours" in first
        assert len(first["sustained_ms"]) == len(first["time_hours"])

    def test_no_windts_dir_no_files_written(self, minimal_config, tmp_path):
        # When windts_output_dir is None, nothing extra is written.
        simulate_typhoon_events(
            config=minimal_config, n_events=2, n_particles=4,
            rng=np.random.default_rng(0), horizon_hours=4.0,
        )
        assert not any(tmp_path.glob("**/EVT-*.json"))

    def test_events_and_windts_use_same_representative(self, minimal_config, tmp_path):
        # The representative particle picked for events/ must be the same
        # one whose wind outputs are written to windts/ — so the storm
        # track and the per-property wind timeseries describe the same
        # realization.
        import json
        events_dir = tmp_path / "events"
        windts_dir = tmp_path / "windts"
        simulate_typhoon_events(
            config=minimal_config, n_events=1, n_particles=6,
            rng=np.random.default_rng(0), horizon_hours=4.0,
            events_output_dir=events_dir, windts_output_dir=windts_dir,
        )
        with (events_dir / "EVT-0000.json").open() as f:
            event_payload = json.load(f)
        with (windts_dir / "EVT-0000.json").open() as f:
            windts_payload = json.load(f)
        # The event's particle_id should match the scenario family the
        # windts file records (the simple proxy that ties them together).
        assert event_payload["scenario_family"] == windts_payload["scenario_family"]
