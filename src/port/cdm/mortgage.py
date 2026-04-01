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

#
# This software is provided under license by MKM Research Labs.
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

"""
Mortgage Common Data Model (CDM) implementation.
Based on Mortgage_CDM v6 specification.

Includes CatchmentID for multi-catchment support.
"""

from typing import Dict, List

from .base import BaseCDM
from .mortgage_schema import MORTGAGE_SCHEMA


class MortgageCDM(BaseCDM):
    """
    Mortgage Common Data Model (CDM) implementation.

    Provides a standardized schema and data transformation methods
    for mortgage data with comprehensive attributes.
    """

    def __init__(self):
        """Initialize the Mortgage CDM with schema definition."""
        self._schema = MORTGAGE_SCHEMA

    @property
    def schema(self) -> Dict:
        """Return the CDM schema."""
        return self._schema

    def validate(self, mortgage_data: dict) -> Dict[str, List[str]]:
        """
        Validate mortgage data against the CDM schema.

        Args:
            mortgage_data: Mortgage data to validate

        Returns:
            Dictionary of validation errors by section
        """
        errors = {}

        try:
            header = mortgage_data.get("Mortgage", {}).get("Header", {})
            header_errors = []

            if not header.get("MortgageID"):
                header_errors.append("Missing required field: MortgageID")

            if not header.get("CatchmentID"):
                header_errors.append("Missing recommended field: CatchmentID")

            if not header.get("PropertyID"):
                header_errors.append("Missing required field: PropertyID")

            if header_errors:
                errors["Header"] = header_errors

            # Validate financial terms
            terms = mortgage_data.get("Mortgage", {}).get("FinancialTerms", {})
            terms_errors = []

            if not terms.get("OriginalLoan"):
                terms_errors.append("Missing required field: OriginalLoan")

            if terms_errors:
                errors["FinancialTerms"] = terms_errors

            return errors

        except Exception as e:
            return {"validation_error": [str(e)]}

    def create_mapping(self, mortgage: dict) -> dict:
        """
        Create a flat dictionary from nested CDM structure.

        Args:
            mortgage: Nested mortgage data in CDM format

        Returns:
            Flat dictionary with snake_case keys
        """
        try:
            m = mortgage.get('Mortgage', {})
            header = m.get('Header', {})
            app = m.get('Application', {})
            terms = m.get('FinancialTerms', {})
            features = m.get('Features', {})
            status = m.get('CurrentStatus', {})
            borrower = m.get('BorrowerDetails', {})
            risk = m.get('RiskAssessment', {})

            mortgage_data = {
                # Header
                'mortgage_id': header.get('MortgageID'),
                'catchment_id': header.get('CatchmentID'),
                'property_id': header.get('PropertyID'),
                'uprn': header.get('UPRN'),

                # Application
                'member_id': app.get('MemberID'),
                'mortgage_provider': app.get('MortgageProvider'),
                'application_date': app.get('ApplicationDate'),
                'application_channel': app.get('ApplicationChannel'),
                'loan_purpose': app.get('LoanPurpose'),
                'occupancy_type': app.get('OccupancyType'),

                # Financial Terms
                'currency': terms.get('currency'),
                'disbursal_date': terms.get('DisbursalDate'),
                'purchase_value': terms.get('PurchaseValue'),
                'original_loan': terms.get('OriginalLoan'),
                'original_term': terms.get('OriginalTerm'),
                'original_lending_rate': terms.get('OriginalLendingRate'),
                'original_rate_type': terms.get('OriginalRateType'),
                'original_ltv': terms.get('OriginalLTV'),
                'maturity_date': terms.get('MaturityDate'),
                'debt_to_income_ratio': terms.get('DebtToIncomeRatio'),

                # Features
                'mortgage_type': features.get('MortgageType'),
                'repayment_type': features.get('RepaymentType'),
                'flexible_features': features.get('FlexibleFeatures'),

                # Current Status
                'outstanding_balance': status.get('OutstandingBalance'),
                'current_ltv': status.get('CurrentLTV'),
                'current_interest_rate': status.get('CurrentInterestRate'),
                'remaining_term': status.get('RemainingTerm'),
                'account_status': status.get('AccountStatus'),
                'default_flag': status.get('DefaultFlag'),
                'arrears_months': status.get('ArrearsMonths'),

                # Borrower
                'borrower_age': borrower.get('BorrowerAge'),
                'borrower_income': borrower.get('BorrowerIncome'),
                'borrower_credit_score': borrower.get('BorrowerCreditScore'),
                'employment_type': borrower.get('EmploymentType'),
                'number_of_borrowers': borrower.get('NumberOfBorrowers'),

                # Risk
                'behavioral_score': risk.get('BehavioralScore'),
                'prepayment_risk': risk.get('PrepaymentRisk'),
                'flood_risk_category': risk.get('FloodRiskCategory')
            }

            # Remove None values
            return {k: v for k, v in mortgage_data.items() if v is not None}

        except Exception as e:
            raise ValueError(f"Error creating mortgage mapping: {str(e)}")

    def get_required_fields(self) -> List[str]:
        """Return list of required fields."""
        return [
            'Mortgage.Header.MortgageID',
            'Mortgage.Header.CatchmentID',
            'Mortgage.Header.PropertyID',
            'Mortgage.FinancialTerms.OriginalLoan'
        ]
