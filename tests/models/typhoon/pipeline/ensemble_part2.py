# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for models.typhoon.pipeline.ensemble — top-level simulator. (part 2 of 2)"""

import json

import numpy as np
import pytest

from models.typhoon.pipeline import (
    TyphoonEventEnsemble,
    simulate_typhoon_events,
    write_ensemble_json,
)


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


class TestCoupledGenesis:
    """Stage 3 — event_severity_q couples genesis Vmax to the paired storm.

    Higher severity quantiles must yield stronger storms on average; per-event
    seeds make the coupled draw reproducible irrespective of loop order; and
    the standalone path (no q) is left untouched.
    """

    def test_severity_q_length_must_match_events(self, minimal_config):
        with pytest.raises(ValueError):
            simulate_typhoon_events(
                config=minimal_config, n_events=3, n_particles=3,
                rng=np.random.default_rng(0), horizon_hours=2.0,
                event_severity_q=[0.5, 0.9],   # 2 != 3
            )

    def test_event_seeds_length_must_match_events(self, minimal_config):
        with pytest.raises(ValueError):
            simulate_typhoon_events(
                config=minimal_config, n_events=2, n_particles=3,
                rng=np.random.default_rng(0), horizon_hours=2.0,
                event_seeds=[1, 2, 3],   # 3 != 2
            )

    def test_metadata_flags_coupled_run(self, minimal_config):
        ensemble = simulate_typhoon_events(
            config=minimal_config, n_events=2, n_particles=3,
            rng=np.random.default_rng(0), horizon_hours=2.0,
            event_severity_q=[0.3, 0.95], event_seeds=[11, 22],
            coupling_beta=0.5,
        )
        assert ensemble.metadata["coupled_genesis"] is True
        assert ensemble.metadata["coupling_beta"] == 0.5

    def test_standalone_metadata_has_no_beta(self, minimal_config):
        ensemble = simulate_typhoon_events(
            config=minimal_config, n_events=2, n_particles=3,
            rng=np.random.default_rng(0), horizon_hours=2.0,
        )
        assert ensemble.metadata["coupled_genesis"] is False
        assert ensemble.metadata["coupling_beta"] is None

    def test_per_event_seed_makes_genesis_reproducible(self, minimal_config, tmp_path):
        # Same q + same seed -> identical representative track peak, regardless
        # of the shared rng (so loop order / other events cannot perturb it).
        def run(outdir):
            simulate_typhoon_events(
                config=minimal_config, n_events=2, n_particles=5,
                rng=np.random.default_rng(0), horizon_hours=3.0,
                event_ids=["EVT-00000", "EVT-00001"],
                event_severity_q=[0.4, 0.92], event_seeds=[123, 456],
                coupling_beta=0.5, events_output_dir=outdir,
            )
        run(tmp_path / "a")
        run(tmp_path / "b")
        for name in ("EVT-00000.json", "EVT-00001.json"):
            with (tmp_path / "a" / name).open() as f:
                pa = json.load(f)
            with (tmp_path / "b" / name).open() as f:
                pb = json.load(f)
            assert pa["summary"]["peak_v_max_ms"] == pytest.approx(
                pb["summary"]["peak_v_max_ms"])

    def test_higher_severity_yields_stronger_storms(self, minimal_config):
        # Average p99 peak wind across properties should rise with severity.
        low = simulate_typhoon_events(
            config=minimal_config, n_events=12, n_particles=8,
            rng=np.random.default_rng(1), horizon_hours=3.0,
            event_severity_q=[0.15] * 12,
            event_seeds=list(range(12)), coupling_beta=0.5,
        )
        high = simulate_typhoon_events(
            config=minimal_config, n_events=12, n_particles=8,
            rng=np.random.default_rng(1), horizon_hours=3.0,
            event_severity_q=[0.95] * 12,
            event_seeds=list(range(12)), coupling_beta=0.5,
        )
        low_peak = np.mean([p.peak_sustained_p99 for p in low.properties])
        high_peak = np.mean([p.peak_sustained_p99 for p in high.properties])
        assert high_peak > low_peak
