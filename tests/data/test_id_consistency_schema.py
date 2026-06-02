# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Schema field validation for core portfolio entities."""

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

def _gauges():
    path = INPUT_DIR / "gauge.json"
    if not path.exists():
        return []
    data = json.load(open(path))
    return [
        g.get("FloodGauge", g) for g in data.get("flood_gauges", [])
    ]


def _properties():
    path = INPUT_DIR / "property.json"
    if not path.exists():
        return []
    data = json.load(open(path))
    return [p.get("PropertyHeader", {}) for p in data.get("properties", [])]


def _mortgages():
    path = INPUT_DIR / "loan.json"
    if not path.exists():
        return []
    data = json.load(open(path))
    return [m.get("RLoan", {}) for m in data.get("loans", [])]


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
# Gauge schema
# =========================================================================

class TestGaugeSchema:
    """Every gauge record must contain required header and sensor fields."""

    def test_gauge_required_fields(self):
        """Every gauge must have GaugeID, GaugeName, and flood stage thresholds."""
        gauges = _gauges()
        if not gauges:
            pytest.skip("gauge.json empty or missing")
        bad = []
        for g in gauges:
            hdr = g.get("Header", {})
            gid = hdr.get("GaugeID", "")
            gname = hdr.get("GaugeName", "")
            fs = g.get("FloodStage", {}).get("UK", {})
            if not gid or not gname:
                bad.append(f"missing GaugeID/GaugeName: {hdr}")
            elif not all(
                k in fs for k in ("FloodAlert", "FloodWarning", "SevereFloodWarning")
            ):
                bad.append(f"{gid}: missing FloodStage.UK thresholds")
        assert len(bad) == 0, (
            f"{len(bad)} gauges have schema issues: {bad[:5]}. "
            "Regenerate: python app.py port --gauge"
        )

    def test_gauge_has_location_coordinates(self):
        """Every gauge must have latitude and longitude."""
        gauges = _gauges()
        if not gauges:
            pytest.skip("gauge.json empty or missing")
        bad = []
        for g in gauges:
            gid = g.get("Header", {}).get("GaugeID", "?")
            info = g.get("SensorDetails", {}).get("GaugeInformation", {})
            lat = info.get("GaugeLatitude")
            lon = info.get("GaugeLongitude")
            if lat is None or lon is None:
                bad.append(gid)
        assert len(bad) == 0, (
            f"{len(bad)} gauges missing lat/lon in SensorDetails.GaugeInformation: "
            f"{bad[:5]}"
        )

    def test_gauge_has_sensor_stats(self):
        """Every gauge must have SensorStats with HistoricalHighLevel."""
        gauges = _gauges()
        if not gauges:
            pytest.skip("gauge.json empty or missing")
        bad = []
        for g in gauges:
            gid = g.get("Header", {}).get("GaugeID", "?")
            stats = g.get("SensorStats", {})
            if "HistoricalHighLevel" not in stats:
                bad.append(gid)
        assert len(bad) == 0, (
            f"{len(bad)} gauges missing SensorStats.HistoricalHighLevel: "
            f"{bad[:5]}"
        )


# =========================================================================
# Property schema
# =========================================================================

class TestPropertySchema:
    """Every property record must contain required header and valuation fields."""

    def test_property_required_fields(self):
        """Every property must have PropertyID and UPRN in Header.Header."""
        props = _properties()
        if not props:
            pytest.skip("property.json empty or missing")
        bad = []
        for p in props:
            hdr = p.get("Header", {})
            pid = hdr.get("PropertyID", "")
            uprn = hdr.get("UPRN", "")
            if not pid or not uprn:
                bad.append(f"PropertyID={pid!r}, UPRN={uprn!r}")
        assert len(bad) == 0, (
            f"{len(bad)} properties missing PropertyID or UPRN: {bad[:5]}. "
            "Regenerate: python app.py port --property"
        )

    def test_property_has_location(self):
        """Every property must have LatitudeDegrees and LongitudeDegrees."""
        props = _properties()
        if not props:
            pytest.skip("property.json empty or missing")
        bad = []
        for p in props:
            loc = p.get("Location", {})
            pid = p.get("Header", {}).get("PropertyID", "?")
            if loc.get("LatitudeDegrees") is None or loc.get("LongitudeDegrees") is None:
                bad.append(pid)
        assert len(bad) == 0, (
            f"{len(bad)} properties missing lat/lon in Header.Location: "
            f"{bad[:5]}"
        )

    def test_property_has_valuation(self):
        """Every property must have a positive PropertyValue."""
        props = _properties()
        if not props:
            pytest.skip("property.json empty or missing")
        bad = []
        for p in props:
            val = p.get("Valuation", {})
            pid = p.get("Header", {}).get("PropertyID", "?")
            pv = val.get("PropertyValue", 0)
            if not pv or pv <= 0:
                bad.append(f"{pid}: PropertyValue={pv}")
        assert len(bad) == 0, (
            f"{len(bad)} properties have invalid PropertyValue: {bad[:5]}"
        )

    def test_property_has_reference_gauges(self):
        """Every property must have a non-empty ReferenceGauges list."""
        props = _properties()
        if not props:
            pytest.skip("property.json empty or missing")
        bad = []
        for p in props:
            pid = p.get("Header", {}).get("PropertyID", "?")
            rg = p.get("ReferenceGauges", [])
            if not rg:
                bad.append(pid)
        assert len(bad) == 0, (
            f"{len(bad)} properties missing ReferenceGauges: {bad[:5]}. "
            "This breaks flood interpolation."
        )


# =========================================================================
# Mortgage schema
# =========================================================================

class TestMortgageSchema:
    """Every mortgage record must contain required header and financial fields."""

    def test_mortgage_required_header(self):
        """Every mortgage must have MortgageID and PropertyID in Header."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = []
        for m in mortgages:
            hdr = m.get("Header", {})
            mid = hdr.get("RLoanID", "")
            pid = hdr.get("PropertyID", "")
            if not mid or not pid:
                bad.append(f"MortgageID={mid!r}, PropertyID={pid!r}")
        assert len(bad) == 0, (
            f"{len(bad)} mortgages missing MortgageID or PropertyID: {bad[:5]}"
        )

    def test_mortgage_has_financial_terms(self):
        """Every mortgage must have FinancialTerms with OriginalLoan/OriginalTerm."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = []
        for m in mortgages:
            mid = m.get("Header", {}).get("RLoanID", "?")
            ft = m.get("FinancialTerms", {})
            if "OriginalLoan" not in ft or "OriginalTerm" not in ft:
                bad.append(mid)
        assert len(bad) == 0, (
            f"{len(bad)} mortgages missing OriginalLoan/OriginalTerm: {bad[:5]}"
        )

    def test_mortgage_has_borrower_details(self):
        """Every mortgage must have BorrowerDetails with BorrowerAge/BorrowerIncome."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = []
        for m in mortgages:
            mid = m.get("Header", {}).get("RLoanID", "?")
            bd = m.get("BorrowerDetails", {})
            if "BorrowerAge" not in bd or "BorrowerIncome" not in bd:
                bad.append(mid)
        assert len(bad) == 0, (
            f"{len(bad)} mortgages missing BorrowerAge/BorrowerIncome: {bad[:5]}"
        )


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
