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

"""Counterparty-to-trade referential integrity (part 2)."""

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
            "python phys.py port --counterparties"
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
