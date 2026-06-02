# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Field value generators by type — called by MortgagePortfolioGenerator."""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from .constants import RATE_TYPES, RATE_TYPE_WEIGHTS, UK_LENDERS


def generate_menu_value(field_name: str, field_def: Dict, index: int, financial_data: Dict) -> str:
    """Generate a menu/enum value based on field name."""
    options = field_def.get("options", field_def.get("values", [])) if isinstance(field_def, dict) else []

    if field_name == "MortgageType":
        return financial_data.get("mortgage_type", "Residential")
    elif field_name == "OriginalRateType":
        return random.choices(RATE_TYPES, weights=RATE_TYPE_WEIGHTS)[0]
    elif field_name == "PaymentFrequency":
        return "Monthly"
    elif field_name == "OccupancyType":
        return financial_data.get("occupancy_type", "PrimaryResidence")
    elif field_name == "LoanPurpose":
        mortgage_type = financial_data.get("mortgage_type", "Residential")
        if mortgage_type == "Buy-to-Let":
            return random.choices(["Purchase", "Refinancing"], weights=[0.6, 0.4])[0]
        return random.choices(["Purchase", "Refinancing", "Home Improvement"], weights=[0.7, 0.25, 0.05])[0]
    elif field_name == "RepaymentType":
        mortgage_type = financial_data.get("mortgage_type", "Residential")
        if mortgage_type == "Buy-to-Let":
            return random.choices(["Interest only", "Repayment", "Part and part"], weights=[0.6, 0.3, 0.1])[0]
        return random.choices(["Repayment", "Interest only", "Part and part"], weights=[0.85, 0.1, 0.05])[0]
    elif field_name == "ApplicationChannel":
        return random.choices(["Retail", "Broker", "Correspondent"], weights=[0.3, 0.5, 0.2])[0]

    if options:
        return random.choice(options)
    return ""


def generate_boolean_value(field_name: str, financial_data: Dict) -> bool:
    """Generate a boolean value based on field name."""
    if field_name == "DefaultFlag":
        return financial_data.get("is_defaulted", False)
    elif field_name == "InArrearsFlag":
        return financial_data.get("is_in_arrears", False)
    elif field_name == "BusinessOrCommercialPurpose":
        return financial_data.get("mortgage_type") == "Buy-to-Let"
    elif field_name == "FirstTimeBuyerFlag":
        if financial_data.get("mortgage_type") == "Buy-to-Let":
            return False
        property_value = financial_data.get("property_value", 0)
        if property_value > 600000:
            return random.random() < 0.1
        return random.random() < 0.3
    elif field_name == "AdvisedFlag":
        return random.random() < 0.85
    elif field_name == "ExecutionOnlyFlag":
        return random.random() < 0.15
    elif field_name == "MMRCompliantFlag":
        return True
    elif field_name == "StressTestCompliantFlag":
        return True
    return random.random() < 0.3


def generate_decimal_value(field_name: str, financial_data: Dict) -> float:
    """Generate a decimal value based on field name."""
    if field_name == "PurchaseValue":
        return financial_data.get("property_value", 500000)
    elif field_name == "ApplicationPropertyValuation":
        return financial_data.get("property_value", 500000)
    elif field_name in ("OriginalLoan", "OriginalLoanAmount"):
        return financial_data.get("loan_amount", 400000)
    elif field_name in ("OutstandingBalance", "CurrentBalance"):
        return financial_data.get("outstanding_balance", 350000)
    elif field_name == "OriginalLTV":
        return financial_data.get("ltv_ratio", 0.8) * 100
    elif field_name in ("CurrentLTV", "LTV"):
        return financial_data.get("current_ltv", 0.75) * 100
    elif field_name == "LoanToValueRatio":
        return financial_data.get("ltv_ratio", 0.8) * 100
    elif field_name == "OriginalLendingRate":
        return round(financial_data.get("interest_rate", 0.035) * 100, 2)
    elif field_name in ("CurrentLendingRate", "CurrentInterestRate", "InterestRate"):
        return round(financial_data.get("interest_rate", 0.035) * 100, 2)
    elif field_name == "InsuranceRate":
        return round(random.uniform(0.0015, 0.003), 4)
    elif field_name == "RecoveryHaircut":
        return round(random.uniform(0.15, 0.30), 3)
    elif field_name == "CurrentPayment":
        return financial_data.get("monthly_payment", 1500)
    elif field_name == "BorrowerIncome":
        return financial_data.get("borrower_income", 60000)
    elif field_name == "DebtToIncomeRatio":
        annual_payment = financial_data.get("annual_payment", 18000)
        income = financial_data.get("borrower_income", 60000)
        return round(annual_payment / income, 3) if income > 0 else 0.3
    elif field_name == "APRCInitialRate":
        return round(financial_data.get("interest_rate", 0.035) * 100 + random.uniform(0.3, 1.0), 2)
    elif field_name == "APRCSecondaryRate":
        return round(financial_data.get("interest_rate", 0.035) * 100 + random.uniform(1.0, 2.5), 2)
    base_amount = financial_data.get("loan_amount", 500000)
    return round(base_amount * random.uniform(0.005, 0.03) + random.uniform(0, 1000), 2)


def generate_integer_value(field_name: str, financial_data: Dict) -> int:
    """Generate an integer value based on field name."""
    if field_name in ("OriginalTerm", "LoanTerm"):
        return financial_data.get("term_months", 300)
    elif field_name == "RemainingTerm":
        return max(0, financial_data.get("term_months", 300) - financial_data.get("months_elapsed", 0))
    elif field_name == "TotalPayments":
        return min(financial_data.get("months_elapsed", 0), financial_data.get("term_months", 300))
    elif field_name == "BorrowerAge":
        mortgage_type = financial_data.get("mortgage_type", "Residential")
        property_value = financial_data.get("property_value", 0)
        if mortgage_type == "Buy-to-Let" or property_value > 800000:
            return random.randint(35, 65)
        return random.randint(25, 60)
    elif field_name == "BorrowerCreditScore":
        interest_rate = financial_data.get("interest_rate", 0.035)
        property_value = financial_data.get("property_value", 0)
        if interest_rate < 0.035:
            return random.randint(750, 850)
        elif property_value > 600000:
            return random.randint(700, 800)
        return random.randint(650, 750)
    elif field_name == "FamilyMembers":
        return random.choices([1, 2, 3, 4], weights=[0.3, 0.35, 0.25, 0.1])[0]
    elif field_name == "NumberOfBorrowers":
        return random.choices([1, 2], weights=[0.4, 0.6])[0]
    elif field_name == "DaysInArrears":
        if financial_data.get("is_defaulted"):
            return random.randint(90, 365)
        elif financial_data.get("is_in_arrears"):
            return random.randint(1, 89)
        return 0
    elif field_name == "ArrearsMonths":
        return random.randint(1, 6) if financial_data.get("is_in_arrears") else 0
    elif field_name == "BehavioralScore":
        return random.randint(30, 100)
    elif field_name == "PrepaymentRisk":
        return random.randint(7, 10) if financial_data.get("interest_rate", 0.035) > 0.05 else random.randint(1, 5)
    return random.randint(1, 10)


def generate_date_value(field_name: str, financial_data: Dict) -> str:
    """Generate a date value based on field name."""
    if field_name == "ApplicationDate":
        months_ago = financial_data.get("months_elapsed", 12) + random.randint(1, 3)
        return (datetime.now() - timedelta(days=30 * months_ago)).strftime("%Y-%m-%d")
    elif field_name == "DisbursalDate":
        months_ago = financial_data.get("months_elapsed", 12)
        return (datetime.now() - timedelta(days=30 * months_ago)).strftime("%Y-%m-%d")
    elif field_name == "MaturityDate":
        remaining = financial_data.get("term_months", 300) - financial_data.get("months_elapsed", 0)
        return (datetime.now() + timedelta(days=30 * remaining)).strftime("%Y-%m-%d")
    elif field_name == "DefaultDate":
        if financial_data.get("is_defaulted"):
            months_ago = random.randint(1, min(12, financial_data.get("months_elapsed", 12)))
            return (datetime.now() - timedelta(days=30 * months_ago)).strftime("%Y-%m-%d")
        return None
    return (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")


def generate_text_value(field_name: str, index: int, financial_data: Dict) -> str:
    """Generate a text value based on field name."""
    if field_name == "MortgageID":
        return financial_data.get("mortgage_id", str(uuid.uuid4()))
    elif field_name == "MortgageProvider":
        return random.choice(UK_LENDERS)
    elif field_name == "MemberID":
        return f"MEMBER-{str(uuid.uuid4())[:8]}"
    elif field_name == "UPRN":
        return financial_data.get("uprn", f"UPRN-{random.randint(100000, 999999)}")
    elif field_name == "PropertyID":
        return financial_data.get("property_id", f"PROP-{index}")
    elif field_name == "CatchmentID":
        return "thames"
    elif field_name == "currency":
        # Function-local import: rand modules are loaded *by* config, so a
        # top-level "from config import config" risks a circular import.
        from config import config
        return config.CURRENCY
    elif field_name == "AccountStatus":
        if financial_data.get("is_defaulted"):
            return "Default"
        return random.choices(["Current", "Arrears", "Closed"], weights=[0.9, 0.06, 0.04])[0]
    elif field_name == "LatestStatus":
        if financial_data.get("is_defaulted"):
            return "Defaulted"
        return random.choices(["Current", "Completed", "Redeemed"], weights=[0.93, 0.05, 0.02])[0]
    elif field_name in ("BorrowerEmployment", "EmploymentType"):
        mortgage_type = financial_data.get("mortgage_type", "Residential")
        if mortgage_type == "Buy-to-Let":
            return random.choices(["Self-employed", "Employed", "Director", "Retired"], weights=[0.4, 0.4, 0.15, 0.05])[0]
        return random.choices(["Employed", "Self-employed", "Retired", "Contractor"], weights=[0.7, 0.15, 0.08, 0.07])[0]
    elif field_name == "MaritalStatus":
        age = financial_data.get("borrower_age", 40)
        if age < 30:
            return random.choices(["Single", "Married", "Civil Partnership"], weights=[0.6, 0.35, 0.05])[0]
        return random.choices(["Married", "Single", "Divorced", "Civil Partnership", "Widowed"], weights=[0.5, 0.25, 0.15, 0.05, 0.05])[0]
    elif field_name == "FloodRiskCategory":
        return financial_data.get("flood_risk", "Low")
    return f"Text-{index}-{random.randint(1000, 9999)}"


def generate_field_value(field_name: str, field_def: Dict, index: int, financial_data: Dict) -> Any:
    """
    Generate a value for any field based on its type in the schema.

    Called by MortgagePortfolioGenerator._build_section() for each field.
    """
    if not isinstance(field_def, dict):
        return field_def if isinstance(field_def, str) else ""

    field_type = field_def.get('type', 'text')

    if field_type in ("menu", "enum"):
        return generate_menu_value(field_name, field_def, index, financial_data)
    elif field_type == "boolean":
        return generate_boolean_value(field_name, financial_data)
    elif field_type == "decimal":
        return generate_decimal_value(field_name, financial_data)
    elif field_type == "integer":
        return generate_integer_value(field_name, financial_data)
    elif field_type == "date":
        return generate_date_value(field_name, financial_data)
    elif field_type == "text":
        return generate_text_value(field_name, index, financial_data)
    return ""
