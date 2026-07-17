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

"""Schema field validation for core portfolio entities (part 1)."""

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
