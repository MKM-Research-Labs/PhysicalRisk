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

"""Schema field validation for core portfolio entities (part 2)."""

import json
from pathlib import Path

import pytest

from tests.data._id_consistency_helpers import (
    INPUT_DIR,
    _load_gauge_ids,
    _load_property_ids,
    _load_mortgage_ids,
    _load_mortgage_property_ids,
)


# ---------------------------------------------------------------------------
# Module-level data loaders (run once, cached)
# ---------------------------------------------------------------------------

def _counterparties():
    path = INPUT_DIR / "counterparty.json"
    if not path.exists():
        return []
    data = json.load(open(path))
    return [
        c.get("CounterpartySet", {}) for c in data.get("counterparties", [])
    ]


def _prs_trades():
    prs_dir = INPUT_DIR / "prs"
    if not prs_dir.exists():
        return []
    trades = []
    for f in sorted(prs_dir.glob("PRS-*.json")):
        try:
            d = json.load(open(f))
            trades.append(d.get("PhysicalSwap", {}))
        except Exception:
            continue
    return trades


# =========================================================================
# Counterparty schema
# =========================================================================

class TestCounterpartySchemaFields:
    """Counterparty records must contain required party and account fields."""

    def test_counterparty_required_fields(self):
        """Every counterparty must have PartyID and PartyName in Party."""
        cps = _counterparties()
        if not cps:
            pytest.skip("counterparty.json empty or missing")
        bad = []
        for cp in cps:
            party = cp.get("Party", {})
            pid = party.get("PartyID", "")
            pname = party.get("PartyName", "")
            if not pid or not pname:
                bad.append(f"PartyID={pid!r}, PartyName={pname!r}")
        assert len(bad) == 0, (
            f"{len(bad)} counterparties missing PartyID/PartyName: {bad[:5]}"
        )

    def test_counterparty_accounts_have_ids(self):
        """Every account in every counterparty must have an AccountID."""
        cps = _counterparties()
        if not cps:
            pytest.skip("counterparty.json empty or missing")
        bad = []
        for cp in cps:
            pid = cp.get("Party", {}).get("PartyID", "?")
            for acct in cp.get("Accounts", []):
                if not acct.get("AccountID"):
                    bad.append(pid)
                    break
        assert len(bad) == 0, (
            f"{len(bad)} counterparties have accounts without AccountID: {bad[:5]}"
        )


# =========================================================================
# PRS trade schema
# =========================================================================

class TestPRSTradeSchema:
    """PRS trade files must contain required header, gauge set, and pricing."""

    def test_prs_required_header(self):
        """Every PRS trade must have SwapID, TradeType, CounterParty, TradeStatus."""
        trades = _prs_trades()
        if not trades:
            pytest.skip("No PRS trades found")
        required = ("SwapID", "TradeType", "CounterParty", "TradeStatus")
        bad = []
        for t in trades:
            hdr = t.get("Header", {})
            missing = [k for k in required if not hdr.get(k)]
            if missing:
                sid = hdr.get("SwapID", "?")
                bad.append(f"{sid}: missing {missing}")
        assert len(bad) == 0, (
            f"{len(bad)} PRS trades have incomplete headers: {bad[:5]}"
        )

    def test_prs_has_gauge_set(self):
        """Every PRS trade must have GaugeSet with a non-empty GaugeBasket."""
        trades = _prs_trades()
        if not trades:
            pytest.skip("No PRS trades found")
        bad = []
        for t in trades:
            sid = t.get("Header", {}).get("SwapID", "?")
            basket = t.get("GaugeSet", {}).get("GaugeBasket", [])
            if not basket:
                bad.append(sid)
        assert len(bad) == 0, (
            f"{len(bad)} PRS trades have empty GaugeBasket: {bad[:5]}. "
            "Trades must reference at least one gauge."
        )

    def test_prs_has_pricing(self):
        """Every PRS trade must have Pricing with SpreadBps and NPV."""
        trades = _prs_trades()
        if not trades:
            pytest.skip("No PRS trades found")
        bad = []
        for t in trades:
            sid = t.get("Header", {}).get("SwapID", "?")
            pricing = t.get("Pricing", {})
            if "SpreadBps" not in pricing or "NPV" not in pricing:
                bad.append(sid)
        assert len(bad) == 0, (
            f"{len(bad)} PRS trades missing SpreadBps/NPV in Pricing: {bad[:5]}"
        )
