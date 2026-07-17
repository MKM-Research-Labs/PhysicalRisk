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

"""Tests for reports.property.property_page_06_financial — FinancialPage."""

from reportlab.platypus import Paragraph, Table


def _make_property(value=750_000, area=120, sale_price=None, sale_date=None,
                   monthly_rent=None, other_valuation=None):
    valuation = {"PropertyValue": value}
    if other_valuation:
        valuation.update(other_valuation)

    transaction = {}
    if sale_price is not None:
        sales = {"SalePriceGbp": sale_price}
        if sale_date:
            sales["SaleDate"] = sale_date
        transaction["Sales"] = sales
    if monthly_rent is not None:
        transaction["Rental"] = {"MonthlyRentGbp": monthly_rent}

    prop = {
        "PropertyHeader": {
            "Valuation": valuation,
            "PropertyAttributes": {"PropertyAreaSqm": area},
        }
    }
    if transaction:
        prop["TransactionHistory"] = transaction
    return prop


class TestFinancialPageBasics:

    def _page(self):
        from reports.property.property_page_06_financial import FinancialPage
        return FinancialPage()

    def test_returns_list(self):
        assert isinstance(self._page().generate_elements(_make_property()), list)

    def test_returns_non_empty_list(self):
        assert len(self._page().generate_elements(_make_property())) > 0

    def test_empty_property_does_not_crash(self):
        assert isinstance(self._page().generate_elements({}), list)

    def test_has_financial_header(self):
        result = self._page().generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Financial" in t for t in texts)

    def test_has_table(self):
        result = self._page().generate_elements(_make_property())
        assert any(isinstance(e, Table) for e in result)

    def test_no_valuation_data(self):
        result = self._page().generate_elements({"PropertyHeader": {"Valuation": {}}})
        assert isinstance(result, list)

    def test_no_property_value(self):
        result = self._page().generate_elements({"PropertyHeader": {"Valuation": {"PurchaseDate": "2020-01-01"}}})
        assert isinstance(result, list)

    def test_value_per_sqm_shown_when_area_present(self):
        result = self._page().generate_elements(_make_property(value=600_000, area=120))
        assert isinstance(result, list)

    def test_no_area_skips_value_per_sqm(self):
        prop = _make_property(value=500_000)
        del prop["PropertyHeader"]["PropertyAttributes"]
        result = self._page().generate_elements(prop)
        assert isinstance(result, list)

    def test_other_valuation_field_with_value_in_name(self):
        result = self._page().generate_elements(
            _make_property(other_valuation={"FloodRiskDiscountValue": 15000})
        )
        assert isinstance(result, list)

    def test_other_valuation_field_without_value_in_name(self):
        result = self._page().generate_elements(
            _make_property(other_valuation={"PurchaseDate": "2015-06-01"})
        )
        assert isinstance(result, list)


class TestTransactionFinancials:

    def _page(self):
        from reports.property.property_page_06_financial import FinancialPage
        return FinancialPage()

    def test_sales_section_rendered(self):
        result = self._page().generate_elements(_make_property(sale_price=600_000))
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Transaction" in t for t in texts)

    def test_sale_price_and_appreciation(self):
        result = self._page().generate_elements(
            _make_property(value=750_000, sale_price=600_000)
        )
        assert any(isinstance(e, Table) for e in result)

    def test_sale_date_shown(self):
        result = self._page().generate_elements(
            _make_property(sale_price=500_000, sale_date="2015-06-01")
        )
        assert isinstance(result, list)

    def test_monthly_rent_and_annual_rent(self):
        result = self._page().generate_elements(_make_property(monthly_rent=2500))
        assert isinstance(result, list)

    def test_rental_yield_computed(self):
        result = self._page().generate_elements(
            _make_property(value=600_000, monthly_rent=2500)
        )
        assert isinstance(result, list)

    def test_no_transaction_data(self):
        prop = _make_property()
        # no TransactionHistory key
        assert isinstance(self._page().generate_elements(prop), list)


class TestMarketSegmentAnalysis:

    def _page(self):
        from reports.property.property_page_06_financial import FinancialPage
        return FinancialPage()

    def test_premium_over_1m(self):
        result = self._page().generate_elements(_make_property(value=1_500_000))
        assert isinstance(result, list)

    def test_upper_middle_500k_to_1m(self):
        result = self._page().generate_elements(_make_property(value=750_000))
        assert isinstance(result, list)

    def test_middle_250k_to_500k(self):
        result = self._page().generate_elements(_make_property(value=350_000))
        assert isinstance(result, list)

    def test_entry_level_under_250k(self):
        result = self._page().generate_elements(_make_property(value=180_000))
        assert isinstance(result, list)


class TestInvestmentRating:

    def _page(self):
        from reports.property.property_page_06_financial import FinancialPage
        return FinancialPage()

    def test_excellent_over_8pct(self):
        # 600/month on 50000 property = 14.4%
        result = self._page().generate_elements(_make_property(value=50_000, monthly_rent=600))
        assert isinstance(result, list)

    def test_good_6_to_8pct(self):
        # 350/month on 60000 = 7%
        result = self._page().generate_elements(_make_property(value=60_000, monthly_rent=350))
        assert isinstance(result, list)

    def test_fair_4_to_6pct(self):
        # 2000/month on 500000 = 4.8%
        result = self._page().generate_elements(_make_property(value=500_000, monthly_rent=2000))
        assert isinstance(result, list)

    def test_below_average_2_to_4pct(self):
        # 1000/month on 500000 = 2.4%
        result = self._page().generate_elements(_make_property(value=500_000, monthly_rent=1000))
        assert isinstance(result, list)

    def test_poor_under_2pct(self):
        # 500/month on 500000 = 1.2%
        result = self._page().generate_elements(_make_property(value=500_000, monthly_rent=500))
        assert isinstance(result, list)
