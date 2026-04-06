# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""File naming conventions and directory file count consistency."""

import json
import re
from pathlib import Path

import pytest

from tests.data._id_consistency_helpers import (
    INPUT_DIR,
    _load_gauge_ids,
    _load_property_ids,
)


# =========================================================================
# Directory file counts
# =========================================================================

class TestDirectoryFileCounts:
    """Data directories must contain the expected number of files."""

    def test_gaugets_count_matches_gauge_count(self):
        """gaugets/ should have one file per gauge (real + synthetic)."""
        gaugets_dir = INPUT_DIR / "gaugets"
        if not gaugets_dir.exists():
            pytest.skip("gaugets/ not generated yet")
        gauge_ids = _load_gauge_ids()
        if not gauge_ids:
            pytest.skip("gauge.json empty or missing")
        # gaugets/ contains both GAUGE-* and SYNTH-* files
        gaugets_count = len(list(gaugets_dir.glob("*.json")))
        assert gaugets_count >= len(gauge_ids), (
            f"gaugets/ has {gaugets_count} files but gauge.json has "
            f"{len(gauge_ids)} gauges. Regenerate: python app.py port --stressm"
        )

    def test_propertyts_count_within_property_range(self):
        """propertyts/ file count should match property.json (+-1 for index)."""
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        prop_ids = _load_property_ids()
        if not prop_ids:
            pytest.skip("property.json empty or missing")
        pts_count = len(list(pts_dir.glob("PROP-*.json")))
        assert abs(pts_count - len(prop_ids)) <= 1, (
            f"propertyts/ has {pts_count} files but property.json has "
            f"{len(prop_ids)} properties (tolerance +-1). "
            f"Regenerate: python app.py port --propertyts"
        )

    def test_propertytsd_count_matches_propertyts(self):
        """propertytsd/ file count should match propertyts/."""
        pts_dir = INPUT_DIR / "propertyts"
        ptsd_dir = INPUT_DIR / "propertytsd"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        if not ptsd_dir.exists():
            pytest.skip("propertytsd/ not generated yet")
        pts_count = len(list(pts_dir.glob("PROP-*.json")))
        ptsd_count = len(list(ptsd_dir.glob("PROP-*.json")))
        assert pts_count == ptsd_count, (
            f"propertytsd/ has {ptsd_count} files but propertyts/ has "
            f"{pts_count}. Regenerate: python app.py port --propertytsd"
        )

    def test_propertytse_count_matches_propertyts(self):
        """propertytse/ file count should match propertyts/."""
        pts_dir = INPUT_DIR / "propertyts"
        ptse_dir = INPUT_DIR / "propertytse"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        if not ptse_dir.exists():
            pytest.skip("propertytse/ not generated yet")
        pts_count = len(list(pts_dir.glob("PROP-*.json")))
        ptse_count = len(list(ptse_dir.glob("PROP-*.json")))
        assert pts_count == ptse_count, (
            f"propertytse/ has {ptse_count} files but propertyts/ has "
            f"{pts_count}. Regenerate: python app.py port --propertytse"
        )

    def test_sequence_gauge_count_close_to_gauge_count(self):
        """sequence_gauge/ file count should be within +-5 of gauge count."""
        seq_dir = INPUT_DIR / "sequence_gauge"
        if not seq_dir.exists():
            pytest.skip("sequence_gauge/ not generated yet")
        gauge_ids = _load_gauge_ids()
        if not gauge_ids:
            pytest.skip("gauge.json empty or missing")
        # sequence_gauge/ contains both GAUGE-* and SYNTH-* files
        seq_count = len(list(seq_dir.glob("*.json")))
        assert abs(seq_count - len(gauge_ids)) <= 5, (
            f"sequence_gauge/ has {seq_count} files but gauge.json has "
            f"{len(gauge_ids)} gauges (tolerance +-5). "
            f"Regenerate: python app.py port --sequence"
        )

    def test_gaugehd_count_within_gauge_range(self):
        """gaugehd/ file count should not exceed gauge count (partial OK)."""
        ghd_dir = INPUT_DIR / "gaugehd"
        if not ghd_dir.exists():
            pytest.skip("gaugehd/ not generated yet")
        gauge_ids = _load_gauge_ids()
        if not gauge_ids:
            pytest.skip("gauge.json empty or missing")
        ghd_count = len(list(ghd_dir.glob("gauge_GAUGE-*_hd.json")))
        assert ghd_count <= len(gauge_ids), (
            f"gaugehd/ has {ghd_count} files but gauge.json only has "
            f"{len(gauge_ids)} gauges. Stale files present — clean up."
        )


# =========================================================================
# File naming conventions
# =========================================================================

class TestFileNamingConventions:
    """All data files must follow standard naming patterns."""

    _GAUGE_HD_PAT = re.compile(r"^gauge_(GAUGE|SYNTH)-[0-9a-f]{8}_hd\.json$")
    _GAUGE_TS_PAT = re.compile(r"^(GAUGE|SYNTH)-[0-9a-f]{8}\.json$")
    _PROP_TS_PAT = re.compile(r"^PROP-[0-9a-f]{8}\.json$")
    _SEQ_GAUGE_PAT = re.compile(r"^(GAUGE|SYNTH)-[0-9a-f]{8}\.json$")
    _PRS_PAT = re.compile(r"^PRS-[0-9a-fA-F]{8}\.(json|pdf)$")
    _EOD_PAT = re.compile(r"^EOD-\d{8}\.json$")

    def test_gaugehd_naming_pattern(self):
        """gaugehd/ files must match gauge_GAUGE-[hex8]_hd.json."""
        ghd_dir = INPUT_DIR / "gaugehd"
        if not ghd_dir.exists():
            pytest.skip("gaugehd/ not generated yet")
        files = list(ghd_dir.glob("*.json"))
        if not files:
            pytest.skip("gaugehd/ is empty")
        bad = [f.name for f in files if not self._GAUGE_HD_PAT.match(f.name)]
        assert len(bad) == 0, (
            f"{len(bad)} files in gaugehd/ violate naming convention: "
            f"{bad[:5]}. Expected: gauge_GAUGE-[hex8]_hd.json"
        )

    def test_gaugets_naming_pattern(self):
        """gaugets/ files must match GAUGE-[hex8].json."""
        gts_dir = INPUT_DIR / "gaugets"
        if not gts_dir.exists():
            pytest.skip("gaugets/ not generated yet")
        files = list(gts_dir.glob("*.json"))
        if not files:
            pytest.skip("gaugets/ is empty")
        bad = [f.name for f in files if not self._GAUGE_TS_PAT.match(f.name)]
        assert len(bad) == 0, (
            f"{len(bad)} files in gaugets/ violate naming convention: "
            f"{bad[:5]}. Expected: GAUGE-[hex8].json"
        )

    def test_propertyts_naming_pattern(self):
        """propertyts/ files must match PROP-[hex8].json."""
        pts_dir = INPUT_DIR / "propertyts"
        if not pts_dir.exists():
            pytest.skip("propertyts/ not generated yet")
        files = list(pts_dir.glob("*.json"))
        if not files:
            pytest.skip("propertyts/ is empty")
        # Exclude known summary/index files
        _SUMMARY_FILES = {"portfolio_flood_summary.json"}
        bad = [f.name for f in files
               if f.name not in _SUMMARY_FILES
               and not self._PROP_TS_PAT.match(f.name)]
        assert len(bad) == 0, (
            f"{len(bad)} files in propertyts/ violate naming convention: "
            f"{bad[:5]}. Expected: PROP-[hex8].json"
        )

    def test_prs_naming_pattern(self):
        """prs/ files must match PRS-[hex8].(json|pdf)."""
        prs_dir = INPUT_DIR / "prs"
        if not prs_dir.exists():
            pytest.skip("prs/ not generated yet")
        files = list(prs_dir.iterdir())
        if not files:
            pytest.skip("prs/ is empty")
        bad = [f.name for f in files if f.is_file() and not self._PRS_PAT.match(f.name)]
        assert len(bad) == 0, (
            f"{len(bad)} files in prs/ violate naming convention: "
            f"{bad[:5]}. Expected: PRS-[hex8].(json|pdf)"
        )

    def test_eod_naming_pattern(self):
        """blotter/eod/ files must match EOD-YYYYMMDD.json."""
        eod_dir = INPUT_DIR / "blotter" / "eod"
        if not eod_dir.exists():
            pytest.skip("blotter/eod/ not generated yet")
        files = list(eod_dir.glob("*.json"))
        if not files:
            pytest.skip("blotter/eod/ is empty")
        bad = [f.name for f in files if not self._EOD_PAT.match(f.name)]
        assert len(bad) == 0, (
            f"{len(bad)} files in blotter/eod/ violate naming convention: "
            f"{bad[:5]}. Expected: EOD-YYYYMMDD.json"
        )


# =========================================================================
# Stress storms sampled validation
# =========================================================================

class TestStressStormsSampled:
    """Stress storm files must exist and follow naming/schema conventions."""

    _STORM_PAT = re.compile(r"^STORM-[0-9a-f]{8}\.json$")

    def test_stress_storms_dir_exists(self):
        """stress_storms/ must exist and be non-empty."""
        storms_dir = INPUT_DIR / "stress_storms"
        if not storms_dir.exists():
            pytest.skip("stress_storms/ not generated yet")
        files = list(storms_dir.glob("STORM-*.json"))
        assert len(files) > 0, (
            "stress_storms/ exists but is empty. "
            "Regenerate: python app.py stress --storms"
        )

    def test_stress_storms_sample_naming(self):
        """Sample 50 storm files — all must match STORM-[hex8].json."""
        storms_dir = INPUT_DIR / "stress_storms"
        if not storms_dir.exists():
            pytest.skip("stress_storms/ not generated yet")
        files = sorted(storms_dir.glob("STORM-*.json"))
        if not files:
            pytest.skip("stress_storms/ is empty")
        step = max(1, len(files) // 50)
        sample = files[::step][:50]
        bad = [f.name for f in sample if not self._STORM_PAT.match(f.name)]
        assert len(bad) == 0, (
            f"{len(bad)}/50 sampled storm files violate naming: "
            f"{bad[:5]}. Expected: STORM-[hex8].json"
        )

    def test_stress_storms_sample_valid_json(self):
        """Sample 20 storm files — all must be valid JSON with storm_id."""
        storms_dir = INPUT_DIR / "stress_storms"
        if not storms_dir.exists():
            pytest.skip("stress_storms/ not generated yet")
        files = sorted(storms_dir.glob("STORM-*.json"))
        if not files:
            pytest.skip("stress_storms/ is empty")
        step = max(1, len(files) // 20)
        sample = files[::step][:20]
        bad = []
        for f in sample:
            try:
                d = json.load(open(f))
                if "storm_id" not in d:
                    bad.append(f"{f.name}: missing storm_id key")
            except json.JSONDecodeError as e:
                bad.append(f"{f.name}: invalid JSON — {e}")
        assert len(bad) == 0, (
            f"{len(bad)}/20 sampled storm files have issues: {bad[:5]}"
        )

    def test_stress_storms_sample_ids_match_filenames(self):
        """Sample 20 — internal storm_id must match filename stem."""
        storms_dir = INPUT_DIR / "stress_storms"
        if not storms_dir.exists():
            pytest.skip("stress_storms/ not generated yet")
        files = sorted(storms_dir.glob("STORM-*.json"))
        if not files:
            pytest.skip("stress_storms/ is empty")
        step = max(1, len(files) // 20)
        sample = files[::step][:20]
        mismatched = []
        for f in sample:
            try:
                d = json.load(open(f))
                internal_id = d.get("storm_id", "")
                if internal_id != f.stem:
                    mismatched.append(
                        f"{f.name}: internal={internal_id}, file={f.stem}"
                    )
            except Exception:
                continue
        assert len(mismatched) == 0, (
            f"{len(mismatched)}/20 storm files have mismatched IDs: "
            f"{mismatched[:5]}. Internal storm_id must equal filename stem."
        )
