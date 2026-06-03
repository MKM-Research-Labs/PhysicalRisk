# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Loan Common Data Model (CDM) class.

Wraps :data:`~port.cdm.asset.loan.schema.MORTGAGE_SCHEMA` and provides
validation, flat-mapping and pricing-adapter methods over loan/mortgage data.
"""

from typing import Dict, List

from ...base import BaseCDM
from .schema import MORTGAGE_SCHEMA, _loan_id, _unwrap_loan


class LoanCDM(BaseCDM):
    """
    Loan Common Data Model (CDM) implementation.

    Provides a standardized schema and data transformation methods
    for loan/mortgage data with comprehensive attributes.
    """

    def __init__(self):
        """Initialize the Loan CDM with schema definition."""
        self._schema = MORTGAGE_SCHEMA

    @property
    def schema(self) -> Dict:
        """Return the CDM schema."""
        return self._schema

    def validate(self, rloan_data: dict) -> Dict[str, List[str]]:
        """
        Validate mortgage data against the CDM schema.

        Args:
            rloan_data: Mortgage data to validate

        Returns:
            Dictionary of validation errors by section
        """
        errors = {}

        try:
            if not isinstance(rloan_data, dict):
                raise ValueError("validate requires a loan record dict")
            inner = _unwrap_loan(rloan_data)
            header = inner.get("Header", {})
            header_errors = []

            if not _loan_id(header):
                header_errors.append("Missing required field: RLoanID")

            if not header.get("CatchmentID"):
                header_errors.append("Missing recommended field: CatchmentID")

            if not header.get("PropertyID"):
                header_errors.append("Missing required field: PropertyID")

            if header_errors:
                errors["Header"] = header_errors

            # Validate financial terms
            terms = inner.get("FinancialTerms", {})
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
            if not isinstance(mortgage, dict):
                raise ValueError("create_mapping requires a loan record dict")
            m = _unwrap_loan(mortgage)
            header = m.get('Header', {})
            app = m.get('Application', {})
            terms = m.get('FinancialTerms', {})
            features = m.get('Features', {})
            status = m.get('CurrentStatus', {})
            borrower = m.get('BorrowerDetails', {})
            risk = m.get('RiskAssessment', {})

            rloan_data = {
                # Header
                'mortgage_id': _loan_id(header),
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
                'insurance_rate': terms.get('InsuranceRate'),

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
                'flood_risk_category': risk.get('FloodRiskCategory'),
                'recovery_haircut': risk.get('RecoveryHaircut')
            }

            # Remove None values
            return {k: v for k, v in rloan_data.items() if v is not None}

        except Exception as e:
            raise ValueError(f"Error creating mortgage mapping: {str(e)}")

    def to_pricer_inputs(self, mortgage: dict) -> dict:
        """
        Translate a CDM mortgage record into the keyword arguments expected by
        ``models.loan.LoanPricer.price_loan``.

        Reconciles the differences between the CDM data shape and the pricing
        engine's vocabulary:

        * field renames (OutstandingBalance -> loan_amount,
          CurrentInterestRate -> interest_rate, BorrowerIncome ->
          gross_annual_income);
        * unit conversions — CDM terms are in **months** (engine wants years)
          and CDM rates/LTV are **percentages** (engine wants decimals);
        * ``property_value`` is derived from OutstandingBalance and CurrentLTV
          (falling back to PurchaseValue) since the CDM has no current-value
          field;
        * ``insurance_rate`` / ``recovery_haircut`` come from the per-loan CDM
          fields, falling back to config defaults when absent.

        Args:
            mortgage: Nested mortgage data in CDM format (with top-level
                      ``Mortgage`` key).

        Returns:
            Dict suitable for ``price_loan(**inputs)`` /
            ``batch_price_loans([inputs])``.
        """
        try:
            from config.models import (
                LOAN_DEFAULT_INSURANCE_RATE,
                LOAN_DEFAULT_RECOVERY_HAIRCUT,
            )
        except Exception:
            LOAN_DEFAULT_INSURANCE_RATE = 0.002
            LOAN_DEFAULT_RECOVERY_HAIRCUT = 0.20

        flat = self.create_mapping(mortgage)

        outstanding_balance = flat.get('outstanding_balance', flat.get('original_loan'))
        current_ltv_pct = flat.get('current_ltv')

        # Derive current property value: balance / (LTV as a fraction).
        if outstanding_balance and current_ltv_pct:
            property_value = outstanding_balance / (current_ltv_pct / 100.0)
        else:
            property_value = flat.get('purchase_value')

        # CDM rates are percentages; the engine wants decimals.
        current_rate_pct = flat.get('current_interest_rate')
        if current_rate_pct is None:
            current_rate_pct = flat.get('original_lending_rate')
        interest_rate = (current_rate_pct / 100.0) if current_rate_pct is not None else None

        # CDM terms are in months; the engine wants years.
        original_term_months = flat.get('original_term')
        remaining_term_months = flat.get('remaining_term', original_term_months)

        insurance_rate = flat.get('insurance_rate', LOAN_DEFAULT_INSURANCE_RATE)
        recovery_haircut = flat.get('recovery_haircut', LOAN_DEFAULT_RECOVERY_HAIRCUT)

        inputs = {
            'mortgage_id': flat.get('mortgage_id'),
            'property_id': flat.get('property_id'),
            'loan_amount': outstanding_balance,
            'property_value': property_value,
            'gross_annual_income': flat.get('borrower_income'),
            'interest_rate': interest_rate,
            'insurance_rate': insurance_rate,
            'original_maturity': (original_term_months / 12.0) if original_term_months else None,
            'current_term': (remaining_term_months / 12.0) if remaining_term_months else None,
            'recovery_haircut': recovery_haircut,
            'flood_risk_category': flat.get('flood_risk_category'),
        }

        # Drop keys the engine has no default for only when truly absent, so
        # batch_price_loans' own .get() defaults can take over.
        return {k: v for k, v in inputs.items() if v is not None}

    def get_required_fields(self) -> List[str]:
        """Return list of required fields."""
        return [
            'RLoan.Header.RLoanID',
            'RLoan.Header.CatchmentID',
            'RLoan.Header.PropertyID',
            'RLoan.FinancialTerms.OriginalLoan'
        ]
