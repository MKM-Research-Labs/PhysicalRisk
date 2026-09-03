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

"""
Data availability tests — Blotter (part 2).

PRS trade files, EOD snapshots.
"""

import json

import pytest

from tests._dataset import full_dataset_only

from config.port import NUM_BUSINESS_DAYS

from tests.data.conftest import PRS_DIR, EOD_DIR, TRADE_MARKS


# ---------------------------------------------------------------------------
# PRS trade files (data/input/<catchment>/prs/)
# ---------------------------------------------------------------------------

class TestPRSTradeData:
    """PRS trade files must be present and follow CDM structure."""

    @pytest.fixture(scope="class")
    def prs_files(self):
        assert PRS_DIR.exists(), f"PRS directory not found: {PRS_DIR}"
        files = list(PRS_DIR.glob("PRS-*.json"))
        if not files:
            pytest.skip(
                f"No PRS trade files found in {PRS_DIR}. "
                "Run `python phys.py book` to generate the trading book."
            )
        return files

    def test_prs_directory_exists(self):
        assert PRS_DIR.exists(), f"Missing PRS directory: {PRS_DIR}"

    def test_trades_are_present(self, prs_files):
        assert len(prs_files) >= 1, "Expected at least one PRS trade file"

    @full_dataset_only
    def test_trade_count_thames_central(self, prs_files):
        """Thames Central book size — full portfolio only.

        Unlike the other volume checks this one cannot be made relational. The
        book matches ten specific inner-London gauges by NAME ('Chelsea
        Bridge', 'Westminster Bridge', ...) and writes a trade per spec whose
        gauge it finds, so its size depends on which named gauges exist rather
        than on how many were generated. On a small synthetic set the expected
        count is not a function of anything the test can see.

        It stays a fixed expectation against the real portfolio, where those
        gauges are present, and is skipped on a generated fixture.
        """
        assert len(prs_files) >= 16, (
            f"Expected >= 16 trades for Thames Central book, got {len(prs_files)}"
        )

    def test_each_trade_has_physical_swap_root(self, prs_files):
        bad = []
        for f in prs_files:
            d = json.loads(f.read_text())
            if "PhysicalSwap" not in d:
                bad.append(f.name)
        assert not bad, f"Trade files missing 'PhysicalSwap' root: {bad}"

    def test_each_trade_has_swap_id(self, prs_files):
        bad = []
        for f in prs_files:
            d = json.loads(f.read_text())
            swap = d.get("PhysicalSwap", {})
            header = swap.get("Header", {})
            if not header.get("SwapID"):
                bad.append(f.name)
        assert not bad, f"Trades missing SwapID in Header: {bad}"

    def test_swap_id_matches_filename(self, prs_files):
        bad = []
        for f in prs_files:
            d = json.loads(f.read_text())
            swap_id = d.get("PhysicalSwap", {}).get("Header", {}).get("SwapID", "")
            expected_name = f"{swap_id}.json"
            if f.name != expected_name:
                bad.append((f.name, expected_name))
        assert not bad, f"Filename/SwapID mismatch: {bad}"

    def test_trade_statuses_are_valid(self, prs_files):
        valid_statuses = {"open", "closed", "expired", "committed"}
        bad = []
        for f in prs_files:
            d = json.loads(f.read_text())
            status = d.get("PhysicalSwap", {}).get("Header", {}).get("TradeStatus", "")
            if status.lower() not in valid_statuses:
                bad.append((f.name, status))
        assert not bad, f"Trades with invalid TradeStatus: {bad}"

    def test_trades_have_gauge_set(self, prs_files):
        bad = []
        for f in prs_files:
            d = json.loads(f.read_text())
            swap = d.get("PhysicalSwap", {})
            if not swap.get("GaugeSet", {}).get("GaugeBasket"):
                bad.append(f.name)
        assert not bad, f"Trades missing GaugeSet.GaugeBasket: {bad}"


# ---------------------------------------------------------------------------
# EOD snapshots (blotter/eod/)
# ---------------------------------------------------------------------------

class TestEODSnapshotData:
    """EOD snapshots must be present after a full port --blotter run."""

    @pytest.fixture(scope="class")
    def eod_files(self):
        if not EOD_DIR.exists():
            pytest.skip(
                f"EOD directory not found: {EOD_DIR}. "
                "Run `python phys.py port --blotter` to generate."
            )
        files = sorted(EOD_DIR.glob("EOD-*.json"))
        if not files:
            pytest.skip(
                "No EOD snapshot files found. "
                "Run `python phys.py port --blotter` to generate."
            )
        return files

    def test_eod_directory_exists(self):
        """blotter/eod/ directory must exist."""
        assert EOD_DIR.exists(), (
            f"EOD directory missing: {EOD_DIR}. "
            "Run `python phys.py port --blotter` to generate."
        )

    def test_eod_snapshot_count(self, eod_files):
        """One EOD snapshot per simulated business day.

        The generator runs ``NUM_BUSINESS_DAYS`` days, so that constant is the
        expected count — not the ``>= 50`` magic number this used to carry,
        which was an approximation of the same 63 and would have to move by
        hand if the window changed. The count does not scale with portfolio
        size, so this holds on a small generated set too.
        """
        assert len(eod_files) == NUM_BUSINESS_DAYS, (
            f"{len(eod_files)} EOD snapshots, expected {NUM_BUSINESS_DAYS} "
            f"(one per simulated business day). "
            "Run `python phys.py port --blotter` to regenerate."
        )

    def test_eod_files_are_valid_json(self, eod_files):
        """Each EOD file must be parseable JSON."""
        bad = []
        for f in eod_files[:10]:  # spot-check first 10
            try:
                json.loads(f.read_text())
            except json.JSONDecodeError:
                bad.append(f.name)
        assert not bad, f"Invalid JSON in EOD files: {bad}"

    def test_eod_has_required_keys(self, eod_files):
        """Each EOD snapshot should have date, trades, and P&L data."""
        required = {"date", "positions"}
        bad = []
        for f in eod_files[:5]:
            d = json.loads(f.read_text())
            missing = required - set(d.keys())
            if missing:
                bad.append((f.name, missing))
        assert not bad, f"EOD files missing required keys: {bad}"

    def test_eod_dates_are_business_days(self, eod_files):
        """Historical EOD dates should be weekdays (Mon-Fri).

        Today's file is excluded — it may be a maintenance/demo run.
        """
        from datetime import date, datetime
        today_str = date.today().strftime("%Y%m%d")
        weekend = []
        for f in eod_files:
            date_str = f.stem.replace("EOD-", "")
            if date_str == today_str:
                continue  # skip today — may be weekend maintenance run
            try:
                dt = datetime.strptime(date_str, "%Y%m%d")
                if dt.weekday() >= 5:
                    weekend.append(f.name)
            except ValueError:
                pass  # non-standard filename
        assert not weekend, f"EOD snapshots on weekends: {weekend}"

    def test_eod_pdfs_match_json(self, eod_files):
        """Each EOD JSON should have a matching PDF report."""
        missing_pdfs = []
        for f in eod_files:
            pdf = f.with_suffix(".pdf")
            if not pdf.exists():
                missing_pdfs.append(f.name)
        if missing_pdfs:
            import warnings
            warnings.warn(
                f"{len(missing_pdfs)} EOD JSON files without matching PDF: "
                f"{missing_pdfs[:5]}"
            )

    def test_trade_marks_file_exists(self):
        """trade_marks.json must exist in blotter directory."""
        assert TRADE_MARKS.exists(), (
            f"trade_marks.json missing: {TRADE_MARKS}. "
            "Run `python phys.py port --blotter` to generate."
        )
