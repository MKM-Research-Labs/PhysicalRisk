"""Unit tests for governance lineage helper functions (_check_staleness, _trace_data)."""

import pathlib

from tests.routes.governance.lineage_shared import (
    SAMPLE_LINEAGE,
    create_fresh_file,
    create_stale_file,
)


# ══════════════════════════════════════════════════════════════════
# _check_staleness helper tests
# ══════════════════════════════════════════════════════════════════


class TestCheckStaleness:
    """Unit tests for _check_staleness helper."""

    def test_all_missing(self, lineage_env, monkeypatch):
        """All pipeline steps missing produces 'missing' statuses."""
        from config import config
        monkeypatch.setattr(config, "get_input_dir",
                            lambda: pathlib.Path(lineage_env["tmp_path"]))
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        assert len(results) == 10
        for r in results:
            assert r["status"] == "missing"
            assert "Output not found on disk" in r["issues"]
            assert r["last_run"] is None

    def test_fresh_file(self, lineage_env, monkeypatch):
        """A recently modified file is reported as 'fresh'."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        create_fresh_file(tmp, "gauge.json")
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        gauge_step = next(r for r in results if r["step"] == "gauges")
        assert gauge_step["status"] == "fresh"
        assert gauge_step["last_run"] is not None
        assert gauge_step["issues"] == []

    def test_stale_file(self, lineage_env, monkeypatch):
        """A file older than 72 hours is reported as 'stale'."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        create_stale_file(tmp, "property.json", days_old=5)
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        prop_step = next(r for r in results if r["step"] == "properties")
        assert prop_step["status"] == "stale"
        assert len(prop_step["issues"]) == 1
        assert "ago" in prop_step["issues"][0]

    def test_directory_step_fresh(self, lineage_env, monkeypatch):
        """A directory step checks most recent file mtime."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        # gaugehd/ is a directory step
        create_fresh_file(tmp, "gaugehd/GAUGE-001.json")
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        ghd_step = next(r for r in results if r["step"] == "gaugehd")
        assert ghd_step["status"] == "fresh"

    def test_directory_step_stale(self, lineage_env, monkeypatch):
        """A directory with only old files is stale."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        create_stale_file(tmp, "gaugehd/GAUGE-001.json", days_old=10)
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        ghd_step = next(r for r in results if r["step"] == "gaugehd")
        assert ghd_step["status"] == "stale"

    def test_empty_directory_is_missing(self, lineage_env, monkeypatch):
        """An empty directory counts as missing."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        (tmp / "gaugehd").mkdir()
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        ghd_step = next(r for r in results if r["step"] == "gaugehd")
        assert ghd_step["status"] == "missing"

    def test_manifest_last_run_used(self, lineage_env, monkeypatch):
        """If lineage manifest has last_run, it is carried through."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        lineage = {
            "steps": {
                "gauges": {"last_run": "2026-03-01T12:00:00"},
            }
        }
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(lineage)
        gauge_step = next(r for r in results if r["step"] == "gauges")
        assert gauge_step["last_run"] == "2026-03-01T12:00:00"

    def test_manifest_last_run_not_overwritten_by_mtime(self, lineage_env, monkeypatch):
        """If manifest has last_run AND file exists, manifest last_run is kept."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        create_fresh_file(tmp, "gauge.json")
        lineage = {"steps": {"gauges": {"last_run": "2026-01-01T00:00:00"}}}
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(lineage)
        gauge_step = next(r for r in results if r["step"] == "gauges")
        # Manifest last_run is preserved (not overridden by filesystem mtime)
        assert gauge_step["last_run"] == "2026-01-01T00:00:00"

    def test_hidden_files_ignored_in_directory(self, lineage_env, monkeypatch):
        """Dotfiles in directories are ignored."""
        from config import config
        tmp = lineage_env["tmp_path"]
        monkeypatch.setattr(config, "get_input_dir", lambda: pathlib.Path(tmp))

        ghd = tmp / "gaugehd"
        ghd.mkdir()
        (ghd / ".DS_Store").write_text("")
        from routes.governance.lineage import _check_staleness

        results = _check_staleness(None)
        ghd_step = next(r for r in results if r["step"] == "gaugehd")
        # Only hidden files = effectively empty
        assert ghd_step["status"] == "missing"


# ══════════════════════════════════════════════════════════════════
# _trace_data helper tests
# ══════════════════════════════════════════════════════════════════


class TestTraceData:
    """Unit tests for _trace_data helper."""

    def test_none_lineage_returns_empty(self):
        from routes.governance.lineage import _trace_data
        assert _trace_data(None, "gauge", "GAUGE-001") == []

    def test_direct_trace_found(self):
        from routes.governance.lineage import _trace_data
        result = _trace_data(SAMPLE_LINEAGE, "gauge", "GAUGE-001")
        assert len(result) == 2
        assert result[0]["step"] == "gauges"
        assert result[1]["step"] == "hazard"

    def test_trace_type_not_found(self):
        from routes.governance.lineage import _trace_data
        result = _trace_data(SAMPLE_LINEAGE, "nonexistent", "X")
        assert result == []

    def test_trace_id_not_found(self):
        from routes.governance.lineage import _trace_data
        result = _trace_data(SAMPLE_LINEAGE, "gauge", "GAUGE-999")
        assert result == []

    def test_fallback_scan_finds_in_outputs(self):
        """When no direct trace exists, scan step outputs for the ID."""
        from routes.governance.lineage import _trace_data
        lineage = {
            "steps": {
                "gauges": {"outputs": ["gauge.json", "GAUGE-ABC.json"]},
                "hazard": {"outputs": ["gaugehc.json"], "inputs": ["GAUGE-ABC.json"]},
            },
        }
        result = _trace_data(lineage, "gauge", "GAUGE-ABC")
        assert len(result) == 2
        roles = {r["role"] for r in result}
        assert "output" in roles
        assert "input" in roles

    def test_fallback_scan_no_match(self):
        from routes.governance.lineage import _trace_data
        lineage = {
            "steps": {
                "gauges": {"outputs": ["gauge.json"]},
            },
        }
        result = _trace_data(lineage, "gauge", "GAUGE-ZZZ")
        assert result == []

    def test_fallback_scan_with_non_string_output(self):
        """Non-string outputs are converted via str() for matching."""
        from routes.governance.lineage import _trace_data
        lineage = {
            "steps": {
                "gauges": {"outputs": [{"file": "GAUGE-007.json", "count": 5}]},
            },
        }
        result = _trace_data(lineage, "gauge", "GAUGE-007")
        assert len(result) == 1
        assert result[0]["role"] == "output"
        # Non-string output is str()-ified in the file field
        assert isinstance(result[0]["file"], str)
