# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for create_mortgage_section and create_mortgage_risk_section."""

import pytest


# ---------------------------------------------------------------------------
# create_mortgage_section
# ---------------------------------------------------------------------------

class TestCreateMortgageSection:

    def test_contains_mortgage_id(self, builder, mortgage_info):
        html = builder.create_mortgage_section(mortgage_info, 400000, 'Medium')
        assert 'MTG-001' in html

    def test_contains_lender(self, builder, mortgage_info):
        html = builder.create_mortgage_section(mortgage_info, 400000, 'Medium')
        assert 'Thames Bank' in html

    def test_loan_amount_formatted(self, builder, mortgage_info):
        html = builder.create_mortgage_section(mortgage_info, 400000, 'Medium')
        assert '300,000' in html

    def test_interest_rate_formatted(self, builder, mortgage_info):
        html = builder.create_mortgage_section(mortgage_info, 400000, 'Medium')
        assert '%' in html

    def test_term_years_shown(self, builder, mortgage_info):
        html = builder.create_mortgage_section(mortgage_info, 400000, 'Medium')
        assert '25' in html

    def test_section_header_present(self, builder, mortgage_info):
        html = builder.create_mortgage_section(mortgage_info, 400000, 'Medium')
        assert 'MORTGAGE DETAILS' in html

    def test_nested_mortgage_key_structure(self, builder):
        nested = {
            'Mortgage': {
                'Header': {'MortgageID': 'MTG-NESTED'},
                'FinancialTerms': {
                    'OriginalLoan': 200000,
                    'OriginalLendingRate': 0.035,
                    'TermYears': 20,
                },
                'Application': {'MortgageProvider': 'Nested Bank'},
            }
        }
        html = builder.create_mortgage_section(nested, 300000, 'Low')
        assert 'MTG-NESTED' in html
        assert 'Nested Bank' in html

    def test_monthly_payment_calculated_and_shown(self, builder, mortgage_info):
        html = builder.create_mortgage_section(mortgage_info, 400000, 'Medium')
        assert 'Monthly Payment' in html


# ---------------------------------------------------------------------------
# create_mortgage_risk_section
# ---------------------------------------------------------------------------

class TestCreateMortgageRiskSection:

    def test_returns_empty_for_none(self, builder):
        assert builder.create_mortgage_risk_section(None) == ""

    def test_returns_empty_for_empty_dict(self, builder):
        assert builder.create_mortgage_risk_section({}) == ""

    def test_contains_mortgage_id(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert 'MTG-001' in html

    def test_contains_loan_amount(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert '300,000' in html

    def test_contains_interest_rate(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert '%' in html

    def test_contains_monthly_payment(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert 'Monthly Payment' in html

    def test_contains_annual_payment(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert 'Annual Payment' in html

    def test_contains_credit_spread(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert 'Credit Spread' in html

    def test_contains_recovery_haircut(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert 'Recovery Haircut' in html

    def test_contains_flood_risk_level(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert 'Medium' in html

    def test_contains_flood_depth(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert '0.20' in html

    def test_contains_overall_assessment(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert 'Overall Assessment' in html

    def test_section_headers_present(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        assert 'MORTGAGE RISK ANALYSIS' in html
        assert 'Risk Metrics' in html
        assert 'Impact Assessment' in html

    def test_ltv_ratio_calculated_from_loan_and_value(self, builder, mortgage_risk_info):
        html = builder.create_mortgage_risk_section(mortgage_risk_info)
        # 300000 / 400000 = 75%
        assert '75' in html
