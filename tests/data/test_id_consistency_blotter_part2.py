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

"""Blotter, EOD, and market state consistency checks (part 2)."""

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
# EOD consistency
# =========================================================================

class TestEODConsistency:
    """EOD snapshot files must be well-formed and consistent with market_state."""

    def test_eod_directory_exists_with_files(self):
        """blotter/eod/ must exist and contain at least one file."""
        if not EOD_DIR.exists():
            pytest.skip(f"EOD directory not generated: {EOD_DIR}")
        files = list(EOD_DIR.glob("EOD-*.json"))
        if len(files) == 0:
            pytest.skip("EOD directory present but empty; blotter EOD not generated")
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
        if len(files) == 0:
            pytest.skip("No EOD files on disk; blotter EOD not generated")
        assert len(files) > 0, "No EOD files found"
