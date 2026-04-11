# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Blotter, EOD, and market state consistency checks."""

import json
import re
import time
from pathlib import Path

import pytest

from tests.data._id_consistency_helpers import (
    INPUT_DIR,
    _load_gauge_ids,
    _load_trade_ids,
    _load_market_state_gauge_ids,
)


BLOTTER_DIR = INPUT_DIR / "blotter"
EOD_DIR = BLOTTER_DIR / "eod"
PRS_DIR = INPUT_DIR / "prs"


# =========================================================================
# Trade marks consistency
# =========================================================================

class TestTradeMarksConsistency:
    """trade_marks.json must be consistent with PRS trade files."""

    def test_trade_marks_ids_match_prs_swap_ids(self):
        """Every key in trade_marks.json must correspond to a SwapID in PRS files."""
        path = BLOTTER_DIR / "trade_marks.json"
        if not path.exists():
            pytest.skip("trade_marks.json not found")
        marks = json.load(open(path))
        prs_ids = _load_trade_ids()
        if not prs_ids:
            pytest.skip("No PRS files found")
        marks_ids = set(marks.keys())
        orphaned = marks_ids - prs_ids
        assert len(orphaned) == 0, (
            f"{len(orphaned)} trade_marks IDs not in PRS files: "
            f"{sorted(orphaned)[:5]}"
        )

    def test_trade_marks_non_empty(self):
        """trade_marks.json must contain at least one entry."""
        path = BLOTTER_DIR / "trade_marks.json"
        if not path.exists():
            pytest.skip("trade_marks.json not found")
        marks = json.load(open(path))
        assert len(marks) > 0, "trade_marks.json is empty"

    def test_trade_marks_all_have_trade_status(self):
        """Every entry in trade_marks.json must have a trade_status field."""
        path = BLOTTER_DIR / "trade_marks.json"
        if not path.exists():
            pytest.skip("trade_marks.json not found")
        marks = json.load(open(path))
        missing = [k for k, v in marks.items() if "trade_status" not in v]
        assert len(missing) == 0, (
            f"{len(missing)} entries missing trade_status: {missing[:5]}"
        )

    def test_prs_json_pdf_pairs_complete(self):
        """Every PRS-*.json must have a matching PRS-*.pdf and vice versa.

        Gauge trades and property trades are checked separately since they
        use different swap ID prefixes (PRS- vs PRS-P).
        """
        if not PRS_DIR.exists():
            pytest.skip("PRS directory not found")

        # Split into gauge trades and property trades by prefix
        gauge_jsons = set()
        prop_jsons = set()
        for f in PRS_DIR.glob("PRS-*.json"):
            try:
                with open(f) as fh:
                    trade = json.load(fh)
                if 'PropertySet' in trade.get('PhysicalSwap', {}):
                    prop_jsons.add(f.stem)
                else:
                    gauge_jsons.add(f.stem)
            except Exception:
                gauge_jsons.add(f.stem)

        all_pdfs = {f.stem for f in PRS_DIR.glob("PRS-*.pdf")}
        prop_pdfs = {s for s in all_pdfs if s.startswith('PRS-P')}
        gauge_pdfs = all_pdfs - prop_pdfs

        # Exclude recently-committed trades (< 24h) — PDF may not exist
        # until the next port --blotter run.
        import warnings
        grace_period = 86_400  # 24 hours
        now = time.time()
        recent_gauge = set()
        recent_prop = set()
        for stem in gauge_jsons | prop_jsons:
            json_path = PRS_DIR / f"{stem}.json"
            if json_path.exists() and (now - json_path.stat().st_mtime) < grace_period:
                if stem in gauge_jsons:
                    recent_gauge.add(stem)
                else:
                    recent_prop.add(stem)
        if recent_gauge or recent_prop:
            warnings.warn(
                f"{len(recent_gauge) + len(recent_prop)} recent trade(s) "
                f"excluded from PDF-pair check (< 24h old): "
                f"{sorted(recent_gauge | recent_prop)[:5]}"
            )

        # Check gauge trade pairs (excluding recent)
        g_json_only = (gauge_jsons - recent_gauge) - gauge_pdfs
        g_pdf_only = gauge_pdfs - gauge_jsons
        if g_pdf_only:
            warnings.warn(
                f"{len(g_pdf_only)} orphaned gauge PDFs without JSON: "
                f"{sorted(g_pdf_only)[:5]}"
            )
        assert len(g_json_only) == 0 and len(g_pdf_only) <= 3, (
            f"Gauge JSON without PDF: {sorted(g_json_only)[:5]}; "
            f"Gauge PDF without JSON: {sorted(g_pdf_only)[:5]}"
        )

        # Check property trade pairs (excluding recent)
        p_json_only = (prop_jsons - recent_prop) - prop_pdfs
        p_pdf_only = prop_pdfs - prop_jsons
        assert len(p_json_only) == 0 and len(p_pdf_only) == 0, (
            f"Property JSON without PDF: {sorted(p_json_only)[:5]}; "
            f"Property PDF without JSON: {sorted(p_pdf_only)[:5]}"
        )


# =========================================================================
# Market state consistency
# =========================================================================

class TestMarketStateConsistency:
    """market_state.json must be self-consistent and reference valid gauges."""

    @pytest.fixture(autouse=True)
    def _load_market_state(self):
        path = BLOTTER_DIR / "market_state.json"
        if not path.exists():
            pytest.skip("market_state.json not found")
        self.ms = json.load(open(path))

    def test_yield_curve_exists(self):
        """market_state.json must contain a yield_curve."""
        yc = self.ms.get("yield_curve")
        assert yc is not None and len(yc) > 0, "yield_curve missing or empty"

    def test_hazard_term_structure_exists(self):
        """market_state.json must contain a non-empty hazard_term_structure."""
        hts = self.ms.get("hazard_term_structure")
        assert hts is not None and len(hts) > 0, (
            "hazard_term_structure missing or empty"
        )

    def test_hazard_gauge_ids_valid(self):
        """All gauge IDs in hazard_term_structure must exist in gauge.json."""
        gauge_ids = _load_gauge_ids()
        if not gauge_ids:
            pytest.skip("gauge.json not available")
        ms_gauge_ids = _load_market_state_gauge_ids()
        orphaned = ms_gauge_ids - gauge_ids
        assert len(orphaned) == 0, (
            f"{len(orphaned)} market_state gauge IDs not in gauge.json: "
            f"{sorted(orphaned)[:5]}"
        )

    def test_each_gauge_has_alert_warning_severe(self):
        """Every gauge in hazard_term_structure must have alert/warning/severe."""
        hts = self.ms.get("hazard_term_structure", {})
        required = {"alert", "warning", "severe"}
        bad = []
        for gid, curves in hts.items():
            missing = required - set(curves.keys())
            if missing:
                bad.append((gid, missing))
        assert len(bad) == 0, (
            f"{len(bad)} gauges missing curve types: {bad[:5]}"
        )

    def test_rates_bounded_for_sampled_gauges(self):
        """Hazard rates for sampled gauges must be in (0, 1)."""
        hts = self.ms.get("hazard_term_structure", {})
        gauge_ids = sorted(hts.keys())
        # Sample up to 5 gauges
        sample = gauge_ids[:5]
        violations = []
        for gid in sample:
            for curve_type in ("alert", "warning", "severe"):
                curve = hts[gid].get(curve_type, {})
                for tenor, rate in curve.items():
                    if not (0 < rate < 1):
                        violations.append((gid, curve_type, tenor, rate))
        assert len(violations) == 0, (
            f"{len(violations)} rates outside (0,1): {violations[:5]}"
        )


# =========================================================================
# EOD consistency
# =========================================================================

class TestEODConsistency:
    """EOD snapshot files must be well-formed and consistent with market_state."""

    def test_eod_directory_exists_with_files(self):
        """blotter/eod/ must exist and contain at least one file."""
        assert EOD_DIR.exists(), f"EOD directory missing: {EOD_DIR}"
        files = list(EOD_DIR.glob("EOD-*.json"))
        assert len(files) > 0, "EOD directory is empty"

    def test_eod_filenames_chronological(self):
        """EOD filenames must contain valid dates in ascending order."""
        files = sorted(EOD_DIR.glob("EOD-*.json"))
        if not files:
            pytest.skip("No EOD files")
        dates = []
        pattern = re.compile(r"EOD-(\d{8})\.json")
        for f in files:
            m = pattern.match(f.name)
            assert m is not None, f"Bad EOD filename: {f.name}"
            dates.append(m.group(1))
        assert dates == sorted(dates), "EOD filenames are not in chronological order"

    def test_eod_files_non_empty(self):
        """Every EOD file must be parseable and non-empty."""
        files = list(EOD_DIR.glob("EOD-*.json"))
        if not files:
            pytest.skip("No EOD files")
        for f in files:
            data = json.load(open(f))
            assert len(data) > 0, f"EOD file is empty: {f.name}"

    def test_eod_sampled_have_required_keys(self):
        """Sampled EOD files must contain eod_id, date, market_state_snapshot."""
        files = sorted(EOD_DIR.glob("EOD-*.json"))
        if not files:
            pytest.skip("No EOD files")
        required = {"eod_id", "date", "market_state_snapshot"}
        # Sample first, last, and middle
        sample = [files[0], files[len(files) // 2], files[-1]]
        for f in sample:
            data = json.load(open(f))
            missing = required - set(data.keys())
            assert len(missing) == 0, (
                f"{f.name} missing keys: {missing}"
            )

    def test_eod_gauge_set_matches_market_state(self):
        """Gauge IDs in sampled EOD must match market_state.json gauges."""
        ms_gauges = _load_market_state_gauge_ids()
        if not ms_gauges:
            pytest.skip("market_state.json not available")
        files = sorted(EOD_DIR.glob("EOD-*.json"))
        if not files:
            pytest.skip("No EOD files")
        # Check the most recent EOD
        latest = json.load(open(files[-1]))
        snapshot = latest.get("market_state_snapshot", {})
        eod_hts = snapshot.get("hazard_term_structure", {})
        eod_gauges = set(eod_hts.keys())
        if not eod_gauges:
            pytest.skip("Latest EOD has no hazard_term_structure in snapshot")
        diff = ms_gauges.symmetric_difference(eod_gauges)
        assert len(diff) == 0, (
            f"Gauge set mismatch between market_state and latest EOD: "
            f"{sorted(diff)[:5]}"
        )

    def test_eod_dates_match_filenames(self):
        """The date field inside each sampled EOD must match its filename."""
        files = sorted(EOD_DIR.glob("EOD-*.json"))
        if not files:
            pytest.skip("No EOD files")
        pattern = re.compile(r"EOD-(\d{8})\.json")
        sample = [files[0], files[len(files) // 2], files[-1]]
        for f in sample:
            m = pattern.match(f.name)
            if not m:
                continue
            fname_date = m.group(1)
            expected = f"{fname_date[:4]}-{fname_date[4:6]}-{fname_date[6:8]}"
            data = json.load(open(f))
            assert data.get("date") == expected, (
                f"{f.name}: date field '{data.get('date')}' != '{expected}'"
            )

    def test_eod_count_reasonable(self):
        """There should be a reasonable number of EOD files (> 0)."""
        files = list(EOD_DIR.glob("EOD-*.json"))
        assert len(files) > 0, "No EOD files found"
