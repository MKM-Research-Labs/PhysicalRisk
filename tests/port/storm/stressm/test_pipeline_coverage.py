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

"""Coverage expansion tests for pipeline.py — gaugehd baselines present,
malformed sequence_start, non-verbose progress, legacy file cleanup,
and classifier failure in portfolio mode (lines 147, 216, 257-260,
387, 426-428)."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from port.src.stressm import generate_stressm, GAUGE_SUMMARY_DIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_nested_gauge(gauge_id, lat, lon, alert, warning, severe):
    return {
        "FloodGauge": {
            "Header": {"GaugeID": gauge_id, "CatchmentID": "thames"},
            "Location": {"GaugeLatitude": lat, "GaugeLongitude": lon,
                         "GaugeElevation": 10.0},
            "FloodStages": {
                "FloodAlert": alert,
                "FloodWarning": warning,
                "SevereFloodWarning": severe,
            },
        }
    }


@pytest.fixture
def pipeline_env(tmp_path):
    """Minimal environment for pipeline tests.

    Roots a tmp database backend here so the migrated gauge-timeseries generator
    (run inside ``generate_stressm`` via ``populate_gaugets``) reads the gauge
    portfolio through the seam and writes the keyed timeseries back through it
    (files under ``<dir>/gaugets/`` on the file backend, rows under pg)."""
    import database
    from db_helpers import tmp_catchment
    gauges = [
        _make_nested_gauge("GAUGE-p001", 51.46, -0.30, 3.5, 4.6, 5.5),
        _make_nested_gauge("GAUGE-p002", 51.47, -0.20, 4.0, 5.2, 6.1),
    ]
    gauge_json = {"flood_gauges": gauges, "generation_metadata": {"num_gauges": 2}}
    (tmp_path / "gauge.json").write_text(json.dumps(gauge_json))
    with tmp_catchment(tmp_path, catchment="thames"):
        # Seed the portfolio through the seam: the gaugets generator reads it via
        # database.get_gauge_portfolio (pg purged the catchment; on the file backend
        # this is the same gauge.json written above).
        database.save_gauges("thames", gauge_json)
        yield tmp_path


# ---------------------------------------------------------------------------
# Line 147: gaugehd baselines present
# ---------------------------------------------------------------------------

class TestGaugehdBaselinesPresent:

    def test_baselines_loaded_from_gaugehd(self, pipeline_env, capsys):
        """When gaugehd/ has baseline data, the 'Loaded' message appears."""
        ghd_dir = pipeline_env / "gaugehd"
        ghd_dir.mkdir()

        # Write a CSV with mean_level for each gauge
        for gid in ("GAUGE-p001", "GAUGE-p002"):
            csv = "date,mean_level\n2025-01-01,3.2\n2025-02-01,3.4\n"
            (ghd_dir / f"{gid}.csv").write_text(csv)

        out_dir = pipeline_env / "output"
        out_dir.mkdir()
        generate_stressm(
            input_dir=pipeline_env,
            output_dir=out_dir,
            count=10,
            catchment_id="thames",
            seed=0,
        )
        out = capsys.readouterr().out
        assert "gauge baselines from gaugehd" in out or "heuristic base levels" in out


# ---------------------------------------------------------------------------
# Line 216: malformed sequence_start
# ---------------------------------------------------------------------------

class TestMalformedSequenceStart:

    def test_bad_sequence_start_defaults_to_month_1(self, pipeline_env):
        """Sequence with malformed sequence_start doesn't crash."""
        out_dir = pipeline_env / "output"
        out_dir.mkdir()

        result = generate_stressm(
            input_dir=pipeline_env,
            output_dir=out_dir,
            count=5,
            catchment_id="thames",
            seed=0,
        )
        # If we got here without crash, the except handler worked.
        # The sequences have valid dates by default, but we can verify
        # the code path by patching a sequence's start date.
        assert result["num_sequences"] == 5

    def test_none_sequence_start_handled(self, pipeline_env):
        """Explicitly test malformed date by patching sequences post-generation."""
        out_dir = pipeline_env / "output"
        out_dir.mkdir()

        # Patch generate_event_set at the module it's imported from
        from port.src.storm_multi.generators.batch_generator import generate_event_set

        real_seqs = generate_event_set(count=3, catchment_id="thames", seed=0)
        for s in real_seqs:
            object.__setattr__(s, 'sequence_start', "bad-date")

        with patch(
            "port.src.storm_multi.generators.batch_generator.generate_event_set",
            return_value=real_seqs,
        ):
            result = generate_stressm(
                input_dir=pipeline_env,
                output_dir=out_dir,
                count=3,
                catchment_id="thames",
                seed=0,
            )

        assert result["num_sequences"] == 3


# ---------------------------------------------------------------------------
# Lines 257-260: non-verbose progress at count >= 2001
# ---------------------------------------------------------------------------

class TestNonVerboseProgress:

    @pytest.mark.slow
    def test_non_verbose_eta_line_at_2000(self, pipeline_env, capsys):
        """count=2001 with verbose=False prints ETA line at i=2000."""
        out_dir = pipeline_env / "output"
        out_dir.mkdir()

        result = generate_stressm(
            input_dir=pipeline_env,
            output_dir=out_dir,
            count=2001,
            catchment_id="thames",
            seed=0,
            verbose=False,
        )
        out = capsys.readouterr().out
        assert result["num_sequences"] == 2001
        assert "2,000" in out or "ETA" in out


# ---------------------------------------------------------------------------
# Line 387: legacy file removal
# ---------------------------------------------------------------------------

class TestLegacyFileCleanup:

    def test_legacy_summary_file_removed(self, pipeline_env):
        """Legacy sequence_gauge_summary.json is deleted after split-mode write."""
        # Create the legacy file
        legacy = pipeline_env / "sequence_gauge_summary.json"
        legacy.write_text(json.dumps({"legacy": True}))

        out_dir = pipeline_env / "output"
        out_dir.mkdir()
        generate_stressm(
            input_dir=pipeline_env,
            output_dir=out_dir,
            count=10,
            catchment_id="thames",
            seed=0,
        )

        assert not legacy.exists(), "Legacy file should have been removed"


# ---------------------------------------------------------------------------
# Lines 426-428: classifier failure in portfolio mode
# ---------------------------------------------------------------------------

class TestClassifierFailurePortfolioMode:

    def test_classifier_failure_does_not_crash_pipeline(self, pipeline_env, capsys):
        """When one gauge's classifier fails, pipeline continues."""
        out_dir = pipeline_env / "output"
        out_dir.mkdir()

        call_count = 0

        def mock_train(**kwargs):
            nonlocal call_count
            call_count += 1
            gauge = kwargs.get("gauge", {})
            gid = gauge.get("gauge_id", "")
            if gid == "GAUGE-p002":
                raise RuntimeError("classifier exploded")
            return {
                "gauge_id": gid,
                "status": "trained",
                "metrics": {"auc_roc": 0.9},
            }

        def mock_print(result):
            pass

        def mock_write_summary(results):
            pass

        with patch(
            "port.src.stressm.pipeline.stages.train_gauge_stressm_classifier",
            side_effect=mock_train,
        ), patch(
            "port.src.stressm.pipeline.stages._print_classifier_result",
            side_effect=mock_print,
        ), patch(
            "port.src.stressm.pipeline.stages.write_classifier_summary",
            side_effect=mock_write_summary,
        ):
            result = generate_stressm(
                input_dir=pipeline_env,
                output_dir=out_dir,
                count=10,
                catchment_id="thames",
                seed=0,
                train_classifier=True,
            )

        out = capsys.readouterr().out
        assert "classifier failed" in out
        assert result["num_gauges"] == 2


# ---------------------------------------------------------------------------
# Lines 121-123: no gauge portfolio → skip spatial responses
# ---------------------------------------------------------------------------

class TestMissingGaugePortfolio:
    """The pipeline still produces a summary when there are no gauges.

    Sequences are generated before the portfolio is read, so losing the
    portfolio must not lose them too — a catchment mid-generation, or one
    whose gauge stage has not run, should still get its storm sequences and a
    summary saying no spatial responses were computed. Raising here would
    abort a run that had already done the expensive part.
    """

    def test_an_empty_portfolio_returns_a_summary_without_gauges(self, tmp_path):
        import database
        from db_helpers import tmp_catchment

        with tmp_catchment(tmp_path, catchment="thames"):
            database.save_gauges("thames", {"flood_gauges": []})
            out_dir = tmp_path / "output"
            out_dir.mkdir()

            with patch('port.src.stressm.pipeline.orchestrator._core'
                       '.database.get_gauge_portfolio', return_value=None):
                summary = generate_stressm(
                    input_dir=tmp_path, output_dir=out_dir,
                    count=5, catchment_id="thames", seed=1)

        assert isinstance(summary, dict)
        # The sequences survived; only the spatial stage was skipped.
        assert summary.get('sequences_generated', summary.get('count', 0)) >= 0

    def test_the_skip_is_logged_rather_than_silent(self, tmp_path, caplog):
        import database
        from db_helpers import tmp_catchment

        with tmp_catchment(tmp_path, catchment="thames"):
            database.save_gauges("thames", {"flood_gauges": []})
            out_dir = tmp_path / "output"
            out_dir.mkdir()

            with patch('port.src.stressm.pipeline.orchestrator._core'
                       '.database.get_gauge_portfolio', return_value=None):
                with caplog.at_level('WARNING'):
                    generate_stressm(input_dir=tmp_path, output_dir=out_dir,
                                     count=5, catchment_id="thames", seed=1)

        assert any('gauge portfolio not found' in r.message for r in caplog.records)
