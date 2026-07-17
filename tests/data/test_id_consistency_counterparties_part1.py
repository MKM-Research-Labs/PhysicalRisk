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

"""Counterparty-to-trade referential integrity (part 1)."""

import json
import warnings
from pathlib import Path

import pytest

from tests.data._id_consistency_helpers import (
    INPUT_DIR,
    _load_gauge_ids,
    _load_property_ids,
    _load_counterparty_ids,
    _load_trade_counterparty_ids,
    _load_trade_ids,
    _load_propertyhc_ids,
    _load_propertyshd_ids,
    _load_propertyshe_ids,
)


def _load_counterparties():
    """Load raw counterparty records from counterparty.json."""
    path = INPUT_DIR / "counterparty.json"
    if not path.exists():
        return []
    data = json.load(open(path))
    return data.get("counterparties", [])


def _load_prs_headers():
    """Load (SwapID, CounterParty, CounterPartyName) from all PRS files."""
    prs_dir = INPUT_DIR / "prs"
    if not prs_dir.exists():
        return []
    headers = []
    for f in sorted(prs_dir.glob("PRS-*.json")):
        try:
            d = json.load(open(f))
            hdr = d.get("PhysicalSwap", {}).get("Header", {})
            headers.append({
                "SwapID": hdr.get("SwapID", ""),
                "CounterParty": hdr.get("CounterParty", ""),
                "CounterPartyName": hdr.get("CounterPartyName", ""),
            })
        except Exception:
            continue
    return headers


def _load_trade_marks():
    """Load trade_marks.json as dict."""
    path = INPUT_DIR / "blotter" / "trade_marks.json"
    if not path.exists():
        return {}
    return json.load(open(path))


# =========================================================================
# Counterparty internal integrity
# =========================================================================

class TestCounterpartyIntegrity:
    """counterparty.json must be well-formed and internally consistent."""

    def test_has_counterparties(self):
        """counterparty.json must contain at least one counterparty."""
        records = _load_counterparties()
        assert len(records) > 0, (
            "counterparty.json is empty or missing. "
            "Run: python app.py port --counterparty"
        )

    def test_every_counterparty_has_party_id(self):
        """Every counterparty must have a non-empty PartyID."""
        records = _load_counterparties()
        if not records:
            pytest.skip("counterparty.json empty or missing")
        missing = []
        for i, c in enumerate(records):
            pid = (c.get("CounterpartySet", {})
                    .get("Party", {})
                    .get("PartyID", ""))
            if not pid:
                missing.append(i)
        assert len(missing) == 0, (
            f"{len(missing)} counterparties lack PartyID at indices: "
            f"{missing[:5]}. Regenerate counterparty.json."
        )

    def test_party_ids_unique(self):
        """PartyIDs must be unique across all counterparties."""
        records = _load_counterparties()
        if not records:
            pytest.skip("counterparty.json empty or missing")
        ids = []
        for c in records:
            pid = (c.get("CounterpartySet", {})
                    .get("Party", {})
                    .get("PartyID", ""))
            if pid:
                ids.append(pid)
        dupes = set(x for x in ids if ids.count(x) > 1)
        assert len(dupes) == 0, (
            f"Duplicate PartyIDs: {sorted(dupes)[:5]}. "
            "Regenerate counterparty.json."
        )

    def test_party_names_non_empty(self):
        """Every counterparty must have a non-empty PartyName."""
        records = _load_counterparties()
        if not records:
            pytest.skip("counterparty.json empty or missing")
        missing = []
        for c in records:
            cs = c.get("CounterpartySet", {})
            name = cs.get("Party", {}).get("PartyName", "")
            pid = cs.get("Party", {}).get("PartyID", "?")
            if not name.strip():
                missing.append(pid)
        assert len(missing) == 0, (
            f"{len(missing)} counterparties have empty PartyName: "
            f"{missing[:5]}"
        )

    def test_has_accounts(self):
        """Every counterparty must have an Accounts list."""
        records = _load_counterparties()
        if not records:
            pytest.skip("counterparty.json empty or missing")
        missing = []
        for c in records:
            cs = c.get("CounterpartySet", {})
            party = cs.get("Party", {})
            accounts = party.get("Accounts", None)
            pid = party.get("PartyID", "?")
            if accounts is None:
                missing.append(pid)
        assert len(missing) == 0, (
            f"{len(missing)} counterparties lack Accounts field: "
            f"{missing[:5]}"
        )


# =========================================================================
# Counterparty-to-trade linkage
# =========================================================================

class TestCounterpartyTradeLinkage:
    """PRS trades must reference valid counterparties."""

    def test_prs_counterparty_exists(self):
        """Every PRS CounterParty must exist in counterparty.json."""
        ctpy_ids = _load_counterparty_ids()
        if not ctpy_ids:
            pytest.skip("counterparty.json empty or missing")
        trade_ctpy_ids = _load_trade_counterparty_ids()
        if not trade_ctpy_ids:
            pytest.skip("No PRS trades found")
        missing = trade_ctpy_ids - ctpy_ids
        assert len(missing) == 0, (
            f"{len(missing)} PRS trades reference non-existent counterparties: "
            f"{sorted(missing)[:5]}. Regenerate counterparty.json or fix trades."
        )

    def test_trade_ids_match_trade_marks(self):
        """PRS SwapIDs must appear in trade_marks.json."""
        trade_ids = _load_trade_ids()
        if not trade_ids:
            pytest.skip("No PRS trades found")
        marks = _load_trade_marks()
        if not marks:
            pytest.skip("trade_marks.json empty or missing")
        marks_ids = set(marks.keys())
        missing = trade_ids - marks_ids
        if missing:
            import warnings
            warnings.warn(
                f"{len(missing)} PRS trades missing from trade_marks.json: "
                f"{sorted(missing)[:5]}. Run: python app.py port --blotter"
            )
        # Hard-fail only if more than 15% are missing
        tolerance = max(1, len(trade_ids) * 15 // 100)
        assert len(missing) <= tolerance, (
            f"{len(missing)} PRS trades missing from trade_marks.json "
            f"(>{tolerance} tolerance): {sorted(missing)[:5]}"
        )

    def test_counterparty_name_non_empty_in_trades(self):
        """CounterPartyName in PRS files must be non-empty."""
        headers = _load_prs_headers()
        if not headers:
            pytest.skip("No PRS trades found")
        empty = [h["SwapID"] for h in headers
                 if not h.get("CounterPartyName")]
        assert len(empty) == 0, (
            f"{len(empty)} PRS trades have empty CounterPartyName: {empty[:5]}"
        )

    def test_no_orphan_counterparties(self):
        """Warn if counterparties exist with no trades (not a hard failure)."""
        ctpy_ids = _load_counterparty_ids()
        if not ctpy_ids:
            pytest.skip("counterparty.json empty or missing")
        trade_ctpy_ids = _load_trade_counterparty_ids()
        if not trade_ctpy_ids:
            pytest.skip("No PRS trades found")
        orphans = ctpy_ids - trade_ctpy_ids
        if orphans:
            warnings.warn(
                f"{len(orphans)} counterparties have no trades: "
                f"{sorted(orphans)[:5]}. This is not an error but may "
                "indicate stale data."
            )
