# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for reports.property.property_page_10_transactions — TransactionsPage."""

from reportlab.platypus import Paragraph, Table


def _make_property():
    return {
        "PropertyHeader": {
            "PropertyID": "PROP-001",
            "Address": "1 Test Street",
            "RiskAssessment": {
                "OverallFloodRisk": "Medium",
                "EAFloodZone": "Zone 2",
                "FloodZoneType": "River",
                "ClimateChangeFloodRisk": "High",
                "FloodInsuranceAvailable": True,
                "FloodInsurancePremiumIndicative": 1200,
            },
            "Construction": {
                "ConstructionMethod": "Traditional Brick",
                "FoundationType": "Strip",
                "RoofType": "Pitched",
                "WallMaterial": "Brick",
                "FloorType": "Solid concrete",
                "NumberOfFloors": 2,
                "BasementPresent": False,
                "FloodAdaptations": ["Flood barriers"],
            },
            "Valuation": {
                "PropertyValue": 750_000,
                "PurchasePrice": 600_000,
                "PurchaseDate": "2015-06-01",
                "RentalYield": 0.045,
                "FloodRiskDiscount": 0.05,
            },
            "Protection": {
                "BuildingsInsuranceProvider": "Aviva",
                "BuildingsInsuranceCover": 800_000,
                "BuildingsInsurancePremium": 1_200,
                "ContentsInsuranceProvider": "Direct Line",
                "ContentsInsurancePremium": 400,
                "FloodInsuranceFlag": True,
                "SecuritySystem": "Alarm + CCTV",
                "SmokeCO2Detectors": True,
            },
            "PropertyAttributes": {
                "PropertyAreaSqm": 120,
                "PropertyType": "Semi-detached",
                "ConstructionYear": 1990,
            },
        },
        "Location": {
            "Latitude": 51.5,
            "Longitude": -0.1,
            "Elevation": 5.0,
            "DistanceToRiver": 150,
        },
        "FloodHistory": {
            "FloodEvents": [
                {"EventDate": "2014-02-10", "FloodDepth": 0.3, "FloodType": "Surface"},
            ],
            "PreviousFloodClaims": 1,
        },
        "TransactionHistory": {
            "Transactions": [
                {"TransactionDate": "2015-06-01", "TransactionType": "Purchase",
                 "TransactionPrice": 600_000, "TransactionStatus": "Completed"},
                {"TransactionDate": "2010-03-01", "TransactionType": "Sale",
                 "TransactionPrice": 480_000, "TransactionStatus": "Completed"},
            ]
        },
    }


def _make_mortgage():
    return {
        "Mortgage": {
            "Header": {"MortgageID": "MORT-001"},
            "CurrentStatus": {
                "CurrentLTV": 0.65,
                "CurrentBalance": 400_000,
                "InArrearsFlag": False,
                "MissedPayments12M": 0,
                "MonthsInArrears": 0,
                "ArrearsAmount": 0,
            },
            "FinancialDetails": {
                "MonthlyPayment": 2_000,
                "InterestRate": 0.035,
                "RemainingTerm": 18,
                "OriginalBalance": 450_000,
                "ProductType": "Fixed",
                "ProductEndDate": "2028-01-01",
            },
            "BorrowerDetails": {
                "BorrowerAge": 42,
                "EmploymentStatus": "Employed",
                "AnnualIncome": 90_000,
                "CreditScore": 750,
            },
        }
    }


class TestTransactionsPage:

    def _page(self):
        from reports.property.property_page_10_transactions import TransactionsPage
        return TransactionsPage()

    def test_returns_list(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        assert isinstance(result, list)
        assert len(result) > 0

    def test_empty_property_does_not_crash(self):
        page = self._page()
        result = page.generate_elements({})
        assert isinstance(result, list)

    def test_has_transactions_header(self):
        page = self._page()
        result = page.generate_elements(_make_property())
        texts = [e.text for e in result if isinstance(e, Paragraph) and hasattr(e, 'text')]
        assert any("Transaction" in t or "History" in t for t in texts)

    def test_with_mortgage_data(self):
        page = self._page()
        result = page.generate_elements(_make_property(), _make_mortgage())
        assert isinstance(result, list)

    def test_no_transaction_history(self):
        page = self._page()
        prop = _make_property()
        del prop["TransactionHistory"]
        result = page.generate_elements(prop)
        assert isinstance(result, list)

    def test_empty_transactions(self):
        page = self._page()
        prop = _make_property()
        prop["TransactionHistory"]["Transactions"] = []
        result = page.generate_elements(prop)
        assert isinstance(result, list)

    def test_with_sales_data(self):
        page = self._page()
        prop = _make_property()
        prop["TransactionHistory"] = {
            "Sales": {
                "SalePriceGbp": 600_000,
                "SaleDate": "2015-06-01",
                "PreviousOwner": "Smith",
                "MarketingDays": 45,
                "OtherField": "extra value",
            }
        }
        result = page.generate_elements(prop)
        assert isinstance(result, list)
        assert any(isinstance(e, Table) for e in result)

    def test_sales_quick_sale(self):
        page = self._page()
        prop = _make_property()
        prop["TransactionHistory"] = {"Sales": {"SalePriceGbp": 500_000, "MarketingDays": 15}}
        result = page.generate_elements(prop)
        assert isinstance(result, list)

    def test_sales_extended_marketing(self):
        page = self._page()
        prop = _make_property()
        prop["TransactionHistory"] = {"Sales": {"SalePriceGbp": 500_000, "MarketingDays": 120}}
        result = page.generate_elements(prop)
        assert isinstance(result, list)

    def test_sales_very_long_marketing(self):
        page = self._page()
        prop = _make_property()
        prop["TransactionHistory"] = {"Sales": {"SalePriceGbp": 500_000, "MarketingDays": 200}}
        result = page.generate_elements(prop)
        assert isinstance(result, list)

    def test_with_rental_data(self):
        page = self._page()
        prop = _make_property()
        prop["TransactionHistory"] = {
            "Rental": {
                "MonthlyRentGbp": 2_000,
                "RentalHistory": "3 years tenancy",
                "VacancyCount": 1,
                "TenancyDuration": "12 months",
                "Agency": "ABC Lettings",
            }
        }
        result = page.generate_elements(prop)
        assert isinstance(result, list)
        assert any(isinstance(e, Table) for e in result)

    def test_assess_yield_excellent(self):
        page = self._page()
        assert page._assess_yield(9.0) == "Excellent yield"

    def test_assess_yield_good(self):
        page = self._page()
        assert page._assess_yield(7.0) == "Good yield"

    def test_assess_yield_average(self):
        page = self._page()
        assert page._assess_yield(5.0) == "Average yield"

    def test_assess_yield_below_average(self):
        page = self._page()
        assert page._assess_yield(3.0) == "Below average yield"

    def test_assess_yield_poor(self):
        page = self._page()
        assert page._assess_yield(1.0) == "Poor yield"

    def test_market_analysis_yield(self):
        page = self._page()
        transaction_data = {"Sales": {"SalePriceGbp": 500_000}, "Rental": {"MonthlyRentGbp": 2_500}}
        prop = _make_property()
        result = page._perform_market_analysis(transaction_data, prop)
        assert "Gross Rental Yield" in result

    def test_market_analysis_appreciation(self):
        page = self._page()
        transaction_data = {"Sales": {"SalePriceGbp": 400_000}, "Rental": {}}
        prop = _make_property()
        prop["PropertyHeader"]["Valuation"]["PropertyValue"] = 750_000
        result = page._perform_market_analysis(transaction_data, prop)
        assert "Capital Appreciation" in result

    def test_market_analysis_marketing_above_30(self):
        page = self._page()
        transaction_data = {"Sales": {"MarketingDays": 60}, "Rental": {}}
        result = page._perform_market_analysis(transaction_data, {})
        assert "Marketing Efficiency" in result
        assert "Good" in result["Marketing Efficiency"]

    def test_market_analysis_marketing_above_90(self):
        page = self._page()
        transaction_data = {"Sales": {"MarketingDays": 100}, "Rental": {}}
        result = page._perform_market_analysis(transaction_data, {})
        assert "Below average" in result["Marketing Efficiency"]

    def test_market_analysis_never_rented(self):
        page = self._page()
        transaction_data = {"Sales": {}, "Rental": {"RentalHistory": "Never rented"}}
        result = page._perform_market_analysis(transaction_data, {})
        assert "Rental History" in result
        assert "No rental history" in result["Rental History"]

    def test_market_analysis_no_vacancy(self):
        page = self._page()
        transaction_data = {"Sales": {}, "Rental": {"VacancyCount": 0}}
        result = page._perform_market_analysis(transaction_data, {})
        assert "Rental Stability" in result
        assert "Excellent" in result["Rental Stability"]

    def test_market_analysis_few_vacancies(self):
        page = self._page()
        transaction_data = {"Sales": {}, "Rental": {"VacancyCount": 2}}
        result = page._perform_market_analysis(transaction_data, {})
        assert "Good" in result["Rental Stability"]

    def test_market_analysis_many_vacancies(self):
        page = self._page()
        transaction_data = {"Sales": {}, "Rental": {"VacancyCount": 5}}
        result = page._perform_market_analysis(transaction_data, {})
        assert "Concerning" in result["Rental Stability"]
