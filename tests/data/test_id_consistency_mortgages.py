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

"""Mortgage-to-property referential integrity and financial term validation."""

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


def _mortgages():
    """Load all mortgage records from loan.json."""
    path = INPUT_DIR / "loan.json"
    if not path.exists():
        return []
    data = json.load(open(path))
    return [m.get("RLoan", {}) for m in data.get("loans", [])]


# =========================================================================
# Mortgage-to-property linkage
# =========================================================================

class TestMortgagePropertyLinkage:
    """Mortgages must reference valid properties with no orphans or duplicates."""

    def test_mortgage_json_has_mortgages(self):
        """loan.json must contain at least one mortgage."""
        ids = _load_mortgage_ids()
        assert len(ids) > 0, "loan.json is empty or missing"

    def test_every_mortgage_has_property_id(self):
        """Every mortgage must have a non-empty PropertyID."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = []
        for m in mortgages:
            hdr = m.get("Header", {})
            mid = hdr.get("RLoanID", "?")
            pid = hdr.get("PropertyID", "")
            if not pid:
                bad.append(mid)
        assert len(bad) == 0, (
            f"{len(bad)} mortgages have empty PropertyID: {bad[:5]}. "
            "Regenerate: python phys.py port --mortgage"
        )

    def test_mortgage_property_ids_exist_in_property_json(self):
        """All PropertyIDs referenced by mortgages must exist in property.json."""
        mort_pids = _load_mortgage_property_ids()
        prop_ids = _load_property_ids()
        if not mort_pids:
            pytest.skip("No mortgage property IDs loaded")
        if not prop_ids:
            pytest.skip("property.json empty or missing")
        assert mort_pids <= prop_ids, (
            f"{len(mort_pids - prop_ids)} mortgage PropertyIDs not in property.json: "
            f"{sorted(mort_pids - prop_ids)[:5]}. "
            "Regenerate: python phys.py port --mortgage"
        )

    def test_no_orphan_mortgages(self):
        """No mortgage should reference a property that does not exist."""
        mort_pids = _load_mortgage_property_ids()
        prop_ids = _load_property_ids()
        if not mort_pids:
            pytest.skip("No mortgage property IDs loaded")
        if not prop_ids:
            pytest.skip("property.json empty or missing")
        orphan = mort_pids - prop_ids
        assert len(orphan) == 0, (
            f"{len(orphan)} orphan mortgages reference non-existent properties: "
            f"{sorted(orphan)[:5]}. Mortgage data is stale."
        )

    def test_mortgage_ids_unique(self):
        """MortgageIDs must be unique across the portfolio."""
        path = INPUT_DIR / "loan.json"
        if not path.exists():
            pytest.skip("loan.json not found")
        data = json.load(open(path))
        all_ids = [
            m.get("RLoan", {}).get("Header", {}).get("RLoanID", "")
            for m in data.get("loans", [])
        ]
        all_ids = [i for i in all_ids if i]
        dupes = [i for i in all_ids if all_ids.count(i) > 1]
        assert len(set(dupes)) == 0, (
            f"{len(set(dupes))} duplicate MortgageIDs found: "
            f"{sorted(set(dupes))[:5]}"
        )


# =========================================================================
# Mortgage financial terms
# =========================================================================

class TestMortgageFinancialTerms:
    """Financial term fields must be present and within valid ranges."""

    def test_every_mortgage_has_financial_terms(self):
        """Every mortgage must have a FinancialTerms key."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = [
            m.get("Header", {}).get("RLoanID", "?")
            for m in mortgages
            if "FinancialTerms" not in m
        ]
        assert len(bad) == 0, (
            f"{len(bad)} mortgages missing FinancialTerms: {bad[:5]}"
        )

    def test_ltv_range_valid(self):
        """OriginalLTV must be 0 < LTV <= 100."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = []
        for m in mortgages:
            mid = m.get("Header", {}).get("RLoanID", "?")
            ltv = m.get("FinancialTerms", {}).get("OriginalLTV")
            if ltv is None:
                continue  # separate test for presence
            if not (0 < ltv <= 100):
                bad.append(f"{mid}: LTV={ltv}")
        assert len(bad) == 0, (
            f"{len(bad)} mortgages have out-of-range LTV: {bad[:5]}"
        )

    def test_loan_amount_positive(self):
        """OriginalLoan must be > 0."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = []
        for m in mortgages:
            mid = m.get("Header", {}).get("RLoanID", "?")
            loan = m.get("FinancialTerms", {}).get("OriginalLoan", 0)
            if loan <= 0:
                bad.append(f"{mid}: OriginalLoan={loan}")
        assert len(bad) == 0, (
            f"{len(bad)} mortgages have non-positive OriginalLoan: {bad[:5]}"
        )

    def test_loan_term_positive(self):
        """OriginalTerm must be > 0."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = []
        for m in mortgages:
            mid = m.get("Header", {}).get("RLoanID", "?")
            term = m.get("FinancialTerms", {}).get("OriginalTerm", 0)
            if term <= 0:
                bad.append(f"{mid}: OriginalTerm={term}")
        assert len(bad) == 0, (
            f"{len(bad)} mortgages have non-positive OriginalTerm: {bad[:5]}"
        )

    def test_outstanding_balance_non_negative(self):
        """OutstandingBalance must be >= 0."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = []
        for m in mortgages:
            mid = m.get("Header", {}).get("RLoanID", "?")
            bal = m.get("FinancialTerms", {}).get("OutstandingBalance")
            if bal is not None and bal < 0:
                bad.append(f"{mid}: OutstandingBalance={bal}")
        assert len(bad) == 0, (
            f"{len(bad)} mortgages have negative OutstandingBalance: {bad[:5]}"
        )


# =========================================================================
# Mortgage count and coverage
# =========================================================================

class TestMortgageCount:
    """Mortgage count and coverage validations."""

    def test_mortgage_count_matches_property_count(self):
        """Mortgage count should be close to property count."""
        mort_ids = _load_mortgage_ids()
        prop_ids = _load_property_ids()
        if not mort_ids:
            pytest.skip("loan.json empty or missing")
        if not prop_ids:
            pytest.skip("property.json empty or missing")
        # Allow some tolerance — not every property needs a mortgage
        ratio = len(mort_ids) / len(prop_ids)
        assert 0.5 <= ratio <= 2.0, (
            f"Mortgage/property ratio is {ratio:.2f} "
            f"({len(mort_ids)} mortgages, {len(prop_ids)} properties). "
            f"Expected roughly 1:1."
        )

    def test_mortgage_property_coverage(self):
        """Warn if some properties lack a mortgage (non-fatal)."""
        mort_pids = _load_mortgage_property_ids()
        prop_ids = _load_property_ids()
        if not mort_pids or not prop_ids:
            pytest.skip("loan.json or property.json missing")
        uncovered = prop_ids - mort_pids
        if uncovered:
            import warnings
            warnings.warn(
                f"{len(uncovered)}/{len(prop_ids)} properties have no mortgage. "
                f"Sample: {sorted(uncovered)[:3]}"
            )

    def test_currency_is_gbp(self):
        """All mortgages must be denominated in GBP."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = []
        for m in mortgages:
            mid = m.get("Header", {}).get("RLoanID", "?")
            ccy = m.get("FinancialTerms", {}).get("Currency", "GBP")
            if ccy != "GBP":
                bad.append(f"{mid}: Currency={ccy}")
        assert len(bad) == 0, (
            f"{len(bad)} mortgages not in GBP: {bad[:5]}. "
            "Thames portfolio must be GBP-denominated."
        )

    def test_maturity_date_after_disbursal(self):
        """MaturityDate must be after DisbursalDate."""
        mortgages = _mortgages()
        if not mortgages:
            pytest.skip("loan.json empty or missing")
        bad = []
        for m in mortgages:
            mid = m.get("Header", {}).get("RLoanID", "?")
            ft = m.get("FinancialTerms", {})
            maturity = ft.get("MaturityDate", "")
            disbursal = ft.get("DisbursalDate", "")
            if maturity and disbursal and maturity <= disbursal:
                bad.append(f"{mid}: maturity={maturity} <= disbursal={disbursal}")
        assert len(bad) == 0, (
            f"{len(bad)} mortgages have MaturityDate <= DisbursalDate: {bad[:5]}"
        )
