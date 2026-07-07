"""Characterisation tests — the lineage subsystem is file-backend coupled.

Context: the platform is migrating portfolio data from per-catchment ``.json``
files to a PostgreSQL database, reached only through the ``database`` seam
(``MKM_REPO_BACKEND=pg``). The lineage subsystem (``src/lineage/``) has *no*
awareness of that seam — it populates and validates the manifest purely by
hashing ``.json`` files and directories on disk under ``config.get_input_dir()``
(``repair_manifest`` scans disk; ``_live_hash`` / ``_outputs_exist`` stat disk).

These tests pin down that honest current behaviour: when the portfolio lives in
the seam (here an in-memory backend, which stands in for the pg backend — neither
writes ``.json`` to disk) the lineage layer is **blind to it**. Every step is
"missing outputs", live hashes are ``None``, and the manifest cannot be built.

They are deliberately written to PASS today and to FAIL the moment lineage grows
a seam-backed provenance path. That failure is the signal to update this module
alongside the migration decision (see the review's recommendation #3: does
provenance hashing move to hashing DB rows, or does lineage stay file-only and
get scoped out under pg?). Until that decision lands, this module is the single
place the suite acknowledges the gap instead of silently asserting a file world
that the pg backend no longer reflects.
"""

from pathlib import Path
from unittest.mock import patch

import database
from db_helpers import memory_catchment

from lineage.manifest import repair_manifest
from lineage.validation._helpers import _live_hash, _outputs_exist


def _seed_seam_gauges(catchment: str = "thames") -> None:
    """Write a minimal gauge portfolio through the seam (no disk artifacts)."""
    database.save_gauges(catchment, {"gauges": [{"gauge_id": "GAUGE-0001"}]})


def test_repair_manifest_blind_to_seam_backed_data(tmp_path):
    """``repair_manifest`` scans disk, so seam-backed data is invisible: no step
    is repaired even though the seam holds the portfolio."""
    data_dir = tmp_path / "input"
    data_dir.mkdir()
    lineage_json = tmp_path / "data_lineage.json"

    with patch("lineage.manifest._core.LINEAGE_PATH", lineage_json):
        with memory_catchment("thames"):
            _seed_seam_gauges()
            # Data is now in the in-memory seam; nothing is on disk at data_dir.
            result = repair_manifest(data_dir=data_dir)

    assert result["repaired"] == []          # lineage cannot see the seam data
    assert len(result["skipped"]) > 0        # every step is "outputs missing"


def test_live_hash_none_for_seam_backed_artifact(tmp_path):
    """The freshness disk-hash fallback returns ``None`` for a seam-backed
    artifact — it only knows how to hash files on disk."""
    with memory_catchment("thames"):
        _seed_seam_gauges()
        assert _live_hash("gauge.json", data_dir=tmp_path) is None


def test_outputs_exist_false_for_seam_backed_step(tmp_path):
    """``_outputs_exist`` reports a step's outputs as absent when they live in the
    seam rather than on disk."""
    with memory_catchment("thames"):
        _seed_seam_gauges()
        assert _outputs_exist("gauges", tmp_path) is False
