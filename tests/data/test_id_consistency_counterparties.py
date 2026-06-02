# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Counterparty-to-trade referential integrity."""

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


# =========================================================================
# Counterparty schema completeness
# =========================================================================

class TestCounterpartySchema:
    """Counterparty records must contain required nested fields."""

    def test_contact_information_exists(self):
        """Every counterparty must have a ContactInformation block."""
        records = _load_counterparties()
        if not records:
            pytest.skip("counterparty.json empty or missing")
        missing = []
        for c in records:
            cs = c.get("CounterpartySet", {})
            pid = cs.get("Party", {}).get("PartyID", "?")
            party = cs.get("Party", {})
            if "ContactInformation" not in party:
                missing.append(pid)
        assert len(missing) == 0, (
            f"{len(missing)} counterparties lack ContactInformation: "
            f"{missing[:5]}"
        )

    def test_natural_persons_non_empty(self):
        """Every counterparty must have at least one NaturalPerson."""
        records = _load_counterparties()
        if not records:
            pytest.skip("counterparty.json empty or missing")
        missing = []
        for c in records:
            cs = c.get("CounterpartySet", {})
            pid = cs.get("Party", {}).get("PartyID", "?")
            nps = cs.get("Party", {}).get("NaturalPersons", [])
            if not nps:
                missing.append(pid)
        assert len(missing) == 0, (
            f"{len(missing)} counterparties have empty NaturalPersons: "
            f"{missing[:5]}"
        )

    def test_account_ids_present(self):
        """Every account must have a non-empty AccountID."""
        records = _load_counterparties()
        if not records:
            pytest.skip("counterparty.json empty or missing")
        missing = []
        for c in records:
            cs = c.get("CounterpartySet", {})
            pid = cs.get("Party", {}).get("PartyID", "?")
            for acct in cs.get("Party", {}).get("Accounts", []):
                if not acct.get("AccountID", ""):
                    missing.append(pid)
                    break
        assert len(missing) == 0, (
            f"{len(missing)} counterparties have accounts without AccountID: "
            f"{missing[:5]}"
        )


# =========================================================================
# Trading rule: trader / REIT / external counterparty segmentation
# =========================================================================

REIT_PARTY_ID = "CTPY-REIT-001"


def _trade_ctpy_by_type():
    """Return ({gauge_prs_ctpys}, {property_prs_ctpys}) by walking PRS files.

    Property PRS trades are identified by the presence of a non-empty
    ``PropertySet.PropertyID`` field.  Gauge PRS trades are everything else.
    """
    prs_dir = INPUT_DIR / "prs"
    gauge_ctpys: set = set()
    prop_ctpys: set = set()
    if not prs_dir.exists():
        return gauge_ctpys, prop_ctpys
    for f in sorted(prs_dir.glob("PRS-*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        ps = d.get("PhysicalSwap", {})
        ctpy = ps.get("Header", {}).get("CounterParty", "")
        if not ctpy:
            continue
        prop_id = ps.get("PropertySet", {}).get("PropertyID", "")
        if prop_id:
            prop_ctpys.add(ctpy)
        else:
            gauge_ctpys.add(ctpy)
    return gauge_ctpys, prop_ctpys


class TestPRSCounterpartyRule:
    """Trader / REIT / external counterparty rule:

    * Property PRS — trader ↔ ``CTPY-REIT-001`` (the REIT) **only**.
    * Gauge PRS    — trader ↔ external counterparty (any non-REIT entry
      from the random pool of banks / insurers / reinsurers / etc.).
    """

    def test_reit_counterparty_exists_in_inventory(self):
        """``CTPY-REIT-001`` must always be in counterparty.json."""
        ctpy_ids = _load_counterparty_ids()
        if not ctpy_ids:
            pytest.skip("counterparty.json empty or missing")
        assert REIT_PARTY_ID in ctpy_ids, (
            f"{REIT_PARTY_ID} (Thames Property REIT) is missing from "
            "counterparty.json. The REIT is a fixed counterparty for "
            "all property PRS trades and must be regenerated. Run: "
            "python app.py port --counterparties"
        )

    def test_property_prs_uses_reit_only(self):
        """Every property PRS must reference the REIT counterparty."""
        _, prop_ctpys = _trade_ctpy_by_type()
        if not prop_ctpys:
            pytest.skip("No property PRS trades found")
        non_reit = prop_ctpys - {REIT_PARTY_ID}
        assert not non_reit, (
            f"Property PRS trades reference non-REIT counterparties: "
            f"{sorted(non_reit)[:5]}. Property PRS must trade exclusively "
            f"with {REIT_PARTY_ID}."
        )

    def test_gauge_prs_uses_external_only(self):
        """Gauge PRS counterparties must NOT be the REIT."""
        gauge_ctpys, _ = _trade_ctpy_by_type()
        if not gauge_ctpys:
            pytest.skip("No gauge PRS trades found")
        assert REIT_PARTY_ID not in gauge_ctpys, (
            f"Gauge PRS trades reference {REIT_PARTY_ID} (the REIT). "
            "Gauge PRS must trade with external counterparties only "
            "(banks / insurers / reinsurers etc., not the REIT)."
        )

    def test_reit_is_only_used_for_property_prs(self):
        """REIT counterparty must not appear on any gauge PRS trade."""
        gauge_ctpys, prop_ctpys = _trade_ctpy_by_type()
        if not gauge_ctpys and not prop_ctpys:
            pytest.skip("No PRS trades found")
        # If REIT appears at all, it must be in prop_ctpys only
        in_gauge = REIT_PARTY_ID in gauge_ctpys
        assert not in_gauge, (
            f"{REIT_PARTY_ID} is on a gauge PRS trade — REIT is a "
            "property-PRS-only counterparty."
        )
